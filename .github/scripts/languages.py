"""Gera um SVG com a porcentagem de cada linguagem nos repositórios públicos do usuário."""

import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "languages.svg"
TOP = 8

# Cores do GitHub Linguist
COLORS = {
    "Go": "#00ADD8", "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "Java": "#B07219", "Astro": "#FF5A03", "HTML": "#E34C26", "CSS": "#663399",
    "Shell": "#89E051", "PowerShell": "#012456", "Dockerfile": "#384D54", "SCSS": "#C6538C",
    "Vue": "#41B883", "Svelte": "#FF3E00", "C#": "#178600", "PLpgSQL": "#336790", "SQL": "#E38C00",
    "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Rust": "#DEA584", "C": "#555555", "C++": "#F34B7D",
}
OTHER = "#8B949E"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    totals = {}
    page = 1
    while True:
        repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["archived"] or repo["name"].lower() == USER.lower():
                continue
            for lang, size in get(repo["languages_url"]).items():
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(totals):
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    items = [(name, size / total * 100, COLORS.get(name, OTHER)) for name, size in ranked[:TOP]]
    rest = sum(size for _, size in ranked[TOP:])
    if rest:
        items.append(("Outras", rest / total * 100, OTHER))

    width, pad, bar_y, bar_h = 800, 24, 56, 10
    row_h, cols = 30, 2
    rows = (len(items) + cols - 1) // cols
    height = bar_y + bar_h + 34 + (rows - 1) * row_h + 22
    inner = width - 2 * pad
    col_w = inner / cols

    segs, x = [], pad
    for name, pct, color in items:
        w = inner * pct / 100
        segs.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{color}"/>')
        x += w

    legend = []
    for i, (name, pct, color) in enumerate(items):
        col, row = i // rows, i % rows
        lx = pad + col * col_w
        ly = bar_y + bar_h + 34 + row * row_h
        legend.append(
            f'<circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{color}"/>'
            f'<text x="{lx + 20}" y="{ly}" class="name">{escape(name)}</text>'
            f'<text x="{lx + col_w - 24}" y="{ly}" class="pct" text-anchor="end">{pct:.1f}%</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Linguagens mais usadas">
<style>
  .card {{ fill: #ffffff; stroke: #d0d7de; }}
  .title {{ fill: #1f2328; font: 600 18px 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif; }}
  .name {{ fill: #1f2328; font: 500 14px 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif; }}
  .pct {{ fill: #656d76; font: 400 14px 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif; }}
  @media (prefers-color-scheme: dark) {{
    .card {{ fill: #0d1117; stroke: #30363d; }}
    .title, .name {{ fill: #e6edf3; }}
    .pct {{ fill: #8d96a0; }}
  }}
</style>
<rect class="card" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>
<text x="{pad}" y="36" class="title">Linguagens mais usadas</text>
<clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{inner}" height="{bar_h}" rx="5"/></clipPath>
<g clip-path="url(#bar)">{''.join(segs)}</g>
{''.join(legend)}
</svg>
"""


if __name__ == "__main__":
    svg = render(collect())
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
