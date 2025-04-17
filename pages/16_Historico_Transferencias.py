import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="Histórico de Transferências", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Verificar login
verificar_login()

st.title("📜 Histórico de Transferências")

# Filtros
st.subheader("🔍 Filtro de Busca")

filtro_jogador = st.text_input("Buscar por nome do jogador")
filtro_time = st.text_input("Buscar por nome do time (Origem ou Destino)")

# Buscar transferências
transferencias_ref = db.collection("transferencias_concluidas").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
transferencias = [doc.to_dict() for doc in transferencias_ref]

# Aplica Filtros
transferencias_filtradas = []
for trans in transferencias:
    jogador = trans.get("jogador", "").lower()
    time_origem = trans.get("time_origem", "").lower()
    time_destino = trans.get("time_destino", "").lower()

    if filtro_jogador.lower() in jogador and (filtro_time.lower() in time_origem or filtro_time.lower() in time_destino):
        transferencias_filtradas.append(trans)

if not transferencias_filtradas:
    st.info("Nenhuma transferência encontrada com os filtros aplicados.")
else:
    for trans in transferencias_filtradas:
        jogador = trans.get("jogador", "Jogador")
        time_origem = trans.get("time_origem", "Desconhecido")
        time_destino = trans.get("time_destino", "Desconhecido")
        valor = trans.get("valor", 0)
        data = trans.get("timestamp")

        if isinstance(data, datetime):
            data_str = data.strftime("%d/%m/%Y - %H:%M")
        else:
            data_str = ""

        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        with col1:
            st.write(f"**{jogador}**")
        with col2:
            st.write(f"Origem: {time_origem}")
        with col3:
            st.write(f"Destino: {time_destino}")
        with col4:
            if valor > 0:
                st.write(f"Valor: R$ {valor:,.0f}")
            else:
                st.write("Transferência via troca")
        with col5:
            st.write(data_str)
