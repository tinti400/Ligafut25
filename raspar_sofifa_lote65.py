import requests
from bs4 import BeautifulSoup
import pandas as pd

# Configurações
URL_BASE = "https://sofifa.com/players"
HEADERS = {"User-Agent": "Mozilla/5.0"}
jogadores = []
offsets = list(range(0, 300, 60))  # Raspando até 300 jogadores

for offset in offsets:
    url = f"{URL_BASE}?offset={offset}"
    print(f"🔄 Raspando: {url}")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    linhas = soup.select("table tbody tr")

    for row in linhas:
        overall = int(row.select_one("td.col.col-oa").text.strip())
        if overall != 65:
            continue

        nome = row.select_one("td.col-name a").text.strip()
        posicao = row.select_one("td.col-name span.pos").text.strip()
        time_tag = row.select("td.col-name a")[1] if len(row.select("td.col-name a")) > 1 else None
        time_origem = time_tag.text.strip() if time_tag else "Sem clube"

        # Liga no link (para filtrar)
        link_time = time_tag["href"] if time_tag else ""
        if any(excluida in link_time.lower() for excluida in ["libertadores", "sudamericana"]):
            continue

        nacionalidade = row.select_one("td.col-name img")["title"].strip()
        foto = "https:" + row.select_one("td.col-name img")["src"]
        valor_raw = row.select_one("td.col.col-vl").text.strip().replace("€", "")
        if "M" in valor_raw:
            valor = float(valor_raw.replace("M", "").replace(",", ".")) * 1_000_000
        elif "K" in valor_raw:
            valor = float(valor_raw.replace("K", "").replace(",", ".")) * 1_000
        else:
            valor = 0

        jogadores.append({
            "nome": nome,
            "posicao": posicao,
            "overall": overall,
            "valor": int(valor),
            "nacionalidade": nacionalidade,
            "time_origem": time_origem,
            "foto": foto
        })

        if len(jogadores) >= 50:
            break
    if len(jogadores) >= 50:
        break

# Salva a planilha
df = pd.DataFrame(jogadores)
df.to_excel("jogadores_lote_65.xlsx", index=False)
print("✅ Planilha gerada com sucesso: jogadores_lote_65.xlsx")
