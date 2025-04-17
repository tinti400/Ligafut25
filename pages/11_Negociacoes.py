import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from utils import verificar_login

st.set_page_config(page_title="Negociações entre Clubes", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Verificar login
verificar_login()

st.title("🤝 Negociações entre Clubes")

# Dados do time logado
id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.markdown(f"### Seu Time: {nome_time}")

# Buscar todos os times
times_ref = db.collection("times").stream()
times = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

# Carregar elenco do time logado
elenco_usuario_ref = db.collection("times").document(id_time).collection("elenco").stream()
meu_elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_usuario_ref]

# Listar times adversários
for time_id, time_nome in times.items():
    if time_id == id_time:
        continue

    with st.expander(f"⚽ Time: {time_nome}"):
        elenco_ref = db.collection("times").document(time_id).collection("elenco").stream()
        elenco_adversario = [jogador.to_dict() | {"id_doc": jogador.id} for jogador in elenco_ref]

        if not elenco_adversario:
            st.write("Nenhum jogador disponível neste time.")
        else:
            for jogador in elenco_adversario:
                nome = jogador.get("nome", "Sem nome")
                posicao = jogador.get("posicao", "Desconhecida")
                overall = jogador.get("overall", "N/A")
                valor = jogador.get("valor", 0)
                id_jogador = jogador.get("id_doc")

                st.markdown("---")
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.markdown(f"**🎯 Jogador alvo:** {nome}")
                with col2:
                    st.markdown(f"**Posição:** {posicao}")
                with col3:
                    st.markdown(f"**Overall:** {overall}")
                with col4:
                    st.markdown(f"**Valor:** R$ {valor:,.0f}")

                tipo_proposta = st.selectbox(
                    "Tipo de Proposta:",
                    ["Somente Dinheiro", "Troca Simples", "Troca + Dinheiro"],
                    key=f"tipo_proposta_{id_jogador}"
                )

                jogadores_oferecidos_dados = []
                valor_adicional = 0

                if tipo_proposta in ["Troca Simples", "Troca + Dinheiro"]:
                    nomes_jogadores = [j['nome'] for j in meu_elenco]
                    jogadores_oferecidos = st.multiselect(
                        "👥 Jogadores oferecidos:",
                        options=nomes_jogadores,
                        key=f"oferecer_{id_jogador}"
                    )
                    jogadores_oferecidos_dados = [
                        j for j in meu_elenco if j["nome"] in jogadores_oferecidos
                    ]

                if tipo_proposta in ["Somente Dinheiro", "Troca + Dinheiro"]:
                    valor_adicional = st.number_input(
                        "💰 Valor em dinheiro (R$)",
                        min_value=1_000_000,
                        step=500_000,
                        value=valor,
                        key=f"valor_dinheiro_{id_jogador}"
                    )

                col_confirmar = st.columns(5)[2]
                with col_confirmar:
                    if st.button(f"📨 Enviar Proposta por {nome}", key=f"confirmar_{id_jogador}"):
                        proposta_data = {
                            "id_time_origem": id_time,
                            "id_time_destino": time_id,
                            "id_jogador": id_jogador,
                            "nome_jogador": nome,
                            "jogador": jogador,
                            "valor_proposta": valor_adicional,
                            "jogadores_oferecidos": jogadores_oferecidos_dados,
                            "tipo_proposta": tipo_proposta,
                            "status": "pendente",
                            "timestamp": firestore.SERVER_TIMESTAMP,
                        }

                        db.collection("negociacoes").add(proposta_data)
                        st.success("Proposta enviada com sucesso!")
                        st.rerun()
