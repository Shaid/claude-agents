# A "no corpus source exists" verdict may only mean the reference PDF sitting right next to the one you already opened was never opened too

**When it bites:** a doc states or is about to state "no third source
exists to arbitrate" / "X has zero illustration, dialogue-portrait, or
[in-corpus] entry anywhere" for a character/asset identification tie — check
`ls data/<game>/` (and sibling platform data dirs) for *every* PDF/manual/
artbook file before trusting that verdict, not just the one already checked
this project's history.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): ten-plus rounds of visual-
matching work on a 42-image portrait-crop bank had left two deity slots
tied, with the row's own text stating the tie was unbreakable because both
candidates "have zero illustration, dialogue-portrait, or battle-sprite
entry anywhere in this corpus." That survey was exhaustive — but scoped
only to the *game disc* corpus, because the only external document this
project had ever opened was one specific manual PDF. A second, unrelated
file had been sitting in the exact same `data/<game>/` directory the whole
time — `Valkyrie_Profile_Material_Collection_World_Guidance.pdf`, a
151-page official JP artbook — never referenced anywhere in the project's
docs or scripts. It was found only because an unrelated audit task ("check
this directory for other scanned manuals") widened the search radius past
the one file everyone already knew about. Its "God & Goddess" section gave
one official, developer-captioned in-game character portrait per deity,
settling both tied identifications in minutes via a feature-for-feature
visual match (same accessory gems, same hood shape, same hair — not generic
similarity).

**The generalizable trap**: "we checked the manual/artbook and it has
nothing" quietly narrows, across many rounds, into "we checked THE [singular]
manual" — and a project's own docs will describe the corpus that WAS
searched (the game disc) with total confidence while never flagging that a
second, unrelated reference document went unopened, because nobody
individually researching one identification question thinks to re-survey
the whole `data/` directory for unrelated PDFs. Re-run `ls data/<game>/`
(and any sibling-platform `data/<game2>/` directory for the same
franchise/publisher) whenever a doc says "no [visual/textual] source
exists" for something a licensed game's own official supplementary material
(artbook, strategy guide, manual, "material collection") would plausibly
cover — character designs, location fiction, bestiary lore, developer
commentary. `pdfinfo` every PDF found this way before reading any of
them: an artbook this size is very likely *also* an image-only scan (this
one was, `ScanSnap`-sourced), so the same vacuous-grep trap as
`image-only-pdf-grep-negative-is-vacuous.md` applies to it independently.

**Don't assume a reference is exhausted once it has solved one item —
re-skim it by category for every other open item too.** A second, later
session on the same project (round 121) re-opened the identical artbook
this file describes — already fully mined for its "God & Goddess"
character-portrait section — and did a full 151-page skim hunting for a
completely different open item's need (named background/location CG art,
not character portraits). It found a section nobody had looked at:
"CG美術館" (CG Art Museum), a one-page themed gallery of 5 named in-game
background scenes, distinct from both the character-bio section and a
"Story" section illustrating real-world Norse mythology. This resolved one
more previously-unmatched background-gallery slot (a vaulted stone
corridor matched to "Military Training Facility"). The generalizable
point: an artbook/strategy-guide's sections are usually organized by asset
*category* (character portraits, background CG, bestiary line art,
real-world lore), not by which TODO item motivated opening the book in the
first place — treat "we already used this artbook" as scoped to the
section actually read, not the whole document, and re-skim the rest
whenever a *different kind* of open item (location art vs. character art
vs. item art) comes up. See
`artbook-mixes-real-world-photos-with-in-game-cg.md` for a trap specific to
sections that show both real-world and in-game imagery side by side within
that same skim.

**Tool-size caveat**: an artbook-scale scanned PDF can exceed the `Read`
tool's ~100 MB direct-PDF-extraction ceiling (this one was 268 MB; `Read`
returned "PDF file exceeds maximum allowed size for text extraction
(100MB)" outright, not degraded output). Workaround: `pdftoppm -f <page> -l
<page> -r <dpi> -png <pdf> <out-prefix>` rasterizes one or more pages to
PNG, which `Read` then opens normally. Use a cheap low-DPI whole-book pass
first (`-r 40`, no `-f`/`-l` — a 151-page book rasterized in ~12s) to skim
every page's rough content and locate the relevant section, THEN a
high-DPI targeted re-render (`-r 300`) of just the 1-3 pages that matter —
reading a multi-hundred-page scanned book at full resolution cover-to-cover
is both slow and unnecessary. Once the fine-detail candidate pages are
found, composite a tight crop of the reference portrait/asset side-by-side
with the already-extracted game asset (scaled to matching height, pasted
into one PNG) rather than switching between two separately-viewed images —
this made an otherwise-subtle match (two similarly-toned grey-haired
character portraits) immediately obvious in a way memory-based comparison
across tool calls was not.
