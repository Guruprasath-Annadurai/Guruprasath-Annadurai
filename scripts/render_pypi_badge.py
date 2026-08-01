#!/usr/bin/env python3
"""
Render data/pypi_stats.json as a terminal-styled stat card: real
PyPI download numbers for a shipped package, plus a sparkline that
draws itself in once and freezes.

    python scripts/render_pypi_badge.py
"""
import json
import sys
from pathlib import Path

WIDTH = 860
HEIGHT = 150
PAD_X = 28
BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
GREEN = "#39d353"
DIM = "#7d8590"
TEXT = "#c9d1d9"
TITLEBAR_H = 34

SPARK_W = 300
SPARK_H = 46


def sparkline_path(series: list[dict]) -> tuple[str, float]:
    if not series:
        return "", 0
    values = [d["downloads"] for d in series]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = (i / max(n - 1, 1)) * SPARK_W
        y = SPARK_H - ((v - lo) / span) * SPARK_H
        pts.append((x, y))
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    length = sum(
        ((pts[i][0] - pts[i - 1][0]) ** 2 + (pts[i][1] - pts[i - 1][1]) ** 2) ** 0.5
        for i in range(1, len(pts))
    )
    return d, length


def build_svg(data: dict) -> str:
    package = data["package"]
    total = data["total_all_time"]
    month = data["last_month"]
    week = data["last_week"]
    spark_d, spark_len = sparkline_path(data.get("series", []))

    # Dynamic spacing for the "N last 30d   M last 7d" row so wider
    # numbers (3+ digits) never collide with their label.
    num_w, label_w, gap = 10.8, 7.2, 10
    stat2_label1_x = PAD_X + len(str(month)) * num_w + gap
    stat2_week_x = stat2_label1_x + len("last 30d") * label_w + gap * 2.5
    stat2_label2_x = stat2_week_x + len(str(week)) * num_w + gap

    spark_x = WIDTH - PAD_X - SPARK_W
    spark_y = TITLEBAR_H + 34

    svg = f'''<svg viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, 'SF Mono', Menlo, Consolas, monospace">
  <style>
    .stat {{ opacity: 0; animation: rise 0.5s cubic-bezier(0.25,0.1,0.25,1) forwards; }}
    .stat.d1 {{ animation-delay: 0.05s; }}
    .stat.d2 {{ animation-delay: 0.20s; }}
    .stat.d3 {{ animation-delay: 0.35s; }}
    @keyframes rise {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .spark {{
      stroke-dasharray: {spark_len:.1f};
      stroke-dashoffset: {spark_len:.1f};
      animation: draw 1.1s 0.5s cubic-bezier(0.25,0.1,0.25,1) forwards;
    }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  </style>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
  <path d="M0.5 8.5a8 8 0 0 1 8-8h{WIDTH - 17}a8 8 0 0 1 8 8v{TITLEBAR_H - 8.5}h-{WIDTH - 1}z" fill="{TITLEBAR}"/>
  <line x1="0" y1="{TITLEBAR_H}" x2="{WIDTH}" y2="{TITLEBAR_H}" stroke="{BORDER}"/>
  <circle cx="16" cy="17" r="6" fill="#ff5f56"/>
  <circle cx="36" cy="17" r="6" fill="#ffbd2e"/>
  <circle cx="56" cy="17" r="6" fill="#27c93f"/>
  <text x="{WIDTH / 2}" y="22" font-size="12" fill="{DIM}" text-anchor="middle">$ pip install {package}</text>

  <g class="stat d1">
    <text x="{PAD_X}" y="{TITLEBAR_H + 42}" font-size="34" fill="{GREEN}" font-weight="bold">{total:,}</text>
    <text x="{PAD_X}" y="{TITLEBAR_H + 60}" font-size="12" fill="{DIM}">downloads all-time (PyPI)</text>
  </g>

  <g class="stat d2">
    <text x="{PAD_X}" y="{TITLEBAR_H + 94}" font-size="18" fill="{TEXT}">{month}</text>
    <text x="{stat2_label1_x:.1f}" y="{TITLEBAR_H + 94}" font-size="12" fill="{DIM}">last 30d</text>
    <text x="{stat2_week_x:.1f}" y="{TITLEBAR_H + 94}" font-size="18" fill="{TEXT}">{week}</text>
    <text x="{stat2_label2_x:.1f}" y="{TITLEBAR_H + 94}" font-size="12" fill="{DIM}">last 7d</text>
  </g>

  <g transform="translate({spark_x},{spark_y})">
    <g class="stat d3">
      <path d="{spark_d}" fill="none" stroke="{GREEN}" stroke-width="2" class="spark"
            stroke-linecap="round" stroke-linejoin="round"/>
      <text x="0" y="-10" font-size="11" fill="{DIM}">last 180 days</text>
    </g>
  </g>
</svg>
'''
    return svg


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/pypi_stats.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "pypi-badge.svg"

    if not Path(src).exists():
        print(f"error: {src} not found. Run scripts/fetch_pypi_stats.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(Path(src).read_text())
    svg = build_svg(data)
    Path(out).write_text(svg)
    print(f"wrote {out}")
