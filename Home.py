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

st.markdown("""
    <style>
    /* Estilos gerais */
    .stApp {
        background-color: #ffffff;
    }

    div[data-testid="stSidebarNav"] {
        display: none;
    }

    .stSidebar {
        background-color: #f8f9fa;
        padding-top: 2rem;
    }

    .main-container {
        padding: 1rem 2rem;
        max-width: none !important;
    }

    .titulo-dashboard-container {
        width: calc(100% - 2rem);
        margin: 2rem auto;
        padding: 25px 20px;
        background: linear-gradient(to right, #F37529, #f8a676);
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(243, 117, 41, 0.2);
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .titulo-dashboard-container::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
    }

    .titulo-dashboard {
        font-size: 50px;
        font-weight: bold;
        color: #0365B0;
        text-transform: uppercase;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }

    .subtitulo-dashboard {
        font-size: 18px;
        color: #555555;
        margin: 10px 0 0 0;
        font-weight: 500;
    }

    .indicador {
        background: linear-gradient(135deg, #0365B0 0%, #034C8C 100%);
        border-radius: 25px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(3, 101, 176, 0.15);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1rem;
    }

    .indicador h3 {
        color: white;
        margin: 0 0 1rem 0;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .indicador p {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Botões */
    .stButton>button {
        width: 100%;
        text-align: left;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        border: 1px solid rgba(3, 101, 176, 0.2);
        background-color: white;
        font-size: 1rem;
        transition: all 0.3s ease;
        color: #0365B0;
        position: relative;
        overflow: hidden;
    }

    .stButton>button:hover {
        background-color: #0365B0;
        color: white;
        border-color: #0365B0;
        box-shadow: 0 4px 15px rgba(3, 101, 176, 0.2);
        transform: translateX(5px);
    }

    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }

    [data-testid="stImage"] > img {
        width: 200px !important;
        margin: 0 auto;
        transition: all 0.3s ease;
    }

    [data-testid="stImage"]:hover > img {
        transform: scale(1.05);
    }

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

    .funcionalidade {
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: white;
        border-radius: 12px;
        border-left: 4px solid #F37529;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    .funcionalidade:hover {
        transform: translateX(10px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }

    .funcionalidade strong {
        color: #0365B0;
        margin-right: 8px;
    }

    .funcionalidade .icon {
        margin-right: 8px;
        font-size: 1.2rem;
    }

    @media (max-width: 768px) {
        .titulo-dashboard {
            font-size: 35px;
        }

        .main-container {
            padding: 0.5rem;
        }

        .funcionalidade {
            margin: 0.75rem 0;
            padding: 0.75rem 1rem;
        }
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
        <h1 class="titulo-dashboard">TORRE DE CONTROLE ITRACKER - DASHBOARD COMERCIAL</h1>
        <p class="subtitulo-dashboard">Monitorando em tempo real as Operações de Importação, Exportação e Cabotagem</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Conteúdo principal
    st.markdown("""
    <h2>Bem-vindo ao Sistema de Análise de Cargas</h2>
    """, unsafe_allow_html=True)
    st.divider()
    
    if st.sidebar.button("📦 Exportações", use_container_width=True):
        st.switch_page("pages/exportacao.py")
    
    if st.sidebar.button("📥 Importações", use_container_width=True):
        st.switch_page("pages/importacao.py")
    
    if st.sidebar.button("🚢 Cabotagem", use_container_width=True):
        st.switch_page("pages/cabotagem.py")
    
    # Indicadores clicáveis
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="indicador">
                <h3>📦 Exportações</h3>
                <p>4.214</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Exportações 📦", key="exp_btn", use_container_width=True):
            st.switch_page("pages/exportacao.py")

    with col2:
        st.markdown("""
            <div class="indicador">
                <h3>📥 Importações</h3>
                <p>14.987</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Importações 📥", key="imp_btn", use_container_width=True):
            st.switch_page("pages/importacao.py")

    with col3:
        st.markdown("""
            <div class="indicador">
                <h3>🚢 Cabotagem</h3>
                <p>19.217</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Cabotagem 🚢", key="cab_btn", use_container_width=True):
            st.switch_page("pages/cabotagem.py")
    
    st.markdown("""
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
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()