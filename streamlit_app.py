import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px

st.title("Indicadores de Controle de Qualidade")
st.write(
    "Adicione o arquivo em Excel com os dados de análise:"
)

upload_file = st.file_uploader("Escolha um arquivo", type="xlsx")

if upload_file:
    
    df = pd.read_excel(upload_file)

    df['Data'] = pd.to_datetime(df['Data'])
    df['Hora Inicial '] = pd.to_datetime(df['Hora Inicial '])
    df['Hora Final'] = pd.to_datetime(df['Hora Final'])
    df['Tempo de Ciclo (min)'] = (df['Hora Final'] - df['Hora Inicial ']).dt.total_seconds() / 60
    df['is_fpy'] = df['Motivo da Correção '].isna() | (df['Motivo da Correção '].astype(str).str.strip() == "")

    # --- FILTROS LATERAIS ---
    st.sidebar.header("Filtros de Visualização")
    
    # Lista única de produtos
    lista_produtos = df['Produto'].unique()
    
    # Seleção de Produto: Iniciamos apenas com o primeiro produto para não sobrecarregar a tela
    produtos_selecionados = st.sidebar.multiselect(
        "Selecionar Produto(s)", 
        options=lista_produtos, 
        default=[lista_produtos[0]] if lista_produtos.all() else None,
        help="Selecione um ou mais produtos para comparar. Se muitos forem selecionados, os gráficos podem ficar poluídos."
    )
    
    analistas = st.sidebar.multiselect(
        "Selecionar Analista", 
        options=df['Analista da Qualidade'].unique(), 
        default=df['Analista da Qualidade'].unique()
    )
    
    # Aplicando o filtro
    filtered_df = df[(df['Produto'].isin(produtos_selecionados)) & (df['Analista da Qualidade'].isin(analistas))]

    if not produtos_selecionados:
        st.warning("⚠️ Por favor, selecione pelo menos um **Produto** no menu lateral para visualizar as análises.")
    else:
        # --- MÉTRICAS KPI ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Ordens", len(filtered_df))
        with col2:
            fpy_rate = (filtered_df['is_fpy'].sum() / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
            st.metric("First Pass Yield", f"{fpy_rate:.1f}%")
        with col3:
            custo_total = filtered_df['Custo da Correção'].sum()
            st.metric("Custo Total de Correção", f"R$ {custo_total:,.2f}")
        with col4:
            avg_cycle = filtered_df['Tempo de Ciclo (min)'].mean()
            st.metric("Tempo Médio de Análise", f"{avg_cycle:.1f} min")

        # --- VISUALIZAÇÕES ---
        
        # 1. Estabilidade por Produto
        st.subheader("📈 Estabilidade de Parâmetros por Produto")
        metrica = st.selectbox("Escolha o parâmetro para análise", ["PH", "Viscosidade", "Densidade"])
        
        # Se houver muitos produtos, avisamos que a visualização pode ser difícil
        if len(produtos_selecionados) > 6:
            st.info("💡 Dica: Você selecionou muitos produtos. Para uma análise detalhada, tente selecionar no máximo 4 por vez.")

        fig_stab = px.scatter(
            filtered_df, 
            x='Data', 
            y=metrica, 
            facet_col='Produto', 
            facet_col_wrap=2, # No máximo 2 colunas para manter a legibilidade
            #markers=True,
            color='Produto',
            title=f"Tendência de {metrica} (Escalas Independentes por Produto)"
        )
        fig_stab.update_yaxes(matches=None) # Mantém as escalas verticais independentes
        st.plotly_chart(fig_stab, use_container_width=True)

        # 2. Motivos de Correção e Custos
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("⚠️ Motivos de Correção (Pareto)")
            df_correcoes = filtered_df[~filtered_df['is_fpy']]
            if not df_correcoes.empty:
                pareto_data = df_correcoes['Motivo da Correção '].value_counts().reset_index()
                pareto_data.columns = ['Motivo', 'Frequência']
                fig_pareto = px.bar(pareto_data, x='Motivo', y='Frequência', color='Motivo')
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.write("Nenhuma correção registrada para os produtos selecionados.")
            
        with col_b:
            st.subheader("💰 Distribuição de Custos")
            cost_prod = filtered_df.groupby('Produto')['Custo da Correção'].sum().reset_index()
            fig_cost = px.pie(cost_prod, values='Custo da Correção', names='Produto', hole=0.4)
            st.plotly_chart(fig_cost, use_container_width=True)

        # Tabela de Dados
        if st.checkbox("Visualizar Tabela de Dados"):
            st.dataframe(filtered_df)

else:
    st.info("Aguardando upload do arquivo CSV para gerar o dashboard.")