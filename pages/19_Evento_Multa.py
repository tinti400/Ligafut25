import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime, timedelta
from utils import verificar_login

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# Inicializa Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

# Verifica login
verificar_login()

usuario_id = st.session_state.get("usuario_id")
id_time = st.session_state.get("id_time")
nome_time = st.session_state.get("nome_time")

st.title("🚨 Evento de Multa - LigaFut")

# Verifica se o usuário é administrador
usuario = st.session_state.get("usuario_logado", "")
admin_ref = db.collection("admins").document(usuario).get()
eh_admin = admin_ref.exists

# Referência do evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento_dados = evento_doc.to_dict() if evento_doc.exists else {}

evento_ativo = evento_dados.get("ativo", False)
inicio = evento_dados.get("inicio", None)
ordem = evento_dados.get("ordem", [])
bloqueios = evento_dados.get("bloqueios", {})
jogadores_perdidos = evento_dados.get("jogadores_perdidos", {})
vez_atual = evento_dados.get("vez_atual", 0)
tempo_inicio_vez = evento_dados.get("tempo_inicio_vez")

# ADMIN - painel
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not evento_ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            times_ref = db.collection("times").stream()
            ordem_sorteada = sorted([doc.id for doc in times_ref])
            evento_ref.set({
                "ativo": True,
                "inicio": datetime.now(),
                "ordem": ordem_sorteada,
                "vez_atual": 0,
                "tempo_inicio_vez": datetime.now(),
                "bloqueios": {},
                "jogadores_perdidos": {}
            })
            st.success("Evento de multa iniciado com sucesso!")
            st.rerun()
    else:
        if st.button("⏭️ Pular Vez do Técnico Atual"):
            if vez_atual + 1 < len(ordem):
                evento_ref.update({
                    "vez_atual": vez_atual + 1,
                    "tempo_inicio_vez": datetime.now()
                })
                st.success("Vez pulada com sucesso!")
                st.rerun()
        if st.button("🛑 Encerrar Evento de Multa"):
            evento_ref.update({"ativo": False})
            st.success("Evento encerrado!")
            st.rerun()

# Status
st.markdown("---")
if evento_ativo:
    st.success("🟢 Evento de multa está ATIVO.")
    if inicio:
        st.markdown(f"📅 Iniciado em: **{inicio.strftime('%d/%m/%Y %H:%M:%S')}**")
    st.markdown(f"📋 Ordem definida: **{ordem}**")

    # Bloqueio de jogadores
    if datetime.now() <= inicio + timedelta(minutes=2):
        st.markdown("## ⛔ Bloqueie até 4 jogadores do seu time")
        if id_time not in bloqueios:
            elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
            elenco = [doc.to_dict() for doc in elenco_ref]
            opcoes = [jogador["nome"] for jogador in elenco]
            bloqueados = st.multiselect("Escolha até 4 jogadores para bloquear:", opcoes)
            if st.button("🔒 Confirmar Bloqueio"):
                if len(bloqueados) <= 4:
                    evento_ref.update({f"bloqueios.{id_time}": bloqueados})
                    st.success("Bloqueios registrados!")
                    st.rerun()
                else:
                    st.warning("Você só pode bloquear até 4 jogadores.")
        else:
            st.info("✅ Você já bloqueou seus jogadores neste evento.")
    else:
        # Fase de ações (compra por multa)
        if vez_atual < len(ordem):
            time_da_vez = ordem[vez_atual]
            nome_time_vez = db.collection("times").document(time_da_vez).get().to_dict().get("nome", "Desconhecido")
            st.markdown(f"## 🎯 Vez de: **{nome_time_vez}**")

            # Verifica se passou 3 min da vez
            agora = datetime.now()
            if tempo_inicio_vez and hasattr(tempo_inicio_vez, 'to_datetime'):
                tempo_inicio_vez = tempo_inicio_vez.to_datetime()
            if tempo_inicio_vez and (agora - tempo_inicio_vez) > timedelta(minutes=3):
                if vez_atual + 1 < len(ordem):
                    evento_ref.update({
                        "vez_atual": vez_atual + 1,
                        "tempo_inicio_vez": datetime.now()
                    })
                    st.warning("⏱️ Tempo esgotado. Passando para o próximo técnico...")
                    st.rerun()

            if time_da_vez == id_time:
                st.markdown("### 🛒 Jogadores disponíveis para compra (por multa)")
                lista_jogadores_disponiveis = []
                times_ref = db.collection("times").stream()
                for time in times_ref:
                    tid = time.id
                    if tid == id_time:
                        continue
                    if jogadores_perdidos.get(tid, 0) >= 4:
                        continue
                    elenco_ref = db.collection("times").document(tid).collection("elenco").stream()
                    bloqueados_do_time = bloqueios.get(tid, [])
                    for jogador_doc in elenco_ref:
                        jogador = jogador_doc.to_dict()
                        if jogador.get("nome") not in bloqueados_do_time:
                            lista_jogadores_disponiveis.append({
                                "nome": jogador.get("nome"),
                                "valor": jogador.get("valor"),
                                "posicao": jogador.get("posicao"),
                                "id_time_origem": tid,
                                "id_doc": jogador_doc.id
                            })

                for j in lista_jogadores_disponiveis:
                    st.markdown(f"**{j['nome']} ({j['posicao']})** - R$ {j['valor']:,.0f}".replace(",", "."))
                    if st.button(f"💰 Comprar por multa", key=f"comprar_{j['id_doc']}"):
                        saldo_time = db.collection("times").document(id_time).get().to_dict().get("saldo", 0)
                        if j["valor"] > saldo_time:
                            st.warning("Saldo insuficiente!")
                        else:
                            db.collection("times").document(j["id_time_origem"]).collection("elenco").document(j["id_doc"]).delete()
                            db.collection("times").document(id_time).collection("elenco").add({
                                "nome": j["nome"],
                                "posicao": j["posicao"],
                                "overall": 0,
                                "valor": j["valor"]
                            })
                            # Ajusta saldos
                            db.collection("times").document(id_time).update({"saldo": saldo_time - j["valor"]})
                            saldo_origem = db.collection("times").document(j["id_time_origem"]).get().to_dict().get("saldo", 0)
                            db.collection("times").document(j["id_time_origem"]).update({"saldo": saldo_origem + j["valor"]})

                            # Atualiza jogadores perdidos
                            perdidos = jogadores_perdidos.get(j["id_time_origem"], 0) + 1
                            evento_ref.update({
                                f"jogadores_perdidos.{j['id_time_origem']}": perdidos
                            })
                            st.success("Transferência concluída!")
                            st.rerun()

        else:
            st.success("🎉 Evento finalizado! Todos os técnicos passaram pela vez.")
else:
    st.warning("🔒 O evento de multa ainda **não foi iniciado**.")
