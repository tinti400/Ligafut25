import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

# 🔐 Inicialização via st.secrets (modo Cloud seguro)
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

# ✅ Verificação de login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state.id_time
nome_time = st.session_state.nome_time

st.markdown(f"<h1 style='text-align: center;'>🏪 Mercado de Transferências</h1><hr>", unsafe_allow_html=True)

# 🔄 Carrega jogadores no mercado
try:
    mercado_ref = db.collection("mercado_transferencias").stream()
    jogadores = [{"id": doc.id, **doc.to_dict()} for doc in mercado_ref]
except Exception as e:
    st.error(f"Erro ao buscar jogadores do mercado: {e}")
    st.stop()

if not jogadores:
    st.info("📭 Nenhum jogador disponível no mercado.")
    st.stop()

# 📋 Exibição estilo planilha
st.markdown("### Jogadores disponíveis")
for jogador in jogadores:
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
        if st.button("Comprar", key=f"comprar_{jogador['id']}"):
            valor = jogador["valor"]

            time_ref = db.collection("times").document(id_time)
            dados_time = time_ref.get().to_dict()
            saldo_atual = dados_time.get("saldo", 0)

            if saldo_atual < valor:
                st.error("❌ Saldo insuficiente para realizar a compra.")
                st.stop()

            # Atualiza saldo do time
            novo_saldo = saldo_atual - valor
            time_ref.update({"saldo": novo_saldo})

            # Adiciona jogador ao elenco do time
            db.collection("times").document(id_time).collection("elenco").add({
                "nome": jogador["nome"],
                "posição": jogador["posição"],
                "overall": jogador["overall"],
                "valor": jogador["valor"]
            })

            # Remove jogador do mercado
            db.collection("mercado_transferencias").document(jogador["id"]).delete()

            st.success(f"{jogador['nome']} comprado com sucesso!")
            st.rerun()
