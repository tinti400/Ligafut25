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
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

# ✅ Verifica login
verificar_login()

# 🧠 Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"<h2 style='text-align: center;'>⚽ Leiloar Jogador do {nome_time}</h2><hr>", unsafe_allow_html=True)

# 🔎 Busca elenco do time
try:
    elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
    elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    st.stop()

if not elenco:
    st.info("📭 Seu elenco está vazio.")
    st.stop()

# 📝 Formulário de leilão
with st.form("form_leiloar"):
    jogador_escolhido = st.selectbox(
        "Escolha o jogador para leiloar:",
        options=elenco,
        format_func=lambda x: f"{x.get('nome', 'Desconhecido')} ({x.get('posição', 'Sem posição')})"
    )
    duracao = st.slider("⏱️ Duração do leilão (minutos)", min_value=1, max_value=10, value=2)
    botao_leiloar = st.form_submit_button("🚀 Iniciar Leilão")

# 🚀 Inicia leilão
if botao_leiloar and jogador_escolhido:
    try:
        fim = datetime.utcnow() + timedelta(minutes=duracao)

        dados_leilao = {
            "jogador": {
                "nome": jogador_escolhido.get("nome", ""),
                "posição": jogador_escolhido.get("posição", "Sem posição"),
                "overall": jogador_escolhido.get("overall", 0),
                "valor": jogador_escolhido.get("valor", 0)
            },
            "valor_atual": jogador_escolhido.get("valor", 0),
            "valor_inicial": jogador_escolhido.get("valor", 0),
            "time_vencedor": "",
            "id_time_atual": id_time,
            "ativo": True,
            "fim": fim
        }

        db.collection("configuracoes").document("leilao_sistema").set(dados_leilao)

        # Remove jogador do elenco do time
        db.collection("times").document(id_time).collection("elenco").document(jogador_escolhido["id_doc"]).delete()

        st.success("✅ Jogador enviado para o leilão com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao iniciar leilão: {e}")
