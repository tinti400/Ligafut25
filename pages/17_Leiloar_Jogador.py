# 17_Leiloar_Jogador.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
from utils import verificar_login

st.set_page_config(page_title="Leiloar Jogador", layout="wide")

if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

verificar_login()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.markdown("""
    <style>
        .card {
            background-color: #f0f2f6;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }
        .label {
            font-weight: bold;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🟡 Leiloar Jogador do Seu Elenco")
st.markdown(f"### 🏟️ Time: **{nome_time}**")

# Buscar elenco do time
elenco_ref = db.collection("times").document(id_time).collection("elenco")
elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref.stream()]

if not elenco:
    st.info("Seu elenco está vazio.")
else:
    st.subheader("📋 Selecione um Jogador para Leilão")
    for jogador in elenco:
        nome = jogador.get("nome", "Sem nome")
        posicao = jogador.get("posicao", "Desconhecida")
        overall = jogador.get("overall", "-")
        valor = jogador.get("valor", 0)

        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            with col1:
                st.markdown(f"<div class='label'>🎽 {nome}</div>", unsafe_allow_html=True)
                st.write(f"Posição: {posicao}")
            with col2:
                st.write(f"Overall: {overall}")
            with col3:
                st.write(f"Valor: R$ {valor:,.0f}")
            with col4:
                duracao = st.number_input(
                    "⏱️ Duração (segundos)",
                    min_value=30,
                    value=120,
                    step=15,
                    key=f"duracao_{jogador['id_doc']}"
                )

                if st.button(f"🚀 Leiloar {nome}", key=f"leiloar_{jogador['id_doc']}"):
                    fim = datetime.now(timezone.utc) + timedelta(seconds=duracao)
                    leilao = {
                        "jogador": {
                            "nome": nome,
                            "posicao": posicao,
                            "overall": overall,
                            "valor": valor
                        },
                        "valor_atual": valor,
                        "ativo": True,
                        "fim": fim,
                        "ultimo_lance": None,
                        "id_time_vencedor": None,
                        "id_time_vendedor": id_time,
                        "nome_time_vendedor": nome_time
                    }

                    db.collection("leiloes_livres").add(leilao)
                    elenco_ref.document(jogador["id_doc"]).delete()
                    st.success(f"Jogador {nome} foi colocado em leilão com sucesso!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
