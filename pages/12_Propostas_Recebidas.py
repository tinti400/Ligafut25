import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Propostas Recebidas", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
verificar_login()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.title("📥 Propostas Recebidas")
st.markdown(f"### Time: {nome_time}")

propostas_ref = db.collection("propostas").where("id_time_destino", "==", id_time).stream()
propostas = [p for p in propostas_ref]

if not propostas:
    st.info("Nenhuma proposta recebida no momento.")
else:
    for proposta in propostas:
        dados = proposta.to_dict()
        jogador = dados['jogador']
        valor = dados['valor']
        id_time_origem = dados['id_time_origem']
        id_proposta = proposta.id
        status = dados.get("status", "pendente")

        if status != "pendente":
            continue

        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 3])
        with col1:
            st.write(jogador["nome"])
        with col2:
            st.write(jogador["posicao"])
        with col3:
            st.write(jogador["overall"])
        with col4:
            st.write(f"R$ {valor:,.0f}")

        with col5:
            col_aceita, col_recusa, col_contra = st.columns(3)

            with col_aceita:
                if st.button("✅ Aceitar", key=f"aceitar_{id_proposta}"):
                    # Atualizar saldos
                    time_origem_ref = db.collection("times").document(id_time_origem)
                    time_destino_ref = db.collection("times").document(id_time)

                    saldo_origem = time_origem_ref.get().to_dict().get("saldo", 0)
                    saldo_destino = time_destino_ref.get().to_dict().get("saldo", 0)

                    if saldo_origem < valor:
                        st.error("O time comprador não tem saldo suficiente.")
                    else:
                        time_origem_ref.update({"saldo": saldo_origem - valor})
                        time_destino_ref.update({"saldo": saldo_destino + valor})

                        # Remover jogador do time destino
                        elenco_destino_ref = time_destino_ref.collection("elenco")
                        elenco_query = elenco_destino_ref.where("nome", "==", jogador["nome"]).get()
                        for doc in elenco_query:
                            doc.reference.delete()

                        # Adicionar jogador ao time origem
                        jogador["valor"] = valor  # Atualiza valor do jogador com valor da proposta
                        time_origem_ref.collection("elenco").add(jogador)

                        # Registrar movimentações
                        registrar_movimentacao(
                            id_time=id_time,
                            jogador=jogador["nome"],
                            categoria="Venda",
                            tipo="Entrada",
                            valor=valor,
                            time_recebimento=st.session_state.nome_time,
                            time_envio="Time Comprador"
                        )
                        registrar_movimentacao(
                            id_time=id_time_origem,
                            jogador=jogador["nome"],
                            categoria="Compra",
                            tipo="Saída",
                            valor=valor,
                            time_envio=st.session_state.nome_time,
                            time_recebimento="Time Comprador"
                        )

                        # Deletar proposta
                        proposta.reference.delete()
                        st.success("Proposta aceita com sucesso!")
                        st.rerun()

            with col_recusa:
                if st.button("❌ Recusar", key=f"recusar_{id_proposta}"):
                    proposta.reference.delete()
                    st.warning("Proposta recusada.")
                    st.rerun()

            with col_contra:
                nova = st.number_input(
                    f"Contra proposta para {jogador['nome']}",
                    min_value=valor + 1_000_000,
                    step=500_000,
                    key=f"contra_valor_{id_proposta}"
                )
                if st.button("📤 Enviar Contra", key=f"enviar_contra_{id_proposta}"):
                    proposta.reference.update({
                        "valor": nova,
                        "status": "pendente"
                    })
                    st.success("Contra proposta enviada.")
                    st.rerun()
