import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="Administração de Times", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("⚙️ Administração de Times")

# Buscar times da coleção raiz
times_ref = db.collection("times").stream()
times = {doc.id: doc.to_dict() for doc in times_ref}

st.subheader("📋 Times Cadastrados:")

for id_time, dados in times.items():
    with st.expander(f"{dados.get('nome')}"):
        st.write(f"ID do Time: {id_time}")
        saldo = dados.get("saldo", 0)

        novo_nome = st.text_input(f"Editar nome do time:", value=dados.get("nome"), key=f"nome_{id_time}")
        novo_saldo = st.number_input(f"Editar saldo do time:", value=saldo, step=1000000, key=f"saldo_{id_time}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", key=f"salvar_{id_time}"):
                db.collection("times").document(id_time).update({
                    "nome": novo_nome,
                    "saldo": novo_saldo
                })
                st.success("Time atualizado com sucesso!")
                st.rerun()

        with col2:
            if st.button("❌ Excluir Time", key=f"excluir_{id_time}"):
                db.collection("times").document(id_time).delete()
                st.warning("Time excluído!")
                st.rerun()

st.markdown("---")
st.subheader("➕ Adicionar Novo Time")

nome_novo_time = st.text_input("Nome do novo time:")
saldo_novo_time = st.number_input("Saldo inicial:", min_value=0, step=1000000)

if st.button("Cadastrar Novo Time"):
    if nome_novo_time == "":
        st.warning("Digite o nome do time.")
    else:
        novo_time_ref = db.collection("times").document()
        novo_time_ref.set({
            "nome": nome_novo_time,
            "saldo": saldo_novo_time
        })
        st.success("Novo time cadastrado com sucesso!")
        st.rerun()
