if aceitar:
    jogador_id = proposta.get("id_jogador")
    jogador_data = proposta.get("jogador")
    novo_valor = proposta.get("valor_proposta", jogador_data.get("valor", 0))

    # Atualiza o valor do jogador antes da transferência
    jogador_data["valor"] = novo_valor

    # 🔁 Transferência de saldo
    doc_comprador = db.collection("times").document(time_origem_id).get()
    doc_vendedor = db.collection("times").document(id_time_logado).get()
    saldo_comprador = doc_comprador.to_dict().get("saldo", 0)
    saldo_vendedor = doc_vendedor.to_dict().get("saldo", 0)

    if saldo_comprador < novo_valor:
        st.error("❌ O time comprador não tem saldo suficiente.")
    else:
        # Atualiza saldos
        db.collection("times").document(time_origem_id).update({
            "saldo": saldo_comprador - novo_valor
        })
        db.collection("times").document(id_time_logado).update({
            "saldo": saldo_vendedor + novo_valor
        })

        # Registra movimentações
        registrar_movimentacao(db, time_origem_id, jogador_data["nome"], "Saída", "Transferência", novo_valor)
        registrar_movimentacao(db, id_time_logado, jogador_data["nome"], "Entrada", "Transferência", novo_valor)

        # Remove jogador do time atual
        db.collection("times").document(id_time_logado).collection("elenco").document(jogador_id).delete()

        # Adiciona jogador ao comprador
        db.collection("times").document(time_origem_id).collection("elenco").add(jogador_data)

        # Transfere jogadores oferecidos (se houver)
        for j_oferecido in jogadores_oferecidos:
            id_oferecido = j_oferecido.get("id_doc")
            j_oferecido.pop("id_doc", None)
            db.collection("times").document(time_origem_id).collection("elenco").document(id_oferecido).delete()
            db.collection("times").document(id_time_logado).collection("elenco").add(j_oferecido)

        # Atualiza proposta
        db.collection("negociacoes").document(proposta["id_doc"]).update({
            "status": "aceita",
            "valor_aceito": novo_valor
        })

        st.success("✅ Proposta aceita com sucesso!")
        st.rerun()
