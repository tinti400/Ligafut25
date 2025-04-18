import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime, timedelta
from utils import verificar_login, registrar_movimentacao
import random

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

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

st.title("🚨 Evento de Multa - LigaFut")

# Verifica se é admin
admin_ref = db.collection("admins").document(id_usuario).get()
eh_admin = admin_ref.exists

# Busca configuração do evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento = evento_doc.to_dict() if evento_doc.exists else {}

ativo = evento.get("ativo", False)
inicio_ts = evento.get("inicio")

# Conversão segura do timestamp
if isinstance(inicio_ts, datetime):
    inicio = inicio_ts.replace(tzinfo=None)
elif hasattr(inicio_ts, "to_datetime"):
    inicio = inicio_ts.to_datetime().replace(tzinfo=None)
else:
    inicio = None

# ADMIN
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            try:
                times_ref = db.collection("times").stream()
                ordem = [doc.id for doc in times_ref]
                random.shuffle(ordem)
                evento_ref.set({
                    "ativo": True,
                    "inicio": datetime.utcnow(),
                    "fase": "bloqueio",
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

# STATUS
st.markdown("---")
if ativo:
    fase = evento.get("fase", "bloqueio")
    ordem = evento.get("ordem", [])
    vez = evento.get("vez", 0)
    concluidos = evento.get("concluidos", [])
    bloqueios = evento.get("bloqueios", {})
    ja_perderam = evento.get("ja_perderam", {})
    roubos = evento.get("roubos", {})

    st.success(f"Evento ativo - Fase: {fase.upper()}")

    # FASE 1 - BLOQUEIO
    if fase == "bloqueio":
        st.subheader("⛔ Bloqueie até 4 jogadores do seu elenco")
        elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
        elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref if "nome" in doc.to_dict() and "posicao" in doc.to_dict()]

        bloqueados = bloqueios.get(id_time, [])
        nomes_bloqueados_formatados = [f"{j['nome']} - {j['posicao']}" for j in bloqueados if 'nome' in j and 'posicao' in j]

        opcoes = [f"{j['nome']} - {j['posicao']}" for j in elenco if f"{j['nome']} - {j['posicao']}" not in nomes_bloqueados_formatados]

        default_validos = [v for v in nomes_bloqueados_formatados if v in opcoes]

        escolhidos = st.multiselect(
            "Jogadores para bloquear:",
            options=opcoes,
            default=default_validos,
            max_selections=4
        )

        if st.button("🔒 Salvar bloqueios"):
            novos = [j for j in elenco if f"{j['nome']} - {j['posicao']}" in escolhidos]
            bloqueios[id_time] = novos
            evento_ref.update({"bloqueios": bloqueios})
            st.success("Bloqueios salvos.")
            st.rerun()

        if eh_admin:
            st.markdown("🛠️ Admin: Avance para a fase de ação quando todos terminarem o bloqueio.")
            if st.button("➡️ Avançar para Ação"):
                evento_ref.update({"fase": "acao"})
                st.success("Avançou para fase de ação.")
                st.rerun()

    # FASE 2 - AÇÃO
    elif fase == "acao":
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
                st.success("É sua vez! Escolha jogadores para pagar a multa.")
                st.markdown("Escolha um time adversário:")

                times_ref = db.collection("times").stream()
                for tdoc in times_ref:
                    tid = tdoc.id
                    if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                        continue

                    nome_t = tdoc.to_dict().get("nome", "Desconhecido")
                    with st.expander(f"📂 {nome_t}"):
                        elenco = db.collection("times").document(tid).collection("elenco").stream()
                        for jogador in elenco:
                            j = jogador.to_dict()
                            if 'nome' not in j or 'posicao' not in j:
                                continue

                            # Verifica se já foi selecionado por outro time
                            ja_roubado = any(
                                j["nome"] == r["nome"] and tid == r["de"]
                                for lst in roubos.values() for r in lst
                            )
                            if ja_roubado:
                                continue

                            bloqueado = any(j['nome'] == b.get('nome') for b in bloqueios.get(tid, []))
                            if bloqueado:
                                st.markdown(f"🔒 {j['nome']} - {j['posicao']} (R$ {j.get('valor', 0):,.0f})")
                            else:
                                if st.button(f"Pagar multa por {j['nome']} (R$ {j.get('valor', 0):,.0f})", key=f"{tid}_{j['nome']}"):
                                    novo = roubos.get(id_time, [])
                                    novo.append({
                                        "nome": j['nome'],
                                        "posicao": j['posicao'],
                                        "valor": j.get("valor", 0),
                                        "de": tid
                                    })
                                    roubos[id_time] = novo
                                    ja_perderam[tid] = ja_perderam.get(tid, 0) + 1
                                    evento_ref.update({"roubos": roubos, "ja_perderam": ja_perderam})
                                    st.success(f"Multa registrada por {j['nome']}")
                                    st.rerun()

                if len(roubos.get(id_time, [])) >= 5:
                    st.info("Você já fez as 5 multas permitidas.")
                if st.button("✅ Finalizar minha vez"):
                    concluidos.append(id_time)
                    evento_ref.update({"concluidos": concluidos, "vez": vez + 1})
                    st.rerun()
            elif eh_admin:
                if st.button("⏩ Pular vez do time atual"):
                    evento_ref.update({"vez": vez + 1})
                    st.rerun()

    # FASE 3 - FINALIZADO
    if evento.get("finalizado"):
        st.success("✅ Evento finalizado. Veja o resumo:")
        for tid, acoes in roubos.items():
            nome_t = db.collection("times").document(tid).get().to_dict().get("nome", "Desconhecido")
            st.markdown(f"### 🗭 {nome_t} comprou por multa:")
            for j in acoes:
                nome_vendido = db.collection("times").document(j['de']).get().to_dict().get("nome", "")
                st.markdown(f"- {j['nome']} ({j['posicao']}) do time {nome_vendido}")
                try:
                    db.collection("times").document(j['de']).collection("elenco").where("nome", "==", j['nome']).get()[0].reference.delete()
                    db.collection("times").document(tid).collection("elenco").add(j)
                    saldo_de = db.collection("times").document(j['de']).get().to_dict().get("saldo", 0)
                    saldo_para = db.collection("times").document(tid).get().to_dict().get("saldo", 0)
                    db.collection("times").document(j['de']).update({"saldo": saldo_de + j['valor']})
                    db.collection("times").document(tid).update({"saldo": saldo_para - j['valor']})
                    registrar_movimentacao(db, tid, j['nome'], "Multa", "Compra", j['valor'])
                except Exception as e:
                    st.error(f"Erro ao transferir {j['nome']}: {e}")
else:
    st.warning("🔒 Evento de multa não está ativo.")
