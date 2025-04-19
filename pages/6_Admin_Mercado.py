import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore

st.set_page_config(page_title="Admin - Mercado", layout="wide")

# 🔐 Firebase
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

# 👑 Verifica se é admin por e-mail
email_usuario = st.session_state.get("usuario", "")

if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

admin_ref = db.collection("admins").document(email_usuario).get()
eh_admin = admin_ref.exists

if not eh_admin:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧭 Título
st.markdown("<h1 style='text-align: center;'>⚙️ Admin - Mercado de Transferências</h1><hr>", unsafe_allow_html=True)

# 🔓 Status do mercado
config_ref = db.collection("configuracoes").document("mercado")
config_doc = config_ref.get()
mercado_aberto = config_doc.to_dict().get("aberto", False) if config_doc.exists else False

st.markdown(f"### 🛒 Status atual do mercado: **{'Aberto' if mercado_aberto else 'Fechado'}**")

# 🔘 Botões de controle
col1, col2 = st.columns(2)
with col1:
    if st.button("🟢 Abrir Mercado"):
        config_ref.set({"aberto": True}, merge=True)
        st.success("✅ Mercado aberto com sucesso!")
        st.rerun()

with col2:
    if st.button("🔴 Fechar Mercado"):
        config_ref.set({"aberto": False}, merge=True)
        st.success("✅ Mercado fechado com sucesso!")
        st.rerun()

# 📝 Cadastro de jogador no mercado
st.markdown("---")
st.subheader("📥 Adicionar Jogador ao Mercado")

with st.form("form_mercado"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
    valor = st.number_input("Valor (R$)", min_value=100_000, step=50_000)
    time_origem = st.text_input("Time de Origem").strip()
    nacionalidade = st.text_input("Nacionalidade").strip()
    botao = st.form_submit_button("Adicionar ao Mercado")

if botao:
    if not nome:
        st.warning("Digite o nome do jogador.")
    else:
        try:
            db.collection("mercado_transferencias").add({
                "nome": nome,
                "posicao": posicao,
                "overall": overall,
                "valor": valor,
                "time_origem": time_origem if time_origem else "N/A",
                "nacionalidade": nacionalidade if nacionalidade else "N/A"
            })
            st.success(f"✅ {nome} foi adicionado ao mercado!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao adicionar jogador: {e}")
