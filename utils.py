import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from datetime import datetime

# 🔐 Função para autenticar usuário
def autenticar_usuario(email, senha, db):
    try:
        usuarios_ref = db.collection("usuarios")
        query = usuarios_ref.where("usuario", "==", email.strip().lower()).stream()

        for doc in query:
            dados = doc.to_dict()
            if dados.get("senha", "").strip() == senha.strip():
                return True, {
                    "id": doc.id,
                    "email": dados.get("usuario"),
                    "usuario": dados.get("usuario"),  # 👈 Adicionado para uso no session_state
                    "id_time": dados.get("id_time"),
                    "nome_time": dados.get("nome_time")
                }
            else:
                print(f"[LOGIN] Senha incorreta para o usuário: {email}")
                return False, {}

        print(f"[LOGIN] Usuário não encontrado: {email}")
        return False, {}

    except Exception as e:
        print(f"[LOGIN] Erro na autenticação: {e}")
        return False, {}

# 🔐 Função para proteger páginas que exigem login
def verificar_login():
    if "id_time" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 💰 Função para registrar movimentações financeiras
def registrar_movimentacao(id_time, jogador, categoria, tipo, valor):
    try:
        db = firestore.client()
        registro = {
            "jogador": jogador,
            "categoria": categoria,
            "tipo": tipo,
            "valor": valor,
            "data": datetime.now(),
        }
        db.collection("times").document(id_time).collection("movimentacoes").add(registro)
    except Exception as e:
        print(f"[ERRO] Falha ao registrar movimentação: {e}")

