import streamlit as st

st.set_page_config(page_title="LigaFut", layout="centered")

# Estilo visual
st.markdown(
    """
    <style>
        body {
            background-color: #0d1117;
        }
        .main {
            background-color: #0d1117;
            color: white;
        }
        .logo {
            font-size: 48px;
            font-weight: bold;
            color: #00FF99;
            text-align: center;
            margin-bottom: 10px;
        }
        .slogan {
            font-size: 20px;
            text-align: center;
            color: #cccccc;
            margin-bottom: 40px;
        }
        .botao {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Conteúdo centralizado
st.markdown("<div class='logo'>🏆 LigaFut</div>", unsafe_allow_html=True)
st.markdown("<div class='slogan'>Simule qualquer campeonato de futebol com seus amigos</div>", unsafe_allow_html=True)

# Botão para login
if st.button("Entrar"):
    st.switch_page("pages/1_Login.py")

