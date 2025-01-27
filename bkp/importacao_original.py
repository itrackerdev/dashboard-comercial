import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO
from style import apply_styles  # Importa os estilos


# Configuração da página
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

apply_styles()

def style_dataframe(df):
    """
    Aplica estilos visuais consistentes a um DataFrame.
    """
    df_reset = df.reset_index(drop=True)
    styles = [
        dict(selector="", props=[("width", "100%")]),  # Adiciona esta linha
        dict(selector="table", props=[("width", "100%")]),  # E esta
        dict(selector="th", props=[
            ("background-color", "#0365B0"),
            ("color", "white"),
            ("text-align", "center"),
            ("font-weight", "bold"),
            ("padding", "8px"),
            ("white-space", "nowrap"),  # Adiciona esta linha
        ]),
        dict(selector="td", props=[
            ("text-align", "center"),
            ("padding", "8px"),
            ("border-bottom", "1px solid #ddd"),
            ("white-space", "nowrap"),  # Adiciona esta linha
            ("max-width", "200px"),     # Adiciona esta linha
            ("overflow", "hidden"),      # Adiciona esta linha
            ("text-overflow", "ellipsis") # Adiciona esta linha
        ]),
    ]
    return df_reset.style.set_table_styles(styles).hide(axis='index')

# Função para baixar arquivo
@st.cache_data
def download_file_from_drive(file_id):
    """Baixa arquivo do Google Drive."""
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"Erro ao baixar arquivo: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Atualiza o cache a cada 1 hora
def load_and_process_data():
    """Carrega e processa os dados do Excel."""
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        excel_content = download_file_from_drive(file_id)

        if not excel_content:
            return pd.DataFrame()

        df = pd.read_excel(excel_content)
        required_columns = {'ETA', 'QTDE CONTAINER', 'UF CONSIGNATÁRIO', 'DATA CONSULTA'}
        if not required_columns.issubset(df.columns):
            st.error(f"O arquivo não contém as colunas necessárias: {', '.join(required_columns - set(df.columns))}")
            return pd.DataFrame()

        df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
        df['DATA CONSULTA'] = pd.to_datetime(df['DATA CONSULTA'], format='%d/%m/%Y', errors='coerce')
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce'
        )

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Função para exibir métricas
def display_metric_card(title, value, delta=None, help_text=None):
    """Exibe um cartão de métrica estilizado."""
    st.metric(label=title, value=value, delta=delta, help=help_text)

def display_paginated_table_with_search(df, rows_per_page=10, key=None):
    """
    Exibe uma tabela paginada com campo de busca e largura total responsiva.
    """
    # Container principal da tabela com margens adequadas
    st.markdown('<div class="section-container">', unsafe_allow_html=True)

    # Tabela estilizada com busca e paginação
    st.markdown('<div class="table-container">', unsafe_allow_html=True)

    # Campo de busca com centralização
    st.markdown('<div class="table-control">', unsafe_allow_html=True)
    search_query = st.text_input("Pesquisar na tabela", "", key=f"{key}_search")
    st.markdown('</div>', unsafe_allow_html=True)

    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    total_rows = df.shape[0]
    total_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page > 0 else 0)

    # Controle de paginação
    st.markdown('<div class="table-control pagination-info">', unsafe_allow_html=True)
    page = st.number_input("Página", min_value=1, max_value=max(1, total_pages), step=1, value=1, key=f"{key}_page")
    st.markdown('</div>', unsafe_allow_html=True)

    start_idx = (page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    paginated_data = df.iloc[start_idx:end_idx]

    # Exibição da tabela com estilo
    styled_table = style_dataframe(paginated_data)
    st.markdown('<div class="table-control pagination-info">', unsafe_allow_html=True)
    st.markdown(f'Exibindo {start_idx + 1} a {min(end_idx, total_rows)} de {total_rows} registros', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(styled_table.to_html(), unsafe_allow_html=True)

    # Fecha os containers
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def create_detailed_tables(df, data_selecionada, uf_selecionada):
    """Cria tabelas detalhadas para a seleção especificada."""
    # Normalizar colunas de datas
    df['ETA'] = pd.to_datetime(df['ETA']).dt.normalize()
    data_selecionada = pd.to_datetime(data_selecionada).normalize()

    # Filtrar os dados
    detalhes = df[(df['ETA'] == data_selecionada) & (df['UF CONSIGNATÁRIO'] == uf_selecionada)]

    if detalhes.empty:
        st.markdown('<div class="stAlert" style="text-align: center;">Sem dados para o filtro selecionado.</div>', unsafe_allow_html=True)
        return

    # **Adicionando os Cards de Insights**
    st.markdown('<div class="metrics-details">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total de Containers", 
            f"{int(detalhes['QTDE CONTAINER'].sum()):,}",
            help="Total de containers para a data e estado selecionados"
        )
    with col2:
        st.metric(
            "Consignatários",
            f"{len(detalhes['CONSIGNATÁRIO'].unique()):,}",
            help="Número de consignatários únicos"
        )
    with col3:
        st.metric(
            "Portos de Descarga",
            f"{len(detalhes['PORTO DESCARGA'].unique()):,}",
            help="Número de portos de descarga"
        )
    with col4:
        st.metric(
            "Terminais",
            f"{len(detalhes['TERMINAL DESCARGA'].unique()):,}",
            help="Número de terminais de descarga"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # **Tabela de trajetória dos containers**
    st.markdown(
        f'<h3 class="subheader">Trajetória dos Containers - {uf_selecionada} ({data_selecionada.strftime("%d/%m/%Y")})</h3>',
        unsafe_allow_html=True
    )

    story_table = detalhes[[
        'PAÍS ORIGEM', 'ETS', 'PORTO DESCARGA', 'ETA',
        'UF CONSIGNATÁRIO', 'QTDE CONTAINER'
    ]].copy()

    story_table.columns = [
        'País de Origem', 'Data de Saída (ETS)',
        'Porto de Descarga', 'Data de Chegada (ETA)',
        'Estado Destino', 'Quantidade de Containers'
    ]

    # Formatar as colunas de datas e quantidades
    story_table['Data de Saída (ETS)'] = pd.to_datetime(
        story_table['Data de Saída (ETS)'], errors='coerce', dayfirst=True
    ).dt.strftime('%d/%m/%Y')

    story_table['Data de Chegada (ETA)'] = pd.to_datetime(
        story_table['Data de Chegada (ETA)'], errors='coerce', dayfirst=True
    ).dt.strftime('%d/%m/%Y')

    story_table['Quantidade de Containers'] = story_table['Quantidade de Containers'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    # Limpar dados desnecessários
    story_table = story_table.dropna(subset=['País de Origem', 'Porto de Descarga', 'Estado Destino'])
    story_table = story_table.sort_values(by='Data de Chegada (ETA)')

    # Exibir a tabela com paginação e busca
    display_paginated_table_with_search(story_table.reset_index(drop=True), rows_per_page=10, key="story_table")

    # **Tabela de detalhes dos containers**
    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)

    # Verificar se as colunas necessárias existem no DataFrame
    columns_needed = ['TERMINAL DESCARGA', 'CONSIGNATÁRIO', 'NAVIO', 'ARMADOR', 'QTDE CONTAINER']
    missing_columns = [col for col in columns_needed if col not in detalhes.columns]

    if missing_columns:
        st.markdown(
            f'<div class="stAlert" style="text-align: center;">Erro: As colunas a seguir estão faltando nos dados: {", ".join(missing_columns)}</div>',
            unsafe_allow_html=True
        )
    else:
        detalhes_tabela = detalhes[columns_needed].copy()

        # Renomear colunas
        detalhes_tabela.columns = [
            'Terminal de Descarga', 'Consignatário', 'Navio', 'Armador', 'Quantidade de Containers'
        ]

        # Formatar a coluna de Quantidade de Containers
        detalhes_tabela['Quantidade de Containers'] = detalhes_tabela['Quantidade de Containers'].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) and x > 0 else "-"
        )

        # Exibir a tabela com paginação e busca
        display_paginated_table_with_search(detalhes_tabela.reset_index(drop=True), rows_per_page=10, key="detalhes_tabela")

    # **Tabela de distribuição por terminal**
    st.markdown('<h3 class="subheader">Distribuição por Terminal</h3>', unsafe_allow_html=True)
    if 'TERMINAL DESCARGA' in detalhes.columns and 'QTDE CONTAINER' in detalhes.columns:
        dist_terminal = detalhes.groupby('TERMINAL DESCARGA')['QTDE CONTAINER'].sum().reset_index()
        dist_terminal.columns = ['Terminal', 'Quantidade']

        dist_terminal['Quantidade'] = dist_terminal['Quantidade'].apply(
            lambda x: f"{int(x):,}" if x > 0 else "-"
        )

        # Exibir a tabela com paginação e busca
        display_paginated_table_with_search(dist_terminal.reset_index(drop=True), rows_per_page=10, key="dist_terminal")

    # **Informações dos navios**
    st.markdown('<h3 class="subheader">Informações dos Navios</h3>', unsafe_allow_html=True)
    if 'NAVIO' in detalhes.columns and 'ARMADOR' in detalhes.columns:
        info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
        info_navios.columns = ['Navio', 'Armador']

        # Exibir a tabela com paginação e busca
        display_paginated_table_with_search(info_navios.reset_index(drop=True), rows_per_page=10, key="info_navios")

# Função principal
def main():
    # Container principal com margem
    st.markdown('<div class="main">', unsafe_allow_html=True)
    
    # Título principal centralizado
    st.markdown('<h1 class="main-title">🚢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

    # Carrega os dados
    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    # Verifica se os dados estão disponíveis
    if df.empty:
        st.markdown(
            '<div class="stAlert" style="text-align: center;">Nenhum dado disponível para exibição.</div>',
            unsafe_allow_html=True
        )
        return

    # Tabela principal
    dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot(
        index='ETA',
        columns='UF CONSIGNATÁRIO',
        values='QTDE CONTAINER'
    ).fillna(0)

    # Ordena o índice em ordem decrescente para mostrar datas mais recentes primeiro
    tabela_pivot = tabela_pivot.sort_index(ascending=False)  # Adicione esta linha

    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    # Adiciona métricas principais com alinhamento uniforme
    total_containers = int(tabela_pivot['TOTAL'].sum())
    ultima_atualizacao = pd.to_datetime(df['DATA CONSULTA']).max()  # Obtém a última data de consulta

    # Container para métricas principais
    st.markdown('<div class="metrics-container" style="display: flex; justify-content: center; gap: 2rem; margin: 2rem 0;">', unsafe_allow_html=True)

    # Métricas com colunas e estilo
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.metric(
            label="TOTAL DE CONTAINERS",
            value=f"{total_containers:,}",
            help="Total de containers no período"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.metric(
            label="ÚLTIMA ATUALIZAÇÃO",
            value=ultima_atualizacao.strftime('%d/%m/%Y'),
            help="Data da última atualização dos dados"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha o container das métricas


    # Adiciona título e espaçamento
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)

    # Formata os dados da tabela
    tabela_formatada = tabela_pivot.copy()
    for coluna in tabela_formatada.columns:
        tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")

    tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')

    # Container para a tabela principal
    st.markdown('<div class="table-section">', unsafe_allow_html=True)
    display_paginated_table_with_search(
        tabela_formatada.reset_index(), 
        rows_per_page=20, 
        key="tabela_principal"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Container para os seletores
    st.markdown('<div class="selectors-container" style="text-align: center;">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        # Encontra a data mais antiga e mais recente corretamente
        data_mais_antiga = pd.to_datetime(tabela_formatada.index[-1], format='%d/%m/%Y')
        data_mais_recente = pd.to_datetime(tabela_formatada.index[0], format='%d/%m/%Y')

        data_selecionada = st.date_input(
            "Data de Chegada", 
            min_value=data_mais_antiga,
            max_value=data_mais_recente,
            value=data_mais_recente,  # Define o valor padrão como a data mais recente
            key="data_chegada"
        )
    with col2:
        uf_selecionada = st.selectbox(
            "Estado Destino", 
            options=[col for col in tabela_pivot.columns if col != 'TOTAL'],
            key="estado_destino"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Container para os detalhes
    if data_selecionada and uf_selecionada:
        st.markdown('<div class="details-section">', unsafe_allow_html=True)
        create_detailed_tables(df, data_selecionada, uf_selecionada)
        st.markdown('</div>', unsafe_allow_html=True)

    # Fecha o container principal
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()