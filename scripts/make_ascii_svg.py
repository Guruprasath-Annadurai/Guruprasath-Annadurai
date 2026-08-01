#!/usr/bin/env python3
"""
Convert source-prepped.png into avi-ascii.svg: a monochrome ASCII
portrait that types itself in row by row (SMIL clip-path wipes),
then freezes. No loop.

    python scripts/make_ascii_svg.py
"""
import html
import sys
from pathlib import Path

from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS = 100
CHAR_W = 6.0
CHAR_H = 11.0
FILL = "#8b949e"          # single light-gray fill, no rainbow
ROW_DUR = 0.6              # seconds per row wipe
ROW_STAGGER = 0.035        # seconds between row starts


def image_to_rows(img_path: str, cols: int = COLS) -> list[str]:
    img = Image.open(img_path).convert("L")
    aspect = img.height / img.width
    rows = max(1, round(cols * aspect * (CHAR_W / CHAR_H)))
    small = img.resize((cols, rows))
    px = small.load()

    lines = []
    for y in range(rows):
        line = []
        for x in range(cols):
            brightness = px[x, y]
            idx = round((1 - brightness / 255) * (len(RAMP) - 1))
            line.append(RAMP[idx])
        lines.append("".join(line).rstrip() or " ")
    return lines


def build_svg(lines: list[str]) -> str:
    cols = max(len(l) for l in lines) or 1
    rows = len(lines)
    width = cols * CHAR_W
    height = rows * CHAR_H

    defs = []
    body = []

    for i, line in enumerate(lines):
        row_width = len(line) * CHAR_W
        y = (i + 1) * CHAR_H - 2.5
        begin = round(i * ROW_STAGGER, 3)
        clip_id = f"clip{i}"

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{i * CHAR_H}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{row_width}" '
            f'dur="{ROW_DUR}s" begin="{begin}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f'</rect></clipPath>'
        )

        escaped = html.escape(line)
        body.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y}" xml:space="preserve">{escaped}</text>'
            f'</g>'
        )

        cursor_x_id = f"cursor{i}"
        body.append(
            f'<rect class="cursor" x="0" y="{i * CHAR_H + 1}" '
            f'width="{CHAR_W * 0.7}" height="{CHAR_H - 2}">'
            f'<animate attributeName="x" from="0" to="{max(row_width - CHAR_W, 0)}" '
            f'dur="{ROW_DUR}s" begin="{begin}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f'<animate attributeName="opacity" from="1" to="0" dur="0.15s" '
            f'begin="{begin + ROW_DUR}s" fill="freeze"/>'
            f'</rect>'
        )

    svg = f'''<svg viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.0f}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
     font-size="{CHAR_H - 1.5:.1f}px">
  <style>
    text {{ fill: {FILL}; }}
    .cursor {{ fill: #39d353; }}
  </style>
  <defs>
    {''.join(defs)}
  </defs>
  {''.join(body)}
</svg>
'''
    return svg


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"

    if not Path(src).exists():
        print(f"error: {src} not found. Run scripts/prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    lines = image_to_rows(src)
    svg = build_svg(lines)
    Path(out).write_text(svg)
    print(f"wrote {out} ({len(lines)} rows)")
