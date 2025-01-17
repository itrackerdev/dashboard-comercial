import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
import requests
from io import BytesIO

# Carregar configurações
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

st.set_page_config(
    page_title="Sistema de Análise de Cargas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏠",
    menu_items=None
)

# Configuração do tema e estilo
st.markdown("""
    <style>
        /* Container e estilo do título principal */
        .main-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            padding: 0;
            margin: 0 auto;
        }
        .logo-container {
            width: 100%;
            padding: 0 1rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: center;
        }
        .logo-image {
            display: block;
            width: 200px;
            margin: 0 auto;
        }
        .titulo-dashboard-container {
            width: calc(100% - 2rem);
            margin: 0 auto;
            padding: 25px 20px;
            background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .titulo-dashboard {
            font-size: 50px;
            font-weight: bold;
            color: #F37529;
            text-transform: uppercase;
            margin: 0;
        }
        .subtitulo-dashboard {
            font-size: 18px;
            color: #555555;
            margin: 10px 0 0 0;
        }

        /* Estilização dos indicadores principais */
        .indicadores-container {
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            gap: 20px;
            margin: 30px 0;
            padding: 0 20px;
        }
        .indicador {
            flex: 1;
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .indicador h3 {
            color: #F37529;
            margin: 0 0 10px 0;
            font-size: 18px;
        }
        .indicador p {
            color: #0066B4;
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }

        /* Estilização dos botões da sidebar */
        .stButton>button {
            width: 100%;
            text-align: left;
            padding: 16px 20px;
            margin: 4px 0px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            background-color: white;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #F37529;
            color: white;
            border-color: #F37529;
        }

        /* Ajustes gerais do layout */
        .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        .stSidebar {
            background-color: #f8f9fa;
            padding-top: 2rem;
        }
        div[data-testid="stSidebarNav"] {
            display: none;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Reset de margens e padding */
        div[data-testid="stAppViewContainer"] > div:nth-child(1) {
            padding: 1rem 1rem;
        }

        /* Container da logo */
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }

        [data-testid="stImage"] > img {
            width: 200px !important;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)

def carregar_logo():
    try:
        url = config['urls']['logo']
        file_id = url.split('/')[5]
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(download_url)
        if response.status_code != 200:
            return None
        img_data = BytesIO(response.content)
        img = Image.open(img_data)
        return img
    except:
        return None

def main():
    # Removendo padding padrão do Streamlit
    st.markdown("""
        <style>
        .block-container {
            padding: 1rem;
        }
        
        /* Ajuste da imagem */
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }
        
        [data-testid="stImage"] img {
            width: 200px !important;
        }
        
        /* Removendo padding das colunas */
        [data-testid="column"] {
            padding: 0 !important;
        }

        /* Centralizando o conteúdo das colunas */
        div[data-testid="column"] > div {
            display: flex;
            justify-content: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Logo centralizada
    logo = carregar_logo()
    if logo:
        col1, col2, col3 = st.columns([2,1,2])
        with col2:
            st.image(logo, width=200)
    
    # Header com título
    st.markdown("""
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">TORRE DE CONTROLE ITRACKER - DASHBOARD Comercial</h1>
        <p class="subtitulo-dashboard">Monitorando em tempo real as Operações de Importação, Exportação e Cabotagem</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navegação na sidebar
    st.sidebar.markdown("### Navegação")
    
    if st.sidebar.button("📦 Exportações", use_container_width=True):
        st.switch_page("pages/exportacao.py")
    
    if st.sidebar.button("📥 Importações", use_container_width=True):
        st.switch_page("pages/importacao.py")
    
    if st.sidebar.button("🚢 Cabotagem", use_container_width=True):
        st.switch_page("pages/cabotagem.py")
    
    # Indicadores
    st.markdown("""
    <div class="indicadores-container">
        <div class="indicador">
            <h3>📦 Exportações</h3>
            <p>4.214</p>
        </div>
        <div class="indicador">
            <h3>📥 Importações</h3>
            <p>14.987</p>
        </div>
        <div class="indicador">
            <h3>🚢 Cabotagem</h3>
            <p>19.217</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal
    st.markdown("## Bem-vindo ao Sistema de Análise de Cargas")
    st.markdown("Este sistema permite analisar dados de:")
    st.markdown("""
    * **Exportações**: Acompanhamento de exportações por estado
    * **Importações**: Monitoramento de importações e chegadas
    * **Cabotagem**: Análise de operações de cabotagem
    """)
    st.markdown("Selecione uma opção no menu lateral para começar.")

if __name__ == "__main__":
    main()
