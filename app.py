import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# Tentativa de importar a biblioteca PDF
try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' é necessária.")

# --- 1. CONEXÃO COM GOOGLE SHEETS ---
# O Streamlit buscará as credenciais em .streamlit/secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a planilha "Página1" (ou o nome da sua aba)
        df = conn.read(ttl="0s") # ttl=0 para carregar dados frescos sempre
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    # Sobrescreve a planilha com o DataFrame atualizado
    conn.update(data=df)

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog Cloud - Gestão de Resíduos", page_icon="♻️", layout="centered")

if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 40px; padding-top: 20px; }
    .footer-container p { margin: 0 !important; padding: 0 !important; line-height: 1.1 !important; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; }
    .footer-label { font-family: 'Bodoni MT', serif; font-size: 14px; color: #444; margin-top: 4px !important; font-style: italic; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 38px; color: #2E7D32; font-weight: bold; }
    
    .btn-row { display: flex; gap: 10px; width: 100%; margin-top: 10px; }
    .btn-link { text-decoration: none; flex: 1; }
    .custom-st-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: white; color: rgb(49, 51, 63);
        width: 100%; border-radius: 0.5rem; border: 1px solid rgba(49, 51, 63, 0.2);
        height: 38.4px; font-size: 14px; font-weight: 400; text-align: center;
    }
    .custom-st-btn:hover { border-color: rgb(255, 75, 75); color: rgb(255, 75, 75); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÃO PDF ---
def gerar_pdf_completo(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "EcoLog - Relatorio de Residuos", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(35, 10, "Data", 1, 0, 'C', True)
    pdf.cell(50, 10, "Unidade", 1, 0, 'C', True)
    pdf.cell(60, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(45, 10, "Peso (kg)", 1, 1, 'C', True)
    pdf.set_font("Arial", "", 10)
    for _, r in df.sort_values('Data', ascending=False).iterrows():
        pdf.cell(35, 10, r['Data'].strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(50, 10, str(r['Unidade'])[:20], 1, 0, 'C')
        pdf.cell(60, 10, str(r['Tipo'])[:25], 1, 0, 'C')
        pdf.cell(45, 10, f"{r['Peso (kg)']:.2f}", 1, 1, 'C')
    return bytes(pdf.output())

# --- 5. INTERFACE DE ENTRADA ---
st.title("♻️ EcoLog - Cloud Edition")

with st.expander("➕ Registrar Coleta", expanded=True):
    c1, c2 = st.columns(2)
    unidade = c1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u{st.session_state.input_key}")
    data_input = c2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
    c3, c4 = st.columns(2)
    tipo = c3.selectbox("Tipo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
    peso = c4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
    
    if st.button("💾 Salvar no Google Sheets", use_container_width=True):
        if peso > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_input).strftime('%Y-%m-%d')], 'Unidade': [unidade], 'Tipo': [tipo], 'Peso (kg)': [peso]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.session_state.input_key += 1
            st.success("Dados sincronizados na nuvem!")
            st.rerun()

# --- 6. GRÁFICO DINÂMICO ---
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado Dinâmico")
    
    # Filtros
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1.2])
    with f_col1:
        u_ops = sorted(st.session_state.db['Unidade'].unique())
        u_sel = st.multiselect("📍 Unidades:", u_ops, default=u_ops)
    with f_col2:
        t_ops = sorted(st.session_state.db['Tipo'].unique())
        t_sel = st.multiselect("♻️ Materiais:", t_ops, default=t_ops)
    with f_col3:
        data_min = st.session_state.db['Data'].min().date()
        data_max = st.session_state.db['Data'].max().date()
        periodo_sel = st.date_input("📅 Período:", value=(data_min, data_max), min_value=data_min, max_value=data_max)

    p_graf = st.select_slider("Agrupar por:", options=["Semanal", "Mensal", "Anual"])
    
    if len(periodo_sel) == 2:
        start_date, end_date = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_date) & (st.session_state.db['Data'].dt.date <= end_date) & (st.session_state.db['Unidade'].isin(u_sel)) & (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
    else:
        df_f = pd.DataFrame()

    if not df_f.empty:
        df_f = df_f.sort_values('Data', ascending=False)
        
        # Gráfico
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo_grafico = df_f.groupby([pd.Grouper(key='Data', freq=freq_map[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        st.bar_chart(resumo_grafico)

        # --- 7. EXPORTAÇÃO ---
        pdf_b = gerar_pdf_completo(df_f) 
        st.download_button("📥 Gerar PDF do Período", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)

        total_kg = df_f['Peso (kg)'].sum()
        txt = f"♻️ *RELATÓRIO ECOLOG*\\n"
        for _, r in df_f.iterrows():
            txt += f"• {r['Data'].strftime('%d/%m/%y')} | {r['Unidade']} | {r['Tipo']} | {r['Peso (kg)']}kg\\n"
        txt += f"\\n*TOTAL: {total_kg:.2f} kg*"
        
        link_w = f"https://wa.me/?text={txt.replace('\\n', '%0A')}"
        link_e = f"mailto:?subject=Relatorio EcoLog&body={txt.replace('\\n', '%0D%0A')}"

        st.markdown(f'<div class="btn-row"><a href="{link_w}" target="_blank" class="btn-link"><div class="custom-st-btn">📲 WhatsApp</div></a><a href="{link_e}" class="btn-link"><div class="custom-st-btn">📧 E-mail</div></a></div>', unsafe_allow_html=True)

    # --- 8. GESTÃO ---
    st.divider()
    with st.expander("⚙️ Gerenciar Banco de Dados Cloud"):
        df_gestao = st.session_state.db.copy()
        df_gestao.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(df_gestao, column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)}, disabled=["Data", "Unidade", "Tipo", "Peso (kg)"], hide_index=True, use_container_width=True)
        
        linhas_selecionadas = tabela_editada[tabela_editada["Selecionar"] == True]
        if not linhas_selecionadas.empty:
            senha = st.text_input("Senha de exclusão:", type="password")
            if st.button("🗑️ Confirmar Exclusão na Planilha", type="primary"):
                if senha == "1234":
                    indices_para_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
                    st.session_state.db = st.session_state.db.iloc[indices_para_manter].reset_index(drop=True)
                    salvar_dados(st.session_state.db)
                    st.success("Sincronizado!")
                    st.rerun()
else:
    st.info("Insira dados para sincronizar com o Google Sheets.")

# --- RODAPÉ ---
st.write("---")
st.markdown("""
    <div class="footer-container">
        <p class="idea-marcia">Idea of: Marcia Olsever</p>
        <p class="footer-label">Developed by:</p>
        <p class="footer-gabriola">Edison Duarte Filho®</p>
    </div>
""", unsafe_allow_html=True)
