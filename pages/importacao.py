import streamlit as st



# Importações restantes e funções de estilo
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from style import apply_styles

# Aplicação de estilos vem depois da configuração inicial
apply_styles()

# No início do arquivo, após os imports
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
        key=f"imp_nav_{nav['suffix']}", 
        use_container_width=True
    ):
        st.switch_page(nav['page'])


@st.cache_data(ttl=3600)
def load_and_process_data():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)
        
        df = pd.read_excel(excel_content)
        
        if df.empty:
            raise ValueError("A planilha está vazia.")
            
        df.columns = df.columns.str.strip().str.upper()
        
        required_cols = ['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA', 'QTDE CONTAINER']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Colunas ausentes: {', '.join(missing_cols)}")
        
        df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce')
        df['QTDE CONTAINER'] = pd.to_numeric(df['QTDE CONTAINER'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        df = df.dropna(subset=['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])
        
        if df.empty:
            raise ValueError("Dados inválidos após processamento.")
            
        return df
            
    except Exception as e:
        st.error(str(e))
        if st.button("Recarregar página"):
            st.session_state.clear()
            st.experimental_rerun()
        return pd.DataFrame()

    
def calcular_total_importacao():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        excel_content = BytesIO(response.content)
        
        df = pd.read_excel(excel_content)
        df['QTDE CONTAINER'] = pd.to_numeric(
            df['QTDE CONTAINER'].str.replace(',', '.'), errors='coerce'
        ).fillna(0)
        
        return int(df['QTDE CONTAINER'].sum())
    except Exception as e:
        st.error(f"Erro ao calcular total de importação: {e}")
        return 0

def display_filtered_details(df, data_inicial, data_final, filtros):
    detalhes = df.copy()
    
    detalhes = detalhes[
        (detalhes['ETA'].dt.date >= data_inicial) &
        (detalhes['ETA'].dt.date <= data_final)
    ]
    
    for coluna, valor in filtros.items():
        if valor and valor != "Todos" and coluna in detalhes.columns:
            detalhes = detalhes[detalhes[coluna] == valor]

    if detalhes.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown('<h3 class="subheader">Detalhes dos Containers</h3>', unsafe_allow_html=True)
    
    colunas = [col for col in [
        'ETA', 'CONSIGNATARIO FINAL', 'CONSOLIDADOR', 'CONSIGNATÁRIO',
        'TERMINAL DESCARGA', 'NOME EXPORTADOR', 'ARMADOR',
        'AGENTE INTERNACIONAL', 'NAVIO', 'PAÍS ORIGEM', 'PORTO ORIGEM',
        'UF CONSIGNATÁRIO', 'PORTO DESCARGA', 'QTDE CONTAINER'
    ] if col in detalhes.columns]
    
    detalhes_tabela = detalhes[colunas].copy()
    detalhes_tabela['ETA'] = detalhes_tabela['ETA'].dt.strftime('%d/%m/%Y')
    detalhes_tabela['QTDE CONTAINER'] = detalhes_tabela['QTDE CONTAINER'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )

    st.dataframe(detalhes_tabela, use_container_width=True, hide_index=True)

def create_dropdown(label, df_column, key):
    if df_column is None:
        return "Todos"
    options = df_column.dropna().unique().tolist()
    options = [str(opt) for opt in options]
    return st.selectbox(label, ['Todos'] + sorted(options), key=key)

def main():
   st.markdown('<h1 class="main-title">📢 Previsão de Importações de Containers</h1>', unsafe_allow_html=True)

   if st.session_state.get("reload_trigger", False):
        st.session_state.clear()  # Limpa o estado
        st.experimental_rerun()


   st.session_state["_is_running"] = True

   if "dataframe" not in st.session_state or st.session_state["dataframe"].empty:
       with st.spinner('Carregando dados...'):
           df = load_and_process_data()
           if not df.empty:
               st.session_state["dataframe"] = df
           else:
               st.stop()
   
   df = st.session_state["dataframe"]
   
   try:
       # Métricas principais
       total_containers = int(df['QTDE CONTAINER'].sum()) if 'QTDE CONTAINER' in df.columns else 0
       data_mais_antiga = df['ETA'].min().strftime('%d/%m/%Y')
       data_mais_recente = df['ETA'].max().strftime('%d/%m/%Y')
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
           data_mais_antiga_dt = df['ETA'].min().date()
           data_mais_recente_dt = df['ETA'].max().date()
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

       # Verificar colunas requeridas
       colunas_requeridas = ['UF CONSIGNATÁRIO', 'PORTO DESCARGA', 'ARMADOR']
       missing_cols = [col for col in colunas_requeridas if col not in df.columns]
       if missing_cols:
           st.error(f"Colunas ausentes: {', '.join(missing_cols)}")
           return

       # Filtros Primários
       col1, col2, col3 = st.columns(3)
       with col1:
           uf_selecionada = create_dropdown("UF Consignatário", df.get('UF CONSIGNATÁRIO'), "uf")
       with col2:
           porto_selecionado = create_dropdown("Porto de Descarga", df.get('PORTO DESCARGA'), "porto")
       with col3:
           armador_selecionado = create_dropdown("Armador", df.get('ARMADOR'), "armador")

       # Filtros Secundários
       with st.expander("Filtros Adicionais", expanded=False):
           col4, col5, col6 = st.columns(3)
           with col4:
               consig_final = create_dropdown("Consignatário Final", df.get('CONSIGNATARIO FINAL'), "consig_final")
           with col5:
               consolidador = create_dropdown("Consolidador", df.get('CONSOLIDADOR'), "consolidador")
           with col6:
               consignatario = create_dropdown("Consignatário", df.get('CONSIGNATÁRIO'), "consignatario")

           col7, col8, col9 = st.columns(3)
           with col7:
               terminal = create_dropdown("Terminal Descarga", df.get('TERMINAL DESCARGA'), "terminal")
           with col8:
               exportador = create_dropdown("Nome Exportador", df.get('NOME EXPORTADOR'), "exportador")
           with col9:
               agente = create_dropdown("Agente Internacional", df.get('AGENTE INTERNACIONAL'), "agente")

       # Aplicar filtros
       df_filtrado = df.copy()
       df_filtrado = df_filtrado[
           (df_filtrado['ETA'].dt.date >= data_inicial) &
           (df_filtrado['ETA'].dt.date <= data_final)
       ]
       
       filtros = {
           'UF CONSIGNATÁRIO': uf_selecionada,
           'PORTO DESCARGA': porto_selecionado,
           'ARMADOR': armador_selecionado,
           'CONSIGNATARIO FINAL': consig_final,
           'CONSOLIDADOR': consolidador,
           'CONSIGNATÁRIO': consignatario,
           'TERMINAL DESCARGA': terminal,
           'NOME EXPORTADOR': exportador,
           'AGENTE INTERNACIONAL': agente
       }
       
       for coluna, valor in filtros.items():
           if valor != "Todos" and coluna in df_filtrado.columns:
               df_filtrado = df_filtrado[df_filtrado[coluna] == valor]

       if df_filtrado.empty:
           st.warning("Nenhum dado encontrado para os filtros selecionados.")
           return

       # Tabela pivot
       dados_pivot = df_filtrado.groupby(['ETA', 'UF CONSIGNATÁRIO', 'PORTO DESCARGA'])['QTDE CONTAINER'].sum().reset_index()
       tabela_pivot = dados_pivot.pivot_table(
           index='ETA',
           columns=['UF CONSIGNATÁRIO', 'PORTO DESCARGA'],
           values='QTDE CONTAINER',
           aggfunc='sum'
       ).fillna(0)

       tabela_pivot = tabela_pivot.sort_index(ascending=False)
       tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)

       st.markdown('<h3 class="subheader">Previsão de Chegadas por Estado</h3>', unsafe_allow_html=True)
       tabela_formatada = tabela_pivot.copy().reset_index()
       tabela_formatada['ETA'] = tabela_formatada['ETA'].dt.strftime('%d/%m/%Y')
       st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

       # Detalhes dos containers
       display_filtered_details(df, data_inicial, data_final, filtros)

   except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        st.warning("Por favor, clique no botão abaixo para recarregar a página e tentar novamente.")
        if st.button("Recarregar página"):
            st.session_state["reload_trigger"] = True  # Adiciona um gatilho
            st.experimental_rerun()


   finally:
       st.session_state["_is_running"] = False

if __name__ == "__main__":
   main()