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

# Estilização CSS atualizada
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

    /* Campo de busca melhorado */
    div[data-testid="stTextInput"] input {
        border-radius: 12px;
        border: 1px solid rgba(3, 101, 176, 0.2);
        padding: 1rem;
        font-size: 1rem;
        width: 100%;
        text-align: center;
        transition: all 0.3s ease;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #F37529;
        box-shadow: 0 0 0 2px rgba(243, 117, 41, 0.2);
    }

    /* Seletores estilizados */
    div[data-baseweb="select"] {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(3, 101, 176, 0.2);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    div[data-baseweb="select"]:hover {
        border-color: #F37529;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: none !important;
        background: transparent !important;
    }

    /* Expanders estilizados */
    section[data-testid="stExpander"] > div:first-child {
        border-radius: 12px !important;
        border: 1px solid rgba(3, 101, 176, 0.2) !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }

    section[data-testid="stExpander"] > div:first-child:hover {
        border-color: #F37529 !important;
        background: rgba(243, 117, 41, 0.05) !important;
    }

    /* Divisores */
    hr {
        border: none;
        height: 3px;
        background: linear-gradient(to right, #0365B0, #F37529);
        margin: 2rem 0;
        opacity: 0.7;
        border-radius: 3px;
    }

    /* Container principal */
    .main-container {
        padding: 1rem 2rem;
        max-width: none !important;
    }

    /* Paginação */
    div.pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin: 1rem 0;
    }

    .pagination-info {
        color: #0365B0;
        font-weight: 600;
        text-align: center !important;
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

def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Título principal
    st.markdown('<h1 class="main-title">📦 Previsão de Exportações por Estado</h1>', unsafe_allow_html=True)
    
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
        media_diaria = int(tabela_pivot['TOTAL'].mean())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "TOTAL DE CONTAINERS",
                f"{total_containers:,}",
                help="Total de containers no período"
            )
        with col2:
            st.metric(
                "MÉDIA DIÁRIA",
                f"{media_diaria:,}",
                help="Média diária de containers"
            )
        
        st.markdown('<hr>', unsafe_allow_html=True)
        
        # Título da seção de previsão
        st.markdown('<h3 class="subheader">Previsão de Exportações por Estado</h3>', unsafe_allow_html=True)
        
        # Container para os seletores
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

        # Formatação da tabela
        tabela_formatada = tabela_pivot.copy()
        for coluna in tabela_formatada.columns:
            tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
        
        tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')
        
        # Campo de busca
        st.text_input("Pesquisar na tabela", key="search", help="Digite para filtrar os dados")
        search_query = st.session_state.search

        # Container para a tabela principal
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.dataframe(
            tabela_formatada,
            use_container_width=True,
            height=400
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Seção de detalhes
        if data_selecionada and uf_selecionada:
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
                
                # Tabela de detalhes
                st.markdown('<div class="details-table">', unsafe_allow_html=True)
                st.dataframe(
                    tabela_detalhes,
                    use_container_width=True,
                    height=400
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Informações adicionais em expansores
                st.markdown('<div class="expanders-grid">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.expander("📊 Distribuição por Terminal", expanded=True):
                        dist_terminal = detalhes.groupby('TERMINAL EMBARQUE')['QTDE CONTEINER'].sum().sort_values(ascending=False)
                        st.dataframe(
                            dist_terminal.map(lambda x: f"{int(x):,}"),
                            use_container_width=True
                        )
                
                with col2:
                    with st.expander("🌎 Países de Destino", expanded=True):
                        dist_paises = detalhes.groupby('PAÍS DE DESTINO')['QTDE CONTEINER'].sum().sort_values(ascending=False)
                        st.dataframe(
                            dist_paises.map(lambda x: f"{int(x):,}"),
                            use_container_width=True
                        )
                
                with st.expander("🚢 Informações dos Navios"):
                    info_navios = detalhes[['NAVIO', 'ARMADOR', 'PORTO DESCARGA']].drop_duplicates()
                    st.dataframe(info_navios, use_container_width=True)
                
                with st.expander("📦 Tipos de Carga"):
                    tipos_carga = detalhes.groupby(['MERCADORIA', 'TIPO CONTEINER'])['QTDE CONTEINER'].sum().sort_values(ascending=False)
                    st.dataframe(
                        tipos_carga.map(lambda x: f"{int(x):,}"),
                        use_container_width=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
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