import streamlit as st

# Importações restantes e funções de estilo
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles
import logging

# Configuração de logging
logging.basicConfig(level=logging.ERROR)

# Chama estilos após a configuração da página
apply_styles()

# Navegação
navigation = [
    {"icon": "🏠", "label": "Home", "page": "Home.py", "suffix": "home"},
    {"icon": "🚢", "label": "Cabotagem", "page": "pages/cabotagem.py", "suffix": "cab"},
    {"icon": "📦", "label": "Exportação", "page": "pages/exportacao.py", "suffix": "exp"},
    {"icon": "📥", "label": "Importação", "page": "pages/importacao.py", "suffix": "imp"}
]

# Navegação na sidebar
if "dataframe" not in st.session_state or st.session_state["dataframe"].empty:
    st.sidebar.warning("Carregando dados... Navegação desabilitada.")
else:
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
            # Obter URL da planilha a partir dos secrets
            file_id = st.secrets["urls"]["planilha_exportacao"]
            url = f"https://drive.google.com/uc?id={file_id}"

            # Fazer a requisição para obter os dados da planilha
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lança uma exceção em caso de erro
            excel_content = BytesIO(response.content)

            # Ler o arquivo Excel
            df = pd.read_excel(excel_content)

            # Verificar se o DataFrame está vazio
            if df.empty:
                st.error("A planilha está vazia.")
                return pd.DataFrame()

            # Padronizar os nomes das colunas
            df.columns = df.columns.str.strip().str.upper()

            
            # Definir colunas obrigatórias
            required_columns = [
                'DATA EMBARQUE', 'ESTADO EXPORTADOR', 'QTDE CONTEINER', 'PORTO EMBARQUE'
            ]

            # Verificar se as colunas obrigatórias estão presentes
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.error(f"Erro: Colunas ausentes: {', '.join(missing_cols)}")
                return pd.DataFrame()

            # Selecionar apenas colunas relevantes
            selected_columns = [
                'DATA EMBARQUE', 'ESTADO EXPORTADOR', 'QTDE CONTEINER', 'PORTO EMBARQUE',
                'NOME EXPORTADOR', 'ARMADOR', 'NAVIO', 'PORTO DE ORIGEM', 'TERMINAL EMBARQUE',
                'PORTO DESCARGA', 'PORTO DE DESTINO', 'PAÍS DE DESTINO', 'CIDADE EXPORTADOR'
            ]
            existing_columns = [col for col in selected_columns if col in df.columns]
            df = df[existing_columns]

            # Processar e converter colunas
            try:
                # Converter DATA EMBARQUE para datetime
                df['DATA EMBARQUE'] = pd.to_datetime(df['DATA EMBARQUE'], errors='coerce')

                # Converter QTDE CONTEINER para numérico (considerando vírgula como separador decimal)
                df['QTDE CONTEINER'] = df['QTDE CONTEINER'].astype(str).str.replace(',', '.')
                df['QTDE CONTEINER'] = pd.to_numeric(df['QTDE CONTEINER'], errors='coerce').fillna(0)
            except Exception as e:
                st.error(f"Erro ao processar colunas: {str(e)}")
                return pd.DataFrame()

            # Remover linhas com valores obrigatórios ausentes
            df = df.dropna(subset=['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE'])

            # Garantir que o DataFrame não está vazio após o processamento
            if df.empty:
                st.error("Não há dados válidos após o processamento.")
                return pd.DataFrame()

            # Adicionar coluna de data simplificada
            df['DATA EMBARQUE SIMPLIFICADA'] = df['DATA EMBARQUE'].dt.date

            return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao acessar a planilha: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return pd.DataFrame()


def calcular_total_exportacao(df):
    """
    Calcula o total de exportações com base na coluna QTDE CONTEINER.
    """
    try:
        # Verificar se a coluna 'QTDE CONTEINER' está presente
        if 'QTDE CONTEINER' not in df.columns:
            st.write("Colunas disponíveis no DataFrame:", df.columns.tolist())  # Debug
            raise KeyError("Coluna 'QTDE CONTEINER' não encontrada nos dados.")

        # Garantir que os dados estejam no formato correto
        df['QTDE CONTEINER'] = pd.to_numeric(
            df['QTDE CONTEINER'], errors='coerce'
        ).fillna(0)

        # Calcular o total
        return int(df['QTDE CONTEINER'].sum())

    except KeyError as e:
        st.error(f"Erro de chave: {e}")
        return 0
    except Exception as e:
        st.error(f"Erro ao calcular total de exportação: {e}")
        return 0



def display_filtered_details(df, data_inicial, data_final, filtros):
    """
    Exibe os detalhes dos contêineres filtrados por data e outros critérios.
    """
    detalhes = df.copy()
    
    # Aplicando filtro de datas
    detalhes = detalhes[
        (detalhes['DATA EMBARQUE SIMPLIFICADA'] >= data_inicial) &
        (detalhes['DATA EMBARQUE SIMPLIFICADA'] <= data_final)
    ]
    
    # Aplicando outros filtros
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
    
    detalhes_tabela = detalhes[colunas].copy()
    detalhes_tabela['DATA EMBARQUE'] = detalhes_tabela['DATA EMBARQUE'].dt.strftime('%d/%m/%Y')
    detalhes_tabela['QTDE CONTEINER'] = detalhes_tabela['QTDE CONTEINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def create_dropdown(label, df_column, key):
    """
    Cria um dropdown para seleção de filtros.
    """
    if df_column is None or df_column.empty:
        st.warning(f"{label} - Nenhum dado disponível.")
        return "Todos"
    options = df_column.dropna().unique().tolist()
    return st.selectbox(label, ['Todos'] + sorted(map(str, options)), key=key)

def get_dataframe():
    """
    Retorna o dataframe armazenado em session_state, ou carrega se ainda não existir.
    """
    if "dataframe" not in st.session_state or st.session_state["dataframe"].empty:
        with st.spinner('Carregando dados...'):
            df = load_and_process_data()
            if df.empty:
                st.warning("Nenhum dado disponível para carregar.")
                st.stop()
            st.session_state["dataframe"] = df
    return st.session_state["dataframe"]

def main():
    st.markdown('<h1 class="main-title">&#x1F6A2; Previsão de Exportações de Containers</h1>', unsafe_allow_html=True)

    # Verificar se o carregamento está em andamento
    if st.session_state.get("_is_running", False):
        st.warning("Carregamento em andamento... Por favor, aguarde.")
        st.stop()

    st.session_state["_is_running"] = True

    try:
        # Obter dataframe
        df = get_dataframe()

        # Ativar navegação na sidebar após carregamento bem-sucedido
        for idx, nav in enumerate(navigation):
            if st.sidebar.button(
                f"{nav['icon']} {nav['label']}", 
                key=f"exp_nav_{nav['suffix']}_{idx}",  # Garantir keys únicas
                use_container_width=True
            ):
                st.switch_page(nav['page'])

        # Verificar colunas obrigatórias
        required_cols = ['DATA EMBARQUE', 'ESTADO EXPORTADOR', 'PORTO EMBARQUE', 'QTDE CONTEINER']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            st.error(f"Colunas ausentes: {', '.join(missing)}")
            if st.button("Recarregar dados"):
                st.session_state.clear()
                st.rerun()
            return

        # Métricas principais
        total_containers = calcular_total_exportacao(df)
        data_mais_antiga = df['DATA EMBARQUE'].min().strftime('%d/%m/%Y')
        data_mais_recente = df['DATA EMBARQUE'].max().strftime('%d/%m/%Y')
        range_datas = f"{data_mais_antiga} - {data_mais_recente}"

        col1, col2 = st.columns(2)
        with col1:
            st.metric("TOTAL DE CONTAINERS", f"{total_containers:,}", help="Total de containers no período")
        with col2:
            st.metric("PERÍODO DOS DADOS", range_datas, help="Intervalo de datas dos dados disponíveis")

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
                value=data_mais_antiga_dt,
                key="data_inicial"
            )
        with col2:
            data_final = st.date_input(
                "Data Final",
                min_value=data_mais_antiga_dt,
                max_value=data_mais_recente_dt,
                value=data_mais_recente_dt,
                key="data_final"
            )

        # Filtros adicionais
        col1, col2, col3 = st.columns(3)
        with col1:
            estado_selecionado = create_dropdown("Estado Exportador", df.get('ESTADO EXPORTADOR'), "estado")
        with col2:
            porto_selecionado = create_dropdown("Porto de Embarque", df.get('PORTO EMBARQUE'), "porto")
        with col3:
            armador_selecionado = create_dropdown("Armador", df.get('ARMADOR'), "armador")

        filtros = {
            'ESTADO EXPORTADOR': estado_selecionado,
            'PORTO EMBARQUE': porto_selecionado,
            'ARMADOR': armador_selecionado,
        }

        # Aplicar filtros
        df_filtrado = df.copy()
        for coluna, valor in filtros.items():
            if valor != "Todos":
                df_filtrado = df_filtrado[df_filtrado[coluna] == valor]

        df_filtrado = df_filtrado[
            (df_filtrado['DATA EMBARQUE SIMPLIFICADA'] >= data_inicial) &
            (df_filtrado['DATA EMBARQUE SIMPLIFICADA'] <= data_final)
        ]

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            return

        # Pivot table
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

        display_filtered_details(df_filtrado, data_inicial, data_final, filtros)

    except Exception as e:
        logging.error("Erro ao processar os dados na função main", exc_info=True)
        st.error(f"Erro ao processar dados: {str(e)}")
        if st.button("Recarregar dados"):
            st.session_state.clear()
            st.rerun()
    finally:
        st.session_state["_is_running"] = False

if __name__ == "__main__":
    main()
