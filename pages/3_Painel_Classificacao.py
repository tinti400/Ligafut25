import random
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime

# 🔐 Conecta ao Firebase usando st.secrets
if "firebase" not in st.session_state:
    cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
    db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
    st.session_state["firebase"] = db
else:
    db = st.session_state["firebase"]

# ID da liga
id_liga = "VUnsRMAPOc9Sj9n5BenE"
colecao_rodadas = f"ligas/{id_liga}/rodadas_divisao_1"

# Apaga todas as rodadas anteriores
for doc in db.collection(colecao_rodadas).stream():
    doc.reference.delete()

# Pega os times
times_ref = db.collection("times").stream()
times = [(doc.id, doc.to_dict().get("nome", "Time")) for doc in times_ref]
ids_times = [t[0] for t in times]

def gerar_turno(times_ids):
    random.shuffle(times_ids)
    n = len(times_ids)
    rodadas = []

    if n % 2 != 0:
        times_ids.append(None)  # Adiciona um "bye" se número ímpar

    for i in range(n - 1):
        rodada = []
        for j in range(len(times_ids) // 2):
            t1 = times_ids[j]
            t2 = times_ids[-(j + 1)]
            if t1 is not None and t2 is not None:
                rodada.append({"mandante": t1, "visitante": t2})
        times_ids = [times_ids[0]] + [times_ids[-1]] + times_ids[1:-1]
        rodadas.append(rodada)

    return rodadas

# Gera turno e returno
turno = gerar_turno(ids_times)
returno = [[{"mandante": jogo["visitante"], "visitante": jogo["mandante"]} for jogo in rodada] for rodada in turno]

todas_rodadas = turno + returno

# Salva no Firestore
for i, jogos in enumerate(todas_rodadas, start=1):
    doc_ref = db.collection(colecao_rodadas).document(f"rodada_{i}")
    doc_ref.set({
        "numero": i,
        "jogos": jogos,
        "criado_em": datetime.utcnow()
    })

st.success(f"✅ {len(todas_rodadas)} rodadas geradas com sucesso.")
