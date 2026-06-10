#!/usr/bin/env python3
"""Generate index.html and colophon.html for the tools collection.

Scans the repo root for standalone tool HTML files, reads each file's
<title> and <meta name="description">, and renders:

  - index.html    a searchable listing of every tool
  - colophon.html created/updated dates pulled from git history

Run locally with `python build.py`, then open index.html. The GitHub
Actions workflow runs this on every push to main before deploying.

No third-party dependencies -- standard library only.
"""

from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Tool pages live here; the generated index/colophon live at the repo root.
TOOLS_DIR = ROOT / "tools"

# Deploy artifact staged for GitHub Pages (git-ignored).
SITE_DIR = ROOT / "_site"

# Config comes from the environment so it can be set outside the codebase
# (e.g. GitHub Actions repository variables). Both have sensible fallbacks.
#
#   REPO_URL           footer "view source" link target
#   GA_MEASUREMENT_ID  Google Analytics (GA4) ID, e.g. "G-XXXXXXXXXX".
#                      Empty by default, so local builds ship no analytics tag.
REPO_URL = os.environ.get("REPO_URL", "https://github.com/haryasa/tools")
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "")


def ga_snippet() -> str:
    return f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>"""


def inject_ga(page: str) -> str:
    """Insert the Google Analytics tag just before </head>.

    A no-op when GA_MEASUREMENT_ID is unset, so local/test builds stay inert.
    Applied only to deployed copies in _site/.
    """
    if not GA_MEASUREMENT_ID:
        return page
    if "</head>" not in page:
        return page
    snippet = "\n".join("  " + line for line in ga_snippet().splitlines())
    return page.replace("</head>", f"{snippet}\n</head>", 1)


class MetaParser(HTMLParser):
    """Pull the <title> text and <meta name="description"> out of a page."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.description: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            attr = {k: v for k, v in attrs}
            if attr.get("name") == "description":
                self.description = attr.get("content")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = (self.title or "") + data


def git_dates(filename: str) -> tuple[str | None, str | None]:
    """Return (created_iso, updated_iso) for a file from git history."""

    def run(args: list[str]) -> str:
        try:
            out = subprocess.run(
                ["git", *args],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            return out.stdout.strip()
        except OSError:
            return ""

    updated = run(["log", "-1", "--format=%aI", "--", filename]) or None
    added = run(["log", "--diff-filter=A", "--format=%aI", "--", filename])
    created = added.splitlines()[-1] if added else None
    return created, updated


def collect_tools() -> list[dict[str, str | None]]:
    tools: list[dict[str, str | None]] = []
    for path in sorted(TOOLS_DIR.glob("*.html")):
        relpath = f"tools/{path.name}"
        parser = MetaParser()
        parser.feed(path.read_text(encoding="utf-8"))
        title = (parser.title or path.stem).strip()
        description = (parser.description or "").strip()
        created, updated = git_dates(relpath)
        tools.append(
            {
                "file": relpath,
                "title": title,
                "description": description,
                "created": created,
                "updated": updated,
            }
        )
    # Newest first when we have dates, otherwise alphabetical (already sorted).
    tools.sort(key=lambda t: (t["created"] or ""), reverse=True)
    return tools


def fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%b %-d, %Y")
    except ValueError:
        return iso[:10]


PAGE_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  margin: 0; line-height: 1.5;
  color: #1a1a1a; background: #fafafa;
}
.wrap { max-width: 820px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
header h1 { margin: 0 0 .25rem; font-size: 1.9rem; }
header p { margin: 0; color: #666; }
header a { color: inherit; }
#search {
  width: 100%; margin: 1.75rem 0 .5rem; padding: .7rem .9rem;
  font-size: 1rem; border: 1px solid #ccc; border-radius: 10px;
  background: #fff; color: inherit;
}
.count { color: #888; font-size: .85rem; margin-bottom: 1rem; }
ul { list-style: none; padding: 0; margin: 0; }
li {
  border: 1px solid #e3e3e3; border-radius: 12px; background: #fff;
  margin-bottom: .75rem; transition: border-color .15s, transform .05s;
}
li:hover { border-color: #b9b9b9; }
li a.card { display: block; padding: 1rem 1.15rem; color: inherit; text-decoration: none; }
li a.card:active { transform: scale(.998); }
.title { font-weight: 600; font-size: 1.05rem; }
.desc { color: #555; margin-top: .2rem; font-size: .92rem; }
.meta { color: #999; font-size: .78rem; margin-top: .4rem; }
footer { margin-top: 2.5rem; color: #999; font-size: .85rem; }
footer a { color: inherit; }
.empty { color: #999; padding: 1rem 0; }
@media (prefers-color-scheme: dark) {
  body { color: #e6e6e6; background: #111; }
  header p, .desc { color: #aaa; }
  #search { background: #1c1c1c; border-color: #333; }
  li { background: #181818; border-color: #2a2a2a; }
  li:hover { border-color: #444; }
}
"""


def render_index(tools: list[dict[str, str | None]]) -> str:
    items = "\n".join(
        f"""      <li data-search="{html.escape((t['title'] + ' ' + (t['description'] or '')).lower(), quote=True)}">
        <a class="card" href="{html.escape(t['file'])}">
          <div class="title">{html.escape(t['title'])}</div>
          {f'<div class="desc">{html.escape(t["description"])}</div>' if t['description'] else ''}
          {f'<div class="meta">Updated {fmt_date(t["updated"])}</div>' if t['updated'] else ''}
        </a>
      </li>"""
        for t in tools
    )
    if not items:
        items = '      <li class="empty">No tools yet. Copy _template.html to get started.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tools</title>
  <meta name="description" content="A personal collection of small, self-contained HTML tools.">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Tools</h1>
      <p>A collection of small, self-contained HTML tools. <a href="colophon.html">Colophon</a></p>
    </header>
    <input id="search" type="search" placeholder="Search tools..." autocomplete="off" autofocus>
    <div class="count" id="count"></div>
    <ul id="list">
{items}
    </ul>
    <footer>
      Each tool is a single static HTML file with no dependencies &mdash;
      <a href="{REPO_URL}">view source</a> or save any file to use it offline.
    </footer>
  </div>
  <script>
    const search = document.getElementById('search');
    const items = [...document.querySelectorAll('#list li[data-search]')];
    const count = document.getElementById('count');
    function update() {{
      const q = search.value.trim().toLowerCase();
      let shown = 0;
      for (const li of items) {{
        const match = !q || li.dataset.search.includes(q);
        li.style.display = match ? '' : 'none';
        if (match) shown++;
      }}
      count.textContent = shown + (shown === 1 ? ' tool' : ' tools');
    }}
    search.addEventListener('input', update);
    update();
  </script>
</body>
</html>
"""


def render_colophon(tools: list[dict[str, str | None]]) -> str:
    rows = "\n".join(
        f"""      <li>
        <a class="card" href="{html.escape(t['file'])}">
          <div class="title">{html.escape(t['title'])}</div>
          <div class="meta">Created {fmt_date(t['created']) or '&mdash;'} &middot; Updated {fmt_date(t['updated']) or '&mdash;'} &middot; {html.escape(t['file'])}</div>
        </a>
      </li>"""
        for t in tools
    )
    if not rows:
        rows = '      <li class="empty">No tools yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Colophon</title>
  <meta name="description" content="When each tool in the collection was created and last updated.">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Colophon</h1>
      <p>When each tool was created and last changed, from git history. <a href="index.html">Back to tools</a></p>
    </header>
    <ul id="list">
{rows}
    </ul>
    <footer>Generated by build.py.</footer>
  </div>
</body>
</html>
"""


def stage_site(index: str, colophon: str) -> None:
    """Assemble the deploy-ready _site/ directory with the GA tag injected.

    Source tool files are copied verbatim except for the analytics tag added
    here, so the committed originals stay self-contained and dependency-free.
    """
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    (SITE_DIR / "tools").mkdir(parents=True)
    for path in TOOLS_DIR.glob("*.html"):
        page = path.read_text(encoding="utf-8")
        (SITE_DIR / "tools" / path.name).write_text(inject_ga(page), encoding="utf-8")
    (SITE_DIR / "index.html").write_text(inject_ga(index), encoding="utf-8")
    (SITE_DIR / "colophon.html").write_text(inject_ga(colophon), encoding="utf-8")


def main() -> None:
    tools = collect_tools()
    index = render_index(tools)
    colophon = render_colophon(tools)
    # Root copies (git-ignored) for local preview with `python -m http.server`.
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    (ROOT / "colophon.html").write_text(colophon, encoding="utf-8")
    # Deploy artifact with the analytics tag stamped into every page.
    stage_site(index, colophon)
    print(f"Built index.html + colophon.html and staged _site/ ({len(tools)} tools)")


if __name__ == "__main__":
    main()
