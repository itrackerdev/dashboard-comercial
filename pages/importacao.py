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

def create_dropdown(label, df_column, key):
    """Cria um dropdown simples com tratamento para valores nulos"""
    options = df_column.dropna().unique().tolist()
    options = [str(opt) for opt in options]
    return st.selectbox(label, ['Todos'] + sorted(options), key=key)

@st.cache_data(ttl=3600)
def load_and_process_data():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)

        df = pd.read_excel(excel_content)

        selected_columns = [
            'ETA', 'UF CONSIGNATÁRIO', 'QTDE CONTAINER', 
            'PORTO DESCARGA', 'CONSIGNATARIO FINAL', 'CONSOLIDADOR',
            'CONSIGNATÁRIO', 'TERMINAL DESCARGA', 'NOME EXPORTADOR',
            'ARMADOR', 'AGENTE INTERNACIONAL', 'NOME IMPORTADOR',
            'NAVIO', 'PAÍS ORIGEM', 'PORTO ORIGEM'
        ]
        df = df[selected_columns]

        df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce', dayfirst=True)
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce'
        ).fillna(0)

        df = df.dropna(subset=['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def display_filtered_details(df, filters):
    mask = (df['ETA'].dt.date >= filters['data_inicio']) & \
           (df['ETA'].dt.date <= filters['data_fim'])
    
    if filters['porto_descarga'] != 'Todos':
        mask &= (df['PORTO DESCARGA'] == filters['porto_descarga'])
    if filters['uf_consignatario'] != 'Todos':
        mask &= (df['UF CONSIGNATÁRIO'] == filters['uf_consignatario'])
    
    filter_columns = {
        'CONSIGNATARIO FINAL': 'consignatario_final',
        'CONSOLIDADOR': 'consolidador',
        'CONSIGNATÁRIO': 'consignatario',
        'TERMINAL DESCARGA': 'terminal_descarga',
        'NOME EXPORTADOR': 'nome_exportador',
        'ARMADOR': 'armador',
        'AGENTE INTERNACIONAL': 'agente_internacional',
        'NOME IMPORTADOR': 'nome_importador'
    }
    
    for col, filter_key in filter_columns.items():
        if filters[filter_key] != 'Todos':
            mask &= (df[col] == filters[filter_key])
    
    detalhes = df[mask]
    
    if detalhes.empty:
        st.warning(f"Nenhum dado encontrado para os filtros selecionados no período de {filters['data_inicio'].strftime('%d/%m/%Y')} a {filters['data_fim'].strftime('%d/%m/%Y')}.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas_exibicao = [
        'CONSIGNATARIO FINAL', 'CONSOLIDADOR', 'CONSIGNATÁRIO', 
        'TERMINAL DESCARGA', 'NOME EXPORTADOR', 'ARMADOR',
        'AGENTE INTERNACIONAL', 'NOME IMPORTADOR', 'QTDE CONTAINER'
    ]
    
    detalhes_tabela = detalhes[colunas_exibicao].copy()
    detalhes_tabela['QTDE CONTAINER'] = detalhes_tabela['QTDE CONTAINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def main():
    st.markdown('<h1 class="main-title">🚢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    if df.empty:
        st.warning("Nenhum dado disponível para exibição.")
        return

    dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])['QTDE CONTAINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot_table(
        index='ETA',
        columns=['UF CONSIGNATÁRIO', 'PORTO DESCARGA'],
        values='QTDE CONTAINER',
        aggfunc='sum'
    ).fillna(0)

    tabela_pivot = tabela_pivot.sort_index(ascending=False)
    
    # Adicionar total
    totais_por_linha = tabela_pivot.sum(axis=1)
    tabela_pivot['TOTAL'] = totais_por_linha

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
        datas = st.date_input(
            "Período",
            [data_mais_recente_dt, data_mais_recente_dt],
            min_value=data_mais_antiga_dt,
            max_value=data_mais_recente_dt,
        )
        if len(datas) == 2:
            data_inicio, data_fim = datas
        else:
            data_inicio = data_fim = datas[0]
    with col2:
        portos_descarga = ['Todos'] + sorted(df['PORTO DESCARGA'].unique().tolist())
        porto_descarga = st.selectbox("Porto de Descarga", options=portos_descarga)
    with col3:
        ufs_consignatario = ['Todos'] + sorted(df['UF CONSIGNATÁRIO'].unique().tolist())
        uf_consignatario = st.selectbox("UF Consignatário", options=ufs_consignatario)

    # Segunda linha de filtros
    col4, col5, col6 = st.columns(3)
    with col4:
        consignatario_final = create_dropdown(
            "Consignatário Final",
            df['CONSIGNATARIO FINAL'],
            "consig_final"
        )
    with col5:
        consolidador = create_dropdown(
            "Consolidador",
            df['CONSOLIDADOR'],
            "consolidador"
        )
    with col6:
        consignatario = create_dropdown(
            "Consignatário",
            df['CONSIGNATÁRIO'],
            "consignatario"
        )

    # Terceira linha de filtros
    col7, col8, col9 = st.columns(3)
    with col7:
        terminal_descarga = create_dropdown(
            "Terminal Descarga",
            df['TERMINAL DESCARGA'],
            "terminal"
        )
    with col8:
        nome_exportador = create_dropdown(
            "Nome Exportador",
            df['NOME EXPORTADOR'],
            "exportador"
        )
    with col9:
        armador = create_dropdown(
            "Armador",
            df['ARMADOR'],
            "armador"
        )

    # Quarta linha de filtros
    col10, col11 = st.columns(2)
    with col10:
        agente_internacional = create_dropdown(
            "Agente Internacional",
            df['AGENTE INTERNACIONAL'],
            "agente"
        )
    with col11:
        nome_importador = create_dropdown(
            "Nome Importador",
            df['NOME IMPORTADOR'],
            "importador"
        )

    st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)
    tabela_formatada = tabela_pivot.copy().reset_index()
    tabela_formatada['ETA'] = tabela_formatada['ETA'].dt.strftime('%d/%m/%Y')
    st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

    filters = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'porto_descarga': porto_descarga,
        'uf_consignatario': uf_consignatario,
        'consignatario_final': consignatario_final,
        'consolidador': consolidador,
        'consignatario': consignatario,
        'terminal_descarga': terminal_descarga,
        'nome_exportador': nome_exportador,
        'armador': armador,
        'agente_internacional': agente_internacional,
        'nome_importador': nome_importador
    }

    if all(filters.values()):
        display_filtered_details(df, filters)

if __name__ == "__main__":
    main()