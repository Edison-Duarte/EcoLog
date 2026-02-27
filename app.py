# --- VISUALIZAÇÃO ---
if not st.session_state.db.empty:
    df = st.session_state.db.copy()
    df['Data'] = pd.to_datetime(df['Data'])
    
    st.divider()
    periodo = st.select_slider("Selecione a Periodicidade do Relatório:", 
                               options=["Semanal", "Mensal", "Anual"])
    
    # Mapeamento de frequências do Pandas
    # 'W' = Semana, 'ME' = Mês (Fim), 'YE' = Ano (Fim)
    freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    # Agrupamento dos dados
    resumo = df.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    # --- AJUSTE DOS RÓTULOS (O segredo para as datas baterem) ---
    if periodo == "Semanal":
        # Exibe "Semana X - Ano"
        resumo.index = resumo.index.strftime('Sem %U/%Y')
    elif periodo == "Mensal":
        # Exibe "Mês/Ano" (Ex: Jan/2026)
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        # Exibe apenas o Ano
        resumo.index = resumo.index.strftime('%Y')

    st.subheader(f"📊 Volume Total {periodo}")
    
    # Agora o gráfico usa os rótulos formatados como texto
    st.bar_chart(resumo)
    
    with st.expander("📄 Ver tabela de dados"):
        st.dataframe(resumo, use_container_width=True)
else:
    st.info("Aguardando o primeiro registro para gerar os gráficos.")
