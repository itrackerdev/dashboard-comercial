import pandas as pd
import requests
from io import BytesIO
import hashlib
import logging
import streamlit as st

def calcular_total_importacao(df):
    """
    Calcula o total de contêineres de importação.
    """
    try:
        if df is None or df.empty:
            return "0"
        
        # Verificar se a coluna existe
        if 'QTDE CONTAINER' not in df.columns:
            return "0"
            
        # Converter valores de string para número
        if df['QTDE CONTAINER'].dtype == 'object':
            df['QTDE CONTAINER'] = pd.to_numeric(
                df['QTDE CONTAINER'].str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
        
        total = df['QTDE CONTAINER'].sum()
        return f"{total:,.0f}".replace(",", ".")
    except Exception as e:
        logging.error(f"Erro ao calcular total de importação: {e}")
        return "0"

def calcular_total_exportacao(df):
    """
    Calcula o total de contêineres de exportação.
    """
    try:
        if df is None or df.empty:
            return "0"
        
        # Verificar se a coluna existe
        if 'QTDE CONTEINER' not in df.columns:
            return "0"
            
        # Converter valores de string para número
        if df['QTDE CONTEINER'].dtype == 'object':
            df['QTDE CONTEINER'] = pd.to_numeric(
                df['QTDE CONTEINER'].str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
        
        total = df['QTDE CONTEINER'].sum()
        return f"{total:,.0f}".replace(",", ".")
    except Exception as e:
        logging.error(f"Erro ao calcular total de exportação: {e}")
        return "0"

def calcular_total_cabotagem(df):
    """
    Calcula o total de contêineres de cabotagem.
    """
    try:
        if df is None or df.empty:
            return "0"
        
        # Verificar se as colunas existem
        if 'QUANTIDADE C20' not in df.columns or 'QUANTIDADE C40' not in df.columns:
            return "0"
            
        # Converter valores de string para número
        for col in ['QUANTIDADE C20', 'QUANTIDADE C40']:
            if df[col].dtype == 'object':
                df[col] = pd.to_numeric(
                    df[col].str.replace(',', '.'), 
                    errors='coerce'
                ).fillna(0)
        
        total = df['QUANTIDADE C20'].sum() + df['QUANTIDADE C40'].sum()
        return f"{total:,.0f}".replace(",", ".")
    except Exception as e:
        logging.error(f"Erro ao calcular total de cabotagem: {e}")
        return "0"

def create_unique_id_safe(row):
    """
    Cria um ID único para cada linha do DataFrame de forma segura.
    """
    try:
        # Concatena os valores das colunas relevantes
        values = [
            str(row.get('DATA DE EMBARQUE', '')),
            str(row.get('QUANTIDADE C20', 0)),
            str(row.get('QUANTIDADE C40', 0))
        ]
        
        # Cria uma string única
        unique_string = '_'.join(values)
        
        # Gera um hash SHA-256
        return hashlib.sha256(unique_string.encode()).hexdigest()
    except Exception as e:
        logging.error(f"Erro ao criar ID único: {e}")
        return None

def limpar_numero(valor):
    """Limpa um valor numérico, tratando vírgula como separador decimal"""
    if pd.isna(valor):
        return 0
    try:
        if isinstance(valor, (int, float)):
            return float(valor)
        
        valor_str = str(valor).strip()
        if not valor_str:
            return 0
            
        # Substitui vírgula por ponto para conversão
        valor_str = valor_str.replace(',', '.')
        
        return float(valor_str)
        
    except Exception as e:
        st.error(f"Erro ao limpar número: {valor} - {str(e)}")
        return 0

@st.cache_data
def carregar_dados_exportacao():
    """Carrega os dados de exportação"""
    try:
        file_id = st.secrets["urls"]["planilha_exportacao"]
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content))
        df['QTDE CONTEINER'] = df['QTDE CONTEINER'].apply(limpar_numero)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de exportação: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_dados_importacao():
    """Carrega os dados de importação"""
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content))
        df['QTDE CONTAINER'] = df['QTDE CONTAINER'].apply(limpar_numero)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de importação: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_dados_cabotagem():
    """Carrega os dados de cabotagem"""
    try:
        file_id = st.secrets["urls"]["planilha_cabotagem"]
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content))
        
        # Processamento específico para cabotagem
        df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'], format='%Y-%m-%d', errors='coerce')
        for col in ['QUANTIDADE C20', 'QUANTIDADE C40']:
            df[col] = df[col].apply(limpar_numero)
        df['QUANTIDADE TOTAL'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de cabotagem: {e}")
        return pd.DataFrame()

def calcular_total_exportacao(df):
    if df.empty:
        return "0"
    try:
        df['QTDE CONTEINER'] = df['QTDE CONTEINER'].apply(lambda x: str(x).replace(',', '.'))
        total = df['QTDE CONTEINER'].astype(float).sum()
        return str(int(total))
    except Exception as e:
        st.error(f"Erro ao calcular total de exportações: {e}")
        return "0"

def calcular_total_importacao(df):
    if df.empty:
        return "0"
    try:
        df['QTDE CONTAINER'] = df['QTDE CONTAINER'].apply(lambda x: str(x).replace(',', '.'))
        total = df['QTDE CONTAINER'].astype(float).sum()
        return str(int(total))
    except Exception as e:
        st.error(f"Erro ao calcular total de importações: {e}")
        return "0"


def calcular_total_cabotagem(df):
    """Calcula o total de cabotagem"""
    if df.empty:
        return "0"
    try:
        total = int(df['QUANTIDADE TOTAL'].astype(float).sum())
        return str(total)
    except Exception as e:
        st.error(f"Erro ao calcular total de cabotagem: {e}")
        return "0"
