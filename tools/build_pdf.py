#!/usr/bin/env python3
"""Lives of the Bible — full-book PDFs (one per volume).

Joins 8 pages of front matter to the 4-page chapter PDFs that build.py
writes into docs/, so the page numbers printed on each chapter line up.

Usage (from the repo root, after python3 tools/build.py):
    python3 tools/build_pdf.py

Output:
    dist/lives-of-the-bible-vol1-old-testament.pdf
    dist/lives-of-the-bible-vol2-new-testament.pdf
These are 6x9 in, no bleed: ready as KDP paperback interiors.
Needs: python3 -m pip install pypdf playwright
"""
import html, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as B
import build_epub as E  # author, year, publisher, subtitle

from pypdf import PdfReader, PdfWriter

VOLS = [
    (1, "Volume I", "The Old Testament", lambda n: n < B.NT_START, "vol1-old-testament"),
    (2, "Volume II", "The New Testament", lambda n: n >= B.NT_START, "vol2-new-testament"),
]
esc = lambda t: html.escape(t, quote=False)
DISP, SERIF, INK, ACC, MUTED, RULE, PAPER = B.DISP, B.SERIF, B.INK, B.ACC, B.MUTED, B.RULE, B.PAPER


def pg(n, body, folio=True, recto=None):
    recto = n % 2 == 1 if recto is None else recto
    pad = "64px 48px 40px 72px" if recto else "64px 72px 40px 48px"
    num = (f'<div style="text-align:{"right" if recto else "left"};font-size:12px;color:{MUTED};">{_roman(n)}</div>' if folio else "")
    return (f'<section style="width:576px;height:864px;box-sizing:border-box;padding:{pad};background:{PAPER};color:{INK};'
            f'font-family:{SERIF};font-size:12.5px;line-height:1.45;display:flex;flex-direction:column;overflow:hidden;break-after:page;">'
            f'<div style="flex-grow:1;display:flex;flex-direction:column;min-height:0;">{body}</div>{num}</section>')


def _roman(n):
    return ["", "i", "ii", "iii", "iv", "v", "vi", "vii", "viii"][n]


def front(vol, parts, chs):
    no, vname, vsub, inv, _ = vol
    t = f"font-family:{DISP};font-weight:700;color:{ACC};"
    half = pg(1, f'<div style="margin:auto;text-align:center;"><p style="margin:0;{t}font-size:40px;">{esc(B.BOOK)}</p></div>', folio=False)
    blank = lambda n: pg(n, "", folio=False)
    pub = f'<p style="margin:0;">{esc(E.PUBLISHER)}</p>' if E.PUBLISHER else ""
    title = pg(3, f'''<div style="margin-top:120px;text-align:center;display:flex;flex-direction:column;gap:18px;align-items:center;">
<h1 style="margin:0;{t}font-size:64px;line-height:0.95;">{esc(B.BOOK)}</h1>
<p style="margin:0;font-family:{DISP};font-style:italic;font-size:22px;">{esc(E.SUBTITLE)}</p>
<div style="width:60px;height:2px;background:{ACC};margin:18px 0;"></div>
<p style="margin:0;font-size:14px;letter-spacing:.25em;text-transform:uppercase;color:{MUTED};">{vname}</p>
<p style="margin:0;font-family:{DISP};font-size:26px;font-weight:600;">{vsub}</p></div>
<div style="margin-top:auto;text-align:center;"><p style="margin:0;font-size:15px;letter-spacing:.12em;text-transform:uppercase;">{esc(E.AUTHOR)}</p>{pub}</div>''', folio=False)
    isbn = f"<p>ISBN {esc(E.ISBN)}</p>" if E.ISBN else ""
    copy = pg(4, f'''<div style="margin-top:auto;font-size:11px;color:{MUTED};display:flex;flex-direction:column;gap:6px;">
<p style="margin:0;">{esc(B.BOOK)}: {esc(E.SUBTITLE)}. {vname}: {vsub}.</p>
<p style="margin:0;">Copyright © {E.YEAR} {esc(E.AUTHOR)}. All rights reserved.</p>{pub}{isbn}
<p style="margin:0;">Scripture quotations are from the King James Version (KJV).</p>
<p style="margin:0;">Dates are approximate. Later tradition and debated views are labelled as such and are not presented as Scripture.</p>
<p style="margin:0;">Free printable handouts for every chapter: mramachandran.github.io/sermon_notes</p></div>''', folio=False)
    h2 = f'style="margin:18px 0 6px;font-family:{DISP};font-size:20px;font-weight:700;"'
    howto = pg(5, f'''<h1 style="margin:0 0 14px;{t}font-size:34px;">How to use this book</h1>
<p style="margin:0 0 8px;">{esc(B.BOOK)} is a small-group study of 170 people in Scripture, from Adam to the early church. This volume covers {vsub.lower().replace("the ", "the ")}.</p>
<h2 {h2}>One person, four pages</h2>
<p style="margin:0 0 6px;">Every chapter follows the same pattern, so a group always knows what to expect:</p>
<ol style="margin:0;padding-left:20px;display:flex;flex-direction:column;gap:4px;">
<li><b>Overview.</b> Who they were, key facts at a glance, and a key verse.</li>
<li><b>Timeline.</b> The main moments of their life, each with its reference.</li>
<li><b>Key activities.</b> What they actually did, numbered and referenced.</li>
<li><b>Across Scripture.</b> Every Old and New Testament passage that mentions them, plus four discussion questions.</li></ol>
<p style="margin:8px 0 0;">Direct references are kept separate from thematic echoes, and later tradition is labelled so it is never passed off as Scripture.</p>
<h2 {h2}>Using it in a group</h2>
<p style="margin:0;">One chapter fits one meeting of about 45 minutes. Lined space for group notes is left on the pages wherever it fits.</p>
<h2 {h2}>Scripture</h2>
<p style="margin:0;">Quotations are from the King James Version. Dates are approximate and follow common scholarly estimates.</p>''')

    # contents: parts and chapters with page numbers, split over pages 7 and 8, two columns each
    lines = []
    for p in parts:
        cs = [c for c in chs if c["part_no"] == p["no"]]
        if not cs:
            continue
        lines.append(f'<div style="break-inside:avoid;margin:8px 0 2px;font-family:{DISP};font-weight:700;font-size:14px;color:{ACC};">Part {p["no"]} · {esc(p["name"])}</div>')
        for c in cs:
            lines.append(f'<div style="display:flex;gap:6px;font-size:10.5px;line-height:1.5;"><span style="width:22px;color:{MUTED};">{c["number"]}</span><span style="flex-grow:1;">{c["name"]}</span><span>{c["first_page"]}</span></div>')
    half_i = (len(lines) + 1) // 2
    cols = lambda ls: f'<div style="column-count:2;column-gap:26px;">{"".join(ls)}</div>'
    c1 = pg(7, f'<h1 style="margin:0 0 6px;{t}font-size:34px;">Contents</h1>' + cols(lines[:half_i]))
    c2 = pg(8, cols(lines[half_i:]))
    return [half, blank(2), title, copy, howto, blank(6), c1, c2]


def main():
    parts = B.parse_list()
    chs = sorted((B.parse_chapter(p, parts) for p in B.CHAPTERS_DIR.glob("*.md")), key=lambda c: c["number"])
    E.DIST.mkdir(exist_ok=True)
    tmp = B.TOOLS / ".tmp"; tmp.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    fonts = B.print_html(chs[0]).split("<style>", 1)[1].split("@page", 1)[0]
    with sync_playwright() as pw:
        br = pw.chromium.launch(); page = br.new_page()
        for vol in VOLS:
            vc = [c for c in chs if vol[3](c["number"])]
            if len(front(vol, parts, vc)) != B.FRONT_MATTER_PAGES:
                raise SystemExit("front matter must be exactly FRONT_MATTER_PAGES pages")
            h = tmp / f"front{vol[0]}.html"
            h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{fonts}@page{{size:6in 9in;margin:0}}body{{margin:0}}</style></head><body>{"".join(front(vol, parts, vc))}</body></html>', encoding="utf-8")
            page.goto(h.as_uri()); page.evaluate("document.fonts.ready"); page.wait_for_timeout(300)
            fp = tmp / f"front{vol[0]}.pdf"
            page.pdf(path=str(fp), width="6in", height="9in", print_background=True, prefer_css_page_size=True)
            w = PdfWriter()
            for pdfpage in PdfReader(fp).pages:
                w.add_page(pdfpage)
            missing = []
            for c in vc:
                f = B.OUT / c["slug"] / f'{c["slug"]}-lives-of-the-bible.pdf'
                if not f.exists():
                    missing.append(c["name"]); continue
                start = len(w.pages)
                for pdfpage in PdfReader(f).pages:
                    w.add_page(pdfpage)
                w.add_outline_item(f'{c["number"]}. {re.sub("<[^>]+>", "", c["name"])}', start)
            if missing:
                raise SystemExit(f"Run tools/build.py first; missing PDFs for: {', '.join(missing)}")
            w.add_metadata({"/Title": f"{B.BOOK} — {vol[1]}: {vol[2]}", "/Author": E.AUTHOR})
            out = E.DIST / f"lives-of-the-bible-{vol[4]}.pdf"
            with open(out, "wb") as fh:
                w.write(fh)
            print(f"{out.name}: {len(w.pages)} pages")
        br.close()
    import shutil; shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
