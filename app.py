import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a planilha em tempo real
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
        
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    try:
        # Converte para string para garantir gravação correta no Sheets
        df_save = df.copy()
        df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d')
        conn.update(data=df_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# Inicializa o banco na sessão
if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO (RODAPÉ COMPACTO E BOTÕES) ---
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 40px; line-height: 1.0 !important; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 22px; color: #666; margin-bottom: -15px !important; }
    .footer-label { font-family: 'Bodoni MT', serif; font-size: 14px; color: #444; font-style: italic; margin-bottom: -25px !important; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 38px; color: #2E7D32; font-weight: bold; }
    
    .btn-row { display: flex; gap: 10px; width: 100%; margin-top: 10px; }
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
    unidade = c1.selectbox("Unidade", ["Guarujá", "Angra dos Reis", "Ilha Bela"], key=f"u{st.session_state.input_key}")
    data_input = c2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
    c3, c4 = st.columns(2)
    tipo = c3.selectbox("Tipo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
    peso = c4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
    
    if st.button("💾 Salvar Registro", use_container_width=True):
        if peso > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_input)], 'Unidade': [unidade], 'Tipo': [tipo], 'Peso (kg)': [peso]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.success("Dados salvos no histórico permanente!")
            st.session_state.input_key += 1
            st.rerun()

# --- 6. GRÁFICO E FILTROS ---
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
        periodo_sel = st.date_input("📅 Período:", value=(data_min, data_max))

    p_graf = st.select_slider("Agrupar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    if len(periodo_sel) == 2:
        start_date, end_date = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_date) & (st.session_state.db['Data'].dt.date <= end_date) & (st.session_state.db['Unidade'].isin(u_sel)) & (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
    else:
        df_f = pd.DataFrame()

    if not df_f.empty:
        df_f = df_f.sort_values('Data')
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo_grafico = df_f.groupby([pd.Grouper(key='Data', freq=freq_map[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        # Formatação do eixo X como Texto para não desregular o gráfico
        if p_graf == "Semanal": resumo_grafico.index = resumo_grafico.index.strftime('%d/%m/%Y')
        elif p_graf == "Mensal": resumo_grafico.index = resumo_grafico.index.strftime('%b/%Y')
        else: resumo_grafico.index = resumo_grafico.index.strftime('%Y')
        
        st.bar_chart(resumo_grafico)

       # --- EXPORTAÇÃO E COMPARTILHAMENTO ---
        st.write("📤 **Exportar Seleção Atual:**")
        
        # 1. Botão de PDF (mantido)
        pdf_b = gerar_pdf_completo(df_f) 
        st.download_button("📥 Baixar Relatório em PDF", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)

        # 2. Montagem do Texto Detalhado para WhatsApp/E-mail
        total_kg = df_f['Peso (kg)'].sum()
        start_date, end_date = periodo_sel
        
        # Cabeçalho
        txt_raw = f"♻️ *RELATÓRIO ECOLOG - DETALHADO*%0A"
        txt_raw += f"Período: {start_date.strftime('%d/%m/%y')} a {end_date.strftime('%d/%m/%y')}%0A"
        txt_raw += "-----------------------------%0A"
        
        # Listagem de cada item (O Relatório Completo)
        # Ordenamos por data para o texto fazer sentido cronológico
        for _, row in df_f.sort_values('Data').iterrows():
            data_str = row['Data'].strftime('%d/%m/%y')
            txt_raw += f"📅 {data_str} | {row['Unidade']}%0A"
            txt_raw += f"└ {row['Tipo']}: {row['Peso (kg)']:.2f} kg%0A%0A"
        
        txt_raw += "-----------------------------%0A"
        
        # Resumo consolidado por tipo
        resumo_tipo = df_f.groupby('Tipo')['Peso (kg)'].sum()
        txt_raw += "*RESUMO POR MATERIAL:*%0A"
        for t, p in resumo_tipo.items():
            txt_raw += f"• {t}: {p:.2f} kg%0A"
            
        # Total Geral
        txt_raw += f"-----------------------------%0A"
        txt_raw += f"🏆 *TOTAL GERAL: {total_kg:.2f} kg*"
        
        # Gerar os links
        link_w = f"https://wa.me/?text={txt_raw}"
        # O replace garante que as quebras de linha funcionem em clientes de e-mail (Outlook/Gmail)
        link_e = f"mailto:?subject=Relatorio EcoLog&body={txt_raw.replace('%0A', '%0D%0A')}"

        # Botões lado a lado
        st.markdown(f"""
            <div class="btn-row">
                <a href="{link_w}" target="_blank" class="btn-link">
                    <div class="custom-st-btn">📲 WhatsApp</div>
                </a>
                <a href="{link_e}" class="btn-link">
                    <div class="custom-st-btn">📧 E-mail</div>
                </a>
            </div>
        """, unsafe_allow_html=True)
    # --- 7. GESTÃO DE DADOS ---
    st.divider()
    with st.expander("⚙️ Gerenciar Banco de Dados"):
        df_gestao = st.session_state.db.copy()
        df_gestao.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(df_gestao, column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)}, disabled=["Data", "Unidade", "Tipo", "Peso (kg)"], hide_index=True, use_container_width=True)
        if st.button("🗑️ Confirmar Exclusão Selecionados", type="primary"):
            indices_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices_manter].reset_index(drop=True)
            salvar_dados(st.session_state.db)
            st.rerun()

# --- 8. RODAPÉ ---
st.write("---")
st.markdown("""
    <div class="footer-container">
        <div class="idea-marcia">Idea of: Marcia Olsever</div>
        <div class="footer-label">Developed by:</div>
        <div class="footer-gabriola">Edison Duarte Filho®</div>
    </div>
""", unsafe_allow_html=True)

