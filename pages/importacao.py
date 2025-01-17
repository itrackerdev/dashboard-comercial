import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

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
        file_id = st.secrets["urls"]["planilha_importacao"]
        
        # Baixando o arquivo
        excel_content = download_file_from_drive(file_id)
        if excel_content is None:
            return pd.DataFrame()
        
        # Lendo o arquivo Excel
        df = pd.read_excel(excel_content)
        
        # Convertendo datas e quantidades
        df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
        df['QTDE CONTAINER'] = df['QTDE CONTAINER'].str.replace(',', '.').astype(float)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()

def get_detailed_info(df, data, uf):
    """Retorna informações detalhadas para uma data e UF específicas"""
    mask = (df['ETA'].dt.date == data.date()) & (df['UF CONSIGNATÁRIO'] == uf)
    return df[mask]

def format_detailed_table(df_filtered):
    """Formata a tabela de detalhes com as informações relevantes"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Selecionando e renomeando colunas relevantes
    colunas_exibir = {
        'TERMINAL DESCARGA': 'Terminal',
        'CONSIGNATÁRIO': 'Empresa',
        'EMAIL': 'Email',
        'TELEFONE': 'Telefone',
        'NAVIO': 'Navio',
        'ARMADOR': 'Armador',
        'AGENTE DE CARGA': 'Agente de Carga',
        'CONSOLIDADOR': 'Consolidador',
        'QTDE CONTAINER': 'Containers',
        'TIPO CONTAINER': 'Tipo',
        'MERCADORIA': 'Mercadoria'
    }
    
    df_detalhes = df_filtered[colunas_exibir.keys()].copy()
    df_detalhes.columns = colunas_exibir.values()
    
    # Formatando o número de containers
    df_detalhes['Containers'] = df_detalhes['Containers'].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
    
    return df_detalhes

def main():
    st.title("📦 Previsão de Chegadas de Containers")
    
    try:
        # Carregando dados
        df = load_and_process_data()
        
        # Criando tabela pivot inicial
        dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
        tabela_pivot = dados_pivot.pivot(
            index='ETA',
            columns='UF CONSIGNATÁRIO',
            values='QTDE CONTAINER'
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
        st.markdown("### Previsão de Chegadas por Estado")
        st.markdown("*Clique em qualquer número para ver os detalhes*")
        
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
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Containers", 
                             f"{int(detalhes['QTDE CONTAINER'].sum()):,}")
                with col2:
                    st.metric("Número de Empresas", 
                             len(detalhes['CONSIGNATÁRIO'].unique()))
                with col3:
                    st.metric("Terminais", 
                             len(detalhes['TERMINAL DESCARGA'].unique()))
                
                # Tabela de detalhes
                st.dataframe(
                    tabela_detalhes,
                    use_container_width=True,
                    height=400
                )
                
                # Informações adicionais em expansores
                with st.expander("📊 Distribuição por Terminal"):
                    dist_terminal = detalhes.groupby('TERMINAL DESCARGA')['QTDE CONTAINER'].sum()
                    st.dataframe(dist_terminal)
                
                with st.expander("🚢 Informações dos Navios"):
                    info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
                    st.dataframe(info_navios)
            else:
                st.info("Não há dados para a seleção especificada")
        
    except Exception as e:
        st.error(f"Erro ao processar os dados: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()