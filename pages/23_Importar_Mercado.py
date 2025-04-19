import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import firestore

st.set_page_config(page_title="📥 Importar Jogadores - Mercado", layout="wide")

st.title("📥 Importar Jogadores automaticamente para o Mercado")

# 🔐 Conexão com Firebase
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

# 📁 Caminho direto do arquivo salvo
caminho_excel = "/mnt/data/jogadores_overall_66_futbin.xlsx"

try:
    df = pd.read_excel(caminho_excel)
    st.success(f"✅ Planilha carregada com {len(df)} jogadores.")
    st.dataframe(df)

    if st.button("📤 Enviar jogadores ao Mercado"):
        sucesso, erro = 0, 0
        for _, row in df.iterrows():
            try:
                jogador = {
                    "nome": row["nome"],
                    "posicao": row["posicao"],
                    "overall": int(row["overall"]),
                    "valor": int(row["valor"]),
                    "nacionalidade": row.get("nacionalidade", "N/A"),
                    "time_origem": row.get("time_origem", "N/A")
                }
                db.collection("mercado_transferencias").add(jogador)
                sucesso += 1
            except Exception as e:
                erro += 1
                st.error(f"Erro ao adicionar jogador: {e}")
        st.success(f"✅ Importação finalizada: {sucesso} jogadores enviados com sucesso.")
        if erro > 0:
            st.warning(f"⚠️ {erro} jogadores não foram importados devido a erro.")

except FileNotFoundError:
    st.error("❌ Arquivo 'jogadores_overall_66_futbin.xlsx' não encontrado.")
except Exception as e:
    st.error(f"Erro ao processar o arquivo: {e}")
