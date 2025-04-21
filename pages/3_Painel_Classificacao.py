import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login, calcular_classificacao
from datetime import datetime

st.set_page_config(page_title="Classificação - LigaFut", layout="wide")

# Firebase
if "firebase" not in st.session_state:
    cred = service_account.Credentials.from_service_account_info(st.secrets["firebase"])
    db = firestore.Client(credentials=cred, project=st.secrets["firebase"]["project_id"])
    st.session_state["firebase"] = db
else:
    db = st.session_state["firebase"]

verificar_login()

id_liga = "VUnsRMAPOc9Sj9n5BenE"
colecao_rodadas = f"ligas/{id_liga}/rodadas_divisao_1"
colecao_times = "times"

st.title("📊 Tabela de Classificação")

# Carrega rodadas ordenadas
rodadas = db.collection(colecao_rodadas).order_by("numero").stream()
rodadas = [r.to_dict() for r in rodadas]

# Busca nomes dos times
times_ref = db.collection(colecao_times).stream()
times_dict = {doc.id: doc.to_dict().get("nome", "Desconhecido") for doc in times_ref}

if not rodadas:
    st.warning("⚠️ Nenhuma rodada encontrada.")
    st.stop()

rodada_atual = rodadas[-1]  # Última rodada
st.subheader(f"📅 Resultados da Rodada {rodada_atual['numero']}")

jogos = rodada_atual.get("jogos", [])

gols_mandante = []
gols_visitante = []

for i, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f"**{times_dict.get(jogo['mandante'], 'Desconhecido')}**")
    with col2:
        gols_m = st.number_input("Gols", key=f"gm_{i}", min_value=0, value=jogo.get("gols_mandante", 0))
    with col3:
        st.markdown("x")
    with col4:
        gols_v = st.number_input(" ", key=f"gv_{i}", min_value=0, value=jogo.get("gols_visitante", 0))
    with col5:
        st.markdown(f"**{times_dict.get(jogo['visitante'], 'Desconhecido')}**")

    gols_mandante.append(gols_m)
    gols_visitante.append(gols_v)

# Botão para salvar
if st.button("💾 Salvar Resultados e Atualizar Classificação"):
    try:
        for i, jogo in enumerate(jogos):
            jogo["gols_mandante"] = gols_mandante[i]
            jogo["gols_visitante"] = gols_visitante[i]

        doc_ref = db.collection(colecao_rodadas).document(f"rodada_{rodada_atual['numero']}")
        doc_ref.update({"jogos": jogos})

        st.success("✅ Resultados salvos com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar os resultados: {e}")

# Classificação
st.markdown("---")
st.subheader("🏆 Classificação Atualizada")

classificacao = calcular_classificacao(rodadas, times_dict)

if not classificacao:
    st.warning("⚠️ Nenhuma classificação disponível.")
else:
    st.dataframe(classificacao, use_container_width=True)
