import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="🚨 Evento Roubo - LigaFut", layout="wide")

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

st.title("🚨 Evento de Roubo de Jogador")

# Listar todos os times (exceto o logado)
st.subheader("Escolha o time alvo para roubo:")
times = db.collection("times").stream()
times_dict = {doc.id: doc.to_dict().get("nome", "Sem nome") for doc in times if doc.id != id_time}

if not times_dict:
    st.info("Nenhum time disponível para roubo.")
    st.stop()

time_alvo_id = st.selectbox("Times disponíveis:", list(times_dict.keys()), format_func=lambda x: times_dict[x])

# Exibir elenco do time alvo
st.subheader(f"🎯 Jogadores do {times_dict[time_alvo_id]} disponíveis para roubo")
elenco_ref = db.collection("times").document(time_alvo_id).collection("elenco").stream()
elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]

if not elenco:
    st.info("Este time não possui jogadores.")
    st.stop()

jogador_escolhido = st.selectbox("Escolha o jogador a ser roubado:", elenco, format_func=lambda x: x.get("nome", "Sem nome"))

# Mostrar detalhes do jogador com segurança
st.markdown("---")
st.markdown(f"**🧍 Jogador:** {jogador_escolhido.get('nome', 'Sem nome')}")
st.markdown(f"**📍 Posição:** {jogador_escolhido.get('posicao', 'Não informada')}")
st.markdown(f"**⭐ Overall:** {jogador_escolhido.get('overall', 'N/A')}")
valor_jogador = jogador_escolhido.get("valor", 0)
st.markdown(f"**💰 Valor do Jogador:** R$ {valor_jogador:,.0f}".replace(",", "."))

# Calcular valor de roubo (50% do valor original)
valor_roubo = int(valor_jogador * 0.5)
st.markdown(f"**💸 Valor do Roubo (50%): R$ {valor_roubo:,.0f}**".replace(",", "."))

# Botão para confirmar roubo
if st.button("🔥 Realizar Roubo"):
    try:
        # Verificar saldo do time logado
        time_ref = db.collection("times").document(id_time)
        time_data = time_ref.get().to_dict()
        saldo = time_data.get("saldo", 0)

        if saldo < valor_roubo:
            st.error("❌ Saldo insuficiente para realizar o roubo.")
            st.stop()

        # Atualiza saldo dos dois times
        db.collection("times").document(id_time).update({
            "saldo": saldo - valor_roubo
        })

        saldo_destino = db.collection("times").document(time_alvo_id).get().to_dict().get("saldo", 0)
        db.collection("times").document(time_alvo_id).update({
            "saldo": saldo_destino + valor_roubo
        })

        # Remove jogador do time alvo e adiciona ao time comprador
        db.collection("times").document(time_alvo_id).collection("elenco").document(jogador_escolhido["id"]).delete()
        db.collection("times").document(id_time).collection("elenco").add({
            "nome": jogador_escolhido.get("nome", ""),
            "posicao": jogador_escolhido.get("posicao", ""),
            "overall": jogador_escolhido.get("overall", 0),
            "valor": valor_jogador
        })

        # Registrar movimentações
        from utils import registrar_movimentacao
        registrar_movimentacao(id_time, jogador_escolhido.get("nome", ""), "roubo", "entrada", -valor_roubo)
        registrar_movimentacao(time_alvo_id, jogador_escolhido.get("nome", ""), "roubo", "saida", valor_roubo)

        st.success("✅ Jogador roubado com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao realizar roubo: {e}")
