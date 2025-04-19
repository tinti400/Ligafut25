from datetime import datetime

def registrar_movimentacao(db, id_time, tipo, descricao, valor, data=None):
    """
    Registra uma movimentação financeira no time informado.
    
    Parâmetros:
    - db: referência do Firestore
    - id_time: ID do time
    - tipo: 'entrada' ou 'saida'
    - descricao: descrição da movimentação
    - valor: valor da movimentação
    - data: opcional – string formatada ou será gerada automaticamente
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

