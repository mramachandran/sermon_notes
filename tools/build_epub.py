#!/usr/bin/env python3
"""Lives of the Bible — Kindle e-book (EPUB 3) build.

Reads the same chapter files as build.py and writes one EPUB containing all
170 chapters (both testaments), with title page, copyright page, a short
"How to use this book" page and a linked table of contents.

Usage (from the repo root):
    python3 tools/build_epub.py

Output: dist/lives-of-the-bible.epub  (upload this to KDP as the manuscript)

No extra installs are needed. Edit the BOOK DETAILS block below before
publishing (author name, year, publisher, ISBN).
"""
import html, re, sys, uuid, zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as B  # reuse the chapter parser so the e-book matches the website and PDFs

# ------------------------------------------------------------------ BOOK DETAILS
TITLE = B.BOOK
SUBTITLE = "A Small-Group Study of 170 People in Scripture"
AUTHOR = "Manoj Ramachandran"
YEAR = 2026
PUBLISHER = ""          # e.g. "Lux Analytics LLC"; leave empty to omit
ISBN = ""               # leave empty for Kindle (Amazon assigns an ASIN)
LANG = "en"
COVER = B.ROOT / "book" / "cover.jpg"   # optional; 1600x2560 JPG. Skipped if missing.
# Fixed id so every rebuild is the same book to KDP and readers.
BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://mramachandran.github.io/sermon_notes/"))

DIST = B.ROOT / "dist"
OUTFILE = DIST / "lives-of-the-bible.epub"

CSS = """
body { font-family: serif; line-height: 1.45; margin: 0 4%; }
h1, h2, h3 { font-family: serif; line-height: 1.2; page-break-after: avoid; }
h1 { font-size: 1.9em; margin: 0.6em 0 0.2em; color: #7E2518; }
h1 .num { display: block; font-size: 0.55em; color: #5E5446; font-weight: normal; }
h2 { font-size: 1.35em; margin: 1.4em 0 0.3em; border-bottom: 1px solid #CFC3AA; padding-bottom: 0.15em; }
h3 { font-size: 1.1em; margin: 1.1em 0 0.2em; }
p { margin: 0.4em 0; text-indent: 0; }
.summary { font-style: italic; font-size: 1.1em; margin-bottom: 0.8em; }
.note { font-style: italic; color: #5E5446; font-size: 0.95em; }
.ref { font-style: italic; color: #7E2518; }
table.glance { border-collapse: collapse; width: 100%; margin: 0.3em 0; }
table.glance td { border-bottom: 1px solid #CFC3AA; padding: 0.25em 0.4em 0.25em 0; vertical-align: top; }
table.glance td.k { font-style: italic; color: #5E5446; width: 30%; }
blockquote.verse { margin: 1.2em 6%; text-align: center; font-style: italic; }
blockquote.verse .cite { display: block; font-style: normal; font-size: 0.9em; color: #7E2518; margin-top: 0.3em; }
dl.timeline dt { font-weight: bold; margin-top: 0.7em; }
dl.timeline dt .when { color: #5E5446; font-weight: normal; }
dl.timeline dd { margin: 0.1em 0 0 1em; }
ol.acts li, ol.qs li { margin: 0.45em 0; }
ul.refs { list-style: none; padding-left: 0; }
ul.refs li { margin: 0.3em 0; }
.center { text-align: center; }
.titlepage h1 { font-size: 2.4em; margin-top: 30%; }
.titlepage .sub { font-style: italic; font-size: 1.2em; }
.titlepage .author { margin-top: 3em; font-size: 1.2em; }
.part { text-align: center; margin-top: 30%; }
.part h1 { color: #1F1C17; }
.small { font-size: 0.85em; }
nav ol { list-style: none; padding-left: 0; }
nav ol ol { padding-left: 1.2em; }
"""


def esc(t):
    return html.escape(t, quote=True)


def xhtml(title, body, epub_type=""):
    et = f' epub:type="{epub_type}"' if epub_type else ""
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{LANG}" xml:lang="{LANG}">
<head><meta charset="utf-8"/><title>{esc(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body{et}>
{body}
</body>
</html>
'''


def to_xml(s):
    """build.md() output is HTML; make it XHTML-safe (it only emits <b>/<i> and escaped text)."""
    return s.replace("&#x27;", "'").replace("<br>", "<br/>")


def chapter_body(ch):
    x = to_xml
    g = "".join(f'<tr><td class="k">{x(k)}</td><td>{x(v)}</td></tr>' for k, v in ch["glance"])
    tl = "".join(
        f'<dt>{x(t)} <span class="when">({x(d)}{" · " + x(a) if a else ""})</span></dt>'
        f'<dd>{x(tx)} <span class="ref">{x(r)}</span></dd>'
        for d, a, t, tx, r in ch["timeline"])
    acts = "".join(f'<li><b>{x(t)}.</b> {x(tx)} <span class="ref">{x(r)}</span></li>' for t, tx, r in ch["acts"])

    def refs(lst):
        return "".join(f'<li><b class="ref">{x(r)}.</b> {x(d)}</li>' for r, d in lst)

    qs = "".join(f'<li><i>{x(k)}:</i> {x(q)}</li>' for k, q in ch["questions"])
    note = lambda n: f'<p class="note">{x(n)}</p>' if n else ""

    extras = ""
    for e in ch.get("extras", []):
        inner, ul = "", []
        for kind, t in e["items"] + [("end", "")]:
            if kind == "li":
                ul.append(f"<li>{x(B.md(t))}</li>"); continue
            if ul:
                inner += f"<ul>{''.join(ul)}</ul>"; ul = []
            if kind == "p":
                inner += f"<p>{x(B.md(t))}</p>"
        extras += f"<h3>{esc(e['title'])}</h3>{inner}"
    if extras:
        extras = f'<h2>Go deeper</h2><p class="note">Extra background and a short reading plan for the week.</p>{extras}'

    out = f'''<section epub:type="chapter" id="c{ch["number"]:03d}">
<h1><span class="num">{ch["number"]}</span>{x(ch["name"])}</h1>
<p class="summary">{x(ch["summary"])}</p>
<p>{x(ch["intro"])}</p>
<h2>At a glance</h2>
<table class="glance">{g}</table>
<blockquote class="verse"><p>“{x(ch["verse_full"])}”</p><span class="cite">{x(ch["verse_ref"])}, KJV</span></blockquote>
<h2>The life of {x(ch["name"])}</h2>
{note(ch["timeline_note"])}
<dl class="timeline">{tl}</dl>
<h2>Key activities</h2>
{note(ch["acts_note"])}
<ol class="acts">{acts}</ol>
<h2>Across Scripture</h2>
{note(ch["refs_note"])}'''
    if ch["ot"]:
        out += f'<h3>Old Testament</h3><ul class="refs">{refs(ch["ot"])}</ul>'
    if ch["nt"]:
        out += f'<h3>New Testament</h3><ul class="refs">{refs(ch["nt"])}</ul>'
    out += f'<h2>For discussion</h2><ol class="qs">{qs}</ol>{extras}'
    if ch["closing"]:
        out += f'<blockquote class="verse"><p>“{x(B.md(ch["closing"]))}”</p><span class="cite">{x(B.md(ch["closing_ref"]))}, KJV</span></blockquote>'
    return out + "</section>"


def front_matter(total):
    title = f'''<section class="titlepage center" epub:type="titlepage">
<h1>{esc(TITLE)}</h1>
<p class="sub">{esc(SUBTITLE)}</p>
<p class="author">{esc(AUTHOR)}</p>
</section>'''
    pub = f"<p>Published by {esc(PUBLISHER)}.</p>" if PUBLISHER else ""
    isbn = f"<p>ISBN {esc(ISBN)}</p>" if ISBN else ""
    copyright_ = f'''<section class="small" epub:type="copyright-page">
<p>{esc(TITLE)}: {esc(SUBTITLE)}</p>
<p>Copyright © {YEAR} {esc(AUTHOR)}. All rights reserved.</p>
{pub}{isbn}
<p>Scripture quotations are from the King James Version (KJV).</p>
<p>Dates are approximate. Later tradition and debated views are labelled as such and are not presented as Scripture.</p>
<p>A free web edition is available at mramachandran.github.io/sermon_notes.</p>
</section>'''
    howto = f'''<section epub:type="foreword">
<h1>How to use this book</h1>
<p>{esc(TITLE)} is a small-group study of {total} people in Scripture, from Adam to the early church.</p>
<h2>One person, four parts</h2>
<p>Every chapter follows the same pattern, so a group always knows what to expect:</p>
<ol>
<li><b>Overview.</b> Who they were, key facts at a glance, and a key verse.</li>
<li><b>Timeline.</b> The main moments of their life, each with its reference.</li>
<li><b>Key activities.</b> What they actually did, numbered and referenced.</li>
<li><b>Across Scripture.</b> Every Old and New Testament passage that mentions them, plus four discussion questions.</li>
</ol>
<p>Direct references are kept separate from thematic echoes, and later tradition is labelled so it is never passed off as Scripture.</p>
<h2>Using it in a group</h2>
<p>One chapter fits one meeting of about 45 minutes. Printable four-page handouts for every chapter are free on the website.</p>
<h2>Scripture</h2>
<p>Quotations are from the King James Version. Dates are approximate and follow common scholarly estimates.</p>
</section>'''
    return [("title.xhtml", "Title page", title), ("copyright.xhtml", "Copyright", copyright_), ("howto.xhtml", "How to use this book", howto)]


def main():
    parts = B.parse_list()
    total = sum(len(p["people"]) for p in parts)
    chs, errors = [], []
    for path in sorted(B.CHAPTERS_DIR.glob("*.md")):
        try:
            chs.append(B.parse_chapter(path, parts))
        except B.ChapterError as e:
            errors.append(str(e))
    if errors:
        print("CHAPTERS WITH FORMAT ERRORS — fix these first:")
        for e in errors: print("  - " + e)
        sys.exit(1)
    chs.sort(key=lambda c: c["number"])
    by_part = {}
    for c in chs:
        by_part.setdefault(c["part_no"], []).append(c)

    docs = front_matter(total)  # (filename, title, body)
    toc_front = [(f, t) for f, t, _ in docs if f != "title.xhtml"]
    nav_parts = []
    for p in parts:
        cs = by_part.get(p["no"], [])
        if not cs:
            continue
        if cs[0]["number"] >= B.NT_START and not any(f == "vol2.xhtml" for f, _, _ in docs):
            docs.append(("vol2.xhtml", "Volume II · The New Testament",
                         '<section class="part"><h1>Volume II</h1><p class="sub">The New Testament</p></section>'))
        elif p["no"] == parts[0]["no"]:
            docs.append(("vol1.xhtml", "Volume I · The Old Testament",
                         '<section class="part"><h1>Volume I</h1><p class="sub">The Old Testament</p></section>'))
        pf = f"part{p['no']:02d}.xhtml"
        docs.append((pf, f"Part {p['no']}: {p['name']}",
                     f'<section class="part" epub:type="part"><p>Part {p["no"]}</p><h1>{esc(p["name"])}</h1><p class="note">{esc(p["span"])}</p></section>'))
        entries = []
        for c in cs:
            cf = f"ch{c['number']:03d}.xhtml"
            docs.append((cf, f"{c['number']}. {re.sub('<[^>]+>', '', c['name'])}", chapter_body(c)))
            entries.append((cf, f"{c['number']}. {re.sub('<[^>]+>', '', c['name'])}"))
        nav_parts.append((pf, f"Part {p['no']}: {p['name']}", entries))

    # nav.xhtml (EPUB 3 table of contents)
    nav_items = "".join(f'<li><a href="{f}">{esc(t)}</a></li>' for f, t in toc_front)
    for pf, pt, entries in nav_parts:
        sub = "".join(f'<li><a href="{f}">{esc(t)}</a></li>' for f, t in entries)
        nav_items += f'<li><a href="{pf}">{esc(pt)}</a><ol>{sub}</ol></li>'
    first_ch = next(f for f, _, _ in docs if f.startswith("ch"))
    nav = f'''<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{nav_items}</ol></nav>
<nav epub:type="landmarks" hidden="hidden"><ol>
<li><a epub:type="toc" href="nav.xhtml">Contents</a></li>
<li><a epub:type="bodymatter" href="{first_ch}">Begin reading</a></li>
</ol></nav>'''

    has_cover = COVER.exists()
    manifest = ['<item id="css" href="style.css" media-type="text/css"/>',
                '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
    spine = []
    if has_cover:
        manifest.append('<item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
        manifest.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        spine.append('<itemref idref="cover"/>')
    for i, (f, _, _) in enumerate(docs):
        manifest.append(f'<item id="d{i}" href="{f}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="d{i}"/>')
        if f == "copyright.xhtml":
            spine.append('<itemref idref="nav"/>')
    ident = f"urn:isbn:{ISBN}" if ISBN else BOOK_ID
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{LANG}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{ident}</dc:identifier>
<dc:title>{esc(TITLE)}</dc:title>
<meta refines="#t1" property="title-type">main</meta>
<dc:creator id="a1">{esc(AUTHOR)}</dc:creator>
<dc:language>{LANG}</dc:language>
{f"<dc:publisher>{esc(PUBLISHER)}</dc:publisher>" if PUBLISHER else ""}
<dc:rights>Copyright © {YEAR} {esc(AUTHOR)}</dc:rights>
<dc:subject>Bible study</dc:subject>
<dc:description>{esc(SUBTITLE)}.</dc:description>
<meta property="dcterms:modified">{date.today().isoformat()}T00:00:00Z</meta>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine>
{chr(10).join(spine)}
</spine>
</package>
'''.replace('<meta refines="#t1" property="title-type">main</meta>\n', "")

    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTFILE, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        def w(name, data):
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        w("META-INF/container.xml", '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>''')
        w("OEBPS/content.opf", opf)
        w("OEBPS/style.css", CSS)
        w("OEBPS/nav.xhtml", xhtml("Contents", nav))
        if has_cover:
            z.write(COVER, "OEBPS/cover.jpg")
            w("OEBPS/cover.xhtml", xhtml("Cover", '<div class="center"><img src="cover.jpg" alt="Cover" style="max-width:100%;max-height:100%"/></div>'))
        for f, t, body in docs:
            w(f"OEBPS/{f}", xhtml(t, body))
    print(f"E-book written to {OUTFILE} ({len(chs)} chapters{', with cover' if has_cover else ', no cover yet'}).")


if __name__ == "__main__":
    main()
