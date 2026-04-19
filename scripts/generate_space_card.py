#!/usr/bin/env python3
"""
Cosmic Damage Report — GitHub profile README card.

Pulls live asteroid data from NASA NeoWs and earthquake data from USGS.
Runs daily via GitHub Actions. No API keys required.

Set BIRTHDAY in: GitHub repo → Settings → Secrets and variables → Actions → Variables
"""

import os
import json
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BIRTHDAY_STR = os.environ.get("BIRTHDAY", "2003-12-23")
CARD_WIDTH   = 330
CARD_HEIGHT  = 195

# Colours — match profile dark theme
BG     = "#0d0d0d"
BORDER = "#2a2a2a"
TITLE  = "#888888"
LABEL  = "#4d4d4d"
VALUE  = "#777777"
DIM    = "#2e2e2e"
SNARK  = "#3d3d3d"

# ── Helpers ───────────────────────────────────────────────────────────────────
def _get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "github-readme-bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def fmt_n(n): return f"{n:,}"

def days_until_bday(birthday: date, today: date) -> int:
    ny = date(today.year, birthday.month, birthday.day)
    if ny <= today:
        ny = date(today.year + 1, birthday.month, birthday.day)
    return (ny - today).days

# ── Live data fetchers ────────────────────────────────────────────────────────
def fetch_asteroid():
    """Closest near-Earth asteroid this week via NASA NeoWs (DEMO_KEY)."""
    try:
        today = date.today()
        end   = today + timedelta(days=7)
        data  = _get(
            f"https://api.nasa.gov/neo/rest/v1/feed"
            f"?start_date={today}&end_date={end}&api_key=DEMO_KEY"
        )
        rocks = []
        for _, group in data.get("near_earth_objects", {}).items():
            for a in group:
                approaches = a.get("close_approach_data", [])
                if not approaches:
                    continue
                closest_km = min(float(x["miss_distance"]["kilometers"]) for x in approaches)
                raw_name   = a["name"].replace("(", "").replace(")", "").strip()
                name       = raw_name[:17] + "…" if len(raw_name) > 18 else raw_name
                rocks.append({"name": name, "km": closest_km,
                              "hazardous": a["is_potentially_hazardous_asteroid"]})
        if not rocks:
            return "2024 YR4", "3.1M km"
        closest = min(rocks, key=lambda x: x["km"])
        return closest["name"], f"{closest['km'] / 1_000_000:.1f}M km"
    except Exception:
        return "2024 YR4", "3.1M km"

def fetch_earthquake():
    """Most recent significant earthquake via USGS GeoJSON feed (no key)."""
    try:
        # Try significant events first, fall back to 4.5+ week
        for url in [
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson",
        ]:
            data     = _get(url)
            features = data.get("features", [])
            if features:
                break
        if not features:
            return "no activity", "suspiciously quiet"
        p     = features[0]["properties"]
        mag   = p.get("mag", "?")
        place = p.get("place", "somewhere on Earth") or "somewhere on Earth"
        place = place[:28] + "…" if len(place) > 29 else place
        return f"{mag}M", place
    except Exception:
        return "7.1M", "somewhere, Earth"

# ── SVG builder ───────────────────────────────────────────────────────────────
def build_svg(birthday: date, today: date) -> str:
    days  = (today - birthday).days
    laps  = f"{days / 365.25:.2f}"
    tbday = days_until_bday(birthday, today)

    ast_name, ast_dist = fetch_asteroid()
    eq_mag,   eq_place = fetch_earthquake()
    updated            = today.strftime("%Y-%m-%d")

    LX = 16
    VX = CARD_WIDTH - 16

    def row(y, label, value, font="10.5"):
        return (
            f'  <text x="{LX}" y="{y}" font-family="\'Courier New\',Courier,monospace" '
            f'font-size="{font}" fill="{LABEL}">{label}</text>\n'
            f'  <text x="{VX}" y="{y}" text-anchor="end" '
            f'font-family="\'Courier New\',Courier,monospace" '
            f'font-size="{font}" fill="{VALUE}">{value}</text>\n'
        )

    def note(y, text):
        return (
            f'  <text x="{LX}" y="{y}" font-family="\'Courier New\',Courier,monospace" '
            f'font-size="8.5" fill="{SNARK}">{text}</text>\n'
        )

    def div(y, color=DIM, w="0.5"):
        return f'  <line x1="{LX}" y1="{y}" x2="{CARD_WIDTH-LX}" y2="{y}" stroke="{color}" stroke-width="{w}"/>\n'

    return (
        f'<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="6" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>\n'

        # title
        f'  <text x="{LX}" y="21" font-family="\'Courier New\',Courier,monospace" font-size="13" font-weight="bold" fill="{TITLE}">cosmic damage report</text>\n'
        f'  <text x="{LX}" y="33" font-family="\'Courier New\',Courier,monospace" font-size="8.5" fill="{DIM}">(you in numbers that don\'t help)</text>\n'
        + div(40, BORDER, "1")

        # personal stats
        + row(55,  "days operational",      fmt_n(days))
        + row(70,  "laps around the sun",   laps)
        + row(85,  "days to fix your life", fmt_n(tbday))
        + div(93)

        # asteroid section
        + row(106, f"nearest asteroid · {ast_name}", ast_dist, "10")
        + note(117, "— let's hope. evolution deserves another shot.")
        + div(124)

        # earthquake section
        + row(137, f"latest quake · {eq_mag}", eq_place, "10")
        + note(148, "— tectonic plates shifted. your semicolon though.")
        + div(155)

        # people in space
        + row(168, "people currently off-planet", "not you")

        # footer
        + div(177)
        + f'  <text x="{CARD_WIDTH//2}" y="188" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="7.5" fill="{DIM}" text-anchor="middle">updated {updated} · live NASA + USGS data</text>\n'
        f'</svg>\n'
    )

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    try:
        birthday = datetime.strptime(BIRTHDAY_STR, "%Y-%m-%d").date()
    except ValueError:
        print(f"[!] Bad BIRTHDAY value: '{BIRTHDAY_STR}' — using 2003-12-23")
        birthday = date(2003, 12, 23)

    today = date.today()
    print(f"[·] Birthday : {birthday}")
    print(f"[·] Today    : {today}")
    print(f"[·] Days     : {(today - birthday).days:,}")

    svg = build_svg(birthday, today)
    out = Path("generated/space-stats.svg")
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"[ok] Saved   : {out}")

if __name__ == "__main__":
    main()
