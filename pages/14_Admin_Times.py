import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import registrar_movimentacao

st.set_page_config(page_title="Admin - Times", layout="wide")

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

# ✅ Verifica se é admin
id_usuario = st.session_state.get("usuario_id", "")
admin_ref = db.collection("admins").document(id_usuario).get()
eh_admin = admin_ref.exists

if not eh_admin:
    st.warning("🔒 Acesso restrito apenas para administradores.")
    st.stop()

st.title("🛠️ Administração de Times")

# 📦 Buscar todos os times
times_ref = db.collection("times").stream()
times = []
for doc in times_ref:
    time = doc.to_dict()
    time["id"] = doc.id
    times.append(time)

# 🔽 Selecionar time para adicionar saldo
nomes_times = [f"{t['nome']} (ID: {t['id']})" for t in times]
escolhido = st.selectbox("Selecione um time:", nomes_times)

indice = nomes_times.index(escolhido)
time = times[indice]
id_time = time["id"]
nome_time = time["nome"]
saldo_atual = time.get("saldo", 0)

st.markdown(f"### 💼 {nome_time}")
st.markdown(f"**Saldo atual:** R$ {saldo_atual:,.0f}".replace(",", "."))

# 💸 Adicionar saldo
valor = st.number_input("💰 Valor a adicionar (R$)", min_value=1_000_000, step=500_000, format="%d")

if st.button("✅ Adicionar saldo"):
    if valor > 0:
        try:
            novo_saldo = saldo_atual + valor
            db.collection("times").document(id_time).update({"saldo": novo_saldo})
            registrar_movimentacao(db, id_time, "-", "Admin", "Adição Manual", valor)
            st.success(f"✅ R$ {valor:,.0f} adicionados ao clube {nome_time}".replace(",", "."))
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar saldo: {e}")
    else:
        st.warning("Informe um valor válido.")
