import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import uuid

st.set_page_config(page_title="Cadastro de Usuário", layout="wide")

# 🔐 Inicializa Firebase
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

usuario = st.text_input("Usuário (e-mail)").strip().lower()
senha = st.text_input("Senha", type="password")
nome_time = st.text_input("Nome do Time").strip()
divisao = st.selectbox("Divisão", ["divisao_1"])  # Futuramente adicione mais divisões aqui

if st.button("Cadastrar"):
    if not usuario or not senha or not nome_time or not divisao:
        st.warning("Preencha todos os campos.")
    else:
        try:
            # Verifica se o usuário já existe
            existe = db.collection("usuarios").where("usuario", "==", usuario).get()
            if existe:
                st.error("Usuário já cadastrado.")
            else:
                # Cria ID único para o time
                id_time = str(uuid.uuid4())

                # Cria time com saldo inicial
                db.collection("times").document(id_time).set({
                    "nome": nome_time,
                    "saldo": 250_000_000,
                    "divisao": divisao
                })

                # Cadastra usuário vinculado ao time
                db.collection("usuarios").add({
                    "usuario": usuario,
                    "senha": senha,
                    "id_time": id_time,
                    "nome_time": nome_time,
                    "divisao": divisao
                })

                st.success("✅ Cadastro realizado com sucesso!")
                st.info("Você já pode acessar o sistema com seu login.")
        except Exception as e:
            st.error(f"Erro ao cadastrar: {e}")

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
