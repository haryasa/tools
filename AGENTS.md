# Agent guide

Guidance for AI agents (and humans) working in this repo. For the project
overview and human-facing setup, see [README.md](README.md).

## What this is

A collection of small, **single-file HTML tools** served via GitHub Pages. Each
tool is one self-contained `.html` file with inline CSS and JS — **no build
step, no framework, no bundler, no shared assets**. This is a hard constraint,
not a preference: a tool must work when saved and opened on its own, with nothing
else from the repo.

The one relaxation: a tool **may** load a third-party library straight from a CDN
via `<script src>` / `<link href>` (e.g. PDF.js, Tesseract.js) when reinventing
it inline would be unreasonable. Such a tool needs a network connection on first
open and so won't work fully offline — that's the accepted trade-off. Prefer
dependency-free; reach for a CDN only when the library is the whole point of the
tool. No npm, no build step, no framework, ever — those are what keep each file
copy-paste portable.

## Layout

```
tools/            one self-contained .html per tool  ← add tools here
_template.html    starting point for a new tool
build.py          generates index.html + colophon.html, stages _site/ (stdlib only)
index.html        GENERATED — do not edit (git-ignored)
colophon.html     GENERATED — do not edit (git-ignored)
_site/            GENERATED deploy artifact, GA tag injected — do not edit (git-ignored)
.github/workflows/deploy.yml   builds + deploys to Pages on push to main
```

## Adding or editing a tool

1. Start from the template: `cp _template.html tools/<name>.html`.
2. Set two things that feed the generated index — get them right:
   - `<title>` → the tool's name in the listing.
   - `<meta name="description" content="...">` → the one-line blurb. One sentence.
3. Keep everything inline in that one file. Don't link sibling files in the repo,
   and don't add a build step, bundler, or framework. A CDN `<script src>` /
   `<link href>` is allowed only when a tool genuinely needs a heavy library
   (note that it then won't work offline); default to dependency-free.
4. Keep the navigation back-link: `<a class="back" href="../index.html">`.
5. Match the existing visual style (system font stack, rounded controls,
   `#2563eb` primary buttons, light/dark via `prefers-color-scheme`). Copying the
   `<style>` block from the template or a sibling tool is the intended path.

## Build & preview

```sh
python build.py        # regenerate index.html + colophon.html
python -m http.server  # then open http://localhost:8000
```

Run `build.py` after adding or renaming a tool. Never hand-edit `index.html` or
`colophon.html` — they are overwritten on every build and on every deploy.

## How the index is generated

`build.py` scans `tools/*.html`, parses each file's `<title>` and
`<meta name="description">`, and pulls created/updated dates from git history.
Missing or wrong metadata shows up directly in the listing, so verify the
generated `index.html` after building.

## Conventions

- **Commits:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`,
  `chore:`). One logical change per commit.
- **Deploy:** pushing to `main` triggers the Pages workflow; no manual deploy.
- **Dependencies:** prefer none — inline a minimal implementation where it's
  reasonable. A CDN-loaded library is the only allowed exception, for cases where
  inlining (e.g. a PDF or OCR engine) is not. No npm, no build step, no framework.
