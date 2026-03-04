import streamlit as st
import pandas as pd
from datetime import datetime
import io
from fpdf import FPDF

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS (Regras Office)
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; margin-bottom: 0.5em; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; margin-bottom: 0; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; margin-top: 0; line-height: 1.0; }
    </style>
    """, unsafe_allow_html=True)

# Função para Gerar PDF
def gerar_pdf(df, unidade_filtro):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio de Residuos - Unidade: {unidade_filtro}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(50, 10, "Tipo", 1)
    pdf.cell(40, 10, "Peso (kg)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    for i, row in df.iterrows():
        pdf.cell(40, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, row['Tipo'], 1)
        pdf.cell(40, 10, str(row['Peso (kg)']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2 = st.columns(2)
    unidade_input = col1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_input = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    
    col3, col4 = st.columns(2)
    tipo_input = col3.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_input = col4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    if st.button("Salvar Dados"):
        if peso_input > 0:
            novo_registro = pd.DataFrame({
                'Data': [pd.to_datetime(data_input)],
                'Unidade': [unidade_input],
                'Tipo': [tipo_input],
                'Peso (kg)': [peso_input]
            })
            st.session_state.db = pd.concat([st.session_state.db, novo_registro], ignore_index=True)
            st.session_state.input_key += 1
            st.success("Registrado com sucesso!")
            st.rerun()

# 5. FILTRO E GESTÃO
if not st.session_state.db.empty:
    st.divider()
    unidade_f = st.sidebar.multiselect("Filtrar por Unidade", ["Angra dos Reis", "Guarujá"], default=["Angra dos Reis", "Guarujá"])
    df_filtrado = st.session_state.db[st.session_state.db['Unidade'].isin(unidade_f)]

    st.subheader("📋 Registros e Relatórios")
    
    # Editor de dados
    st.data_editor(df_filtrado, use_container_width=True, hide_index=True)

    # 6. GERAÇÃO DE RELATÓRIOS E COMPARTILHAMENTO
    col_rel1, col_rel2, col_rel3 = st.columns(3)
    
    # PDF
    pdf_bytes = gerar_pdf(df_filtrado, "Geral" if len(unidade_f) > 1 else unidade_f[0])
    col_rel1.download_button("📥 Baixar PDF", data=pdf_bytes, file_name="relatorio_ecolog.pdf", mime="application/pdf")
    
    # WhatsApp (Texto resumido)
    texto_whats = f"Relatorio EcoLog: {len(df_filtrado)} registros encontrados."
    link_whats = f"https://wa.me/?text={texto_whats}"
    col_rel2.markdown(f'[<button style="width:100%">📲 WhatsApp</button>]({link_whats})', unsafe_allow_html=True)
    
    # Email
    corpo_email = "Segue em anexo o resumo da gestao de residuos."
    link_email = f"mailto:?subject=Relatorio EcoLog&body={corpo_email}"
    col_rel3.markdown(f'[<button style="width:100%">📧 E-mail</button>]({link_email})', unsafe_allow_html=True)

    # 7. GRÁFICOS
    st.divider()
    periodo = st.select_slider("Periodicidade:", options=["Semanal", "Mensal", "Anual"])
    freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    if not df_filtrado.empty:
        resumo = df_filtrado.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        st.bar_chart(resumo)
else:
    st.info("O banco de dados está vazio.")

# Assinatura
st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
