import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuração da página (Deve ser a primeira coisa)
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado (Evita o NameError)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])

# 3. Estilização CSS para as fontes
st.markdown("""
    <style>
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 20px; text-align: center; margin-bottom: -15px; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 40px; text-align: center; color: #2E7D32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("♻️ EcoLog - Gestão de Resíduos")

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
        st.rerun() # Atualiza o gráfico imediatamente

# 5. VISUALIZAÇÃO (Só executa se houver dados)
if not st.session_state.db.empty:
    df = st.session_state.db.copy()
    
    st.divider()
    periodo = st.select_slider("Selecione a Periodicidade:", options=["Semanal", "Mensal", "Anual"])
    
    # Mapeamento de frequências
    freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    # Agrupamento e formatação para o gráfico bater com a data
    resumo = df.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    if periodo == "Semanal":
        resumo.index = resumo.index.strftime('Sem %U/%Y')
    elif periodo == "Mensal":
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        resumo.index = resumo.index.strftime('%Y')

    st.subheader(f"📊 Volume Total {periodo}")
    st.bar_chart(resumo)
    
    with st.expander("📄 Ver tabela de dados"):
        st.dataframe(resumo, use_container_width=True)
else:
    st.info("Aguardando o primeiro registro para gerar os gráficos.")

# 6. ASSINATURA FINAL
st.write("---")
st.markdown('<p class="footer-aharoni">Developed by:</p>', unsafe_allow_html=True)
st.markdown('<p class="footer-gabriola">Edison Duarte Filho®</p>', unsafe_allow_html=True)


