import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

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

# ✅ Verifica login com segurança
verificar_login()

# ⚠️ Garante que id_time e nome_time existem
if "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.error("⚠️ Informações do time não encontradas. Faça login novamente.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📋 Elenco do Clube")
st.markdown(f"### 🏟️ Time: **{nome_time}**")

# 🔎 Busca elenco do time no Firestore
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]

if not elenco:
    st.info("📭 Nenhum jogador no elenco atualmente.")
    st.stop()

# 📊 Exibe elenco em formato de tabela
import pandas as pd

df = pd.DataFrame(elenco)

# Ordena por overall
df = df.sort_values(by="overall", ascending=False)

# Formata valor com R$
df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
df["valor_formatado"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".") if pd.notnull(x) else "N/A")

# Define colunas a exibir
df = df[["posicao", "nome", "overall", "valor_formatado"]]
df.columns = ["Posição", "Nome", "Overall", "Valor"]

st.dataframe(df, use_container_width=True)
