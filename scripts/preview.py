"""Genera docs/preview-*.svg con datos de ejemplo (sin llamar a Spotify)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
import now  # noqa: E402

demo = dict(playing=True, name="Nombre de la canción", artists="Artista, Otro Artista", album="Nombre del álbum",
            cover=None, progress=95_000, duration=201_000, played_at=None)
for name, info, lang, accent in [
    ("preview-es.svg", demo, "es", None),
    ("preview-en.svg", {**demo, "playing": False, "played_at": "2026-01-01T00:00:00Z"}, "en", None),
    ("preview-green.svg", demo, "en", "1db954"),
]:
    with open(os.path.join(ROOT, "docs", name), "w", encoding="utf-8") as f:
        f.write(now.render(info, lang, accent))
print("ok")
