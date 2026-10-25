"""Draws docs/architecture.png.

Writes the diagram as SVG next to this file; render.js turns it into the PNG:

    python3 docs/diagram/architecture.py
    node docs/diagram/render.js   # needs the playwright npm package
"""

from html import escape
from pathlib import Path

HERE = Path(__file__).parent

SETUP = dict(stroke="#1D4ED8", fill="#EFF6FF", tint="#F5F9FF", text="#1E3A8A")
APP = dict(stroke="#C2410C", fill="#FFF4EB", tint="#FFFAF5", text="#7C2D12")
EXT = dict(stroke="#6B7280", fill="#F3F4F6", tint="#F9FAFB", text="#374151")
INK = "#111827"
MUTED = "#4B5563"
CTRL = "#6B7280"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, stroke, rx=12, dash=False, sw=2):
        d = ' stroke-dasharray="7 5"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=15, weight=400, fill=INK, anchor="start", mono=False, rotate=None):
        fam = "JetBrains Mono" if mono else "Inter"
        rot = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{rot}>{escape(s)}</text>')

    def lines(self, x, y, rows, anchor="start", gap=None):
        """rows: list of (text, size, weight, fill, mono)."""
        for s, size, weight, fill, mono in rows:
            self.text(x, y, s, size, weight, fill, anchor, mono)
            y += gap or size + 8
        return y

    def badge(self, x, y, label, c, anchor="start"):
        w = 8.2 * len(label) + 20
        if anchor == "end":
            x -= w
        self.rect(x, y, w, 24, c["stroke"], c["stroke"], rx=12, sw=0)
        self.text(x + w / 2, y + 16.5, label, 12, 600, "#FFFFFF", "middle", mono=True)

    def cyl(self, x, y, w, h, c, ry=12):
        s, f = c["stroke"], c["fill"]
        self.add(
            f'<path d="M{x},{y + ry} L{x},{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} '
            f'L{x + w},{y + ry}" fill="{f}" stroke="{s}" stroke-width="2"/>'
        )
        self.add(f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{f}" stroke="{s}" stroke-width="2"/>')

    def arrow(self, d, color=INK, dash=False, sw=2.5, both=False):
        mid = {INK: "ink", CTRL: "ctrl", SETUP["stroke"]: "setup", APP["stroke"]: "app"}[color]
        da = ' stroke-dasharray="6 5"' if dash else ""
        start = f' marker-start="url(#s-{mid})"' if both else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da} marker-end="url(#e-{mid})"{start}/>')

    def label(self, x, y, rows, anchor="middle", bg=True):
        """Arrow label with a white halo so it stays readable over lines."""
        y0 = y
        for s, size, weight, fill, mono in rows:
            fam = "JetBrains Mono" if mono else "Inter"
            if bg:
                self.add(
                    f'<text x="{x}" y="{y0}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
                    f'text-anchor="{anchor}" stroke="#FFFFFF" stroke-width="6" stroke-linejoin="round" fill="#FFFFFF">{escape(s)}</text>'
                )
            self.text(x, y0, s, size, weight, fill, anchor, mono)
            y0 += size + 6

    def render(self):
        markers = ""
        for name, col in [("ink", INK), ("ctrl", CTRL), ("setup", SETUP["stroke"]), ("app", APP["stroke"])]:
            markers += (
                f'<marker id="e-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
                f'<marker id="s-{name}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                f'<path d="M10,0 L0,5 L10,10 z" fill="{col}"/></marker>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" style="font-variant-ligatures:none">'
            f"<defs>{markers}</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>' + "".join(self.parts) + "</svg>"
        )


def T(s, size=15, weight=400, fill=INK, mono=False):
    return (s, size, weight, fill, mono)


def legend(g, x, y, items):
    for kind, c, label in items:
        if kind == "box":
            g.rect(x, y - 13, 22, 16, c["fill"], c["stroke"], rx=4)
            g.text(x + 32, y, label, 14, 500, MUTED)
            x += 56 + 7.6 * len(label)
        else:
            g.arrow(f"M{x},{y - 5} L{x + 36},{y - 5}", c, dash=(kind == "dash"))
            g.text(x + 46, y, label, 14, 500, MUTED)
            x += 76 + 7.6 * len(label)


def header(g, title, sub):
    g.text(40, 52, title, 26, 700)
    g.text(40, 82, sub, 15, 400, MUTED)


def uc_box(g, x, y, w, h, show_badge=True):
    g.rect(x, y, w, h, SETUP["fill"], SETUP["stroke"])
    g.text(x + 20, y + 32, "Unity Catalog", 13, 700, SETUP["text"])
    g.text(x + 20, y + 56, "lake_dev.sync_bakehouse", 15, 600, INK, mono=True)
    g.text(x + 20, y + 78, "Delta tables, Change Data Feed on", 13, 400, MUTED)
    ty = y + 98
    for t, mode in [("sales_franchises", "SNAPSHOT"), ("sales_customers", "TRIGGERED"), ("sales_transactions", "TRIGGERED")]:
        g.rect(x + 16, ty, w - 32, 34, "#FFFFFF", "#BFDBFE", rx=6, sw=1.5)
        g.text(x + 28, ty + 22, t, 13, 500, INK, mono=True)
        g.text(x + w - 28, ty + 22, mode, 11, 600, SETUP["text"], "end", mono=True)
        ty += 42
    if show_badge:
        g.badge(x + w - 12, y - 12, "lakebase_setup_dab", SETUP, "end")


def samples_box(g, x, y, w, h):
    g.rect(x, y, w, h, EXT["fill"], EXT["stroke"], dash=True)
    g.lines(x + 20, y + 34, [
        T("Unity Catalog", 13, 700, EXT["text"]),
        T("samples.bakehouse", 15, 600, INK, True),
        T("Databricks sample data", 13, 400, MUTED),
        T("read-only, not deployed", 13, 400, MUTED),
    ])


def db(g, x, y, w, h, c, name, rows):
    g.cyl(x, y, w, h, c)
    g.text(x + w / 2, y + 50, name, 18, 700, INK, "middle", mono=True)
    g.lines(x + w / 2, y + 76, rows, "middle", gap=21)


def app_box(g, x, y, w, h, name, sub="Streamlit · Databricks App", badge=True):
    g.rect(x, y, w, h, APP["fill"], APP["stroke"])
    g.text(x + 20, y + 32, "Databricks App", 13, 700, APP["text"])
    names = name if isinstance(name, list) else [name]
    for i, n in enumerate(names):
        g.text(x + 20, y + 56 + 20 * i, n, 15, 600, INK, mono=True)
    if sub:
        g.text(x + 20, y + 58 + 20 * len(names), sub, 13, 400, MUTED)
    if badge:
        g.badge(x + w - 12, y - 12, "lakebase_app_dab", APP, "end")


def architecture():
    g = Svg(1560, 780)
    header(g, "How data moves, and which bundle owns what",
           "Blue is deployed by lakebase_setup_dab, orange by lakebase_app_dab. Shown for the prod target.")

    samples_box(g, 40, 230, 230, 140)
    uc_box(g, 360, 170, 320, 240)

    # Lakebase project
    lx, ly, lw, lh = 790, 130, 450, 520
    g.rect(lx, ly, lw, lh, SETUP["tint"], SETUP["stroke"])
    g.badge(lx + lw - 12, ly - 12, "lakebase_setup_dab", SETUP, "end")
    g.text(lx + 22, ly + 34, "Lakebase project (Postgres 17)", 13, 700, SETUP["text"])
    g.text(lx + 22, ly + 58, "lakebase-bakehouse-demo", 16, 600, INK, mono=True)
    g.text(lx + 22, ly + 80, "branch production · endpoint primary · role lakebase_owner", 13, 400, MUTED)

    db(g, lx + 40, ly + 110, lw - 80, 170, SETUP, "databricks_postgres", [
        T("schema sync_bakehouse", 13, 500, INK, True),
        T("3 synced tables, read-only", 13, 400, MUTED),
        T("written only by the sync pipeline", 13, 400, MUTED),
    ])
    db(g, lx + 40, ly + 320, lw - 80, 150, APP, "app_db", [
        T("schema app · table comments", 13, 500, INK, True),
        T("read/write, owned by the app", 13, 400, MUTED),
    ])
    g.badge(lx + lw - 52, ly + 308, "lakebase_app_dab", APP, "end")

    app_box(g, 1320, 330, 210, 120, ["bakehouse-", "lakebase-viewer"], sub="Streamlit")

    # flows
    g.arrow("M270,300 L354,300")
    g.label(312, 288, [T("copy", 13, 700, INK)])

    g.arrow("M680,290 L826,290")
    g.label(752, 252, [T("synced tables", 13, 700, INK), T("Delta → Postgres", 12, 400, MUTED)])

    g.arrow("M1200,325 C1260,325 1270,370 1314,370")
    g.label(1262, 318, [T("read", 13, 700, INK)])
    g.arrow("M1320,415 C1270,415 1260,525 1206,525")
    g.label(1268, 505, [T("write", 13, 700, INK)])

    # jobs
    g.rect(360, 470, 320, 160, "#FFFFFF", SETUP["stroke"], dash=True)
    g.lines(380, 498, [
        T("Jobs (setup bundle)", 13, 700, SETUP["text"]),
        T("seed_source_tables", 13, 600, INK, True),
        T("   copies the samples, enables CDF", 12, 400, MUTED),
        T("simulate_changes", 13, 600, INK, True),
        T("   edits rows in the Delta tables", 12, 400, MUTED),
        T("trigger_lakebase_sync", 13, 600, INK, True),
        T("   refreshes the synced tables", 12, 400, MUTED),
    ], gap=19)
    g.arrow("M520,470 L520,416", CTRL, dash=True, sw=1.5)
    g.arrow("M680,590 C740,590 752,420 752,298", CTRL, dash=True, sw=1.5)

    legend(g, 40, 735, [
        ("box", SETUP, "owned by lakebase_setup_dab"),
        ("box", APP, "owned by lakebase_app_dab"),
        ("box", EXT, "external"),
        ("solid", INK, "data"),
        ("dash", CTRL, "job / trigger"),
    ])
    return g


if __name__ == "__main__":
    (HERE / "architecture.svg").write_text(architecture().render())
