import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="EcoLog - Gestão Mensal", page_icon="♻️")

# Estilização da Assinatura
st.markdown("""
    <style>
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 20px; text-align: center; margin-top: 30px; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 38px; text-align: center; color: #1E5631; font-weight: bold; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

st.title("♻️ Gestão de Resíduos")
st.subheader("Monitoramento de Volume Mensal")

# Inicialização do Banco de Dados na sessão
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])

# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Registrar Coleta")
    data_input = st.date_input("Data", datetime.now())
    tipo_input = st.radio("Tipo de Resíduo", ["Reciclável", "Orgânico"])
    peso_input = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
    
    if st.button("Salvar Registro"):
        novo = pd.DataFrame([[pd.to_datetime(data_input), tipo_input, peso_input]], 
                             columns=['Data', 'Tipo', 'Peso (kg)'])
        st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
        st.success("Registrado!")

# --- EXIBIÇÃO DO GRÁFICO MENSAL ---
if not st.session_state.db.empty:
    df = st.session_state.db.copy()
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Agrupamento fixo por Mês
    # 'ME' agrupa pelo fim do mês (Month End)
    resumo_mensal = df.groupby([pd.Grouper(key='Data', freq='ME'), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    # Formatação da data para exibição (Ex: Jan/2026)
    resumo_mensal.index = resumo_mensal.index.strftime('%b/%Y')

    st.write("### Volume por Categoria (kg)")
    st.bar_chart(resumo_mensal)
    
    st.write("### Detalhamento Mensal")
    st.dataframe(resumo_mensal, use_container_width=True)
else:
    st.info("💡 Dica: Adicione os dados na barra lateral para visualizar o gráfico mensal.")

# --- ASSINATURA ---
st.markdown('<p class="footer-aharoni">Developed by:</p>', unsafe_allow_html=True)
st.markdown('<p class="footer-gabriola">Edison Duarte Filho®</p>', unsafe_allow_html=True)
