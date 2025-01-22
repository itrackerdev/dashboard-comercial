import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Previsão de Exportações",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

st.markdown(
    """
    <style>
    /* Estilos gerais */
    .stApp {
        background-color: #ffffff;
    }

    /* Título principal */
    h1 {
        background: linear-gradient(120deg, #0365B0 0%, #034C8C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 2rem auto;
        padding: 1.5rem;
        border-bottom: 4px solid #F37529;
        max-width: 90%;
        border-radius: 15px 15px 0 0;
    }

    /* Subtítulos e cabeçalhos de seção */
    h2, h3, .subheader {
        background: linear-gradient(90deg, #0365B0 0%, #034C8C 100%);
        color: white !important;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(3, 101, 176, 0.1);
        text-align: center !important;
    }

    /* Cards de métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0365B0 0%, #034C8C 100%);
        border-radius: 16px;
        padding: 1.5rem !important;
        box-shadow: 0 10px 15px -3px rgba(3, 101, 176, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(4px);
        transition: all 0.3s ease;
        margin: 0.5rem 0;
        text-align: center !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 20px -3px rgba(3, 101, 176, 0.15);
    }

    div[data-testid="stMetric"] > div {
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 700;
        text-align: center !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    div[data-testid="stMetric"] label {
        color: white !important;
        font-weight: 600;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: center !important;
    }

    /* DataFrames */
    div[data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px !important;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        margin: 1rem 0;
        width: 100% !important;
    }

    div[data-testid="stDataFrame"] table {
        width: 100% !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stDataFrame"] th {
        background: linear-gradient(90deg, #0365B0 0%, #034C8C 100%);
        color: white !important;
        padding: 1rem 0.75rem !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: center !important;
        border-bottom: 3px solid #F37529;
        white-space: nowrap;
        font-size: 0.95rem !important;
    }

    div[data-testid="stDataFrame"] td {
        padding: 0.875rem 0.75rem !important;
        text-align: center !important;
        border-bottom: 1px solid rgba(3, 101, 176, 0.1);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        background-color: white !important;
        transition: all 0.2s ease;
    }

    div[data-testid="stDataFrame"] tr:hover td {
        background-color: rgba(243, 117, 41, 0.08) !important;
    }

    /* Campo de busca */
    div[data-testid="stTextInput"] input {
        border-radius: 8px;
        border: 1px solid #d9d9d9;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #0365B0;
        box-shadow: 0 0 4px rgba(3, 101, 176, 0.4);
    }

    /* Paginação */
    .pagination-container {
        text-align: center;
        font-size: 0.8rem;
        color: #555;
        margin-top: 1rem;
        padding: 0.25rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #ddd;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .pagination-container span {
        font-weight: normal;
        color: #0365B0;
    }

    /* Mensagens de alerta */
    div[data-testid="stAlert"] {
        background-color: rgba(243, 117, 41, 0.05);
        color: #F37529;
        border-left: 4px solid #F37529;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        text-align: center;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
            padding: 1rem;
        }

        div[data-testid="stMetric"] {
            padding: 1rem !important;
        }

        div[data-testid="stMetric"] > div {
            font-size: 1.8rem !important;
        }

        .subheader {
            padding: 0.75rem 1rem;
            font-size: 1.1rem;
        }

        div[data-testid="stDataFrame"] th,
        div[data-testid="stDataFrame"] td {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }

        .main-container {
            padding: 0.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
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
        file_id = st.secrets["urls"]["planilha_exportacao"]
        excel_content = download_file_from_drive(file_id)

        if excel_content is None:
            return pd.DataFrame()

        df = pd.read_excel(excel_content)
        df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')
        df['QTDE CONTEINER'] = pd.to_numeric(df['QTDE CONTEINER'].str.replace(',', '.'), errors='coerce')
        df['QTDE CONTEINER'] = df['QTDE CONTEINER'].fillna(0)
        df['DATA CONSULTA'] = pd.to_datetime(df['DATA CONSULTA'], format='%d/%m/%Y', errors='coerce')

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
    df_detalhes['Containers'] = df_detalhes['Containers'].apply(lambda x: f"{int(x):,}" if x > 0 else "-")

    return df_detalhes

def style_dataframe(df):
    """
    Aplica estilos visuais consistentes a um DataFrame.
    """
    df_reset = df.reset_index(drop=True)
    styles = [
        dict(selector="", props=[("width", "100%")]),
        dict(selector="table", props=[("width", "100%")]),
        dict(selector="th", props=[
            ("background-color", "#0365B0"),
            ("color", "white"),
            ("text-align", "center"),
            ("font-weight", "bold"),
            ("padding", "8px"),
            ("white-space", "nowrap"),
        ]),
        dict(selector="td", props=[ 
            ("text-align", "center"),
            ("padding", "8px"),
            ("border-bottom", "1px solid #ddd"),
            ("white-space", "nowrap"),
            ("max-width", "200px"),
            ("overflow", "hidden"),
            ("text-overflow", "ellipsis"),
        ]),
    ]
    return df_reset.style.set_table_styles(styles).hide(axis='index')

def display_paginated_table_with_search(df, rows_per_page=10, key=None):
    """
    Exibe uma tabela paginada com busca e posiciona os botões de paginação no lado direito, abaixo da tabela.
    """
    # Campo de busca acima da tabela
    search_query = st.text_input(
        "Pesquisar",
        "",
        placeholder="Digite para buscar na tabela...",
        key=f"{key}_search"
    )
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    # Configurações de paginação
    total_rows = df.shape[0]
    total_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page > 0 else 0)
    page = st.session_state.get(f"{key}_page", 1)

    # Paginando os dados
    start_idx = (page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    paginated_data = df.iloc[start_idx:end_idx].reset_index(drop=True)

    # Estilização e exibição da tabela
    styled_table = style_dataframe(paginated_data)
    st.markdown(styled_table.to_html(), unsafe_allow_html=True)

    # Paginação abaixo da tabela
    st.markdown(f"""
        <div class="pagination-container">
            <span>Exibindo {start_idx + 1} a {min(end_idx, total_rows)} de {total_rows} registros</span>
            <br>
            Página {page} de {total_pages}
        </div>
    """, unsafe_allow_html=True)

    # Container para os botões no lado direito
    st.markdown(
        """
        <style>
        .button-container {
            display: flex;
            justify-content: flex-end;
            margin-top: 1rem;
        }
        .button-container button {
            margin-left: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="button-container">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Anterior", key=f"{key}_prev") and page > 1:
            st.session_state[f"{key}_page"] = page - 1
    with col2:
        if st.button("Próxima ➡️", key=f"{key}_next") and page < total_pages:
            st.session_state[f"{key}_page"] = page + 1

    st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Título principal
    st.markdown('<h1 class="main-title">🚢 Previsão de Exportações de Containers </h1>', unsafe_allow_html=True)

    try:
        # Carregando dados
        df = load_and_process_data()

        if df.empty:
            st.error("Não foi possível carregar os dados.")
            return

        # Tabela principal
        dados_pivot = df.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR'])['QTDE CONTEINER'].sum().reset_index()
        tabela_pivot = dados_pivot.pivot(
            index='DATA EMBARQUE',
            columns='ESTADO EXPORTADOR',
            values='QTDE CONTEINER'
        ).fillna(0)

        # Ordena o índice em ordem decrescente
        tabela_pivot = tabela_pivot.sort_index(ascending=False)
        tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

        # Métricas principais
        total_containers = int(tabela_pivot['TOTAL'].sum())
        ultima_atualizacao = pd.to_datetime(df['DATA CONSULTA']).max()  # Obtém a última data de consulta

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "TOTAL DE CONTAINERS",
                f"{total_containers:,}",
                help="Total de containers no período"
            )
        with col2:
            st.metric(
                "ÚLTIMA ATUALIZAÇÃO",
                ultima_atualizacao.strftime('%d/%m/%Y'),
                help="Data da última atualização dos dados"
            )

        st.markdown('<hr>', unsafe_allow_html=True)

        # Filtros
        st.markdown('<div class="selectors-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            data_selecionada = st.selectbox(
                "Selecione a Data",
                options=pd.to_datetime(tabela_pivot.index),
                format_func=lambda x: x.strftime('%d/%m/%Y'),
                index=0  # Seleciona a data mais recente por padrão
            )
        with col2:
            uf_selecionada = st.selectbox(
                "Selecione o Estado",
                options=[col for col in tabela_pivot.columns if col != 'TOTAL']
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Exibe a tabela principal com busca e paginação
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        tabela_formatada = tabela_pivot.copy()
        for coluna in tabela_formatada.columns:
            tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
        tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')

        # Exibe tabela principal paginada
        display_paginated_table_with_search(
            tabela_formatada.reset_index(),
            rows_per_page=20,
            key="tabela_principal"
        )

        st.markdown('</div>', unsafe_allow_html=True)

        # Exibe resumo de exportações por porto somente após a aplicação do filtro
        if data_selecionada and uf_selecionada:
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown(
                f'<h3 class="subheader">Resumo de Exportações por Porto - {uf_selecionada} ({data_selecionada.strftime("%d/%m/%Y")})</h3>',
                unsafe_allow_html=True
            )

            resumo_filtrado = df[
                (df['DATA EMBARQUE'].dt.date == data_selecionada.date()) & 
                (df['ESTADO EXPORTADOR'] == uf_selecionada)
            ]

            if resumo_filtrado.empty:
                st.markdown('<div class="alert">Sem dados para o filtro selecionado.</div>', unsafe_allow_html=True)
            else:
                resumo_agrupado = resumo_filtrado.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])['QTDE CONTEINER'].sum().reset_index()
                resumo_agrupado['DATA EMBARQUE'] = resumo_agrupado['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
                resumo_agrupado['QTDE CONTEINER'] = resumo_agrupado['QTDE CONTEINER'].apply(lambda x: f"{int(x):,}" if x > 0 else "-")

                display_paginated_table_with_search(
                    resumo_agrupado.reset_index(drop=True),
                    rows_per_page=10,
                    key="tabela_resumo_filtrada"
                )

            # Seção de detalhes
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown(
                f'<h3 class="subheader">Detalhes para {uf_selecionada} - {data_selecionada.strftime("%d/%m/%Y")}</h3>',
                unsafe_allow_html=True
            )

            detalhes = get_detailed_info(df, data_selecionada, uf_selecionada)
            if not detalhes.empty:
                tabela_detalhes = format_detailed_table(detalhes)

                # Cards de métricas detalhadas
                st.markdown('<div class="metrics-details">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Total de Containers", 
                        f"{int(detalhes['QTDE CONTEINER'].sum()):,}",
                        help="Total de containers para a data e estado selecionados"
                    )
                with col2:
                    st.metric(
                        "Exportadores",
                        f"{len(detalhes['NOME EXPORTADOR'].unique()):,}",
                        help="Número de empresas exportadoras"
                    )
                with col3:
                    st.metric(
                        "Países de Destino",
                        f"{len(detalhes['PAÍS DE DESTINO'].unique()):,}",
                        help="Número de países de destino"
                    )
                with col4:
                    st.metric(
                        "Terminais",
                        f"{len(detalhes['TERMINAL EMBARQUE'].unique()):,}",
                        help="Número de terminais de embarque"
                    )
                st.markdown('</div>', unsafe_allow_html=True)

                # Exibir tabela de detalhes com paginação e busca
                st.markdown('<div class="details-table">', unsafe_allow_html=True)
                display_paginated_table_with_search(
                    tabela_detalhes.reset_index(drop=True),
                    rows_per_page=10,
                    key="detalhes_tabela"
                )
                st.markdown('</div>', unsafe_allow_html=True)

                # Tabela de distribuição por terminal
                st.markdown('<h3 class="subheader">Distribuição por Terminal</h3>', unsafe_allow_html=True)
                if 'TERMINAL EMBARQUE' in detalhes.columns and 'QTDE CONTEINER' in detalhes.columns:
                    dist_terminal = detalhes.groupby('TERMINAL EMBARQUE')['QTDE CONTEINER'].sum().reset_index()
                    dist_terminal.columns = ['Terminal', 'Quantidade']
                    
                    dist_terminal['Quantidade'] = dist_terminal['Quantidade'].apply(
                        lambda x: f"{int(x):,}" if x > 0 else "-"
                    )
                    
                    display_paginated_table_with_search(
                        dist_terminal.reset_index(drop=True), 
                        rows_per_page=10, 
                        key="dist_terminal"
                    )

                # Informações dos navios
                st.markdown('<h3 class="subheader">Informações dos Navios</h3>', unsafe_allow_html=True)
                if 'NAVIO' in detalhes.columns and 'ARMADOR' in detalhes.columns:
                    info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
                    info_navios.columns = ['Navio', 'Armador']
                    
                    display_paginated_table_with_search(
                        info_navios.reset_index(drop=True), 
                        rows_per_page=10, 
                        key="info_navios"
                    )

            else:
                st.markdown(
                    '<div class="alert">Não há dados para a seleção especificada</div>',
                    unsafe_allow_html=True
                )
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
