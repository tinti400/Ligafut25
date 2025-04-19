import os

# Palavras-chave suspeitas (você pode adicionar outras)
palavras_chave = [
    "apikey", "api_key", "private_key", "firebase", "credential",
    "client_email", "client_id", "secret", "token", "auth_domain"
]

print("Verificando arquivos por possíveis vazamentos de credenciais...\n")

# Pastas que não precisam ser verificadas
ignorar_pastas = [".git", "__pycache__", ".venv", "venv", "node_modules"]

# Extensões de arquivos para verificar
extensoes_validas = (".py", ".json", ".toml", ".env", ".js", ".ts")

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ignorar_pastas]
    for file in files:
        if file.endswith(extensoes_validas):
            caminho = os.path.join(root, file)
            try:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    for i, linha in enumerate(f, start=1):
                        if any(palavra in linha.lower() for palavra in palavras_chave):
                            print(f"[SUSPEITA] {caminho} (linha {i}): {linha.strip()}")
            except Exception as e:
                print(f"[ERRO] Ao ler {caminho}: {e}")
