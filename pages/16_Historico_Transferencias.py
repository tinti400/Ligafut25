import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="Histórico de Transferências", layout="wide")

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

# ✅ Verifica login
verificar_login()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📜 Histórico de Transferências")

# 🔎 Buscar movimentações financeiras do time logado
mov_ref = db.collection("times").document(id_time).collection("movimentacoes") \
            .order_by("data", direction=firestore.Query.DESCENDING).stream()

movimentacoes = [doc.to_dict() for doc in mov_ref]

if not movimentacoes:
    st.info("Nenhuma movimentação registrada.")
else:
    for mov in movimentacoes:
        jogador = mov.get("jogador", "Desconhecido")
        categoria = mov.get("categoria", "N/A")
        tipo = mov.get("tipo", "N/A")
        valor = mov.get("valor", 0)
        data = mov.get("data", None)

        if isinstance(data, datetime):
            data_str = data.strftime('%d/%m/%Y %H:%M')
        else:
            data_str = "Data não disponível"

        st.markdown("---")
        st.markdown(f"**👤 Jogador:** {jogador}")
        st.markdown(f"**📂 Categoria:** {categoria}")
        st.markdown(f"**💬 Tipo:** {tipo}")
        st.markdown(f"**💰 Valor:** R$ {valor:,.0f}".replace(",", "."))
        st.markdown(f"**📅 Data:** {data_str}")
