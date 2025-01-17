import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os
import requests
from io import BytesIO

st.set_page_config(
    page_title="Análise de Cabotagem",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚢",
    menu_items=None
)

def create_unique_id(row):
    """Cria um ID único para cada registro baseado em campos chave"""
    unique_string = f"{row['DATA DE EMBARQUE']}_{row['PORTO DE ORIGEM']}_{row['PORTO DE DESTINO']}_{row['NAVIO']}_{row['VIAGEM']}_{row['REMETENTE']}_{row['DESTINATÁRIO']}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def remove_duplicates(df):
    """Remove registros duplicados mantendo apenas a versão mais recente"""
    df['ID_UNICO'] = df.apply(create_unique_id, axis=1)
    df['DATA_ATUALIZACAO'] = datetime.now()
    
    if os.path.exists('dados_cabotagem_consolidados.parquet'):
        df_consolidated = pd.read_parquet('dados_cabotagem_consolidados.parquet')
        df_all = pd.concat([df_consolidated, df])
        df_all = df_all.sort_values('DATA_ATUALIZACAO').drop_duplicates(
            subset=['ID_UNICO'], 
            keep='last'
        )
    else:
        df_all = df
    
    df_all.to_parquet('dados_cabotagem_consolidados.parquet')
    
    with open('log_atualizacao_cabotagem.txt', 'a') as f:
        f.write(f"{datetime.now()} - Registros processados: {len(df)}, "
                f"Registros únicos após processamento: {len(df_all)}\n")
    
    return df_all

def download_file_from_drive(file_id):
    """Download arquivo do Google Drive"""
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"Erro ao baixar arquivo do Google Drive: {str(e)}")
        return None

def load_and_process_data():
    try:
        # ID do arquivo no Google Drive
        file_id = st.secrets["urls"]["planilha_cabotagem"]
        
        # Baixando o arquivo
        excel_content = download_file_from_drive(file_id)
        if excel_content is None:
            return pd.DataFrame()
        
        # Lendo o arquivo Excel
        df = pd.read_excel(excel_content)
        
        # Convertendo datas
        df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'])
        
        # Convertendo colunas numéricas
        for col in ['QUANTIDADE C20', 'QUANTIDADE C40', 'QUANTIDADE TEUS', 'QTDE FCL']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Limpando colunas de texto
        text_columns = ['PORTO DE ORIGEM', 'PORTO DE DESTINO', 'TERMINAL DE EMBARQUE', 
                       'TERMINAL DE DESCARGA', 'REMETENTE', 'DESTINATÁRIO', 'ARMADOR', 
                       'NAVIO', 'TIPO DE CARGA', 'TIPO DE CONTEINER', 'DESCRIÇÃO DA MERCADORIA']
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip().str.upper()
        
        df = remove_duplicates(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()

def get_detailed_info(df, data_selecionada, porto_origem, porto_destino):
    """Retorna informações detalhadas para uma data e rota específicas"""
    data_filtro = pd.to_datetime(data_selecionada)
    
    mask = (
        (df['DATA DE EMBARQUE'].dt.strftime('%Y-%m-%d') == data_filtro.strftime('%Y-%m-%d')) & 
        (df['PORTO DE ORIGEM'] == porto_origem) & 
        (df['PORTO DE DESTINO'] == porto_destino)
    )
    return df[mask]

def create_summary_table(df):
    """Cria tabela resumo com volumes por porto"""
    # Calculando total de containers (C20 + C40)
    df['TOTAL_CONTAINERS'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']
    
    # Criando sumário para origem
    origem_summary = df.groupby('PORTO DE ORIGEM').agg({
        'TOTAL_CONTAINERS': 'sum',
        'ID_UNICO': 'count',
        'REMETENTE': 'nunique'
    }).reset_index()
    origem_summary.columns = ['Porto', 'Containers Embarcados', 'Operações', 'Empresas']
    origem_summary['Tipo'] = 'Origem'
    
    # Criando sumário para destino
    destino_summary = df.groupby('PORTO DE DESTINO').agg({
        'TOTAL_CONTAINERS': 'sum',
        'ID_UNICO': 'count',
        'DESTINATÁRIO': 'nunique'
    }).reset_index()
    destino_summary.columns = ['Porto', 'Containers Recebidos', 'Operações', 'Empresas']
    destino_summary['Tipo'] = 'Destino'
    
    # Combinando os dados
    combined_summary = pd.merge(
        origem_summary,
        destino_summary,
        on='Porto',
        suffixes=('_orig', '_dest'),
        how='outer'
    ).fillna(0)
    
    # Calculando totais
    combined_summary['Total Containers'] = combined_summary['Containers Embarcados'] + combined_summary['Containers Recebidos']
    combined_summary['Total Operações'] = combined_summary['Operações_orig'] + combined_summary['Operações_dest']
    combined_summary['Total Empresas'] = combined_summary['Empresas_orig'] + combined_summary['Empresas_dest']
    
    # Formatando números
    for col in ['Containers Embarcados', 'Containers Recebidos', 'Total Containers']:
        combined_summary[col] = combined_summary[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
    
    for col in ['Operações_orig', 'Operações_dest', 'Total Operações', 
                'Empresas_orig', 'Empresas_dest', 'Total Empresas']:
        combined_summary[col] = combined_summary[col].apply(lambda x: f"{int(x):,}")
    
    return combined_summary.sort_values('Porto')

def format_detailed_table(df_filtered):
    """Formata a tabela de detalhes com as informações relevantes"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Calculando total de containers
    df_filtered['TOTAL_CONTAINERS'] = df_filtered['QUANTIDADE C20'] + df_filtered['QUANTIDADE C40']
    
    colunas_exibir = {
        'TERMINAL DE EMBARQUE': 'Terminal Origem',
        'TERMINAL DE DESCARGA': 'Terminal Destino',
        'REMETENTE': 'Remetente',
        'DESTINATÁRIO': 'Destinatário',
        'ARMADOR': 'Armador',
        'NAVIO': 'Navio',
        'TIPO DE CARGA': 'Tipo Carga',
        'TIPO DE CONTEINER': 'Tipo Container',
        'DESCRIÇÃO DA MERCADORIA': 'Mercadoria',
        'TOTAL_CONTAINERS': 'Containers',
        'QUANTIDADE C20': 'C20',
        'QUANTIDADE C40': 'C40',
        'PESO BRUTO': 'Peso (ton)'
    }
    
    df_detalhes = df_filtered[colunas_exibir.keys()].copy()
    df_detalhes.columns = colunas_exibir.values()
    
    # Formatando números
    for col in ['Containers', 'C20', 'C40']:
        df_detalhes[col] = df_detalhes[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
    df_detalhes['Peso (ton)'] = df_detalhes['Peso (ton)'].apply(lambda x: f"{float(x):,.2f}" if pd.notnull(x) else "-")
    
    return df_detalhes

def show_update_info():
    """Exibe informações sobre as atualizações dos dados"""
    if os.path.exists('log_atualizacao_cabotagem.txt'):
        with open('log_atualizacao_cabotagem.txt', 'r') as f:
            last_updates = f.readlines()[-5:]  # Mostra as últimas 5 atualizações
        
        st.markdown("### ⏱️ Últimas Atualizações")
        for update in last_updates:
            st.text(update.strip())

def main():
    st.title("🚢 Análise de Operações de Cabotagem")
    
    try:
        # Carregando dados
        df = load_and_process_data()
        
        # Calculando total de containers
        df['TOTAL_CONTAINERS'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']
        
        # Criando e exibindo tabela resumo
        st.markdown("### 📊 Visão Geral por Porto")
        summary_table = create_summary_table(df)
        st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_containers = df['TOTAL_CONTAINERS'].sum()
            st.metric("Total Containers", f"{int(total_containers):,}")
        with col2:
            st.metric("Total Portos", f"{len(summary_table):,}")
        with col3:
            total_empresas = len(pd.concat([
                df['REMETENTE'].dropna(),
                df['DESTINATÁRIO'].dropna()
            ]).unique())
            st.metric("Total Empresas", f"{total_empresas:,}")
        with col4:
            st.metric("Total Navios", f"{len(df['NAVIO'].unique()):,}")
        
        # Tipo de Container
        col1, col2 = st.columns(2)
        with col1:
            total_c20 = df['QUANTIDADE C20'].sum()
            st.metric("Total C20", f"{int(total_c20):,}")
        with col2:
            total_c40 = df['QUANTIDADE C40'].sum()
            st.metric("Total C40", f"{int(total_c40):,}")
        
        # Opção para ver análise de duplicidades
        if st.checkbox("Mostrar Análise de Duplicidades"):
            st.markdown("### 🔍 Análise de Duplicidades")
            duplicates = df.groupby('ID_UNICO').size().reset_index(name='contagem')
            duplicates = duplicates[duplicates['contagem'] > 1]
            
            if not duplicates.empty:
                st.warning(f"Encontrados {len(duplicates)} registros com potenciais duplicidades.")
                st.dataframe(duplicates)
            else:
                st.success("Nenhuma duplicidade encontrada nos dados!")
        
        # Separador
        st.markdown("---")
        st.markdown("### 🔍 Análise Detalhada por Rota")
        
        # Seletor de data
        data_selecionada = st.date_input(
            "Selecione a Data",
            value=pd.to_datetime(df['DATA DE EMBARQUE'].min()).date(),
            min_value=pd.to_datetime(df['DATA DE EMBARQUE'].min()).date(),
            max_value=pd.to_datetime(df['DATA DE EMBARQUE'].max()).date()
        )
        
        # Filtrando dados pela data
        data_filtro = pd.to_datetime(data_selecionada)
        df_data = df[df['DATA DE EMBARQUE'].dt.strftime('%Y-%m-%d') == data_filtro.strftime('%Y-%m-%d')]
        
        # Matriz origem-destino usando containers
        matriz_od = pd.pivot_table(
            df_data,
            values='TOTAL_CONTAINERS',
            index='PORTO DE ORIGEM',
            columns='PORTO DE DESTINO',
            aggfunc='sum',
            fill_value=0
        )
        
        # Formatando números na matriz
        matriz_formatted = matriz_od.applymap(lambda x: f"{int(x):,}" if x > 0 else "-")
        
        # Exibindo matriz
        st.markdown("#### Matriz Origem-Destino (Containers)")
        st.dataframe(matriz_formatted, use_container_width=True)
        
        # Seletores de portos
        col1, col2 = st.columns(2)
        with col1:
            portos_origem = sorted([p for p in df['PORTO DE ORIGEM'].unique() if p])
            porto_origem = st.selectbox("Porto de Origem", options=portos_origem)
        with col2:
            portos_destino = sorted([p for p in df['PORTO DE DESTINO'].unique() if p])
            porto_destino = st.selectbox("Porto de Destino", options=portos_destino)
        
        # Detalhes da rota selecionada
        st.markdown(f"#### Detalhes da Rota: {porto_origem} → {porto_destino}")
        
        detalhes = get_detailed_info(df, data_selecionada, porto_origem, porto_destino)
        if not detalhes.empty:
            # Métricas da rota
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_containers_rota = detalhes['TOTAL_CONTAINERS'].sum()
                st.metric("Containers na Rota", f"{int(total_containers_rota):,}")
            with col2:
                st.metric("Peso Total (ton)", f"{detalhes['PESO BRUTO'].sum():,.2f}")
            with col3:
                st.metric("Empresas", len(detalhes[['REMETENTE', 'DESTINATÁRIO']].nunique()))
            with col4:
                st.metric("Navios", len(detalhes['NAVIO'].unique()))
            
            # Tabela detalhada
            st.markdown("#### Operações na Rota")
            tabela_detalhes = format_detailed_table(detalhes)
            st.dataframe(tabela_detalhes, use_container_width=True)
            
            # Expansores com informações adicionais
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("📊 Tipos de Carga"):
                    dist_carga = detalhes.groupby('TIPO DE CARGA')['TOTAL_CONTAINERS'].sum()
                    dist_carga = dist_carga.apply(lambda x: f"{int(x):,}")
                    st.dataframe(dist_carga)
            with col2:
                with st.expander("🚢 Navios e Armadores"):
                    info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
                    st.dataframe(info_navios)
        else:
            st.info("Não há dados para a rota e data selecionadas")
        
    except Exception as e:
        st.error(f"Erro ao processar os dados: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()