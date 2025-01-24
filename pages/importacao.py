import streamlit as st

# O comando set_page_config precisa ser chamado como o primeiro comando Streamlit
st.set_page_config(
    page_title="Previsão de Chegadas",
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

# Aplicação de estilos vem depois da configuração inicial
apply_styles()

# Sidebar navigation
if st.sidebar.button("🏠 Home", key="home_btn", use_container_width=True):
    st.switch_page("Home.py")
if st.sidebar.button("📢 Cabotagem", key="cab_side_btn", use_container_width=True):
    st.switch_page("pages/cabotagem.py")
if st.sidebar.button("📦 Exportação", key="exp_side_btn", use_container_width=True):
    st.switch_page("pages/exportacao.py")
if st.sidebar.button("📥 Importação", key="imp_side_btn", use_container_width=True):
    st.switch_page("pages/importacao.py")

@st.cache_data(ttl=3600)
def load_and_process_data():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)
        
        df = pd.read_excel(excel_content)
        
        df.columns = df.columns.str.strip()
        
        # Mapeamento correto considerando campos separados
        column_map = {
            'ETA': 'ETA',
            'UF CONSIGNATÁRIO': 'UF CONSIGNATÁRIO',
            'QTDE CONTAINER': 'QTDE CONTAINER',
            'PORTO DESCARGA': 'PORTO DESCARGA',
            'CONSIGNATARIO FINAL': 'CONSIGNATARIO FINAL',
            'CONSOLIDADOR': 'CONSOLIDADOR',
            'TERMINAL DESCARGA': 'TERMINAL DESCARGA',
            'NOME EXPORTADOR': 'NOME EXPORTADOR',
            'ARMADOR': 'ARMADOR',
            'AGENTE INTERNACIONAL': 'AGENTE INTERNACIONAL',
            'NAVIO': 'NAVIO'
        }
        
        rename_dict = {old: new for old, new in column_map.items() if old in df.columns}
        df = df.rename(columns=rename_dict)
        
        if 'ETA' in df.columns:
            df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce')
            
        if 'QTDE CONTAINER' in df.columns:
            df['QTDE CONTAINER'] = pd.to_numeric(df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce').fillna(0)
        
        required_cols = ['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA']
        existing_required = [col for col in required_cols if col in df.columns]
        if existing_required:
            df = df.dropna(subset=existing_required)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()
    
def calcular_total_importacao():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)
        
        df = pd.read_excel(excel_content)
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce'
        ).fillna(0)
        
        return int(df['QTDE CONTAINER'].sum())
    except Exception as e:
        st.error(f"Erro ao calcular total de importação: {e}")
        return 0

def display_filtered_details(df, data_inicial, data_final, filtros):
    detalhes = df.copy()
    
    detalhes = detalhes[
        (detalhes['ETA'].dt.date >= data_inicial) &
        (detalhes['ETA'].dt.date <= data_final)
    ]
    
    for coluna, valor in filtros.items():
        if valor and valor != "Todos" and coluna in detalhes.columns:
            detalhes = detalhes[detalhes[coluna] == valor]

    if detalhes.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas = [col for col in [
        'ETA', 'CONSIGNATARIO FINAL', 'CONSOLIDADOR', 'CONSIGNATÁRIO',
        'TERMINAL DESCARGA', 'NOME EXPORTADOR', 'ARMADOR',
        'AGENTE INTERNACIONAL', 'NAVIO', 'PAÍS ORIGEM', 'PORTO ORIGEM',
        'UF CONSIGNATÁRIO', 'PORTO DESCARGA', 'QTDE CONTAINER'
    ] if col in detalhes.columns]
    
    detalhes_tabela = detalhes[colunas].copy()
    detalhes_tabela['ETA'] = detalhes_tabela['ETA'].dt.strftime('%d/%m/%Y')
    detalhes_tabela['QTDE CONTAINER'] = detalhes_tabela['QTDE CONTAINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def create_dropdown(label, df_column, key):
    if df_column is None:
        return "Todos"
    options = df_column.dropna().unique().tolist()
    options = [str(opt) for opt in options]
    return st.selectbox(label, ['Todos'] + sorted(options), key=key)

def main():
    st.markdown('<h1 class="main-title">📢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    if df.empty:
        st.warning("Nenhum dado disponível para exibição.")
        return

    # Métricas principais
    total_containers = int(df['QTDE CONTAINER'].sum()) if 'QTDE CONTAINER' in df.columns else 0
    data_mais_antiga = df['ETA'].min().strftime('%d/%m/%Y')
    data_mais_recente = df['ETA'].max().strftime('%d/%m/%Y')
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
        data_mais_antiga_dt = df['ETA'].min().date()
        data_mais_recente_dt = df['ETA'].max().date()
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

    # Filtros Primários
    col1, col2, col3 = st.columns(3)
    with col1:
        uf_selecionada = create_dropdown("UF Consignatário", df.get('UF CONSIGNATÁRIO'), "uf")
    with col2:
        porto_selecionado = create_dropdown("Porto de Descarga", df.get('PORTO DESCARGA'), "porto")
    with col3:
        armador_selecionado = create_dropdown("Armador", df.get('ARMADOR'), "armador")

    # Filtros Secundários
    with st.expander("Filtros Adicionais", expanded=False):
        col4, col5, col6 = st.columns(3)
        with col4:
            consig_final = create_dropdown("Consignatário Final", df.get('CONSIGNATARIO FINAL'), "consig_final")
        with col5:
            consolidador = create_dropdown("Consolidador", df.get('CONSOLIDADOR'), "consolidador")
        with col6:
            consignatario = create_dropdown("Consignatário", df.get('CONSIGNATÁRIO'), "consignatario")

        col7, col8, col9 = st.columns(3)
        with col7:
            terminal = create_dropdown("Terminal Descarga", df.get('TERMINAL DESCARGA'), "terminal")
        with col8:
            exportador = create_dropdown("Nome Exportador", df.get('NOME EXPORTADOR'), "exportador")
        with col9:
            agente = create_dropdown("Agente Internacional", df.get('AGENTE INTERNACIONAL'), "agente")

    # Aplicar filtros ao DataFrame
    df_filtrado = df.copy()
    
    # Filtros de data
    df_filtrado = df_filtrado[
        (df_filtrado['ETA'].dt.date >= data_inicial) &
        (df_filtrado['ETA'].dt.date <= data_final)
    ]
    
    # Outros filtros
    filtros = {
        'UF CONSIGNATÁRIO': uf_selecionada,
        'PORTO DESCARGA': porto_selecionado,
        'ARMADOR': armador_selecionado,
        'CONSIGNATARIO FINAL': consig_final,
        'CONSOLIDADOR': consolidador,
        'CONSIGNATÁRIO': consignatario,
        'TERMINAL DESCARGA': terminal,
        'NOME EXPORTADOR': exportador,
        'AGENTE INTERNACIONAL': agente
    }
    
    for coluna, valor in filtros.items():
        if valor != "Todos" and coluna in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[coluna] == valor]

    # Tabela pivot
    dados_pivot = df_filtrado.groupby(['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])['QTDE CONTAINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot_table(
        index='ETA',
        columns=['UF CONSIGNATÁRIO', 'PORTO DESCARGA'],
        values='QTDE CONTAINER',
        aggfunc='sum'
    ).fillna(0)

    tabela_pivot = tabela_pivot.sort_index(ascending=False)
    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)
    tabela_formatada = tabela_pivot.copy().reset_index()
    tabela_formatada['ETA'] = tabela_formatada['ETA'].dt.strftime('%d/%m/%Y')
    st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

    # Detalhes dos containers
    display_filtered_details(df, data_inicial, data_final, filtros)

if __name__ == "__main__":
    main()