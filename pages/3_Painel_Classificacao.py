import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import pandas as pd

st.set_page_config(page_title="Classificação - LigaFut", layout="wide")

# 🔐 Inicialização do Firestore via st.secrets
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

st.markdown("<h1 style='text-align: center;'>📊 Tabela de Classificação</h1><hr>", unsafe_allow_html=True)

# 🔄 Recupera times
try:
    times_ref = db.collection("times").stream()
    times = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 🧮 Inicializa dados da tabela
tabela = {tid: {
    "Time": nome,
    "P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0
} for tid, nome in times.items()}

# 🔁 Processa rodadas e resultados
try:
    rodadas_ref = db.collection_group("rodadas_divisao_1").stream()
    for doc in rodadas_ref:
        rodada = doc.to_dict()
        jogos = rodada.get("jogos", [])
        for jogo in jogos:
            mandante = jogo["mandante"]
            visitante = jogo["visitante"]
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")

            # Só contabiliza se os dois gols foram informados
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
except Exception as e:
    st.error(f"Erro ao processar rodadas: {e}")
    st.stop()

# Calcula pontos e saldo de gols
for t in tabela.values():
    t["P"] = t["V"] * 3 + t["E"]
    t["SG"] = t["GP"] - t["GC"]

# 🔢 Converte para DataFrame
df = pd.DataFrame(tabela.values())
df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
df.index += 1

# 🎨 Estiliza G4 e Z2
def destaque_linha(row):
    pos = row.name + 1
    if pos <= 4:
        return ["background-color: #d4edda"] * len(row)  # Verde (G4)
    elif pos > len(df) - 2:
        return ["background-color: #f8d7da"] * len(row)  # Vermelho (Z2)
    else:
        return [""] * len(row)

st.dataframe(
    df.style.apply(destaque_linha, axis=1),
    use_container_width=True
)
