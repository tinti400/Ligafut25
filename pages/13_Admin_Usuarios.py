import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="Admin Usuários - LigaFut", layout="centered")

# Inicializa Firebase
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

# Verifica login
verificar_login()

usuario_logado = st.session_state.get("usuario_logado", "")
usuario_id = st.session_state.get("usuario_id", "")

# Verifica se o usuário logado é admin
admin_doc = db.collection("admins").document(usuario_id).get()
eh_admin = admin_doc.exists

st.title("👥 Gerenciar Administradores")

if eh_admin:
    st.success(f"Você está logado como ADMIN: `{usuario_logado}`")

    st.markdown("### ➕ Adicionar novo administrador")
    novo_email = st.text_input("E-mail do usuário a ser promovido")

    if st.button("✅ Tornar administrador"):
        if novo_email:
            try:
                db.collection("admins").document(novo_email).set({"email": novo_email})
                st.success(f"Usuário `{novo_email}` agora é um administrador!")
            except Exception as e:
                st.error(f"Erro ao adicionar administrador: {e}")
        else:
            st.warning("Informe um e-mail válido.")
else:
    st.error("❌ Você não tem permissão para acessar esta página. Apenas administradores.")
