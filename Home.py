import streamlit as st
import pandas as pd
import json
import logging
from PIL import Image
import requests
from io import BytesIO
from utils.data_processing import (
   calcular_total_importacao,
   calcular_total_exportacao,
   calcular_total_cabotagem
)
from style import apply_styles

st.set_page_config(
   page_title="Sistema de Análise de Cargas",
   layout="wide",
   initial_sidebar_state="expanded",
   page_icon="📊"
)

logging.basicConfig(level=logging.ERROR)

navigation = [
   {"icon": "🏠", "label": "Home", "page": "Home.py", "suffix": "home"},
   {"icon": "🚢", "label": "Cabotagem", "page": "pages/cabotagem.py", "suffix": "cab"},
   {"icon": "📦", "label": "Exportação", "page": "pages/exportacao.py", "suffix": "exp"},
   {"icon": "📥", "label": "Importação", "page": "pages/importacao.py", "suffix": "imp"}
]

apply_styles()

st.markdown("""
   <style>
       .titulo-dashboard-container {
           display: flex;
           flex-direction: column;
           justify-content: center;
           align-items: center;
           text-align: center;
           margin: 0 auto;
           padding: 25px 20px;
           background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
           border-radius: 15px;
           box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
       }
       .titulo-dashboard {
           font-size: 50px;
           font-weight: bold;
           color: #F37529;
           text-transform: uppercase;
           margin: 0;
           text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
       }
       .subtitulo-dashboard {
           font-size: 18px;
           color: #555555;
           margin: 10px 0 0 0;
       }
       .logo-container {
           display: flex;
           justify-content: center;
           align-items: center;
           text-align: center;
           margin-bottom: 20px;
       }
       .logo-container img {
           max-width: 200px;
           height: auto;
           filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
       }
       
       .metric-card {
           background: linear-gradient(135deg, #0365B0 0%, #0481e3 100%);
           border-radius: 1rem;
           padding: 2rem 1.5rem;
           height: 100%;
           box-shadow: 0 10px 15px -3px rgba(3, 101, 176, 0.2);
           transition: all 0.3s ease;
           display: flex;
           flex-direction: column;
           align-items: center;
           justify-content: center;
           text-align: center;
           cursor: pointer;
           position: relative;
           overflow: hidden;
       }
       
       .metric-card::before {
           content: '';
           position: absolute;
           top: 0;
           left: 0;
           right: 0;
           bottom: 0;
           background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
           opacity: 0;
           transition: opacity 0.3s ease;
       }
       
       .metric-card:hover {
           transform: translateY(-5px);
           box-shadow: 0 20px 25px -5px rgba(3, 101, 176, 0.25);
       }
       
       .metric-card:hover::before {
           opacity: 1;
       }
       
       .metric-icon {
           background: rgba(255, 255, 255, 0.1);
           border-radius: 50%;
           padding: 1rem;
           margin-bottom: 1rem;
           display: inline-flex;
           align-items: center;
           justify-content: center;
           font-size: 1.5rem;
       }
       
       .metric-title {
           color: white !important;
           font-size: 1.5rem !important;
           font-weight: 600 !important;
           margin: 0.75rem 0 !important;
           letter-spacing: 0.5px;
           text-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       
       .metric-value {
           color: white !important;
           font-size: 2.5rem !important;
           font-weight: 700 !important;
           margin: 0.5rem 0 1.5rem !important;
           text-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       
       .metric-button {
           background: rgba(255, 255, 255, 0.15);
           border: 1px solid rgba(255, 255, 255, 0.3);
           border-radius: 0.75rem;
           padding: 0.75rem 1.5rem;
           transition: all 0.3s ease;
           text-decoration: none;
           color: white !important;
           font-weight: 500;
           letter-spacing: 0.3px;
           width: 100%;
           text-align: center;
           display: flex;
           align-items: center;
           justify-content: center;
           gap: 0.5rem;
       }
       
       .metric-button:hover {
           background: rgba(255, 255, 255, 0.25);
           transform: translateY(-2px);
           box-shadow: 0 4px 6px rgba(0,0,0,0.1);
       }
       
       .metric-button::after {
           content: '→';
           transition: transform 0.3s ease;
           display: inline-block;
           margin-left: 0.5rem;
       }
       
       .metric-button:hover::after {
           transform: translateX(4px);
       }
       
       /* Estilo para Sidebar */
       section[data-testid="stSidebar"] > div {
           background-color: #f8f9fa;
           padding: 1rem;
           box-shadow: 2px 0 5px rgba(0,0,0,0.05);
       }
       section[data-testid="stSidebar"] .stButton > button {
           width: 100%;
           display: flex;
           align-items: center;
           background-color: transparent;
           border: none;
           padding: 0.75rem 1rem;
           text-align: left;
           color: #0C0D0E;
           font-size: 1rem;
           margin: 0.3rem 0;
           border-radius: 0.5rem;
           transition: all 0.2s ease;
       }
       section[data-testid="stSidebar"] .stButton > button:hover {
           background-color: rgba(151, 166, 195, 0.15);
           transform: translateX(2px);
       }
       
       .features-container {
           background: white;
           border-radius: 1rem;
           padding: 2.5rem;
           box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
           margin-top: 2rem;
       }
       .feature-item {
           padding: 1rem;
           border-left: 4px solid #F37529;
           margin-bottom: 1rem;
           background: #f8f9fa;
           border-radius: 0 0.75rem 0.75rem 0;
           box-shadow: 0 2px 4px rgba(0,0,0,0.05);
           transition: all 0.2s ease;
       }
       .feature-item:hover {
           transform: translateX(5px);
           box-shadow: 0 4px 6px rgba(0,0,0,0.1);
       }
   </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_logo():
   try:
       file_id = st.secrets["urls"]["logo"]
       download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
       response = requests.get(download_url)
       response.raise_for_status()
       return Image.open(BytesIO(response.content))
   except Exception as e:
       st.error(f"Erro ao carregar logo: {str(e)}")
       return None

@st.cache_data
def carregar_dados_exportacao():
   try:
       file_id = st.secrets["urls"]["planilha_exportacao"]
       url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
       response = requests.get(url)
       response.raise_for_status()
       return pd.read_excel(BytesIO(response.content))
   except Exception as e:
       st.error(f"Erro ao carregar dados de exportação: {e}")
       return pd.DataFrame()

@st.cache_data
def carregar_dados_importacao():
   try:
       file_id = st.secrets["urls"]["planilha_importacao"]
       url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
       response = requests.get(url)
       response.raise_for_status()
       return pd.read_excel(BytesIO(response.content))
   except Exception as e:
       st.error(f"Erro ao carregar dados de importação: {e}")
       return pd.DataFrame()

@st.cache_data
def carregar_dados_cabotagem():
   try:
       file_id = st.secrets["urls"]["planilha_cabotagem"]
       url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
       response = requests.get(url)
       response.raise_for_status()
       df = pd.read_excel(BytesIO(response.content))
       
       df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'], format='%Y-%m-%d', errors='coerce')
       for col in ['QUANTIDADE C20', 'QUANTIDADE C40']:
           df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)
       df['QUANTIDADE TOTAL'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']
       
       return df
   except Exception as e:
       st.error(f"Erro ao carregar dados de cabotagem: {e}")
       return pd.DataFrame()

def main():
   with st.sidebar:
       for nav in navigation:
           if st.button(
               f"{nav['icon']} {nav['label']}", 
               key=f"nav_{nav['suffix']}", 
               use_container_width=True
           ):
               st.switch_page(nav['page'])

   if st.session_state.get('clear_cache', False):
       st.cache_data.clear()
       st.session_state.clear_cache = False

   logo = carregar_logo()
   if logo:
       col1, col2, col3 = st.columns([2, 1, 2])
       with col2:
           st.markdown('<div class="logo-container">', unsafe_allow_html=True)
           st.image(logo, use_container_width=False, width=150)
           st.markdown('</div>', unsafe_allow_html=True)
       
       st.markdown("""
           <div class="titulo-dashboard-container">
               <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard Comercial</h1>
               <p class="subtitulo-dashboard">Monitorando em tempo-real as Operações de Importação, Exportação e Cabotagem</p>
           </div>
       """, unsafe_allow_html=True)


       st.divider()

   df_exp = carregar_dados_exportacao()
   df_imp = carregar_dados_importacao()
   df_cab = carregar_dados_cabotagem()

   col1, col2, col3 = st.columns(3)

   with col1:
       st.markdown(
           f"""
           <div class="metric-card">
               <div class="metric-icon">📦</div>
               <h3 class="metric-title">EXPORTAÇÕES</h3>
               <p class="metric-value">{calcular_total_exportacao(df_exp)}</p>
           </div>
           """,
           unsafe_allow_html=True
       )
       if st.button("Visualizar Exportações", key="btn_exp", use_container_width=True):
           st.switch_page("pages/exportacao.py")

   with col2:
       st.markdown(
           f"""
           <div class="metric-card">
               <div class="metric-icon">📥</div>
               <h3 class="metric-title">IMPORTAÇÕES</h3>
               <p class="metric-value">{calcular_total_importacao(df_imp)}</p>
           </div>
           """,
           unsafe_allow_html=True
       )
       if st.button("Visualizar Importações", key="btn_imp", use_container_width=True):
           st.switch_page("pages/importacao.py")

   with col3:
       st.markdown(
           f"""
           <div class="metric-card">
               <div class="metric-icon">🚢</div>
               <h3 class="metric-title">CABOTAGEM</h3>
               <p class="metric-value">{calcular_total_cabotagem(df_cab)}</p>
           </div>
           """,
           unsafe_allow_html=True
       )
       if st.button("Visualizar Cabotagem", key="btn_cab", use_container_width=True):
           st.switch_page("pages/cabotagem.py")

   st.markdown("""
       <div class="features-container">
           <h3 style="color: #0365B0; margin-bottom: 1.5rem; text-align: center; font-size: 1.3rem; font-weight: 600; letter-spacing: 0.5px;">
               Este sistema permite analisar dados de:
           </h3>
           <div class="feature-item">
               <strong style="color: #2c3e50; font-weight: 600;">Exportações:</strong>
               <span style="color: #2c3e50; margin-left: 0.5rem; font-weight: 500;">Acompanhamento de exportações por estado</span>
           </div>
           <div class="feature-item">
               <strong style="color: #2c3e50; font-weight: 600;">Importações:</strong>
               <span style="color: #2c3e50; margin-left: 0.5rem; font-weight: 500;">Monitoramento de importações e chegadas</span>
           </div>
           <div class="feature-item">
               <strong style="color: #2c3e50; font-weight: 600;">Cabotagem:</strong>
               <span style="color: #2c3e50; margin-left: 0.5rem; font-weight: 500;">Análise de operações de cabotagem</span>
           </div>
       </div>
   """, unsafe_allow_html=True)

if __name__ == "__main__":
   main()