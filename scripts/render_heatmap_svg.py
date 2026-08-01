#!/usr/bin/env python3
"""
Render data/contributions.json as the classic 53-week x 7-day
contribution calendar: rounded colored boxes that slide in
diagonally on load, then freeze (no looping "glow"), plus a
Less->More legend and a stats footer.

    python scripts/render_heatmap_svg.py
"""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 28
TOP_PAD = 20
LEGEND_H = 24
FOOTER_H = 26

WEEKS = 53
DUR = 0.5
STAGGER = 0.012


def load_days(data: dict) -> dict[str, dict]:
    return {d["date"]: d for d in data["days"]}


def build_grid(day_map: dict[str, dict]) -> list[list[dict | None]]:
    if not day_map:
        return []

    dates = sorted(day_map.keys())
    latest = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    earliest_needed = latest - timedelta(weeks=WEEKS - 1)
    # align to the Sunday on/before earliest_needed
    dow_sun0 = (earliest_needed.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0
    start = earliest_needed - timedelta(days=dow_sun0)

    grid: list[list[dict | None]] = [[] for _ in range(WEEKS)]
    cur = start
    week_idx = 0
    while cur <= latest:
        day_of_week = (cur.weekday() + 1) % 7  # Sun=0..Sat=6
        entry = day_map.get(cur.isoformat())
        grid[week_idx].append(entry or {"date": cur.isoformat(), "count": 0, "level": 0})
        if day_of_week == 6:
            week_idx += 1
        cur += timedelta(days=1)

    return [w for w in grid if w]


def color_for(entry: dict, p95: float) -> str:
    if not entry or entry["count"] == 0:
        return PALETTE[0]
    level = min(max(entry.get("level", 1), 1), 4)
    if level == 4 and entry["count"] >= p95 and p95 > 0:
        return PALETTE[5]
    return PALETTE[level]


def percentile95(day_map: dict[str, dict]) -> float:
    counts = sorted(d["count"] for d in day_map.values() if d["count"] > 0)
    if not counts:
        return 0
    idx = int(len(counts) * 0.95)
    return counts[min(idx, len(counts) - 1)]


def build_svg(data: dict) -> str:
    day_map = load_days(data)
    grid = build_grid(day_map)
    p95 = percentile95(day_map)
    stats = data.get("stats", {})

    n_weeks = len(grid)
    width = LEFT_PAD + n_weeks * CELL + GAP
    height = TOP_PAD + 7 * CELL + LEGEND_H + FOOTER_H

    month_labels = []
    seen_months = set()
    for wi, week in enumerate(grid):
        for entry in week:
            m = entry["date"][:7]
            if m not in seen_months:
                seen_months.add(m)
                label = datetime.strptime(entry["date"], "%Y-%m-%d").strftime("%b")
                month_labels.append((wi, label))
                break

    boxes = []
    for wi, week in enumerate(grid):
        for entry in week:
            di = (datetime.strptime(entry["date"], "%Y-%m-%d").weekday() + 1) % 7
            x = LEFT_PAD + wi * CELL
            y = TOP_PAD + di * CELL
            fill = color_for(entry, p95)
            diag = wi + di
            delay = round(diag * STAGGER, 3)
            title = f"{entry['count']} contributions on {entry['date']}"
            boxes.append(
                f'<rect class="box" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" '
                f'fill="{fill}" style="animation-delay:{delay}s">'
                f'<title>{title}</title></rect>'
            )

    months_svg = "".join(
        f'<text x="{LEFT_PAD + wi * CELL}" y="{TOP_PAD - 6}" font-size="10" fill="#7d8590">{label}</text>'
        for wi, label in month_labels
    )

    legend_x = width - LEFT_PAD - 5 * (BOX + 4) - 40
    legend_boxes = "".join(
        f'<rect x="{legend_x + 30 + i * (BOX + 4)}" y="{height - FOOTER_H - LEGEND_H + 6}" '
        f'width="{BOX}" height="{BOX}" rx="2" fill="{PALETTE[i]}"/>'
        for i in range(5)
    )
    legend = (
        f'<text x="{legend_x}" y="{height - FOOTER_H - LEGEND_H + 6 + BOX - 1}" '
        f'font-size="10" fill="#7d8590">Less</text>'
        f'{legend_boxes}'
        f'<text x="{legend_x + 30 + 5 * (BOX + 4) + 4}" y="{height - FOOTER_H - LEGEND_H + 6 + BOX - 1}" '
        f'font-size="10" fill="#7d8590">More</text>'
    )

    total = stats.get("total", sum(e["count"] for w in grid for e in w))
    streak = stats.get("longest_streak", 0)
    cur_streak = stats.get("current_streak", 0)
    footer = (
        f'<text x="{LEFT_PAD}" y="{height - 8}" font-size="11" fill="#7d8590">'
        f'{total:,} contributions in the last year &#8226; '
        f'longest streak {streak}d &#8226; current streak {cur_streak}d</text>'
    )

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, 'SF Mono', Menlo, Consolas, monospace">
  <style>
    .box {{
      opacity: 0;
      transform: translateY(-8px);
      animation: slideIn {DUR}s cubic-bezier(0.25,0.1,0.25,1) forwards;
    }}
    @keyframes slideIn {{
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
  {months_svg}
  {''.join(boxes)}
  {legend}
  {footer}
</svg>
'''
    return svg


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

    if not Path(src).exists():
        print(f"error: {src} not found. Run scripts/fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(Path(src).read_text())
    svg = build_svg(data)
    Path(out).write_text(svg)
    print(f"wrote {out}")
