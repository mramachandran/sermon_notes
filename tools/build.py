#!/usr/bin/env python3
"""Lives of the Bible — build script.

Reads every chapter in chapters/ (NNN-slug.md) plus book/02-character-list.md
and writes the website and a 4-page printable PDF for each chapter into docs/.

Usage (from the repo root):
    python3 tools/build.py            build everything
    python3 tools/build.py 056 098    build only these chapter numbers (plus the index pages)

Setup, once:
    python3 -m pip install playwright
    python3 -m playwright install chromium
"""
import html, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
CHAPTERS_DIR = ROOT / "chapters"
LIST_FILE = ROOT / "book" / "02-character-list.md"
OUT = ROOT / "docs"
BOOK = "Lives of the Bible"
NT_START = 117          # first chapter of Volume II (New Testament)
FRONT_MATTER_PAGES = 8  # page numbers start after this many pages

INK = "#1F1C17"; ACC = "#7E2518"; MUTED = "#5E5446"; RULE = "#CFC3AA"; PAPER = "#FBF8F1"
SERIF = "'Source Serif 4', Georgia, serif"; DISP = "'Cormorant Garamond', Georgia, serif"


class ChapterError(Exception):
    pass


# ------------------------------------------------------------------ helpers
def md(text):
    """Escape HTML, then turn **bold** and *italic* into tags."""
    t = html.escape(text.strip(), quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return t


def parse_list():
    parts = []; cur = None
    for line in LIST_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"## Part (\d+) — (.+)", line)
        if m:
            cur = {"no": int(m[1]), "name": m[2].strip(), "span": "", "people": []}
            parts.append(cur); continue
        if cur and line.startswith("*") and not cur["span"]:
            cur["span"] = line.strip().strip("*")
        m = re.match(r"\| (\d{3}) \| (.+?) \| [MS] \| (.+?) \|", line)
        if m and cur:
            cur["people"].append((int(m[1]), m[2], m[3]))
    if not parts:
        raise SystemExit(f"Could not read the character list at {LIST_FILE}")
    return parts


def first_page(number):
    base = number - (NT_START - 1) if number >= NT_START else number
    return FRONT_MATTER_PAGES + (base - 1) * 4 + 1


# ------------------------------------------------------------------ parser
def parse_chapter(path, parts):
    fn = path.name
    m = re.match(r"(\d{3})-([a-z0-9-]+)\.md$", fn)
    if not m:
        raise ChapterError(f"{fn}: file name must look like 056-ruth.md")
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    fm = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not fm:
        raise ChapterError(f"{fn}: missing front matter between --- lines")
    meta = {}
    for line in fm[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    body = text[fm.end():]
    pages = [p.strip() for p in body.split("\\newpage")]
    if len(pages) != 4:
        raise ChapterError(f"{fn}: needs exactly 4 pages separated by 3 \\newpage lines (found {len(pages)})")

    number = int(meta.get("number", m[1]))
    ch = {"slug": m[2], "number": number, "name": meta.get("name", ""),
          "closing": meta.get("closing", ""), "closing_ref": meta.get("closing_ref", "")}
    for p in parts:
        for n, name, _ in p["people"]:
            if n == number:
                ch["part_no"], ch["part"] = p["no"], p["name"]
    if "part_no" not in ch:
        raise ChapterError(f"{fn}: number {number} is not in the character list")
    ch["first_page"] = first_page(number)

    def lines(page):
        return [l.rstrip() for l in page.splitlines()]

    # page 1
    L = lines(pages[0])
    try:
        title_i = next(i for i, l in enumerate(L) if l.startswith("# "))
        glance_i = next(i for i, l in enumerate(L) if l.strip() == "## At a glance")
    except StopIteration:
        raise ChapterError(f"{fn}: page 1 needs '# Name' and '## At a glance'")
    head = [l for l in L[title_i + 1:glance_i] if l.strip()]
    if not head or not re.match(r"^\*[^*].*\*$", head[0]):
        raise ChapterError(f"{fn}: page 1 needs an *italic one-line summary* under the title")
    ch["summary"] = md(head[0][1:-1])
    ch["intro"] = md(" ".join(head[1:]))
    ch["glance"] = []
    for l in L[glance_i + 1:]:
        mm = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", l)
        if mm and not set(mm[1]) <= set("-: ") and mm[1].strip():
            ch["glance"].append((md(mm[1]), md(mm[2])))
    quote = [l[1:].strip() for l in L if l.startswith(">")]
    quote = [q for q in quote if q]
    if len(quote) < 2 or not quote[-1].startswith("—"):
        raise ChapterError(f"{fn}: page 1 needs a key verse blockquote ending with '> — Reference, KJV'")
    ch["verse"] = md(" ".join(quote[:-1]))
    ch["verse_full"] = ch["verse"]
    ch["verse_ref"] = md(re.sub(r",\s*KJV$", "", quote[-1].lstrip("— ").strip()))

    def note_after_heading(L):
        for l in L:
            if re.match(r"^\*[^*].*\*$", l.strip()):
                return md(l.strip()[1:-1])
        return ""

    # page 2
    L = lines(pages[1])
    ch["timeline_note"] = note_after_heading(L)
    ch["timeline"] = []
    for l in L:
        mm = re.match(r"^\*\*(.+?) — (.+?)\.?\*\* (.+) \*([^*]+)\*$", l.strip())
        if mm:
            when = mm[1].split(" · ", 1)
            ch["timeline"].append((md(when[0]), md(when[1]) if len(when) > 1 else "", md(mm[2]), md(mm[3]), md(mm[4])))
    if len(ch["timeline"]) < 3:
        raise ChapterError(f"{fn}: page 2 needs at least 3 timeline entries like '**c. 640 BC · Age 8 — Title.** Text. *Reference*'")

    # page 3
    L = lines(pages[2])
    ch["acts_note"] = note_after_heading(L)
    ch["acts"] = []
    for l in L:
        mm = re.match(r"^\d+\.\s+\*\*(.+?)\.?\*\* (.+) \*([^*]+)\*$", l.strip())
        if mm:
            ch["acts"].append((md(mm[1]), md(mm[2]), md(mm[3])))
    if len(ch["acts"]) < 4:
        raise ChapterError(f"{fn}: page 3 needs at least 4 key activities like '1. **Title.** Text. *Reference*'")

    # page 4
    L = lines(pages[3])
    ch["refs_note"] = note_after_heading(L)
    ch["ot"], ch["nt"], ch["questions"] = [], [], []
    section = None
    for l in L:
        s = l.strip()
        if s == "### Old Testament": section = "ot"; continue
        if s == "### New Testament": section = "nt"; continue
        if s == "## For discussion": section = "q"; continue
        if section in ("ot", "nt"):
            mm = re.match(r"^- \*\*(.+?)\.?\*\* (.+)$", s)
            if mm: ch[section].append((md(mm[1]), md(mm[2])))
        if section == "q":
            mm = re.match(r"^\d+\.\s+\*\*(.+?):\*\* (.+)$", s)
            if mm: ch["questions"].append((md(mm[1]), md(mm[2])))
    if not ch["ot"] and not ch["nt"]:
        raise ChapterError(f"{fn}: page 4 needs '### Old Testament' and/or '### New Testament' lists")
    if len(ch["questions"]) != 4:
        raise ChapterError(f"{fn}: page 4 needs exactly 4 discussion questions like '1. **Observe:** ...'")
    ch["extras"] = parse_extras(pages)
    return ch


EXTRA_HEADS = ("The world around them", "Words and places", "Read it yourself")


def parse_extras(pages):
    """Web-only study extras: '### The world around them', '### Words and places',
    '### Read it yourself' blocks and loose '*Tradition.*' paragraphs. Not printed in the PDF."""
    out = []
    for page in pages:
        cur = None
        for raw in page.splitlines():
            s = raw.strip()
            if s.startswith("#"):
                h = s.lstrip("#").strip()
                cur = {"title": h, "items": []} if h in EXTRA_HEADS else None
                if cur: out.append(cur)
                continue
            mt = re.match(r"^\*(Tradition|Debated)\.\*\s*(.+)$", s)
            if mt:
                out.append({"title": "Tradition" if mt[1] == "Tradition" else "A debated point", "items": [("p", mt[2])]})
                cur = None
                continue
            if cur is not None and s:
                cur["items"].append(("li", s[2:]) if s.startswith("- ") else ("p", s))
    return [x for x in out if x["items"]]


# ------------------------------------------------------------------ print pages
def page(ch, n, body, section):
    recto = n % 2 == 1
    pad = "44px 48px 40px 72px" if recto else "44px 72px 40px 48px"
    left, right = (f"{ch['number']} · {ch['name']}", section) if recto else (BOOK, f"Part {ch['part_no']}: {ch['part']}")
    align = "right" if recto else "left"
    return f'''<section class="pg" style="width: 576px; height: 864px; box-sizing: border-box; padding: {pad}; background: {PAPER}; color: {INK}; font-family: {SERIF}; font-size: 12.5px; line-height: 1.4; display: flex; flex-direction: column; overflow: hidden; break-after: page;">
  <div style="display: flex; justify-content: space-between; font-size: 12px; font-style: italic; color: {MUTED}; padding-bottom: 8px; border-bottom: 1px solid {RULE};"><span>{left}</span><span>{right}</span></div>
  <div class="content" style="display: flex; flex-direction: column; flex-grow: 1; min-height: 0;">{body}</div>
  <div style="text-align: {align}; font-size: 12px; color: {MUTED}; padding-top: 10px;">{n}</div>
</section>'''


def h2(t, note):
    return f'''<h2 style="margin: 18px 0 4px; font-family: {DISP}; font-size: 30px; font-weight: 700; line-height: 1;">{t}</h2>
<p style="margin: 0 0 12px; font-size: 12px; font-style: italic; color: {MUTED};">{note}</p>'''


def notes():
    # Fills leftover space with ruled lines; removed automatically if the page has no room.
    return f'''<div class="notes" style="margin-top: 16px; flex-grow: 1; min-height: 110px; display: flex; flex-direction: column; gap: 4px;">
<span style="font-family: {DISP}; font-size: 17px; font-weight: 700;">Group notes</span>
<div style="flex-grow: 1; background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 27px, {RULE} 27px, {RULE} 28px);"></div></div>'''


def p1(ch):
    rows = "".join(f'<div style="display: flex; gap: 12px; padding: 5px 0; border-bottom: 1px solid {RULE};"><span style="width: 96px; flex-shrink: 0; font-style: italic; color: {MUTED};">{k}</span><span>{v}</span></div>' for k, v in ch["glance"])
    return f'''<div style="display: flex; flex-direction: column; gap: 10px; margin-top: 26px;">
  <div style="display: flex; align-items: baseline; gap: 14px;"><span style="font-family: {DISP}; font-size: 22px; font-weight: 600; color: {ACC};">{ch['number']}</span><h1 style="margin: 0; font-family: {DISP}; font-size: 54px; font-weight: 700; line-height: 1; color: {ACC};">{ch['name']}</h1></div>
  <p style="margin: 0; font-family: {DISP}; font-size: 19px; line-height: 1.2; font-style: italic; font-weight: 500;">{ch['summary']}</p>
  <p style="margin: 4px 0 0;">{ch['intro']}</p>
</div>
<h2 style="margin: 18px 0 6px; font-family: {DISP}; font-size: 20px; font-weight: 700;">At a glance</h2>
<div style="border-top: 1.5px solid {INK};">{rows}</div>
<div style="margin-top: auto; padding: 14px 0 0; border-top: 1px solid {RULE}; display: flex; flex-direction: column; gap: 8px; align-items: center; text-align: center;">
  <p style="margin: 0; font-family: {DISP}; font-size: 18px; line-height: 1.3; font-style: italic; font-weight: 500; max-width: 410px;">"{ch['verse']}"</p>
  <span style="font-size: 12px; color: {ACC};">{ch['verse_ref']}, KJV</span>
</div>'''


def p2(ch):
    rows = ""
    for i, (d, a, t, x, r) in enumerate(ch["timeline"]):
        last = i == len(ch["timeline"]) - 1
        sub = f'<span style="font-size: 12px; font-style: italic; color: {MUTED};">{a}</span>' if a else ""
        rows += f'''<div style="display: flex;">
  <div style="width: 84px; flex-shrink: 0; display: flex; flex-direction: column; gap: 1px;"><span style="font-weight: 600;">{d}</span>{sub}</div>
  <div style="width: 22px; flex-shrink: 0; display: flex; flex-direction: column; align-items: center;"><div style="width: 9px; height: 9px; border-radius: 50%; background: {ACC}; margin-top: 5px; flex-shrink: 0;"></div><div style="width: 1px; flex-grow: 1; background: {'transparent' if last else RULE}; margin-top: 3px;"></div></div>
  <div style="flex-grow: 1; padding: 0 0 6px 8px; display: flex; flex-direction: column; gap: 1px;"><span style="font-family: {DISP}; font-size: 17px; font-weight: 700; line-height: 1.15;">{t}</span><span>{x} <i style="color: {ACC};">{r}</i></span></div>
</div>'''
    return h2(f"The life of {ch['name']}", ch["timeline_note"]) + f"<div>{rows}</div>" + notes()


def p3(ch):
    items = "".join(f'''<div style="display: flex; gap: 14px; padding: 6px 0; border-bottom: 1px solid {RULE};"><span style="width: 22px; flex-shrink: 0; font-family: {DISP}; font-size: 22px; font-weight: 700; line-height: 1; color: {ACC}; text-align: right;">{i}</span><span><b style="font-weight: 600;">{t}.</b> {x} <i style="color: {ACC};">{r}</i></span></div>''' for i, (t, x, r) in enumerate(ch["acts"], 1))
    return h2("Key activities", ch["acts_note"]) + f'<div style="border-top: 1.5px solid {INK};">{items}</div>' + notes()


def p4(ch):
    def refs(lst):
        return "".join(f'<div style="display: flex; gap: 12px; padding: 4px 0; border-bottom: 1px solid {RULE};"><span style="width: 142px; flex-shrink: 0; font-weight: 600; color: {ACC};">{r}</span><span>{d}</span></div>' for r, d in lst)
    qs = "".join(f'<div style="display: flex; gap: 10px;"><span style="width: 16px; flex-shrink: 0; font-weight: 600;">{i}.</span><span><i>{k}:</i> {q}</span></div>' for i, (k, q) in enumerate(ch["questions"], 1))
    h3 = f"font-family: {DISP}; font-size: 18px; font-weight: 700;"
    out = h2("Across Scripture", ch["refs_note"])
    if ch["ot"]:
        out += f'<h3 style="margin: 0 0 2px; {h3}">Old Testament</h3><div style="border-top: 1.5px solid {INK};">{refs(ch["ot"])}</div>'
    if ch["nt"]:
        out += f'<h3 style="margin: 12px 0 2px; {h3}">New Testament</h3><div style="border-top: 1.5px solid {INK};">{refs(ch["nt"])}</div>'
    return out + f'''<div style="margin-top: 14px; padding: 12px 16px; background: #F1EADB; border-radius: 3px; display: flex; flex-direction: column; gap: 5px;"><span style="{h3}">For discussion</span>{qs}</div>''' + notes()


def print_html(ch):
    f = {k: (TOOLS / "fonts" / v).as_uri() for k, v in
         {"c": "Cormorant.ttf", "ci": "Cormorant-Italic.ttf", "s": "SourceSerif.ttf", "si": "SourceSerif-Italic.ttf"}.items()}
    faces = f"""@font-face{{font-family:'Cormorant Garamond';src:url('{f["c"]}');font-weight:300 700;font-style:normal}}
@font-face{{font-family:'Cormorant Garamond';src:url('{f["ci"]}');font-weight:300 700;font-style:italic}}
@font-face{{font-family:'Source Serif 4';src:url('{f["s"]}');font-weight:200 900;font-style:normal}}
@font-face{{font-family:'Source Serif 4';src:url('{f["si"]}');font-weight:200 900;font-style:italic}}"""
    n = ch["first_page"]
    pages = [page(ch, n, p1(ch), "Overview"), page(ch, n + 1, p2(ch), f"The life of {ch['name']}"),
             page(ch, n + 2, p3(ch), "Key activities"), page(ch, n + 3, p4(ch), "Across Scripture")]
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{faces}@page{{size:6in 9in;margin:0}}body{{margin:0}}</style></head><body>{"".join(pages)}</body></html>'


FIT_JS = """() => {
  const out = [];
  document.querySelectorAll('.content').forEach((c, i) => {
    const n = c.querySelector('.notes');
    if (n && c.scrollHeight > c.clientHeight + 1) n.remove();
    out.push(Math.max(0, c.scrollHeight - c.clientHeight));
  });
  return out;
}"""


# ------------------------------------------------------------------ website
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">'


def shell(title, desc, root, body, current=""):
    links = [("home", "", "Home"), ("people", "characters/", "All people"), ("about", "about/", "About the book")]
    nav = "".join(f'<a href="{root}{href}"' + (' aria-current="page"' if current == key else "") + f'>{label}</a>' for key, href, label in links)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{html.escape(re.sub('<[^>]+>', '', desc))}">
{FONTS}
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<header class="site"><div class="wrap"><a class="brand" href="{root}">{BOOK}</a><nav aria-label="Site">{nav}</nav></div></header>
{body}
<footer class="site"><div class="wrap"><p>{BOOK} · A small-group study of people in Scripture. Scripture quotations from the King James Version. Dates are approximate.</p></div></footer>
</body>
</html>
'''


def chapter_page(ch, prev, nxt):
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in ch["glance"])
    tl = "".join(f'<li><div class="when"><strong>{d}</strong><span>{a}</span></div><div class="spine" aria-hidden="true"></div><div class="what"><h3>{t}</h3><p>{x}</p><span class="ref">{r}</span></div></li>' for d, a, t, x, r in ch["timeline"])
    acts = "".join(f'<li class="act"><span class="n" aria-hidden="true">{i}</span><h3>{t}</h3><p>{x}</p><span class="ref">{r}</span></li>' for i, (t, x, r) in enumerate(ch["acts"], 1))
    refs = lambda lst: "".join(f"<li><b>{r}</b><span>{d}</span></li>" for r, d in lst)
    cols = ""
    if ch["ot"]: cols += f'<div><h3 class="display">Old Testament</h3><ul>{refs(ch["ot"])}</ul></div>'
    if ch["nt"]: cols += f'<div><h3 class="display">New Testament</h3><ul>{refs(ch["nt"])}</ul></div>'
    qs = "".join(f"<li><em>{k}:</em> {q}</li>" for k, q in ch["questions"])
    pn = (f'<a class="prev" href="../{prev["slug"]}/">← {prev["number"]} · {prev["name"]}</a>' if prev else "<span></span>")
    pn += (f'<a class="next" href="../{nxt["slug"]}/">{nxt["number"]} · {nxt["name"]} →</a>' if nxt else "")
    blocks = ""
    for x in ch.get("extras", []):
        inner, ul = "", []
        for kind, t in x["items"] + [("end", "")]:
            if kind == "li": ul.append(f"<li>{md(t)}</li>"); continue
            if ul: inner += f"<ul>{''.join(ul)}</ul>"; ul = []
            if kind == "p": inner += f"<p>{md(t)}</p>"
        blocks += f'<div class="deep"><h3 class="display">{html.escape(x["title"])}</h3>{inner}</div>'
    deeper = (f'<section id="deeper"><div class="wrap"><h2 class="display">Go deeper</h2><p class="intro">Extra background and a short reading plan for the week. These are on the website only, not in the printed pages.</p><div class="deeper">{blocks}</div></div></section>' if blocks else "")
    deeper_link = '<a href="#deeper">Go deeper</a>' if blocks else ""
    closing = (f'<div class="closing"><div class="wrap"><blockquote>“{md(ch["closing"])}”<cite>{md(ch["closing_ref"])}, KJV</cite></blockquote></div></div>' if ch["closing"] else "")
    body = f'''<main>
<div class="wrap">
<header class="hero">
  <div>
    <p class="kicker">Part {ch["part_no"]} · {ch["part"]} · Chapter {ch["number"]}</p>
    <h1 class="display">{ch["name"]}</h1>
    <p class="lede">{ch["summary"]}</p>
    <p>{ch["intro"]}</p>
    <p class="actions"><a class="button" href="{ch["slug"]}-lives-of-the-bible.pdf" download>Download printable PDF (4 pages)</a></p>
    <nav class="jump" aria-label="On this page"><a href="#timeline">Timeline</a><a href="#activities">Key activities</a><a href="#references">Across Scripture</a><a href="#discussion">Discussion</a>{deeper_link}</nav>
  </div>
  <dl class="facts">{facts}</dl>
</header>
</div>
<div class="verdict"><div class="wrap"><blockquote>“{ch["verse_full"]}”<cite>{ch["verse_ref"]}, KJV</cite></blockquote></div></div>
<section id="timeline"><div class="wrap"><h2 class="display">The life of {ch["name"]}</h2><p class="intro">{ch["timeline_note"]}</p><ol class="timeline">{tl}</ol></div></section>
<section id="activities"><div class="wrap"><h2 class="display">Key activities</h2><p class="intro">{ch["acts_note"]}</p><ol class="acts">{acts}</ol></div></section>
<section id="references"><div class="wrap"><h2 class="display">Across Scripture</h2><p class="intro">{ch["refs_note"]}</p><div class="refs">{cols}</div></div></section>
<section id="discussion"><div class="wrap"><div class="discuss"><h2 class="display">For discussion</h2><ol>{qs}</ol></div></div></section>
{deeper}
{closing}
<div class="wrap"><nav class="pn" aria-label="Chapters">{pn}</nav></div>
</main>'''
    return shell(f'{ch["name"]} — {BOOK}', f'{ch["name"]}: {ch["summary"]} A four-page small-group study with timeline, key activities and every Bible reference.', "../", body)


def characters_page(parts, ready):
    total = sum(len(p["people"]) for p in parts)
    secs = ""
    for p in parts:
        lis = ""
        for n, name, ref in p["people"]:
            if n in ready:
                lis += f'<li class="ready"><a href="../{ready[n]}/"><span class="num">{n}</span><span class="nm">{name}</span><span class="rf">{ref}</span><span class="st">Read</span></a></li>'
            else:
                lis += f'<li><span><span class="num">{n}</span><span class="nm">{name}</span><span class="rf">{ref}</span><span class="st">Coming soon</span></span></li>'
        secs += f'<section class="part"><h2 class="display">Part {p["no"]} · {p["name"]}</h2><p class="span">{p["span"]}</p><ul class="people">{lis}</ul></section>'
    body = f'''<main><div class="wrap">
<header class="pagehead"><h1 class="display">All {total} people</h1><p>The full reading order of the book, from Adam to the early church. Each person gets the same four-page study. {len(ready)} {"is" if len(ready) == 1 else "are"} ready to read now; the rest are on the way.</p></header>
{secs}
</div></main>'''
    return shell(f"All people — {BOOK}", f"The full list of {total} people covered in {BOOK}, in reading order.", "../", body, "people")


def about_page(total):
    body = f'''<main><div class="wrap narrow">
<header class="pagehead"><h1 class="display">About the book</h1><p class="lede">{BOOK} is a small-group study of {total} people in Scripture, from Adam to the early church.</p></header>
<div class="prose">
<h2 class="display">One person, four pages</h2>
<p>Every chapter follows the same pattern, so a group always knows what to expect:</p>
<ol>
<li><strong>Overview.</strong> Who they were, key facts at a glance, and a key verse.</li>
<li><strong>Timeline.</strong> The main moments of their life, each with its reference.</li>
<li><strong>Key activities.</strong> What they actually did, numbered and referenced.</li>
<li><strong>Across Scripture.</strong> Every Old and New Testament passage that mentions them, plus four discussion questions.</li>
</ol>
<p>Direct references are kept separate from thematic echoes, and later tradition is labelled so it is never passed off as Scripture.</p>
<h2 class="display">Using it in a group</h2>
<p>One chapter fits one meeting of about 45 minutes. Download the printable PDF from any chapter page and hand out copies, or read along on a phone.</p>
<h2 class="display">Kindle and paperback</h2>
<p>The complete book is being prepared for Kindle and as a paperback in two volumes: <em>The Old Testament</em> and <em>The New Testament</em>. Chapters appear here first, free to read, as they are written.</p>
<h2 class="display">Scripture</h2>
<p>Quotations are from the King James Version. Dates are approximate and follow common scholarly estimates.</p>
</div>
</div></main>'''
    return shell(f"About the book — {BOOK}", f"About {BOOK}: a four-page small-group study of {total} people in Scripture.", "../", body, "about")


def home_page(chs, total):
    cards = "".join(f'<li><a href="{c["slug"]}/"><span class="num">{c["number"]}</span><div><h3 class="display">{c["name"]}</h3><p>{c["summary"]}</p></div><span class="ref">Part {c["part_no"]}</span></a></li>' for c in chs)
    body = f'''<main><div class="wrap">
<header class="homehero">
  <h1 class="display">{BOOK}</h1>
  <p class="lede">{total} people from Genesis to Revelation. One four-page study for each: who they were, what they did, and every passage that mentions them.</p>
  <p class="actions"><a class="button" href="characters/">See all {total} people</a><a class="textlink" href="about/">About the book →</a></p>
</header>
<section class="ready"><h2 class="display">Ready to read</h2><ul class="studies">{cards}</ul></section>
</div></main>'''
    return shell(f"{BOOK} — a small-group study of people in Scripture", f"{BOOK}: {total} people from Genesis to Revelation, each in a four-page small-group study.", "", body, "home")


# ------------------------------------------------------------------ main
def main():
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}
    parts = parse_list()
    total = sum(len(p["people"]) for p in parts)

    chs, errors = [], []
    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        try:
            chs.append(parse_chapter(path, parts))
        except ChapterError as e:
            errors.append(str(e))
    chs.sort(key=lambda c: c["number"])

    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    shutil.copy(TOOLS / "style.css", OUT / "assets" / "style.css")
    (OUT / ".nojekyll").write_text("")

    from playwright.sync_api import sync_playwright
    tmp = TOOLS / ".tmp"; tmp.mkdir(exist_ok=True)
    overflow = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 700, "height": 1000})
        for c in chs:
            if only and c["number"] not in only:
                continue
            (OUT / c["slug"]).mkdir(exist_ok=True)
            h = tmp / f'{c["slug"]}.html'
            h.write_text(print_html(c), encoding="utf-8")
            pg.goto(h.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            over = pg.evaluate(FIT_JS)
            for i, px in enumerate(over, 1):
                if px > 0:
                    overflow.append(f'{c["number"]:03d} {c["name"]}: page {i} is {px}px too long — shorten it by about {px // 18 + 1} line(s)')
            pg.pdf(path=str(OUT / c["slug"] / f'{c["slug"]}-lives-of-the-bible.pdf'), width="6in", height="9in",
                   print_background=True, prefer_css_page_size=True)
            print(f'built {c["number"]:03d} {c["name"]}')
        browser.close()
    shutil.rmtree(tmp, ignore_errors=True)

    for i, c in enumerate(chs):
        prev = chs[i - 1] if i > 0 else None
        nxt = chs[i + 1] if i + 1 < len(chs) else None
        (OUT / c["slug"]).mkdir(exist_ok=True)
        (OUT / c["slug"] / "index.html").write_text(chapter_page(c, prev, nxt), encoding="utf-8")
    (OUT / "characters").mkdir(exist_ok=True)
    (OUT / "about").mkdir(exist_ok=True)
    (OUT / "characters" / "index.html").write_text(characters_page(parts, {c["number"]: c["slug"] for c in chs}), encoding="utf-8")
    (OUT / "about" / "index.html").write_text(about_page(total), encoding="utf-8")
    (OUT / "index.html").write_text(home_page(chs, total), encoding="utf-8")

    print(f"\nWebsite written to {OUT} ({len(chs)} chapters).")
    if errors:
        print("\nCHAPTERS SKIPPED — fix the format:")
        for e in errors: print("  - " + e)
    if overflow:
        print("\nPAGES TOO LONG — the PDF cuts these off:")
        for o in overflow: print("  - " + o)
    if errors or overflow:
        sys.exit(1)
    print("All chapters fit on their 4 pages.")


if __name__ == "__main__":
    main()
