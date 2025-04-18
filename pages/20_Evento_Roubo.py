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
        if st.button("🚨 Iniciar Evento de Roubo"):
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
                st.success("Evento de roubo iniciado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")
    else:
        if st.button("🛑 Encerrar Evento de Roubo"):
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
                        elenco = db.collection("times").document(tid).collection("elenco").stream()
                        for jogador in elenco:
                            j = jogador.to_dict()
                            if 'nome' not in j or 'posicao' not in j:
                                continue

                            # Verifica se já foi roubado por outro
                            ja_roubado = any(j['nome'] == r['nome'] for rlist in roubos.values() for r in rlist)
                            if ja_roubado:
                                continue

                            bloqueado = any(j['nome'] == b.get('nome') for b in bloqueios.get(tid, []))
                            if bloqueado:
                                st.markdown(f"🔒 {j['nome']} - {j['posicao']} (R$ {j.get('valor', 0):,.0f})")
                            else:
                                preco = j.get("valor", 0) * 0.5
                                if st.button(f"Roubar {j['nome']} por R$ {preco:,.0f}", key=f"{tid}_{j['nome']}"):
                                    novo = roubos.get(id_time, [])
                                    novo.append({
                                        "nome": j['nome'],
                                        "posicao": j['posicao'],
                                        "valor": j.get("valor", 0),  # entra com valor integral
                                        "de": tid
                                    })
                                    roubos[id_time] = novo
                                    ja_perderam[tid] = ja_perderam.get(tid, 0) + 1
                                    evento_ref.update({"roubos": roubos, "ja_perderam": ja_perderam})
                                    st.success(f"Jogador {j['nome']} marcado para roubo.")
                                    st.rerun()

                if st.button("✅ Finalizar minha vez"):
                    concluidos.append(id_time)
                    evento_ref.update({"concluidos": concluidos, "vez": vez + 1})
                    st.rerun()
            elif eh_admin:
                if st.button("⏭️ Pular vez do time atual"):
                    evento_ref.update({"vez": vez + 1})
                    st.rerun()

    # FASE FINAL
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
                    db.collection("times").document(tid).collection("elenco").add(j)

                    valor_inteiro = j["valor"]
                    valor_pago = int(valor_inteiro * 0.5)

                    saldo_de = db.collection("times").document(j['de']).get().to_dict().get("saldo", 0)
                    saldo_para = db.collection("times").document(tid).get().to_dict().get("saldo", 0)

                    db.collection("times").document(j['de']).update({"saldo": saldo_de + valor_pago})
                    db.collection("times").document(tid).update({"saldo": saldo_para - valor_pago})

                    registrar_movimentacao(db, tid, j['nome'], "Roubo", "Compra", valor_pago)
                except Exception as e:
                    st.error(f"Erro ao transferir {j['nome']}: {e}")
else:
    st.warning("🔒 Evento de roubo não está ativo.")
