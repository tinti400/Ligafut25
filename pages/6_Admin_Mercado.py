import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore

st.set_page_config(page_title="Admin - Mercado", layout="wide")

# 🔐 Inicializa Firebase com st.secrets
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = gc_firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

# 🔒 Verifica se é admin
id_usuario = st.session_state.get("usuario_id", "")
admin_ref = db.collection("admins").document(id_usuario).get()
if not admin_ref.exists:
    st.warning("🔒 Acesso restrito apenas para administradores.")
    st.stop()

st.markdown("<h1 style='text-align: center;'>⚙️ Admin - Mercado de Transferências</h1><hr>", unsafe_allow_html=True)

# 📝 Formulário de cadastro de jogador
with st.form("form_mercado"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
    valor = st.number_input("Valor (R$)", min_value=100000, step=50000)

    time_origem = st.text_input("Time de Origem").strip()
    nacionalidade = st.text_input("Nacionalidade").strip()

    botao = st.form_submit_button("Adicionar ao Mercado")

# 💾 Envia jogador ao Firestore
if botao:
    if not nome:
        st.warning("Digite o nome do jogador.")
    else:
        try:
            jogador = {
                "nome": nome,
                "posicao": posicao,
                "overall": overall,
                "valor": valor,
                "time_origem": time_origem if time_origem else "Desconhecido",
                "nacionalidade": nacionalidade if nacionalidade else "Desconhecida"
            }
            db.collection("mercado_transferencias").add(jogador)
            st.success(f"✅ {nome} foi adicionado ao mercado!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao adicionar jogador: {e}")
