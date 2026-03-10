import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
# O Streamlit busca as credenciais automaticamente em .streamlit/secrets.toml (no Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Adicione o parâmetro query para garantir que ele tente ler algo
        df = conn.read(ttl=0) 
        
        # Se o que voltar não for um DataFrame válido, cria um vazio
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
            
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except Exception as e:
        # Se der erro de resposta 200, ele apenas retorna o banco vazio para você começar a preencher
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    # Atualiza a planilha inteira com o novo DataFrame
    conn.update(data=df)
    st.cache_data.clear()

# Inicializa o banco de dados na sessão
if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 40px; padding-top: 20px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 38px; color: #2E7D32; font-weight: bold; }
    .btn-row { display: flex; gap: 10px; width: 100%; margin-top: 10px; }
    .btn-link { text-decoration: none; flex: 1; }
    .custom-st-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: white; color: rgb(49, 51, 63);
        width: 100%; border-radius: 0.5rem; border: 1px solid rgba(49, 51, 63, 0.2);
        height: 38.4px; font-size: 14px; font-weight: 400; text-align: center;
    }
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
            # Atualiza o estado e a planilha
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.success("Dados salvos no Google Sheets!")
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

    if len(periodo_sel) == 2:
        start_date, end_date = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_date) & (st.session_state.db['Data'].dt.date <= end_date) & (st.session_state.db['Unidade'].isin(u_sel)) & (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
        
        if not df_f.empty:
            resumo_grafico = df_f.groupby([pd.Grouper(key='Data', freq="ME"), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
            resumo_grafico.index = resumo_grafico.index.strftime('%m/%Y')
            st.bar_chart(resumo_grafico)

            # Exportação
            pdf_b = gerar_pdf_completo(df_f) 
            st.download_button("📥 Gerar PDF do Período", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)

    # --- 7. GESTÃO DE DADOS (EXCLUSÃO) ---
    st.divider()
    with st.expander("⚙️ Gerenciar Banco de Dados"):
        df_gestao = st.session_state.db.copy()
        df_gestao.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(
            df_gestao,
            column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)},
            disabled=["Data", "Unidade", "Tipo", "Peso (kg)"],
            hide_index=True, use_container_width=True
        )
        if st.button("🗑️ Confirmar Exclusão", type="primary"):
            indices_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices_manter].reset_index(drop=True)
            salvar_dados(st.session_state.db)
            st.rerun()

# --- RODAPÉ ---
st.write("---")
st.markdown('<div class="footer-container"><p class="idea-marcia">Idea of: Marcia Olsever</p><p class="footer-gabriola">Edison Duarte Filho®</p></div>', unsafe_allow_html=True)

