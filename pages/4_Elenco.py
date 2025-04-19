import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
from utils import verificar_login, registrar_movimentacao
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

# 🔄 Abas
aba = st.tabs(["📋 Lista", "🧠 Formação Tática"])

# 🔄 Verifica se o mercado está aberto
mercado_doc = db.collection("configuracoes").document("mercado").get()
mercado_aberto = mercado_doc.to_dict().get("aberto", False) if mercado_doc.exists else False

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
    jogador["nacionalidade"] = jogador.get("nacionalidade", "N/A")
    jogador["time_origem"] = jogador.get("time_origem", nome_time)
    elenco.append(jogador)

if not elenco:
    st.info("📭 Nenhum jogador no elenco atualmente.")
    st.stop()

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

    if not filtrado:
        st.warning("Nenhum jogador encontrado com os filtros selecionados.")
    else:
        for jogador in filtrado:
            nome = jogador["nome"]
            posicao = jogador["posicao"]
            overall = jogador["overall"]
            valor = jogador["valor"]
            valor_formatado = f"R$ {valor:,.0f}".replace(",", ".")
            id_doc = jogador["id_doc"]
            origem = jogador.get("time_origem", "N/A")
            nacionalidade = jogador.get("nacionalidade", "N/A")

            col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])
            with col1:
                st.markdown(f"**👤 {nome}** ({posicao})")
                st.markdown(f"🏳️ {nacionalidade}")
                st.markdown(f"🏟️ Origem: `{origem}`")
            with col2:
                st.markdown(f"⭐ {overall}")
            with col3:
                st.markdown(f"💰 {valor_formatado}")
            with col4:
                if mercado_aberto:
                    if st.button("💸 Vender", key=f"vender_{id_doc}"):
                        try:
                            db.collection("times").document(id_time).collection("elenco").document(id_doc).delete()
                            db.collection("mercado_transferencias").add({
                                "nome": nome,
                                "posicao": posicao,
                                "overall": overall,
                                "valor": valor,
                                "time_origem": origem,
                                "nacionalidade": nacionalidade
                            })
                            valor_recebido = int(valor * 0.7)
                            time_doc = db.collection("times").document(id_time).get()
                            saldo_atual = time_doc.to_dict().get("saldo", 0)
                            novo_saldo = saldo_atual + valor_recebido
                            db.collection("times").document(id_time).update({"saldo": novo_saldo})
                            registrar_movimentacao(db, id_time, "entrada", "Venda para o mercado", valor_recebido, jogador=nome)
                            st.success(f"{nome} vendido por R$ {valor_recebido:,.0f}".replace(",", "."))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao vender jogador: {e}")
                else:
                    st.markdown("🔒 Mercado fechado")

# =========================
# 🧠 ABA 2 - TÁTICA
# =========================
with aba[1]:
    st.markdown("### 🧠 Formação Tática")

    posicoes_taticas = [
        "GL", "LD", "ZAG1", "ZAG2", "LE",
        "VOL", "MC", "ME",
        "PD", "SA", "PE"
    ]

    nomes_jogadores = [j["nome"] for j in elenco]
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

