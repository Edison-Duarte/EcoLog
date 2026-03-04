import streamlit as st
import pandas as pd
from datetime import datetime
try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf' não foi encontrada. Verifique o arquivo requirements.txt no GitHub.")

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
    .stDownloadButton > button { width: 100% !important; background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# Função para Gerar PDF
def gerar_pdf(df, titulo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio Geral EcoLog".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 10, "Data", 1)
    pdf.cell(50, 10, "Unidade", 1)
    pdf.cell(50, 10, "Tipo", 1)
    pdf.cell(40, 10, "Peso (kg)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(35, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, row['Unidade'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(50, 10, row['Tipo'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(40, 10, str(row['Peso (kg)']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2 = st.columns(2)
    unidade_input = col1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_input = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    
    col3, col4 = st.columns(2)
    tipo_input = col3.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_input = col4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    if st.button("Salvar Dados"):
        if peso_input > 0:
            novo_registro = pd.DataFrame({
                'Data': [pd.to_datetime(data_input)],
                'Unidade': [unidade_input],
                'Tipo': [tipo_input],
                'Peso (kg)': [peso_input]
            })
            st.session_state.db = pd.concat([st.session_state.db, novo_registro], ignore_index=True)
            st.session_state.input_key += 1
            st.success("Registrado com sucesso!")
            st.rerun()

# 5. RELATÓRIOS E PDF (Sempre com todos os dados)
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📋 Relatórios e Exportação (Geral)")
    
    df_todos = st.session_state.db.copy()
    
    col_rel1, col_rel2, col_rel3 = st.columns(3)
    
    # PDF Geral
    pdf_output = gerar_pdf(df_todos, "Geral")
    col_rel1.download_button("📥 Baixar PDF Geral", data=pdf_output, file_name="relatorio_geral_ecolog.pdf", mime="application/pdf")
    
    # WhatsApp
    link_whats = f"https://wa.me/?text=EcoLog: Relatório geral atualizado em {datetime.now().strftime('%d/%m/%Y')}"
    col_rel2.markdown(f'<a href="{link_whats}" target="_blank"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
    
    # Email
    link_email = f"mailto:?subject=Relatorio de Residuos EcoLog&body=Segue resumo geral da gestao de residuos."
    col_rel3.markdown(f'<a href="{link_email}"><button style="width:100%;height:38px;border-radius:5px;border:1px solid #ccc;cursor:pointer;">📧 E-mail</button></a>', unsafe_allow_html=True)

    # 6. ANÁLISE GRÁFICA COM FILTRO EXCLUSIVO
    st.divider()
    st.subheader("📊 Análise de Volume por Unidade")
    
    unidades_grafico = st.multiselect("Filtrar visualização no Gráfico:", 
                                     options=["Angra dos Reis", "Guarujá"], 
                                     default=["Angra dos Reis", "Guarujá"])
    
    periodo = st.select_slider("Periodicidade do Gráfico:", options=["Semanal", "Mensal", "Anual"])
    
    # Aplica o filtro apenas para o gráfico
    df_grafico = df_todos[df_todos['Unidade'].isin(unidades_grafico)]
    
    if not df_grafico.empty:
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        resumo = df_grafico.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        if periodo == "Semanal": resumo.index = resumo.index.strftime('Sem %W/%Y')
        elif periodo == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        st.bar_chart(resumo)
    else:
        st.warning("Selecione ao menos uma unidade para visualizar o gráfico.")

    # Tabela detalhada (Sempre mostra tudo)
    with st.expander("📄 Ver Tabela Completa (Todos os dados)", expanded=False):
        st.dataframe(df_todos.sort_values(by='Data', ascending=False), use_container_width=True, hide_index=True)

# Assinatura
st.write("---")
st.markdown(
    """
    <div class="footer-container">
        <p class="idea-marcia">Idea of Marcia Olsever</p>
        <p class="footer-aharoni">Developed by:</p>
        <p class="footer-gabriola">Edison Duarte Filho®</p>
    </div>
    """, 
    unsafe_allow_html=True
)
