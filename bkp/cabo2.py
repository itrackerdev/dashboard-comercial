import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os
import requests
from io import BytesIO

st.set_page_config(
    page_title="Previsão de Cabotagem",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚢",
    menu_items=None
)

st.markdown("""
    <style>
    /* Estilos gerais */
    .stApp {
        background-color: #ffffff;
    }

    /* Título principal */
    h1 {
        background: linear-gradient(120deg, #0365B0 0%, #034C8C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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

    /* Cards de métricas */
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

    /* Inputs e Seletores */
    div[data-testid="stSelectbox"], div[data-testid="stNumberInput"] {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(3, 101, 176, 0.2);
        padding: 0.5rem;
    }

    div[data-testid="stSelectbox"]:hover, div[data-testid="stNumberInput"]:hover {
        border-color: #F37529;
        box-shadow: 0 4px 6px rgba(3, 101, 176, 0.1);
    }

    /* Radio buttons */
    div[data-testid="stRadio"] > div {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    /* Containers e margins */
    .main-container {
        padding: 1rem 2rem;
        max-width: none !important;
    }

    .stAlert {
        background-color: rgba(243, 117, 41, 0.05);
        border-left: 4px solid #F37529;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
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
        st.error(f"Erro ao baixar arquivo do Google Drive: {str(e)}")
        return None

def remove_duplicates(df):
    """Remove registros duplicados mantendo apenas a versão mais recente."""
    try:
        # Adicionar ou atualizar coluna de DATA_ATUALIZACAO
        df['DATA_ATUALIZACAO'] = datetime.now()
        
        # Verificar se todas as colunas necessárias para o ID único existem
        required_columns = [
            'DATA DE EMBARQUE', 'PORTO DE ORIGEM', 'PORTO DE DESTINO',
            'NAVIO', 'VIAGEM', 'REMETENTE', 'DESTINATÁRIO'
        ]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Coluna obrigatória ausente: {col}")
        
        # Criar ID único
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)
        
        # Validar que a coluna foi gerada corretamente
        if df['ID_UNICO'].isnull().any():
            raise ValueError("Falha ao criar a coluna ID_UNICO. Verifique os dados de entrada.")
        
        # Carregar registros consolidados se existirem
        if os.path.exists('dados_cabotagem_consolidados.parquet'):
            df_consolidated = pd.read_parquet('dados_cabotagem_consolidados.parquet')
            df_all = pd.concat([df_consolidated, df], ignore_index=True)
        else:
            df_all = df
        
        # Remover duplicados com base no ID_UNICO
        df_all = df_all.sort_values('DATA DE EMBARQUE', ascending=False).drop_duplicates(
            subset=['ID_UNICO'], keep='first'
        )
        
        # Salvar DataFrame consolidado
        df_all.to_parquet('dados_cabotagem_consolidados.parquet', engine='pyarrow', index=False)
        
        return df_all
    
    except Exception as e:
        st.error(f"Erro em remove_duplicates: {e}")
        return pd.DataFrame()

def create_unique_id_safe(row):
    """Gera um ID único para cada registro com base em colunas específicas."""
    try:
        data = str(row.get('DATA DE EMBARQUE', ''))
        origem = str(row.get('PORTO DE ORIGEM', ''))
        destino = str(row.get('PORTO DE DESTINO', ''))
        navio = str(row.get('NAVIO', ''))
        viagem = str(row.get('VIAGEM', ''))
        remetente = str(row.get('REMETENTE', ''))
        destinatario = str(row.get('DESTINATÁRIO', ''))

        unique_string = f"{data}_{origem}_{destino}_{navio}_{viagem}_{remetente}_{destinatario}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    except Exception as e:
        print(f"Erro ao criar ID único: {e}")
        return None


def load_and_process_data():
    try:
        # Link do Google Sheets
        url = "https://docs.google.com/spreadsheets/d/1kvjmYigg06aEOrgFG4gRFwzCIjTrns2P/export?format=xlsx"

        # Baixando o arquivo diretamente do Google Sheets
        response = requests.get(url)
        response.raise_for_status()
        excel_content = BytesIO(response.content)

        # Lendo o arquivo Excel
        df = pd.read_excel(
            excel_content,
            dtype=str  # Forçar leitura como string para evitar problemas de tipo
        )

        # Exibir as primeiras linhas do DataFrame
        st.write("Primeiras linhas do DataFrame carregado:")
        st.dataframe(df.head())

        # Convertendo a coluna de DATA DE EMBARQUE para datetime
        df['DATA DE EMBARQUE'] = pd.to_datetime(
            df['DATA DE EMBARQUE'],
            format='%Y-%m-%d',  # Formato esperado
            errors='coerce'  # Define NaT para valores inválidos
        )

        # Validar que todas as colunas necessárias existem
        required_columns = [
            'DATA DE EMBARQUE', 'PORTO DE ORIGEM', 'PORTO DE DESTINO',
            'NAVIO', 'VIAGEM', 'REMETENTE', 'DESTINATÁRIO'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"As seguintes colunas estão ausentes na planilha: {missing_columns}")

        # Criar coluna ID_UNICO
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)

        # Validar se ID_UNICO foi criado corretamente
        if 'ID_UNICO' not in df.columns or df['ID_UNICO'].isna().any():
            raise ValueError("Falha ao criar a coluna ID_UNICO. Verifique os dados de entrada.")

        # Exibir as primeiras linhas após a criação do ID_UNICO
        st.write("Primeiras linhas do DataFrame após criação de ID_UNICO:")
        st.dataframe(df[['DATA DE EMBARQUE', 'PORTO DE ORIGEM', 'PORTO DE DESTINO', 'ID_UNICO']].head())

        # Verificar registros com datas inválidas
        invalid_dates = df[df['DATA DE EMBARQUE'].isna()]
        st.write("Registros com DATA DE EMBARQUE inválida (se existirem):")
        st.dataframe(invalid_dates)

        # Contar valores únicos na coluna DATA DE EMBARQUE
        st.write("Quantidade de registros por DATA DE EMBARQUE:")
        st.write(df['DATA DE EMBARQUE'].value_counts())

        return df

    except Exception as e:
        st.error(f"Erro ao carregar ou processar os dados: {e}")
        return pd.DataFrame()


def get_estado_info(df, data, uf):
    """Retorna informações detalhadas para uma data e UF específicas"""
    # Convertendo a data de comparação para datetime
    data_filtro = pd.to_datetime(data, format='%d/%m/%Y')
    
    return df[
        (df['DATA DE EMBARQUE'].dt.date == data_filtro.date()) & 
        ((df['ESTADO_ORIGEM'] == uf) | (df['ESTADO_DESTINO'] == uf))
    ]

def format_estado_table(df_filtered):
    """Formata a tabela de detalhes com as informações relevantes para visão por estado"""
    if df_filtered.empty:
        st.warning("Não há dados para os filtros selecionados.")
        return
    
    COLUNAS_OBRIGATORIAS = [
        'DATA DE EMBARQUE',
        'DESTINATÁRIO',
        'DESTINATÁRIO - CIDADE',
        'DESTINATÁRIO - ESTADO',
        'PORTO DE DESCARGA',
        'PORTO DE DESTINO',
        'PORTO DE EMBARQUE',
        'PORTO DE ORIGEM',
        'QUANTIDADE C20',
        'QUANTIDADE C40',
        'REMETENTE',
        'REMETENTE - CIDADE',
        'TERMINAL DE DESCARGA',
        'TERMINAL DE EMBARQUE',
        'VOLUME (M³)'
    ]
    
    # Obtém todas as colunas disponíveis exceto as obrigatórias
    colunas_opcionais = [col for col in df_filtered.columns if col not in COLUNAS_OBRIGATORIAS]
    
    # Multiselect para escolher colunas adicionais
    colunas_selecionadas = st.multiselect(
        "Selecione colunas adicionais para visualizar:",
        options=colunas_opcionais,
        default=[]
    )
    
    # Combina as colunas obrigatórias com as selecionadas
    colunas_para_exibir = COLUNAS_OBRIGATORIAS + colunas_selecionadas
    
    # Filtra apenas as colunas que existem no DataFrame
    colunas_existentes = [col for col in colunas_para_exibir if col in df_filtered.columns]
    
    # Exibe a tabela com as colunas selecionadas
    st.dataframe(
        df_filtered[colunas_existentes],
        use_container_width=True,
        hide_index=True
    )

def format_date_safe(date):
    """Formata data com tratamento seguro para valores nulos"""
    try:
        if pd.isna(date):
            return '-'
        return pd.to_datetime(date, dayfirst=True).strftime('%d/%m/%Y')
    except:
        return '-'


def get_formatted_dates(df):
    try:
        valid_dates = df['DATA DE EMBARQUE'].dropna()
        return sorted(valid_dates.dt.strftime('%d/%m/%Y').unique(), reverse=True)
    except:
        return []

def create_state_summary_table(df, view_type='destinatario'):
    """Cria uma tabela resumo por data e estado ou cidade, mostrando registros mais atuais."""
    try:
        # Fazer uma cópia explícita do DataFrame
        df_work = df.copy()

        # Garantir que todas as datas são datetime
        df_work.loc[:, 'DATA DE EMBARQUE'] = pd.to_datetime(df_work['DATA DE EMBARQUE'], errors='coerce')
        df_work = df_work.dropna(subset=['DATA DE EMBARQUE'])

        # Remover duplicatas e manter apenas os registros mais recentes
        df_work = df_work.sort_values('DATA DE EMBARQUE', ascending=False).drop_duplicates(subset=['ID_UNICO'], keep='first')

        # Garantir que QUANTIDADE TEUS seja numérico
        df_work.loc[:, 'QUANTIDADE TEUS'] = pd.to_numeric(
            df_work['QUANTIDADE TEUS'].fillna(0).astype(str).str.replace(',', '.'), 
            errors='coerce'
        ).fillna(0)

        # Definir campo de estado baseado no tipo de visualização
        if view_type == 'destinatario':
            estados = sorted([
                e for e in df_work['DESTINATÁRIO - ESTADO'].unique()
                if e is not None and str(e).strip()
            ])

            # Agrupar por data e estado de destino
            table_data = []
            for date in sorted(df_work['DATA DE EMBARQUE'].unique(), reverse=True):
                if pd.isna(date):
                    continue

                row_data = {'DATA EMBARQUE': format_date_safe(date)}

                for estado in estados:
                    mask = (
                        (df_work['DATA DE EMBARQUE'].dt.date == pd.to_datetime(date).date()) & 
                        (df_work['DESTINATÁRIO - ESTADO'] == estado)
                    )
                    total_containers = int(df_work.loc[mask, 'QUANTIDADE TEUS'].sum())
                    row_data[estado] = str(total_containers) if total_containers > 0 else '-'

                total_row = sum(
                    int(v) for v in row_data.values() 
                    if isinstance(v, str) and v.isdigit()
                )
                row_data['TOTAL'] = str(total_row) if total_row > 0 else '-'

                table_data.append(row_data)
        else:
            # Extrair cidade do remetente
            df_work['CIDADE_REMETENTE'] = df_work['REMETENTE - CIDADE'].apply(
                lambda x: str(x).strip() if pd.notnull(x) else ''
            )

            cidades = sorted([
                c for c in df_work['CIDADE_REMETENTE'].unique()
                if c and str(c).strip()
            ])

            # Agrupar por data e cidade de origem
            table_data = []
            for date in sorted(df_work['DATA DE EMBARQUE'].unique()):
                if pd.isna(date):
                    continue

                row_data = {'DATA EMBARQUE': format_date_safe(date)}

                for cidade in cidades:
                    mask = (
                        (df_work['DATA DE EMBARQUE'].dt.date == pd.to_datetime(date).date()) & 
                        (df_work['CIDADE_REMETENTE'] == cidade)
                    )
                    total_containers = int(df_work.loc[mask, 'QUANTIDADE TEUS'].sum())
                    row_data[cidade] = str(total_containers) if total_containers > 0 else '-'

                total_row = sum(
                    int(v) for v in row_data.values() 
                    if isinstance(v, str) and v.isdigit()
                )
                row_data['TOTAL'] = str(total_row) if total_row > 0 else '-'

                table_data.append(row_data)

        # Criar DataFrame final
        if not table_data:
            return pd.DataFrame()

        summary_df = pd.DataFrame(table_data)

        # Ordenar colunas
        if view_type == 'destinatario':
            cols = ['DATA EMBARQUE'] + sorted(estados) + ['TOTAL']
        else:
            cols = ['DATA EMBARQUE'] + sorted(cidades) + ['TOTAL']

        summary_df = summary_df[cols]

        return summary_df

    except Exception as e:
        st.error(f"Erro ao criar tabela resumo: {str(e)}")
        st.exception(e)
        return pd.DataFrame()

def get_estado_info(df, data, uf):
    """Retorna informações detalhadas para uma data e UF específicas"""
    try:
        # Fazer uma cópia explícita do DataFrame para evitar alterações no original
        df_work = df.copy()
        
        # Convertendo a data de comparação para datetime com dayfirst=True
        data_filtro = pd.to_datetime(data, format='%d/%m/%Y', dayfirst=True)
        
        # Padronizar estados
        df_work['ESTADO_ORIGEM'] = df_work['REMETENTE - CIDADE'].apply(
            lambda x: x.split('-')[-1].strip() if isinstance(x, str) else None
        )
        df_work['ESTADO_DESTINO'] = df_work['DESTINATÁRIO - ESTADO']
        
        # Filtrando os dados com base na data e no estado fornecido
        mask = (
            (df_work['DATA DE EMBARQUE'].dt.date == data_filtro.date()) & 
            ((df_work['ESTADO_ORIGEM'] == uf) | (df_work['ESTADO_DESTINO'] == uf))
        )
        
        # Retornar os registros que atendem ao filtro
        return df_work[mask].copy()
        
    except Exception as e:
        # Exibir uma mensagem de erro em caso de problemas durante o processamento
        st.error(f"Erro ao filtrar dados: {str(e)}")
        return pd.DataFrame()


def main():
   st.markdown('<div class="main-container">', unsafe_allow_html=True)
   
   st.markdown('<h1 class="main-title">🚢 Análise de Operações de Cabotagem</h1>', unsafe_allow_html=True)
   
   df = load_and_process_data()
   
   if df.empty:
       st.error("Não foi possível carregar os dados.")
       return

   try:
       col1, col2 = st.columns(2)
       with col1:
           st.metric(
               "TOTAL DE REGISTROS", 
               f"{len(df):,}",
               help="Total de registros únicos"
           )
       with col2:
           ultima_atualizacao = df['DATA CONSULTA'].max()
           st.metric(
               "ÚLTIMA ATUALIZAÇÃO",
               format_date_safe(ultima_atualizacao),
               help="Data da última atualização dos dados"
           )

       st.markdown('<hr>', unsafe_allow_html=True)

       st.markdown('<h3 class="subheader">Resumo de Operações</h3>', unsafe_allow_html=True)
       summary_df = create_state_summary_table(df, 'destinatario')
       
       if not summary_df.empty:
           st.dataframe(
               data=summary_df,
               use_container_width=True,
               hide_index=True
           )

       st.markdown('<hr>', unsafe_allow_html=True)
           
       col1, col2 = st.columns(2)
       with col1:
           datas_disponiveis = get_formatted_dates(df)
           if not datas_disponiveis:
               st.error("Não há datas disponíveis para seleção")
               return
           data_selecionada = st.selectbox("Selecione a Data", datas_disponiveis, key='data_estado')
       
       with col2:    
           view_type = st.radio(
               "Tipo de Visualização",
               ['Estado Destinatário', 'Cidade Remetente'],
               index=0
           )

       locais = sorted([
           e for e in df['DESTINATÁRIO - ESTADO'].unique()
           if e is not None and str(e).strip()
       ]) if view_type == 'Estado Destinatário' else sorted([
           e for e in df['ESTADO_ORIGEM'].unique()
           if e is not None and str(e).strip()
       ])
       
       local_selecionado = st.selectbox(
           "Selecione o Estado" if view_type == 'Estado Destinatário' else "Selecione a Cidade", 
           locais, 
           key='local_select'
       )
       
       if data_selecionada and local_selecionado:
           st.markdown('<hr>', unsafe_allow_html=True)
           
           mask = (
               (df['DATA DE EMBARQUE'].dt.strftime('%d/%m/%Y') == data_selecionada) & 
               (df['DESTINATÁRIO - ESTADO' if view_type == 'Estado Destinatário' else 'REMETENTE - CIDADE'] == local_selecionado)
           )
           
           df_filtered = df[mask].copy()
           
           col1, col2, col3 = st.columns(3)
           with col1:
               st.metric("Total de Contêineres", int(df_filtered['QUANTIDADE TEUS'].sum()))
           with col2:
               st.metric("Número de Empresas", len(df_filtered['ARMADOR'].unique()))
           with col3:
               st.metric("Total de Navios", len(df_filtered['NAVIO'].unique()))
           
           st.markdown(
               f'<h3 class="subheader">Detalhes para {view_type}: {local_selecionado} - {data_selecionada}</h3>', 
               unsafe_allow_html=True
           )
           format_estado_table(df_filtered)
       
   except Exception as e:
       st.error(f"Erro ao processar dados: {str(e)}")
       st.exception(e)

   st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
   main()