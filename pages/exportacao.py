import streamlit as st

# O comando set_page_config precisa ser chamado como o primeiro comando Streamlit
st.set_page_config(
    page_title="Previsão de Exportações",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
)

# Importações restantes e funções de estilo
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles

# Chama estilos após a configuração da página
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
    """
    Função para carregar e processar os dados da planilha de exportação.
    """
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
        
        # Normalizar e processar as colunas
        df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')
        df['QTDE CONTEINER'] = pd.to_numeric(
            df['QTDE CONTEINER'].astype(str).str.replace(',', '.'), errors='coerce'
        ).fillna(0)
        
        # Remover linhas com valores essenciais ausentes
        df = df.dropna(subset=['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def calcular_total_exportacao(df=None):
    """
    Função para calcular o total de contêineres na exportação.
    Retorna o total de contêineres com base nos dados processados.
    """
    try:
        if df is None:
            df = load_and_process_data()
        if 'QTDE CONTEINER' not in df.columns:
            raise KeyError("Coluna 'QTDE CONTEINER' não encontrada nos dados.")
        return int(df['QTDE CONTEINER'].sum())
    except Exception as e:
        st.error(f"Erro ao calcular total de exportação: {e}")
        return 0

def display_filtered_details(df, data_inicial, data_final, filtros):
    """
    Exibe os detalhes dos contêineres filtrados por data e outros critérios.
    """
    detalhes = df.copy()
    
    # Aplicando filtro de datas
    detalhes = detalhes[
        (detalhes['DATA EMBARQUE'].dt.date >= data_inicial) &
        (detalhes['DATA EMBARQUE'].dt.date <= data_final)
    ]
    
    # Aplicando outros filtros
    for coluna, valor in filtros.items():
        if valor and valor != "Todos" and coluna in detalhes.columns:
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

def create_dropdown(label, df_column, key):
    """
    Cria um dropdown para seleção de filtros.
    """
    if df_column is None:
        return "Todos"
    options = df_column.dropna().unique().tolist()
    options = [str(opt) for opt in options]
    return st.selectbox(label, ['Todos'] + sorted(options), key=key)

def main():
    
    st.markdown('<h1 class="main-title">🚢 Previsão de Exportações de Containers</h1>', unsafe_allow_html=True)

    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    if df.empty:
        st.warning("Nenhum dado disponível para exibição.")
        return

    # Métricas principais
    total_containers = calcular_total_exportacao(df)
    data_mais_antiga = df['DATA EMBARQUE'].min().strftime('%d/%m/%Y')
    data_mais_recente = df['DATA EMBARQUE'].max().strftime('%d/%m/%Y')
    range_datas = f"{data_mais_antiga} - {data_mais_recente}"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}", help="Total de containers no período")
    with col2:
        st.metric("PERÍODO DOS DADOS", range_datas, help="Intervalo de datas dos dados disponíveis")

    # Filtros principais
    st.markdown('<h3 class="subheader">Filtros</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input(
            "Data Inicial", value=df['DATA EMBARQUE'].min().date(), key="data_inicial"
        )
    with col2:
        data_final = st.date_input(
            "Data Final", value=df['DATA EMBARQUE'].max().date(), key="data_final"
        )

    # Filtros adicionais
    col1, col2, col3 = st.columns(3)
    with col1:
        estado_selecionado = create_dropdown("Estado Exportador", df.get('ESTADO EXPORTADOR'), "estado")
    with col2:
        porto_selecionado = create_dropdown("Porto de Embarque", df.get('PORTO EMBARQUE'), "porto")
    with col3:
        armador_selecionado = create_dropdown("Armador", df.get('ARMADOR'), "armador")

    filtros = {
        'ESTADO EXPORTADOR': estado_selecionado,
        'PORTO EMBARQUE': porto_selecionado,
        'ARMADOR': armador_selecionado,
    }

    # Aplicar filtros
    df_filtrado = df.copy()
    for coluna, valor in filtros.items():
        if valor != "Todos":
            df_filtrado = df_filtrado[df_filtrado[coluna] == valor]

    df_filtrado = df_filtrado[
        (df_filtrado['DATA EMBARQUE'].dt.date >= data_inicial) &
        (df_filtrado['DATA EMBARQUE'].dt.date <= data_final)
    ]

    # Pivot table
    dados_pivot = df_filtrado.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])['QTDE CONTEINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot_table(
        index='DATA EMBARQUE',
        columns=['ESTADO EXPORTADOR', 'PORTO EMBARQUE'],
        values='QTDE CONTEINER',
        aggfunc='sum'
    ).fillna(0)

    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    st.markdown('<h3 class="subheader">Previsão de Embarques por Estado e Porto</h3>', unsafe_allow_html=True)
    st.dataframe(tabela_pivot.reset_index(), use_container_width=True, hide_index=True)

    # Detalhes
    display_filtered_details(df_filtrado, data_inicial, data_final, filtros)


if __name__ == "__main__":
    main()
