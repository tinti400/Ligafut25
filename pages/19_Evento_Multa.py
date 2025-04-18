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

st.title("🚨 Evento de Multa - LigaFut")

# Verifica se o usuário é administrador
usuario = st.session_state.get("usuario_logado", "")
admin_ref = db.collection("admins").document(usuario).get()
eh_admin = admin_ref.exists

# Referência ao evento
evento_ref = db.collection("configuracoes").document("evento_multa")
evento_doc = evento_ref.get()
evento_dados = evento_doc.to_dict() if evento_doc.exists else {}

evento_ativo = evento_dados.get("ativo", False)
inicio = evento_dados.get("inicio")
ordem = evento_dados.get("ordem", [])
vez_idx = evento_dados.get("vez_idx", 0)
protegidos = evento_dados.get("protegidos", {})
tempo_inicio_vez = evento_dados.get("tempo_inicio_vez")

# Admin inicia ou encerra evento
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    col1, col2 = st.columns(2)
    with col1:
        if not evento_ativo:
            if st.button("🚀 Iniciar Evento de Multa"):
                # sorteia ordem dos times
                times_ref = db.collection("times").stream()
                times_ids = [doc.id for doc in times_ref]
                import random
                random.shuffle(times_ids)
                evento_ref.set({
                    "ativo": True,
                    "inicio": datetime.now(),
                    "ordem": times_ids,
                    "vez_idx": 0,
                    "tempo_inicio_vez": datetime.now(),
                    "protegidos": {}
                })
                st.success("Evento de multa iniciado com sucesso!")
                st.rerun()
    with col2:
        if evento_ativo:
            if st.button("🛑 Encerrar Evento de Multa"):
                evento_ref.update({"ativo": False})
                st.success("Evento encerrado!")
                st.rerun()

# Exibe status
st.markdown("---")
if evento_ativo:
    st.success("🟢 Evento de multa está ATIVO.")
    if inicio:
        st.markdown(f"📅 Iniciado em: **{inicio.strftime('%d/%m/%Y %H:%M:%S')}**")

    # Exibe ordem
    st.markdown("### 🧩 Ordem dos Times")
    for idx, tid in enumerate(ordem):
        time_doc = db.collection("times").document(tid).get()
        nome = time_doc.to_dict().get("nome", "Desconhecido")
        if idx == vez_idx:
            st.markdown(f"➡️ **{nome}** (agora)")
        else:
            st.markdown(f"{idx+1}. {nome}")

    # Avança a vez após 3 minutos automaticamente
    if tempo_inicio_vez:
        if isinstance(tempo_inicio_vez, str):
            tempo_inicio_vez = datetime.fromisoformat(tempo_inicio_vez)
        agora = datetime.now()
        if (agora - tempo_inicio_vez) > timedelta(minutes=3):
            if vez_idx < len(ordem) - 1:
                evento_ref.update({
                    "vez_idx": vez_idx + 1,
                    "tempo_inicio_vez": agora
                })
                st.rerun()
            else:
                evento_ref.update({"ativo": False})
                st.warning("🔚 Evento finalizado! Todos os times passaram.")
                st.rerun()

    # Se é a vez do usuário, permite proteger jogadores
    id_time = st.session_state.get("id_time", "")
    if ordem and ordem[vez_idx] == id_time:
        st.markdown("### 🛡️ Proteja até 4 jogadores do seu time")
        elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
        elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]

        jogadores_antigos = evento_dados.get("protegidos_anteriores", {}).get(id_time, [])

        nomes_disponiveis = [j["nome"] for j in elenco if j["nome"] not in jogadores_antigos]
        selecionados = st.multiselect("Escolha os jogadores a proteger:", nomes_disponiveis, max_selections=4)

        if st.button("✅ Confirmar Proteção"):
            protegidos[id_time] = selecionados
            evento_ref.update({"protegidos": protegidos})
            st.success("Jogadores protegidos!")
            st.rerun()
else:
    st.warning("🔒 O evento de multa ainda **não foi iniciado**.")

