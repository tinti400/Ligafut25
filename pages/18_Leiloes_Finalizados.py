import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

st.set_page_config(page_title="Leilões Finalizados", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("📜 Leilões Finalizados")

# Buscar todos os leilões encerrados
leiloes_ref = db.collection("leiloes_livres").where("ativo", "==", False).stream()
leiloes = [doc.to_dict() for doc in leiloes_ref]

# Ordenar por data mais recente
leiloes.sort(key=lambda x: x.get("fim", datetime.min), reverse=True)

if not leiloes:
    st.info("Nenhum leilão finalizado ainda.")
else:
    st.markdown("### 📋 Histórico de Leilões")
    for leilao in leiloes:
        jogador = leilao.get("jogador", {})
        valor_final = leilao.get("valor_atual", jogador.get("valor", 0))
        time_vendedor = leilao.get("nome_time_vendedor", "Desconhecido")
        time_comprador = leilao.get("id_time_vencedor", "Comprador")

        col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 1, 2, 3, 3])
        with col1:
            st.write(f"**{jogador.get('posicao', '')}**")
        with col2:
            st.write(jogador.get("nome", ""))
        with col3:
            st.write(jogador.get("overall", ""))
        with col4:
            st.write(f"R$ {valor_final:,.0f}")
        with col5:
            st.write(f"👤 {time_vendedor}")
        with col6:
            st.write(f"🤝 {time_comprador}")
