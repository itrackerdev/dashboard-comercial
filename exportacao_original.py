import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles  # Importa os estilos personalizados

# Configuração da página
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
)

apply_styles()

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
