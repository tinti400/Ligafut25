import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
import datetime

st.set_page_config(page_title="🕵️ Evento de Roubo", layout="wide")

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

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"## 🕵️ Evento de Roubo - {nome_time}")

# Buscar todos os times disponíveis (exceto o seu)
times = db.collection("times").stream()
opcoes_times = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times if doc.id != id_time}

time_alvo_id = st.selectbox("Selecione um time para roubar jogador:", options=list(opcoes_times.keys()), format_func=lambda x: opcoes_times[x])

# Listar jogadores disponíveis do time alvo
elenco_ref = db.collection("times").document(time_alvo_id).collection("elenco").stream()
jogadores_alvo = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]

# Buscar jogadores protegidos no time alvo
protecao_ref = db.collection("eventos_multa").document("protecoes").collection(time_alvo_id).stream()
protegidos = [doc.id for doc in protecao_ref]

# Filtrar apenas jogadores não protegidos
jogadores_disponiveis = [j for j in jogadores_alvo if j["nome"] not in protegidos]

if not jogadores_disponiveis:
    st.warning("❌ Nenhum jogador disponível para roubo neste time (todos estão protegidos).")
    st.stop()

# Interface para selecionar jogador
jogador_nome = st.selectbox("Escolha o jogador para roubar:", options=[j["nome"] for j in jogadores_disponiveis])
jogador_escolhido = next(j for j in jogadores_disponiveis if j["nome"] == jogador_nome)

# Mostrar detalhes
st.markdown("---")
st.markdown(f"**🧍 Jogador:** {jogador_escolhido['nome']}")
st.markdown(f"**📍 Posição:** {jogador_escolhido['posicao']}")
st.markdown(f"**⭐ Overall:** {jogador_escolhido['overall']}")
st.markdown(f"**💰 Valor:** R$ {jogador_escolhido['valor']:,.0f}".replace(",", "."))

# Confirmar roubo
if st.button("🚨 Roubar Jogador"):
    valor_roubo = jogador_escolhido['valor'] * 0.5

    # Verifica saldo
    time_ref = db.collection("times").document(id_time)
    saldo = time_ref.get().to_dict().get("saldo", 0)

    if saldo < valor_roubo:
        st.error("❌ Saldo insuficiente para realizar o roubo.")
        st.stop()

    try:
        # Remove jogador do elenco do time alvo
        db.collection("times").document(time_alvo_id).collection("elenco").document(jogador_escolhido["id_doc"]).delete()

        # Adiciona jogador ao seu elenco
        db.collection("times").document(id_time).collection("elenco").add({
            "nome": jogador_escolhido["nome"],
            "posicao": jogador_escolhido["posicao"],
            "overall": jogador_escolhido["overall"],
            "valor": jogador_escolhido["valor"]
        })

        # Atualiza saldos
        db.collection("times").document(id_time).update({"saldo": firestore.Increment(-valor_roubo)})
        db.collection("times").document(time_alvo_id).update({"saldo": firestore.Increment(valor_roubo)})

        st.success(f"✅ Jogador {jogador_escolhido['nome']} roubado com sucesso por R$ {valor_roubo:,.0f}".replace(",", "."))
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao processar roubo: {e}")
