import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="Administração de Times", layout="wide")

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

# Verifica se está logado
verificar_login()

st.title("⚙️ Administração de Times")

# Adicionar novo time
with st.expander("➕ Adicionar Novo Time"):
    nome_time = st.text_input("Nome do Time")
    saldo_inicial = st.number_input("Saldo Inicial (R$)", min_value=0, value=250_000_000, step=1_000_000)

    if st.button("✅ Cadastrar Time"):
        if nome_time:
            db.collection("times").add({
                "nome": nome_time,
                "saldo": saldo_inicial
            })
            st.success("Time cadastrado com sucesso!")
            st.rerun()
        else:
            st.warning("Preencha o nome do time.")

st.markdown("---")
st.subheader("📋 Lista de Times Cadastrados")

# Exibir times
times_ref = db.collection("times").stream()
for doc in times_ref:
    time = doc.to_dict()
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.text(f"🏷️ {time.get('nome', 'Sem Nome')}")
    with col2:
        saldo_formatado = f"R$ {time.get('saldo', 0):,.0f}".replace(",", ".")
        st.text(f"💰 Saldo: {saldo_formatado}")
    with col3:
        if st.button("🗑️ Excluir", key=f"excluir_{doc.id}"):
            db.collection("times").document(doc.id).delete()
            st.success("Time excluído com sucesso!")
            st.rerun()
