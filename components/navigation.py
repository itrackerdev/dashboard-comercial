import streamlit as st

def create_sidebar():
    # Verificar se a sidebar já foi inicializada
    if "sidebar_initialized" not in st.session_state:
        st.session_state.sidebar_initialized = True

        # Configuração da navegação
        navigation = [
            {"icon": "🏠", "label": "Home", "page": "home", "suffix": "home"},
            {"icon": "🚢", "label": "Cabotagem", "page": "cabotagem", "suffix": "cab"},
            {"icon": "📦", "label": "Exportação", "page": "exportacao", "suffix": "exp"},
            {"icon": "📥", "label": "Importação", "page": "importacao", "suffix": "imp"}
        ]

        # Criar os botões da sidebar
        for idx, nav in enumerate(navigation):
            if st.sidebar.button(
                f"{nav['icon']} {nav['label']}",
                key=f"nav_{nav['suffix']}_{idx}",  # Garantir keys únicas
                use_container_width=True
            ):
                try:
                    st.switch_page(nav['page'])  # Passar apenas o nome da página (sem extensão .py)
                except Exception as e:
                    st.error(f"Erro ao carregar a página: {nav['page']}. Detalhes: {e}")
