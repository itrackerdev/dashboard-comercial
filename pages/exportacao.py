import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles, render_sidebar

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
    try:
        file_id = st.secrets["urls"]["planilha_exportacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)

        df = pd.read_excel(excel_content)
        
        selected_columns = [
            'DATA EMBARQUE', 'ESTADO EXPORTADOR', 'QTDE CONTEINER', 'PORTO EMBARQUE',
            'NOME EXPORTADOR', 'ARMADOR', 'NAVIO', 'PORTO DE ORIGEM', 'TERMINAL EMBARQUE',
            'PORTO DESCARGA', 'PORTO DE DESTINO', 'PAÍS DE DESTINO', 'CIDADE EXPORTADOR'
        ]
        df = df[selected_columns]
        
        df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')
        df['QTDE CONTEINER'] = pd.to_numeric(
            df['QTDE CONTEINER'].str.replace(',', '.'), errors='coerce'
        ).fillna(0)
        
        df = df.dropna(subset=['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def display_filtered_details(df, data_selecionada, porto_embarque, estado_exportador):
    df_dates = df['DATA EMBARQUE'].dt.strftime('%Y-%m-%d')
    selected_date = data_selecionada.strftime('%Y-%m-%d')
    
    detalhes = df[
        (df_dates == selected_date) &
        (df['ESTADO EXPORTADOR'] == estado_exportador)&
        (df['PORTO EMBARQUE'] == porto_embarque) 
    ]

    if detalhes.empty:
        st.warning(f"Nenhum dado encontrado para o filtro selecionado ({porto_embarque} -> {estado_exportador}) em {data_selecionada.strftime('%d/%m/%Y')}.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas = [
        'NOME EXPORTADOR', 'NAVIO', 'PORTO DE ORIGEM', 'PORTO EMBARQUE',
        'TERMINAL EMBARQUE', 'PORTO DESCARGA', 'PORTO DE DESTINO', 
        'PAÍS DE DESTINO', 'CIDADE EXPORTADOR', 'ESTADO EXPORTADOR',
        'ARMADOR', 'QTDE CONTEINER'
    ]
    
    detalhes_tabela = detalhes[colunas].copy()

    # Formatando quantidade de containers
    detalhes_tabela['QTDE CONTEINER'] = detalhes_tabela['QTDE CONTEINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def main():
    st.markdown('<h1 class="main-title">🚢 Previsão de Exportações de Containers</h1>', unsafe_allow_html=True)

    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    if df.empty:
        st.warning("Nenhum dado disponível para exibição.")
        return

    dados_pivot = df.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR'])['QTDE CONTEINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot(
        index='DATA EMBARQUE',
        columns='ESTADO EXPORTADOR',
        values='QTDE CONTEINER'
    ).fillna(0)

    tabela_pivot = tabela_pivot.sort_index(ascending=False)
    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    total_containers = int(tabela_pivot['TOTAL'].sum())
    data_mais_antiga = df['DATA EMBARQUE'].min().strftime('%d/%m/%Y')
    data_mais_recente = df['DATA EMBARQUE'].max().strftime('%d/%m/%Y')
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
            "Data de Embarque",
            min_value=data_mais_antiga_dt,
            max_value=data_mais_recente_dt,
            value=data_mais_recente_dt,
            key="data_embarque"
        )
    with col2:
        estados_exportador = sorted(df['ESTADO EXPORTADOR'].unique())
        estado_exportador = st.selectbox("Estado Exportador", options=estados_exportador)
    with col3:
        portos_embarque = sorted(df['PORTO EMBARQUE'].unique())
        porto_embarque = st.selectbox("Porto de Embarque", options=portos_embarque)

    st.markdown('<h3 class="subheader">Previsão de Embarques por Estado</h3>', unsafe_allow_html=True)
    tabela_formatada = tabela_pivot.copy().reset_index()
    tabela_formatada['DATA EMBARQUE'] = tabela_formatada['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
    st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

    if data_selecionada and porto_embarque and estado_exportador:
        display_filtered_details(df, data_selecionada, porto_embarque, estado_exportador)

if __name__ == "__main__":
    main()