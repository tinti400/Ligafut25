import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="Administração de Usuários - LigaFut", layout="wide")

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

verificar_login()

usuario_id = st.session_state["usuario_id"]
email = st.session_state["usuario_logado"]

st.title("👤 Painel de Administração de Usuários")
st.markdown(f"**Usuário logado:** `{email}`")

st.markdown("---")

# Verifica se já é admin
admin_doc = db.collection("admins").document(usuario_id).get()

if admin_doc.exists:
    st.success("✅ Você já é administrador do sistema.")
else:
    if st.button("🔐 Tornar-se Administrador"):
        try:
            db.collection("admins").document(usuario_id).set({
                "email": email
            })
            st.success("Agora você é um administrador! Reinicie a página ou acesse o painel de admin.")
        except Exception as e:
            st.error(f"Erro ao registrar como admin: {e}")

