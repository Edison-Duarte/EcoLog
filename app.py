import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuração da página
st.set_page_config(page_title="EcoLog - Gestão de Resíduos", page_icon="♻️")

# 2. Inicialização do Estado (Base de Dados e Chave de Reset)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 3. Estilização CSS (Regras de Espaçamento Misto: 1.5 e 1.0)
st.markdown("""
    <style>
    .footer-container { 
        text-align: center; 
        margin-top: 50px; 
    }
    .idea-marcia { 
        font-family: 'Gabriola', serif; 
        font-size: 20px; 
        color: #666; 
        margin-bottom: 0.5em; /* Gera o efeito de 1.5 em relação à linha de baixo */
        line-height: 1.0;
    }
    .footer-aharoni { 
        font-family: 'Aharoni', sans-serif; 
        font-size: 18px; 
        color: #333; 
        margin-bottom: 0; 
        line-height: 1.0; /* Espaçamento simples */
    }
    .footer-gabriola { 
        font-family: 'Gabriola', serif; 
        font-size: 42px; 
        color: #2E7D32; 
        font-weight: bold; 
        margin-top: 0; 
        line-height: 1.0; /* Espaçamento simples */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("♻️ Gestão de Resíduos Empresariais")

# 4. ENTRADA DE DADOS
with st.expander("➕ Registrar Coleta de Resíduos", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    data_input = col1.date_input("Data", datetime.now(), format="DD/MM/YYYY", key=f"d_{st.session_state.input_key}")
    tipo_input = col2.selectbox("Categoria", ["Reciclável", "Orgânico"], key=f"t_{st.session_state.input_key}")
    peso_input = col3.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p_{st.session_state.input_key}")
    
    if st.button("Salvar Dados"):
        if peso_input > 0:
            novo_registro = pd.DataFrame({
                'Data': [pd.to_datetime(data_input)],
                'Tipo': [tipo_input],
                'Peso (kg)': [peso_input]
            })
            st.session_state.db = pd.concat([st.session_state.db, novo_registro], ignore_index=True)
            st.session_state.input_key += 1
            st.success("Registrado com sucesso!")
            st.rerun()
        else:
            st.warning("Por favor, insira um peso válido.")

# 5. GESTÃO E EXCLUSÃO DE DADOS
if not st.session_state.db.empty:
    st.divider()
    st.subheader("📋 Gestão de Registros")
    
    df_exibicao = st.session_state.db.copy()
    df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
    df_exibicao.insert(0, "Selecionar", False)
    
    edited_df = st.data_editor(
        df_exibicao,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(required=True),
            "Data": st.column_config.TextColumn("Data (BR)")
        },
        disabled=["Data", "Tipo", "Peso (kg)"],
        hide_index=True,
        use_container_width=True
    )

    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("🗑️ Apagar Selecionados"):
        indices_para_manter = edited_df[edited_df["Selecionar"] == False].index
        st.session_state.db = st.session_state.db.iloc[indices_para_manter].reset_index(drop=True)
        st.rerun()

    if col_btn2.button("💥 Limpar Tudo"):
        st.session_state.db = pd.DataFrame(columns=['Data', 'Tipo', 'Peso (kg)'])
        st.rerun()

    # 6. VISUALIZAÇÃO DOS GRÁFICOS
    st.divider()
    periodo = st.select_slider("Filtro de Periodicidade:", options=["Semanal", "Mensal", "Anual"])
    
    df_plot = st.session_state.db.copy()
    freq_map = {"Semanal": "W", "Mensal": "ME", "Anual": "YE"}
    
    resumo = df_plot.groupby([pd.Grouper(key='Data', freq=freq_map[periodo]), 'Tipo'])['Peso (kg)'].sum().unstack().fillna(0)
    
    if periodo == "Semanal":
        resumo.index = resumo.index.strftime('Sem %W/%Y')
    elif periodo == "Mensal":
        resumo.index = resumo.index.strftime('%m/%Y')
    else:
        resumo.index = resumo.index.strftime('%Y')

    st.subheader(f"📊 Volume Total {periodo}")
    st.bar_chart(resumo)
    
else:
    st.info("O banco de dados está vazio.")

# --- ASSINATURA FINAL (REGRAS OFFICE MISTAS) ---
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
