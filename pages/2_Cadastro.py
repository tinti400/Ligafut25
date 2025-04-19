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

# Formulário
usuario = st.text_input("Usuário (E-mail)").strip().lower()
senha = st.text_input("Senha", type="password")
nome_time = st.text_input("Nome do Time").strip()

if st.button("Cadastrar"):
    if usuario and senha and nome_time:
        try:
            # Verifica se já existe
            users = db.collection("usuarios").where("usuario", "==", usuario).stream()
            if any(users):
                st.warning("🚨 Já existe um usuário com esse e-mail.")
            else:
                id_time = str(uuid.uuid4())  # ID único do time

                # Cria o time
                db.collection("times").document(id_time).set({
                    "nome": nome_time,
                    "saldo": 250_000_000  # saldo inicial
                })

                # Cria o usuário
                db.collection("usuarios").add({
                    "usuario": usuario,
                    "senha": senha,
                    "id_time": id_time,
                    "nome_time": nome_time
                })

                st.success("✅ Cadastro realizado com sucesso!")
                st.info("Agora você pode fazer login na página inicial.")
        except Exception as e:
            st.error(f"Erro ao cadastrar: {e}")
    else:
        st.warning("Preencha todos os campos.")

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
