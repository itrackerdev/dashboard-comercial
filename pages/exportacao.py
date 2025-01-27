import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles
import logging

# Configuração da página
st.set_page_config(
    page_title="Sistema de Análise de Cargas - Exportação",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦"
)

# Configuração de logging
logging.basicConfig(level=logging.ERROR)

# Aplicar estilos
apply_styles()

# Navegação
navigation = [
    {"icon": "🏠", "label": "Home", "page": "Home.py", "suffix": "home"},
    {"icon": "🚢", "label": "Cabotagem", "page": "pages/cabotagem.py", "suffix": "cab"},
    {"icon": "📦", "label": "Exportação", "page": "pages/exportacao.py", "suffix": "exp"},
    {"icon": "📥", "label": "Importação", "page": "pages/importacao.py", "suffix": "imp"}
]

# Navegação na sidebar
for nav in navigation:
    if st.sidebar.button(
        f"{nav['icon']} {nav['label']}", 
        key=f"exp_nav_{nav['suffix']}", 
        use_container_width=True
    ):
        st.switch_page(nav['page'])

@st.cache_data(ttl=3600)
def load_and_process_data():
    """
    Carrega e processa os dados da planilha de exportação.
    """
    try:
        with st.spinner('Carregando dados...'):
            file_id = st.secrets["urls"]["planilha_exportacao"]
            url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            excel_content = BytesIO(response.content)
            
            df = pd.read_excel(excel_content)
            
            if df.empty:
                raise ValueError("A planilha está vazia.")
                
            df.columns = df.columns.str.strip().str.upper()
            
            required_columns = [
                'DATA EMBARQUE', 'ESTADO EXPORTADOR', 'QTDE CONTEINER', 'PORTO EMBARQUE'
            ]
            
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Colunas ausentes: {', '.join(missing_cols)}")
            
            df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')
            df['QTDE CONTEINER'] = pd.to_numeric(
                df['QTDE CONTEINER'].astype(str).str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
            
            df = df.dropna(subset=['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])
            
            if df.empty:
                raise ValueError("Dados inválidos após processamento.")
            
            df['DATA EMBARQUE SIMPLIFICADA'] = df['DATA EMBARQUE'].dt.date
            
            return df
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def display_filtered_details(df, data_inicial, data_final, filtros):
    """
    Exibe os detalhes dos contêineres filtrados por data e outros critérios.
    """
    detalhes = df.copy()
    
    detalhes = detalhes[
        (detalhes['DATA EMBARQUE SIMPLIFICADA'] >= data_inicial) &
        (detalhes['DATA EMBARQUE SIMPLIFICADA'] <= data_final)
    ]
    
    for coluna, valor in filtros.items():
        if valor and valor != "Todos" and coluna in detalhes.columns:
            detalhes = detalhes[detalhes[coluna] == valor]

    if detalhes.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas = [
        'DATA EMBARQUE', 'NOME EXPORTADOR', 'NAVIO', 'PORTO DE ORIGEM', 'PORTO EMBARQUE',
        'TERMINAL EMBARQUE', 'PORTO DESCARGA', 'PORTO DE DESTINO', 
        'PAÍS DE DESTINO', 'CIDADE EXPORTADOR', 'ESTADO EXPORTADOR',
        'ARMADOR', 'QTDE CONTEINER'
    ]
    
    colunas_existentes = [col for col in colunas if col in detalhes.columns]
    detalhes_tabela = detalhes[colunas_existentes].copy()
    
    if 'DATA EMBARQUE' in detalhes_tabela.columns:
        detalhes_tabela['DATA EMBARQUE'] = detalhes_tabela['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
    
    if 'QTDE CONTEINER' in detalhes_tabela.columns:
        detalhes_tabela['QTDE CONTEINER'] = detalhes_tabela['QTDE CONTEINER'].apply(
            lambda x: f"{int(x):,}" if x > 0 else "-"
        )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def create_dropdown(label, df_column, key):
    """
    Cria um dropdown para seleção de filtros.
    """
    if df_column is None:
        return "Todos"
    options = df_column.dropna().unique().tolist()
    return st.selectbox(label, ['Todos'] + sorted(map(str, options)), key=key)

def main():
    st.markdown('<h1 class="main-title">📦 Previsão de Exportações de Containers</h1>', unsafe_allow_html=True)

    if st.session_state.get("_is_running", False):
        st.warning("Carregamento em andamento...")
        st.stop()

    st.session_state["_is_running"] = True

    try:
        df = load_and_process_data()
        if df.empty:
            st.error("Não foi possível carregar os dados.")
            st.stop()

        # Métricas principais
        total_containers = int(df['QTDE CONTEINER'].sum())
        data_mais_antiga = df['DATA EMBARQUE'].min().strftime('%d/%m/%Y')
        data_mais_recente = df['DATA EMBARQUE'].max().strftime('%d/%m/%Y')
        range_datas = f"{data_mais_antiga} - {data_mais_recente}"

        col1, col2 = st.columns(2)
        with col1:
            st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}")
        with col2:
            st.metric("PERÍODO DOS DADOS", range_datas)

        # Filtros principais
        st.markdown('<h3 class="subheader">Filtros</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            data_mais_antiga_dt = df['DATA EMBARQUE'].min().date()
            data_mais_recente_dt = df['DATA EMBARQUE'].max().date()
            data_inicial = st.date_input(
                "Data Inicial",
                min_value=data_mais_antiga_dt,
                max_value=data_mais_recente_dt,
                value=data_mais_antiga_dt
            )
        with col2:
            data_final = st.date_input(
                "Data Final",
                min_value=data_mais_antiga_dt,
                max_value=data_mais_recente_dt,
                value=data_mais_recente_dt
            )

        # Filtros Primários
        col1, col2, col3 = st.columns(3)
        with col1:
            estado_selecionado = create_dropdown("Estado Exportador", df['ESTADO EXPORTADOR'], "estado")
        with col2:
            porto_selecionado = create_dropdown("Porto de Embarque", df['PORTO EMBARQUE'], "porto")
        with col3:
            armador_selecionado = create_dropdown("Armador", df.get('ARMADOR'), "armador")

        # Filtros Secundários
        with st.expander("Filtros Adicionais"):
            col4, col5, col6 = st.columns(3)
            with col4:
                pais_procedencia = create_dropdown("País de Procedência", df.get('PAÍS DE PROCEDÊNCIA'), "pais_proc")
            with col5:
                tipo_embarque = create_dropdown("Tipo de Embarque", df.get('TIPO EMBARQUE'), "tipo_emb")
            with col6:
                atividade_exportador = create_dropdown("Atividade Exportador", df.get('ATIVIDADE EXPORTADOR'), "atividade_exp")

            col7, col8, col9 = st.columns(3)
            with col7:
                trade_lane = create_dropdown("Trade Lane", df.get('TRADE LANE'), "trade_lane")
            with col8:
                tipo_container = create_dropdown("Tipo de Contêiner", df.get('TIPO CONTEINER'), "tipo_cont")
            with col9:
                mercadoria = create_dropdown("Mercadoria", df.get('MERCADORIA'), "mercadoria")

        # Aplicar filtros
        filtros = {
            'ESTADO EXPORTADOR': estado_selecionado,
            'PORTO EMBARQUE': porto_selecionado,
            'ARMADOR': armador_selecionado,
            'PAÍS DE PROCEDÊNCIA': pais_procedencia,
            'TIPO EMBARQUE': tipo_embarque,
            'ATIVIDADE EXPORTADOR': atividade_exportador,
            'TRADE LANE': trade_lane,
            'TIPO CONTEINER': tipo_container,
            'MERCADORIA': mercadoria
        }

        df_filtrado = df.copy()
        df_filtrado = df_filtrado[
            (df_filtrado['DATA EMBARQUE SIMPLIFICADA'] >= data_inicial) &
            (df_filtrado['DATA EMBARQUE SIMPLIFICADA'] <= data_final)
        ]
        
        for coluna, valor in filtros.items():
            if valor != "Todos" and coluna in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[coluna] == valor]

        if not df_filtrado.empty:
            # Tabela pivot
            dados_pivot = df_filtrado.groupby(['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])['QTDE CONTEINER'].sum().reset_index()
            tabela_pivot = dados_pivot.pivot_table(
                index='DATA EMBARQUE',
                columns=['ESTADO EXPORTADOR', 'PORTO EMBARQUE'],
                values='QTDE CONTEINER',
                aggfunc='sum'
            ).fillna(0)

            tabela_pivot = tabela_pivot.sort_index(ascending=False)
            tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

            st.markdown('<h3 class="subheader">Previsão de Embarques por Estado e Porto</h3>', unsafe_allow_html=True)
            tabela_formatada = tabela_pivot.copy().reset_index()
            tabela_formatada['DATA EMBARQUE'] = tabela_formatada['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
            st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

            # Detalhes dos containers
            display_filtered_details(df, data_inicial, data_final, filtros)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        if st.button("Recarregar página"):
            st.rerun()
    finally:
        st.session_state["_is_running"] = False

if __name__ == "__main__":
    main()
