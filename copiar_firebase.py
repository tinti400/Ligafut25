from google.cloud import firestore
from google.oauth2 import service_account

# Configura credenciais
cred_antigo = service_account.Credentials.from_service_account_file("credenciais_antigo.json")
db_antigo = firestore.Client(credentials=cred_antigo, project="ligafut-a0056")

cred_novo = service_account.Credentials.from_service_account_file("credenciais_novo.json")
db_novo = firestore.Client(credentials=cred_novo, project="ligafut-681c2")

def copiar_colecao(colecao_nome):
    print(f"🔄 Copiando coleção: {colecao_nome}")
    docs = db_antigo.collection(colecao_nome).stream()

    for doc in docs:
        dados = doc.to_dict()
        doc_id = doc.id
        db_novo.collection(colecao_nome).document(doc_id).set(dados)
        print(f"✅ Documento copiado: {colecao_nome}/{doc_id}")

# Coleções principais do LigaFut
colecoes = [
    "usuarios",
    "times",
    "admins",
    "mercado_transferencias",
    "configuracoes"
]

# Subcoleções opcionais por time (ex: elenco, movimentacoes)
def copiar_subcolecoes_por_time(subcolecao_nome):
    times = db_antigo.collection("times").stream()
    for time in times:
        time_id = time.id
        subdocs = db_antigo.collection("times").document(time_id).collection(subcolecao_nome).stream()
        for subdoc in subdocs:
            dados = subdoc.to_dict()
            sub_id = subdoc.id
            db_novo.collection("times").document(time_id).collection(subcolecao_nome).document(sub_id).set(dados)
            print(f"📂 Subcoleção copiada: times/{time_id}/{subcolecao_nome}/{sub_id}")

# Começa a cópia
for colecao in colecoes:
    copiar_colecao(colecao)

# Subcoleções especiais
copiar_subcolecoes_por_time("elenco")
copiar_subcolecoes_por_time("movimentacoes")

print("🎉 Migração finalizada com sucesso!")
