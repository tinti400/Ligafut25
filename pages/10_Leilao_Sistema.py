# 10_Leilao_Sistema.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Leilão do Sistema", layout="wide")

# Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
verificar_login()

# Auto atualização a cada 5 segundos
st_autorefresh(interval=5000, key="leilao_refresh")

st.markdown("""
    <style>
        .card {
            background-color: #f0f2f6;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }
        .leilao-header {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .leilao-sub {
            font-size: 14px;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Leilão do Sistema")

# Buscar leilões ativos
leiloes_ref = db.collection("leiloes_livres").where("ativo", "==", True)
leiloes = [doc.to_dict() | {"id": doc.id} for doc in leiloes_ref.stream()]

if not leiloes:
    st.info("Nenhum leilão ativo no momento.")
else:
    for leilao in leiloes:
        jogador = leilao.get("jogador", {})
        nome = jogador.get("nome", "Desconhecido")
        posicao = jogador.get("posicao", "-")
        overall = jogador.get("overall", "-")
        valor_atual = leilao.get("valor_atual", 0)
        fim = leilao.get("fim")
        ultimo_lance = leilao.get("ultimo_lance")
        id_time_vencedor = leilao.get("id_time_vencedor")

        tempo_restante = 0
        if isinstance(fim, datetime):
            tempo_restante = int((fim - datetime.now(timezone.utc)).total_seconds())

        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            with col1:
                st.markdown(f"<div class='leilao-header'>🎽 {nome}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='leilao-sub'>Posição: {posicao} | Overall: {overall}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='leilao-sub'>Valor Atual:</div>")
                st.markdown(f"<b>R$ {valor_atual:,.0f}</b>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='leilao-sub'>Tempo Restante:</div>")
                st.markdown(f"<b>{max(0, tempo_restante)} seg</b>", unsafe_allow_html=True)
            with col4:
                if tempo_restante > 0:
                    novo_lance = st.number_input("Lance", min_value=valor_atual + 100_000, step=100_000, key=f"lance_{leilao['id']}")
                    if st.button("📤 Dar Lance", key=f"btn_{leilao['id']}"):
                        db.collection("leiloes_livres").document(leilao['id']).update({
                            "valor_atual": novo_lance,
                            "ultimo_lance": st.session_state.usuario,
                            "id_time_vencedor": st.session_state.id_time,
                            "fim": datetime.now(timezone.utc) + timedelta(seconds=15)
                        })
                        st.success("Lance enviado com sucesso!")
                        st.rerun()
                else:
                    st.markdown("<span style='color:red;'>⛔ Leilão Encerrado</span>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Finalizar leilão com vencedor
        if tempo_restante <= 0 and id_time_vencedor:
            doc_ref = db.collection("leiloes_livres").document(leilao["id"])
            jogador["valor"] = valor_atual

            db.collection("times").document(id_time_vencedor).collection("elenco").add(jogador)

            time_ref = db.collection("times").document(id_time_vencedor)
            time_doc = time_ref.get()
            saldo_atual = time_doc.to_dict().get("saldo", 0)
            time_ref.update({"saldo": saldo_atual - valor_atual})

            doc_ref.update({
                "ativo": False,
                "fim": datetime.now(timezone.utc)
            })

            id_time_vendedor = leilao.get("id_time_vendedor")
            if id_time_vendedor:
                registrar_movimentacao(db, id_time_vendedor, "leilao_venda", nome, valor_atual)
            registrar_movimentacao(db, id_time_vencedor, "leilao_compra", nome, valor_atual)

            st.success(f"✅ Leilão de {nome} finalizado!")
            st.rerun()

        # Finalizar leilão sem vencedor
        if tempo_restante <= 0 and not id_time_vencedor:
            doc_ref = db.collection("leiloes_livres").document(leilao["id"])
            id_time_vendedor = leilao.get("id_time_vendedor")
            jogador["valor"] = valor_atual

            if id_time_vendedor:
                db.collection("times").document(id_time_vendedor).collection("elenco").add(jogador)

            doc_ref.update({
                "ativo": False,
                "fim": datetime.now(timezone.utc)
            })

            st.warning(f"⛔ Ninguém deu lance em {nome}. Ele voltou ao elenco do time vendedor.")
            st.rerun()
