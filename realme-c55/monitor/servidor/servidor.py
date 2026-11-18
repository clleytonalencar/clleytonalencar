#!/usr/bin/env python3
"""Servidor do monitor do Realme C55.

- Entrega ao celular os scripts da pasta publico/ (o celular sempre baixa a versão mais nova).
- Recebe os relatórios do celular e guarda em dados/relatorios.jsonl.
- Opcional: avisa num webhook (ex.: ntfy.sh) quando aparecem alertas novos.

Variáveis de ambiente:
  MONITOR_TOKEN   (obrigatória) senha compartilhada com o celular
  MONITOR_PORT    porta local (padrão 8787). Coloque atrás de HTTPS (nginx/Caddy).
  MONITOR_DATA    pasta dos relatórios (padrão ./dados)
  ALERTA_WEBHOOK  URL que recebe um POST de texto quando surgem alertas novos
"""
import hmac, json, os, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(BASE, "publico")
DATA = os.environ.get("MONITOR_DATA", os.path.join(BASE, "dados"))
TOKEN = os.environ["MONITOR_TOKEN"]
PORT = int(os.environ.get("MONITOR_PORT", "8787"))
WEBHOOK = os.environ.get("ALERTA_WEBHOOK", "")
ARQUIVOS = {"agente.sh", "monitor.sh", "config.env", "pacotes.txt", "instalar.sh"}
REL = os.path.join(DATA, "relatorios.jsonl")
os.makedirs(DATA, exist_ok=True)


def ultimo_relatorio():
    try:
        with open(REL, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            linhas = f.read().splitlines()
        return json.loads(linhas[-1]) if linhas else None
    except (OSError, ValueError, IndexError):
        return None


def avisar(texto):
    if not WEBHOOK:
        return
    try:
        req = urllib.request.Request(WEBHOOK, data=texto.encode(), method="POST",
                                     headers={"Title": "Realme C55"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:  # aviso nunca derruba o servidor
        print("webhook falhou:", e, flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "realme-monitor"

    def _resp(self, code, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _autorizado(self):
        return hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN)

    def do_GET(self):
        if self.path == "/realme/saude":
            return self._resp(200, b"ok\n")
        if not self._autorizado():
            return self._resp(401)
        nome = self.path.removeprefix("/realme/")
        if nome in ARQUIVOS and os.path.isfile(os.path.join(PUB, nome)):
            with open(os.path.join(PUB, nome), "rb") as f:
                return self._resp(200, f.read())
        if nome == "status":
            r = ultimo_relatorio()
            if r is None:
                return self._resp(404, b"sem relatorios ainda\n")
            r["minutos_desde_ultimo"] = round((time.time() - r.get("recebido_em", 0)) / 60)
            return self._resp(200, json.dumps(r, ensure_ascii=False, indent=2).encode(),
                              "application/json; charset=utf-8")
        return self._resp(404)

    def do_POST(self):
        if self.path != "/realme/relatorio":
            return self._resp(404)
        if not self._autorizado():
            return self._resp(401)
        tam = int(self.headers.get("Content-Length", "0"))
        if not 0 < tam <= 65536:
            return self._resp(413)
        try:
            r = json.loads(self.rfile.read(tam))
            assert isinstance(r, dict)
        except Exception:
            return self._resp(400, b"json invalido\n")
        anterior = ultimo_relatorio() or {}
        r["recebido_em"] = int(time.time())
        with open(REL, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        alertas = r.get("alertas") or []
        if alertas and alertas != anterior.get("alertas"):
            avisar("\n".join(map(str, alertas)))
        return self._resp(200, b"ok\n")

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    print(f"realme-monitor na porta {PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
