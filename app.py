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
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS (Regras Office 1.0 e 1.5)
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; margin-bottom: 0.5em; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; margin-bottom: 0; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; margin-top: 0; line-height: 1.0; }
    </style>
    """, unsafe_allow_html=True)

# 4. Função para Gerar PDF (Com correção técnica de compatibilidade)
def gerar_pdf(df, info_filtro, resumo_grafico):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio EcoLog".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Filtros: {info_filtro}".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(5)

    # Inserção do Gráfico no PDF
    if not resumo_grafico.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        resumo_grafico.plot(kind='bar', ax=ax, color=['#2E7D32', '#81C784'])
        plt.title("Volume de Residuos")
        plt.tight_layout()
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=120)
        img_buf.seek(0)
        pdf.image(img_buf, x=15, y=35, w=180, type='PNG')
        plt.close(fig)
        pdf.ln(65)

    # Tabela
    pdf.set_font("Arial", "B", 10)
    for col, width in zip(["Data", "Unidade", "Tipo", "Peso (kg)"], [30, 50, 50, 30]):
        pdf.cell(width, 10, col, 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(30, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, str(row['Unidade']).encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(50, 10, str(row['Tipo']).encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(30, 10, f"{row['Peso (kg)']:.2f}", 1)
        pdf.ln()
    return bytes(pdf.output())

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS (Visual Original)
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2 = st.columns(2)
    unidade_in = col1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_in = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    col3, col4 = st.columns(2)
    tipo_in = col3.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_in = col4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    # Botões Lado a Lado
    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("Salvar Registro", use_container_width=True):
        if peso_in > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_in)], 'Unidade': [unidade_in], 'Tipo': [tipo_in], 'Peso (kg)': [peso_in]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            st.session_state.input_key += 1
            st.success("Registro Salvo!")
            st.rerun()

    if btn_col2.button("Limpar Campos", use_container_width=True):
        st.session_state.input_key += 1
        st.rerun()

# 5. GESTÃO E EXCLUSÃO
if not st.session_state.db.empty:
    st.divider()
    with st.expander("🗑️ Gestão e Exclusão de Registros"):
        df_edit = st.session_state.db.copy()
        df_edit.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(
            df_edit,
            column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)},
            disabled=["Data", "Unidade", "Tipo", "Peso (kg)"],
            hide_index=True,
            use_container_width=True,
            key="editor_exclusao"
        )
        c1, c2 = st.columns(2)
        if c1.button("🗑️ Apagar Selecionados", use_container_width=True):
            indices_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices_manter].reset_index(drop=True)
            st.rerun()
        if c2.button("💥 Limpar Tudo", use_container_width=True):
            st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
            st.rerun()

    # 6. FILTROS AVANÇADOS
    st.subheader("🔍 Filtros de Relatório")
    min_d, max_d = st.session_state.db['Data'].min().date(), st.session_state.db['Data'].max().date()
    periodo = st.date_input("Período:", value=(min_d, max_d), format="DD/MM/YYYY")
    f_col1, f_col2 = st.columns(2)
    unidades_f = f_col1.multiselect("Unidades:", ["Angra dos Reis", "Guarujá"], default=["Angra dos Reis", "Guarujá"])
    categorias_f = f_col2.multiselect("Categorias:", ["Reciclável", "Orgânico"], default=["Reciclável", "Orgânico"])

    df_f = st.session_state.db.copy()
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_f = df_f[(df_f['Data'].dt.date >= periodo[0]) & (df_f['Data'].dt.date <= periodo[1])]
    df_f = df_f[df_f['Unidade'].isin(unidades_f)]
    df_f = df_f[df_f['Tipo'].isin(categorias_f)]

    if not df_f.empty:
        # EXPORTAÇÃO
        col_r1, col_r2, col_r3 = st.columns(3)
        txt_f = f"{periodo[0].strftime('%d/%m/%y')} a {periodo[1].strftime('%d/%m/%y')}"
        
        # Preparação do Resumo para o PDF
        p_graf = st.select_slider("Visualizar por:", options=["Semanal", "Mensal", "Anual"])
        freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        resumo_vis = resumo.copy()
        resumo_vis.index = resumo_vis.index.strftime('%d/%m/%Y') if p_graf == "Semanal" else (resumo_vis.index.strftime('%m/%Y') if p_graf == "Mensal" else resumo_vis.index.strftime('%Y'))

        pdf_b = gerar_pdf(df_f, txt_f, resumo_vis)
        col_r1.download_button("📥 PDF Filtrado", pdf_b, "relatorio_ecolog.pdf", "application/pdf")
        
        link_w = f"https://wa.me/?text=Relatorio EcoLog ({txt_f})"
        col_r2.markdown(f'<a href="{link_w}" target="_blank"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
        link_e = f"mailto:?subject=Relatorio EcoLog&body=Segue resumo."
        col_r3.markdown(f'<a href="{link_e}"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📧 E-mail</button></a>', unsafe_allow_html=True)

        # GRÁFICO NA TELA
        st.divider()
        st.subheader("📊 Gráfico de Volume")
        st.bar_chart(resumo_vis)
    else:
        st.warning("Nenhum dado para estes filtros.")

# Assinatura
st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
