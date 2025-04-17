import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore

st.set_page_config(page_title="Painel do Usuário - LigaFut", layout="wide")

# 🔐 Inicializa Firebase via st.secrets (sem credenciais.json)
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

# ✅ Verifica se está logado
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

# 🔢 Busca saldo do time
try:
    time_ref = db.collection("times").document(id_time)
    dados_time = time_ref.get().to_dict()
    saldo = dados_time.get("saldo", 0)
except Exception as e:
    st.error(f"Erro ao buscar saldo do time: {e}")
    st.stop()

# 🎨 Painel principal
st.markdown(f"<h1 style='text-align: center;'>👤 Painel do Técnico</h1><hr>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### 🏷️ Time: **{nome_time}**")

with col2:
    st.markdown(f"### 💰 Saldo: **R$ {saldo:,.0f}**".replace(",", "."))

st.markdown("---")
st.markdown("### 🔎 Ações rápidas")

col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("📋 Ver Elenco"):
        st.switch_page("pages/4_Elenco.py")

with col_b:
    if st.button("🏪 Ir para o Mercado"):
        st.switch_page("pages/5_Mercado_Transferencias.py")

with col_c:
    if st.button("💼 Ver Finanças"):
        st.switch_page("pages/8_Financas.py")
