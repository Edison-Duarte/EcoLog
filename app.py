import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# Estilização da Assinatura (Aharoni/Gabriola)
st.markdown("""
    <style>
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 22px; text-align: center; margin-top: 50px; margin-bottom: -10px; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 45px; text-align: center; color: #2E7D32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("♻️ Gestão de Resíduos")
st.markdown("Sistema de Segregação: Recicláveis vs. Orgânicos")

# Banco de dados temporário na nuvem
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])

# --- ÁREA DE INPUT ---
with st.expander("➕ Registrar Nova Coleta", expanded=True):
    col1, col2, col3 = st.columns(3)
    data_input = col1.date_input("Data da Coleta", datetime.now())
    tipo_input = col2.selectbox("Tipo", ["Reciclável", "Orgânico"])
    peso_input = col3.number_input("Peso (kg)", min_value=0.0, step=0.1)
    
    if st.button("Salvar no Sistema"):
        novo_dado = pd.DataFrame([[pd.to_datetime(data_input), tipo_input, peso_input]], 
                                 columns=['Data', 'Tipo', 'Peso (kg)'])
        st.session_state.db = pd.concat([st.session_state.db, novo_dado], ignore_index=True)
        st.success("Dados registrados com sucesso!")

# --- PROCESSAMENTO E GRÁFICO ---
if not st.session_state.db.empty:
    df = st.session_state.db.copy()
    df['Data'] = pd.to_datetime(df['Data'])
    
    st.divider()
    
    # Seletor de Periodicidade conforme solicitado no início
    periodo = st.radio("Selecione o período de visualização do volume:", 
                       ["Semanal", "Mensal", "Anual"], horizontal=True)
    
    # Mapeamento técnico para o gráfico
    mapa_freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    # Agrupamento dos dados
    resumo = df.groupby([pd.Grouper(key='Data', freq=mapa_freq[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    # Ajuste de rótulos para melhor leitura
    if periodo == "Mensal":
        resumo.index = resumo.index.strftime('%B/%Y')
    elif periodo == "Semanal":
        resumo.index = resumo.index.strftime('Semana %U - %Y')
    else:
        resumo.index = resumo.index.strftime('%Y')

    st.subheader(f"📊 Volume Gerado ({periodo})")
    st.bar_chart(resumo)
    
    with st.expander("Ver Detalhamento em Tabela"):
        st.dataframe(resumo, use_container_width=True)
else:
    st.info("Insira os dados acima para gerar o gráfico de volume.")

# --- ASSINATURA EXIGIDA ---
st.write("---")
st.markdown('<p class="footer-aharoni">Developed by:</p>', unsafe_allow_html=True)
st.markdown('<p class="footer-gabriola">Edison Duarte Filho®</p>', unsafe_allow_html=True)
