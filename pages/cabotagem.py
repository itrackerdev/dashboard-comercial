import streamlit as st

# Configuração da página DEVE ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Cabotagem - Sistema de Análise de Cargas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚢"
)

# Restante das importações
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
import logging
import hashlib
import os
from utils.data_processing import calcular_total_cabotagem, create_unique_id_safe
from style import apply_styles

# Configuração de logging
logging.basicConfig(level=logging.ERROR)

# Navegação
navigation = [
    {"icon": "🏠", "label": "Home", "page": "Home.py", "suffix": "home"},
    {"icon": "🚢", "label": "Cabotagem", "page": "pages/cabotagem.py", "suffix": "cab"},
    {"icon": "📦", "label": "Exportação", "page": "pages/exportacao.py", "suffix": "exp"},
    {"icon": "📥", "label": "Importação", "page": "pages/importacao.py", "suffix": "imp"}
]

# Aplicar estilos
apply_styles()

# Estilo da Sidebar
st.markdown("""
    <style>
        section[data-testid="stSidebar"] > div {
            background-color: #f8f9fa;
            padding: 1rem;
        }
        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            display: flex;
            align-items: center;
            background-color: transparent;
            border: none;
            padding: 0.5rem 1rem;
            text-align: left;
            color: #0C0D0E;
            font-size: 1rem;
            margin: 0.2rem 0;
            border-radius: 0.25rem;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(151, 166, 195, 0.15);
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_and_process_data():
    """
    Carrega e processa os dados da planilha de cabotagem.
    """
    try:
        file_id = st.secrets["urls"]["planilha_cabotagem"]
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
               
        response = requests.get(url)
        response.raise_for_status()
                
        df = pd.read_excel(BytesIO(response.content), dtype=str)
        
        # Processamento específico para cabotagem
        df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'], format='%Y-%m-%d', errors='coerce', dayfirst=True)
        for col in ['QUANTIDADE C20', 'QUANTIDADE C40']:
            df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)
        df['QUANTIDADE TOTAL'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def download_file_from_drive(file_id):
    """Baixa arquivo do Google Drive."""
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"Erro ao baixar arquivo: {e}")
        return None

def remove_duplicates(df):
    """Remove registros duplicados do DataFrame."""
    try:
        # Adiciona coluna com timestamp atual
        df['DATA_ATUALIZACAO'] = datetime.now()

        # Colunas necessárias para ID único
        required_columns = [
            'DATA DE EMBARQUE', 'PORTO DE ORIGEM', 'PORTO DE DESTINO',
            'NAVIO', 'VIAGEM', 'REMETENTE', 'DESTINATÁRIO'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"As seguintes colunas estão ausentes: {missing_columns}")

        # Criação de ID único
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)

        # Consolidar registros existentes
        if os.path.exists('dados_cabotagem_consolidados.parquet'):
            df_existing = pd.read_parquet('dados_cabotagem_consolidados.parquet')
            df_all = pd.concat([df_existing, df], ignore_index=True)
        else:
            df_all = df

        # Remoção de duplicatas
        df_all = df_all.sort_values('DATA DE EMBARQUE', ascending=False).drop_duplicates(
            subset=['ID_UNICO'], keep='first'
        )

        # Salvar arquivo consolidado
        df_all.to_parquet('dados_cabotagem_consolidados.parquet', index=False, engine='pyarrow')
        return df_all

    except Exception as e:
        st.error(f"Erro ao remover duplicatas: {e}")
        return pd.DataFrame()

def create_unique_id_safe(row):
    """Cria um ID único para cada registro."""
    try:
        fields = [
            row.get('DATA DE EMBARQUE', ''), row.get('PORTO DE ORIGEM', ''),
            row.get('PORTO DE DESTINO', ''), row.get('NAVIO', ''),
            row.get('VIAGEM', ''), row.get('REMETENTE', ''), row.get('DESTINATÁRIO', '')
        ]
        unique_string = "_".join(map(str, fields))
        return hashlib.md5(unique_string.encode()).hexdigest()
    except Exception as e:
        return None

def calcular_total_cabotagem(df):
    """
    Calcula o total de contêineres de cabotagem.
    
    Args:
        df (pd.DataFrame): DataFrame com os dados de cabotagem
        
    Returns:
        int: Total de contêineres
    """
    try:
        if df is None or df.empty:
            return 0
            
        if 'QUANTIDADE C20' not in df.columns or 'QUANTIDADE C40' not in df.columns:
            return 0
            
        # Convert container quantities if they are strings
        if df['QUANTIDADE C20'].dtype == 'object':
            df['QUANTIDADE C20'] = pd.to_numeric(df['QUANTIDADE C20'].str.replace(',', '.'), errors='coerce').fillna(0)
        if df['QUANTIDADE C40'].dtype == 'object':
            df['QUANTIDADE C40'] = pd.to_numeric(df['QUANTIDADE C40'].str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Simple sum of C20 and C40
        total_containers = int(df['QUANTIDADE C20'].sum() + df['QUANTIDADE C40'].sum())
        return total_containers

    except Exception as e:
        st.error(f"Erro ao calcular total de cabotagem: {e}")
        return 0

def get_estado_info(df, data, uf):
    """Retorna informações filtradas por estado."""
    try:
        data_filtro = pd.to_datetime(data, format='%d/%m/%Y', dayfirst=True)
        df['ESTADO_ORIGEM'] = df['REMETENTE - CIDADE'].apply(
            lambda x: x.split('-')[-1].strip() if isinstance(x, str) else None
        )
        df['ESTADO_DESTINO'] = df['DESTINATÁRIO - ESTADO']
        mask = (
            (df['DATA DE EMBARQUE'].dt.date == data_filtro.date()) &
            ((df['ESTADO_ORIGEM'] == uf) | (df['ESTADO_DESTINO'] == uf))
        )
        return df[mask].copy()
    except Exception as e:
        st.error(f"Erro ao filtrar por estado: {e}")
        return pd.DataFrame()
    
def create_state_summary_table(df, view_type='destinatario'):
    """Cria uma tabela resumo por data e estado ou cidade."""
    try:
        # Filtrar dados válidos
        df = df.dropna(subset=['DATA DE EMBARQUE', 'QUANTIDADE TOTAL'])
        df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'], errors='coerce')

        # Agrupar por estado ou cidade com base no tipo de visualização
        if view_type == 'destinatario':
            agrupado = df.groupby(['DATA DE EMBARQUE', 'DESTINATÁRIO - ESTADO'])['QUANTIDADE TOTAL'].sum().reset_index()
            pivot_table = agrupado.pivot(index='DATA DE EMBARQUE', columns='DESTINATÁRIO - ESTADO', values='QUANTIDADE TOTAL').fillna(0)
        else:
            agrupado = df.groupby(['DATA DE EMBARQUE', 'REMETENTE - CIDADE'])['QUANTIDADE TOTAL'].sum().reset_index()
            pivot_table = agrupado.pivot(index='DATA DE EMBARQUE', columns='REMETENTE - CIDADE', values='QUANTIDADE TOTAL').fillna(0)

        # Adicionar coluna total
        pivot_table['TOTAL'] = pivot_table.sum(axis=1)

        # Resetar índice para exibição e ordenar
        resumo_df = pivot_table.reset_index().sort_values('DATA DE EMBARQUE', ascending=False)
        resumo_df['DATA DE EMBARQUE'] = resumo_df['DATA DE EMBARQUE'].dt.strftime('%d/%m/%Y')

        return resumo_df
    except Exception as e:
        st.error(f"Erro ao criar tabela resumo: {e}")
        return pd.DataFrame()

def format_date_safe(date):
    """Formata data com segurança."""
    try:
        return pd.to_datetime(date, dayfirst=True).strftime('%d/%m/%Y')
    except:
        return '-'

def get_formatted_dates(df):
    """Retorna uma lista de datas formatadas disponíveis no DataFrame."""
    try:
        valid_dates = df['DATA DE EMBARQUE'].dropna()
        # Ordenar do mais recente para o mais antigo
        return sorted(valid_dates.dt.strftime('%d/%m/%Y').unique(), reverse=True)
    except Exception as e:
        st.error(f"Erro ao formatar datas: {e}")
        return []

def main():
    # Barra lateral de navegação
    with st.sidebar:
        for nav in navigation:
            if st.button(
                f"{nav['icon']} {nav['label']}", 
                key=f"nav_{nav['suffix']}", 
                use_container_width=True
            ):
                st.switch_page(nav['page'])

    # Resto do código da página
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">🚢 Análise de Operações de Cabotagem</h1>', unsafe_allow_html=True)

    # Carregar dados
    df = load_and_process_data()

    # Garantir que dados foram carregados
    if df.empty:
        st.error("Não foi possível carregar os dados. Verifique o arquivo ou a fonte de dados.")
        return

    # Métricas principais
    col1, col2 = st.columns(2)
    with col1:
        total_containers = calcular_total_cabotagem(df)
        st.metric("Total de Containers", f"{total_containers:,}", help="Quantidade total de containers (C20 + C40)")
    with col2:
        ultima_atualizacao = format_date_safe(df['DATA DE EMBARQUE'].max())
        st.metric("Última Atualização", ultima_atualizacao, help="Data mais recente nos dados.")

    # Resumo de Operações
    st.markdown('<h3 class="subheader">Resumo de Operações</h3>', unsafe_allow_html=True)
    view_type = st.radio(
        "Tipo de Visualização",
        ['destinatario', 'remetente'],
        format_func=lambda x: "Por Destinatário" if x == 'destinatario' else "Por Remetente",
        horizontal=True
    )
    
    summary_df = create_state_summary_table(df, view_type)
    if summary_df.empty:
        st.warning("Nenhum dado disponível para exibição no resumo de operações.")
    else:
        st.dataframe(summary_df, use_container_width=True)

    # Detalhamento por estado
    st.markdown('<h3 class="subheader">Detalhamento por Estado</h3>', unsafe_allow_html=True)

    datas_disponiveis = get_formatted_dates(df)
    if not datas_disponiveis:
        st.warning("Nenhuma data disponível para seleção.")
        return

    col1, col2 = st.columns(2)
    with col1:
        data_selecionada = st.selectbox("Selecione a Data", datas_disponiveis)

    estados_disponiveis = sorted(df['DESTINATÁRIO - ESTADO'].dropna().unique())
    with col2:
        estado_selecionado = st.selectbox("Selecione o Estado", estados_disponiveis)

    if data_selecionada and estado_selecionado:
        df_filtered = get_estado_info(df, data_selecionada, estado_selecionado)
        if df_filtered.empty:
            st.warning(f"Nenhum dado encontrado para {estado_selecionado} na data {data_selecionada}.")
        else:
            st.dataframe(df_filtered, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()