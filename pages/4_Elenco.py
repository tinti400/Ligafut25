import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
import pandas as pd

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

# ✅ Garante que sessão tenha time
if "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.error("⚠️ Informações do time não encontradas. Faça login novamente.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📋 Elenco do Clube")
st.markdown(f"### 🏟️ Time: **{nome_time}**")

# 🔍 Busca elenco do time
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

# 📊 Exibe elenco formatado
df = pd.DataFrame(elenco)

df = df.sort_values(by="overall", ascending=False)
df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
df["valor_formatado"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".") if pd.notnull(x) else "N/A")

df = df[["posicao", "nome", "overall", "valor_formatado"]]
df.columns = ["Posição", "Nome", "Overall", "Valor"]

st.dataframe(df, use_container_width=True)
