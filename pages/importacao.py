import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles, render_sidebar

# Configuração da página
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
)

apply_styles()
render_sidebar()

@st.cache_data(ttl=3600)
def load_and_process_data():
    """Carrega e processa os dados da planilha."""
    try:
        # ID do arquivo Google Drive armazenado nos secrets
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        # Baixar o arquivo
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)

        # Ler os dados
        df = pd.read_excel(excel_content)

        # Selecionar apenas os campos necessários
        selected_columns = [
            'ETA', 'UF CONSIGNATÁRIO', 'QTDE CONTAINER', 
            'PORTO DESCARGA', 'CONSIGNATÁRIO', 'ARMADOR', 
            'NAVIO', 'PAÍS ORIGEM', 'PORTO ORIGEM'
        ]
        df = df[selected_columns]

        # Garantir processamento correto dos dados
        df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce', dayfirst=True)
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce'
        ).fillna(0)

        # Remover linhas com dados inválidos
        df = df.dropna(subset=['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def display_filtered_details(df, data_selecionada, porto_descarga, uf_consignatario):
    """
    Exibe os detalhes filtrados com base no Porto de Descarga, UF Consignatário e Data.
    """
    # Converter data_selecionada para datetime
    data_datetime = pd.to_datetime(data_selecionada)
    
    # Aplicar os filtros usando apenas a data (sem hora)
    detalhes = df[
        (df['ETA'].dt.date == data_selecionada) &
        (df['PORTO DESCARGA'] == porto_descarga) &
        (df['UF CONSIGNATÁRIO'] == uf_consignatario)
    ]

    if detalhes.empty:
        st.warning(f"Nenhum dado encontrado para o filtro selecionado ({porto_descarga} -> {uf_consignatario}) em {data_selecionada.strftime('%d/%m/%Y')}.")
        return

    # Exibir os detalhes dos containers
    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    detalhes_tabela = detalhes[[
        'CONSIGNATÁRIO', 'ARMADOR', 'NAVIO', 'PAÍS ORIGEM', 
        'PORTO ORIGEM', 'PORTO DESCARGA', 'QTDE CONTAINER'
    ]].copy()

    # Renomear colunas para exibição
    detalhes_tabela.columns = [
        'Consignatário', 'Armador', 'Navio', 'País de Origem', 
        'Porto de Origem', 'Porto de Descarga', 'Quantidade de Containers'
    ]

    # Formatar a quantidade de containers
    detalhes_tabela['Quantidade de Containers'] = detalhes_tabela['Quantidade de Containers'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    # Exibir a tabela
    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def main():
   st.markdown('<h1 class="main-title">🚢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

   if "dataframe" not in st.session_state:
       st.session_state["dataframe"] = load_and_process_data()
   df = st.session_state["dataframe"]

   if df.empty:
       st.warning("Nenhum dado disponível para exibição.")
       return

   dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
   tabela_pivot = dados_pivot.pivot(
       index='ETA', columns='UF CONSIGNATÁRIO', values='QTDE CONTAINER'
   ).fillna(0)

   tabela_pivot = tabela_pivot.sort_index(ascending=False)
   tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

   total_containers = int(tabela_pivot['TOTAL'].sum())
   data_mais_antiga = df['ETA'].min().strftime('%d/%m/%Y')
   data_mais_recente = df['ETA'].max().strftime('%d/%m/%Y')
   range_datas = f"{data_mais_antiga} - {data_mais_recente}"

   col1, col2 = st.columns(2)
   with col1:
       st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}", help="Total de containers no período")
   with col2:
       st.metric("PERÍODO DOS DADOS", range_datas, help="Intervalo de datas dos dados disponíveis")

   col1, col2, col3 = st.columns(3)
   with col1:
       data_mais_antiga_dt = tabela_pivot.index.min()
       data_mais_recente_dt = tabela_pivot.index.max()
       data_selecionada = st.date_input(
           "Data de Chegada",
           min_value=data_mais_antiga_dt,
           max_value=data_mais_recente_dt,
           value=data_mais_recente_dt,
           key="data_chegada"
       )
   with col2:
       portos_descarga = sorted(df['PORTO DESCARGA'].unique())
       porto_descarga = st.selectbox("Porto de Descarga", options=portos_descarga)
   with col3:
       ufs_consignatario = sorted(df['UF CONSIGNATÁRIO'].unique())
       uf_consignatario = st.selectbox("UF Consignatário", options=ufs_consignatario)

   st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)
   tabela_formatada = tabela_pivot.copy().reset_index()
   tabela_formatada['ETA'] = tabela_formatada['ETA'].dt.strftime('%d/%m/%Y')
   st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)   

   if data_selecionada and porto_descarga and uf_consignatario:
       display_filtered_details(df, data_selecionada, porto_descarga, uf_consignatario)

if __name__ == "__main__":
    main()
