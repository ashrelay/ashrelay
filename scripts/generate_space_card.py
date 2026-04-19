#!/usr/bin/env python3
"""
Generate a personal space-stats SVG card for the GitHub profile README.
Fetches live ISS position and calculates facts from a birthday.

Set the BIRTHDAY environment variable (YYYY-MM-DD) via:
  GitHub repo → Settings → Secrets and variables → Actions → Variables → New variable
  Name: BIRTHDAY
  Value: your date e.g. 2001-04-15
"""

import os
import json
import urllib.request
import urllib.error
from datetime import date, datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BIRTHDAY_STR = os.environ.get("BIRTHDAY", "2003-12-23")
CARD_WIDTH   = 330
CARD_HEIGHT  = 195

# Colours — match the profile dark theme exactly
BG     = "#0d0d0d"
BORDER = "#2a2a2a"
TITLE  = "#888888"
LABEL  = "#4d4d4d"
VALUE  = "#777777"
DIM    = "#333333"
ACCENT = "#555555"

# ── Calculations ──────────────────────────────────────────────────────────────
def compute_stats(birthday: date, today: date) -> dict:
    days = (today - birthday).days
    return {
        "days_operational" : f"{days:,}",
        "iss_orbits"       : f"{int(days * 15.53):,}",    # ISS ~15.53 orbits/day
        "earth_km"         : fmt_km(days),                # km Earth travels/year ÷ 365.25 × days
        "moon_cycles"      : f"{days / 29.53:.1f}",
        "solar_laps"       : f"{days / 365.25:.2f}",
    }

def fmt_km(days: int) -> str:
    km = days * (940_000_000 / 365.25)
    if km >= 1_000_000_000:
        return f"{km / 1_000_000_000:.2f}B km"
    return f"{km / 1_000_000:.1f}M km"

def fetch_iss() -> str:
    """Fetch live ISS lat/lon via HTTPS. Falls back gracefully."""
    try:
        url = "https://api.wheretheiss.at/v1/satellites/25544"
        req = urllib.request.Request(url, headers={"User-Agent": "github-readme-bot/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
            lat = float(data["latitude"])
            lon = float(data["longitude"])
            return f"{lat:+.2f}°,  {lon:+.2f}°"
    except Exception:
        return "location: classified"

# ── SVG builder ───────────────────────────────────────────────────────────────
def build_svg(stats: dict, iss_pos: str, birthday: date, today: date) -> str:
    rows = [
        ("days operational",      stats["days_operational"]),
        ("ISS orbits since birth", stats["iss_orbits"]),
        ("earth km traveled",     stats["earth_km"]),
        ("lunar cycles done",     stats["moon_cycles"]),
        ("laps around the sun",   stats["solar_laps"]),
        ("ISS is right now at",   iss_pos),
    ]

    ROW_Y_START = 58
    ROW_GAP     = 22
    LX          = 16          # label left x
    VX          = CARD_WIDTH - 16  # value right x (text-anchor=end)

    rows_svg = ""
    for i, (label, value) in enumerate(rows):
        y = ROW_Y_START + i * ROW_GAP
        rows_svg += (
            f'  <text x="{LX}" y="{y}" font-family="\'Courier New\',Courier,monospace" '
            f'font-size="10.5" fill="{LABEL}">{label}</text>\n'
            f'  <text x="{VX}" y="{y}" text-anchor="end" font-family="\'Courier New\',Courier,monospace" '
            f'font-size="10.5" fill="{VALUE}">{value}</text>\n'
        )

    updated = today.strftime("%Y-%m-%d")

    return f"""<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <!-- background -->
  <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="6" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>

  <!-- title -->
  <text x="{LX}" y="22" font-family="'Courier New',Courier,monospace" font-size="13" font-weight="bold" fill="{TITLE}">cosmic damage report</text>
  <text x="{LX}" y="36" font-family="'Courier New',Courier,monospace" font-size="9" fill="{DIM}">(you in numbers that don't help)</text>

  <!-- divider -->
  <line x1="{LX}" y1="43" x2="{CARD_WIDTH - LX}" y2="43" stroke="{BORDER}" stroke-width="1"/>

  <!-- rows -->
{rows_svg}
  <!-- footer divider -->
  <line x1="{LX}" y1="{CARD_HEIGHT - 18}" x2="{CARD_WIDTH - LX}" y2="{CARD_HEIGHT - 18}" stroke="{DIM}" stroke-width="0.5"/>

  <!-- updated timestamp -->
  <text x="{CARD_WIDTH // 2}" y="{CARD_HEIGHT - 7}" font-family="'Courier New',Courier,monospace" font-size="8" fill="{DIM}" text-anchor="middle">updated {updated} · ISS position live</text>
</svg>
"""

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    try:
        birthday = datetime.strptime(BIRTHDAY_STR, "%Y-%m-%d").date()
    except ValueError:
        print(f"[!] Invalid BIRTHDAY value: '{BIRTHDAY_STR}'. Expected YYYY-MM-DD.")
        print("    Using fallback date 2000-01-01 — set the BIRTHDAY variable in repo settings.")
        birthday = date(2000, 1, 1)

    today = date.today()

    if birthday >= today:
        print("[!] BIRTHDAY is in the future. Check the value.")
        birthday = date(2000, 1, 1)

    print(f"[·] Birthday : {birthday}")
    print(f"[·] Today    : {today}")
    print(f"[·] Days     : {(today - birthday).days:,}")

    stats   = compute_stats(birthday, today)
    iss_pos = fetch_iss()

    print(f"[·] ISS      : {iss_pos}")

    svg = build_svg(stats, iss_pos, birthday, today)

    out = Path("generated/space-stats.svg")
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"[ok] Saved   : {out}")

if __name__ == "__main__":
    main()
