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
nome_time = st.text_input("Nome do Time").strip()
divisao = st.selectbox("Divisão", ["divisao_1"])  # Para o futuro: adicionar outras divisões

if st.button("Cadastrar"):
    if usuario and senha and nome_time:
        try:
            # Cria documento na coleção 'times'
            time_ref = db.collection("times").document()
            time_ref.set({
                "nome": nome_time,
                "saldo": 250_000_000,
                "divisao": divisao
            })

            # Cadastra usuário e vincula ao time
            db.collection("usuarios").add({
                "usuario": usuario,
                "senha": senha,
                "id_time": time_ref.id,
                "nome_time": nome_time,
                "divisao": divisao
            })

            st.success("✅ Usuário e time cadastrados com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao cadastrar: {e}")
    else:
        st.warning("Preencha todos os campos.")
