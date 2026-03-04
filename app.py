import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# Tentativa de importar a biblioteca PDF
try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' não foi encontrada. Instale-a com: pip install fpdf2")

# --- BANCO DE DADOS LOCAL ---
DB_FILE = "banco_de_dados.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 2. CSS PARA ESTILIZAÇÃO E RODAPÉ
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; line-height: 1.0; }
    
    /* Centralizar o botão de download */
    .stDownloadButton {
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Função para Gerar PDF Completo
def gerar_pdf_completo(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "EcoLog - Relatório Completo de Resíduos", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(35, 10, "Data", 1, 0, 'C', True)
    pdf.cell(50, 10, "Unidade", 1, 0, 'C', True)
    pdf.cell(60, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(45, 10, "Peso (kg)", 1, 1, 'C', True)
    
    # Dados
    pdf.set_font("Arial", "", 10)
    df_sorted = df.sort_values('Data', ascending=False)
    for _, r in df_sorted.iterrows():
        pdf.cell(35, 10, r['Data'].strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(50, 10, str(r['Unidade']), 1, 0, 'C')
        pdf.cell(60, 10, str(r['Tipo']), 1, 0, 'C')
        pdf.cell(45, 10, f"{r['Peso (kg)']:.2f}", 1, 1, 'C')
    
    # Rodapé do PDF
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 10, f"Total Geral: {df['Peso (kg)'].sum():.2f} kg", ln=True, align='R')
    
    return bytes(pdf.output())

# 4. Interface Principal
st.title("♻️ EcoLog - Gestão de Resíduos")

with st.expander("➕ Registrar Coleta", expanded=True):
    c1, c2 = st.columns(2)
    unidade = c1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u{st.session_state.input_key}")
    data = c2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
    c3, c4 = st.columns(2)
    tipo = c3.selectbox("Tipo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
    peso = c4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
    
    if st.button("💾 Salvar Registro", use_container_width=True):
        if peso > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data)], 'Unidade': [unidade], 'Tipo': [tipo], 'Peso (kg)': [peso]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.session_state.input_key += 1
            st.rerun()

# 5. GRÁFICO CRONOLÓGICO
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado")

    p_graf = st.select_slider("Visualizar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    # Ordenação correta para o gráfico
    df_f = st.session_state.db.copy().sort_values('Data', ascending=True)
    resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    if p_graf == "Semanal":
        resumo.index = resumo.index.strftime('%d/%m/%Y')
    elif p_graf == "Mensal":
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        resumo.index = resumo.index.strftime('%Y')
    
    st.bar_chart(resumo)

    # 6. EXPORTAÇÃO (APENAS PDF CENTRALIZADO)
    st.write("📤 **Exportar:**")
    
    col_a, col_b, col_c = st.columns([1, 2, 1]) # Coluna central maior para o botão
    with col_b:
        pdf_bytes = gerar_pdf_completo(st.session_state.db)
        st.download_button(
            label="📥 Gerar Relatório PDF Completo",
            data=pdf_bytes,
            file_name="relatorio_completo_ecolog.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # 7. GESTÃO
    with st.expander("⚙️ Gerenciar Dados"):
        df_edit = st.session_state.db.copy().sort_values('Data', ascending=False)
        df_edit.insert(0, "Sel", False)
        tabela = st.data_editor(df_edit, hide_index=True, use_container_width=True, key="ed")
        if st.button("🗑️ Excluir Selecionados"):
            indices_para_manter = tabela[tabela["Sel"] == False].index
            st.session_state.db = st.session_state.db.loc[indices_para_manter].reset_index(drop=True)
            salvar_dados(st.session_state.db)
            st.rerun()
else:
    st.info("Insira dados para visualizar o gráfico e gerar o relatório.")

st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
