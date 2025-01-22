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
    """Remove registros duplicados mantendo apenas a versão mais recente"""
    try:
        df['DATA_ATUALIZACAO'] = datetime.now()
        df['ANO/MÊS'] = df['ANO/MÊS'].astype(str)
        
        # Garantindo que todas as colunas String sejam tratadas corretamente
        str_columns = df.select_dtypes(include=['object']).columns
        for col in str_columns:
            df[col] = df[col].astype(str)
        
        # Cria ID único
        df['ID_UNICO'] = df.apply(lambda row: create_unique_id_safe(row), axis=1)
        
        if os.path.exists('dados_cabotagem_consolidados.parquet'):
            try:
                df_consolidated = pd.read_parquet('dados_cabotagem_consolidados.parquet')
                df_all = pd.concat([df_consolidated, df], ignore_index=True)
                df_all = df_all.sort_values('DATA_ATUALIZACAO').drop_duplicates(
                    subset=['ID_UNICO'], 
                    keep='last'
                )
            except Exception as e:
                print(f"Erro ao ler arquivo consolidado: {str(e)}")
                df_all = df
        else:
            df_all = df
            
        try:
            # Convertendo todas as colunas object para string antes de salvar
            for col in df_all.select_dtypes(include=['object']).columns:
                df_all[col] = df_all[col].astype(str)
            
            # Salvando sem schema explícito para evitar conversões automáticas
            df_all.to_parquet('dados_cabotagem_consolidados.parquet', 
                            engine='pyarrow',
                            index=False)
                            
            with open('log_atualizacao_cabotagem.txt', 'a') as f:
                f.write(f"{datetime.now()} - Registros processados: {len(df)}, "
                        f"Registros únicos após processamento: {len(df_all)}\n")
                        
        except Exception as e:
            print(f"Erro ao salvar arquivo consolidado: {str(e)}")
            
        return df_all
        
    except Exception as e:
        print(f"Erro em remove_duplicates: {str(e)}")
        return df

def create_unique_id_safe(row):
    """Versão segura da função create_unique_id"""
    try:
        # Converte todos os valores para string de forma segura
        data = str(row['DATA DE EMBARQUE'])
        origem = str(row['PORTO DE ORIGEM'])
        destino = str(row['PORTO DE DESTINO'])
        navio = str(row['NAVIO'])
        viagem = str(row['VIAGEM'])
        remetente = str(row['REMETENTE'])
        destinatario = str(row['DESTINATÁRIO'])
        
        unique_string = f"{data}_{origem}_{destino}_{navio}_{viagem}_{remetente}_{destinatario}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    except Exception as e:
        print(f"Erro ao criar ID único: {str(e)}")
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()  # Fallback

def load_and_process_data():
    try:
        # ID do arquivo no Google Drive
        file_id = st.secrets["urls"]["planilha_cabotagem"]
        
        # Baixando o arquivo
        excel_content = download_file_from_drive(file_id)
        if excel_content is None:
            st.error("Não foi possível baixar o arquivo do Google Drive")
            return pd.DataFrame()

        # Lendo o arquivo Excel como string
        df = pd.read_excel(
            excel_content,
            dtype=str
        )
        
        # Função para converter números com segurança
        def convert_number(x):
            try:
                if pd.isna(x):
                    return 0.0
                if isinstance(x, str):
                    return float(x.replace(',', '.').strip())
                return float(x)
            except:
                return 0.0

        # Convertendo colunas numéricas
        numeric_columns = ['QUANTIDADE C20', 'QUANTIDADE C40', 'QUANTIDADE TEUS', 
                         'QTDE FCL', 'PESO BRUTO', 'VOLUME (M³)']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_number)
        
        # Convertendo datas com dayfirst=True
        date_format = '%d/%m/%Y'
        df['DATA CONSULTA'] = pd.to_datetime(df['DATA CONSULTA'], 
                                           format=date_format, 
                                           dayfirst=True, 
                                           errors='coerce')
        df['DATA DE EMBARQUE'] = pd.to_datetime(df['DATA DE EMBARQUE'], 
                                              format=date_format, 
                                              dayfirst=True, 
                                              errors='coerce')
        
        # Garantindo que ANO/MÊS é string
        df['ANO/MÊS'] = df['ANO/MÊS'].astype(str)
        
        # Limpando colunas de texto
        text_columns = [
            'PORTO DE ORIGEM', 'PORTO DE DESTINO', 'TERMINAL DE EMBARQUE', 
            'TERMINAL DE DESCARGA', 'REMETENTE', 'DESTINATÁRIO', 'ARMADOR', 
            'NAVIO', 'TIPO DE CARGA', 'TIPO DE CONTEINER', 'DESCRIÇÃO DA MERCADORIA'
        ]
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip().str.upper()
        
        # Extraindo estado dos portos
        def extrair_estado(porto):
            try:
                if isinstance(porto, str) and len(porto) >= 2:
                    return porto[:2]
                return None
            except:
                return None
        
        df['ESTADO_ORIGEM'] = df['COD. PORTO ORIGEM'].apply(extrair_estado)
        df['ESTADO_DESTINO'] = df['COD. PORTO DESTINO'].apply(extrair_estado)
        
        # Remove duplicatas
        df = remove_duplicates(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        st.write("Tipo do erro:", type(e))
        st.write("Detalhes do erro:", str(e))
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
        return pd.to_datetime(date).strftime('%d/%m/%Y')
    except:
        return '-'

def get_formatted_dates(df):
    """Retorna lista de datas formatadas de forma segura"""
    try:
        # Filtra datas válidas e formata
        valid_dates = df['DATA DE EMBARQUE'].dropna()
        return sorted(valid_dates.dt.strftime('%d/%m/%Y').unique())
    except:
        return []

def create_state_summary_table(df, view_type='destinatario'):
    """Cria uma tabela resumo por data e estado"""
    try:
        # Fazer uma cópia explícita do DataFrame
        df_work = df.copy()
        
        # Garantir que todas as datas são datetime
        df_work.loc[:, 'DATA DE EMBARQUE'] = pd.to_datetime(df_work['DATA DE EMBARQUE'], errors='coerce')
        df_work = df_work.dropna(subset=['DATA DE EMBARQUE'])
        
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
        # Fazer uma cópia explícita do DataFrame
        df_work = df.copy()
        
        # Convertendo a data de comparação para datetime
        data_filtro = pd.to_datetime(data, format='%d/%m/%Y')
        
        # Padronizar estados
        df_work.loc[:, 'ESTADO_ORIGEM'] = df_work['REMETENTE - CIDADE'].apply(
            lambda x: x.split('-')[-1].strip() if isinstance(x, str) else None
        )
        df_work.loc[:, 'ESTADO_DESTINO'] = df_work['DESTINATÁRIO - ESTADO']
        
        # Filtrando dados
        mask = (
            (df_work['DATA DE EMBARQUE'].dt.date == data_filtro.date()) & 
            ((df_work['ESTADO_ORIGEM'] == uf) | (df_work['ESTADO_DESTINO'] == uf))
        )
        return df_work[mask].copy()
        
    except Exception as e:
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