import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import pandas as pd
from utils import registrar_movimentacao

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

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
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state.usuario_id
id_time = st.session_state.id_time
nome_time = st.session_state.nome_time
email_usuario = st.session_state.get("usuario", "")

# 👑 Verifica se é admin por e-mail
admin_ref = db.collection("admins").document(email_usuario).get()
eh_admin = admin_ref.exists

# ⚙️ Controle de mercado (admin)
mercado_cfg_ref = db.collection("configuracoes").document("mercado")
mercado_doc = mercado_cfg_ref.get()
mercado_aberto = mercado_doc.to_dict().get("aberto", True) if mercado_doc.exists else True

if eh_admin:
    st.sidebar.markdown("## ⚙️ Admin - Controle do Mercado")
    if mercado_aberto:
        if st.sidebar.button("🔒 Fechar Mercado"):
            mercado_cfg_ref.set({"aberto": False}, merge=True)
            st.success("✅ Mercado fechado com sucesso.")
            st.rerun()
    else:
        if st.sidebar.button("🔓 Abrir Mercado"):
            mercado_cfg_ref.set({"aberto": True}, merge=True)
            st.success("✅ Mercado aberto com sucesso.")
            st.rerun()

    if st.sidebar.button("🧹 Limpar Mercado"):
        try:
            docs = db.collection("mercado_transferencias").stream()
            for doc in docs:
                doc.reference.delete()
            st.success("✅ Todos os jogadores foram removidos do mercado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao limpar mercado: {e}")

# 💰 Saldo
saldo_time = db.collection("times").document(id_time).get().to_dict().get("saldo", 0)
st.title("🛒 Mercado de Transferências")
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# 🔍 Filtros
st.markdown("### 🔍 Filtros de Pesquisa")
col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
with col1:
    filtro_nome = st.text_input("Nome do jogador").strip().lower()
with col2:
    filtro_posicao = st.selectbox("Posição", ["Todas", "GL", "LD", "ZAG", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"])
with col3:
    filtro_valor_manual = st.text_input("Valor máximo (R$)", "1000000000")
    try:
        filtro_valor = int(filtro_valor_manual.replace(".", "").replace(",", "").replace("R$", "").strip())
    except:
        filtro_valor = 1_000_000_000
with col4:
    filtro_ordenacao = st.selectbox("Ordenar por", ["Nenhum", "Maior Overall", "Menor Overall", "Maior Valor", "Menor Valor"])

# 📦 Carrega jogadores do mercado
mercado_ref = db.collection("mercado_transferencias").stream()
todos_jogadores = []
for doc in mercado_ref:
    j = doc.to_dict()
    j["id_doc"] = doc.id
    if j.get("nome") and j.get("valor") is not None:
        todos_jogadores.append(j)

# 🎯 Aplica filtros
jogadores_filtrados = []
for j in todos_jogadores:
    if filtro_nome and filtro_nome not in j["nome"].lower():
        continue
    if filtro_posicao != "Todas" and j.get("posicao") != filtro_posicao:
        continue
    if j.get("valor", 0) > filtro_valor:
        continue
    jogadores_filtrados.append(j)

# 📊 Ordenação
if filtro_ordenacao == "Maior Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0), reverse=True)
elif filtro_ordenacao == "Menor Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0))
elif filtro_ordenacao == "Maior Valor":
    jogadores_filtrados.sort(key=lambda x: x.get("valor", 0), reverse=True)
elif filtro_ordenacao == "Menor Valor":
    jogadores_filtrados.sort(key=lambda x: x.get("valor", 0))

# 🔢 Paginação
if "pagina_mercado" not in st.session_state:
    st.session_state["pagina_mercado"] = 1

total_jogadores = len(jogadores_filtrados)
por_pagina = 15
total_paginas = max(1, (total_jogadores + por_pagina - 1) // por_pagina)
pagina = st.session_state["pagina_mercado"]
pagina = max(1, min(pagina, total_paginas))

inicio = (pagina - 1) * por_pagina
fim = inicio + por_pagina
jogadores_pagina = jogadores_filtrados[inicio:fim]

# 🔄 Navegação entre páginas
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    if st.button("⏪ Anterior", disabled=pagina <= 1):
        st.session_state["pagina_mercado"] -= 1
        st.rerun()
with col_nav2:
    st.markdown(f"<p style='text-align: center;'>Página {pagina} de {total_paginas}</p>", unsafe_allow_html=True)
with col_nav3:
    if st.button("⏩ Próxima", disabled=pagina >= total_paginas):
        st.session_state["pagina_mercado"] += 1
        st.rerun()

# 📋 Exibição
if not jogadores_pagina:
    st.info("Nenhum jogador disponível com os filtros selecionados.")
else:
    for j in jogadores_pagina:
        nome = j.get("nome", "Desconhecido")
        posicao = j.get("posicao", "Desconhecida")
        overall = j.get("overall", "N/A")
        valor = j.get("valor", 0)
        time_origem = j.get("time_origem", "N/A")
        nacionalidade = j.get("nacionalidade", "N/A")
        foto = j.get("foto")

        st.markdown("---")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 1])
        with col1:
            if foto:
                st.image(foto, width=60)
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
        with col2:
            st.markdown(f"**👤 {nome}** ({posicao}) - {nacionalidade}")
            st.markdown(f"Origem: `{time_origem}`")
        with col3:
            st.markdown(f"⭐ Overall: **{overall}**")
        with col4:
            st.markdown(f"💰 Valor: **R$ {valor:,.0f}**".replace(",", "."))
        with col5:
            if mercado_aberto:
                if st.button("✅ Comprar", key=f"comprar_{j['id_doc']}"):
                    if saldo_time < valor:
                        st.error("❌ Saldo insuficiente.")
                    else:
                        try:
                            db.collection("mercado_transferencias").document(j["id_doc"]).delete()
                            db.collection("times").document(id_time).collection("elenco").add({
                                "nome": nome,
                                "posicao": posicao,
                                "overall": overall,
                                "valor": valor,
                                "time_origem": time_origem,
                                "nacionalidade": nacionalidade,
                                "foto": foto
                            })
                            db.collection("times").document(id_time).update({"saldo": saldo_time - valor})
                            registrar_movimentacao(db, id_time, "saida", "Compra no mercado", valor)
                            st.success(f"{nome} comprado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na compra: {e}")
            else:
                st.markdown("🔒 Mercado Fechado")

        with col6:
            if eh_admin:
                if st.button("🗑️ Excluir", key=f"excluir_{j['id_doc']}"):
                    try:
                        db.collection("mercado_transferencias").document(j["id_doc"]).delete()
                        st.success(f"{nome} removido do mercado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

# 📜 Histórico
with st.expander("📜 Ver histórico de transferências"):
    mov_ref = db.collection("times").document(id_time).collection("movimentacoes").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    historico = []
    for doc in mov_ref:
        d = doc.to_dict()
        historico.append({
            "Tipo": d.get("tipo"),
            "Descrição": d.get("descricao", "N/A"),
            "Valor": f"R$ {d.get('valor', 0):,.0f}".replace(",", ".")
        })

    if not historico:
        st.info("Nenhuma movimentação registrada.")
    else:
        df_hist = pd.DataFrame(historico)
        st.dataframe(df_hist, use_container_width=True)
