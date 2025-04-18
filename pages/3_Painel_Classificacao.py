import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore

st.set_page_config(page_title="Rodadas - LigaFut", layout="wide")

# 🔐 Inicializa Firebase
if "firebase" not in st.session_state:
    try:
        cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
        db = gc_firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
        st.session_state["firebase"] = db
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        st.stop()
else:
    db = st.session_state["firebase"]

st.markdown("<h1 style='text-align: center;'>🏟️ Resultados das Rodadas</h1><hr>", unsafe_allow_html=True)

# 📋 Lista os times
times_ref = db.collection("times").stream()
times_dict = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

# 🔁 Lista e ordena as rodadas
rodadas_ref = db.collection_group("rodadas_divisao_1").stream()
rodadas = sorted(rodadas_ref, key=lambda r: r.to_dict().get("numero", 0))

for rodada_doc in rodadas:
    rodada_data = rodada_doc.to_dict()
    numero_rodada = rodada_data.get("numero", "?")
    jogos = rodada_data.get("jogos", [])

    st.markdown(f"<h3 style='color:#444;'>📅 Rodada {numero_rodada}</h3>", unsafe_allow_html=True)

    for idx, jogo in enumerate(jogos):
        mandante_id = jogo.get("mandante")
        visitante_id = jogo.get("visitante")
        gols_mandante = jogo.get("gols_mandante", 0)
        gols_visitante = jogo.get("gols_visitante", 0)

        nome_mandante = times_dict.get(mandante_id, "Time A")
        nome_visitante = times_dict.get(visitante_id, "Time B")

        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
        with col1:
            st.markdown(f"**{nome_mandante}**")
        with col2:
            gm = st.number_input(" ", min_value=0, step=1, value=gols_mandante, key=f"{rodada_doc.id}_{idx}_gm")
        with col3:
            st.markdown("**x**")
        with col4:
            gv = st.number_input("  ", min_value=0, step=1, value=gols_visitante, key=f"{rodada_doc.id}_{idx}_gv")
        with col5:
            st.markdown(f"**{nome_visitante}**")

        salvar_col = st.columns(5)[2]
        with salvar_col:
            if st.button("💾 Salvar", key=f"salvar_{rodada_doc.id}_{idx}"):
                try:
                    jogos[idx]["gols_mandante"] = gm
                    jogos[idx]["gols_visitante"] = gv
                    rodada_doc.reference.update({"jogos": jogos})
                    st.success("✅ Resultado salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
