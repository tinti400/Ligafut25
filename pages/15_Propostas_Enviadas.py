import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from utils import verificar_login

st.set_page_config(page_title="Propostas Enviadas", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Verificar login
verificar_login()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.title("📤 Propostas Enviadas")
st.markdown(f"### Time: {nome_time}")

# Buscar propostas enviadas
propostas_ref = db.collection("negociacoes").where("id_time_origem", "==", id_time).stream()
propostas = [doc.to_dict() | {"id_doc": doc.id} for doc in propostas_ref]

if not propostas:
    st.info("Você não enviou nenhuma proposta ainda.")
else:
    st.subheader("📋 Propostas em andamento")

    for proposta in propostas:
        jogador = proposta.get("jogador", {})
        nome_jogador = proposta.get("nome_jogador", "Desconhecido")
        posicao = jogador.get("posicao", "N/D")
        overall = jogador.get("overall", "N/A")
        valor = proposta.get("valor_proposta", 0)
        tipo = proposta.get("tipo_proposta", "Não informado")
        status = proposta.get("status", "pendente")
        jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
        id_time_destino = proposta.get("id_time_destino")

        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 2, 1.5, 2])
        with col1:
            st.write(f"**🎯 Jogador Desejado:** {nome_jogador}")
        with col2:
            st.write(f"**Posição:** {posicao}")
        with col3:
            st.write(f"**Overall:** {overall}")
        with col4:
            st.write(f"**Tipo de Proposta:** {tipo}")

        if tipo != "Somente Dinheiro":
            st.markdown("**👥 Jogadores Oferecidos:**")
            for j in jogadores_oferecidos:
                st.write(f"- {j.get('nome')} ({j.get('posicao')}) - Overall {j.get('overall')} - R$ {j.get('valor',0):,.0f}")

        if tipo != "Troca Simples":
            st.write(f"**💰 Valor em dinheiro:** R$ {valor:,.0f}")

        st.write(f"**📌 Status da proposta:** `{status}`")

        if status == "pendente":
            if st.button("❌ Cancelar Proposta", key=f"cancelar_{proposta['id_doc']}"):
                db.collection("negociacoes").document(proposta["id_doc"]).delete()
                st.warning("Proposta cancelada.")
                st.rerun()

        elif status == "pendente" and proposta.get("foi_contra_proposta", False):
            st.warning("⚠️ Você recebeu uma contra proposta com novo valor!")

        elif status == "recusada":
            st.error("❌ Sua proposta foi recusada.")
        elif status == "aceita":
            st.success("✅ Sua proposta foi aceita!")
