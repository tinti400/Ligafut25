import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="Leilões Finalizados", layout="wide")

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

st.title("📜 Leilões Finalizados")

# 🔎 Buscar todos os leilões finalizados (inativos)
leiloes_ref = db.collection("leiloes_finalizados").order_by("fim", direction=firestore.Query.DESCENDING).stream()

leiloes = [doc.to_dict() for doc in leiloes_ref]

if not leiloes:
    st.info("Nenhum leilão finalizado até o momento.")
else:
    for leilao in leiloes:
        jogador = leilao.get("jogador", {})
        nome_jogador = jogador.get("nome", "Desconhecido")
        posicao = jogador.get("posição", "-")
        overall = jogador.get("overall", "N/A")
        valor = leilao.get("valor_atual", 0)
        time_vencedor = leilao.get("time_vencedor", "Sem vencedor")
        fim = leilao.get("fim")

        if isinstance(fim, datetime):
            fim_str = fim.strftime("%d/%m/%Y %H:%M")
        else:
            fim_str = "Data desconhecida"

        st.markdown("---")
        st.markdown(f"**🎯 Jogador:** {nome_jogador} ({posicao}) - ⭐ {overall}")
        st.markdown(f"**💰 Valor Final:** R$ {valor:,.0f}".replace(",", "."))
        st.markdown(f"**🏆 Time Vencedor:** {time_vencedor}")
        st.markdown(f"**🕒 Finalizado em:** {fim_str}")
