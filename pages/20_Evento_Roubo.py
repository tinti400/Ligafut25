import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime
from utils import verificar_login

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

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

st.title("🕵️ Evento de Roubo - LigaFut")

# Verifica se o usuário é administrador
usuario = st.session_state.get("usuario_logado", "")
admin_ref = db.collection("admins").document(usuario).get()
eh_admin = admin_ref.exists

evento_ref = db.collection("configuracoes").document("evento_roubo")
evento_doc = evento_ref.get()
evento_dados = evento_doc.to_dict() if evento_doc.exists else {}

evento_ativo = evento_dados.get("ativo", False)
inicio = evento_dados.get("inicio", None)

# Botão para iniciar o evento (apenas para admins)
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not evento_ativo:
        if st.button("🚨 Iniciar Evento de Roubo"):
            evento_ref.set({
                "ativo": True,
                "inicio": datetime.now(),
            })
            st.success("Evento de roubo iniciado com sucesso!")
            st.rerun()
    else:
        st.info("✅ Evento de roubo já está ativo.")

# Exibição do status do evento
st.markdown("---")
if evento_ativo:
    st.success("🟢 Evento de roubo está ATIVO.")
    if inicio:
        st.markdown(f"📅 Iniciado em: **{inicio.strftime('%d/%m/%Y %H:%M:%S')}**")
    st.info("⚠️ O evento está em andamento. Aguarde seu momento de ação.")
else:
    st.warning("🔒 O evento de roubo ainda **não foi iniciado**.")
