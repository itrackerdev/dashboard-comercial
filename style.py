import streamlit as st

def apply_styles():
    styles = """
    <style>
    /* Estilos gerais */
    .stApp {
        background-color: #ffffff;
    }

    /* Barra lateral personalizada */
    .stSidebar {
        background-color: #f8f9fa;
        padding-top: 2rem;
    }

    div[data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Botões estilizados na barra lateral */
    .sidebar-button {
        color: #0365B0;
        text-decoration: none;
        font-size: 1rem;
        font-weight: bold;
        padding: 1rem;
        display: block;
        transition: all 0.3s ease;
        text-align: center;
        background: white;
        border-radius: 10px;
        margin: 0.5rem 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .sidebar-button:hover {
        background-color: #0365B0;
        color: white;
        box-shadow: 0 4px 10px rgba(3, 101, 176, 0.2);
    }

    /* Título principal */
    h1 {
        background: none;
        color: black !important;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 2rem auto;
        padding: 1.5rem;
        border-bottom: 4px solid #F37529;
        max-width: 90%;
        border-radius: 15px 15px 0 0;
    }

    /* Subtítulos e cabeçalhos de seção */
    h2, h3, .subheader {
        background: linear-gradient(90deg, #0365B0 0%, #034C8C 100%);
        color: white !important;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(3, 101, 176, 0.1);
        text-align: center !important;
    }

    /* Indicadores */
    .indicador {
        background: linear-gradient(135deg, #0365B0 0%, #034C8C 100%);
        border-radius: 25px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(3, 101, 176, 0.15);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1rem;
    }

    .indicador h3 {
        color: white;
        margin: 0 0 1rem 0;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .indicador p {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Estilo para métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0365B0 0%, #034C8C 100%);
        border-radius: 16px;
        padding: 1.5rem !important;
        box-shadow: 0 10px 15px -3px rgba(3, 101, 176, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(4px);
        transition: all 0.3s ease;
        margin: 0.5rem 0;
        text-align: center !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 20px -3px rgba(3, 101, 176, 0.15);
    }

    div[data-testid="stMetric"] > div {
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 700;
        text-align: center !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    div[data-testid="stMetric"] label {
        color: white !important;
        font-weight: 600;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: center !important;
    }

    /* DataFrames */
    div[data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px !important;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        margin: 1rem 0;
        width: 100% !important;
    }

    div[data-testid="stDataFrame"] table {
        width: 100% !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stDataFrame"] th {
        background: linear-gradient(90deg, #0365B0 0%, #034C8C 100%);
        color: white !important;
        padding: 1rem 0.75rem !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: center !important;
        border-bottom: 3px solid #F37529;
        white-space: nowrap;
        font-size: 0.95rem !important;
    }

    div[data-testid="stDataFrame"] td {
        padding: 0.875rem 0.75rem !important;
        text-align: center !important;
        border-bottom: 1px solid rgba(3, 101, 176, 0.1);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        background-color: white !important;
        transition: all 0.2s ease;
    }

    div[data-testid="stDataFrame"] tr:hover td {
        background-color: rgba(243, 117, 41, 0.08) !important;
    }

    /* Containers e margins */
    .main-container {
        padding: 1rem 2rem;
        max-width: none !important;
    }

    .titulo-dashboard-container {
        width: calc(100% - 2rem);
        margin: 2rem auto;
        padding: 25px 20px;
        background: linear-gradient(to right, #F37529, #f8a676);
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(243, 117, 41, 0.2);
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .titulo-dashboard-container::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
    }

    .titulo-dashboard {
        font-size: 50px;
        font-weight: bold;
        color: black;
        text-transform: uppercase;
        margin: 0;
        text-shadow: none;
    }

    .subtitulo-dashboard {
        font-size: 18px;
        color: #555555;
        margin: 10px 0 0 0;
        font-weight: 500;
    }

    .funcionalidade {
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: white;
        border-radius: 12px;
        border-left: 4px solid #F37529;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    .funcionalidade:hover {
        transform: translateX(10px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }

    .funcionalidade strong {
        color: #0365B0;
        margin-right: 8px;
    }

    .funcionalidade .icon {
        margin-right: 8px;
        font-size: 1.2rem;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
            padding: 1rem;
        }

        div[data-testid="stMetric"] {
            padding: 1rem !important;
        }

        div[data-testid="stMetric"] > div {
            font-size: 1.8rem !important;
        }

        .main-container {
            padding: 0.5rem;
        }

        div[data-testid="stDataFrame"] th,
        div[data-testid="stDataFrame"] td {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }

        .titulo-dashboard-container {
            padding: 15px 10px;
        }

        .titulo-dashboard {
            font-size: 35px;
        }

        .funcionalidade {
            margin: 0.75rem 0;
            padding: 0.75rem 1rem;
        }
    }
    </style>
    """
    st.markdown(styles, unsafe_allow_html=True)

if __name__ == "__main__":
    apply_styles()