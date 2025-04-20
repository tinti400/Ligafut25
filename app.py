import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore

# ⚙️ Configuração da página
st.set_page_config(page_title="LigaFut", page_icon="⚽", layout="wide")

# 🔐 Conecta ao Firebase
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

# 🧠 Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar o sistema.")
    st.stop()

id_usuario = st.session_state["usuario_id"]

# 👑 Verifica se é admin
admin_ref = db.collection("admins").document(id_usuario).get()
eh_admin = admin_ref.exists

# 📋 Menu lateral
st.sidebar.title("📋 LigaFut - Menu")

# Menu comum para todos os usuários logados
st.sidebar.page_link("pages/1_Login.py", label="🔐 Login")
st.sidebar.page_link("pages/3_Painel_Classificacao.py", label="📊 Classificação")
st.sidebar.page_link("pages/4_Elenco.py", label="🧑‍💼 Meu Elenco")
st.sidebar.page_link("pages/5_Mercado_Transferencias.py", label="💰 Mercado")
st.sidebar.page_link("pages/7_Painel_Usuario.py", label="👤 Painel do Usuário")
st.sidebar.page_link("pages/8_Financas.py", label="💵 Finanças")
st.sidebar.page_link("pages/10_Leilao_Sistema.py", label="📣 Leilão em Andamento")
st.sidebar.page_link("pages/11_Negociacoes.py", label="🤝 Negociações")
st.sidebar.page_link("pages/12_Propostas_Recebidas.py", label="📨 Propostas Recebidas")
st.sidebar.page_link("pages/15_Propostas_Enviadas.py", label="📤 Propostas Enviadas")
st.sidebar.page_link("pages/16_Historico_Transferencias.py", label="📜 Histórico de Transferências")
st.sidebar.page_link("pages/17_Leiloar_Jogador.py", label="📤 Leiloar Jogador")
st.sidebar.page_link("pages/19_Evento_Multa.py", label="🚨 Evento de Multa")
st.sidebar.page_link("pages/20_Evento_Roubo.py", label="🕵️ Evento de Roubo")

# Opções exclusivas para administradores
if eh_admin:
    st.sidebar.markdown("---")
    st.sidebar.page_link("pages/6_Admin_Mercado.py", label="⚙️ Admin - Mercado")
    st.sidebar.page_link("pages/13_Admin_Usuarios.py", label="👥 Admin - Usuários")
    st.sidebar.page_link("pages/14_Admin_Times.py", label="🏟️ Admin - Times")
    st.sidebar.page_link("pages/9_Admin_Leilao.py", label="🎯 Admin - Leilão")

# Exibe usuário logado
st.sidebar.markdown("---")
st.sidebar.success(f"Logado como: {st.session_state.get('usuario', 'Desconhecido')}")


