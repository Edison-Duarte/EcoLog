# 5. GRÁFICO (Atualizado com Filtro de Unidades)
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado")
    
    # --- FILTRO DE UNIDADES ---
    unidades_disponiveis = st.session_state.db['Unidade'].unique().tolist()
    unidades_selecionadas = st.multiselect(
        "Filtrar por Unidade(s):", 
        options=unidades_disponiveis, 
        default=unidades_disponiveis
    )
    
    p_graf = st.select_slider("Visualizar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    # Filtrando os dados com base na seleção do usuário
    df_f = st.session_state.db[st.session_state.db['Unidade'].isin(unidades_selecionadas)].copy()
    
    if not df_f.empty:
        df_f = df_f.sort_values('Data', ascending=True)
        freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        # Formatação das datas no eixo X
        if p_graf == "Semanal": resumo.index = resumo.index.strftime('%d/%m/%Y')
        elif p_graf == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        st.bar_chart(resumo)
    else:
        st.warning("Nenhuma unidade selecionada ou sem dados para estas unidades.")

    # ... (restante do código de exportação e mensagens)
