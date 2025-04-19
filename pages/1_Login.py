import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore

st.set_page_config(page_title="Login - LigaFut", page_icon="🔐", layout="centered")

# 🔐 Conecta Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

st.markdown("<h2 style='text-align: center;'>🏟️ LigaFut - Login</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ✅ SE JÁ ESTIVER LOGADO → mostra painel direto
if "usuario" in st.session_state and st.session_state["usuario"]:
    st.success(f"✅ Bem-vindo, {st.session_state['usuario']}!")

    st.markdown("### 🏁 Painel Inicial")
    st.info("Use o menu lateral para navegar entre as seções da LigaFut.")
    st.markdown("⚽ Você já pode acessar sua equipe, transferências, classificação e muito mais!")

    st.markdown("---")
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

    st.stop()

# ✅ FORMULÁRIO DE LOGIN
with st.form("login_form"):
    usuario = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    botao_login = st.form_submit_button("Entrar")

if botao_login:
    if usuario and senha:
        try:
            usuarios_ref = db.collection("usuarios").where("usuario", "==", usuario).where("senha", "==", senha).stream()
            usuario_encontrado = None
            for doc in usuarios_ref:
                usuario_encontrado = doc
                break

            if usuario_encontrado:
                dados = usuario_encontrado.to_dict()
                st.session_state["usuario"] = dados.get("usuario")
                st.session_state["usuario_id"] = usuario_encontrado.id

                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        except Exception as e:
            st.error(f"Erro durante o login: {e}")
    else:
        st.warning("Preencha todos os campos.")
