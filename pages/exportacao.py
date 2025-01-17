import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import requests
from io import BytesIO

st.set_page_config(
    page_title="Previsão de Exportações",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

def create_unique_id(row):
    """Cria um ID único para cada registro baseado em campos chave"""
    unique_string = f"{row['DATA EMBARQUE']}_{row['NOME EXPORTADOR']}_{row['CONSIGNATÁRIO']}_{row['NAVIO']}_{row['VIAGEM']}_{row['PORTO EMBARQUE']}_{row['PORTO DESCARGA']}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def remove_duplicates(df):
    """Remove registros duplicados mantendo apenas a versão mais recente"""
    # Criando ID único para cada registro
    df['ID_UNICO'] = df.apply(create_unique_id, axis=1)
    
    # Adicionando DATA CONSULTA ao DataFrame carregado, caso não exista
    if 'DATA CONSULTA' not in df.columns:
        df['DATA CONSULTA'] = datetime.now()
    
    # Verificar se o arquivo consolidado existe
    if os.path.exists('dados_exportacao_consolidados.parquet'):
        df_consolidated = pd.read_parquet('dados_exportacao_consolidados.parquet')
        
        # Garantindo que o consolidado possua a coluna DATA CONSULTA
        if 'DATA CONSULTA' not in df_consolidated.columns:
            df_consolidated['DATA CONSULTA'] = datetime.now() - timedelta(days=1)
        
        # Concatenando os dados e removendo duplicados
        df_all = pd.concat([df_consolidated, df])
        df_all = df_all.sort_values('DATA CONSULTA').drop_duplicates(
            subset=['ID_UNICO'], 
            keep='last'
        )
    else:
        df_all = df
    
    # Salvando o arquivo consolidado atualizado
    df_all.to_parquet('dados_exportacao_consolidados.parquet')
    
    # Log de atualizações
    with open('log_atualizacao_exportacao.txt', 'a') as f:
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
        file_id = st.secrets["urls"]["planilha_exportacao"]
        
        # Baixando o arquivo
        excel_content = download_file_from_drive(file_id)
        if excel_content is None:
            return pd.DataFrame()
        
        # Lendo o arquivo Excel
        df = pd.read_excel(excel_content)
        
        # Convertendo datas
        df['DATA CONSULTA'] = pd.to_datetime(df['DATA CONSULTA'], format='%d/%m/%Y', dayfirst=True)
        df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')
        
        # Convertendo quantidade de contêineres
        df['QTDE CONTEINER'] = pd.to_numeric(df['QTDE CONTEINER'].str.replace(',', '.'), errors='coerce')
        df['QTDE CONTEINER'] = df['QTDE CONTEINER'].fillna(0)
        
        # Removendo duplicatas e processando
        df = remove_duplicates(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()

def get_detailed_info(df, data, uf):
    """Retorna informações detalhadas para uma data e UF específicas"""
    mask = (df['DATA EMBARQUE'].dt.date == data.date()) & (df['ESTADO EXPORTADOR'] == uf)
    return df[mask]

def format_detailed_table(df_filtered):
    """Formata a tabela de detalhes com as informações relevantes"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Selecionando e renomeando colunas relevantes
    colunas_exibir = {
        'TERMINAL EMBARQUE': 'Terminal',
        'NOME EXPORTADOR': 'Empresa',
        'ATIVIDADE EXPORTADOR': 'Atividade',
        'NAVIO': 'Navio',
        'ARMADOR': 'Armador',
        'AGENTE DE CARGA': 'Agente de Carga',
        'CONSIGNATÁRIO': 'Consignatário',
        'QTDE CONTEINER': 'Containers',
        'TIPO CONTEINER': 'Tipo',
        'MERCADORIA': 'Mercadoria',
        'PAÍS DE DESTINO': 'País Destino'
    }
    
    df_detalhes = df_filtered[colunas_exibir.keys()].copy()
    df_detalhes.columns = colunas_exibir.values()
    
    # Formatando o número de containers
    df_detalhes['Containers'] = df_detalhes['Containers'].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
    
    return df_detalhes

def show_update_info():
    """Exibe informações sobre as atualizações dos dados"""
    if os.path.exists('log_atualizacao_exportacao.txt'):
        with open('log_atualizacao_exportacao.txt', 'r') as f:
            last_updates = f.readlines()[-5:]  # Mostra as últimas 5 atualizações
        st.sidebar.markdown("### Últimas Atualizações")
        for update in last_updates:
            st.text(update.strip())

def main():
    st.title("📦 Previsão de Exportações por Estado")
    
    try:
        # Carregando dados
        df = load_and_process_data()
        
        if df.empty:
            st.warning("Não foi possível carregar os dados.")
            return
            
        # Exibindo informações sobre a última atualização
        ultima_atualizacao = df['DATA CONSULTA'].max()
        
        # Informações na página principal
        st.markdown("### 🔄 Status dos Dados")
        st.markdown(f"Última atualização: {ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}")
        st.markdown(f"Total de registros únicos: {len(df)}")
        
        # Criando tabela pivot inicial
        dados_pivot = df.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR'])['QTDE CONTEINER'].sum().reset_index()
        tabela_pivot = dados_pivot.pivot(
            index='DATA EMBARQUE',
            columns='ESTADO EXPORTADOR',
            values='QTDE CONTEINER'
        ).fillna(0)
        
        # Adicionando total por dia
        tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)
        
        # Formatando a tabela principal
        tabela_formatada = tabela_pivot.copy()
        for coluna in tabela_formatada.columns:
            tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
        
        # Convertendo índice para data formatada
        tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')
        
        # Exibindo a tabela principal
        st.markdown("### Previsão de Exportações por Estado")
        st.markdown("*Selecione uma data e estado para ver os detalhes*")
        
        # Criando seletor de data e UF
        col1, col2 = st.columns(2)
        with col1:
            data_selecionada = st.selectbox(
                "Selecione a Data",
                options=pd.to_datetime(tabela_formatada.index, format='%d/%m/%Y'),
                format_func=lambda x: x.strftime('%d/%m/%Y')
            )
        with col2:
            uf_selecionada = st.selectbox(
                "Selecione o Estado",
                options=[col for col in tabela_pivot.columns if col != 'TOTAL']
            )
        
        # Exibindo tabela principal
        st.dataframe(
            tabela_formatada,
            use_container_width=True,
            height=400
        )
        
        # Exibindo detalhes se data e UF foram selecionados
        if data_selecionada and uf_selecionada:
            st.markdown(f"### Detalhes para {uf_selecionada} - {data_selecionada.strftime('%d/%m/%Y')}")

            detalhes = get_detailed_info(df, data_selecionada, uf_selecionada)
            if not detalhes.empty:
                tabela_detalhes = format_detailed_table(detalhes)
                
                # Sumário
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Containers", 
                             f"{int(detalhes['QTDE CONTEINER'].sum()):,}")
                with col2:
                    st.metric("Número de Exportadores", 
                             len(detalhes['NOME EXPORTADOR'].unique()))
                with col3:
                    st.metric("Países de Destino", 
                             len(detalhes['PAÍS DE DESTINO'].unique()))
                with col4:
                    st.metric("Terminais", 
                             len(detalhes['TERMINAL EMBARQUE'].unique()))
                
                # Tabela de detalhes
                st.dataframe(
                    tabela_detalhes,
                    use_container_width=True,
                    height=400
                )
                
                # Informações adicionais em expansores
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.expander("📊 Distribuição por Terminal"):
                        dist_terminal = detalhes.groupby('TERMINAL EMBARQUE')['QTDE CONTEINER'].sum()
                        st.dataframe(dist_terminal)
                
                with col2:
                    with st.expander("🌎 Países de Destino"):
                        dist_paises = detalhes.groupby('PAÍS DE DESTINO')['QTDE CONTEINER'].sum()
                        st.dataframe(dist_paises)
                
                with st.expander("🚢 Informações dos Navios"):
                    info_navios = detalhes[['NAVIO', 'ARMADOR', 'PORTO DESCARGA']].drop_duplicates()
                    st.dataframe(info_navios)
                
                with st.expander("📦 Tipos de Carga"):
                    tipos_carga = detalhes.groupby(['MERCADORIA', 'TIPO CONTEINER'])['QTDE CONTEINER'].sum()
                    st.dataframe(tipos_carga)
            else:
                st.info("Não há dados para a seleção especificada")
        
        # Exibindo informações sobre as atualizações dos dados
        show_update_info()
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")

if __name__ == "__main__":
    main()
