import streamlit as st

st.set_page_config(page_title="LigaFut", layout="wide")

# Estilo visual centralizado com responsividade e fundo escuro
st.markdown("""
    <style>
        body {
            background-color: #0d1117;
        }
        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            height: 80vh;
            color: white;
        }
        .logo {
            font-size: 48px;
            font-weight: bold;
            color: #00FF99;
            margin-bottom: 10px;
        }
        .slogan {
            font-size: 20px;
            text-align: center;
            color: #cccccc;
            margin-bottom: 40px;
        }
        .button-container {
            margin-top: 20px;
        }
    </style>
    <div class='container'>
        <div class='logo'>🏆 LigaFut 2025</div>
        <div class='slogan'>Acesse o menu lateral para navegar pelo sistema.</div>
    </div>
""", unsafe_allow_html=True)

