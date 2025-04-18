import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="Propostas Enviadas", layout="wide")

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

st.title("📤 Propostas Enviadas")

# 🔎 Buscar propostas enviadas
try:
    propostas_ref = db.collection("negociacoes") \
        .where("id_time_origem", "==", id_time) \
        .order_by("timestamp", direction=firestore.Query.DESCENDING) \
        .stream()
    
    propostas = [doc.to_dict() for doc in propostas_ref]

    if not propostas:
        st.info("Você ainda não enviou nenhuma proposta.")
    else:
        for proposta in propostas:
            jogador = proposta.get("nome_jogador", "Desconhecido")
            tipo = proposta.get("tipo_proposta", "N/A")
            status = proposta.get("status", "pendente")
            valor = proposta.get("valor_proposta", 0)
            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            data = proposta.get("timestamp")

            if isinstance(data, datetime):
                data_str = data.strftime('%d/%m/%Y %H:%M')
            else:
                data_str = "Data não disponível"

            st.markdown("---")
            st.markdown(f"**🎯 Jogador Alvo:** {jogador}")
            st.markdown(f"**📌 Tipo de Proposta:** {tipo}")
            st.markdown(f"**💬 Status:** {status.capitalize()}")
            st.markdown(f"**💰 Valor Oferecido:** R$ {valor:,.0f}".replace(",", "."))
            st.markdown(f"**📅 Enviada em:** {data_str}")

            if jogadores_oferecidos:
                nomes = ", ".join([j.get("nome", "") for j in jogadores_oferecidos])
                st.markdown(f"**👥 Jogadores Oferecidos:** {nomes}")
except Exception as e:
    st.error(f"Erro ao carregar propostas: {e}")
