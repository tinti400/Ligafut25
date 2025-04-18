import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime
from utils import verificar_login, registrar_movimentacao
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

verificar_login()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("🕵️ Evento de Roubo - LigaFut")

# Verifica se é admin
admin_ref = db.collection("admins").document(id_usuario).get()
eh_admin = admin_ref.exists

# Busca configuração do evento
evento_ref = db.collection("configuracoes").document("evento_roubo")
evento_doc = evento_ref.get()
evento = evento_doc.to_dict() if evento_doc.exists else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "bloqueio")
ordem = evento.get("ordem", [])
vez = evento.get("vez", 0)
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})

# ---------------------- ADMIN ----------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        if st.button("🚀 Iniciar Evento de Roubo"):
            try:
                times_ref = db.collection("times").stream()
                ordem = [doc.id for doc in times_ref]
                random.shuffle(ordem)
                evento_ref.set({
                    "ativo": True,
                    "inicio": datetime.utcnow(),
                    "fase": "acao",
                    "ordem": ordem,
                    "bloqueios": {},
                    "roubos": {},
                    "vez": 0,
                    "concluidos": [],
                    "ja_perderam": {},
                    "finalizado": False
                })
                st.success("Evento iniciado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")
    else:
        if st.button("🛑 Encerrar Evento"):
            try:
                evento_ref.update({"ativo": False, "finalizado": True})
                st.success("Evento encerrado.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao encerrar: {e}")

# ---------------------- STATUS ----------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase: {fase.upper()}")

    # FASE ÚNICA - AÇÃO
    if fase == "acao":
        st.subheader("🎯 Ordem e Vez Atual")
        for i, tid in enumerate(ordem):
            nome = db.collection("times").document(tid).get().to_dict().get("nome", "Desconhecido")
            if tid in concluidos:
                st.markdown(f"🟢 {nome}")
            elif i == vez:
                st.markdown(f"🟡 {nome} (vez atual)")
            else:
                st.markdown(f"⚪ {nome}")

        if vez < len(ordem):
            id_vez = ordem[vez]
            if id_time == id_vez:
                st.success("É sua vez! Escolha jogadores para roubar (pagar 50% do valor).")
                st.markdown("Escolha um time adversário:")

                times_ref = db.collection("times").stream()
                for tdoc in times_ref:
                    tid = tdoc.id
                    if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                        continue

                    nome_t = tdoc.to_dict().get("nome", "Desconhecido")
                    with st.expander(f"📂 {nome_t}"):
                        elenco_ref = db.collection("times").document(tid).collection("elenco").stream()
                        for jogador in elenco_ref:
                            j = jogador.to_dict()
                            nome = j.get("nome", "Desconhecido")
                            posicao = j.get("posicao", "Desconhecida")
                            valor = j.get("valor", 0)

                            # Verifica se esse jogador já foi roubado por outro time
                            ja_roubado = any(
                                nome == rob.get("nome") and rob.get("de") == tid
                                for r in roubos.values() for rob in r
                            )
                            if ja_roubado:
                                continue

                            bloqueado = any(nome == b.get("nome") for b in bloqueios.get(tid, []))
                            if bloqueado:
                                st.markdown(f"🔒 {nome} - {posicao} (R$ {valor:,.0f})")
                            else:
                                if st.button(f"Roubar {nome} (R$ {valor/2:,.0f})", key=f"{tid}_{nome}"):
                                    novo = roubos.get(id_time, [])
                                    novo.append({"nome": nome, "posicao": posicao, "valor": valor, "de": tid})
                                    roubos[id_time] = novo
                                    ja_perderam[tid] = ja_perderam.get(tid, 0) + 1
                                    evento_ref.update({"roubos": roubos, "ja_perderam": ja_perderam})
                                    st.success(f"{nome} selecionado para roubo!")
                                    st.rerun()

                if len(roubos.get(id_time, [])) >= 5:
                    st.info("Você já fez os 5 roubos permitidos.")
                if st.button("✅ Finalizar minha vez"):
                    concluidos.append(id_time)
                    evento_ref.update({"concluidos": concluidos, "vez": vez + 1})
                    st.rerun()
            elif eh_admin:
                if st.button("⏭️ Pular vez do time atual"):
                    evento_ref.update({"vez": vez + 1})
                    st.rerun()

    # FINALIZADO
    if evento.get("finalizado"):
        st.success("✅ Evento finalizado. Veja o resumo:")
        for tid, acoes in roubos.items():
            nome_t = db.collection("times").document(tid).get().to_dict().get("nome", "Desconhecido")
            st.markdown(f"### 🟦 {nome_t} roubou:")
            for j in acoes:
                nome_vendido = db.collection("times").document(j['de']).get().to_dict().get("nome", "")
                st.markdown(f"- {j['nome']} ({j['posicao']}) do time {nome_vendido}")
                try:
                    db.collection("times").document(j['de']).collection("elenco").where("nome", "==", j['nome']).get()[0].reference.delete()
                    db.collection("times").document(tid).collection("elenco").add({
                        "nome": j["nome"],
                        "posicao": j["posicao"],
                        "valor": j["valor"]  # entra com valor total no elenco
                    })
                    saldo_de = db.collection("times").document(j['de']).get().to_dict().get("saldo", 0)
                    saldo_para = db.collection("times").document(tid).get().to_dict().get("saldo", 0)
                    metade = j["valor"] / 2
                    db.collection("times").document(j['de']).update({"saldo": saldo_de + metade})
                    db.collection("times").document(tid).update({"saldo": saldo_para - metade})
                    registrar_movimentacao(db, tid, j['nome'], "Roubo", "Compra", metade)
                except Exception as e:
                    st.error(f"Erro ao transferir {j['nome']}: {e}")
else:
    st.warning("🔒 Evento de roubo não está ativo.")
