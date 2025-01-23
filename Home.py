import streamlit as st

st.set_page_config(
    page_title="Sistema de Análise de Cargas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏠",
    menu_items=None
)

import pandas as pd
import json
import os
from PIL import Image
import requests
from io import BytesIO
from style import apply_styles

apply_styles()

# Carregar configurações
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

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
    # Sidebar navigation
    if st.sidebar.button("🏠 Home", key="home_btn", use_container_width=True):
        st.switch_page("Home.py")
    if st.sidebar.button("🚢 Cabotagem", key="cab_side_btn", use_container_width=True):
        st.switch_page("pages/cabotagem.py")
    if st.sidebar.button("📦 Exportação", key="exp_side_btn", use_container_width=True):
        st.switch_page("pages/exportacao.py")
    if st.sidebar.button("📥 Importação", key="imp_side_btn", use_container_width=True):
        st.switch_page("pages/importacao.py")

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Logo centralizada
    logo = carregar_logo()
    if logo:
        col1, col2, col3 = st.columns([2,1,2])
        with col2:
            st.image(logo, width=200)

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

    # Indicadores clicáveis
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="indicador">
                <h3>📦 Exportações</h3>
                <p>4.214</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Acessar Exportações 📦", key="exp_main_btn", use_container_width=True):
            st.switch_page("pages/exportacao.py")

    with col2:
        st.markdown(
            """
            <div class="indicador">
                <h3>📥 Importações</h3>
                <p>14.987</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Acessar Importações 📥", key="imp_main_btn", use_container_width=True):
            st.switch_page("pages/importacao.py")

    with col3:
        st.markdown(
            """
            <div class="indicador">
                <h3>🚢 Cabotagem</h3>
                <p>19.217</p>
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
    main()