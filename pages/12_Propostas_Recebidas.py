import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="Propostas Recebidas", layout="wide")

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

# 🔐 Verifica se o usuário está logado
verificar_login()

st.title("📨 Propostas Recebidas")

id_time_logado = st.session_state["id_time"]
nome_time_logado = st.session_state["nome_time"]

# 🔍 Busca propostas destinadas ao time logado
propostas_ref = db.collection("negociacoes").where("id_time_destino", "==", id_time_logado).stream()
propostas = [doc.to_dict() | {"id_doc": doc.id} for doc in propostas_ref]

if not propostas:
    st.info("Nenhuma proposta recebida até o momento.")
    st.stop()

for proposta in propostas:
    st.markdown("---")
    jogador = proposta.get("jogador", {})
    nome_jogador = jogador.get("nome", "Desconhecido")
    posicao = jogador.get("posicao", "N/A")
    overall = jogador.get("overall", "N/A")
    valor = proposta.get("valor_proposta", 0)
    tipo = proposta.get("tipo_proposta", "N/A")
    status = proposta.get("status", "pendente")
    jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
    time_origem_id = proposta.get("id_time_origem")

    col1, col2 = st.columns([4, 2])
    with col1:
        st.markdown(f"**👤 Jogador:** {nome_jogador} ({posicao}) - ⭐ {overall}")
        st.markdown(f"**💼 Tipo de proposta:** {tipo}")
        st.markdown(f"**💸 Valor em dinheiro:** R$ {valor:,.0f}".replace(",", "."))
        if jogadores_oferecidos:
            st.markdown("**👥 Jogadores oferecidos:**")
            for j in jogadores_oferecidos:
                st.markdown(f"- {j.get('nome')} ({j.get('posicao')}) ⭐ {j.get('overall')}")

        st.markdown(f"**📝 Status:** {status.upper()}")
    
    with col2:
        if status == "pendente":
            aceitar = st.button("✅ Aceitar", key=f"aceitar_{proposta['id_doc']}")
            recusar = st.button("❌ Recusar", key=f"recusar_{proposta['id_doc']}")

            if aceitar:
                # 🔁 Transferência do jogador
                jogador_id = proposta.get("id_jogador")
                jogador_data = proposta.get("jogador")
                
                # Remove jogador do time atual
                db.collection("times").document(id_time_logado).collection("elenco").document(jogador_id).delete()

                # Adiciona ao time de origem
                db.collection("times").document(time_origem_id).collection("elenco").add(jogador_data)

                # Se houver jogadores oferecidos, transfere também
                for j_oferecido in jogadores_oferecidos:
                    id_oferecido = j_oferecido["id_doc"]
                    db.collection("times").document(time_origem_id).collection("elenco").document(id_oferecido).delete()
                    db.collection("times").document(id_time_logado).collection("elenco").add(j_oferecido)

                # Atualiza valor do jogador
                novo_valor = proposta.get("valor_proposta", jogador_data.get("valor", 0))
                jogador_data["valor"] = novo_valor

                # Atualiza proposta
                db.collection("negociacoes").document(proposta["id_doc"]).update({"status": "aceita"})

                st.success("✅ Proposta aceita com sucesso!")
                st.rerun()

            if recusar:
                db.collection("negociacoes").document(proposta["id_doc"]).update({"status": "recusada"})
                st.warning("🚫 Proposta recusada.")
                st.rerun()
        else:
            st.info("⏳ Proposta já respondida.")
