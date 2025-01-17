import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Previsão de Chegadas",
    layout="wide"
)

def load_and_process_data():
    # Lendo o arquivo
    df = pd.read_excel('Importação.xlsx')
    
    # Convertendo datas e quantidades
    df['ETA'] = pd.to_datetime(df['ETA'], format='%d/%m/%Y')
    df['QTDE CONTAINER'] = df['QTDE CONTAINER'].str.replace(',', '.').astype(float)
    
    # Agrupando por data e UF
    previsao = df.groupby(['ETA', 'UF CONSIGNATÁRIO'])['QTDE CONTAINER'].sum().reset_index()
    
    # Ordenando por data
    previsao = previsao.sort_values('ETA')
    
    return previsao

def main():
    st.title("📦 Previsão de Chegadas de Containers")
    
    try:
        # Carregando dados
        dados = load_and_process_data()
        
        # Criando tabela pivot
        tabela_pivot = dados.pivot(
            index='ETA',
            columns='UF CONSIGNATÁRIO',
            values='QTDE CONTAINER'
        ).fillna(0)
        
        # Adicionando total por dia
        tabela_pivot['TOTAL'] = tabela_pivot.sum(axis=1)
        
        # Formatando a tabela
        tabela_formatada = tabela_pivot.copy()
        for coluna in tabela_formatada.columns:
            tabela_formatada[coluna] = tabela_formatada[coluna].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
        
        # Convertendo índice para data formatada
        tabela_formatada.index = tabela_formatada.index.strftime('%d/%m/%Y')
        
        # Exibindo a tabela
        st.markdown("### Previsão de Chegadas por Estado")
        st.dataframe(
            tabela_formatada,
            use_container_width=True,
            height=600
        )
        
        # Totais por UF
        st.markdown("### Totais por Estado")
        totais_uf = dados.groupby('UF CONSIGNATÁRIO')['QTDE CONTAINER'].sum().sort_values(ascending=False)
        totais_formatados = totais_uf.apply(lambda x: f"{int(x):,}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(totais_formatados, use_container_width=True)
        
        with col2:
            st.markdown("""
            #### Instruções:
            - A tabela mostra a quantidade de containers por UF em cada data
            - "-" indica que não há containers previstos
            - A coluna TOTAL mostra o volume total do dia
            - Os totais por estado mostram o volume acumulado no período
            """)
        
    except Exception as e:
        st.error(f"Erro ao processar os dados: {str(e)}")

if __name__ == "__main__":
    main()