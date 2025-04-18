import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime, timedelta
from utils import verificar_login

st.set_page_config(page_title="Leiloar Jogador", layout="wide")

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

st.title("🔨 Leiloar Jogador do Elenco")

# Carregar elenco do time logado
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]

if not elenco:
    st.info("Seu elenco está vazio.")
    st.stop()

jogadores_nomes = [j["nome"] for j in elenco]
jogador_selecionado = st.selectbox("Selecione o jogador para leilão:", jogadores_nomes)

jogador_dados = next((j for j in elenco if j["nome"] == jogador_selecionado), None)

if jogador_dados:
    st.markdown(f"**Posição:** {jogador_dados.get('posição', '-')}")
    st.markdown(f"**Overall:** {jogador_dados.get('overall', '-')}")
    st.markdown(f"**Valor de mercado:** R$ {jogador_dados.get('valor', 0):,.0f}".replace(",", "."))

    duracao = st.slider("⏱️ Duração do Leilão (minutos)", 1, 10, 2)

    if st.button("🚀 Iniciar Leilão"):
        agora = datetime.now()
        fim = agora + timedelta(minutes=duracao)

        leilao_data = {
            "inicio": agora,
            "fim": fim,
            "jogador": jogador_dados,
            "valor_atual": jogador_dados["valor"],
            "time_vencedor": "",
            "id_time_vencedor": "",
            "ativo": True
        }

        db.collection("configuracoes").document("leilao_sistema").set(leilao_data)

        # Remove jogador do elenco
        db.collection("times").document(id_time).collection("elenco").document(jogador_dados["id"]).delete()

        st.success(f"Leilão iniciado para {jogador_dados['nome']}!")
        st.rerun()
