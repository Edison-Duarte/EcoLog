import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="centered")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
# Esta função utiliza as credenciais configuradas nos Secrets do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a planilha. ttl=0 garante que não use cache antigo
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
        
        # Garante que a coluna Data seja interpretada corretamente
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

def salvar_dados(df):
    try:
        # Converte datas para string antes de enviar para evitar erros de formato no Sheets
        df_save = df.copy()
        df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d')
        conn.update(data=df_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# Inicialização do estado da sessão
if 'db' not in st.session_state:
    st.session_state.db = carregar_dados()

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# --- 3. CSS CUSTOMIZADO (RODAPÉ COM ESPAÇAMENTO 1,5) ---
st.markdown("""
    <style>
    .footer-container { 
        text-align: center; 
        margin-top: 50px; 
        padding-top: 20px;
        line-height: 1.5; /* Espaçamento padrão Word 1,5 */
    }
    .idea-marcia { 
        font-family: 'Gabriola', serif; 
        font-size: 22px; 
        color: #666; 
        margin-bottom: 5px;
    }
    .footer-label { 
        font-family: 'Bodoni MT', serif; 
        font-size: 16px; 
        color: #444; 
        font-style: italic;
    }
    .footer-gabriola { 
        font-family: 'Gabriola', serif; 
        font-size: 42px; 
        color: #2E7D32; 
        font-weight: bold;
        margin-top: 10px;
    }
    
    /* Estilos dos botões permanecem os mesmos */
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
            novo = pd.DataFrame({
                'Data': [pd.to_datetime(data_input)], 
                'Unidade': [unidade], 
                'Tipo': [tipo], 
                'Peso (kg)': [peso]
            })
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            salvar_dados(st.session_state.db)
            st.success("Registro salvo com sucesso no Histórico!")
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.warning("O peso deve ser maior que zero.")

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

    # BARRA DESLIZANTE RESTAURADA
    p_graf = st.select_slider("Agrupar gráfico por:", options=["Semanal", "Mensal", "Anual"])
    
    if len(periodo_sel) == 2:
        start_date, end_date = periodo_sel
        mask = (st.session_state.db['Data'].dt.date >= start_date) & \
               (st.session_state.db['Data'].dt.date <= end_date) & \
               (st.session_state.db['Unidade'].isin(u_sel)) & \
               (st.session_state.db['Tipo'].isin(t_sel))
        df_f = st.session_state.db.loc[mask].copy()
    else:
        df_f = pd.DataFrame()

    if not df_f.empty:
        # Ordenamos os dados antes de agrupar
        df_f = df_f.sort_values('Data')
        
        # Mapeamento de Frequência (ME = Month End, essencial para o Pandas atual)
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        # Criamos o resumo para o gráfico
        resumo_grafico = df_f.groupby([pd.Grouper(key='Data', freq=freq_map[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        # FORMATAÇÃO DO EIXO X (Transformar em Texto para não desregular)
        if p_graf == "Semanal": 
            resumo_grafico.index = resumo_grafico.index.strftime('%d/%m/%Y')
        elif p_graf == "Mensal": 
            resumo_grafico.index = resumo_grafico.index.strftime('%b/%Y') # Ex: Jan/2024
        else: 
            resumo_grafico.index = resumo_grafico.index.strftime('%Y')
        
        # Exibe o gráfico de barras
        st.bar_chart(resumo_grafico)

        # --- EXPORTAÇÃO (Fica logo abaixo do gráfico) ---
        st.write("📤 **Exportar Seleção Atual:**")
        pdf_b = gerar_pdf_completo(df_f) 
        st.download_button("📥 Gerar PDF do Período", pdf_b, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)
    # --- 7. GESTÃO E EXCLUSÃO ---
    st.divider()
    with st.expander("⚙️ Gerenciar Histórico Permanente"):
        df_gestao = st.session_state.db.copy()
        df_gestao.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(
            df_gestao,
            column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)},
            disabled=["Data", "Unidade", "Tipo", "Peso (kg)"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("🗑️ Confirmar Exclusão Selecionados", type="primary"):
            indices_para_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices_para_manter].reset_index(drop=True)
            salvar_dados(st.session_state.db)
            st.rerun()
else:
    st.info("O histórico está vazio. Insira dados para visualizar os relatórios.")

# --- 8. RODAPÉ ---
st.write("---")
st.markdown("""
    <div class="footer-container">
        <p class="idea-marcia">Idea of: Marcia Olsever</p>
        <p class="footer-label">Developed by:</p>
        <p class="footer-gabriola">Edison Duarte Filho®</p>
    </div>
""", unsafe_allow_html=True)


