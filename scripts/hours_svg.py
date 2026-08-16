#!/usr/bin/env python3
"""Render assets/hours.svg from WakaTime last-7-days stats.

Run by .github/workflows/waka-readme.yml. If the API can't be reached the
existing SVG is left untouched rather than being replaced with empty data.
"""
import base64
import json
import math
import os
import sys
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "hours.svg")
API = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
MONO = "ui-monospace,'JetBrains Mono','Fira Code',Consolas,monospace"
BG = "#000000"

# Stable colour per language; anything unknown cycles through the tail palette.
LANG_COLOURS = {
    "Python": "#4B8BBE", "TypeScript": "#3178C6", "JavaScript": "#F7DF1E",
    "Bash": "#3FB950", "Shell": "#3FB950", "Markdown": "#8B949E",
    "YAML": "#FF7B72", "JSON": "#FFA657", "HTML": "#E34F26", "CSS": "#1572B6",
    "C++": "#00599C", "C": "#5599DD", "Java": "#F89820", "Go": "#00ADD8",
    "Rust": "#DEA584", "SQL": "#4169E1", "Docker": "#2496ED", "Other": "#6E7681",
}
FALLBACK = ["#BC8CFF", "#56D4DD", "#FF8C69", "#4ADE80", "#A78BFA", "#FFD21E"]


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def fetch(key):
    req = urllib.request.Request(API)
    req.add_header("Authorization",
                   "Basic " + base64.b64encode(key.encode()).decode())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]


def render(total_text, rng, langs):
    """langs: list of (name, time_text, percent)."""
    W, H = 900, 330
    cx, cy, R = 208, 178, 104
    s = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    # ---- header
    s.append(f'<text x="40" y="46" font-family="{MONO}" font-size="13" font-weight="700" '
             f'letter-spacing=".22em" fill="#8B949E">WHERE THE HOURS GO</text>')
    s.append(f'<text x="40" y="70" font-family="{MONO}" font-size="11.5" '
             f'fill="#4A4A4A">{esc(rng)}</text>')

    # ---- dial: arc lengths are the real percentages
    for r in (R * 0.56, R * 0.79, R):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="none" stroke="#141414" '
                 f'stroke-width="1"/>')
    for h in range(24):
        a = math.radians(h * 15 - 90)
        r1 = R * (0.93 if h % 6 else 0.86)
        s.append(f'<line x1="{cx+r1*math.cos(a):.1f}" y1="{cy+r1*math.sin(a):.1f}" '
                 f'x2="{cx+R*math.cos(a):.1f}" y2="{cy+R*math.sin(a):.1f}" '
                 f'stroke="{"#3A3A3A" if h % 6 else "#242424"}" stroke-width="1.4"/>')

    ang = -90.0
    for i, (name, _t, pct) in enumerate(langs):
        col = LANG_COLOURS.get(name, FALLBACK[i % len(FALLBACK)])
        sweep = max(pct, 0.0) * 3.6                      # percent -> degrees
        if sweep < 0.4:
            continue
        a0, a1 = math.radians(ang), math.radians(ang + sweep)
        rr = R * 0.70
        large = 1 if sweep > 180 else 0
        d = (f"M{cx+rr*math.cos(a0):.1f} {cy+rr*math.sin(a0):.1f} "
             f"A{rr:.1f} {rr:.1f} 0 {large} 1 {cx+rr*math.cos(a1):.1f} {cy+rr*math.sin(a1):.1f}")
        # arc length so the stroke can draw itself on
        length = 2 * math.pi * rr * (sweep / 360.0)
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="13" '
                 f'stroke-linecap="butt" stroke-dasharray="{length:.1f}" '
                 f'stroke-dashoffset="{length:.1f}">'
                 f'<animate attributeName="stroke-dashoffset" values="{length:.1f};0" '
                 f'dur="1.1s" begin="{0.15*i:.2f}s" fill="freeze" calcMode="spline" '
                 f'keySplines="0.2 0.7 0.3 1"/>'
                 f'<animate attributeName="opacity" values="1;.55;1" dur="{3.0+i*0.4:.1f}s" '
                 f'begin="{1.2+0.15*i:.2f}s" repeatCount="indefinite"/></path>')
        ang += sweep

    # total in the middle
    s.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-family="{MONO}" '
             f'font-size="24" font-weight="700" fill="#FFFFFF">{esc(total_text.split(" hr")[0])}'
             f'<tspan font-size="13" fill="#8B949E"> hrs</tspan></text>')
    s.append(f'<text x="{cx}" y="{cy+20}" text-anchor="middle" font-family="{MONO}" '
             f'font-size="10.5" letter-spacing=".18em" fill="#4A4A4A">LAST 7 DAYS</text>')

    # ---- rows: real language, real time, real percent
    lx, ly, bw = 400, 118, 300
    for i, (name, t, pct) in enumerate(langs):
        col = LANG_COLOURS.get(name, FALLBACK[i % len(FALLBACK)])
        y = ly + i * 32
        s.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.45s" '
            f'begin="{0.12*i:.2f}s" fill="freeze"/>'
            f'<circle cx="{lx}" cy="{y-4}" r="4.2" fill="{col}">'
            f'<animate attributeName="opacity" values="1;.35;1" dur="{2.4+i*0.3:.1f}s" '
            f'begin="{i*0.3:.2f}s" repeatCount="indefinite"/></circle>'
            f'<text x="{lx+15}" y="{y}" font-family="{MONO}" font-size="12" '
            f'font-weight="700" fill="{col}">{esc(name)}</text>'
            f'<text x="{lx+140}" y="{y}" font-family="{MONO}" font-size="11" '
            f'fill="#8B949E">{esc(t)}</text>'
            f'<rect x="{lx+15}" y="{y+6}" width="{bw}" height="5" rx="2.5" fill="#141414"/>'
            f'<rect x="{lx+15}" y="{y+6}" width="0" height="5" rx="2.5" fill="{col}" '
            f'fill-opacity=".85">'
            f'<animate attributeName="width" values="0;{bw*pct/100:.1f}" dur="1.2s" '
            f'begin="{0.2+0.12*i:.2f}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 0.7 0.3 1"/></rect>'
            f'<text x="{lx+bw+26}" y="{y}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" font-weight="700" fill="{col}">{pct:.1f}%</text></g>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}" role="img">\n' + "\n".join(s) + "\n</svg>\n")


def main():
    key = os.environ.get("WAKATIME_API_KEY", "").strip()
    if not key:
        print("no WAKATIME_API_KEY; leaving hours.svg untouched")
        return 0
    try:
        d = fetch(key)
    except Exception as e:                      # noqa: BLE001 - never fail the build
        print(f"wakatime fetch failed ({e}); leaving hours.svg untouched")
        return 0

    langs = [(l["name"], l["text"], float(l["percent"]))
             for l in d.get("languages", []) if float(l["percent"]) >= 0.5][:6]
    if not langs:
        print("no language data; leaving hours.svg untouched")
        return 0

    total = d.get("human_readable_total", "0 hrs")
    rng = f'{d.get("start", "")[:10]}  ->  {d.get("end", "")[:10]}'
    open(os.path.abspath(OUT), "w").write(render(total, rng, langs))
    print(f"wrote hours.svg — {total}, {len(langs)} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
