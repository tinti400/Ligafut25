with st.form("form_leiloar"):
    jogador_escolhido = st.selectbox(
        "Escolha o jogador para leiloar:",
        options=elenco,
        format_func=lambda x: f"{x.get('nome', 'Desconhecido')} ({x.get('posicao') or x.get('posição', 'Sem posição')})"
    )

    valor_base = jogador_escolhido.get("valor", 0)
    valor_padrao = max(valor_base, 100_000)

    valor_minimo = st.number_input("💰 Lance mínimo inicial (R$)", min_value=100_000, value=valor_padrao, step=100_000)
    duracao = st.slider("⏱️ Duração do leilão (minutos)", min_value=1, max_value=10, value=2)
    botao_leiloar = st.form_submit_button("🚀 Iniciar Leilão")

if botao_leiloar and jogador_escolhido:
    try:
        fim = datetime.utcnow() + timedelta(minutes=duracao)

        dados_leilao = {
            "jogador": {
                "nome": jogador_escolhido.get("nome", ""),
                "posicao": jogador_escolhido.get("posicao") or jogador_escolhido.get("posição", "Sem posição"),
                "overall": jogador_escolhido.get("overall", 0),
                "valor": valor_minimo
            },
            "valor_atual": valor_minimo,
            "valor_inicial": valor_minimo,
            "time_vencedor": "",
            "id_time_atual": id_time,
            "ativo": True,
            "fim": fim
        }

        db.collection("configuracoes").document("leilao_sistema").set(dados_leilao)

        db.collection("times").document(id_time).collection("elenco").document(jogador_escolhido["id_doc"]).delete()

        st.success("✅ Jogador enviado para o leilão com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao iniciar leilão: {e}")
