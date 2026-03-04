import streamlit as st
import pandas as pd
from datetime import datetime
try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf' não foi encontrada no servidor. Verifique o requirements.txt.")

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

# Função para Gerar PDF
def gerar_pdf(df, info_filtro):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio EcoLog".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Filtros aplicados: {info_filtro}".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(45, 10, "Unidade", 1)
    pdf.cell(45, 10, "Tipo", 1)
    pdf.cell(30, 10, "Peso (kg)", 1)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(30, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(45, 10, row['Unidade'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(45, 10, row['Tipo'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(30, 10, f"{row['Peso (kg)']:.2f}", 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2 = st.columns(2)
    unidade_in = col1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_in = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    
    col3, col4 = st.columns(2)
    tipo_in = col3.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_in = col4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    if st.button("Salvar Dados"):
        if peso_in > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_in)], 'Unidade': [unidade_in], 'Tipo': [tipo_in], 'Peso (kg)': [peso_in]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            st.session_state.input_key += 1
            st.success("Salvo!")
            st.rerun()

# 5. FILTROS AVANÇADOS
if not st.session_state.db.empty:
    st.divider()
    st.subheader("🔍 Filtros de Relatório")
    
    # Linha 1 de Filtros: Datas
    min_d, max_d = st.session_state.db['Data'].min().date(), st.session_state.db['Data'].max().date()
    periodo = st.date_input("Período:", value=(min_d, max_d), format="DD/MM/YYYY")
    
    # Linha 2 de Filtros: Unidade e Categoria
    f_col1, f_col2 = st.columns(2)
    unidades_f = f_col1.multiselect("Unidades:", ["Angra dos Reis", "Guarujá"], default=["Angra dos Reis", "Guarujá"])
    categorias_f = f_col2.multiselect("Categorias:", ["Reciclável", "Orgânico"], default=["Reciclável", "Orgânico"])

    # Aplicando Lógica de Filtro
    df_f = st.session_state.db.copy()
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_f = df_f[(df_f['Data'].dt.date >= periodo[0]) & (df_f['Data'].dt.date <= periodo[1])]
    df_f = df_f[df_f['Unidade'].isin(unidades_f)]
    df_f = df_f[df_f['Tipo'].isin(categorias_f)]

    if not df_f.empty:
        # 6. EXPORTAÇÃO
        col_r1, col_r2, col_r3 = st.columns(3)
        txt_filtro = f"{periodo[0].strftime('%d/%m/%y')} a {periodo[1].strftime('%d/%m/%y')}"
        
        pdf_bytes = gerar_pdf(df_f, txt_filtro)
        col_r1.download_button("📥 PDF Filtrado", pdf_bytes, "relatorio_ecolog.pdf", "application/pdf")
        
        link_w = f"https://wa.me/?text=EcoLog: Relatório disponível ({txt_filtro})"
        col_r2.markdown(f'<a href="{link_w}" target="_blank"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
        
        link_e = f"mailto:?subject=Relatorio EcoLog&body=Segue resumo de residuos."
        col_r3.markdown(f'<a href="{link_e}"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📧 E-mail</button></a>', unsafe_allow_html=True)

        # 7. GRÁFICOS E TABELA
        st.divider()
        st.subheader("📊 Gráfico de Volume")
        p_grafico = st.select_slider("Visualizar por:", options=["Semanal", "Mensal", "Anual"])
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq_map[p_grafico]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        if p_grafico == "Semanal": resumo.index = resumo.index.strftime('Sem %W/%Y')
        elif p_grafico == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        st.bar_chart(resumo)
        with st.expander("📄 Ver Tabela Filtrada"):
            st.dataframe(df_f.sort_values(by='Data', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado para estes filtros.")

# Assinatura
st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
