import requests
from bs4 import BeautifulSoup
import pandas as pd

url_base = "https://sofifa.com/players?offset="

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

jogadores = []

# 🔁 Raspando múltiplas páginas (60 jogadores por página)
for offset in range(0, 240, 60):  # 4 páginas = 240 jogadores
    url = url_base + str(offset)
    print(f"Raspando: {url}")
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    linhas = soup.select("table tbody tr")

    for row in linhas:
        try:
            nome_tag = row.select_one("td.col-name a")
            nome = nome_tag.text.strip()
            foto = "https:" + row.select_one("td.col-name img")["data-src"]
            posicao = row.select_one("td.col-name .pos").text.strip()
            overall = row.select_one("td.col-oa").text.strip()
            valor = row.select_one("td.col-vl").text.strip()
            bandeira_tag = row.select_one("td.col-name img.flag")
            nacionalidade = bandeira_tag["title"] if bandeira_tag else "N/A"

            jogadores.append({
                "nome": nome,
                "foto": foto,
                "posicao": posicao,
                "overall": overall,
                "valor": valor,
                "nacionalidade": nacionalidade
            })
        except Exception as e:
            print(f"Erro ao processar jogador: {e}")

# 💾 Exporta para Excel
df = pd.DataFrame(jogadores)
df.to_excel("jogadores_sofifa.xlsx", index=False)
print("✅ Arquivo jogadores_sofifa.xlsx salvo com sucesso!")
