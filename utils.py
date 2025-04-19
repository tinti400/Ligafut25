from datetime import datetime

def registrar_movimentacao(db, id_time, tipo, descricao, valor, jogador=None):
    """
    Registra uma movimentação financeira no histórico de um time.

    Parâmetros:
    - db: instância do firestore
    - id_time: ID do time (documento na coleção 'times')
    - tipo: "entrada" ou "saida"
    - descricao: texto descritivo da movimentação
    - valor: valor numérico (positivo)
    - jogador: (opcional) nome do jogador envolvido
    """
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
        print(f"Erro ao registrar movimentação: {e}")
