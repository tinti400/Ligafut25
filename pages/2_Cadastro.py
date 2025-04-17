import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import uuid

st.set_page_config(page_title="Cadastro de Usuário", layout="wide")

# 🔐 Inicializar Firebase com secrets seguros (compatível com Cloud)
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = gc_firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

st.title("📝 Cadastro de Usuário")

usuario = st.text_input("Usuário (E-mail)").strip().lower()
senha = st.text_input("Senha", type="password")

if st.button("Cadastrar"):
    if usuario and senha:
        usuarios_ref = db.collection("usuarios")

        docs = usuarios_ref.where("usuario", "==", usuario).stream()
        usuario_existente = any(True for _ in docs)

        if usuario_existente:
            st.warning("Este usuário já está cadastrado.")
        else:
            novo_id = str(uuid.uuid4())
            usuarios_ref.document(novo_id).set({
                "usuario": usuario,
                "senha": senha
            })
            st.success("✅ Usuário cadastrado com sucesso!")
    else:
        st.warning("Preencha todos os campos para se cadastrar.")
