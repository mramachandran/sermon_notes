# Trim brief: make chapters fit their 4 printed pages

Book: *Lives of the Bible*, a small-group Bible study. Chapters live in `/mnt/user-data/outputs/kit/chapters/NNN-slug.md`.
Read first: `/mnt/user-data/outputs/kit/book/01-style-guide.md` and the two model chapters `chapters/056-ruth.md` and `chapters/098-josiah.md` (these already fit — match their length and density).

## Your job
For each chapter number assigned to you, shorten the text so every page fits, then verify.

Check command (parallel-safe, does not touch docs/):
`python3 /mnt/user-data/outputs/check.py NNN NNN ...`
It lists pages that are too long and roughly how many lines to cut. Repeat until your chapters no longer appear in the "PAGES TOO LONG" list. Ignore lines for chapters not assigned to you.

## How to trim (in this order of preference)
- **Page 1:** intro paragraph to 80–110 words. Each "At a glance" value short enough for one line; keep 6–8 rows. You may shorten the key verse with " … " between exact KJV fragments, as Ruth does.
- **Page 4 (Across Scripture):** each bullet becomes `- **Reference.** Short description` of one line (about 8–12 words), like Ruth. Merge or drop the weakest items. Thematic links use `- **Echo: Reference.** description` (one per bullet) or keep one `- **Echoes.**` bullet if short. Keep For discussion at exactly 4 questions, but shorten wording if needed.
- **Page 2 (timeline):** tighten each entry to one or two sentences; shorten the italic date note. M chapters may drop to 6–7 entries (merge adjacent events). Keep at least 3.
- **Page 3 (key activities):** one sentence each; may merge to reach fewer items, keep at least 4.

## Hard rules
- Only cut or condense. **Never add** new facts, dates, references or quotations.
- Never change the wording inside a KJV quotation. You may remove a quotation, or shorten with " … " between exact fragments.
- Keep tradition and debated-view labels. If you cut a sentence that labels tradition ("Tradition says…", "later tradition, not the Bible"), keep a short version of it somewhere visible (e.g. the italic note line under the page heading).
- Keep line formats the parser needs exactly:
  - Timeline: `**<when> — <Title>.** <text> *<Reference>*` — line must end with the italic reference.
  - Activities: `N. **Title.** text *Reference*`
  - Across Scripture: `- **Reference.** text` under `### Old Testament` / `### New Testament`
  - Questions: `1. **Observe:** …`, `2. **Understand:** …`, `3. **Apply:** …`, `4. **Apply:** …`
  - Exactly 3 `\newpage` lines; front matter unchanged.
- Extra sections the build does not render (`### The world around them`, `### Words and places`, `### Read it yourself`, `## Group notes`, loose `*Tradition.*` paragraphs) do NOT count toward length. Leave them as they are.
- Don't overshoot: aim to just fit, not gut the chapter. Keep the warm, plain voice.
- Edit only your assigned files. Use the Edit tool.

## Finish
Run the check for all your numbers one last time. Reply with: (1) any chapter that still doesn't fit, (2) at most 5 bullets total of anything substantive you removed that the author might miss (e.g. a dropped tradition note or debated view). Keep the reply short.
