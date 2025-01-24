import streamlit as st

# Configuração da página DEVE ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
)

# Importações que usam st só depois do set_page_config
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles

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

def create_dropdown(label, df_column, key):
    """Cria um dropdown simples com tratamento para valores nulos"""
    options = df_column.dropna().unique().tolist()
    options = [str(opt) for opt in options]
    return st.selectbox(label, ['Todos'] + sorted(options), key=key)

def format_dates(df, date_columns):
    """Formata as colunas de data para o padrão brasileiro."""
    for col in date_columns:
        if col not in df.columns:
            st.warning(f"A coluna {col} não existe no dataframe.")
            continue
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            df[col] = df[col].dt.strftime('%d/%m/%Y')  # Converte para o formato brasileiro
        except Exception as e:
            st.warning(f"Erro ao formatar a coluna {col}: {e}")
    return df


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
            'ARMADOR', 'AGENTE INTERNACIONAL', 'NAVIO', 
            'PAÍS ORIGEM', 'PORTO ORIGEM'
        ]

        missing_columns = [col for col in selected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")
            return pd.DataFrame()

        df = df[selected_columns]

        df = format_dates(df, ['ETA'])

        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].astype(str).str.replace(',', '.'), errors='coerce'
        ).fillna(0)

        df = df.dropna(subset=['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def display_filtered_details(df, filters):
    # Certificar que as datas em 'ETA' e os filtros estão no mesmo formato (datetime)
    df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y', errors='coerce')
    filters['data_inicio'] = pd.to_datetime(filters['data_inicio'])
    filters['data_fim'] = pd.to_datetime(filters['data_fim'])

    # Criar a máscara de filtragem
    mask = (df['ETA'] >= filters['data_inicio']) & (df['ETA'] <= filters['data_fim'])

    if filters['porto_descarga'] != 'Todos':
        mask &= (df['PORTO DESCARGA'] == filters['porto_descarga'])
    if filters['uf_consignatario'] != 'Todos':
        mask &= (df['UF CONSIGNATÁRIO'] == filters['uf_consignatario'])

    # Lista de colunas para aplicar filtros
    filter_columns = {
        'CONSIGNATARIO FINAL': 'consignatario_final',
        'CONSOLIDADOR': 'consolidador',
        'CONSIGNATÁRIO': 'consignatario',
        'TERMINAL DESCARGA': 'terminal_descarga',
        'NOME EXPORTADOR': 'nome_exportador',
        'ARMADOR': 'armador',
        'AGENTE INTERNACIONAL': 'agente_internacional',
        'NOME EXPORTADOR': 'nome_exportador'  # Remover esta linha se a coluna não existir
    }

    # Aplicar filtros somente em colunas existentes
    for col, filter_key in filter_columns.items():
        if col in df.columns and filters.get(filter_key, 'Todos') != 'Todos':
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

    # Exibir somente colunas existentes
    colunas_exibicao = [col for col in colunas_exibicao if col in df.columns]

    detalhes_tabela = detalhes[colunas_exibicao].copy()
    detalhes_tabela['QTDE CONTAINER'] = detalhes_tabela['QTDE CONTAINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def main():
    st.markdown('<h1 class="main-title">📢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

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
    data_mais_antiga = pd.to_datetime(df['ETA'], format='%d/%m/%Y').min().strftime('%d/%m/%Y')
    data_mais_recente = pd.to_datetime(df['ETA'], format='%d/%m/%Y').max().strftime('%d/%m/%Y')
    range_datas = f"{data_mais_antiga} - {data_mais_recente}"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}", help="Total de containers no período")
    with col2:
        st.metric("PERÍODO DOS DADOS", range_datas, help="Intervalo de datas dos dados disponíveis")

    col1, col2, col3 = st.columns(3)
    with col1:
        # Garantir que as datas mínima e máxima sejam coerentes
        data_mais_antiga_dt = min(pd.to_datetime(tabela_pivot.index.min(), format='%d/%m/%Y'), 
                                  pd.to_datetime(tabela_pivot.index.max(), format='%d/%m/%Y'))
        data_mais_recente_dt = max(pd.to_datetime(tabela_pivot.index.min(), format='%d/%m/%Y'), 
                                   pd.to_datetime(tabela_pivot.index.max(), format='%d/%m/%Y'))

        # Configurar o componente de seleção de período
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

    st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)
    tabela_formatada = tabela_pivot.copy().reset_index()
    tabela_formatada['ETA'] = pd.to_datetime(tabela_formatada['ETA'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
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
        'agente_internacional': agente_internacional
    }

    if any(filters.values()):
        display_filtered_details(df, filters)

if __name__ == "__main__":
    main()
