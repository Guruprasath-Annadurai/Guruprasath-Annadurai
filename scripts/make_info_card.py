#!/usr/bin/env python3
"""
Hand-authored neofetch-style info card SVG. Lines fade + slide in
on a short stagger, then freeze.

    python scripts/make_info_card.py            # animated
    STATIC=1 python scripts/make_info_card.py    # frozen frame (Quick Look)

Edit the ROWS / TITLE constants below to update your own info --
this script does not fetch anything, it just renders what you type.
"""
import html
import os
from pathlib import Path

TITLE = "guruprasath@github"
ROWS = [
    ("Now", "Building Edora — EdTech for JEE/NEET"),
    ("Prev", "Creator of ResponsibleAI (bias testing)"),
    ("Stack", "Python · LLM tooling · AI Engineering"),
    ("Highlights", "pip install biasbuster"),
]

WIDTH = 490
PAD_X = 24
LINE_H = 30
TITLEBAR_H = 40
FONT = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
DIM = "#6e7681"

STAGGER = 0.12
DUR = 0.4


def esc(s: str) -> str:
    return html.escape(s)


def build_svg(static: bool) -> str:
    height = TITLEBAR_H + len(ROWS) * LINE_H + PAD_X

    rows_svg = []
    for i, (key, val) in enumerate(ROWS):
        y = TITLEBAR_H + PAD_X * 0.6 + i * LINE_H + LINE_H * 0.7
        delay = i * STAGGER
        line = (
            f'<tspan fill="{KEY_COLOR}">{esc(key)}</tspan>'
            f'<tspan fill="{DIM}">: </tspan>'
            f'<tspan fill="{VAL_COLOR}">{esc(val)}</tspan>'
        )
        if static:
            rows_svg.append(
                f'<text x="{PAD_X}" y="{y:.1f}" font-size="15">{line}</text>'
            )
        else:
            rows_svg.append(
                f'<g opacity="0" transform="translate(-12,0)">'
                f'<animate attributeName="opacity" from="0" to="1" dur="{DUR}s" '
                f'begin="{delay:.2f}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-12,0" to="0,0" dur="{DUR}s" begin="{delay:.2f}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
                f'<text x="{PAD_X}" y="{y:.1f}" font-size="15">{line}</text>'
                f'</g>'
            )

    dots = (
        '<circle cx="16" cy="20" r="6" fill="#ff5f56"/>'
        '<circle cx="36" cy="20" r="6" fill="#ffbd2e"/>'
        '<circle cx="56" cy="20" r="6" fill="#27c93f"/>'
    )

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8"
        fill="{BG}" stroke="{BORDER}"/>
  <path d="M0.5 8.5a8 8 0 0 1 8-8h{WIDTH - 17}a8 8 0 0 1 8 8v{TITLEBAR_H - 8.5}h-{WIDTH - 1}z"
        fill="{TITLEBAR}"/>
  <line x1="0" y1="{TITLEBAR_H}" x2="{WIDTH}" y2="{TITLEBAR_H}" stroke="{BORDER}"/>
  {dots}
  <text x="{WIDTH / 2}" y="25" font-size="13" fill="{DIM}" text-anchor="middle">{esc(TITLE)}</text>
  {''.join(rows_svg)}
</svg>
'''
    return svg


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    out = "info-card.svg"
    svg = build_svg(static)
    Path(out).write_text(svg)
    print(f"wrote {out}{' (static)' if static else ''}")
