import streamlit as st
from google.cloud import firestore
from datetime import datetime

def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar o sistema.")
        st.stop()

def calcular_classificacao(jogos, times_ref):
    tabela = {}

    for time in times_ref:
        tabela[time.id] = {
            "nome": time.to_dict().get("nome", "Desconhecido"),
            "pontos": 0,
            "v": 0,
            "e": 0,
            "d": 0,
            "gp": 0,
            "gc": 0,
            "sg": 0,
        }

    for jogo in jogos:
        mandante = jogo.get("mandante")
        visitante = jogo.get("visitante")
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")

        if None in [mandante, visitante, gm, gv]:
            continue

        gm = int(gm)
        gv = int(gv)

        tabela[mandante]["gp"] += gm
        tabela[mandante]["gc"] += gv
        tabela[mandante]["sg"] += gm - gv

        tabela[visitante]["gp"] += gv
        tabela[visitante]["gc"] += gm
        tabela[visitante]["sg"] += gv - gm

        if gm > gv:
            tabela[mandante]["pontos"] += 3
            tabela[mandante]["v"] += 1
            tabela[visitante]["d"] += 1
        elif gm < gv:
            tabela[visitante]["pontos"] += 3
            tabela[visitante]["v"] += 1
            tabela[mandante]["d"] += 1
        else:
            tabela[mandante]["pontos"] += 1
            tabela[visitante]["pontos"] += 1
            tabela[mandante]["e"] += 1
            tabela[visitante]["e"] += 1

    return sorted(
        tabela.items(),
        key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]),
        reverse=True
    )

def registrar_movimentacao(id_time, jogador, categoria, tipo, valor):
    if valor <= 0:
        st.warning("❗ Valor inválido para movimentação.")
        return

    db = st.session_state["firebase"]
    ref = db.collection("times").document(id_time).collection("movimentacoes")
    ref.add({
        "jogador": jogador,
        "categoria": categoria,
        "tipo": tipo,
        "valor": valor,
        "data": datetime.utcnow()
    })


