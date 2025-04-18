import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
from datetime import datetime

st.set_page_config(page_title="🚨 Evento de Multa", layout="wide")

# 🔐 Inicializa Firebase com st.secrets
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

# ✅ Verifica login
verificar_login()

# 📌 Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("🚨 Evento de Multa")
st.markdown(f"### 👤 Time: {nome_time}")

#⚙️ Buscar times disponíveis
times_ref = db.collection("times").stream()
times = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

# Mostrar elenco dos outros times
for time_id, time_nome in times.items():
    if time_id == id_time:
        continue

    with st.expander(f"⚽ Time: {time_nome}"):
        elenco_ref = db.collection("times").document(time_id).collection("elenco").stream()
        elenco = [doc.to_dict() | {"id_doc": doc.id} for doc in elenco_ref]

        if not elenco:
            st.write("Este time não possui jogadores cadastrados.")
        else:
            for jogador in elenco:
                nome = jogador.get("nome", "Desconhecido")
                posicao = jogador.get("posição", "-")
                overall = jogador.get("overall", "N/A")
                valor = jogador.get("valor", 0)

                col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 2, 2])
                with col1:
                    st.markdown(f"**🎯 {nome}**")
                with col2:
                    st.markdown(f"**Posição:** {posicao}")
                with col3:
                    st.markdown(f"⭐ {overall}")
                with col4:
                    st.markdown(f"💰 R$ {valor:,.0f}".replace(",", "."))

                with col5:
                    if st.button(f"🔓 Pagar Multa", key=f"multa_{jogador['id_doc']}"):
                        try:
                            saldo_time_ref = db.collection("times").document(id_time)
                            saldo = saldo_time_ref.get().to_dict().get("saldo", 0)

                            if saldo < valor:
                                st.error("❌ Saldo insuficiente para pagar a multa.")
                            else:
                                # 💸 Debita do comprador
                                novo_saldo = saldo - valor
                                saldo_time_ref.update({"saldo": novo_saldo})

                                # 💰 Credita no vendedor
                                saldo_time_ref_destino = db.collection("times").document(time_id)
                                saldo_destino = saldo_time_ref_destino.get().to_dict().get("saldo", 0)
                                saldo_time_ref_destino.update({"saldo": saldo_destino + valor})

                                # 👋 Remove jogador do elenco anterior
                                db.collection("times").document(time_id).collection("elenco").document(jogador["id_doc"]).delete()

                                # ✅ Insere jogador no novo time
                                db.collection("times").document(id_time).collection("elenco").add({
                                    "nome": nome,
                                    "posição": posicao,
                                    "overall": overall,
                                    "valor": valor
                                })

                                st.success(f"✅ Jogador {nome} foi transferido com sucesso por multa!")
                                st.rerun()

                        except Exception as e:
                            st.error(f"Erro ao concluir transferência: {e}")
