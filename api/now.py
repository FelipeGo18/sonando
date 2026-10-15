"""Tarjeta "sonando ahora" de Spotify, con la estética del perfil (RHLM x Chrome Hearts)."""
import base64
import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from art import DIM, GRAY, LINE, RED, W, WHITE, anton, mono, svg_doc, title  # noqa: E402

CID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REFRESH = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")


def access_token():
    auth = base64.b64encode(f"{CID}:{SECRET}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": REFRESH}).encode()
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=data,
                                 headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.load(r)["access_token"]


def get(url, tok):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=8) as r:
        return json.load(r) if r.status == 200 else None


def track_info():
    """Devuelve lo que suena ahora o, si no hay nada, lo último que sonó."""
    tok = access_token()
    now = get("https://api.spotify.com/v1/me/player/currently-playing", tok)
    if now and now.get("item") and now.get("currently_playing_type") == "track":
        it = now["item"]
        return dict(playing=now.get("is_playing", False), name=it["name"],
                    artists=", ".join(a["name"] for a in it["artists"]), album=it["album"]["name"],
                    cover=pick_cover(it["album"]["images"]), progress=now.get("progress_ms", 0),
                    duration=it["duration_ms"], played_at=None)
    rec = get("https://api.spotify.com/v1/me/player/recently-played?limit=1", tok)
    item = rec["items"][0]
    it = item["track"]
    return dict(playing=False, name=it["name"], artists=", ".join(a["name"] for a in it["artists"]),
                album=it["album"]["name"], cover=pick_cover(it["album"]["images"]), progress=0,
                duration=it["duration_ms"], played_at=item["played_at"])


def pick_cover(images):
    if not images:
        return None
    img = sorted(images, key=lambda i: abs((i.get("width") or 300) - 300))[0]
    with urllib.request.urlopen(img["url"], timeout=8) as r:
        return "data:image/jpeg;base64," + base64.b64encode(r.read()).decode()


def clean(font, text):
    return "".join(ch for ch in text if ord(ch) in font.cmap)


def fit(font, text, size, max_w, tracking=0.0):
    text = clean(font, text)
    if font.width(text, size, tracking) <= max_w:
        return text
    while text and font.width(text + "...", size, tracking) > max_w:
        text = text[:-1]
    return text.rstrip() + "..."


def mmss(ms):
    s = int(ms // 1000)
    return f"{s // 60}:{s % 60:02d}"


def hace(iso):
    t = time.mktime(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    m = int((time.time() - t) // 60)
    if m < 60:
        return f"HACE {max(m, 1)} MIN"
    if m < 1440:
        return f"HACE {m // 60} H"
    return f"HACE {m // 1440} D"


def vinyl(cx, cy, r, spinning):
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#1f1f1f" stroke-width="1"/>'
                    for rr in range(int(r * 0.42), int(r), 5))
    spin = (f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
            f'dur="2.4s" repeatCount="indefinite"/>') if spinning else ""
    return (f'<g><circle cx="{cx}" cy="{cy}" r="{r}" fill="#0d0d0d" stroke="#2a2a2a"/>{rings}'
            f'<g>{spin}<circle cx="{cx}" cy="{cy}" r="{r * 0.34:.1f}" fill="{RED}"/>'
            f'<rect x="{cx - 2}" y="{cy - r * 0.3:.1f}" width="4" height="{r * 0.16:.1f}" fill="#7f1520"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="#0a0a0a"/>'
            f'<path d="M{cx} {cy - r} A{r} {r} 0 0 1 {cx + r * 0.87:.1f} {cy - r * 0.5:.1f} L{cx} {cy} Z" '
            f'fill="#fff" opacity="0.05"/></g>')


def render(info):
    H, x0, y_title = 440, 70, 132
    playing = info["playing"]
    g, t, wt = title("Sonando" if playing else "Lo último", y_title, H)
    out = [t]
    if playing:
        out.append(f'<circle cx="{x0 + wt + 30}" cy="{y_title - 6}" r="6" fill="{RED}">'
                   f'<animate attributeName="opacity" values="1;0.2;1" dur="1.4s" repeatCount="indefinite"/></circle>')
        tag, _ = mono.path("EN VIVO", 15, x0 + wt + 46, y_title, RED, tracking=3)
    else:
        tag, _ = mono.path(hace(info["played_at"]) if info["played_at"] else "EN PAUSA", 15, x0 + wt + 26, y_title, DIM,
                           tracking=3)
    sp = "SPOTIFY"
    right, _ = mono.path(sp, 15, W - x0 - mono.width(sp, 15, 3), y_title, DIM, tracking=3)
    out += [tag, right, f'<rect x="{x0}" y="{y_title + 22}" width="{W - 2 * x0}" height="2" fill="{RED}"/>']

    cs, cy0 = 210, 186
    out.append(vinyl(x0 + cs - 20, cy0 + cs / 2, cs * 0.48, playing))
    if info["cover"]:
        out.append(f'<rect x="{x0 + 4}" y="{cy0 + 6}" width="{cs}" height="{cs}" fill="#000" opacity="0.6"/>')
        out.append(f'<image href="{info["cover"]}" x="{x0}" y="{cy0}" width="{cs}" height="{cs}" preserveAspectRatio="xMidYMid slice"/>')
        out.append(f'<rect x="{x0}" y="{cy0}" width="{cs}" height="{cs}" fill="none" stroke="url(#chromeFrame)" stroke-width="2"/>')

    tx = x0 + cs + 150
    max_w = W - x0 - tx
    name = fit(anton, info["name"].upper(), 56, max_w - 60, 1)
    n, wn = anton.path(name, 56, tx, 262, WHITE, tracking=1)
    out.append(n)
    a, _ = mono.path(fit(mono, info["artists"], 20, max_w), 20, tx, 302, GRAY)
    al, _ = mono.path(fit(mono, info["album"].upper(), 13, max_w, 2), 13, tx, 330, DIM, tracking=2)
    out += [a, al]

    if playing:
        ex, ey = tx + wn + 22, 258
        for j, (vals, dur) in enumerate([("6;22;10;26;6", "0.9s"), ("18;8;24;12;18", "0.7s"), ("10;26;6;20;10", "1.1s")]):
            hs = [int(v) for v in vals.split(";")]
            ys = ";".join(str(ey - h) for h in hs)
            out.append(f'<rect x="{ex + j * 8}" y="{ey - hs[0]}" width="5" height="{hs[0]}" fill="{RED}">'
                       f'<animate attributeName="height" values="{vals}" dur="{dur}" repeatCount="indefinite"/>'
                       f'<animate attributeName="y" values="{ys}" dur="{dur}" repeatCount="indefinite"/></rect>')

    # barra de progreso: arranca donde va la canción y avanza hasta el final en tiempo real
    by, bw = 362, max_w
    dur, prog = info["duration"] or 1, info["progress"] if playing else info["duration"] or 1
    start = bw * prog / dur
    out.append(f'<rect x="{tx}" y="{by}" width="{bw}" height="3" fill="{LINE}"/>')
    if playing:
        remain = max((dur - prog) / 1000, 1)
        out.append(f'<rect x="{tx}" y="{by}" width="{start:.1f}" height="3" fill="{RED}">'
                   f'<animate attributeName="width" from="{start:.1f}" to="{bw}" dur="{remain:.1f}s" fill="freeze"/></rect>')
        out.append(f'<circle cx="{tx + start:.1f}" cy="{by + 1.5}" r="6" fill="{RED}">'
                   f'<animate attributeName="cx" from="{tx + start:.1f}" to="{tx + bw}" dur="{remain:.1f}s" fill="freeze"/></circle>')
    else:
        out.append(f'<rect x="{tx}" y="{by}" width="{bw}" height="3" fill="#3a3a3a"/>')
    t1, _ = mono.path(mmss(prog if playing else 0), 13, tx, by + 28, DIM, tracking=1)
    total = mmss(dur)
    t2, _ = mono.path(total, 13, tx + bw - mono.width(total, 13, 1), by + 28, DIM, tracking=1)
    out += [t1, t2]

    label = f'{"Sonando" if playing else "Lo último"}: {info["name"]} — {info["artists"]}'
    return svg_doc(H, html.escape(label), "".join(out), extra_defs=g)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            body, code = render(track_info()), 200
        except Exception as e:  # la tarjeta nunca debe romper el README
            body, code = svg_doc(200, "Spotify no disponible", mono.path("SPOTIFY NO DISPONIBLE", 18, 70, 110, DIM)[0]), 200
            print("error:", repr(e))
        self.send_response(code)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
