import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

# Estilização CSS aprimorada
st.markdown(
    """
    <style>
    /* Estilos gerais */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Título principal */
    h1 {
        color: #0365B0 !important;
        font-weight: 800;
        font-size: 2.5rem;
        margin: 2rem auto;
        text-align: center;
        padding: 1.5rem;
        border-bottom: 4px solid #F37529;
        max-width: 90%;
        background: linear-gradient(120deg, rgba(3,101,176,0.1) 0%, rgba(255,255,255,1) 50%, rgba(243,117,41,0.1) 100%);
        border-radius: 15px 15px 0 0;
    }
    
    /* Subtítulos e cabeçalhos de seção */
    h2, h3, .subheader {
        color: #0365B0 !important;
        font-weight: 600;
        padding: 0.75rem 1rem;
        margin: 1.5rem 0;
        background-color: #f8f9fa;
        border-left: 6px solid #F37529;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Cards de métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0365B0, #0357A6);
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(3, 101, 176, 0.15);
        transition: all 0.3s ease;
        margin: 0.5rem 0;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(3, 101, 176, 0.2);
    }

    div[data-testid="stMetric"] > div {
        color: white !important; /* Deixa os números brancos */
        font-size: 2rem !important;
        font-weight: 700;
    }

    div[data-testid="stMetric"] label {
        color: white !important; /* Deixa os textos brancos */
        font-weight: 600;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* DataFrames aprimorados */
    .stDataFrame {
        border: none !important;
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        margin: 1rem 0;
        background: white;
    }
    
    /* Esconder índices das tabelas */
    .stDataFrame [data-testid="stDataFrameIndexHeader"] {
        display: none !important;
    }
    
    .stDataFrame th:first-child {
        display: none !important;
    }
    
    .stDataFrame td:first-child {
        display: none !important;
    }
    
    .stDataFrame th {
        background-color: #0365B0 !important;
        color: white !important;
        font-weight: 600;
        text-align: center !important;
        padding: 1rem 0.75rem !important;
        font-size: 0.9rem !important;
        border-top: 3px solid #F37529 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        text-align: center !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 0.5rem !important;
        border-bottom: 1px solid rgba(3, 101, 176, 0.1);
        transition: background-color 0.2s ease;
        background-color: white !important;
    }
    
    .stDataFrame tr:nth-child(even) td {
        background-color: rgba(3, 101, 176, 0.02) !important;
    }
    
    .stDataFrame tr:hover td {
        background-color: rgba(243, 117, 41, 0.05) !important;
    }
    
    /* Seletores estilizados */
    .stSelectbox, .stDateInput {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stSelectbox label, .stDateInput label {
        color: #0365B0 !important;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border: 1px solid rgba(3, 101, 176, 0.2);
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #F37529;
    }
    
    /* Mensagens de alerta estilizadas */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #F37529;
        background-color: rgba(243, 117, 41, 0.05);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Divisores de seção aprimorados */
    hr {
        border: none;
        height: 3px;
        background: linear-gradient(to right, #0365B0, #F37529);
        margin: 2rem 0;
        opacity: 0.7;
        border-radius: 3px;
    }

    /* Container principal */
    .main {
        padding: 1rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
            padding: 1rem;
        }
        
        .stDataFrame th {
            font-size: 0.85rem !important;
            padding: 0.75rem 0.5rem !important;
        }
        
        .stDataFrame td {
            font-size: 0.8rem !important;
            padding: 0.5rem !important;
        }
        
        div[data-testid="stMetric"] > div {
            font-size: 1.5rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

# Função para carregar e processar dados
@st.cache_data
def load_and_process_data():
    """Carrega e processa os dados do Excel."""
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        excel_content = download_file_from_drive(file_id)

        if not excel_content:
            return pd.DataFrame()

        df = pd.read_excel(excel_content)
        if not {'ETA', 'QTDE CONTAINER', 'UF CONSIGNATÁRIO'}.issubset(df.columns):
            st.error("O arquivo não contém as colunas necessárias.")
            return pd.DataFrame()

        df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Função para exibir métricas
def display_metric_card(title, value, delta=None, help_text=None):
    """Exibe um cartão de métrica estilizado."""
    st.metric(label=title, value=value, delta=delta, help=help_text)

# Função para formatar DataFrame
def style_dataframe(df):
    """Aplica estilos ao DataFrame."""
    # Cria uma cópia do DataFrame para não modificar o original
    styled_df = df.copy()
    
    # Define os estilos básicos da tabela
    styles = [
        dict(selector="th", props=[
            ("background-color", "#0365B0"),
            ("color", "white"),
            ("font-weight", "bold"),
            ("text-align", "center"),
            ("padding", "1rem"),
            ("border-top", "3px solid #F37529"),
            ("text-transform", "uppercase"),
            ("letter-spacing", "0.5px")
        ]),
        dict(selector="td", props=[
            ("text-align", "center"),
            ("padding", "0.75rem"),
            ("border-bottom", "1px solid rgba(3, 101, 176, 0.1)")
        ])
    ]
    
    return (styled_df.style
            .set_table_styles(styles)
            .hide(axis='index')  # Tentando um método alternativo para esconder o índice
            .background_gradient(axis=None, subset=None, text_color_threshold=0.408,
                              cmap=lambda x: 'rgba(3, 101, 176, 0.03)' if x % 2 == 0 else 'white'))

# Função para criar tabelas detalhadas
def create_detailed_tables(df, data_selecionada, uf_selecionada):
    """Cria tabelas detalhadas para a seleção especificada."""
    df['ETA'] = pd.to_datetime(df['ETA']).dt.normalize()
    data_selecionada = pd.to_datetime(data_selecionada).normalize()

    detalhes = df[(df['ETA'] == data_selecionada) & (df['UF CONSIGNATÁRIO'] == uf_selecionada)]

    if detalhes.empty:
        st.info("Sem dados para o filtro selecionado.")
        return

    # Função auxiliar para estilizar tabelas
    def style_table(df, hide_index=True):
        styles = [
            {'selector': 'th',
             'props': [
                ('background-color', '#0365B0'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('padding', '1rem'),
                ('border-top', '3px solid #F37529'),
                ('text-transform', 'uppercase'),
                ('letter-spacing', '0.5px')
            ]},
            {'selector': 'td',
             'props': [
                ('text-align', 'center'),
                ('padding', '0.75rem'),
                ('border-bottom', '1px solid rgba(3, 101, 176, 0.1)')
            ]},
            {'selector': '.index_name, .blank, .col_heading.level0, .index_name.level0',
             'props': [
                ('display', 'none')
            ]}
        ]
        
        styled = df.style.set_table_styles(styles)
        if hide_index:
            styled = styled.hide(axis='index')
        return styled

    # Tabela de trajetória dos containers
    st.subheader(f"Trajetória dos Containers - {uf_selecionada} ({data_selecionada.strftime('%d/%m/%Y')})")

    story_table = detalhes[[
        'PAÍS ORIGEM', 'ETS', 'PORTO DESCARGA', 'ETA',
        'UF CONSIGNATÁRIO', 'QTDE CONTAINER'
    ]].copy()

    story_table.columns = [
        'País de Origem', 'Data de Saída (ETS)',
        'Porto de Descarga', 'Data de Chegada (ETA)',
        'Estado Destino', 'Quantidade de Containers'
    ]

    # Formatação das colunas
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

    # Resetar o índice para remover os índices originais
    story_table_reset = story_table.reset_index(drop=True)

    # Converter a tabela para HTML e remover completamente os índices
    story_table_html = story_table_reset.to_html(index=False, justify='center')

    # Exibir a tabela usando Markdown com CSS básico
    st.markdown(f"""
    <div style="overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
        {story_table_html}
    </div>
    """, unsafe_allow_html=True)


    # Tabela de detalhes dos containers
    st.subheader("Detalhes dos Containers")
    detalhes_tabela = detalhes[[
        'TERMINAL DESCARGA', 'CONSIGNATÁRIO', 'EMAIL',
        'TELEFONE', 'NAVIO', 'ARMADOR', 'QTDE CONTAINER'
    ]].copy()

    detalhes_tabela.columns = [
        'Terminal de Descarga', 'Consignatário', 'Email',
        'Telefone', 'Navio', 'Armador', 'Quantidade de Containers'
    ]

    detalhes_tabela['Quantidade de Containers'] = detalhes_tabela['Quantidade de Containers'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    # Resetar o índice e converter para HTML
    detalhes_tabela_reset = detalhes_tabela.reset_index(drop=True)
    detalhes_tabela_html = detalhes_tabela_reset.to_html(index=False, justify='center')

    # Exibir tabela formatada
    st.markdown(f"""
    <div style="overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
        {detalhes_tabela_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Distribuição por terminal
    st.subheader("Distribuição por Terminal")
    dist_terminal = detalhes.groupby('TERMINAL DESCARGA')['QTDE CONTAINER'].sum().reset_index()
    dist_terminal.columns = ['Terminal', 'Quantidade']

    dist_terminal['Quantidade'] = dist_terminal['Quantidade'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    # Resetar o índice e converter para HTML
    dist_terminal_reset = dist_terminal.reset_index(drop=True)
    dist_terminal_html = dist_terminal_reset.to_html(index=False, justify='center')

    # Exibir tabela formatada
    st.markdown(f"""
    <div style="overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
        {dist_terminal_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Informações dos navios
    st.subheader("Informações dos Navios")
    info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
    info_navios.columns = ['Navio', 'Armador']

    # Resetar o índice e converter para HTML
    info_navios_reset = info_navios.reset_index(drop=True)
    info_navios_html = info_navios_reset.to_html(index=False, justify='center')

    # Exibir tabela formatada
    st.markdown(f"""
    <div style="overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
        {info_navios_html}
    </div>
    """, unsafe_allow_html=True)


# Função principal
def main():
    # Container principal com margem
    st.markdown('<div class="main">', unsafe_allow_html=True)
    
    st.title("Previsão de Chegadas de Containers")

    # Carrega os dados
    if "dataframe" not in st.session_state:
        st.session_state["dataframe"] = load_and_process_data()
    df = st.session_state["dataframe"]

    if df.empty:
        st.warning("Nenhum dado disponível para exibição.")
        return

    # Tabela principal
    dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
    tabela_pivot = dados_pivot.pivot(
        index='ETA',
        columns='UF CONSIGNATÁRIO',
        values='QTDE CONTAINER'
    ).fillna(0)

    tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

    # Adiciona resumo de métricas
    total_containers = int(tabela_pivot['TOTAL'].sum())
    media_diaria = int(tabela_pivot['TOTAL'].mean())
    
    col1, col2 = st.columns(2)
    with col1:
        display_metric_card(
            "Total de Containers",
            f"{total_containers:,}",
            help_text="Total de containers em todas as datas"
        )
    with col2:
        display_metric_card(
            "Média Diária",
            f"{media_diaria:,}",
            help_text="Média diária de containers"
        )

    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.subheader("Previsão de Chegadas por Estado")
    tabela_formatada = tabela_pivot.copy()
    for coluna in tabela_formatada.columns:
        tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")

    tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')
    st.dataframe(style_dataframe(tabela_formatada), use_container_width=True, height=400)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Seletores de data e estado em colunas com espaçamento melhorado
    col1, col2 = st.columns([1, 1])
    with col1:
        data_selecionada = st.date_input(
            "Data de Chegada", 
            min_value=pd.to_datetime(tabela_formatada.index[0], format='%d/%m/%Y'),
            max_value=pd.to_datetime(tabela_formatada.index[-1], format='%d/%m/%Y')
        )
    with col2:
        uf_selecionada = st.selectbox(
            "Estado Destino", 
            options=[col for col in tabela_pivot.columns if col != 'TOTAL']
        )

    if data_selecionada and uf_selecionada:
        create_detailed_tables(df, data_selecionada, uf_selecionada)

    # Fecha o container principal
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()