import streamlit as st
st.cache_data.clear()  # Limpa o cache ao executar o script

st.set_page_config(
    page_title="Sistema de Análise de Cargas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏠",
    menu_items=None
)

import pandas as pd
import json
from PIL import Image
import requests
from io import BytesIO
from style import apply_styles
from pages.importacao import calcular_total_importacao
from pages.exportacao import calcular_total_exportacao

apply_styles()

# Carregar configurações
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    st.error("Arquivo de configuração 'config.json' não encontrado.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Erro ao interpretar 'config.json': {e}")
    st.stop()

@st.cache_data(ttl=3600)
def carregar_planilha(file_id, colunas_obrigatorias):
    """
    Carrega uma planilha do Google Drive e verifica se as colunas obrigatórias existem.
    """
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), dtype=str)

        # Padronizar colunas
        df.columns = df.columns.str.strip().str.upper()

        # Verificar se todas as colunas obrigatórias estão presentes
        for col in colunas_obrigatorias:
            if col not in df.columns:
                st.error(f"Coluna obrigatória '{col}' não encontrada na planilha.")
                return pd.DataFrame()

        return df
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return pd.DataFrame()

def calcular_total_cabotagem():
    df = carregar_planilha(
        st.secrets["urls"]["planilha_cabotagem"], 
        ['QUANTIDADE C20', 'QUANTIDADE C40']
    )
    if df.empty:
        return 0

    # Processar as colunas
    df['QUANTIDADE C20'] = pd.to_numeric(df['QUANTIDADE C20'].str.replace(',', '.'), errors='coerce').fillna(0)
    df['QUANTIDADE C40'] = pd.to_numeric(df['QUANTIDADE C40'].str.replace(',', '.'), errors='coerce').fillna(0)

    return int(df['QUANTIDADE C20'].sum() + df['QUANTIDADE C40'].sum())



def carregar_dados_exportacao():
    df = carregar_planilha(
        st.secrets["urls"]["planilha_exportacao"], 
        ['QTDE CONTEINER']
    )
    if df.empty:
        return 0, df

    # Processar a coluna "QTDE CONTEINER"
    df['QTDE CONTEINER'] = pd.to_numeric(
        df['QTDE CONTEINER'].str.replace(',', '.'), errors='coerce'
    ).fillna(0)

    total = int(df['QTDE CONTEINER'].sum())
    return total, df

def carregar_logo():
    try:
        url = config['urls']['logo']
        try:
            file_id = url.split('/')[5]
        except IndexError:
            st.error("Erro ao extrair o ID do Google Drive. Verifique a URL configurada.")
            return None

        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(download_url)
        if response.status_code != 200:
            st.error("Erro ao carregar o logo. Verifique a URL.")
            return None

        img_data = BytesIO(response.content)
        img = Image.open(img_data)
        return img
    except KeyError:
        st.error("O campo 'logo' não está configurado corretamente no arquivo 'config.json'.")
        st.stop()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar o logo: {e}")
        return None

def create_sidebar():
    if st.session_state.get("sidebar_initialized", False):
        return  # Impede re-execução desnecessária
    st.session_state.sidebar_initialized = True

    navigation = [
        {"icon": "🏠", "label": "Home", "page": "Home", "suffix": "home"},
        {"icon": "🚢", "label": "Cabotagem", "page": "pages/cabotagem", "suffix": "cab"},
        {"icon": "📦", "label": "Exportação", "page": "pages/exportacao", "suffix": "exp"},
        {"icon": "📥", "label": "Importação", "page": "pages/importacao", "suffix": "imp"}
    ]

    for idx, nav in enumerate(navigation):
        if st.sidebar.button(
            f"{nav['icon']} {nav['label']}",
            key=f"nav_{nav['suffix']}_{idx}",
            use_container_width=True
        ):
            st.switch_page(nav['page'])



def formatar_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except ValueError:
        return "0"

def main():
    # Garantir que a sidebar seja criada apenas uma vez
    if "sidebar_initialized" not in st.session_state:
        st.session_state.sidebar_initialized = False

    # Criar sidebar apenas na inicialização
    if not st.session_state.sidebar_initialized:
        create_sidebar()
        st.session_state.sidebar_initialized = True  # Marcar como inicializada

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Logo centralizada
    logo = carregar_logo()
    if logo:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.image(logo, width=200)
    else:
        st.warning("Logo não carregada. Verifique o arquivo de configuração.")

    # Header com título
    st.markdown(
        """
        <div class="titulo-dashboard-container">
            <h1 class="titulo-dashboard">TORRE DE CONTROLE ITRACKER - DASHBOARD COMERCIAL</h1>
            <p class="subtitulo-dashboard">Monitorando em tempo real as Operações de Importação, Exportação e Cabotagem</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # Conteúdo principal
    st.markdown("<h2>Bem-vindo ao Sistema de Análise de Cargas</h2>", unsafe_allow_html=True)
    st.divider()

    # Calcular totais dinamicamente
    try:
        total_exportacao, df_exportacao = carregar_dados_exportacao()
        if total_exportacao == 0:
            st.warning("Nenhum dado válido de exportação encontrado.")
    except Exception as e:
        total_exportacao = "Erro"
        st.error(f"Erro ao carregar total de exportações: {e}")

    try:
        total_importacao = calcular_total_importacao()
    except Exception as e:
        total_importacao = "Erro"
        st.error(f"Erro ao carregar total de importações: {e}")

    try:
        total_cabotagem = calcular_total_cabotagem()
    except Exception as e:
        total_cabotagem = "Erro"
        st.error(f"Erro ao carregar total de cabotagem: {e}")

    # Indicadores clicáveis
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="indicador">
                <h3>📦 Exportações</h3>
                <p>{formatar_numero(total_exportacao)}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Acessar Exportações 📦", key="exp_main_btn", use_container_width=True):
            st.switch_page("pages/exportacao.py")

    with col2:
        st.markdown(
            f"""
            <div class="indicador">
                <h3>📥 Importações</h3>
                <p>{total_importacao}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Acessar Importações 📥", key="imp_main_btn", use_container_width=True):
            st.switch_page("pages/importacao.py")

    with col3:
        st.markdown(
            f"""
            <div class="indicador">
                <h3>🚢 Cabotagem</h3>
                <p>{total_cabotagem}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Acessar Cabotagem 🚢", key="cab_main_btn", use_container_width=True):
            st.switch_page("pages/cabotagem.py")

    st.markdown(
        """
        <div style='background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <p style='font-size: 1.1rem; color: #333; margin-bottom: 1.5rem;'>Este sistema permite analisar dados de:</p>
            <div class="funcionalidades-container">
                <div class="funcionalidade">
                    <span class="icon">📦</span>
                    <strong>Exportações:</strong>
                    <span class="descricao">Acompanhamento de exportações por estado</span>
                </div>
                <div class="funcionalidade">
                    <span class="icon">📥</span>
                    <strong>Importações:</strong>
                    <span class="descricao">Monitoramento de importações e chegadas</span>
                </div>
                <div class="funcionalidade">
                    <span class="icon">🚢</span>
                    <strong>Cabotagem:</strong>
                    <span class="descricao">Análise de operações de cabotagem</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    # Configuração inicial para garantir a execução única da sidebar
    if "sidebar_initialized" not in st.session_state:
        st.session_state.sidebar_initialized = False

    main()
