import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Oportunidades Comerciais",
    page_icon="🚢",
    layout="wide"
)

def create_unique_id(row):
    """Cria um ID único para cada registro baseado em campos chave"""
    # Combinando campos relevantes para criar uma chave única
    unique_string = f"{row['EMBARQUE']}_{row['CONSIGNATÁRIO']}_{row['ETA']}_{row['PORTO DESTINO']}_{row['CONTAINER PARCIAL']}_{row['VIAGEM']}"
    # Criando um hash do string para ter um ID único
    return hashlib.md5(unique_string.encode()).hexdigest()

def remove_duplicates(df):
    """Remove registros duplicados mantendo apenas a versão mais recente"""
    # Criando ID único para cada registro
    df['ID_UNICO'] = df.apply(create_unique_id, axis=1)
    
    # Adicionando data de atualização
    df['DATA_ATUALIZACAO'] = datetime.now()
    
    # Se existe um arquivo de dados consolidados, carregar
    if os.path.exists('dados_consolidados.parquet'):
        df_consolidated = pd.read_parquet('dados_consolidados.parquet')
        
        # Combinando dados antigos com novos, mantendo apenas os mais recentes
        df_all = pd.concat([df_consolidated, df])
        df_all = df_all.sort_values('DATA_ATUALIZACAO').drop_duplicates(
            subset=['ID_UNICO'], 
            keep='last'
        )
    else:
        df_all = df
    
    # Salvando dados consolidados
    df_all.to_parquet('dados_consolidados.parquet')
    
    # Registrando log de atualização
    with open('log_atualizacao.txt', 'a') as f:
        f.write(f"{datetime.now()} - Registros processados: {len(df)}, "
                f"Registros únicos após processamento: {len(df_all)}\n")
    
    return df_all

def load_data():
    """Carrega e processa os dados do Excel"""
    try:
        # Lendo o arquivo Excel
        df = pd.read_excel('Importação.xlsx')
        
        # Convertendo datas
        df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
        
        # Convertendo QTDE CONTAINER para numérico
        df['QTDE CONTAINER'] = df['QTDE CONTAINER'].str.replace(',', '.').astype(float)
        
        # Removendo duplicidades
        df = remove_duplicates(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return None

def show_update_info():
    """Exibe informações sobre as atualizações dos dados"""
    if os.path.exists('log_atualizacao.txt'):
        with open('log_atualizacao.txt', 'r') as f:
            last_updates = f.readlines()[-5:]  # Mostra as últimas 5 atualizações
        
        st.sidebar.markdown("### ⏱️ Últimas Atualizações")
        for update in last_updates:
            st.sidebar.text(update.strip())

def main():
    st.title("📊 Dashboard de Oportunidades Comerciais")
    st.markdown("### Análise de Importações e Oportunidades de Negócio")

    # Adicionando informações de atualização na sidebar
    show_update_info()

    try:
        # Carregando os dados
        df = load_data()
        
        if df is None:
            st.error("Não foi possível carregar os dados.")
            return

        # Exibindo última atualização
        st.sidebar.markdown(f"### 🔄 Status dos Dados")
        st.sidebar.markdown(f"Última atualização: {df['DATA_ATUALIZACAO'].max().strftime('%d/%m/%Y %H:%M')}")
        st.sidebar.markdown(f"Total de registros únicos: {len(df)}")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_containers = df['QTDE CONTAINER'].sum()
            st.metric("Total de Containers", f"{int(total_containers):,}")
            
        with col2:
            total_clientes = df['CONSIGNATÁRIO'].nunique()
            st.metric("Total de Clientes", f"{total_clientes:,}")
            
        with col3:
            total_estados = df['UF CONSIGNATÁRIO'].nunique()
            st.metric("Estados Atendidos", total_estados)
            
        with col4:
            total_mercadorias = df['MERCADORIA'].nunique()
            st.metric("Tipos de Mercadorias", total_mercadorias)

        # Análise por Estado
        st.markdown("### 📍 Distribuição por Estado")
        
        # Agrupando dados por estado
        estado_data = df.groupby('UF CONSIGNATÁRIO').agg({
            'QTDE CONTAINER': 'sum',
            'CONSIGNATÁRIO': 'nunique',
            'ID_UNICO': 'count'  # Contagem de registros únicos
        }).reset_index()
        estado_data.columns = ['UF', 'Containers', 'Clientes', 'Registros']
        estado_data = estado_data.sort_values('Containers', ascending=False)

        # Visualizações
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                estado_data.head(10),
                x='UF',
                y='Containers',
                title='Top 10 Estados por Volume de Containers',
                color='Containers',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.scatter(
                estado_data,
                x='Containers',
                y='Clientes',
                text='UF',
                title='Relação entre Volume de Containers e Número de Clientes',
                size='Containers',
                color='Clientes',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Timeline de chegadas
        st.markdown("### 📅 Timeline de Chegadas")
        
        timeline_data = df.groupby('ETA').agg({
            'QTDE CONTAINER': 'sum',
            'CONSIGNATÁRIO': 'nunique',
            'ID_UNICO': 'count'
        }).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timeline_data['ETA'],
            y=timeline_data['QTDE CONTAINER'],
            name='Containers',
            mode='lines+markers'
        ))
        fig.update_layout(title='Volume de Containers por Data de Chegada')
        st.plotly_chart(fig, use_container_width=True)

        # Análise de Duplicidades (para monitoramento)
        if st.sidebar.checkbox("Mostrar Análise de Duplicidades"):
            st.markdown("### 🔍 Análise de Duplicidades")
            duplicates = df.groupby('ID_UNICO').size().reset_index(name='contagem')
            duplicates = duplicates[duplicates['contagem'] > 1]
            
            if not duplicates.empty:
                st.warning(f"Encontrados {len(duplicates)} registros com potenciais duplicidades.")
                st.dataframe(duplicates)
            else:
                st.success("Nenhuma duplicidade encontrada nos dados!")

        # Recomendações
        st.markdown("### 📋 Recomendações Comerciais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🔴 Prioridade Alta
            - Foco em RJ, SP e MG
            - Visitas prioritárias aos maiores importadores
            - Desenvolver pacotes especiais para grandes volumes
            """)
            
        with col2:
            st.markdown("""
            #### 🟡 Prioridade Média
            - Manter relacionamento ativo
            - Identificar oportunidades de cross-selling
            - Desenvolver estratégias de crescimento
            """)
            
        with col3:
            st.markdown("""
            #### 🟢 Prioridade Baixa
            - Monitorar mercado
            - Buscar parcerias estratégicas
            - Avaliar potencial de crescimento
            """)

    except Exception as e:
        st.error(f"Erro ao processar os dados: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()