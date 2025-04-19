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

# 👑 Verifica se é admin
admin_ref = db.collection("admins").document(id_usuario).get()
eh_admin = admin_ref.exists

# 💵 Saldo do time
saldo_time = db.collection("times").document(id_time).get().to_dict().get("saldo", 0)
st.title("Mercado de Transferências")
st.markdown(f"### Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# 🔎 Filtros
st.markdown("### Filtros")
col1, col2, col3 = st.columns(3)
with col1:
    filtro_nome = st.text_input("Nome do jogador").strip().lower()
with col2:
    filtro_posicao = st.selectbox("Posição", ["Todas", "GL", "LD", "ZAG", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"])
with col3:
    filtro_valor = st.slider("Valor máximo (R$)", 0, 300_000_000, 300_000_000, step=1_000_000)

# 🔢 Paginação
if "pagina_mercado" not in st.session_state:
    st.session_state["pagina_mercado"] = 1

col_pag1, col_pag2, col_pag3 = st.columns([1, 1, 5])
with col_pag1:
    if st.button("Anterior", disabled=st.session_state["pagina_mercado"] <= 1):
        st.session_state["pagina_mercado"] -= 1
with col_pag2:
    if st.button("Próxima"):
        st.session_state["pagina_mercado"] += 1

# 📦 Busca jogadores do mercado
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

# 📄 Paginação
por_pagina = 20
total_paginas = max(1, (len(jogadores_filtrados) + por_pagina - 1) // por_pagina)
pagina = st.session_state["pagina_mercado"]
pagina = max(1, min(pagina, total_paginas))
inicio = (pagina - 1) * por_pagina
fim = inicio + por_pagina
jogadores_exibidos = jogadores_filtrados[inicio:fim]

st.markdown(f"#### Mostrando página {pagina} de {total_paginas} | Total de jogadores: {len(jogadores_filtrados)}")

# 📝 Exibição
if not jogadores_exibidos:
    st.info("Nenhum jogador disponível com os filtros selecionados.")
else:
    for j in jogadores_exibidos:
        nome = j.get("nome", "Desconhecido")
        posicao = j.get("posicao", "Desconhecida")
        overall = j.get("overall", "N/A")
        valor = j.get("valor", 0)
        time_origem = j.get("time_origem", "N/A")
        nacionalidade = j.get("nacionalidade", "N/A")

        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2, 1, 2, 2, 1, 1, 1])
        with col1:
            st.write(nome)
        with col2:
            st.write(posicao)
        with col3:
            st.write(overall)
        with col4:
            st.write(f"R$ {valor:,.0f}".replace(",", "."))
        with col5:
            st.write(time_origem)
        with col6:
            st.write(nacionalidade)
        with col7:
            if st.button("Comprar", key=f"comprar_{j['id_doc']}"):
                if saldo_time < valor:
                    st.error("Saldo insuficiente.")
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
                        registrar_movimentacao(db, id_time, nome, "Compra", "Mercado", valor)
                        st.success(f"{nome} comprado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na compra: {e}")
        with col8:
            if eh_admin:
                if st.button("Excluir", key=f"excluir_{j['id_doc']}"):
                    try:
                        db.collection("mercado_transferencias").document(j["id_doc"]).delete()
                        st.success(f"{nome} removido do mercado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

# 📜 Histórico de transferências
with st.expander("Ver histórico de transferências"):
    mov_ref = db.collection("times").document(id_time).collection("movimentacoes").order_by("timestamp", direction=gc_firestore.Query.DESCENDING).stream()
    historico = [{"tipo": doc.to_dict().get("tipo"), "jogador": doc.to_dict().get("jogador"), "valor": doc.to_dict().get("valor")} for doc in mov_ref]

    if not historico:
        st.info("Nenhuma movimentação registrada.")
    else:
        df_hist = pd.DataFrame(historico)
        df_hist["valor"] = df_hist["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".")) if not df_hist.empty else "-"
        df_hist.columns = ["Tipo", "Jogador", "Valor"]
        st.dataframe(df_hist, use_container_width=True)

