#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BACKEND_PATH = Path(os.getenv(
    "TUTOR_BACKEND_PATH",
    Path.home() / ".local/share/cinnamon/desklets/tutor-escolar@mint/tutor_backend.py"
)).expanduser()

if not BACKEND_PATH.exists():
    raise RuntimeError(f"No se encontro el backend: {BACKEND_PATH}")

sys.path.insert(0, str(BACKEND_PATH.parent))
import tutor_backend as backend


class TutorAPIHandler(BaseHTTPRequestHandler):
    server_version = "TutorEscolarAPI/1.0"

    def _send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "tutor-escolar-api"})
        else:
            self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/ask":
            self._send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            self._send_json(400, {"error": f"json_invalido: {e}"})
            return

        texto = (payload.get("texto") or "").strip()
        if not texto:
            self._send_json(400, {"error": "falta_el_campo_texto"})
            return

        seguro, motivo = backend.es_pregunta_segura(texto)
        if not seguro:
            self._send_json(200, {"respuesta": motivo})
            return

        try:
            respuesta = backend.orquestar_chat(texto, payload.get("imagen"))
            resultado = {"respuesta": respuesta}
            if payload.get("voz"):
                audio = backend.text_to_speech(respuesta)
                if audio:
                    resultado["audio"] = audio
            self._send_json(200, resultado)
        except Exception as e:
            self._send_json(500, {"error": f"error_tutor: {e}"})

    def log_message(self, format, *args):
        return


def main():
    port = int(os.getenv("TUTOR_API_PORT", "8090"))
    server = ThreadingHTTPServer(("127.0.0.1", port), TutorAPIHandler)
    print(f"Tutor API escuchando en http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
