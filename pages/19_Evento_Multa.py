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

# 🔑 Verifica login
verificar_login()

# ⚙️ Informações do usuário
usuario_id = st.session_state.get("usuario_logado")
id_time = st.session_state.get("id_time")
nome_time = st.session_state.get("nome_time")

st.title("🚨 Evento de Multa - LigaFut")

# 👑 Verifica se é admin
admin_ref = db.collection("admins").document(usuario_id).get()
eh_admin = admin_ref.exists

# 🔄 Carrega configurações do evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento_dados = evento_doc.to_dict() if evento_doc.exists else {}

ativo = evento_dados.get("ativo", False)
inicio = evento_dados.get("inicio")
fase = evento_dados.get("fase", "aguardando")
ordem = evento_dados.get("ordem", [])
bloqueios = evento_dados.get("bloqueios", {})
tempo_vez = evento_dados.get("tempo_vez")
jogadores_roubados = evento_dados.get("jogadores_roubados", {})
concluidos = evento_dados.get("concluidos", [])
finalizado = evento_dados.get("finalizado", False)

# 🔁 Atualiza tempo atual
agora = datetime.now()

# 👑 ADMIN: iniciar evento ou encerrar
if eh_admin:
    st.subheader("👑 Painel do Administrador")
    col1, col2 = st.columns(2)
    with col1:
        if not ativo and st.button("🚀 Iniciar Evento de Multa"):
            times = [doc.id for doc in db.collection("times").stream()]
            from random import shuffle
            shuffle(times)
            evento_ref.set({
                "ativo": True,
                "inicio": agora,
                "fase": "bloqueio",
                "ordem": times,
                "bloqueios": {},
                "jogadores_roubados": {},
                "tempo_vez": None,
                "concluidos": [],
                "finalizado": False,
            })
            st.rerun()

    with col2:
        if ativo and not finalizado and st.button("🛑 Finalizar Evento"):
            # Processa as transferências
            for comprador_id, jogadores in jogadores_roubados.items():
                for jogador in jogadores:
                    vendedor_id = jogador.get("id_time_origem")
                    valor = jogador.get("valor")

                    if not vendedor_id or not valor:
                        continue

                    # transfere jogador
                    db.collection("times").document(comprador_id).collection("elenco").add({
                        "nome": jogador.get("nome"),
                        "posição": jogador.get("posição"),
                        "overall": jogador.get("overall"),
                        "valor": valor,
                    })

                    # atualiza saldos
                    comprador_ref = db.collection("times").document(comprador_id)
                    vendedor_ref = db.collection("times").document(vendedor_id)

                    saldo_comprador = comprador_ref.get().to_dict().get("saldo", 0)
                    saldo_vendedor = vendedor_ref.get().to_dict().get("saldo", 0)

                    comprador_ref.update({"saldo": saldo_comprador - valor})
                    vendedor_ref.update({"saldo": saldo_vendedor + valor})

                # remove jogadores do time original após a transferência
                for jogador in jogadores:
                    id_jogador = jogador.get("id_doc")
                    if id_jogador and jogador.get("id_time_origem"):
                        db.collection("times").document(jogador.get("id_time_origem")).collection("elenco").document(id_jogador).delete()

            # Finaliza
            evento_ref.update({"ativo": False, "finalizado": True})
            st.success("✅ Evento finalizado e transferências concluídas!")
            st.rerun()

# 🔍 Exibe status
st.markdown("---")
if not ativo:
    st.warning("🔒 O evento de multa ainda não foi iniciado.")
    st.stop()
if finalizado:
    st.success("✅ Evento finalizado. Todas as transferências foram concluídas.")
    st.stop()

# 🛡️ BLOQUEIOS (fase 1)
if fase == "bloqueio":
    st.info("⏳ Fase de bloqueio: todos os técnicos podem proteger até 4 jogadores.")

    elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
    elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]
    bloqueados = bloqueios.get(id_time, [])

    selecionados = st.multiselect("Selecione até 4 jogadores para bloquear:", [j["nome"] for j in elenco], default=bloqueados)

    if st.button("🔒 Salvar bloqueios"):
        if len(selecionados) > 4:
            st.error("Você só pode bloquear até 4 jogadores.")
        else:
            bloqueios[id_time] = selecionados
            evento_ref.update({"bloqueios": bloqueios})
            st.success("✅ Bloqueios salvos com sucesso.")
            st.rerun()

    # após 2 minutos muda para próxima fase
    if inicio and agora > inicio + timedelta(minutes=2):
        evento_ref.update({"fase": "roubo", "tempo_vez": agora})
        st.rerun()

# 🤺 ROUBO (fase 2)
if fase == "roubo":
    st.markdown("### 🕵️ Fase de roubo: cada time pode roubar até 5 jogadores!")

    # lista os nomes dos times
    nomes = {}
    for tid in ordem:
        doc = db.collection("times").document(tid).get()
        nomes[tid] = doc.to_dict().get("nome", "Sem Nome")

    atual_id = ordem[len(concluidos)] if len(concluidos) < len(ordem) else None
    cor_status = lambda tid: (
        "background-color: #fff3cd" if tid == atual_id else
        ("background-color: #d4edda" if tid in concluidos else "")
    )

    for tid in ordem:
        st.markdown(f"<div style='{cor_status(tid)}; padding:5px; border-radius:5px; margin-bottom:3px'>🧾 {nomes.get(tid, tid)}</div>", unsafe_allow_html=True)

    # ADM pode pular vez
    if eh_admin and atual_id and st.button("⏭️ Pular vez"):
        evento_ref.update({
            "tempo_vez": agora,
            "concluidos": firestore.ArrayUnion([atual_id])
        })
        st.rerun()

    if id_time == atual_id:
        st.success("🎯 É a sua vez! Selecione os jogadores para roubar.")

        # monta lista de times disponíveis (que ainda não perderam 4)
        roubos_totais = {}
        for jogs in jogadores_roubados.values():
            for j in jogs:
                tid = j.get("id_time_origem")
                if tid:
                    roubos_totais[tid] = roubos_totais.get(tid, 0) + 1

        times_disp = [tid for tid in nomes if roubos_totais.get(tid, 0) < 4]

        time_alvo = st.selectbox("Selecione um time para visualizar o elenco:", times_disp, format_func=lambda x: nomes.get(x, x))
        if time_alvo:
            elenco_ref = db.collection("times").document(time_alvo).collection("elenco").stream()
            bloqueados_alvo = bloqueios.get(time_alvo, [])
            disponiveis = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref if doc.to_dict().get("nome") not in bloqueados_alvo]

            for jogador in disponiveis:
                nome = jogador.get("nome")
                pos = jogador.get("posição")
                overall = jogador.get("overall")
                valor = jogador.get("valor")

                st.markdown(f"<div style='border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:8px;'>
                <b>{nome}</b> - {pos} - ⭐ {overall} - 💰 R$ {valor:,.0f} <br>
                <form action='' method='post'>
                <button name='roubar_{jogador['id_doc']}' type='submit'>🔁 Roubar jogador</button>
                </form>
                </div>", unsafe_allow_html=True)

                if st.button(f"⚡ Roubar {nome}", key=f"roubar_{jogador['id_doc']}"):
                    if len(jogadores_roubados.get(id_time, [])) >= 5:
                        st.error("Limite de 5 jogadores roubados atingido!")
                    else:
                        jogador["id_time_origem"] = time_alvo
                        jogadores_roubados.setdefault(id_time, []).append(jogador)
                        evento_ref.update({"jogadores_roubados": jogadores_roubados})
                        st.success(f"✅ Jogador {nome} roubado com sucesso!")
                        st.rerun()

        # após 3 min ou todos os 5 roubados, passa vez
        tempo_vez = tempo_vez if isinstance(tempo_vez, datetime) else tempo_vez.to_datetime() if tempo_vez else agora
        if (agora - tempo_vez) > timedelta(minutes=3) or len(jogadores_roubados.get(id_time, [])) >= 5:
            evento_ref.update({
                "tempo_vez": agora,
                "concluidos": firestore.ArrayUnion([id_time])
            })
            st.rerun()

