import streamlit as st
from google.oauth2 import service_account
import google.cloud.firestore as gc_firestore
import pandas as pd
from utils import registrar_movimentacao

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

# 🔐 Firebase
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

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state.usuario_id
id_time = st.session_state.id_time
nome_time = st.session_state.nome_time
email_usuario = st.session_state.get("usuario", "")

# 👑 Verifica se é admin
admin_ref = db.collection("admins").document(email_usuario).get()
eh_admin = admin_ref.exists

# ⚙️ Configuração do mercado
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

# 💰 Saldo
saldo_time = db.collection("times").document(id_time).get().to_dict().get("saldo", 0)
st.title("🛒 Mercado de Transferências")
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# 🔍 Filtros
st.markdown("### 🔍 Filtros de Pesquisa")
col1, col2, col3, col4 = st.columns([3, 3, 3, 3])
with col1:
    filtro_nome = st.text_input("Nome do jogador").strip().lower()
with col2:
    filtro_posicao = st.selectbox("Posição", [
        "Todas",
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
with col3:
    filtro_valor = st.slider("Valor máximo (R$)", 0, 300_000_000, 300_000_000, step=1_000_000)
with col4:
    filtro_ordenacao = st.selectbox("Ordenar por", [
        "Padrão", "Maior Overall", "Menor Overall", "Maior Valor", "Menor Valor"
    ])

# Corrige erro na primeira execução
filtros_aplicados = st.session_state.get("filtros_aplicados", {})
filtro_nome_old = filtros_aplicados.get("nome", "")
filtro_posicao_old = filtros_aplicados.get("posicao", "Todas")
filtro_valor_old = filtros_aplicados.get("valor", 300_000_000)
filtro_ordenacao_old = filtros_aplicados.get("ordenacao", "Padrão")

mudou_filtro = (
    filtro_nome != filtro_nome_old or
    filtro_posicao != filtro_posicao_old or
    filtro_valor != filtro_valor_old or
    filtro_ordenacao != filtro_ordenacao_old
)

if mudou_filtro:
    st.session_state["pagina_mercado"] = 1
    st.session_state["filtros_aplicados"] = {
        "nome": filtro_nome,
        "posicao": filtro_posicao,
        "valor": filtro_valor,
        "ordenacao": filtro_ordenacao
    }

# 🔍 Busca jogadores
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
    if filtro_nome and filtro_nome not in j.get("nome", "").lower():
        continue
    if filtro_posicao != "Todas" and j.get("posicao") != filtro_posicao:
        continue
    if j.get("valor", 0) > filtro_valor:
        continue
    jogadores_filtrados.append(j)

# 🔃 Ordenação
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

# 🔄 Navegação
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

        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])
        with col1:
            st.markdown(f"**👤 {nome}** ({posicao}) - {nacionalidade}")
            st.markdown(f"Origem: `{time_origem}`")
        with col2:
            st.markdown(f"⭐ Overall: **{overall}**")
        with col3:
            st.markdown(f"💰 Valor: **R$ {valor:,.0f}**".replace(",", "."))
        with col4:
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
                                "nacionalidade": nacionalidade
                            })
                            db.collection("times").document(id_time).update({"saldo": saldo_time - valor})
                            registrar_movimentacao(db, id_time, "saida", "Compra no mercado", valor, jogador=nome)
                            st.success(f"{nome} comprado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na compra: {e}")
            else:
                st.markdown("🔒 Mercado Fechado")
        with col5:
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
    mov_ref = db.collection("times").document(id_time).collection("movimentacoes").order_by("timestamp", direction=gc_firestore.Query.DESCENDING).stream()
    historico = []
    for doc in mov_ref:
        d = doc.to_dict()
        historico.append({
            "Tipo": d.get("tipo"),
            "Jogador": d.get("jogador", "N/A"),
            "Valor": f"R$ {d.get('valor', 0):,.0f}".replace(",", ".")
        })

    if not historico:
        st.info("Nenhuma movimentação registrada.")
    else:
        df_hist = pd.DataFrame(historico)
        st.dataframe(df_hist, use_container_width=True)
