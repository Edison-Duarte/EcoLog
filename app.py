import streamlit as st
import pandas as pd
from datetime import datetime
import io

try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf2' não foi encontrada. Verifique o requirements.txt.")

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado (Os registros ficam acumulados aqui)
if 'db' not in st.session_state:
    # Caso queira que ele abra VAZIO mas mostre o gráfico assim que inserir o 1º:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Unidade', 'Tipo', 'Peso (kg)'])
    
    # OPCIONAL: Se quiser que ele já abra com dados de exemplo para mostrar o gráfico:
    # st.session_state.db = pd.DataFrame({
    #     'Data': [pd.to_datetime('2024-01-01')],
    #     'Unidade': ['Angra dos Reis'],
    #     'Tipo': ['Reciclável'],
    #     'Peso (kg)': [0.0]
    # })

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS
st.markdown("""
    <style>
    .footer-container { text-align: center; margin-top: 50px; }
    .idea-marcia { font-family: 'Gabriola', serif; font-size: 20px; color: #666; margin-bottom: 0.5em; line-height: 1.0; }
    .footer-aharoni { font-family: 'Aharoni', sans-serif; font-size: 18px; color: #333; margin-bottom: 0; line-height: 1.0; }
    .footer-gabriola { font-family: 'Gabriola', serif; font-size: 42px; color: #2E7D32; font-weight: bold; margin-top: 0; line-height: 1.0; }
    .btn-envio { width:100%; height:38px; border-radius:5px; border:1px solid #ccc; cursor:pointer; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# 4. Função para Gerar PDF
def gerar_pdf(df, info_filtro):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "EcoLog - Gestao de Residuos".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Relatorio de Registros - Filtros: {info_filtro}".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 10, "Data", 1, 0, 'C', True)
    pdf.cell(50, 10, "Unidade", 1, 0, 'C', True)
    pdf.cell(50, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(30, 10, "Peso (kg)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", "", 10)
    df_sorted = df.sort_values(by='Data', ascending=False)
    for _, row in df_sorted.iterrows():
        pdf.cell(30, 10, row['Data'].strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(50, 10, str(row['Unidade']).encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(50, 10, str(row['Tipo']).encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(30, 10, f"{row['Peso (kg)']:.2f}", 1, 1, 'C')
    return bytes(pdf.output())

# Título Principal
st.title("♻️ EcoLog - Gestão de Resíduos")

# 5. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2 = st.columns(2)
    unidade_in = col1.selectbox("Unidade", ["Angra dos Reis", "Guarujá"], key=f"u_{st.session_state.input_key}")
    data_in = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    col3, col4 = st.columns(2)
    tipo_in = col3.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_in = col4.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    if st.button("Salvar Registro", use_container_width=True):
        if peso_in > 0:
            novo = pd.DataFrame({'Data': [pd.to_datetime(data_in)], 'Unidade': [unidade_in], 'Tipo': [tipo_in], 'Peso (kg)': [peso_in]})
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            st.session_state.input_key += 1
            st.rerun()

# 6. GRÁFICO E RELATÓRIO (MOSTRAR SEMPRE QUE HOUVER DADOS)
if not st.session_state.db.empty:
    st.divider()
    
    # Filtros rápidos no topo para o gráfico abrir certo
    st.subheader("📊 Consolidado de Resíduos")
    
    df_f = st.session_state.db.copy()
    
    # Gráfico de Barras Principal
    resumo = df_f.groupby([pd.Grouper(key='Data', freq='D'), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    resumo.index = resumo.index.strftime('%d/%m/%Y')
    st.bar_chart(resumo)

    # Botões de Envio (Lado a lado com o gráfico)
    col_r1, col_r2, col_r3 = st.columns(3)
    pdf_b = gerar_pdf(df_f, "Geral")
    col_r1.download_button("📥 Baixar PDF", pdf_b, "relatorio.pdf", "application/pdf", use_container_width=True)
    
    link_w = f"https://wa.me/?text=EcoLog: Total de {df_f['Peso (kg)'].sum():.2f}kg coletados."
    col_r2.markdown(f'<a href="{link_w}" target="_blank"><button class="btn-envio">📲 WhatsApp</button></a>', unsafe_allow_html=True)
    
    link_e = f"mailto:?subject=EcoLog&body=Relatorio de residuos."
    col_r3.markdown(f'<a href="{link_e}"><button class="btn-envio">📧 E-mail</button></a>', unsafe_allow_html=True)

    # 7. GESTÃO E EXCLUSÃO (Fica no final)
    with st.expander("⚙️ Gerenciar Registros / Filtros Detalhados"):
        st.write("Edite ou exclua registros abaixo:")
        df_edit = st.session_state.db.copy()
        df_edit.insert(0, "Selecionar", False)
        tabela_editada = st.data_editor(df_edit, column_config={"Selecionar": st.column_config.CheckboxColumn(required=True)}, disabled=["Data", "Unidade", "Tipo", "Peso (kg)"], hide_index=True, use_container_width=True, key="editor_exclusao")
        
        if st.button("🗑️ Apagar Selecionados", use_container_width=True):
            indices_manter = tabela_editada[tabela_editada["Selecionar"] == False].index
            st.session_state.db = st.session_state.db.iloc[indices_manter].reset_index(drop=True)
            st.rerun()
            
else:
    st.info("O gráfico aparecerá aqui assim que você salvar o primeiro registro.")

# Assinatura
st.write("---")
st.markdown("""<div class="footer-container">
    <p class="idea-marcia">Idea of Marcia Olsever</p>
    <p class="footer-aharoni">Developed by:</p>
    <p class="footer-gabriola">Edison Duarte Filho®</p>
</div>""", unsafe_allow_html=True)
