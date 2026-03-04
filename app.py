# 5. PAINEL DE CONTROLE E GRÁFICO DINÂMICO
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado Dinâmico")
    
    # --- FILTROS LADO A LADO ---
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unidades_disponiveis = sorted(st.session_state.db['Unidade'].unique().tolist())
        unidades_sel = st.multiselect(
            "📍 Selecione as Unidades:", 
            options=unidades_disponiveis, 
            default=unidades_disponiveis
        )
        
    with col_f2:
        tipos_disponiveis = sorted(st.session_state.db['Tipo'].unique().tolist())
        tipos_sel = st.multiselect(
            "♻️ Selecione os Materiais:", 
            options=tipos_disponiveis, 
            default=tipos_disponiveis
        )
    
    # Seletor de período (Slider)
    p_graf = st.select_slider("Visualizar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    # --- LÓGICA DE FILTRAGEM CRUZADA ---
    df_f = st.session_state.db[
        (st.session_state.db['Unidade'].isin(unidades_sel)) & 
        (st.session_state.db['Tipo'].isin(tipos_sel))
    ].copy()
    
    if not df_f.empty:
        df_f = df_f.sort_values('Data', ascending=True)
        freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        # Agrupamento para o gráfico
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        # Formatação do eixo X
        if p_graf == "Semanal": resumo.index = resumo.index.strftime('%d/%m/%Y')
        elif p_graf == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        # Renderização do Gráfico
        st.bar_chart(resumo)
        
        # Métrica de resumo rápido abaixo do gráfico
        total_filtrado = df_f['Peso (kg)'].sum()
        st.caption(f"Exibindo um total de **{total_filtrado:.2f} kg** para a seleção atual.")
    else:
        st.warning("Selecione pelo menos uma unidade e um tipo de material para visualizar os dados.")

    # ... (restante do código de exportação)
