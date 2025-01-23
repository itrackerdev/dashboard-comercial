import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import os
import requests
from io import BytesIO
from style import apply_styles


st.set_page_config(
    page_title="Previsão de Cabotagem",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚢"
)

# Função para baixar arquivo do Google Drive
def download_file_from_drive(file_id):
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"Erro ao baixar arquivo: {e}")
        return None

# Função para remover duplicatas
def remove_duplicates(df):
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

# Função para criar ID único
def create_unique_id_safe(row):
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

# Função para carregar e processar dados
def load_and_process_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/1kvjmYigg06aEOrgFG4gRFwzCIjTrns2P/export?format=xlsx"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), dtype=str)

        # Conversão de data
        df['DATA DE EMBARQUE'] = pd.to_datetime(
            df['DATA DE EMBARQUE'], format='%Y-%m-%d', errors='coerce', dayfirst=True
        )

        # Corrigir formato de números com vírgula e calcular quantidade total de contêineres
        for col in ['QUANTIDADE C20', 'QUANTIDADE C40']:
            df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)

        # Adicionar coluna para quantidade total de contêineres
        df['QUANTIDADE TOTAL'] = df['QUANTIDADE C20'] + df['QUANTIDADE C40']

        # Criar coluna ID_UNICO
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Função para retornar informações por estado
def get_estado_info(df, data, uf):
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

# Função para formatar data com segurança
def format_date_safe(date):
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
    apply_styles()
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
        st.metric("Total de Registros", f"{len(df):,}", help="Quantidade total de registros processados.")
    with col2:
        ultima_atualizacao = format_date_safe(df['DATA DE EMBARQUE'].max())
        st.metric("Última Atualização", ultima_atualizacao, help="Data mais recente nos dados.")

    # Resumo de Operações
    st.markdown('<h3 class="subheader">Resumo de Operações</h3>', unsafe_allow_html=True)
    summary_df = create_state_summary_table(df, view_type='destinatario')

    # Verificar se o resumo contém dados
    if summary_df.empty:
        st.warning("Nenhum dado disponível para exibição no resumo de operações.")
    else:
        st.dataframe(summary_df, use_container_width=True)

    # Detalhamento por estado
    st.markdown('<h3 class="subheader">Detalhamento por Estado</h3>', unsafe_allow_html=True)

    # Seleção de data
    datas_disponiveis = get_formatted_dates(df)
    if not datas_disponiveis:
        st.warning("Nenhuma data disponível para seleção.")
        return

    col1, col2 = st.columns(2)
    with col1:
        data_selecionada = st.selectbox("Selecione a Data", datas_disponiveis)

    # Seleção de estado
    estados_disponiveis = sorted(df['DESTINATÁRIO - ESTADO'].dropna().unique())
    with col2:
        estado_selecionado = st.selectbox("Selecione o Estado", estados_disponiveis)

    # Filtrar e exibir detalhes
    if data_selecionada and estado_selecionado:
        df_filtered = get_estado_info(df, data_selecionada, estado_selecionado)
        if df_filtered.empty:
            st.warning(f"Nenhum dado encontrado para {estado_selecionado} na data {data_selecionada}.")
        else:
            st.dataframe(df_filtered, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Chamar a função principal
if __name__ == "__main__":
    main()
