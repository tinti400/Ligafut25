import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="Histórico de Transferências", layout="wide")

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

# ✅ Verifica login
verificar_login()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📜 Histórico de Transferências")

# 🔎 Buscar movimentações financeiras do time logado
mov_ref = db.collection("times").document(id_time).collection("movimentacoes") \
import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import pandas as pd

st.set_page_config(page_title="Histórico de Transferências", layout="wide")

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

# 🧠 Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state.get("id_time")
nome_time = st.session_state.get("nome_time", "")

st.title("📜 Histórico de Transferências")
st.markdown(f"### 🏠 Time: `{nome_time}`")

# 🔍 Consulta movimentações
try:
    mov_ref = db.collection("times").document(id_time).collection("movimentacoes").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    historico = []
    for doc in mov_ref:
        d = doc.to_dict()
        tipo = d.get("tipo", "").capitalize()
        descricao = d.get("descricao", "")
        valor = d.get("valor", 0)

        try:
            valor_formatado = f"R$ {float(valor):,.0f}".replace(",", ".")
        except:
            valor_formatado = "R$ 0"

        historico.append({
            "Tipo": tipo,
            "Descrição": descricao,
            "Valor": valor_formatado
        })

    if not historico:
        st.info("Nenhuma movimentação registrada.")
    else:
        df = pd.DataFrame(historico)
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao buscar histórico: {e}")

