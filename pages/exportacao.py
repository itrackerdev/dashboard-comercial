import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles

st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
)

apply_styles()

# Sidebar navigation
if st.sidebar.button("🏠 Home", key="home_btn", use_container_width=True):
    st.switch_page("Home.py")
if st.sidebar.button("🚢 Cabotagem", key="cab_side_btn", use_container_width=True):
    st.switch_page("pages/cabotagem.py")
if st.sidebar.button("📦 Exportação", key="exp_side_btn", use_container_width=True):
    st.switch_page("pages/exportacao.py")
if st.sidebar.button("📥 Importação", key="imp_side_btn", use_container_width=True):
    st.switch_page("pages/importacao.py")

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

def display_filtered_details(df, data_inicial, data_final, filtros):
    detalhes = df.copy()
    
    # Aplicando filtro de datas
    detalhes = detalhes[
        (detalhes['DATA EMBARQUE'].dt.date >= data_inicial) &
        (detalhes['DATA EMBARQUE'].dt.date <= data_final)
    ]
    
    # Aplicando outros filtros
    for coluna, valor in filtros.items():
        if valor and valor != "Todos":
            detalhes = detalhes[detalhes[coluna] == valor]

    if detalhes.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas = [
        'DATA EMBARQUE', 'NOME EXPORTADOR', 'NAVIO', 'PORTO DE ORIGEM', 'PORTO EMBARQUE',
        'TERMINAL EMBARQUE', 'PORTO DESCARGA', 'PORTO DE DESTINO', 
        'PAÍS DE DESTINO', 'CIDADE EXPORTADOR', 'ESTADO EXPORTADOR',
        'ARMADOR', 'QTDE CONTEINER'
    ]
    
    detalhes_tabela = detalhes[colunas].copy()
    detalhes_tabela['DATA EMBARQUE'] = detalhes_tabela['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
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

    # Métricas principais
    total_containers = int(df['QTDE CONTEINER'].sum())
    data_mais_antiga = df['DATA EMBARQUE'].min().strftime('%d/%m/%Y')
    data_mais_recente = df['DATA EMBARQUE'].max().strftime('%d/%m/%Y')
    range_datas = f"{data_mais_antiga} - {data_mais_recente}"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}", help="Total de containers no período")
    with col2:
        st.metric("PERÍODO DOS DADOS", range_datas, help="Intervalo de datas dos dados disponíveis")

    # Filtros
    st.markdown('<h3 class="subheader">Filtros</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        data_mais_antiga_dt = df['DATA EMBARQUE'].min().date()
        data_mais_recente_dt = df['DATA EMBARQUE'].max().date()
        data_inicial = st.date_input(
            "Data Inicial",
            min_value=data_mais_antiga_dt,
            max_value=data_mais_recente_dt,
            value=data_mais_antiga_dt,
            key="data_inicial"
        )
    with col2:
        data_final = st.date_input(
            "Data Final",
            min_value=data_mais_antiga_dt,
            max_value=data_mais_recente_dt,
            value=data_mais_recente_dt,
            key="data_final"
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        estados = ["Todos"] + sorted(df['ESTADO EXPORTADOR'].unique().tolist())
        estado_selecionado = st.selectbox("Estado Exportador", options=estados)
    
    with col2:
        portos = ["Todos"] + sorted(df['PORTO EMBARQUE'].unique().tolist())
        porto_selecionado = st.selectbox("Porto de Embarque", options=portos)
    
    with col3:
        armadores = ["Todos"] + sorted(df['ARMADOR'].unique().tolist())
        armador_selecionado = st.selectbox("Armador", options=armadores)

    # Tabela pivot
    df_filtrado = df.copy()

    # Aplicar filtros
    if estado_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['ESTADO EXPORTADOR'] == estado_selecionado]
    if porto_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['PORTO EMBARQUE'] == porto_selecionado]
    if armador_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['ARMADOR'] == armador_selecionado]

    # Filtrar por intervalo de datas
    df_filtrado = df_filtrado[
        (df_filtrado['DATA EMBARQUE'].dt.date >= data_inicial) &
        (df_filtrado['DATA EMBARQUE'].dt.date <= data_final)
    ]

    # Agrupamento e criação de dados para a tabela pivot
    dados_pivot = df_filtrado.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])['QTDE CONTEINER'].sum().reset_index()

    # Criar a tabela pivot com índices, colunas combinadas e valores
    tabela_pivot = dados_pivot.pivot_table(
        index='DATA EMBARQUE',
        columns=['ESTADO EXPORTADOR', 'PORTO EMBARQUE'],
        values='QTDE CONTEINER',
        aggfunc='sum'
    ).fillna(0)

    # Ordenar e adicionar a coluna TOTAL
    tabela_pivot = tabela_pivot.sort_index(ascending=False)
    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    # Exibir no Streamlit
    st.markdown('<h3 class="subheader">Previsão de Embarques por Estado e Porto</h3>', unsafe_allow_html=True)
    tabela_formatada = tabela_pivot.copy().reset_index()
    tabela_formatada['DATA EMBARQUE'] = tabela_formatada['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
    st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

    # Detalhes dos containers
    filtros = {
        'ESTADO EXPORTADOR': estado_selecionado,
        'PORTO EMBARQUE': porto_selecionado,
        'ARMADOR': armador_selecionado
    }
    display_filtered_details(df, data_inicial, data_final, filtros)

if __name__ == "__main__":
    main()