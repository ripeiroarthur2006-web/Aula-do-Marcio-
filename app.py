"""Servidor web local do sistema de planejamento agregado."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys

from optimizer import optimize

ROOT = Path(__file__).parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # A interface muda com frequência; evita que o navegador mantenha JS/CSS antigos.
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path != "/api/optimize":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("A solicitação é muito grande.")
            payload = json.loads(self.rfile.read(length))
            response, status = optimize(payload), 200
        except (ValueError, json.JSONDecodeError) as exc:
            response, status = {"success": False, "error": str(exc)}, 400
        except Exception:
            response, status = {"success": False, "error": "Erro interno ao executar a otimização."}, 500
        body = json.dumps(response, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Sistema disponível em http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()

