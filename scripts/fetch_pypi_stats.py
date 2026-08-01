#!/usr/bin/env python3
"""
Fetch real PyPI download stats for a package via the public
pypistats.org API -- no auth needed.

    python scripts/fetch_pypi_stats.py [package_name]

Writes data/pypi_stats.json with recent totals plus a daily
timeseries (last ~180 days) for a sparkline.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

DEFAULT_PACKAGE = "rai-governance-platform"
UA = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"


def fetch(url: str) -> dict:
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    package = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PACKAGE

    recent = fetch(f"https://pypistats.org/api/packages/{package}/recent")["data"]
    overall = fetch(f"https://pypistats.org/api/packages/{package}/overall?mirrors=false")["data"]

    cutoff = (datetime.utcnow() - timedelta(days=180)).date().isoformat()
    series = sorted(
        [{"date": d["date"], "downloads": d["downloads"]} for d in overall if d["date"] >= cutoff],
        key=lambda d: d["date"],
    )
    total_all_time = sum(d["downloads"] for d in overall)

    out = {
        "package": package,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "last_day": recent.get("last_day", 0),
        "last_week": recent.get("last_week", 0),
        "last_month": recent.get("last_month", 0),
        "total_all_time": total_all_time,
        "series": series,
    }

    out_path = Path("data/pypi_stats.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path} (last_month={out['last_month']}, all_time={total_all_time})")
