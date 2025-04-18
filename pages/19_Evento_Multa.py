import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime, timedelta
from utils import verificar_login

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Inicializa Firebase
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

# ✅ Verifica login
verificar_login()

st.title("🚨 Evento de Multa - LigaFut")

# Verifica se o usuário é administrador
usuario = st.session_state.get("usuario_logado", "")
admin_ref = db.collection("admins").document(usuario).get()
eh_admin = admin_ref.exists

# 🔄 Buscar times
times_ref = db.collection("times").stream()
times_dict = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

# 🔄 Buscar dados do evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento_dados = evento_doc.to_dict() if evento_doc.exists else {}

evento_ativo = evento_dados.get("ativo", False)
inicio = evento_dados.get("inicio")
ordem_ids = evento_dados.get("ordem", [])
vez_atual = evento_dados.get("vez_atual", 0)
tempo_inicio_vez = evento_dados.get("tempo_inicio_vez")
bloqueios = evento_dados.get("bloqueios", {})
jogadores_roubados = evento_dados.get("jogadores_roubados", {})
times_indisponiveis = evento_dados.get("times_indisponiveis", [])

# Converte timestamps
if hasattr(inicio, "to_datetime"):
    inicio = inicio.to_datetime().replace(tzinfo=None)
if hasattr(tempo_inicio_vez, "to_datetime"):
    tempo_inicio_vez = tempo_inicio_vez.to_datetime().replace(tzinfo=None)

# 👑 Painel do ADM
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not evento_ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            import random
            nova_ordem = list(times_dict.keys())
            random.shuffle(nova_ordem)
            evento_ref.set({
                "ativo": True,
                "inicio": datetime.now(),
                "ordem": nova_ordem,
                "vez_atual": 0,
                "tempo_inicio_vez": datetime.now(),
                "bloqueios": {},
                "jogadores_roubados": {},
                "times_indisponiveis": []
            })
            st.success("✅ Evento iniciado com sucesso!")
            st.rerun()
    else:
        if st.button("⏭️ Pular vez do time atual"):
            evento_ref.update({
                "vez_atual": vez_atual + 1,
                "tempo_inicio_vez": datetime.now()
            })
            st.warning("⏭️ Vez pulada.")
            st.rerun()

# 📋 Status do Evento
st.markdown("---")
if evento_ativo:
    st.success("🟢 Evento de multa está ATIVO.")
    agora = datetime.now()

    nomes_ordem = []
    for i, tid in enumerate(ordem_ids):
        nome = times_dict.get(tid, tid)
        status = ""
        if i < vez_atual:
            status = "🟩"
        elif i == vez_atual:
            status = "🟨"
        else:
            status = "⬜"
        nomes_ordem.append(f"{status} {i+1}. {nome}")

    st.markdown("### 📋 Ordem dos Times:")
    for nome in nomes_ordem:
        st.markdown(nome)

    if inicio and agora <= inicio + timedelta(minutes=2):
        restante = (inicio + timedelta(minutes=2)) - agora
        st.warning(f"⏳ Etapa de bloqueio: ainda restam {int(restante.total_seconds())} segundos.")

        if st.session_state.get("id_time") in ordem_ids:
            id_time_usuario = st.session_state["id_time"]
            elenco_ref = db.collection("times").document(id_time_usuario).collection("elenco").stream()
            elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]
            jogadores_bloqueados = bloqueios.get(id_time_usuario, [])
            st.markdown("#### 🛡️ Selecione até 4 jogadores para bloquear:")
            nomes_disponiveis = [j["nome"] for j in elenco if j["nome"] not in jogadores_bloqueados]
            bloqueios_input = st.multiselect("Jogadores:", options=nomes_disponiveis, default=jogadores_bloqueados)

            if st.button("💾 Salvar bloqueios"):
                if len(bloqueios_input) > 4:
                    st.warning("❌ Você só pode bloquear até 4 jogadores.")
                else:
                    bloqueios[id_time_usuario] = bloqueios_input
                    evento_ref.update({"bloqueios": bloqueios})
                    st.success("✅ Bloqueios salvos!")
                    st.rerun()

    else:
        if vez_atual < len(ordem_ids):
            time_vez_id = ordem_ids[vez_atual]
            nome_vez = times_dict.get(time_vez_id, "Desconhecido")
            st.markdown(f"### 🎯 É a vez do time: **{nome_vez}**")

            # Verifica tempo de vez
            if tempo_inicio_vez and (agora - tempo_inicio_vez) > timedelta(minutes=3):
                evento_ref.update({
                    "vez_atual": vez_atual + 1,
                    "tempo_inicio_vez": datetime.now()
                })
                st.warning("⏳ Tempo expirado. Pulando vez automaticamente.")
                st.rerun()
        else:
            st.success("🏁 Evento finalizado.")
else:
    st.warning("🔒 O evento de multa ainda **não foi iniciado**.")
