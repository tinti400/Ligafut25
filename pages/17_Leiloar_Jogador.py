import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
from datetime import datetime, timedelta
from utils import verificar_login

st.set_page_config(page_title="Leiloar Jogador", layout="wide")

# 🔐 Inicializa Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = gc_firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

verificar_login()

id_time = st.session_state.get("id_time")
nome_time = st.session_state.get("nome_time")

st.markdown(f"<h2 style='text-align:center;'>🎦 Leiloar Jogador - {nome_time}</h2><hr>", unsafe_allow_html=True)

# 🔍 Busca elenco
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]

if not elenco:
    st.info("Seu elenco está vazio.")
    st.stop()

# 🔍 Verifica se já existe leilão ativo
leilao_doc = db.collection("configuracoes").document("leilao_sistema").get()
if leilao_doc.exists and leilao_doc.to_dict().get("ativo", False):
    st.warning("Já existe um leilão ativo no sistema. Aguarde ele terminar para iniciar um novo.")
    st.stop()

jogador_escolhido = st.selectbox("Escolha o jogador para leiloar:", options=elenco, format_func=lambda x: f"{x['nome']} ({x['posição']})")
valor_inicial = st.number_input("Valor inicial do leilão (R$):", min_value=100000, step=50000, value=jogador_escolhido["valor"])
duracao = st.slider("Duração do Leilão (minutos):", min_value=1, max_value=10, value=2)

if st.button("🚀 Iniciar Leilão"):
    try:
        fim = datetime.utcnow() + timedelta(minutes=duracao)

        dados_leilao = {
            "jogador": {
                "nome": jogador_escolhido["nome"],
                "posicao": jogador_escolhido["posição"],
                "overall": jogador_escolhido["overall"],
                "valor": valor_inicial
            },
            "valor_atual": valor_inicial,
            "valor_inicial": valor_inicial,
            "id_time_original": id_time,
            "ativo": True,
            "fim": fim,
            "time_vencedor": ""
        }

        db.collection("configuracoes").document("leilao_sistema").set(dados_leilao)

        db.collection("times").document(id_time).collection("elenco").document(jogador_escolhido["id"]).delete()

        st.success("Leilão iniciado com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao iniciar leilão: {e}")
