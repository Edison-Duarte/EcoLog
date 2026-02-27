import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado (Base de Dados)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])

# 3. Estilização CSS para as fontes solicitadas
st.markdown("""
    <style>
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 20px; text-align: center; margin-bottom: -15px; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 40px; text-align: center; color: #2E7D32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2, col3 = st.columns(3)
    data_input = col1.date_input("Data", datetime.now())
    tipo_input = col2.selectbox("Categoria", ["Reciclável", "Orgânico"])
    peso_input = col3.number_input("Peso (kg)", min_value=0.0, step=0.1)
    
    if st.button("Salvar Dados"):
        novo_registro = pd.DataFrame({
            'Data': [pd.to_datetime(data_input)],
            'Tipo': [tipo_input],
            'Peso (kg)': [peso_input]
        })
        st.session_state.db = pd.concat([st.session_state.db, novo_registro], ignore_index=True)
        st.success("Registrado!")
        st.rerun()

# 5. GESTÃO E EXCLUSÃO DE DADOS (Apagar um por um ou tudo)
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📋 Gestão de Registos")
    
    # Criar uma cópia para exibição com checkbox de seleção
    df_edicao = st.session_state.db.copy()
    df_edicao.insert(0, "Selecionar", False)
    
    # Tabela editável para seleção de linhas
    edited_df = st.data_editor(
        df_edicao,
        column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)},
        disabled=["Data", "Tipo", "Peso (kg)"],
        hide_index=True,
        use_container_width=True
    )

    col_btn1, col_btn2 = st.columns(2)
    
    # Botão para apagar selecionados
    if col_btn1.button("🗑️ Apagar Selecionados"):
        indices_para_manter = edited_df[edited_df["Selecionar"] == False].index
        st.session_state.db = st.session_state.db.iloc[indices_para_manter].reset_index(drop=True)
        st.rerun()

    # Botão para apagar tudo
    if col_btn2.button("💥 Limpar Toda a Base de Dados"):
        st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])
        st.rerun()

    # 6. VISUALIZAÇÃO DOS GRÁFICOS
    st.divider()
    periodo = st.select_slider("Selecione a Periodicidade do Relatório:", options=["Semanal", "Mensal", "Anual"])
    
    df_plot = st.session_state.db.copy()
    freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    # Agrupamento para o gráfico
    resumo = df_plot.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    # Formatação das datas para o gráfico bater com o inserido
    if periodo == "Semanal":
        resumo.index = resumo.index.strftime('Sem %U/%Y')
    elif periodo == "Mensal":
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        resumo.index = resumo.index.strftime('%Y')

    st.subheader(f"📊 Volume Total {periodo}")
    st.bar_chart(resumo)
    
else:
    st.info("Aguardando registos para gestão e visualização.")

# --- ASSINATURA FINAL ---
st.write("---")
st.markdown('<p class="footer-aharoni">Developed by:</p>', unsafe_allow_html=True)
st.markdown('<p class="footer-gabriola">Edison Duarte Filho®</p>', unsafe_allow_html=True)
