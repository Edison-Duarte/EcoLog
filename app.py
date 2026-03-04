import streamlit as st
import pandas as pd
from datetime import datetime
import io
import matplotlib.pyplot as plt

try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' não foi encontrada. Verifique o requirements.txt.")

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️", layout="wide")

# 2. Inicialização do Estado
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    .idea-marcia { font-family: 'serif'; font-size: 18px; color: #666; font-style: italic; }
    .footer-aharoni { font-family: 'sans-serif'; font-size: 16px; color: #333; font-weight: bold; }
    .footer-gabriola { font-family: 'serif'; font-size: 38px; color: #2E7D32; font-weight: bold; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# 4. Função para Gerar PDF com Gráfico (CORRIGIDA)
def gerar_pdf(df_filtrado, info_periodo, resumo_grafico):
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(190, 10, "Relatorio de Gestao de Residuos - EcoLog", ln=True, align='C')
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(190, 10, f"Periodo: {info_periodo}", ln=True, align='C')
    pdf.ln(5)

    # Inserindo o Gráfico no PDF
    if not resumo_grafico.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        resumo_grafico.plot(kind='bar', ax=ax, color=['#2E7D32', '#81C784'])
        plt.title("Volume por Categoria (kg)")
        plt.xticks(rotation=30)
        plt.tight_layout()
        
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=150)
        img_buf.seek(0)
        
        # Uso de PNG para evitar erro de leitura de cabeçalho
        pdf.image(img_buf, x=15, y=40, w=180) 
        
        plt.close(fig)
        pdf.ln(75) 

    # Tabela de Dados
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(35, 10, "Data", 1, 0, 'C', True)
    pdf.cell(55, 10, "Unidade", 1, 0, 'C', True)
    pdf.cell(55, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(45, 10, "Peso (kg)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", "", 10)
    for _, row in df_filtrado.iterrows():
        pdf.cell(35, 10, row['Data'].strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(55, 10, str(row['Unidade']), 1)
        pdf.cell(55, 10, str(row['Tipo']), 1)
        pdf.cell(45, 10, f"{row['Peso (kg)']:.2f}", 1, 1, 'C')
        
    # RETORNO CORRIGIDO PARA FPDF2
    return bytes(pdf.output())

st.title("♻️ EcoLog - Sistema de Gestão")

# 5. ÁREA DE INSERÇÃO DE DADOS
with st.expander("➕ Registrar Nova Coleta", expanded=True):
    c1, c2 = st.columns(2)
    unidade_in = c1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_in = c2.date_input("Data da Coleta", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    
    c3, c4 = st.columns(2)
    tipo_in = c3.selectbox("Categoria do Resíduo", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_in = c4.number_input("Peso Total (kg)", min_value=0.0, step=0.1, format="%.2f", key=f"p_{st.session_state.input_key}")
    
    b1, b2 = st.columns(2)
    if b1.button("💾 Salvar Registro", use_container_width=True, type="primary"):
        if peso_in > 0:
            novo_d = pd.DataFrame({'Data': [pd.to_datetime(data_in)], 'Unidade': [unidade_in], 'Tipo': [tipo_in], 'Peso (kg)': [peso_in]})
            st.session_state.db = pd.concat([st.session_state.db, novo_d], ignore_index=True)
            st.session_state.input_key += 1 
            st.success("Dados salvos!")
            st.rerun()
        else:
            st.warning("Insira um peso válido.")
            
    if b2.button("🧹 Limpar Campos", use_container_width=True):
        st.session_state.input_key += 1
        st.rerun()

# 6. GESTÃO E FILTROS
if not st.session_state.db.empty:
    st.divider()
    
    with st.expander("🗑️ Editar ou Excluir Lançamentos"):
        df_edit = st.session_state.db.copy()
        df_edit.insert(0, "Selecionar", False)
        sel_data = st.data_editor(df_edit, hide_index=True, use_container_width=True, key="editor_v1")
        
        col_ex1, col_ex2 = st.columns(2)
        if col_ex1.button("🗑️ Apagar Selecionados", use_container_width=True):
            indices = sel_data[sel_data["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices].reset_index(drop=True)
            st.rerun()
        if col_ex2.button("💥 Resetar Todo o Banco", use_container_width=True):
            st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
            st.rerun()

    st.subheader("🔍 Filtros e Exportação")
    f_c1, f_c2, f_c3 = st.columns([2, 1, 1])
    
    min_dt = st.session_state.db['Data'].min().date()
    max_dt = st.session_state.db['Data'].max().date()
    periodo_f = f_c1.date_input("Filtrar Período:", value=(min_dt, max_dt), format="DD/MM/YYYY")
    unidades_f = f_c2.multiselect("Unidades:", ["Angra dos Reis", "Guarujá"], default=["Angra dos Reis", "Guarujá"])
    categorias_f = f_c3.multiselect("Categorias:", ["Reciclável", "Orgânico"], default=["Reciclável", "Orgânico"])

    df_f = st.session_state.db.copy()
    if isinstance(periodo_f, tuple) and len(periodo_f) == 2:
        df_f = df_f[(df_f['Data'].dt.date >= periodo_f[0]) & (df_f['Data'].dt.date <= periodo_f[1])]
    df_f = df_f[df_f['Unidade'].isin(unidades_f)]
    df_f = df_f[df_f['Tipo'].isin(categorias_f)]

    if not df_f.empty:
        p_escolha = st.select_slider("Visualização Temporal:", options=["Semanal", "Mensal", "Anual"])
        f_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=f_map[p_escolha]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        resumo.index = resumo.index.strftime('%d/%m/%Y') if p_escolha == "Semanal" else (resumo.index.strftime('%m/%Y') if p_escolha == "Mensal" else resumo.index.strftime('%Y'))

        st.write("---")
        exp_c1, exp_c2, exp_c3 = st.columns(3)
        
        info_txt = f"{periodo_f[0].strftime('%d/%m/%y')} a {periodo_f[1].strftime('%d/%m/%y')}"
        
        # Geração de PDF
        pdf_bytes = gerar_pdf(df_f, info_txt, resumo)
        
        exp_c1.download_button("📥 Baixar PDF com Gráfico", pdf_bytes, "relatorio_ecolog.pdf", "application/pdf", use_container_width=True)
        
        link_w = f"https://wa.me/?text=EcoLog: Relatorio consolidado ({info_txt})"
        exp_c2.markdown(f'<a href="{link_w}" target="_blank"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
        
        link_e = f"mailto:?subject=Relatorio EcoLog&body=Seguem dados de gestao de residuos."
        exp_c3.markdown(f'<a href="{link_e}"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📧 E-mail</button></a>', unsafe_allow_html=True)

        st.subheader("📊 Visualização Gráfica")
        st.bar_chart(resumo)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

# Assinatura Final
st.markdown(f"""
    <div class="footer-container">
        <p class="idea-marcia">Idea of Marcia Olsever</p>
        <p class="footer-aharoni">Developed by:</p>
        <p class="footer-gabriola">Edison Duarte Filho®</p>
    </div>
    """, unsafe_allow_html=True)
