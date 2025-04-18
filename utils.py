import streamlit as st
from datetime import datetime
from google.cloud import firestore

# 🔐 Verifica se o usuário está logado
def verificar_login():
    if "id_time" not in st.session_state or "usuario_logado" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 👑 Verifica se o usuário logado é admin (baseado no campo 'usuario_logado')
def is_admin():
    try:
        db = st.session_state["firebase"]
        usuario = st.session_state.get("usuario_logado", "")
        if not usuario:
            return False
        admin_ref = db.collection("admins").document(usuario)
        return admin_ref.get().exists
    except Exception as e:
        print(f"[ADMIN CHECK ERRO] {e}")
        return False

# 💰 Registra movimentações financeiras no Firestore
def registrar_movimentacao(id_time, jogador, categoria, tipo, valor):
    try:
        db = st.session_state["firebase"]
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
