import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import pandas as pd

st.set_page_config(page_title="Finanças - LigaFut", layout="wide")

# 🔐 Inicializa Firebase com st.secrets (sem credenciais.json)
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

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.markdown(f"<h1 style='text-align: center;'>💼 Finanças do {nome_time}</h1><hr>", unsafe_allow_html=True)

# 🔄 Recupera movimentações
try:
    movs_ref = db.collection("times").document(id_time).collection("movimentacoes").stream()
    movimentacoes = [doc.to_dict() for doc in movs_ref]
except Exception as e:
    st.error(f"Erro ao buscar movimentações financeiras: {e}")
    st.stop()

# 📋 Exibição
if not movimentacoes:
    st.info("📭 Nenhuma movimentação financeira registrada.")
else:
    df = pd.DataFrame(movimentacoes)
    if "tipo" in df.columns and "jogador" in df.columns and "valor" in df.columns:
        df = df[["tipo", "jogador", "valor"]]
        df["valor"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
        df.columns = ["Tipo", "Jogador", "Valor"]
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Dados incompletos nas movimentações.")
