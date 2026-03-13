# --- 5. INTERFACE DE ENTRADA COM BLOQUEIO DE ACESSO ---
st.title("♻️ EcoLog - Gestão de Resíduos")

SENHAS_UNIDADES = {
    "Guarujá": "GUICS",
    "Angra dos Reis": "ARICS",
    "Ilha Bela": "IBICS",
    "São Paulo": "SPICS"
}

# 1. Primeiro, o usuário escolhe a unidade
u_login = st.selectbox("Selecione sua Unidade para acessar:", ["Selecione..."] + list(SENHAS_UNIDADES.keys()))

if u_login != "Selecione...":
    # 2. Solicita a senha ANTES de mostrar qualquer campo de dado
    senha_acesso = st.text_input(f"Digite a senha de acesso para {u_login}:", type="password")

    if senha_acesso == SENHAS_UNIDADES[u_login]:
        st.success(f"🔓 Acesso liberado para {u_login}")
        
        # 3. Só agora o formulário de inserção aparece
        with st.expander("➕ Registrar Nova Coleta", expanded=True):
            c1, c2 = st.columns(2)
            # A unidade já fica travada na que ele logou
            st.info(f"Registrando para: **{u_login}**")
            data_reg = c1.date_input("Data da Coleta", datetime.now(), format="DD/MM/YYYY", key=f"d{st.session_state.input_key}")
            tipo_reg = c2.selectbox("Tipo de Resíduo", ["Reciclável", "Orgânico"], key=f"t{st.session_state.input_key}")
            
            peso_reg = st.number_input("Peso (kg)", min_value=0.0, step=0.1, key=f"p{st.session_state.input_key}")
            
            if st.button("💾Confirmar e Salvar no Banco", use_container_width=True):
                if peso_reg > 0:
                    novo = pd.DataFrame({
                        'Data': [pd.to_datetime(data_reg)], 
                        'Unidade': [u_login], 
                        'Tipo': [tipo_reg], 
                        'Peso (kg)': [peso_reg]
                    })
                    st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
                    salvar_dados(st.session_state.db)
                    st.success("Dados enviados com sucesso!")
                    st.session_state.input_key += 1
                    st.rerun()
                else:
                    st.warning("Por favor, insira o peso para salvar.")
    elif senha_acesso != "":
        st.error("⚠️ Senha incorreta. Verifique com o administrador.")
else:
    st.info("Aguardando seleção de unidade para liberar o registro.")
