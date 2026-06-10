# Tools

A personal collection of small, self-contained HTML tools — each one a single
static file with no build step, no framework, and no external dependencies.
Inspired by [Simon Willison's tools.simonwillison.net](https://tools.simonwillison.net/)
and his note on [hoarding things you know how to do](https://simonwillison.net/guides/agentic-engineering-patterns/hoard-things-you-know-how-to-do/).

Two purposes:

1. **Quick-grab utilities** — open the page, or save the file and use it offline.
2. **Code reference** — each file is a complete, copy-pasteable example of how to
   do one thing in plain HTML/CSS/JS.

## Layout

```
tools/            standalone tool pages (one .html each)
_template.html    starting point for a new tool
build.py          generates index.html + colophon.html
index.html        generated: searchable listing      (git-ignored)
colophon.html     generated: created/updated dates    (git-ignored)
```

## How it works

- Every tool lives in `tools/` as a standalone `*.html` file.
- `build.py` scans that directory, reads each file's `<title>` and
  `<meta name="description">`, and generates `index.html` (a searchable listing)
  and `colophon.html` (creation/update dates from git history) at the repo root.
- A GitHub Actions workflow runs `build.py` and deploys to GitHub Pages on every
  push to `main`.

`index.html` and `colophon.html` are generated artifacts and are git-ignored.

## Adding a tool

1. Copy the template into `tools/`:
   ```sh
   cp _template.html tools/my-tool.html
   ```
2. Edit `my-tool.html`. Set the `<title>` (its name in the index) and the
   `<meta name="description">` (the one-line blurb). Keep everything in the one
   file so it stays grabbable and works offline.
3. Rebuild and preview locally:
   ```sh
   python build.py
   python -m http.server   # then open http://localhost:8000
   ```
4. Commit and push — the Action rebuilds the index and deploys.

## Starter tools

- `tools/json-formatter.html` — pretty-print, minify, and validate JSON
- `tools/uuid-generator.html` — generate v4 UUIDs in bulk
- `tools/base64.html` — UTF-8-safe Base64 encode/decode

## One-time GitHub Pages setup

After pushing to GitHub: **Settings → Pages → Build and deployment → Source:
GitHub Actions**. The included workflow handles the rest.
