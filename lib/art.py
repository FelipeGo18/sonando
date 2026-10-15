"""Motor de dibujo: cuero negro, plata cromada y letra gótica (Real Hasta La Muerte x Chrome Hearts).

Todo el texto se convierte a trazos con fontTools, así que los SVG no dependen de fuentes externas
(GitHub no carga fuentes dentro de imágenes).
"""
import math
import os

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")

BLACK, RED, WHITE, GRAY, DIM, LINE = "#0a0a0a", "#e11d2e", "#f5f5f5", "#a3a3a3", "#6b6b6b", "#262626"
W = 1200


class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]

    def cap(self, size, ch="H"):
        bp = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(bp)
        return bp.bounds[3] * size / self.upm

    def glyphs(self, text, size, x, y, tracking=0.0):
        sc = size / self.upm
        out, cx = [], x
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                raise SystemExit(f"glifo faltante: {ch!r}")
            adv = self.hmtx[g][0] * sc
            pen = SVGPathPen(self.gs)
            self.gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
            out.append((pen.getCommands(), cx, adv))
            cx += adv + tracking
        return out, cx - tracking - x

    def d(self, text, size, x, y, tracking=0.0):
        gl, w = self.glyphs(text, size, x, y, tracking)
        return " ".join(g[0] for g in gl if g[0]), w

    def path(self, text, size, x, y, fill, tracking=0.0, extra=""):
        d, w = self.d(text, size, x, y, tracking)
        return f'<path d="{d}" fill="{fill}" {extra}/>', w

    def width(self, text, size, tracking=0.0):
        return self.glyphs(text, size, 0, 0, tracking)[1]


anton = Font(f"{FONTS}/Anton-Regular.ttf")
mono = Font(f"{FONTS}/SpaceMono-Regular.ttf")
monob = Font(f"{FONTS}/SpaceMono-Bold.ttf")
gothic = Font(f"{FONTS}/UnifrakturMaguntia-Book.ttf")


# ---------------------------------------------------------------- materiales

def defs_base(h):
    """Cuero, grano, cromo y el destello que recorre el metal."""
    return f"""<filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.07 0"/>
  </filter>
  <filter id="leather" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.045 0.06" numOctaves="4" seed="11" result="n"/>
    <feDiffuseLighting in="n" surfaceScale="2.2" lighting-color="#161616" result="l">
      <feDistantLight azimuth="235" elevation="58"/>
    </feDiffuseLighting>
    <feComposite in="l" in2="SourceGraphic" operator="in"/>
  </filter>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="-420" y1="0" x2="-180" y2="{h}">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#fff" stop-opacity="0.95"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0;{W + 700} 0;{W + 700} 0"
      keyTimes="0;0.4;1" dur="6s" repeatCount="indefinite"/>
  </linearGradient>
  {chrome_grad("chromeFrame", 0, h)}"""


def chrome_grad(gid, top, bottom):
    """Plata pulida: bandas claras y oscuras con un horizonte marcado, como joyería."""
    return f"""<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{top:.1f}" x2="0" y2="{bottom:.1f}">
    <stop offset="0" stop-color="#ffffff"/>
    <stop offset="0.28" stop-color="#c9c9c9"/>
    <stop offset="0.48" stop-color="#5c5c5c"/>
    <stop offset="0.52" stop-color="#2b2b2b"/>
    <stop offset="0.56" stop-color="#e6e6e6"/>
    <stop offset="0.8" stop-color="#8f8f8f"/>
    <stop offset="1" stop-color="#f2f2f2"/>
  </linearGradient>"""


def background(h):
    return (f'<rect width="{W}" height="{h}" fill="{BLACK}"/>'
            f'<rect width="{W}" height="{h}" fill="#000" filter="url(#leather)" opacity="0.35"/>')


def overlay(h):
    return f'<rect width="{W}" height="{h}" filter="url(#grain)" pointer-events="none"/>'


def cross_d(cx, cy, size, long_bottom=True):
    """Cruz gótica propia: brazos que se abren y terminan en punta, centro hueco para la gema."""
    r0, w0 = size * 0.10, size * 0.075
    pts = []
    for k, ang in enumerate((0, 90, 180, 270)):
        L = size * (1.45 if (long_bottom and ang == 90) else 1.0)
        w1 = size * 0.2
        local = [(r0, -w0), (L - size * 0.24, -w1), (L - size * 0.12, -w1 + size * 0.05), (L, 0),
                 (L - size * 0.12, w1 - size * 0.05), (L - size * 0.24, w1), (r0, w0)]
        a = math.radians(ang)
        for x, y in local:
            pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def cross(cx, cy, size, gid, gem=True, long_bottom=True):
    d = cross_d(cx, cy, size, long_bottom)
    inner = cross_d(cx, cy, size * 0.8, long_bottom)
    parts = [
        f'<path d="{d}" fill="#000" transform="translate(4 6)" opacity="0.7"/>',
        f'<path d="{d}" fill="url(#{gid})" stroke="#ffffff" stroke-opacity="0.35" stroke-width="1"/>',
        f'<path d="{inner}" fill="none" stroke="#1a1a1a" stroke-opacity="0.55" stroke-width="{max(size * 0.02, 1):.1f}"/>',
        f'<path d="{d}" fill="url(#shine)"/>',
    ]
    if gem:
        r = size * 0.11
        parts += [f'<circle cx="{cx}" cy="{cy}" r="{r * 1.35:.1f}" fill="url(#{gid})" stroke="#000" stroke-opacity="0.5"/>',
                  f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{RED}"/>',
                  f'<circle cx="{cx - r * 0.35:.1f}" cy="{cy - r * 0.35:.1f}" r="{r * 0.3:.1f}" fill="#fff" opacity="0.55"/>']
    return "".join(parts)


def frame(h, gid="chromeFrame"):
    """Marco doble de plata con una cruz pequeña en cada esquina."""
    i1, i2 = 22, 30
    out = [f'<rect x="{i1}" y="{i1}" width="{W - 2 * i1}" height="{h - 2 * i1}" fill="none" stroke="url(#{gid})" stroke-width="2"/>',
           f'<rect x="{i2}" y="{i2}" width="{W - 2 * i2}" height="{h - 2 * i2}" fill="none" stroke="#3a3a3a" stroke-width="1"/>']
    for x, y in ((i1, i1), (W - i1, i1), (i1, h - i1), (W - i1, h - i1)):
        out.append(f'<rect x="{x - 9}" y="{y - 9}" width="18" height="18" fill="{BLACK}"/>')
        out.append(cross(x, y, 11, gid, gem=False, long_bottom=False))
    return "".join(out)


def chrome_text(font, text, size, x, y, gid, tracking=0.0):
    d, w = font.d(text, size, x, y, tracking)
    return (f'<path d="{d}" fill="#000" transform="translate(3 5)" opacity="0.75"/>'
            f'<path d="{d}" fill="url(#{gid})" stroke="#fff" stroke-opacity="0.3" stroke-width="0.8"/>'
            f'<path d="{d}" fill="url(#shine)"/>'), w


def title(text, y, h_card):
    """Título de sección en gótica cromada con su línea roja debajo."""
    size = 84
    top = y - gothic.cap(size, "T") - 6
    g = chrome_grad("chromeTitle", top, y + 18)
    t, w = chrome_text(gothic, text, size, 70, y, "chromeTitle")
    return g, t, w


def typed(font, text, size, x, y, D, t0, step, t_out, tracking=0.0, fill=None, gid=None):
    """Cada glifo aparece en t0 + i*step y se apaga en t_out (bucle de D segundos)."""
    gl, w = font.glyphs(text, size, x, y, tracking)
    parts = []
    for i, (d, _, _) in enumerate(gl):
        if not d:
            continue
        a = (t0 + i * step) / D
        anim = (f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
                f'keyTimes="0;{a:.4f};{t_out / D:.4f}" dur="{D}s" repeatCount="indefinite"/>')
        if gid:
            body = (f'<path d="{d}" fill="#000" transform="translate(3 5)" opacity="0.75"/>'
                    f'<path d="{d}" fill="url(#{gid})" stroke="#fff" stroke-opacity="0.3" stroke-width="0.8"/>'
                    f'<path d="{d}" fill="url(#shine)"/>')
        else:
            body = f'<path d="{d}" fill="{fill}"/>'
        parts.append(f"<g>{anim}{body}</g>")
    return "".join(parts), w, t0 + len(text) * step


def svg_doc(h, label, body, extra_defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{label}">
<defs>
  {defs_base(h)}
  {extra_defs}
</defs>
{background(h)}
{body}
{frame(h)}
{overlay(h)}
</svg>
"""
