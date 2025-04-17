import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="Administração de Usuários", layout="wide")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("👥 Administração de Usuários")

usuarios = []

# Buscar usuários na raiz do Firestore
usuarios_ref = db.collection("usuarios").stream()
for doc in usuarios_ref:
    data = doc.to_dict()
    usuarios.append({
        "email": data.get("usuario"),  # Campo correto no seu banco
        "id_time": data.get("id_time"),
        "nome_time": data.get("nome_time", "Não Vinculado"),
        "doc_id": doc.id
    })

# Buscar todos os times na raiz do Firestore
times_ref = db.collection("times").stream()
times = {doc.id: doc.to_dict().get("nome", "Sem Nome") for doc in times_ref}

# Interface
if usuarios:
    emails = [u["email"] for u in usuarios if u["email"] is not None]
    email_selecionado = st.selectbox("Selecione o usuário para editar:", emails)

    usuario = next((u for u in usuarios if u["email"] == email_selecionado), None)

    if usuario:
        st.write(f"📧 **Email:** {usuario['email']}")
        st.write(f"🆔 **ID Time Atual:** {usuario['id_time']}")
        st.write(f"⚽ **Nome Time Atual:** {usuario['nome_time']}")

        if times:
            novo_id_time = st.selectbox(
                "Selecione o novo time:",
                list(times.keys()),
                format_func=lambda x: times[x]
            )

            if st.button("✅ Atualizar Time do Usuário"):
                db.collection("usuarios").document(usuario["doc_id"]).update({
                    "id_time": novo_id_time,
                    "nome_time": times[novo_id_time]
                })
                st.success("Usuário atualizado com sucesso!")
                st.rerun()
        else:
            st.warning("⚠️ Nenhum time encontrado.")
else:
    st.warning("⚠️ Nenhum usuário encontrado.")

st.divider()
st.subheader("📋 Times Cadastrados:")

for id_time, nome_time in times.items():
    st.write(f"🆔 {id_time} | 🏷️ {nome_time}")
