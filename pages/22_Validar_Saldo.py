import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore

st.set_page_config(page_title="💰 Validar Saldos - LigaFut", layout="wide")

# 🔐 Firebase
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

# ✅ Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
admin_ref = db.collection("admins").document(email_usuario).get()
if not admin_ref.exists:
    st.warning("🔒 Acesso restrito a administradores.")
    st.stop()

st.title("💰 Validação de Saldos por Rodada")

id_liga = "VUnsRMAPOc9Sj9n5BenE"
colecao_rodadas = f"ligas/{id_liga}/rodadas_divisao_1"

def atualizar_saldo(id_time, valor):
    time_ref = db.collection("times").document(id_time)
    doc = time_ref.get()
    if doc.exists:
        saldo_atual = doc.to_dict().get("saldo", 0)
        time_ref.update({"saldo": saldo_atual + valor})

if st.button("💰 Validar saldos das rodadas"):
    rodadas = db.collection(colecao_rodadas).stream()
    jogos_processados = 0

    for rodada in rodadas:
        dados = rodada.to_dict()
        jogos = dados.get("jogos", [])
        for jogo in jogos:
            mandante = jogo.get("mandante")
            visitante = jogo.get("visitante")
            gols_mandante = jogo.get("gols_mandante")
            gols_visitante = jogo.get("gols_visitante")

            # Pula jogos sem placar
            if gols_mandante is None or gols_visitante is None:
                continue

            saldo_mandante = 0
            saldo_visitante = 0

            # Vitória
            if gols_mandante > gols_visitante:
                saldo_mandante += 2_000_000
            elif gols_visitante > gols_mandante:
                saldo_visitante += 2_000_000

            # Gols feitos / sofridos
            saldo_mandante += (gols_mandante * 50_000) - (gols_visitante * 5_000)
            saldo_visitante += (gols_visitante * 50_000) - (gols_mandante * 5_000)

            # Atualiza Firestore
            atualizar_saldo(mandante, saldo_mandante)
            atualizar_saldo(visitante, saldo_visitante)

            jogos_processados += 1

    st.success(f"✅ Saldos atualizados com sucesso para {jogos_processados} jogos!")
