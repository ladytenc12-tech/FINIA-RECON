
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.reconciliation import run_reconciliation
from app.ai_agent import FinancialReconciliationAgent


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

HOST = "0.0.0.0"
PORT = 8000


class FINIAHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(STATIC_DIR),
            **kwargs
        )

    def send_json(self, data, status=200):
        response = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):

        if self.path == "/api/health":
            self.send_json({
                "application": "FINIA-RECON",
                "status": "ONLINE",
                "message": "Servidor funcionando correctamente"
            })
            return

        if self.path.startswith("/api/"):
            self.send_json({
                "error": "Endpoint no encontrado"
            }, 404)
            return

        super().do_GET()

    def do_POST(self):

        if self.path != "/api/reconcile":
            self.send_json({
                "error": "Endpoint no encontrado"
            }, 404)
            return

        try:
            report = run_reconciliation()

            agent = FinancialReconciliationAgent()
            analysis = agent.analyze(report)

            self.send_json({
                "success": True,
                "report": report,
                "analysis": analysis
            })

        except (FileNotFoundError, ValueError) as error:
            self.send_json({
                "success": False,
                "error": str(error)
            }, 400)

        except Exception as error:
            print(f"[FINIA-RECON] Error: {error}")

            self.send_json({
                "success": False,
                "error": "Error interno al procesar la conciliación"
            }, 500)

    def log_message(self, format, *args):
        print(f"[FINIA-RECON] {format % args}")


def start_server():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        FINIAHandler
    )

    print("=" * 50)
    print("FINIA-RECON | SERVIDOR INICIADO")
    print("=" * 50)
    print(f"Servidor: http://localhost:{PORT}")
    print("Estado: ONLINE")
    print("Presiona CTRL + C para detener el servidor.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nServidor detenido.")

    finally:
        server.server_close()


if __name__ == "__main__":
    start_server()
