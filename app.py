import streamlit as st
import pandas as pd
from datetime import datetime
import io
import matplotlib.pyplot as plt # Nova biblioteca para o gráfico no PDF

try:
    from fpdf import FPDF
except ImportError:
    st.error("A biblioteca 'fpdf' não foi encontrada. Verifique o requirements.txt.")

# --- FUNÇÃO ATUALIZADA PARA INCLUIR GRÁFICO ---
def gerar_pdf(df, info_filtro, resumo_grafico):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio EcoLog".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Filtros: {info_filtro}".encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(5)

    # --- PARTE DO GRÁFICO NO PDF ---
    if not resumo_grafico.empty:
        # Criar o gráfico em memória
        fig, ax = plt.subplots(figsize=(6, 3))
        resumo_grafico.plot(kind='bar', ax=ax, color=['#2E7D32', '#81C784'])
        plt.title("Volume de Resíduos por Período")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Salvar gráfico em um buffer de imagem
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=150)
        img_buf.seek(0)
        
        # Inserir imagem no PDF
        pdf.image(img_buf, x=15, y=35, w=180)
        pdf.ln(65) # Espaço para não sobrepor a tabela à imagem
        plt.close(fig)

    # Tabela de Dados
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(50, 10, "Unidade", 1)
    pdf.cell(50, 10, "Tipo", 1)
    pdf.cell(30, 10, "Peso (kg)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(30, 10, row['Data'].strftime('%d/%m/%Y'), 1)
        pdf.cell(50, 10, row['Unidade'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(50, 10, row['Tipo'].encode('latin-1', 'replace').decode('latin-1'), 1)
        pdf.cell(30, 10, f"{row['Peso (kg)']:.2f}", 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# ... (Mantenha as seções 1, 2, 3 e 4 do seu código original) ...

# 5. GESTÃO E FILTROS (Mantenha como está)
# ... (Seu código de filtros aqui) ...

    if not df_f.empty:
        # --- PREPARAÇÃO DO GRÁFICO (Necessário para o PDF) ---
        p_graf = st.select_slider("Visualizar por:", options=["Semanal", "Mensal", "Anual"])
        freq = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
        
        # Geramos o resumo antes para passar para a função do PDF
        resumo = df_f.groupby([pd.Grouper(key='Data', freq=freq[p_graf]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
        resumo_visual = resumo.copy()
        resumo_visual.index = resumo_visual.index.strftime('%d/%m/%Y') if p_graf == "Semanal" else (resumo_visual.index.strftime('%m/%Y') if p_graf == "Mensal" else resumo_visual.index.strftime('%Y'))

        # EXPORTAÇÃO (Agora enviando o resumo para o PDF)
        col_r1, col_r2, col_r3 = st.columns(3)
        txt_f = f"{periodo[0].strftime('%d/%m/%y')} a {periodo[1].strftime('%d/%m/%y')}"
        
        # CHAMADA DO PDF COM O GRÁFICO
        pdf_b = gerar_pdf(df_f, txt_f, resumo_visual) 
        
        col_r1.download_button("📥 PDF com Gráfico", pdf_b, "relatorio_ecolog_grafico.pdf", "application/pdf")
        
        # WhatsApp e Email (Mantenha como está)
        # ...
        
        # EXIBIÇÃO DO GRÁFICO NA TELA
        st.divider()
        st.subheader("📊 Gráfico de Volume")
        st.bar_chart(resumo_visual)
