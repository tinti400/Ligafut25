import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="Administração de Usuários", layout="wide")

# 🔐 Inicializa Firebase com st.secrets
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

# Verifica se está logado
verificar_login()

st.title("👥 Administração de Usuários")

# Formulário para novo usuário
with st.expander("➕ Adicionar Novo Usuário"):
    usuario = st.text_input("Usuário (e-mail)").strip().lower()
    senha = st.text_input("Senha", type="password")
    id_time = st.text_input("ID do Time")
    nome_time = st.text_input("Nome do Time")

    if st.button("✅ Cadastrar Usuário"):
        if usuario and senha and id_time and nome_time:
            usuarios_ref = db.collection("usuarios")
            existente = list(usuarios_ref.where("usuario", "==", usuario).stream())

            if existente:
                st.warning("⚠️ Este usuário já está cadastrado.")
            else:
                usuarios_ref.add({
                    "usuario": usuario,
                    "senha": senha,
                    "id_time": id_time,
                    "nome_time": nome_time
                })
                st.success("Usuário cadastrado com sucesso!")
                st.rerun()
        else:
            st.warning("Preencha todos os campos.")

st.markdown("---")

# Lista de usuários cadastrados
st.subheader("📋 Lista de Usuários Cadastrados")
usuarios = db.collection("usuarios").stream()

for doc in usuarios:
    dados = doc.to_dict()
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        st.text(f"📧 {dados.get('usuario')}")
    with col2:
        st.text(f"🧾 Time: {dados.get('nome_time')}")
    with col3:
        st.text(f"🔢 ID Time: {dados.get('id_time')}")
    with col4:
        if st.button("🗑️ Excluir", key=f"excluir_{doc.id}"):
            db.collection("usuarios").document(doc.id).delete()
            st.success("Usuário excluído com sucesso!")
            st.rerun()
