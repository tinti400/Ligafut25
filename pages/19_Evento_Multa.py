import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
import datetime

st.set_page_config(page_title="🚨 Evento de Multa", layout="wide")

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

# ✅ Verifica se o usuário está logado
verificar_login()

# Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"## 🛡️ Proteja seus jogadores - {nome_time}")

# Busca elenco do time logado
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]

# Busca jogadores protegidos no último evento
protecao_ref = db.collection("eventos_multa").document("protecoes").collection(id_time).stream()
protegidos_anteriores = [doc.id for doc in protecao_ref]

# Interface para proteger até 4 jogadores
jogadores_disponiveis = [j["nome"] for j in elenco if j["nome"] not in protegidos_anteriores]
selecionados = st.multiselect("Escolha até 4 jogadores para proteger:", jogadores_disponiveis, max_selections=4)

if st.button("✅ Confirmar Proteção"):
    if not selecionados:
        st.warning("Selecione pelo menos um jogador.")
        st.stop()

    try:
        protecoes_path = db.collection("eventos_multa").document("protecoes").collection(id_time)
        # Apaga proteções anteriores
        for doc in db.collection("eventos_multa").document("protecoes").collection(id_time).stream():
            protecoes_path.document(doc.id).delete()

        # Salva novas proteções
        for nome in selecionados:
            protecoes_path.document(nome).set({
                "nome": nome,
                "data": datetime.datetime.now()
            })

        st.success("🎯 Jogadores protegidos com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao proteger jogadores: {e}")
