import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' não foi encontrada.")

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

# 2. CSS AJUSTADO PARA ALINHAMENTO PERFEITO
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; line-height: 1.0; }
    
    /* Forçar colunas lado a lado no mobile */
    [data-testid="column"] {
        width: calc(33.3333% - 1rem) !important;
        flex: 1 1 calc(33.3333% - 1rem) !important;
        min-width: calc(33.3333% - 1rem) !important;
    }

    .stDownloadButton, .btn-link {
        width: 100%;
    }
    
    .custom-st-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: rgb(255, 255, 255);
        color: rgb(49, 51, 63);
        padding: 0px 0.5rem;
        width: 100%;
        border-radius: 0.5rem;
        font-weight: 400;
        line-height: 1.6;
        text-decoration: none;
        vertical-align: middle;
        border: 1px solid rgba(49, 51, 63, 0.2);
        height: 38.4px; 
        font-size: 14px; /* Reduzido levemente para caber melhor em telas pequenas */
        transition: border-color 0.2s, color 0.2s;
        box-sizing: border-box;
    }
    
    .custom-st-btn:hover {
        border-color: rgb(255, 75, 75);
        color: rgb(255, 75, 75);
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Função PDF
def gerar_pdf(df, info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "EcoLog - Relatorio".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(50, 10, "Unidade", 1)
    pdf.cell(60, 10, "Tipo", 1)
    pdf.cell(40, 10, "Peso (kg)", 1, 1)
    pdf.set_font("Arial", "", 10)
    df_pdf = df.sort_values('Data', ascending=False)
    for _, r in df_pdf.iterrows():
        pdf.cell(40, 10, r['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, str(r['Unidade'])[:20], 1)
        pdf.cell(60, 10, str(r['Tipo'])[:25], 1)
        pdf.cell(40, 10, f"{r['Peso (kg)']:.2f}", 1, 1)
    return bytes(pdf.output())

st.title("♻️ EcoLog - Gestão de Resíduos")

# 4. ENTRADA DE DADOS
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
    
    df_f = st.session_state.db.copy().sort_values('Data', ascending=True)
    resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    if p_graf == "Semanal":
        resumo.index = resumo.index.strftime('%d/%m/%Y')
    elif p_graf == "Mensal":
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        resumo.index = resumo.index.strftime('%Y')
    
    st.bar_chart(resumo)

    # Preparação de Texto
    total_periodo = df_f['Peso (kg)'].sum()
    txt_dados = f"Relatorio EcoLog (%s):\\n" % p_graf
    for idx, row in resumo.iterrows():
        txt_dados += f"- {idx}: {row.sum():.2f}kg\\n"
    txt_dados += f"\\nTotal Geral: {total_periodo:.2f}kg"

    # 6. SEÇÃO DE EXPORTAÇÃO COM ALINHAMENTO FORÇADO
    st.write("📤 **Exportar:**")
    
    # Criamos as 3 colunas
    col_pdf, col_whats, col_email = st.columns(3)
    
    with col_pdf:
        pdf_b = gerar_pdf(df_f, p_graf)
        st.download_button("📥 PDF", pdf_b, "relatorio.pdf", "application/pdf", use_container_width=True)
    
    with col_whats:
        link_w = f"https://wa.me/?text={txt_dados.replace('\\n', '%0A')}"
        st.markdown(f'<a href="{link_w}" target="_blank" class="btn-link"><div class="custom-st-btn">📲 Whats</div></a>', unsafe_allow_html=True)
        
    with col_email:
        link_e = f"mailto:?subject=Relatorio EcoLog - {p_graf}&body={txt_dados.replace('\\n', '%0D%0A')}"
        st.markdown(f'<a href="{link_e}" class="btn-link"><div class="custom-st-btn">📧 Email</div></a>', unsafe_allow_html=True)

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
    st.info("Insira dados para visualizar o gráfico.")

# Rodapé
st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
