import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import firestore

st.set_page_config(page_title="Importar Mercado", layout="wide")

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

# 👑 Verifica se é admin por e-mail
email_usuario = st.session_state.get("usuario", "")
if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

admin_ref = db.collection("admins").document(email_usuario).get()
if not admin_ref.exists:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧭 Título
st.markdown("<h1 style='text-align: center;'>📦 Importar Jogadores para o Mercado</h1><hr>", unsafe_allow_html=True)

# 📤 Upload do arquivo
arquivo = st.file_uploader("📂 Selecione um arquivo .xlsx com os jogadores", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)

        # Tratamento de colunas com nomes diferentes
        colunas_esperadas = {
            "foto": "foto",
            "nome": "nome",
            "posicao": "posicao",
            "posição": "posicao",
            "overall": "overall",
            "valor": "valor",
            "nacionalidade": "nacionalidade",
            "time de origem": "time_origem",
            "time_origem": "time_origem"
        }

        df.columns = [colunas_esperadas.get(col.lower(), col.lower()) for col in df.columns]

        obrigatorias = ["nome", "posicao", "overall", "valor", "nacionalidade", "time_origem"]
        if not all(col in df.columns for col in obrigatorias):
            st.error(f"❌ A planilha deve conter as colunas: {', '.join(obrigatorias)}")
            st.stop()

        with st.expander("👀 Visualizar Jogadores Importados"):
            st.dataframe(df)

        if st.button("🚀 Enviar jogadores ao mercado"):
            count = 0
            for _, row in df.iterrows():
                try:
                    db.collection("mercado_transferencias").add({
                        "nome": str(row["nome"]),
                        "posicao": str(row["posicao"]),
                        "overall": int(row["overall"]),
                        "valor": float(row["valor"]),
                        "nacionalidade": str(row["nacionalidade"]),
                        "time_origem": str(row["time_origem"]),
                        "foto": str(row["foto"]) if "foto" in row and pd.notna(row["foto"]) else ""
                    })
                    count += 1
                except Exception as e:
                    st.error(f"Erro ao adicionar jogador: {e}")
            st.success(f"✅ {count} jogadores adicionados ao mercado com sucesso!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
