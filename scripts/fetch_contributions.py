#!/usr/bin/env python3
"""
Fetch a GitHub user's public contribution calendar -- no token, no
GraphQL API. GitHub serves it as an HTML fragment at
https://github.com/users/<username>/contributions, the same markup
the profile page itself uses.

Writes data/contributions.json with raw days plus derived stats.

    python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "Guruprasath-Annadurai"
UA = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if cells:
        tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.select("tool-tip[for]")}
        for cell in cells:
            d = cell["data-date"]
            level = int(cell.get("data-level", 0))
            tip = tooltips.get(cell.get("id"), "")
            m = re.match(r"([\d,]+)\s+contribution", tip)
            count = int(m.group(1).replace(",", "")) if m else (0 if level == 0 else level)
            days.append({"date": d, "count": count, "level": level})
        return days

    # Fallback: older markup uses rect with title attribute.
    rects = soup.select("rect[data-date], rect.ContributionCalendar-day")
    for rect in rects:
        d = rect.get("data-date")
        if not d:
            continue
        level = int(rect.get("data-level", 0))
        title = rect.get("title", "")
        m = re.match(r"([\d,]+)\s+contribution", title)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": d, "count": count, "level": level})
    return days


def derive_stats(days: list[dict]) -> dict:
    days_sorted = sorted(days, key=lambda d: d["date"])
    total = sum(d["count"] for d in days_sorted)

    longest = current = 0
    running = 0
    today = date.today().isoformat()
    for d in days_sorted:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak: walk backwards from the most recent day with data
    running = 0
    for d in reversed(days_sorted):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            running += 1
        else:
            break
    current = running

    best_day = max(days_sorted, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days_sorted:
        month = d["date"][:7]
        monthly[month] += d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": dict(sorted(monthly.items())),
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    html = fetch_html(username)
    days = parse_days(html)

    if not days:
        print("error: no contribution cells parsed -- GitHub markup may have changed", file=sys.stderr)
        sys.exit(1)

    stats = derive_stats(days)
    out = {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    out_path = Path("data/contributions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path} ({len(days)} days, {stats['total']} contributions)")
