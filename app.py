import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import base64

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS (Regras Office + Estilo de Botões)
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; margin-bottom: 0.5em; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; margin-bottom: 0; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; margin-top: 0; line-height: 1.0; }
    .stButton > button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Função para Gerar PDF (Tratamento de caracteres especiais)
def gerar_pdf(df, unidade_filtro):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio EcoLog - Unidade: {unidade_filtro}", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(50, 10, "Unidade", 1)
    pdf.cell(50, 10, "Tipo", 1)
    pdf.cell(40, 10, "Peso (kg)", 1)
    pdf.ln()
    
    # Conteúdo
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(40, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, str(row['Unidade']), 1)
        pdf.cell(50, 10, str(row['Tipo']), 1)
        pdf.cell(40, 10, f"{row['Peso (kg)']:.2f}", 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

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

# 5. FILTROS E RELATÓRIOS
if not st.session_state.db.empty:
    st.divider()
    unidades_selecionadas = st.multiselect("Filtrar visualização por Unidade:", 
                                         options=["Angra dos Reis", "Guarujá"], 
                                         default=["Angra dos Reis", "Guarujá"])
    
    df_filtrado = st.session_state.db[st.session_state.db['Unidade'].isin(unidades_selecionadas)]

    if not df_filtrado.empty:
        # 6. BOTÕES DE EXPORTAÇÃO
        col_rel1, col_rel2, col_rel3 = st.columns(3)
        
        # Gerar PDF
        pdf_data = gerar_pdf(df_filtrado, "Filtro Selecionado")
        col_rel1.download_button(label="📥 Baixar PDF", 
                                 data=pdf_data, 
                                 file_name=f"Relatorio_Residuos_{datetime.now().strftime('%d_%m_%Y')}.pdf", 
                                 mime="application/pdf")
        
        # WhatsApp Link
        msg_whats = f"EcoLog: Relatorio de Residuos enviado em {datetime.now().strftime('%d/%m/%Y')}"
        link_whats = f"https://wa.me/?text={msg_whats}"
        col_rel2.markdown(f'<a href="{link_whats}" target="_blank"><button style="width:100%; height:38px; background-color:#25D366; color:white; border:none; border-radius:4px; cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
        
        # Email Link
        link_email = f"mailto:?subject=Relatorio de Residuos EcoLog&body=Segue resumo dos dados de gestao de residuos."
        col_rel3.markdown(f'<a href="{link_email}"><button style="width:100%; height:38px; background-color:#0078D4; color:white; border:none; border-radius:4px; cursor:pointer;">📧 E-mail</button></a>', unsafe_allow_html=True)

        # 7. GRÁFICOS
        st.subheader("📊 Análise de Volume")
        periodo = st.select_slider("Alterar Periodicidade:", options=["Semanal", "Mensal", "Anual"], value="Mensal")
        freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        resumo = df_filtrado.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        
        # Formatação Datas BR
        if periodo == "Semanal": resumo.index = resumo.index.strftime('Sem %W/%Y')
        elif periodo == "Mensal": resumo.index = resumo.index.strftime('%m/%Y')
        else: resumo.index = resumo.index.strftime('%Y')
        
        st.bar_chart(resumo)
        
        with st.expander("📄 Ver tabela de dados detalhada"):
            st.dataframe(df_filtrado.sort_values(by='Data', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado para as unidades selecionadas.")

else:
    st.info("Aguardando registros para gerar relatórios.")

# --- ASSINATURA FINAL ---
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
