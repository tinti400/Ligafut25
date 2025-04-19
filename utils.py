import streamlit as st
from datetime import datetime

def verificar_login():
    """
    Verifica se o usuário está logado com base no session_state.
    Se não estiver logado, exibe aviso e interrompe o app.
    """
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("🔐 Você precisa estar logado para acessar esta página.")
        st.stop()

def registrar_movimentacao(db, id_time, tipo, descricao, valor, data=None):
    """
    Registra uma movimentação financeira no Firestore na subcoleção 'movimentacoes' do time.

    Parâmetros:
    - db: conexão com Firestore
    - id_time: ID do time
    - tipo: 'entrada' ou 'saida'
    - descricao: texto explicando a movimentação
    - valor: valor numérico da movimentação
    - data (opcional): string formatada (se não for enviada, usa a data/hora atual)
    """
    if not data:
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    movimentacao = {
        "tipo": tipo,
        "descricao": descricao,
        "valor": valor,
        "data": data
    }

    db.collection("times").document(id_time).collection("movimentacoes").add(movimentacao)
