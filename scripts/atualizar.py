"""
Atualiza o dashboard de Meta Ads da Connectabil.

1. Busca os dados dos últimos 90 dias no Windsor.ai (se WINDSOR_API_KEY estiver definida).
   Sem a chave, usa os arquivos já salvos em dados/.
2. Monta o dashboard com os dados embutidos.
3. Protege com senha (DASH_SENHA) e grava index.html na raiz do repositório.
   Para publicar sem senha, defina DASH_PUBLICO=1 (não recomendado: expõe investimento e resultados).

Variáveis de ambiente (no GitHub, cadastre como "Secrets" do repositório):
  WINDSOR_API_KEY   chave da API do Windsor.ai
  DASH_SENHA        senha para abrir o dashboard
"""
import base64, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
SCRIPTS = os.path.join(RAIZ, "scripts")
DIAS = 90

CAMPOS_CAMPANHAS = ["date", "account_name", "campaign", "campaign_objective", "campaign_status", "spend",
                    "impressions", "clicks", "link_clicks", "actions_lead", "actions_landing_page_view",
                    "actions_complete_registration", "actions_onsite_conversion_messaging_conversation_started_7d"]
CAMPOS_ANUNCIOS = ["date", "campaign", "ad_name", "spend", "impressions", "frequency", "link_clicks",
                   "actions_lead", "actions_onsite_conversion_messaging_conversation_started_7d"]

hoje = datetime.now(timezone(timedelta(hours=-3))).date()
inicio = hoje - timedelta(days=DIAS - 1)


def windsor(campos):
    params = {
        "api_key": os.environ["WINDSOR_API_KEY"],
        "date_from": inicio.isoformat(),
        "date_to": hoje.isoformat(),
        "fields": ",".join(campos),
    }
    url = "https://connectors.windsor.ai/facebook?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=300) as r:
        resp = json.loads(r.read().decode("utf-8"))
    linhas = resp.get("data", resp) if isinstance(resp, dict) else resp
    if not isinstance(linhas, list):
        sys.exit("Resposta inesperada do Windsor.ai: " + json.dumps(resp)[:500])
    return linhas


def salvar(nome, linhas):
    with open(os.path.join(DADOS, nome), "w", encoding="utf-8") as f:
        json.dump({"status": "done", "data": linhas}, f, ensure_ascii=False)


def ler(nome):
    with open(os.path.join(DADOS, nome), encoding="utf-8") as f:
        d = json.load(f)
    return d["data"] if isinstance(d, dict) else d


os.makedirs(DADOS, exist_ok=True)
if os.environ.get("WINDSOR_API_KEY"):
    print("Buscando dados no Windsor.ai de", inicio, "a", hoje)
    salvar("campanhas.json", windsor(CAMPOS_CAMPANHAS))
    salvar("anuncios.json", windsor(CAMPOS_ANUNCIOS))
    ate = hoje.isoformat()
else:
    print("WINDSOR_API_KEY não definida: usando os dados já salvos em dados/")
    ate = None

campanhas, anuncios = ler("campanhas.json"), ler("anuncios.json")
if ate is None:
    ate = max(r["date"] for r in campanhas)

payload = {"gerado_em": datetime.now(timezone.utc).isoformat(), "ate": ate,
           "campanhas": campanhas, "anuncios": anuncios}

html = open(os.path.join(SCRIPTS, "dashboard.html"), encoding="utf-8").read()
ini, fim = html.index("/*__DATA__*/"), html.index("/*__END__*/") + len("/*__END__*/")
dados_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
html = html[:ini] + dados_js + html[fim:]

# d3 embutido (sem depender de CDN)
d3_local = os.path.join(SCRIPTS, "d3.min.js")
tag_cdn = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
if os.path.exists(d3_local) and tag_cdn in html:
    html = html.replace(tag_cdn, "<script>" + open(d3_local, encoding="utf-8").read().replace("</script", "<\\/script") + "</script>")

saida = os.path.join(RAIZ, "index.html")
if os.environ.get("DASH_PUBLICO") == "1":
    open(saida, "w", encoding="utf-8").write(html)
    print("Dashboard SEM senha gravado em index.html")
    sys.exit(0)

senha = os.environ.get("DASH_SENHA")
if not senha:
    sys.exit("Defina DASH_SENHA (ou DASH_PUBLICO=1 para publicar sem senha).")

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

salt, iv, ITER = os.urandom(16), os.urandom(12), 250000
chave = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(senha.encode())
ct = AESGCM(chave).encrypt(iv, html.encode("utf-8"), None)
b = lambda x: base64.b64encode(x).decode()
gate = open(os.path.join(SCRIPTS, "senha.html"), encoding="utf-8").read()
gate = gate.replace("%SALT%", b(salt)).replace("%IV%", b(iv)).replace("%CT%", b(ct)).replace("%ITER%", str(ITER))
open(saida, "w", encoding="utf-8").write(gate)
print("Dashboard com senha gravado em index.html (%d linhas de campanha, %d de anúncio)" % (len(campanhas), len(anuncios)))
