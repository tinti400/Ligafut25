import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
from datetime import datetime, timedelta

st.set_page_config(page_title="Admin - Leilão", layout="wide")

# 🔐 Inicializa Firebase
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

st.markdown("<h1 style='text-align: center;'>🧑‍⚖️ Administração de Leilão</h1><hr>", unsafe_allow_html=True)

# 📝 Formulário para criar leilão
with st.form("form_leilao"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
    valor_inicial = st.number_input("Valor Inicial (R$)", min_value=100000, step=50000)
    duracao = st.slider("Duração do Leilão (minutos)", min_value=1, max_value=10, value=2)
    botao_criar = st.form_submit_button("Criar Leilão")

# 🔄 Atualiza Firestore com novo leilão
if botao_criar:
    if not nome:
        st.warning("Informe o nome do jogador.")
    else:
        fim = datetime.utcnow() + timedelta(minutes=duracao)
        dados_leilao = {
            "nome": nome,
            "posição": posicao,
            "overall": overall,
            "valor_atual": valor_inicial,
            "valor_inicial": valor_inicial,
            "id_time_atual": None,
            "ultimo_lance": None,
            "ativo": True,
            "fim": fim.isoformat()
        }

        try:
            db.collection("configuracoes").document("leilao_sistema").set(dados_leilao)
            st.success("✅ Leilão criado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao criar leilão: {e}")

# 🔘 Controle de ativação e desativação
st.markdown("---")
st.markdown("### ⚙️ Controle de Leilão")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Ativar Leilão"):
        db.collection("configuracoes").document("leilao_sistema").update({"ativo": True})
        st.success("Leilão ativado.")
        st.rerun()

with col2:
    if st.button("🛑 Desativar Leilão"):
        db.collection("configuracoes").document("leilao_sistema").update({"ativo": False})
        st.success("Leilão desativado.")
        st.rerun()
