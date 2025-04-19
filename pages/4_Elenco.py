import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login
import pandas as pd

st.set_page_config(page_title="📋 Elenco", layout="wide")

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

# ✅ Verifica login
verificar_login()

# ✅ Garante que sessão tenha time
if "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.error("⚠️ Informações do time não encontradas. Faça login novamente.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📋 Elenco do Clube")
st.markdown(f"### 🏟️ Time: **{nome_time}**")

# 🔍 Busca elenco
elenco_ref = db.collection("times").document(id_time).collection("elenco").stream()
elenco = []
for doc in elenco_ref:
    jogador = doc.to_dict()
    jogador["id_doc"] = doc.id
    jogador["posicao"] = jogador.get("posicao", "Desconhecido")
    jogador["nome"] = jogador.get("nome", "Desconhecido")
    jogador["overall"] = jogador.get("overall", 0)
    jogador["valor"] = jogador.get("valor", 0)
    elenco.append(jogador)

if not elenco:
    st.info("📭 Nenhum jogador no elenco atualmente.")
    st.stop()

# 🔄 Abas
aba = st.tabs(["📋 Lista", "🧠 Formação Tática"])

# =========================
# 📋 ABA 1 - LISTA
# =========================
with aba[0]:
    st.markdown("### 📋 Lista de Jogadores")
    col1, col2, col3 = st.columns([3, 3, 3])
    with col1:
        filtro_nome = st.text_input("Filtrar por nome").strip().lower()
    with col2:
        filtro_posicao = st.selectbox("Filtrar por posição", [
            "Todas",
            "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
            "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
            "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
        ])
    with col3:
        ordenacao = st.selectbox("Ordenar por", ["Maior Overall", "Menor Overall", "Maior Valor", "Menor Valor"])

    filtrado = []
    for jogador in elenco:
        if filtro_nome and filtro_nome not in jogador["nome"].lower():
            continue
        if filtro_posicao != "Todas" and jogador["posicao"] != filtro_posicao:
            continue
        filtrado.append(jogador)

    if ordenacao == "Maior Overall":
        filtrado.sort(key=lambda x: x.get("overall", 0), reverse=True)
    elif ordenacao == "Menor Overall":
        filtrado.sort(key=lambda x: x.get("overall", 0))
    elif ordenacao == "Maior Valor":
        filtrado.sort(key=lambda x: x.get("valor", 0), reverse=True)
    elif ordenacao == "Menor Valor":
        filtrado.sort(key=lambda x: x.get("valor", 0))

    df = pd.DataFrame(filtrado)
    if df.empty:
        st.warning("Nenhum jogador encontrado com os filtros selecionados.")
    else:
        df["valor_formatado"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".") if pd.notnull(x) else "N/A")
        df = df[["posicao", "nome", "overall", "valor_formatado"]]
        df.columns = ["Posição", "Nome", "Overall", "Valor"]
        st.dataframe(df, use_container_width=True)

# =========================
# 🧠 ABA 2 - TÁTICA
# =========================
with aba[1]:
    st.markdown("### 🧠 Formação Tática")

    # Posições da formação padrão 4-3-3
    posicoes_taticas = [
        "GL", "LD", "ZAG1", "ZAG2", "LE",
        "VOL", "MC", "ME",
        "PD", "SA", "PE"
    ]

    nomes_jogadores = [j["nome"] for j in elenco]

    # 🔄 Carrega formação salva se existir
    formacao_salva = db.collection("times").document(id_time).get().to_dict().get("formacao", {})
    formacao = {}

    colunas = st.columns(5)
    for i, pos in enumerate(posicoes_taticas):
        with colunas[i % 5]:
            formacao[pos] = st.selectbox(
                f"{pos}",
                options=[""] + nomes_jogadores,
                index=([""] + nomes_jogadores).index(formacao_salva.get(pos, "")) if formacao_salva.get(pos, "") in nomes_jogadores else 0,
                key=f"form_{pos}"
            )

    if st.button("💾 Salvar Formação"):
        try:
            db.collection("times").document(id_time).update({"formacao": formacao})
            st.success("✅ Formação salva com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar formação: {e}")
