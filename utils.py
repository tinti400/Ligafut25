from datetime import datetime
import streamlit as st

def verificar_login():
    """
    Verifica se o usuário está logado.
    Se não estiver, exibe um aviso e encerra a execução da página.
    """
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.stop()

def registrar_movimentacao(db, id_time, tipo, descricao, valor, jogador=None):
    """
    Registra uma movimentação financeira no histórico de um time.

    Parâmetros:
    - db: instância do Firestore
    - id_time: ID do time (documento na coleção 'times')
    - tipo: "entrada" ou "saida"
    - descricao: texto explicando o motivo
    - valor: valor numérico positivo
    - jogador: (opcional) nome do jogador envolvido
    """
    if valor <= 0:
        st.warning("❗ Valor inválido para movimentação.")
        return

    movimentacao = {
        "tipo": tipo,
        "descricao": descricao,
        "valor": valor,
        "timestamp": datetime.utcnow()
    }

    if jogador:
        movimentacao["jogador"] = jogador

    try:
        db.collection("times").document(id_time).collection("movimentacoes").add(movimentacao)
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

