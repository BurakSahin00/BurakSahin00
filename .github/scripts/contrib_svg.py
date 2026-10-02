"""Kırmızı temalı, sade katkı grafiği üretir.
Kullanım (GitHub Actions içinde):  python contrib_svg.py --user BurakSahin00 --style iso --out profile-contrib/contrib.svg
GITHUB_TOKEN ortam değişkeni gerekir. --sample ile sahte veriyle önizleme üretir."""
import argparse, json, math, os, random, urllib.request, datetime

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
TOP  = ["#151b2e", "#2f2a6e", "#4f3fb0", "#7c5cff", "#22d3ee"]
SIDE_L = ["#121a30", "#3f0c16", "#6b111f", "#951326", "#b3162c"]
SIDE_R = ["#10080a", "#2e0910", "#4f0c17", "#6e0e1c", "#850f21"]
FONT = "'JetBrains Mono','Fira Code','Courier New',monospace"

def fetch(user, token):
    q = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{contributionCount contributionLevel date weekday}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["weekday"], d["contributionCount"], LEVELS.index(d["contributionLevel"])) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return cal["totalContributions"], weeks

def sample():
    random.seed(4); weeks = []; total = 0
    for w in range(53):
        days = []
        for d in range(7):
            busy = 0.35 + 0.45 * (w / 53)
            c = int(random.random() * random.random() * 14) if random.random() < busy else 0
            lv = 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 9 else 4
            days.append((d, c, lv)); total += c
        weeks.append(days)
    return total, weeks

def header(total, W, H):
    return (f'<text x="40" y="44" font-family="{FONT}" font-size="12" fill="#5b6480" letter-spacing="1.5">CONTRIBUTIONS · LAST 12 MONTHS</text>'
            f'<text x="40" y="84" font-family="{FONT}" font-size="34" font-weight="700" fill="#e6e9f2">{total:,}</text>')

def iso(total, weeks):
    W, H = 1000, 370
    WV, DV = (11.4, 4.3), (-7.2, 5.1)
    x0, y0 = 300, 30
    cells = []
    for wi, days in enumerate(weeks):
        for (d, c, lv) in days:
            h = 2 if lv == 0 else min(64, 6 + math.sqrt(c) * 11)
            cells.append((wi + d, wi, d, h, lv))
    cells.sort()
    out = []
    for _, wi, d, h, lv in cells:
        px = x0 + wi * WV[0] + d * DV[0]; py = y0 + wi * WV[1] + d * DV[1] + 70
        def pt(a, b, z): return f"{px + a*WV[0] + b*DV[0]:.1f},{py + a*WV[1] + b*DV[1] - z:.1f}"
        top = f'<polygon points="{pt(0,0,h)} {pt(1,0,h)} {pt(1,1,h)} {pt(0,1,h)}" fill="{TOP[lv]}"/>'
        left = f'<polygon points="{pt(0,1,h)} {pt(1,1,h)} {pt(1,1,0)} {pt(0,1,0)}" fill="{SIDE_L[lv]}"/>'
        right = f'<polygon points="{pt(1,0,h)} {pt(1,1,h)} {pt(1,1,0)} {pt(1,0,0)}" fill="{SIDE_R[lv]}"/>'
        anim = f' class="g" style="animation-delay:{wi*0.025:.3f}s"' if lv else ''
        out.append(f'<g{anim}>{left}{right}{top}</g>')
    style = ('.g{opacity:0;animation:rise .6s ease-out forwards}'
             '@keyframes rise{from{opacity:0;transform:translateY(-14px)}to{opacity:1;transform:none}}')
    return W, H, style, header(total, W, H) + "".join(out)

def flat(total, weeks):
    W, H = 1000, 250
    cs, gap, x0, y0 = 14, 3.3, 40, 110
    out = []
    for wi, days in enumerate(weeks):
        for (d, c, lv) in days:
            x = x0 + wi * (cs + gap); y = y0 + d * (cs + gap)
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cs}" height="{cs}" rx="2.5" fill="{TOP[lv]}"/>')
    span = len(weeks) * (cs + gap)
    beam = (f'<g class="beam"><rect x="-50" y="{y0-6}" width="50" height="{7*(cs+gap)+8}" fill="url(#bg)"/>'
            f'<rect x="-1.5" y="{y0-6}" width="1.5" height="{7*(cs+gap)+8}" fill="#22d3ee" fill-opacity=".8"/></g>')
    defs = ('<defs><linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#7c5cff" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#22d3ee" stop-opacity=".2"/></linearGradient></defs>')
    style = (f'.beam{{animation:sw 7s linear infinite}}'
             f'@keyframes sw{{0%{{transform:translateX({x0}px)}}70%{{transform:translateX({x0+span}px)}}70.01%,100%{{transform:translateX({W+60}px)}}}}')
    legend = "".join(f'<rect x="{W-74-5*17+i*17}" y="52" width="12" height="12" rx="2" fill="{TOP[i]}"/>' for i in range(5))
    legend += (f'<text x="{W-74-5*17-8}" y="62" text-anchor="end" font-family="{FONT}" font-size="11" fill="#5b6480">LESS</text>'
               f'<text x="{W-70}" y="62" font-family="{FONT}" font-size="11" fill="#5b6480">MORE</text>')
    return W, H, style, defs + header(total, W, H) + legend + "".join(out) + beam

def render(total, weeks, style_name):
    W, H, css, body = (iso if style_name == "iso" else flat)(total, weeks)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year">'
            f'<style>{css}</style><rect width="{W}" height="{H}" rx="12" fill="#0b0f1a"/><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="none" stroke="#7c5cff" stroke-opacity="0.35"/>{body}</svg>')

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user"); ap.add_argument("--style", default="iso", choices=["iso", "flat"])
    ap.add_argument("--out", required=True); ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    total, weeks = sample() if a.sample else fetch(a.user, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w").write(render(total, weeks, a.style))
