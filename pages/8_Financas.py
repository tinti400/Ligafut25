import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import pandas as pd

st.set_page_config(page_title="Finanças - LigaFut", layout="wide")

# 🔐 Inicializa Firebase com st.secrets
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

# 💰 Exibe o saldo atual
try:
    time_doc = db.collection("times").document(id_time).get()
    saldo = time_doc.to_dict().get("saldo", 0)
    saldo_formatado = f"R$ {saldo:,.0f}".replace(",", ".")
    st.markdown(f"<h3 style='text-align: center;'>📦 Caixa Atual: {saldo_formatado}</h3><br>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro ao buscar saldo: {e}")
    st.stop()

# 📋 Recupera movimentações
try:
    movs_ref = db.collection("times").document(id_time).collection("movimentacoes").stream()
    movimentacoes = [doc.to_dict() for doc in movs_ref]
except Exception as e:
    st.error(f"Erro ao buscar movimentações financeiras: {e}")
    st.stop()

# 📊 Exibe a tabela de movimentações
if not movimentacoes:
    st.info("📭 Nenhuma movimentação financeira registrada.")
else:
    df = pd.DataFrame(movimentacoes)
    if all(col in df.columns for col in ["tipo", "jogador", "valor", "origem"]):
        df["valor"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
        df = df[["tipo", "origem", "jogador", "valor"]]
        df.columns = ["Tipo", "Origem", "Jogador", "Valor"]
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Existem movimentações com dados incompletos.")
