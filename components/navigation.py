import streamlit as st

def create_sidebar(current_page=None):
    """
    Cria a barra lateral de navegação.
    
    Args:
        current_page (str): Nome da página atual para evitar mostrar seu botão na navegação
    """
    # Configuração da navegação
    navigation = [
        {"label": "Home", "page": "Home.py", "key": "nav_home"},
        {"label": "Cabotagem", "page": "pages/cabotagem.py", "key": "nav_cab"},
        {"label": "Exportação", "page": "pages/exportacao.py", "key": "nav_exp"},
        {"label": "Importação", "page": "pages/importacao.py", "key": "nav_imp"}
    ]

    # Criar os botões da sidebar apenas para páginas diferentes da atual
    for nav in navigation:
        if current_page != nav['page']:
            if st.sidebar.button(
                nav['label'], 
                key=f"{nav['key']}_{current_page.replace('/', '_')}",
                use_container_width=True
            ):
                st.switch_page(nav['page'])
