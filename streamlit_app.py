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

    # Toggle de normalização
    normalizar = st.sidebar.toggle("Normalização", value=False)
    
    # Lista única de produtos
    lista_produtos = df['Produto'].unique()
    
    # Seleção de Produto: Iniciamos apenas com o primeiro produto para não sobrecarregar a tela
    produtos_selecionados = st.sidebar.multiselect(
        "Selecionar Produto(s)", 
        options=lista_produtos, 
        default=[lista_produtos[0]] if lista_produtos.all() else None,
        help="Selecione um ou mais produtos para comparar. Se muitos forem selecionados, os gráficos podem ficar poluídos."
    )
  
    # Aplicando o filtro
    filtered_df = df[(df['Produto'].isin(produtos_selecionados))]

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
        
        # --- LÓGICA DE PLOTAGEM ---
        metricas_disponiveis = ["PH", "Viscosidade", "Densidade"]
        metrica_alvo = st.sidebar.selectbox("Métrica para o Gráfico", metricas_disponiveis)
        coluna_para_plot = metrica_alvo
        titulo_y = f"Valor Real de {metrica_alvo}"

        if normalizar:
            # Calculamos o Z-Score para cada produto individualmente
            # (Valor - Média do Produto) / Desvio Padrão do Produto
            filtered_df['Z-Score'] = filtered_df.groupby('Produto')[metrica_alvo].transform(
                lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
            )
            coluna_para_plot = 'Z-Score'
            titulo_y = f"Estabilidade (Z-Score de {metrica_alvo})"
            st.info("💡 **Modo Normalizado:** O valor '0' no gráfico representa a média exata de cada produto.")
        
        # Criando o gráfico único
        fig = px.line(
            filtered_df,
            x='Data',
            y=coluna_para_plot,
            color='Produto',
            markers=True,
            title=f"Comparativo de {metrica_alvo}: " + ("Escala Normalizada" if normalizar else "Valores Reais")
        )

        if normalizar:
            fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Média Individual")

        st.plotly_chart(fig, use_container_width=True)

        # --- TABELA DE ESTABILIDADE ---
        st.subheader("📊 Resumo Estatístico")
        resumo = filtered_df.groupby('Produto')[metrica_alvo].agg(['mean', 'std', 'min', 'max']).reset_index()
        resumo.columns = ['Produto', 'Média', 'Desvio Padrão (Volatilidade)', 'Mín', 'Máx']
        st.dataframe(resumo, use_container_width=True)

        # 2. Motivos de Correção e Custos

        st.subheader("⚠️ Motivos de Correção (Pareto)")
        df_correcoes = filtered_df[~filtered_df['is_fpy']]
        if not df_correcoes.empty:
            pareto_data = df_correcoes['Motivo da Correção '].value_counts().reset_index()
            pareto_data.columns = ['Motivo', 'Frequência']
            fig_pareto = px.bar(pareto_data, x='Motivo', y='Frequência', color='Motivo')
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.write("Nenhuma correção registrada para os produtos selecionados.")
            

        # Tabela de Dados
        if st.checkbox("Visualizar Tabela de Dados"):
            st.dataframe(filtered_df)

else:
    st.info("Aguardando upload do arquivo CSV para gerar o dashboard.")