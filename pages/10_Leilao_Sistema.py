import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
from datetime import datetime, timedelta
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# 🔐 Inicializa Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = gc_firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

verificar_login()

# Busca leilão ativo
doc_ref = db.collection("configuracoes").document("leilao_sistema")
doc = doc_ref.get()

if not doc.exists or not doc.to_dict().get("ativo", False):
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

leilao = doc.to_dict()
jogador = leilao.get("jogador", {})
valor_atual = leilao.get("valor_atual", 0)
id_time_vencedor = leilao.get("time_vencedor", "")
fim = leilao.get("fim")
id_time_usuario = st.session_state.get("id_time", "")

# Converte fim para datetime sem timezone
if hasattr(fim, 'to_datetime'):
    fim = fim.to_datetime()
if fim.tzinfo is not None:
    fim = fim.replace(tzinfo=None)

# Cronômetro
try:
    tempo_restante = (fim - datetime.now()).total_seconds()
    tempo_restante = max(0, int(tempo_restante))
    minutos, segundos = divmod(tempo_restante, 60)
    st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro ao calcular o cronômetro: {e}")
    st.stop()

st.markdown("---")

# Nome do time que está vencendo
nome_time_vencedor = ""
if id_time_vencedor:
    time_doc = db.collection("times").document(id_time_vencedor).get()
    nome_time_vencedor = time_doc.to_dict().get("nome", "Desconhecido")

# Exibição do jogador
col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
with col1:
    st.subheader(jogador.get("posicao", ""))
with col2:
    st.subheader(jogador.get("nome", ""))
with col3:
    st.metric("⭐ Overall", jogador.get("overall", ""))
with col4:
    st.metric("💰 Lance Atual", f"R$ {valor_atual:,.0f}".replace(",", "."))

if nome_time_vencedor:
    st.info(f"🏷️ Último Lance: {nome_time_vencedor}")

st.markdown("---")

# Finaliza leilão e adiciona jogador ao elenco
if tempo_restante == 0 and id_time_vencedor and jogador:
    try:
        jogador_final = {
            "nome": jogador.get("nome"),
            "posicao": jogador.get("posicao"),
            "overall": jogador.get("overall"),
            "valor": valor_atual
        }

        elenco_ref = db.collection("times").document(id_time_vencedor).collection("elenco")
        elenco_ref.add(jogador_final)

        # Atualiza saldo
        time_doc = db.collection("times").document(id_time_vencedor)
        saldo_atual = time_doc.get().to_dict().get("saldo", 0)
        novo_saldo = saldo_atual - valor_atual
        time_doc.update({"saldo": novo_saldo})

        # Movimentação financeira
        registrar_movimentacao(id_time_vencedor, jogador.get("nome", ""), "Leilão", "Compra", valor_atual)

        # Finaliza leilão
        doc_ref.update({"ativo": False})
        st.success("✅ Leilão encerrado! Jogador transferido com sucesso.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao finalizar o leilão: {e}")
        st.stop()

# Lances
if tempo_restante > 0:
    novo_lance = st.number_input("💸 Seu lance (mínimo: R$100.000 acima)", min_value=valor_atual + 100_000, step=100_000)
    if st.button("💥 Fazer Lance"):
        try:
            time_ref = db.collection("times").document(id_time_usuario)
            saldo = time_ref.get().to_dict().get("saldo", 0)

            if novo_lance > saldo:
                st.error("❌ Saldo insuficiente.")
            else:
                agora = datetime.now()
                novo_fim = fim
                if (fim - agora).total_seconds() <= 15:
                    novo_fim = agora + timedelta(seconds=15)

                doc_ref.update({
                    "valor_atual": novo_lance,
                    "time_vencedor": id_time_usuario,
                    "fim": novo_fim
                })

                st.success(f"✅ Lance de R$ {novo_lance:,.0f} enviado!".replace(",", "."))
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao registrar lance: {e}")
else:
    st.info("⏱️ O tempo do leilão acabou.")
