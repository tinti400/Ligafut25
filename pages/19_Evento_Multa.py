import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime, timedelta
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# Firebase
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

# Login
verificar_login()
usuario = st.session_state.get("usuario_logado")
id_time_usuario = st.session_state.get("id_time")
nome_time_usuario = st.session_state.get("nome_time")

# Admin?
admin_ref = db.collection("admins").document(usuario).get()
eh_admin = admin_ref.exists

# Configuração do evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento = evento_doc.to_dict() if evento_doc.exists else {}

ativo = evento.get("ativo", False)
inicio = evento.get("inicio")
bloqueios = evento.get("bloqueios", {})
ordem = evento.get("ordem", [])
vez = evento.get("vez", 0)
concluidos = evento.get("concluidos", {})

# Início
st.title("🚨 Evento de Multa - LigaFut")

# Admin painel
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Iniciar Evento"):
            times = [doc.id for doc in db.collection("times").stream()]
            import random
            random.shuffle(times)
            evento_ref.set({
                "ativo": True,
                "inicio": datetime.now(),
                "bloqueios": {},
                "ordem": times,
                "vez": 0,
                "concluidos": {},
                "transferencias": []
            })
            st.success("Evento iniciado com sucesso!")
            st.rerun()
    with col2:
        if ativo and st.button("⏭️ Pular vez atual"):
            evento_ref.update({"vez": vez + 1})
            st.warning("Vez atual pulada!")
            st.rerun()
    with col3:
        if ativo and st.button("🛑 Encerrar Evento"):
            evento_ref.update({"ativo": False})
            st.success("Evento encerrado!")
            st.rerun()

# Classificação da ordem
st.markdown("---")
st.subheader("📋 Ordem de Participação")
for i, tid in enumerate(ordem):
    cor = "white"
    if concluidos.get(tid, False):
        cor = "#d4edda"
    elif i == vez:
        cor = "#fff3cd"
    nome = db.collection("times").document(tid).get().to_dict().get("nome", "Desconhecido")
    st.markdown(f"<div style='background-color:{cor};padding:6px;border-radius:5px'>{i+1}. {nome}</div>", unsafe_allow_html=True)

# Bloqueio
if ativo and inicio and datetime.now() <= inicio + timedelta(minutes=2):
    st.warning("⏳ Tempo para bloqueio de até 4 jogadores do seu elenco!")
    elenco_ref = db.collection("times").document(id_time_usuario).collection("elenco").stream()
    elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]
    bloqueados = bloqueios.get(id_time_usuario, [])
    nomes = [j["nome"] for j in elenco]
    selecionados = st.multiselect("🔒 Escolha até 4 jogadores para bloquear:", nomes, default=bloqueados)
    if st.button("✅ Salvar bloqueios"):
        evento_ref.update({f"bloqueios.{id_time_usuario}": selecionados[:4]})
        st.success("Bloqueios salvos!")
        st.rerun()

# Execução da vez
elif ativo and vez < len(ordem) and ordem[vez] == id_time_usuario:
    st.success("🟡 É a sua vez! Você pode realizar até 5 ações de multa!")

    # Selecionar time alvo
    times_ref = db.collection("times").stream()
    times_dict = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

    col_time = st.selectbox("🎯 Escolha o time alvo:", [tid for tid in times_dict if tid != id_time_usuario])

    # Elenco alvo
    elenco_ref = db.collection("times").document(col_time).collection("elenco").stream()
    bloqueados = bloqueios.get(col_time, [])

    # Verifica se já perdeu 4 jogadores
    ja_perdeu = sum(1 for t in evento.get("transferencias", []) if t["perdedor"] == col_time)
    if ja_perdeu >= 4:
        st.warning("❌ Este time já perdeu 4 jogadores e não pode mais ser atacado.")
    else:
        st.markdown("---")
        st.markdown("### 👥 Jogadores disponíveis:")
        for doc in elenco_ref:
            jogador = doc.to_dict()
            nome = jogador.get("nome")
            if nome in bloqueados:
                continue
            posicao = jogador.get("posição")
            overall = jogador.get("overall")
            valor = jogador.get("valor")
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                col1.markdown(f"**{nome}**")
                col2.markdown(f"{posicao}")
                col3.markdown(f"⭐ {overall}")
                col4.markdown(f"💰 R$ {valor:,.0f}".replace(",", "."))

                if st.button(f"💥 Multar {nome}", key=f"multa_{doc.id}"):
                    try:
                        # Saldo
                        comprador_ref = db.collection("times").document(id_time_usuario)
                        vendedor_ref = db.collection("times").document(col_time)
                        saldo_comprador = comprador_ref.get().to_dict().get("saldo", 0)
                        if saldo_comprador < valor:
                            st.error("Saldo insuficiente!")
                            st.stop()

                        comprador_ref.update({"saldo": saldo_comprador - valor})
                        saldo_vendedor = vendedor_ref.get().to_dict().get("saldo", 0)
                        vendedor_ref.update({"saldo": saldo_vendedor + valor})

                        # Transferência
                        db.collection("times").document(id_time_usuario).collection("elenco").add(jogador)
                        db.collection("times").document(col_time).collection("elenco").document(doc.id).delete()

                        registrar_movimentacao(id_time_usuario, nome, "Multa", "Compra", valor)
                        registrar_movimentacao(col_time, nome, "Multa", "Venda", valor)

                        # Atualiza lista
                        transferencias = evento.get("transferencias", [])
                        transferencias.append({
                            "comprador": id_time_usuario,
                            "perdedor": col_time,
                            "jogador": nome
                        })
                        evento_ref.update({"transferencias": transferencias})

                        # Marca se completou
                        concluidos[id_time_usuario] = concluidos.get(id_time_usuario, 0) + 1
                        if concluidos[id_time_usuario] >= 5:
                            evento_ref.update({f"concluidos.{id_time_usuario}": 5, "vez": vez + 1})
                        else:
                            evento_ref.update({f"concluidos.{id_time_usuario}": concluidos[id_time_usuario]})

                        st.success(f"✅ Jogador {nome} adquirido via multa!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

# Final do evento
elif ativo and vez >= len(ordem):
    st.success("✅ Evento de multa finalizado com sucesso! Todas as ações foram concluídas.")
    if eh_admin and st.button("🔁 Resetar evento para o próximo uso"):
        evento_ref.set({"ativo": False})
        st.success("Evento resetado com sucesso!")
        st.rerun()
else:
    st.info("🔒 Aguardando sua vez ou o início do evento.")

