# Style guide — Lives of the Bible (working title)

A small-group study of 170 people in Scripture, from Adam to the early church. It is published three ways: Kindle e-book, paperback, and a free website.

## 1. Reader and voice

- **Reader:** small groups and Sunday school classes. That means adults and older teens meeting weekly, often with a volunteer leader who is not a trained teacher.
- **Voice:** warm, clear, and plain. Aim for an 8th–10th grade reading level. Use short paragraphs and concrete verbs. No jargon without a one-line explanation.
- **Stance:** faithful to the text and non-denominational. Where Christians disagree (the date of the Exodus, the Nephilim, predestination), give the main views in one or two neutral sentences. Do not argue for any of them.
- **Tone:** never preachy or sentimental. Let the story carry the lesson.

## 2. Scripture rules (non-negotiable)

- **Quote only the King James Version (KJV).** It is public domain, so it is safe for a commercial book. Never quote the NIV, ESV, NKJV, NASB, NLT or other modern translations.
- Quote only verses you are certain of, word for word. If unsure of exact wording, paraphrase and give the reference instead.
- Never invent a verse, reference, date, or detail. If something is uncertain, say so ("c.", "probably", "tradition says").
- **Separate Scripture from tradition.** For example, "Mary Magdalene was a prostitute" is later tradition, not the Bible, and must be labelled as such.
- **Reference format:** full book names, an en dash for ranges, and semicolons between passages. For example: *2 Kings 22:1–2; 2 Chronicles 34:3*. Write "the LORD" in small capitals only inside KJV quotations.
- **Dates:** use BC/AD with "c." for approximations, for example *c. 640 BC*. If scholars differ widely, give the range or note it.

## 3. The chapter template: four pages per character

Every character gets exactly **four printed pages**: Overview, Timeline, Key activities, and Across Scripture with discussion. Pages are separated by a line containing only `\newpage`.

Each chapter is one file in `chapters/`, named `NNN-slug.md` (for example `056-ruth.md`), where NNN is the number from the character list. **The build script reads this exact format**, so follow the patterns below character for character. The finished examples are `chapters/056-ruth.md` and `chapters/098-josiah.md`; copy their shape.

```markdown
---
number: 56
name: Ruth
closing: "A KJV verse for the bottom of the web page."
closing_ref: Ruth 2:12
---

# Ruth

*One-line italic summary.*

An 80–110 word introduction paragraph.

## At a glance

| | |
|---|---|
| Name | Meaning of the name |
| When | c. date |
| ... | 6–8 rows, each value short enough for one line |

> The key verse in KJV (you may shorten it with …)
>
> — Ruth 1:16, KJV

\newpage

## The life of Ruth

*One italic line about dates.*

**c. 1100 BC · Days of the judges — Title of the moment.** One or two sentences. *Ruth 1:1–2*

**On the road — Title with no sub-line.** Text. *Ruth 1:6–18*

\newpage

## Key activities

*One italic line.*

1. **Title.** One sentence. *Reference*
2. **Title.** One sentence. *Reference*

\newpage

## Across Scripture

*One italic line.*

### Old Testament

- **Reference.** Short description
- **Echo: Reference.** Label thematic links with "Echo:"

### New Testament

- **Matthew 1:5.** Short description

## For discussion

1. **Observe:** Question
2. **Understand:** Question
3. **Apply:** Question
4. **Apply:** Question
```

**Rules the build checks:** exactly 4 pages; at least 3 timeline entries; at least 4 key activities; an Old and/or New Testament list; exactly 4 discussion questions; and every page fits on a 6×9 page. If a page is too long, the build says which page and roughly how many lines to cut.

**Characters with little material** (for example Simon of Cyrene or Methuselah) still get four pages. Use shorter lists and never pad with invented detail. The build automatically fills leftover space on pages 2–4 with a ruled **Group notes** area.

**Web-only extras (optional).** A chapter may add `### The world around them`, `### Words and places` and `### Read it yourself` blocks, plus a loose `*Tradition.*` paragraph, at the end of pages 2 or 3. The build shows them in a "Go deeper" section on the website only. They are not printed, so they never cause a page to overflow.

**Length:** about 280–320 words on page 1, and about 240–270 on the list pages. Keep each "At a glance" value and each reference description to one line.

## 4. Markdown rules (so one file builds EPUB, PDF and web)

- Use only standard Markdown: headings, lists, tables, blockquotes, bold and italic. No raw HTML, emoji, or images unless agreed.
- Use one `#` heading per file (the character's name). Sections use `##` and `###`, with no deeper levels.
- Keep tables to two to four columns so they fit a 6×9 page and a phone.
- Use straight front matter exactly as shown above, because the build scripts read it.

## 5. Accuracy checklist (run before a chapter is final)

1. Every reference was checked against the passage it cites.
2. Every quotation is exact KJV.
3. Dates are marked "c." and match the other chapters (for example, a king's dates agree in every chapter where he appears).
4. Tradition and debated views are labelled.
5. Cross-links to other characters use their exact names from the character list.
6. `python3 tools/build.py` finishes with "All chapters fit on their 4 pages."

## 6. Publishing notes

- **Kindle:** one e-book with all 170 chapters. There is no page limit.
- **Paperback:** 170 characters × 4 pages is about 680 pages plus front matter. That is heavy for a small group, so plan two volumes: *Old Testament* (Parts 1–7, 116 characters, about 470 pages) and *New Testament* (Parts 8–12, 54 characters, about 220 pages).
- **Web:** `tools/build.py` turns each chapter into a page and a printable PDF in `docs/`, which GitHub Pages publishes.
