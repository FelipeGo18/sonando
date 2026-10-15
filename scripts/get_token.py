"""Obtiene tu SPOTIFY_REFRESH_TOKEN (solo se hace una vez).

1. Copia .env.example a .env y pon tu SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET.
2. En tu app de Spotify agrega el Redirect URI: http://127.0.0.1:8888/callback
3. Ejecuta:  python scripts/get_token.py
4. Acepta en el navegador. El refresh token queda guardado en tu .env (que nunca se sube a git).
"""
import base64
import json
import os
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-currently-playing user-read-recently-played"

if not os.path.exists(ENV):
    raise SystemExit("No encontré .env — copia .env.example a .env y llena el client id y el secret.")
cfg = dict(line.strip().split("=", 1) for line in open(ENV, encoding="utf-8") if "=" in line and not line.startswith("#"))
CID, SECRET = cfg.get("SPOTIFY_CLIENT_ID", ""), cfg.get("SPOTIFY_CLIENT_SECRET", "")
if not CID or not SECRET:
    raise SystemExit("Falta SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en .env")


class Callback(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" not in q:
            self.send_response(400)
            self.end_headers()
            return
        data = urllib.parse.urlencode({"grant_type": "authorization_code", "code": q["code"][0],
                                       "redirect_uri": REDIRECT}).encode()
        auth = base64.b64encode(f"{CID}:{SECRET}".encode()).decode()
        req = urllib.request.Request("https://accounts.spotify.com/api/token", data=data,
                                     headers={"Authorization": f"Basic {auth}"})
        refresh = json.load(urllib.request.urlopen(req))["refresh_token"]
        lines = [ln for ln in open(ENV, encoding="utf-8") if not ln.startswith("SPOTIFY_REFRESH_TOKEN=")]
        with open(ENV, "w", encoding="utf-8") as f:
            f.write("".join(lines).rstrip("\n") + f"\nSPOTIFY_REFRESH_TOKEN={refresh}\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h1>Listo, ya puedes cerrar esta pestaña.</h1>".encode())
        self.server.done = True

    def log_message(self, *args):
        pass


url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
    {"client_id": CID, "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES})
server = HTTPServer(("127.0.0.1", 8888), Callback)
server.done = False
print("Si no se abre el navegador, entra a:\n" + url)
webbrowser.open(url)
while not server.done:
    server.handle_request()
print("Refresh token guardado en .env. Cópialo a las variables de entorno de Vercel.")
