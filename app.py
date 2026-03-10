import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Título e Configuração
st.set_page_config(page_title="EcoLog Cloud", page_icon="♻️")
st.title("♻️ EcoLog - Gestão na Nuvem")

# Conexão com a Planilha
conn = st.connection("gsheets", type=GSheetsConnection)

# Carregar Dados
df = conn.read(ttl=0)

# Formulário de Entrada
with st.form("add_data"):
    unidade = st.selectbox("Unidade", ["Angra dos Reis", "Guarujá"])
    tipo = st.selectbox("Tipo", ["Reciclável", "Orgânico"])
    peso = st.number_input("Peso (kg)", min_value=0.0)
    if st.form_submit_button("Salvar na Planilha"):
        novo_item = pd.DataFrame([{"Data": pd.Timestamp.now().strftime('%Y-%m-%d'), "Unidade": unidade, "Tipo": tipo, "Peso (kg)": peso}])
        df_atualizado = pd.concat([df, novo_item], ignore_index=True)
        conn.update(data=df_atualizado)
        st.success("Dados salvos no Google Sheets!")
        st.rerun()

# Exibir Tabela
st.divider()
st.subheader("Dados Atuais")
st.dataframe(df, use_container_width=True)

# Rodapé Personalizado
st.markdown("""
    <hr>
    <div style='text-align: center;'>
        <p style='font-family: "Gabriola"; font-size: 20px; color: #666;'>Idea of: Marcia Olsever</p>
        <p style='font-family: "Bodoni MT", serif; font-size: 14px; font-style: italic;'>Developed by:</p>
        <p style='font-family: "Gabriola"; font-size: 38px; color: #2E7D32; font-weight: bold;'>Edison Duarte Filho®</p>
    </div>
""", unsafe_allow_html=True)
