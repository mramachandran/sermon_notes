# Lives of the Bible — instructions for Claude

This folder is the working copy of the book *Lives of the Bible*: a small-group Bible study of 170 people, from Adam to the early church. It is published three ways: a free website (GitHub Pages), a Kindle e-book, and a two-volume paperback.

Read these before doing any work:

- `book/01-style-guide.md`: voice, Scripture rules (KJV only), the exact four-page chapter format, and the accuracy checklist.
- `book/02-character-list.md`: the official order, numbers and main passages for all 170 people.
- `chapters/056-ruth.md` and `chapters/098-josiah.md`: finished chapters. Match their depth, tone and format exactly.

## Folder layout

- `chapters/` — one Markdown file per person, named `NNN-slug.md` (for example `001-adam.md`). This is the source of truth.
- `tools/build.py` — turns every chapter into a web page and a 4-page printable PDF.
- `docs/` — the generated website. Never edit it by hand; rebuild it instead.
- `book/` — style guide and character list.

## Writing a chapter

1. Look up the person's number and main passages in the character list.
2. Write `chapters/NNN-slug.md` following the style guide's format character for character.
3. Quote only the King James Version, and only verses you are certain of word for word. Never invent references, dates or details. Label tradition and debated views.
4. Run `python3 tools/build.py`.
5. If it reports a page is too long, shorten that page and run it again until it says "All chapters fit on their 4 pages."
6. After each batch, give me a short list of anything to double-check (uncertain dates, debated points).

When I ask for a batch (for example "write chapters 1–10"), write them in order, build once at the end, and fix any pages that are too long.

## One-time setup

1. Install the build tools:
   `python3 -m pip install playwright` then `python3 -m playwright install chromium`
2. Run `python3 tools/build.py` once to check everything works.

## Publishing

The website is served from the `docs/` folder. After building, commit and push the changes (for example with GitHub Desktop). The site updates at https://mramachandran.github.io/sermon_notes/ within a couple of minutes.
