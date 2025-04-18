import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import pandas as pd

st.set_page_config(page_title="Rodadas e Classificação - LigaFut", layout="wide")

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

st.markdown("<h1 style='text-align: center;'>⚽ Resultados e Classificação</h1><hr>", unsafe_allow_html=True)

# 🔁 Carrega times
try:
    times_ref = db.collection("times").stream()
    times_dict = {}
    for doc in times_ref:
        times_dict[doc.id] = doc.to_dict().get("nome", "Sem Nome")
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 🔁 Lista e ordena rodadas
try:
    rodadas_ref = db.collection_group("rodadas_divisao_1").stream()
    rodadas = sorted(rodadas_ref, key=lambda r: r.to_dict().get("numero", 0))
except Exception as e:
    st.error(f"Erro ao buscar rodadas: {e}")
    st.stop()

# 📋 Exibe rodadas e resultados com botão de salvar
st.markdown("## 📅 Rodadas")

for rodada_doc in rodadas:
    rodada_data = rodada_doc.to_dict()
    numero_rodada = rodada_data.get("numero", "?")
    jogos = rodada_data.get("jogos", [])

    st.markdown(f"### Rodada {numero_rodada}")

    for idx, jogo in enumerate(jogos):
        mandante_id = jogo.get("mandante")
        visitante_id = jogo.get("visitante")
        gols_mandante = jogo.get("gols_mandante", 0)
        gols_visitante = jogo.get("gols_visitante", 0)

        nome_mandante = times_dict.get(mandante_id, "Time A")
        nome_visitante = times_dict.get(visitante_id, "Time B")

        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 3, 1])
        with col1:
            st.markdown(f"{nome_mandante}")
        with col2:
            gm = st.number_input(" ", min_value=0, step=1, value=gols_mandante, key=f"{rodada_doc.id}_{idx}_gm")
        with col3:
            st.markdown("x")
        with col4:
            gv = st.number_input("  ", min_value=0, step=1, value=gols_visitante, key=f"{rodada_doc.id}_{idx}_gv")
        with col5:
            st.markdown(f"{nome_visitante}")
        with col6:
            if st.button("💾", key=f"salvar_{rodada_doc.id}_{idx}"):
                try:
                    jogos[idx]["gols_mandante"] = gm
                    jogos[idx]["gols_visitante"] = gv
                    rodada_doc.reference.update({"jogos": jogos})
                    st.success("✅ Salvo")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# 📊 Classificação
st.markdown("---")
st.markdown("## 📊 Classificação Atualizada")

tabela = {tid: {
    "Time": nome,
    "P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0
} for tid, nome in times_dict.items()}

for rodada_doc in rodadas:
    rodada_data = rodada_doc.to_dict()
    jogos = rodada_data.get("jogos", [])
    for jogo in jogos:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")

        if gm is not None and gv is not None:
            for time_id in [mandante, visitante]:
                if time_id not in tabela:
                    continue
                tabela[time_id]["J"] += 1

            tabela[mandante]["GP"] += gm
            tabela[mandante]["GC"] += gv
            tabela[visitante]["GP"] += gv
            tabela[visitante]["GC"] += gm

            if gm > gv:
                tabela[mandante]["V"] += 1
                tabela[visitante]["D"] += 1
            elif gv > gm:
                tabela[visitante]["V"] += 1
                tabela[mandante]["D"] += 1
            else:
                tabela[mandante]["E"] += 1
                tabela[visitante]["E"] += 1

# Pontos e SG
for t in tabela.values():
    t["P"] = t["V"] * 3 + t["E"]
    t["SG"] = t["GP"] - t["GC"]

df = pd.DataFrame(tabela.values())
df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
df.index += 1

def estilo(row):
    pos = row.name + 1
    if pos <= 4:
        return ["background-color: #d4edda"] * len(row)
    elif pos > len(df) - 2:
        return ["background-color: #f8d7da"] * len(row)
    return [""] * len(row)

st.dataframe(df.style.apply(estilo, axis=1), use_container_width=True)

