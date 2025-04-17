# Evento de Multa - Revisado com finalização após tempo do último time
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import random
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Multa", layout="wide")

# Inicializa Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
verificar_login()

st.title("🚨 Evento de Multa - LigaFut")

usuario_id = st.session_state.usuario_id
id_time_usuario = st.session_state.id_time
nome_time = st.session_state.nome_time

evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento = evento_doc.to_dict() if evento_doc.exists else {}

# Inicia evento
if not evento.get("ativo"):
    if st.button("🎲 Iniciar Evento de Multa"):
        times_ref = db.collection("times").stream()
        times = [doc.id for doc in times_ref]
        random.shuffle(times)
        ordem = [{"id_time": t, "inicio": None, "concluido": False, "quantidade": 0} for t in times]
        protecao_fim = datetime.now(timezone.utc) + timedelta(minutes=5)

        evento_ref.set({
            "ativo": True,
            "ordem": ordem,
            "indice_atual": -1,
            "inicio_evento": datetime.now(timezone.utc).isoformat(),
            "protecao_fim": protecao_fim.isoformat(),
            "pendentes_transferencia": [],
            "jogadores_ja_adquiridos": {}
        })

        protecoes_antigas = db.collection("protecao_evento").stream()
        for p in protecoes_antigas:
            dados = p.to_dict()
            if dados.get("bloqueado_proximo"):
                p.reference.update({"bloqueado_proximo": False})

        st.success("Evento de multa iniciado com sucesso. Ordem dos times sorteada!")
        st.rerun()

if not evento.get("ativo"):
    st.info("Nenhum evento de multa ativo no momento.")
    st.stop()

ordem = evento.get("ordem", [])
indice_atual = evento.get("indice_atual", -1)
protecao_fim = datetime.fromisoformat(evento.get("protecao_fim"))
agora = datetime.now(timezone.utc)
jogadores_ja_adquiridos = evento.get("jogadores_ja_adquiridos", {})

# Atualiza times cujo tempo expirou automaticamente
if indice_atual >= 0:
    for i in range(indice_atual, len(ordem)):
        t = ordem[i]
        if t.get("inicio"):
            dt_inicio = datetime.fromisoformat(t["inicio"])
            if agora > dt_inicio + timedelta(minutes=3):
                t["concluido"] = True
                indice_atual += 1
            else:
                break
        else:
            break
    evento_ref.update({"ordem": ordem, "indice_atual": indice_atual})

# Fase de protecao
if indice_atual == -1:
    tempo_restante = max(0, int((protecao_fim - agora).total_seconds()))
    st.subheader(f"⛔️ Fase de proteção - Tempo restante: {tempo_restante} segundos")

    elenco_ref = db.collection("times").document(id_time_usuario).collection("elenco").stream()
    elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]

    protecoes_ref = db.collection("protecao_evento").where("id_time", "==", id_time_usuario).stream()
    protecoes_atuais = [doc.to_dict().get("id_jogador") for doc in protecoes_ref]

    bloqueios_ref = db.collection("protecao_evento").where("bloqueado_proximo", "==", True).stream()
    bloqueados_gerais = [doc.to_dict().get("id_jogador") for doc in bloqueios_ref]

    if tempo_restante == 0:
        evento_ref.update({"indice_atual": 0})
        st.rerun()

    st.markdown("### 🔐 Selecione até 4 jogadores para proteger")
    protegidos = protecoes_atuais[:]

    for jogador in elenco:
        nome = jogador.get("nome")
        id_jogador = jogador.get("id")

        if id_jogador in bloqueados_gerais:
            st.markdown(f"🚫 **{nome}** não pode ser protegido neste evento")
        elif id_jogador in protegidos:
            st.markdown(f"✅ **{nome}** já protegido")
        elif len(protegidos) < 4:
            if st.button(f"Proteger {nome}", key=f"proteger_{id_jogador}"):
                db.collection("protecao_evento").add({
                    "id_time": id_time_usuario,
                    "id_jogador": id_jogador,
                    "data_evento": datetime.now(timezone.utc),
                    "bloqueado_proximo": True
                })
                st.success(f"{nome} protegido!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Ordem sorteada dos times")
    for idx, item in enumerate(ordem):
        nome = db.collection("times").document(item["id_time"]).get().to_dict().get("nome", "Desconhecido")
        st.markdown(f"{idx+1}. 🕒 {nome} - Aguardando")
    st.stop()

# Ação por time
if indice_atual >= 0 and indice_atual < len(ordem):
    time_atual = ordem[indice_atual]
    id_time_vez = time_atual["id_time"]
    inicio_time = time_atual["inicio"]

    if not inicio_time:
        inicio_time = datetime.now(timezone.utc)
        ordem[indice_atual]["inicio"] = inicio_time.isoformat()
        evento_ref.update({"ordem": ordem})
        st.rerun()

    inicio_time = datetime.fromisoformat(inicio_time)
    tempo_expirado = agora > (inicio_time + timedelta(minutes=3))

    if tempo_expirado:
        ordem[indice_atual]["concluido"] = True
        evento_ref.update({"ordem": ordem, "indice_atual": indice_atual + 1})
        st.warning("Tempo esgotado. Avançando para o próximo time...")
        st.rerun()

    st.markdown("### 📋 Ordem sorteada dos times")
    for idx, item in enumerate(ordem):
        nome = db.collection("times").document(item["id_time"]).get().to_dict().get("nome", "Desconhecido")
        status = "🔵 Em ação" if idx == indice_atual else "⚪ Aguardando"
        st.markdown(f"{idx+1}. {nome} - {status}")

    if id_time_usuario == id_time_vez:
        st.success("✅ É sua vez de executar a ação de multa!")

        times_ref = db.collection("times").stream()
        times = {doc.id: doc.to_dict().get("nome") for doc in times_ref if doc.id != id_time_usuario}

        for id_alvo, nome_alvo in times.items():
            elenco_alvo_ref = db.collection("times").document(id_alvo).collection("elenco").stream()
            elenco_alvo = [doc.to_dict() | {"id": doc.id} for doc in elenco_alvo_ref if doc.id not in jogadores_ja_adquiridos]

            st.markdown(f"#### Time: {nome_alvo}")
            for jogador in elenco_alvo:
                nome_jogador = jogador.get("nome")
                valor = jogador.get("valor", 0)
                id_jogador = jogador.get("id")

                protegido = db.collection("protecao_evento").where("id_jogador", "==", id_jogador).where("id_time", "==", id_alvo).get()
                if protegido:
                    st.markdown(f"🚫 {nome_jogador} está protegido")
                    continue

                if st.button(f"💸 Pagar Multa por {nome_jogador} (R$ {valor:,.0f})", key=f"multa_{id_jogador}"):
                    pendente = evento.get("pendentes_transferencia", [])
                    pendente.append({
                        "id_time_origem": id_alvo,
                        "id_time_destino": id_time_usuario,
                        "jogador": jogador,
                        "valor": valor
                    })
                    jogadores_ja_adquiridos[id_jogador] = True
                    ordem[indice_atual]["quantidade"] += 1

                    evento_ref.update({
                        "pendentes_transferencia": pendente,
                        "jogadores_ja_adquiridos": jogadores_ja_adquiridos,
                        "ordem": ordem
                    })
                    st.success(f"✅ {nome_jogador} adquirido com sucesso!")

                    if ordem[indice_atual]["quantidade"] >= 5:
                        evento_ref.update({"indice_atual": indice_atual + 1})
                        st.info("✅ Limite atingido! Avançando para o próximo time.")
                    st.rerun()

# Finaliza evento
if indice_atual >= len(ordem):
    st.success("Evento de multa encerrado! Processando transferências...")
    pendentes = evento.get("pendentes_transferencia", [])
    for mov in pendentes:
        jogador = mov["jogador"]
        valor = mov["valor"]
        id_origem = mov["id_time_origem"]
        id_destino = mov["id_time_destino"]

        db.collection("times").document(id_destino).collection("elenco").add(jogador)
        db.collection("times").document(id_origem).collection("elenco").document(jogador["id"]).delete()

        saldo_origem = db.collection("times").document(id_origem).get().to_dict().get("saldo", 0)
        saldo_destino = db.collection("times").document(id_destino).get().to_dict().get("saldo", 0)

        db.collection("times").document(id_destino).update({"saldo": saldo_destino - valor})
        db.collection("times").document(id_origem).update({"saldo": saldo_origem + valor})

        registrar_movimentacao(db, id_destino, "multa_compra", jogador["nome"], valor)
        registrar_movimentacao(db, id_origem, "multa_venda", jogador["nome"], valor)

    evento_ref.update({"ativo": False})
    st.success("🔄 Todas transferências processadas com sucesso!")
    st.rerun()
