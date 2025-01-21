import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📦",
    menu_items=None
)

# Estilização global
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin: 0.5rem 0;
    }
    .dataframe {
        font-size: 0.9rem !important;
    }
    .st-emotion-cache-16txtl3 h4 {
        padding-top: 0;
    }
    </style>
""", unsafe_allow_html=True)

def download_file_from_drive(file_id):
    """Download arquivo do Google Drive"""
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"❌ Erro ao baixar arquivo do Google Drive: {str(e)}")
        return None

def load_and_process_data():
    try:
        file_id = st.secrets["urls"]["planilha_importacao"]
        excel_content = download_file_from_drive(file_id)
        
        if excel_content is None:
            return pd.DataFrame()
        
        df = pd.read_excel(excel_content)
        df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
        df['QTDE CONTAINER'] = df['QTDE CONTAINER'].str.replace(',', '.').astype(float)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()

def create_pagination_controls(total_pages, current_page, on_change):
    """Cria controles de paginação personalizados"""
    cols = st.columns([1, 2, 3, 2, 1])
    
    with cols[0]:
        if st.button("⏮️", disabled=current_page == 1):
            on_change(1)
    
    with cols[1]:
        if st.button("◀️ Anterior", disabled=current_page == 1):
            on_change(current_page - 1)
    
    with cols[2]:
        st.markdown(f"<div style='text-align: center;'>Página {current_page} de {total_pages}</div>", unsafe_allow_html=True)
    
    with cols[3]:
        if st.button("Próxima ▶️", disabled=current_page == total_pages):
            on_change(current_page + 1)
    
    with cols[4]:
        if st.button("⏭️", disabled=current_page == total_pages):
            on_change(total_pages)

def create_metric_card(title, value, delta=None, help_text=None):
    """Cria card personalizado para métricas"""
    help_div = f"<div style='font-size: 0.8rem; color: #6c757d;'>{help_text}</div>" if help_text else ""
    delta_div = (
        f"<div style='color: {'#28a745' if float(str(delta).rstrip('%')) > 0 else '#dc3545'};'>{delta}</div>"
        if delta else ""
    )
    
    card_html = f"""
        <div class="metric-card">
            <h4 style="color: #6c757d; margin: 0;">{title}</h4>
            <div style="font-size: 2rem; font-weight: bold; color: #212529; margin: 0.5rem 0;">
                {value}
            </div>
            {delta_div}
            {help_div}
        </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def style_dataframe(df):
    """
    Aplica estilos personalizados ao DataFrame e
    esconde o índice via CSS (para versões de pandas < 1.4).
    """
    return (
        df.style
        .set_table_styles([
            # Esconde o índice (row_heading) e células em branco (blank)
            {
                'selector': 'th.row_heading, th.blank',
                'props': [('display', 'none')]
            },
            # Estilização do cabeçalho das colunas
            {
                'selector': 'th',
                'props': [
                    ('background-color', '#e9ecef'),
                    ('color', '#495057'),
                    ('font-weight', 'bold'),
                    ('padding', '0.5rem'),
                    ('text-align', 'center')
                ]
            }
        ])
        .set_properties(**{
            'background-color': '#f8f9fa',
            'color': '#212529',
            'border': '1px solid #dee2e6',
            'padding': '0.5rem'
        })
    )

def get_detailed_info(df, data, uf):
    """Retorna informações detalhadas para uma data e UF específicas"""
    if isinstance(data, str):
        data = pd.to_datetime(data)
    
    df_date = df['ETA'].dt.normalize()
    compare_date = pd.to_datetime(data).normalize()
    
    mask = (df_date == compare_date) & (df['UF CONSIGNATÁRIO'] == uf)
    return df[mask]

def format_detailed_table(df_filtered):
    """Formata a tabela de detalhes com as informações relevantes"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    colunas_exibir = {
        'TERMINAL DESCARGA': 'Terminal',
        'CONSIGNATÁRIO': 'Empresa',
        'EMAIL': 'Email',
        'TELEFONE': 'Telefone',
        'NAVIO': 'Navio',
        'ARMADOR': 'Armador',
        'AGENTE DE CARGA': 'Agente de Carga',
        'CONSOLIDADOR': 'Consolidador',
        'QTDE CONTAINER': 'Containers',
        'TIPO CONTAINER': 'Tipo',
        'MERCADORIA': 'Mercadoria'
    }
    
    df_detalhes = df_filtered[colunas_exibir.keys()].copy()
    df_detalhes.columns = colunas_exibir.values()
    df_detalhes['Containers'] = df_detalhes['Containers'].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
    
    return df_detalhes

def format_story_table(df, data, uf):
    """Cria tabela para trajetória dos containers"""
    filtered_df = df[
        (df['ETA'].dt.strftime('%d/%m/%Y') == data.strftime('%d/%m/%Y')) &
        (df['UF CONSIGNATÁRIO'] == uf)
    ]
    
    story_df = filtered_df[[
        'PAÍS ORIGEM', 'ETS', 'PORTO DESCARGA', 'ETA',
        'UF CONSIGNATÁRIO', 'QTDE CONTAINER'
    ]].copy()
    
    story_df.columns = [
        'País de Origem', 'Data de Saída (ETS)',
        'Porto de Descarga', 'Data de Chegada (ETA)',
        'Estado Destino', 'Quantidade de Containers'
    ]
    
    # Converte datas para string no formato dd/mm/yyyy
    story_df['Data de Saída (ETS)'] = pd.to_datetime(
        story_df['Data de Saída (ETS)'],
        errors='coerce',
        dayfirst=True
    ).dt.strftime('%d/%m/%Y')
    
    story_df['Data de Chegada (ETA)'] = pd.to_datetime(
        story_df['Data de Chegada (ETA)'],
        errors='coerce',
        dayfirst=True
    ).dt.strftime('%d/%m/%Y')
    
    # Formata a quantidade de containers, removendo decimais e adicionando separador de milhar
    story_df['Quantidade de Containers'] = story_df['Quantidade de Containers'].apply(
        lambda x: f"{int(x):,}" if x > 0 else "-"
    )
    
    # Remove linhas com colunas essenciais vazias
    story_df = story_df.dropna(subset=['País de Origem', 'Porto de Descarga', 'Estado Destino'])
    
    # Ordena pela data de chegada
    story_df = story_df.sort_values(by='Data de Chegada (ETA)').reset_index(drop=True)
    
    return story_df

def main():
    # Título principal centralizado e em negrito
    st.markdown("<h1 style='text-align: center; font-weight: bold;'>📦 Previsão de Chegadas de Containers</h1>", unsafe_allow_html=True)
    
    try:
        df = load_and_process_data()
        if df.empty:
            st.warning("⚠️ Não foi possível carregar os dados")
            return
        
        # Criando tabela pivot inicial
        dados_pivot = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
        tabela_pivot = dados_pivot.pivot(
            index='ETA',
            columns='UF CONSIGNATÁRIO',
            values='QTDE CONTAINER'
        ).fillna(0)
        
        # Adicionando total por dia
        tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)
        
        # Formatando a tabela principal
        tabela_formatada = tabela_pivot.copy()
        for coluna in tabela_formatada.columns:
            tabela_formatada[coluna] = tabela_formatada[coluna].apply(
                lambda x: f"{int(x):,}" if x > 0 else "-"
            )
        
        tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')

        # Título centralizado e em negrito
        st.markdown("<h3 style='text-align: center; font-weight: bold;'>📊 Previsão de Chegadas por Estado</h3>", unsafe_allow_html=True)
        st.markdown("""
            <div style='font-size: 0.9rem; color: #6c757d; margin-bottom: 1rem; text-align: center;'>
                Clique em qualquer número para ver os detalhes
            </div>
        """, unsafe_allow_html=True)
        
        # Exibição da tabela principal usando a função de estilo
        st.dataframe(
            style_dataframe(tabela_formatada),
            use_container_width=True,
            height=400
        )

        # Seletores
        col1, col2 = st.columns(2)
        with col1:
            data_selecionada = st.date_input(
                "📅 Data",
                value=pd.to_datetime(tabela_formatada.index[0], format='%d/%m/%Y'),
                min_value=pd.to_datetime(tabela_formatada.index[0], format='%d/%m/%Y'),
                max_value=pd.to_datetime(tabela_formatada.index[-1], format='%d/%m/%Y')
            )
        with col2:
            uf_selecionada = st.selectbox(
                "🗺️ Estado",
                options=[col for col in tabela_pivot.columns if col != 'TOTAL']
            )

        if data_selecionada and uf_selecionada:
            detalhes = get_detailed_info(df, data_selecionada, uf_selecionada)
            
            if not detalhes.empty:
                # Título centralizado e em negrito
                st.markdown(f"<h3 style='text-align: center; font-weight: bold;'>📈 Detalhes para {uf_selecionada} - {data_selecionada.strftime('%d/%m/%Y')}</h3>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label="Total de Containers",
                        value=f"{int(detalhes['QTDE CONTAINER'].sum()):,}"
                    )
                with col2:
                    st.metric(
                        label="Empresas",
                        value=len(detalhes['CONSIGNATÁRIO'].unique())
                    )
                with col3:
                    st.metric(
                        label="Terminais",
                        value=len(detalhes['TERMINAL DESCARGA'].unique())
                    )

                # Título centralizado e em negrito
                st.markdown("<h3 style='text-align: center; font-weight: bold;'>🚢 Trajetória dos Containers</h3>", unsafe_allow_html=True)
                story_table = format_story_table(df, data_selecionada, uf_selecionada)
                
                if not story_table.empty:
                    rows_per_page = 10
                    total_rows = len(story_table)
                    total_pages = (total_rows + rows_per_page - 1) // rows_per_page
                    
                    if 'current_page' not in st.session_state:
                        st.session_state.current_page = 1
                    
                    create_pagination_controls(
                        total_pages,
                        st.session_state.current_page,
                        lambda x: setattr(st.session_state, 'current_page', x)
                    )
                    
                    start_idx = (st.session_state.current_page - 1) * rows_per_page
                    end_idx = start_idx + rows_per_page

                    # 🔴 Reset do índice para esconder coluna de índice na exibição
                    story_page = story_table.iloc[start_idx:end_idx].reset_index(drop=True)
                    
                    st.dataframe(
                        style_dataframe(story_page),
                        use_container_width=True,
                        height=400
                    )
                
                # Título centralizado e em negrito
                st.markdown("<h3 style='text-align: center; font-weight: bold;'>📋 Detalhes dos Containers</h3>", unsafe_allow_html=True)
                tabela_detalhes = format_detailed_table(detalhes)
                st.dataframe(
                    style_dataframe(tabela_detalhes),
                    use_container_width=True,
                    height=400
                )
                
                # Informações adicionais
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("📊 Distribuição por Terminal"):
                        dist_terminal = detalhes.groupby('TERMINAL DESCARGA')['QTDE CONTAINER'].sum()
                        dist_terminal_df = dist_terminal.to_frame('Quantidade')
                        st.dataframe(style_dataframe(dist_terminal_df), use_container_width=True)
                
                with col2:
                    with st.expander("🚢 Informações dos Navios"):
                        info_navios = detalhes[['NAVIO', 'ARMADOR']].drop_duplicates()
                        st.dataframe(style_dataframe(info_navios), use_container_width=True)
            else:
                st.info("ℹ️ Não há dados para a seleção especificada")
        
    except Exception as e:
        st.error("❌ Ocorreu um erro ao processar os dados")
        st.exception(e)

if __name__ == "__main__":
    main()