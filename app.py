import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

# --- 2. CONEXÃO E FUNÇÕES DE DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Data'] = pd.to_datetime(df['Data'].dt.date)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    try:
        df_save = df.copy()
        df_save['Data'] = pd.to_datetime(df_save['Data']).dt.strftime('%Y-%m-%d')
        conn.update(data=df_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO (ASSINATURA COMPACTA) ---
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 40px; padding-bottom: 20px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 24px; color: #666; line-height: 0.9 !important; margin-bottom: 2px !important; }
    .footer-label { font-family: 'Bodoni MT', serif; font-size: 16px; color: #444; font-style: italic; line-height: 0.9 !important; margin-bottom: 0px !important; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 26px; color: #2E7D32; font-weight: bold; line-height: 1.0 !important; margin-top: 2px !important; }
    
    .btn-row { display: flex; gap: 10px; width: 100%; margin-top: 15px; margin-bottom: 20px; }
    .btn-link { text-decoration: none; flex: 1; }
    .custom-st-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: white; color: rgb(49, 51, 63);
        width: 100%; border-radius: 0.5rem; border: 1px solid rgba(49, 51, 63, 0.2);
        height: 38.4px; font-size: 14px; text-align: center; transition: 0.3s;
    }
    .custom-st-btn:hover { border-color: rgb(255, 75, 75); color: rgb(255, 75, 75); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÃO PDF (COM TOTAL GERAL) ---
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
    total_peso = 0
    for _, r in df.sort_values('Data', ascending=False).iterrows():
        total_peso += r['Peso (kg)']
        pdf.cell(35, 10, r['Data'].strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(50, 10, str(r['Unidade'])[:20], 1, 0, 'C')
        pdf.cell(60, 10, str(r['Tipo'])[:25], 1, 0, 'C')
        pdf.cell(45, 10, f"{r['Peso (kg)']:.2f}", 1, 1, 'C')
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(220, 230, 220)
    pdf.cell(145, 10, "TOTAL GERAL", 1, 0, 'R', True)
    pdf.cell(45, 10, f"{total_peso:.2f} kg", 1, 1, 'C', True)
    return bytes(pdf.output())

# --- 5. INTERFACE DE ENTRADA COM BLOQUEIO DE SENHA ---
st.title("♻️ EcoLog - Gestão de Resíduos")

SENHAS_UNIDADES = {
    "Guarujá": "GUICS",
    "Angra dos Reis": "ARICS",
    "Ilha Bela": "IBICS",
    "São Paulo": "SPICS"
}

u_login = st.selectbox("Selecione sua Unidade para acessar o registro:", ["Selecione..."] + list(SENHAS_UNIDADES.keys()))

if u_login != "Selecione...":
    senha_acesso = st.text_input(f"Senha de acesso para {u_login}:", type="password")

    if senha_acesso == SENHAS_UNIDADES[u_login]:
        st.success(f"🔓 Acesso liberado para {u_login}")
        
        with st.expander("➕ Registrar Nova Coleta", expanded=True):
            c1, c2 = st.columns(2)
            data_reg = c1.date_input("Data da Coleta", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
            tipo_reg = c2.selectbox("Tipo de Resíduo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
            peso_reg = st.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
            
            if st.button("💾 Salvar Registro", use_container_width=True):
                if peso_reg > 0:
                    novo = pd.DataFrame({'Data': [pd.to_datetime(data_reg)], 'Unidade': [u_login], 'Tipo': [tipo_reg], 'Peso (kg)': [peso_reg]})
                    st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
                    salvar_dados(st.session_state.db)
                    st.success("Registro sincronizado!")
                    st.session_state.input_key += 1
                    st.rerun()
                else:
                    st.warning("Insira um peso válido.")
    elif senha_acesso != "":
        st.error("⚠️ Senha incorreta.")
else:
    st.info("Escolha uma unidade acima para liberar o formulário de inserção.")

# --- 6. GRÁFICO E RELATÓRIOS (CORREÇÃO DE VISUALIZAÇÃO) ---
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📊 Consolidado Dinâmico")
    
    # 1. Filtros
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1.2])
    with f_col1:
        u_ops = sorted(st.session_state.db['Unidade'].unique())
        u_sel = st.multiselect("📍 Unidades:", u_ops, default=u_ops)
    with f_col2:
        t_ops = sorted(st.session_state.db['Tipo'].unique())
        t_sel = st.multiselect("♻️ Materiais:", t_ops, default=t_ops)
    with f_col3:
        # Pega a data real do banco de dados para o calendário não começar vazio
        data_min_db = st.session_state.db['Data'].min().date()
        data_max_db = st.session_state.db['Data'].max().date()
        
        # O segredo está aqui: se der erro ou estiver vazio, ele usa hoje
        periodo_sel = st.date_input("📅 Período:", 
                                     value=(data_min_db, data_max_db), 
                                     format="DD/MM/YYYY")

    p_graf = st.select_slider("Agrupar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    # Validação do intervalo de datas
    if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
        start_d, end_d = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_d) & \
               (st.session_state.db['Data'].dt.date <= end_d) & \
               (st.session_state.db['Unidade'].isin(u_sel)) & \
               (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
    else:
        # Se o usuário clicou apenas em uma data, mostra tudo por enquanto
        df_f = st.session_state.db.copy()

    if not df_f.empty:
        # ... (restante do código do gráfico igual ao anterior)
        # --- EXPORTAÇÃO ---
        st.write("📤 **Exportar Seleção Atual:**")
        pdf_b = gerar_pdf_completo(df_f) 
        st.download_button("📥 Baixar Relatório em PDF", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)

        total_kg = df_f['Peso (kg)'].sum()
        txt_raw = f"♻️ *RELATÓRIO ECOLOG DETALHADO*%0APeríodo: {start_d.strftime('%d/%m/%y')} a {end_d.strftime('%d/%m/%y')}%0A-----------------------------%0A"
        for _, row in df_f.sort_values('Data').iterrows():
            txt_raw += f"📅 {row['Data'].strftime('%d/%m/%y')} | {row['Unidade']}%0A└ {row['Tipo']}: {row['Peso (kg)']:.2f} kg%0A%0A"
        
        txt_raw += "-----------------------------%0A*RESUMO POR TIPO:*%0A"
        res_t = df_f.groupby('Tipo')['Peso (kg)'].sum()
        for t, p in res_t.items():
            txt_raw += f"• {t}: {p:.2f} kg%0A"
        txt_raw += f"-----------------------------%0A🏆 *TOTAL: {total_kg:.2f} kg*"
        
        link_w = f"https://wa.me/?text={txt_raw}"
        link_e = f"mailto:?subject=Relatorio EcoLog&body={txt_raw.replace('%0A', '%0D%0A')}"

        st.markdown(f'<div class="btn-row"><a href="{link_w}" target="_blank" class="btn-link"><div class="custom-st-btn">📲 WhatsApp</div></a><a href="{link_e}" class="btn-link"><div class="custom-st-btn">📧 E-mail</div></a></div>', unsafe_allow_html=True)

# --- 8. RODAPÉ ---
st.write("---")
st.markdown("""
    <div class="footer-container">
        <div class="idea-marcia">Idea of: Marcia Olsever</div>
        <div class="footer-label">Developed by:</div>
        <div class="footer-gabriola">Edison Duarte Filho®</div>
    </div>
""", unsafe_allow_html=True)
