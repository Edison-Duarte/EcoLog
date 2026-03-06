import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Tentativa de importar a biblioteca PDF
try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' é necessária. Instale-a para gerar PDFs.")

# --- 1. BANCO DE DADOS LOCAL (CSV) ---
DB_FILE = "banco_de_dados.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
    return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; }
    
    .btn-row { display: flex; gap: 10px; width: 100%; margin-top: 10px; }
    .btn-link { text-decoration: none; flex: 1; }
    .custom-st-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: white; color: rgb(49, 51, 63);
        width: 100%; border-radius: 0.5rem; border: 1px solid rgba(49, 51, 63, 0.2);
        height: 38.4px; font-size: 14px; font-weight: 400; text-align: center;
    }
    .custom-st-btn:hover { border-color: rgb(255, 75, 75); color: rgb(255, 75, 75); }
    [data-testid="stDownloadButton"] { display: flex; justify-content: center; }
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
st.title("♻️ EcoLog - Gestão de Resíduos")

with st.expander("➕ Registrar Coleta", expanded=True):
    c1, c2 = st.columns(2)
    unidade = c1.selectbox("Unidade", ["Angra dos Reis", "Guarujá", Ilha Bela"], key=f"u{st.session_state.input_key}")
    data_input = c2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
    c3, c4 = st.columns(2)
    tipo = c3.selectbox("Tipo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
    peso = c4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
    
    if st.button("💾 Salvar Registro", use_container_width=True):
        if peso > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_input)], 'Unidade': [unidade], 'Tipo': [tipo], 'Peso (kg)': [peso]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.session_state.input_key += 1
            st.rerun()

# --- 6. GRÁFICO DINÂMICO ---
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado Dinâmico")
    
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

    p_graf = st.select_slider("Agrupar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    if len(periodo_sel) == 2:
        start_date, end_date = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_date) & (st.session_state.db['Data'].dt.date <= end_date) & (st.session_state.db['Unidade'].isin(u_sel)) & (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
    else:
        df_f = pd.DataFrame()

    if not df_f.empty:
        df_f = df_f.sort_values('Data')
        freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        if p_graf == "Semanal": resumo.index = resumo.index.strftime('%d/%m/%Y')
        elif p_graf == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        st.bar_chart(resumo)

        # --- 7. EXPORTAÇÃO ---
        st.write("📤 **Exportar Seleção Atual:**")
        pdf_b = gerar_pdf_completo(df_f) 
        st.download_button("📥 Gerar PDF do Período", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)

        total_kg = df_f['Peso (kg)'].sum()
        txt = f"♻️ *Relatório EcoLog*\\nTotal Filtrado: {total_kg:.2f} kg"
        link_w = f"https://wa.me/?text={txt.replace('\\n', '%0A')}"
        link_e = f"mailto:?subject=Relatorio EcoLog&body={txt.replace('\\n', '%0D%0A')}"

        st.markdown(f'<div class="btn-row"><a href="{link_w}" target="_blank" class="btn-link"><div class="custom-st-btn">📲 WhatsApp</div></a><a href="{link_e}" class="btn-link"><div class="custom-st-btn">📧 E-mail</div></a></div>', unsafe_allow_html=True)

    # --- 8. GESTÃO DE DADOS (COM SENHA E CHECKBOX) ---
    st.divider()
    with st.expander("⚙️ Gerenciar Banco de Dados"):
        st.write("Selecione as linhas que deseja remover:")
        
        # Cria cópia com coluna de seleção
        df_gestao = st.session_state.db.copy()
        df_gestao.insert(0, "Selecionar", False)
        
        # Editor de dados com checkbox
        tabela_editada = st.data_editor(
            df_gestao,
            column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)},
            disabled=["Data", "Unidade", "Tipo", "Peso (kg)"],
            hide_index=True,
            use_container_width=True
        )
        
        # Filtra as linhas selecionadas para exclusão
        linhas_selecionadas = tabela_editada[tabela_editada["Selecionar"] == True]
        
        if not linhas_selecionadas.empty:
            st.warning(f"Você selecionou {len(linhas_selecionadas)} registro(s) para exclusão.")
            
            # Campo de senha
            senha = st.text_input("Digite a senha para confirmar a exclusão:", type="password")
            
            if st.button("🗑️ Confirmar Exclusão Definitiva", type="primary"):
                if senha == "1234":
                    # Mantém apenas as linhas que NÃO foram selecionadas
                    indices_para_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
                    st.session_state.db = st.session_state.db.iloc[indices_para_manter].reset_index(drop=True)
                    salvar_dados(st.session_state.db)
                    st.success("Registros excluídos com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta! A exclusão foi cancelada.")
        else:
            st.info("Nenhuma linha selecionada para exclusão.")

else:
    st.info("Insira dados para habilitar as ferramentas.")

st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)

