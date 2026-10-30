#!/usr/bin/env python3
"""Build data.json for the Ici-Trouille dashboard.

Source: public, unauthenticated endpoints of icitrouille.fr
  - /api/houses  (houses, used only for aggregation)
  - /api/recap   (server-side aggregates)

Privacy: only aggregates are written. No address, id, coordinates or code
ever leaves this script, because the repo is public.

Dating: there is no creation date in the public API, so each house is dated
by its `updatedAt` (Europe/Paris day). This is an approximation by design.

Usage: python3 scripts/collect.py [--out data.json]
"""
import argparse
import collections
import datetime as dt
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

BASE = "https://icitrouille.fr"
PARIS = ZoneInfo("Europe/Paris")
UA = "icitrouille-dashboard/1.0 (+https://github.com/misterbenj34/icitrouille-dashboard)"


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_utc(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def build(houses_payload, recap_payload, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    houses = houses_payload.get("houses", [])

    dated = [(parse_utc(h["updatedAt"]), h) for h in houses if h.get("updatedAt")]
    per_day = collections.Counter(t.astimezone(PARIS).date() for t, _ in dated)

    if per_day:
        first = min(per_day)
        last = max(max(per_day), now.astimezone(PARIS).date())
        days = []
        cum = 0
        d = first
        while d <= last:
            added = per_day.get(d, 0)
            cum += added
            days.append({"date": d.isoformat(), "added": added, "total": cum})
            d += dt.timedelta(days=1)
    else:
        days = []

    last_24h = sum(1 for t, _ in dated if now - t <= dt.timedelta(hours=24))
    last_7d = sum(1 for t, _ in dated if now - t <= dt.timedelta(days=7))
    cities = {h["address"]["city"] for h in houses if h.get("address", {}).get("city")}
    participation = collections.Counter(h.get("participation") for h in houses)
    recap = recap_payload.get("recap", {})

    return {
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dating": "updatedAt (approximation, Europe/Paris day)",
        "totals": {
            "houses": len(houses),
            "last_24h": last_24h,
            "last_7d": last_7d,
            "cities": len(cities),
            "welcome": participation.get("welcome", 0),
            "do_not_disturb": participation.get("do_not_disturb", 0),
        },
        "recap": recap,
        "daily": days,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data.json"))
    args = ap.parse_args()

    data = build(fetch("/api/houses"), fetch("/api/recap"))
    out = os.path.abspath(args.out)

    # Only rewrite when the aggregates changed, so the auto-commit stays quiet.
    previous = None
    if os.path.exists(out):
        with open(out, encoding="utf8") as f:
            previous = json.load(f)
    if previous and {k: v for k, v in previous.items() if k != "generated_at"} == \
            {k: v for k, v in data.items() if k != "generated_at"}:
        print("unchanged")
        return

    with open(out, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("updated", out, data["totals"])


if __name__ == "__main__":
    main()
