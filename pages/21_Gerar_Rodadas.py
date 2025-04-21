import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime
import random

st.set_page_config(page_title="Gerar Rodadas - LigaFut", layout="centered")

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

# ✅ Verifica se o usuário é admin pelo e-mail
usuario_email = st.session_state.get("usuario", "")
admin_ref = db.collection("admins").document(usuario_email).get()

if not admin_ref.exists:
    st.warning("🔒 Acesso restrito a administradores.")
    st.stop()

# 🎯 ID da Liga
id_liga = "VUnsRMAPOc9Sj9n5BenE"
colecao_rodadas = f"ligas/{id_liga}/rodadas_divisao_1"

st.markdown("<h2 style='text-align: center;'>🗖️ Gerar Rodadas Estilo Brasileirão</h2><hr>", unsafe_allow_html=True)
st.warning("⚠️ Isso irá apagar todas as rodadas atuais e gerar um novo calendário completo.")

if st.button("🧐 Gerar Rodadas Automáticas"):
    try:
        # Apaga rodadas anteriores
        for doc in db.collection(colecao_rodadas).stream():
            doc.reference.delete()

        # Busca times
        times_ref = db.collection("times").stream()
        times = [(doc.id, doc.to_dict().get("nome", "Time")) for doc in times_ref]
        ids_times = [t[0] for t in times]

        def gerar_turno(times_ids):
            random.shuffle(times_ids)
            n = len(times_ids)
            rodadas = []

            if n % 2 != 0:
                times_ids.append(None)

            for i in range(n - 1):
                rodada = []
                for j in range(len(times_ids) // 2):
                    t1 = times_ids[j]
                    t2 = times_ids[-(j + 1)]
                    if t1 and t2:
                        rodada.append({"mandante": t1, "visitante": t2})
                times_ids = [times_ids[0]] + [times_ids[-1]] + times_ids[1:-1]
                rodadas.append(rodada)

            return rodadas

        # Turno e returno
        turno = gerar_turno(ids_times)
        returno = [[{"mandante": j["visitante"], "visitante": j["mandante"]} for j in r] for r in turno]
        todas_rodadas = turno + returno

        for i, rodada in enumerate(todas_rodadas, start=1):
            db.collection(colecao_rodadas).document(f"rodada_{i}").set({
                "numero": i,
                "jogos": rodada,
                "criado_em": datetime.utcnow()
            })

        st.success(f"✅ {len(todas_rodadas)} rodadas geradas com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao gerar rodadas: {e}")
