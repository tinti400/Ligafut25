import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Inicializa Firebase com secrets (compatível com Streamlit Cloud)
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

# 🚧 Verifica se o usuário está logado
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.markdown(
        """
        <div style='background-color: #ffcccc; padding: 20px; border-radius: 10px; text-align: center;'>
            <h4 style='color: red;'>🚫 Você precisa estar logado para acessar esta página.</h4>
            <p style='color: black;'>Retorne à tela de login e entre com suas credenciais.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# 🧠 Dados do usuário logado
usuario_id = st.session_state.usuario_id
id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

# 🏷️ Título
st.markdown(f"<h2 style='text-align: center;'>📋 Elenco do {nome_time}</h2><hr>", unsafe_allow_html=True)

# 🔄 Busca elenco do Firebase
try:
    elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
    elenco = [doc.to_dict() | {"id": doc.id} for doc in elenco_ref]
except Exception as e:
    st.error(f"Erro ao buscar elenco: {e}")
    st.stop()

if not elenco:
    st.info("📭 Nenhum jogador cadastrado no elenco.")
    st.stop()

# 📊 Exibição estilo planilha
st.markdown("---")
for jogador in elenco:
    col1, col2, col3, col4, col5 = st.columns([1.2, 3, 1.2, 2, 1.5])

    with col1:
        st.markdown(f"**{jogador.get('posição', '-')[:3]}**")
    with col2:
        st.markdown(f"**{jogador.get('nome', '-')}**")
    with col3:
        st.markdown(f"⭐ {jogador.get('overall', 0)}")
    with col4:
        valor_formatado = f"R$ {jogador.get('valor', 0):,.0f}".replace(",", ".")
        st.markdown(f"💰 {valor_formatado}")
    with col5:
        if st.button("Vender", key=f"vender_{jogador['id']}"):
            valor_total = jogador["valor"]
            valor_recebido = int(valor_total * 0.7)

            time_ref = db.collection("times").document(id_time)
            saldo_atual = time_ref.get().to_dict().get("saldo", 0)
            time_ref.update({"saldo": saldo_atual + valor_recebido})

            db.collection("mercado_transferencias").add(jogador)
            db.collection("times").document(id_time).collection("elenco").document(jogador["id"]).delete()

            registrar_movimentacao(db, id_time, "venda_mercado", jogador["nome"], valor_recebido)

            st.success(f"{jogador['nome']} vendido por R$ {valor_recebido:,.0f}".replace(",", "."))
            st.rerun()
