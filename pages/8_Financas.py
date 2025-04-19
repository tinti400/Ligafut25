import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login

st.set_page_config(page_title="💰 Finanças", layout="wide")

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

# 🔐 Verifica login
verificar_login()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("💰 Finanças do Clube")
st.markdown(f"### 📊 Time: **{nome_time}**")

# 📥 Carrega movimentações
mov_ref = db.collection("times").document(id_time).collection("movimentacoes").order_by("data", direction=firestore.Query.DESCENDING).stream()
movimentacoes = [doc.to_dict() for doc in mov_ref]

# ✅ Preenche jogador com "N/A" se não existir
for mov in movimentacoes:
    if "jogador" not in mov:
        mov["jogador"] = "N/A"

# 📊 Monta DataFrame
df = pd.DataFrame(movimentacoes)

if not df.empty and all(col in df.columns for col in ["tipo", "jogador", "valor"]):
    # Garante que valor seja numérico
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["valor_formatado"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".") if pd.notnull(x) else "N/A")

    # Trata a data corretamente
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Reorganiza e renomeia colunas
    colunas = ["data", "tipo", "jogador", "valor_formatado"]
    if "descricao" in df.columns:
        colunas.append("descricao")
    df = df[colunas]
    df = df.rename(columns={
        "data": "Data",
        "tipo": "Tipo",
        "jogador": "Jogador",
        "valor_formatado": "Valor",
        "descricao": "Descrição"
    })

    st.dataframe(df, use_container_width=True)
else:
    st.info("⚠️ Nenhuma movimentação financeira registrada ou dados incompletos.")
