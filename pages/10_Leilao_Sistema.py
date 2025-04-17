import streamlit as st
from firebase_admin import firestore, credentials, initialize_app
import datetime
import time

# Configuração da página
st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# Inicializa Firebase
if "firebase" not in st.session_state:
    try:
        cred = credentials.Certificate(st.secrets["firebase"])
        initialize_app(cred)
        st.session_state["firebase"] = firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()

db = st.session_state["firebase"]

# Busca leilão ativo
leilao_ref = db.collection("configuracoes").document("leilao_sistema")
leilao_doc = leilao_ref.get()
if not leilao_doc.exists or not leilao_doc.to_dict().get("ativo", False):
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

dados = leilao_doc.to_dict()
fim = dados.get("fim")
inicio = dados.get("inicio")
jogador = dados.get("jogador", {})
valor_atual = dados.get("valor_atual", 0)
time_vencedor = dados.get("time_vencedor", "")
id_time_usuario = st.session_state.get("id_time", "")

# Cronômetro regressivo
tempo_restante = (fim - datetime.datetime.now()).total_seconds()
tempo_restante = max(0, int(tempo_restante))
minutos, segundos = divmod(tempo_restante, 60)

st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)
st.markdown("---")

# Exibição do jogador
col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
with col1:
    st.subheader(jogador.get("posição", ""))
with col2:
    st.subheader(jogador.get("nome", ""))
with col3:
    st.metric("⭐ Overall", jogador.get("overall", ""))
with col4:
    st.metric("💰 Lance Atual", f"R$ {valor_atual:,.0f}".replace(",", "."))

st.markdown("---")

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
                novo_fim = fim
                agora = datetime.datetime.now()
                if (fim - agora).total_seconds() <= 15:
                    novo_fim = agora + datetime.timedelta(seconds=15)

                leilao_ref.update({
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
    st.stop()
import streamlit as st
import datetime
from google.oauth2 import service_account
from google.cloud import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

# Inicializa o Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")
st.title("🏆 Leilão de Jogadores")

leilao_ref = db.collection("configuracoes").document("leilao_sistema")
leilao_doc = leilao_ref.get()

if not leilao_doc.exists:
    st.info("Nenhum leilão ativo no momento.")
    st.stop()

leilao = leilao_doc.to_dict()
jogador = leilao.get("jogador")
valor_inicial = leilao.get("valor")
time_vencedor = leilao.get("time_vencedor")
fim = leilao.get("fim")
lance_atual = leilao.get("lance_atual", valor_inicial)

# Converte o campo fim para datetime se necessário
if hasattr(fim, "timestamp"):
    fim_datetime = fim.to_datetime()
else:
    fim_datetime = fim

tempo_restante = (fim_datetime - datetime.datetime.now()).total_seconds()
tempo_restante = max(0, int(tempo_restante))
minutos, segundos = divmod(tempo_restante, 60)

# Exibe informações
st.markdown(f"### 👤 Jogador: {jogador}")
st.markdown(f"### 💰 Lance Atual: R$ {lance_atual:,.0f}".replace(",", "."))
st.markdown(f"### ⏳ Tempo restante: {minutos:02d}:{segundos:02d}")
if time_vencedor:
    st.markdown(f"### 🏷️ Último Lance: {time_vencedor}")

# Botão para dar lance
novo_lance = st.number_input("Digite seu lance (mínimo R$ 100.000 acima):", min_value=lance_atual + 100_000, step=100_000)
if st.button("💸 Dar Lance"):
    if "id_time" not in st.session_state or not st.session_state["id_time"]:
        st.warning("Você precisa estar logado para dar um lance.")
        st.stop()

    id_time = st.session_state["id_time"]
    nome_time = st.session_state["nome_time"]

    # Verifica saldo
    time_ref = db.collection("times").document(id_time)
    time_data = time_ref.get().to_dict()
    saldo = time_data.get("saldo", 0)

    if saldo < novo_lance:
        st.error("Saldo insuficiente para este lance.")
        st.stop()

    # Atualiza leilão
    leilao_ref.update({
        "lance_atual": novo_lance,
        "time_vencedor": nome_time,
        "id_time_vencedor": id_time,
        "fim": SERVER_TIMESTAMP  # Será ajustado manualmente ou com lógica adicional
    })

    st.success("Lance realizado com sucesso! Aguarde o término do leilão.")
    st.rerun()
