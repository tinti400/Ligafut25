import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="📋 Elenco", layout="wide")

# 🔐 Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

# ✅ Verifica login
verificar_login()

if "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.error("⚠️ Informações do time não encontradas. Faça login novamente.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📋 Elenco do Clube")
st.markdown(f"### 🏟️ Time: **{nome_time}**")

# 🔓 Verifica se o mercado está aberto
config_ref = db.collection("configuracoes").document("mercado").get()
mercado_aberto = config_ref.to_dict().get("aberto", False) if config_ref.exists else False

# 🔍 Busca elenco
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()

elenco = []
for doc in elenco_ref:
    jogador = doc.to_dict()
    jogador["id_doc"] = doc.id
    jogador["posicao"] = jogador.get("posicao", "Desconhecido")
    jogador["nome"] = jogador.get("nome", "Desconhecido")
    jogador["overall"] = jogador.get("overall", 0)
    jogador["valor"] = jogador.get("valor", 0)
    elenco.append(jogador)

if not elenco:
    st.info("📭 Nenhum jogador no elenco atualmente.")
    st.stop()

# 🔁 Exibe jogador por jogador com botão de ação
for jogador in sorted(elenco, key=lambda x: x["overall"], reverse=True):
    col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 2, 2])
    with col1:
        st.markdown(f"**{jogador['posicao']}**")
    with col2:
        st.markdown(f"**{jogador['nome']}**")
    with col3:
        st.markdown(f"⭐ {jogador['overall']}")
    with col4:
        valor = jogador['valor']
        st.markdown(f"💰 R$ {valor:,.0f}".replace(",", "."))
    with col5:
        if mercado_aberto:
            if st.button("💸 Vender", key=jogador["id_doc"]):
                try:
                    # Calcula valor recebido (70%)
                    valor_recebido = int(valor * 0.7)

                    # Atualiza saldo do time
                    time_ref = db.collection("times").document(id_time)
                    time_doc = time_ref.get()
                    saldo_atual = time_doc.to_dict().get("saldo", 0)
                    novo_saldo = saldo_atual + valor_recebido
                    time_ref.update({"saldo": novo_saldo})

                    # Remove do elenco
                    db.collection("times").document(id_time).collection("elenco").document(jogador["id_doc"]).delete()

                    # Adiciona ao mercado com valor cheio
                    jogador_para_mercado = {
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": jogador["valor"],
                        "time_origem": nome_time,
                        "nacionalidade": jogador.get("nacionalidade", "N/A")
                    }
                    db.collection("mercado_transferencias").add(jogador_para_mercado)

                    # Registra movimentação
                    registrar_movimentacao(db, id_time, "entrada", f"Venda de {jogador['nome']} ao mercado", valor_recebido, jogador["nome"])

                    st.success(f"{jogador['nome']} foi vendido ao mercado por R$ {valor_recebido:,.0f}".replace(",", "."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao vender jogador: {e}")
        else:
            st.markdown("🔒 Mercado Fechado")
