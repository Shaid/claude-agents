# Page types

Eight page types cover everything a seer field-guide site needs. Each has a
purpose, a required frontmatter shape, a section skeleton, and a crawl exemplar
to open and match.

All paths below are relative to `~/Development/crawl/www/src/content/docs/`
unless stated otherwise. **Open the exemplar** — the skeletons here are
compressed; the exemplar carries the tone.

---

## Frontmatter contract (all types)

```yaml
---
title: bcdfs — Map / Dungeon Data
description: The format of the file holding all 13 dungeon maps.
---
```

- `title` and `description` on **every** page. `description` is a full sentence
  that says what the page contains — it feeds Starlight's search index, the
  `<meta>` description, and social cards. Pages that omit it (crawl's gallery
  pages are the weak spot here) are worse for it; don't copy that.
- `sidebar: { order: N }` only where source order matters within a group and the
  manifest can't express it.
- `template: splash` plus a `hero:` block on home pages only.
- Title style: `<identifier> — <plain-English identity>` for format pages
  (`bcdft — Data Carrier (LZ77)`), plain title case otherwise.

## Sidebar and slugs

- Order and labels live in `src/content/docs/<game>/_sidebar.json`;
  `scripts/build.mjs` generates `generated/sidebar.mjs` from it. **Never edit
  the generated file.**
- Slugs are content file paths under `src/content/docs/`, minus the extension.
  A game's home page slug is `<game>` — **not** `<game>/index`.
- Entries are `{ "label", "slug" }`, nested inside `{ "label", "items": [...] }`
  groups. Multi-game sites (middilgard) concatenate one `_sidebar.json` per game.
- Group labels name an axis of the material, not a folder. Crawl's seven:
  *Black Crypt* (home + status), *The Game*, *Graphics Foundations*,
  *File Formats*, *Sound & Music*, *DOS Version*, *Extracted Assets*.

---

## 1. Game home (splash)

**Exemplar:** `blackcrypt/index.mdx` · multi-game site root: `middilgard`'s
`index.mdx` with its `GameCardGrid`.

Purpose: orient a stranger in 30 seconds and route them.

```
frontmatter: title, description, template: splash, hero { tagline, actions[2-3] }
├─ 2 paragraphs: what this site is, what the analysis is grounded in
├─ <CardGrid> — one <Card> per real section, each with a one-line
│   description of what's in it and a link ("Start here", "Read more")
└─ ## Source of truth — the raw-notes files by path, and the rule:
    "These pages are a curated summary. When they disagree with the raw
    notes, the raw notes win."
```

Hero actions: a primary "Start reading" into the overview, a secondary into the
assets, and a `variant: minimal` third into status. Cards must match sections
that actually exist — a card pointing at a stub is worse than no card.

## 2. Project overview

**Exemplar:** `blackcrypt/game/overview.md`

Purpose: what the game is, how its data is shaped, what the project achieved.

```
├─ Identity paragraph: game, year, developer/publisher, platform, engine idea
│   ("first-person dungeon crawler … uses the Amiga's EHB display mode —
│    6 bitplanes, 64 colours")
├─ How the data is organised — the file inventory in one paragraph
├─ ## What this project did — the goal, then "The headline results:" as a
│   bulleted list where every bullet is a quantified win
├─ ## How to read this site — an ordered link ladder (inventory →
│   foundations → formats → assets)
└─ ## A note on the raw notes — size and location of the real analysis
```

The headline-results list is the page's reason to exist. Each bullet is bold
subject + hard number: *"**All 204 monster sprites** across the 13 dungeon
levels extract byte-exactly."*

## 3. Foundations

**Exemplars:** `blackcrypt/graphics/display.md`, `graphics/blitter.md`,
`graphics/palettes.md`

Purpose: the platform/engine concepts a reader must hold before any format page
makes sense. Write these *before* the format pages if the material needs them.

```
├─ One-sentence statement of why this page comes first
├─ "X in one paragraph" — the concept, plainly, then the real register/values
│   in a code fence (BPLCON0 $6200, plane pitch $1F40 = 320×200/8)
├─ Mechanics sections with the actual formulas and bit orders
├─ Real-value tables (offsets, palettes, per-level assignments)
├─ ## Ground-truth oracle — how claims on this page were verified
└─ ## A common pitfall — the wrong belief this page exists to kill
```

`graphics/palettes.md` is the model for evidence density: a census table of
every copy of the palette in the game files with inline colour swatches, then
the authoritative table's address, then the runtime setter's address, then the
correlation table, then the correction.

## 4. One page per format

**Exemplar:** `blackcrypt/files/bcdfs.md` (map data),
`files/bcdfa.md` (mixed container)

Purpose: everything needed to write a decoder. **One page per format, always** —
never one "file formats" page with sections.

```
├─ H1 `file` — Identity
├─ Size in bytes + one-line identity, including what it is *not*
│   ("Despite being read by a routine that looks like a save-file loader,
│     it is not a save file")
├─ > Pitfall blockquote — the thing that breaks naive implementations
├─ ## File-level structure — numbered list of regions with sizes
├─ ## <Header> (N bytes) — code fence of `+off  size  meaning`
├─ ## <Record> format — code fence for the bit layout, then a
│   | Field | Bits | Description | table for semantics
├─ Worked example: a real record's bytes decoded to meaning
│   ("Map 1's header `00 00 00 00 1D 00 39` means rows 0–29 …")
├─ Variable-length / chaining rules, with an ASCII diagram if it chains
├─ Cross-format references, tagged-pointer rules, and the count that
│   proves them ("685/685 references … resolve exactly under this rule")
├─ ## The open bits — what's unsolved, linking to the status page
└─ ## Runtime parser — the routine this was derived from, and whether the
    project's decoder is ported instruction-for-instruction from it
```

For a container (`bcdfa`), lead with a `| Offset | Size | Content | Status |`
table of every block, then one section per interesting block.

## 5. Asset index

**Exemplar:** `blackcrypt/assets/screens.md`, `assets/sprites.md`

Purpose: show what came out, in bulk, with links onward to the interactive
galleries.

```
├─ Where the assets are served from (`/assets/<game>/<platform>/sprites/`)
│   and what a manifest is (PNG + JSON frame geometry)
├─ Link list to the per-atlas galleries
└─ One `##` per atlas: quantified caption naming the source file
    ("204 monster sprites across all 13 dungeon levels, byte-exact"),
    then the flat ![atlas](…) image
```

Note the caption pattern `## Monsters (from bcdfb–bcdfn)` — the section header
carries the provenance. State honestly when colour is unconfirmed: *"rendered in
greyscale unless the palette is confirmed."*

## 6. Gallery

**Exemplars:** `blackcrypt/assets/monster-gallery.mdx`,
`assets/effect-gallery.mdx`, `assets/other-sprite-galleries.mdx`,
`assets/textures.mdx`

Purpose: browse individual frames, with real names.

```
├─ imports
├─ H1
├─ 1–2 paragraphs answering: what am I looking at, how many are there,
│   where did the names come from, what can I do with a card
│   ("Hover a card to pause it")
└─ <Component />
```

Rules specific to galleries:

- **Say where names came from.** Crawl's monster gallery: names came from the
  manual, clue book, ending text, and — for the majority — the Windows demo's
  `crypt.exe`, which shares the creature-ID space.
- **Never invent a name.** The effect gallery shows 92 of 95 attributed effects
  and simply omits the three unattributed, "rather than given an invented name".
- A page can host several small galleries with an `##` each
  (`other-sprite-galleries.mdx`), each with its own one-line quantified intro.
- If the images are rendered rather than extracted, the page owes the reader a
  provenance section and a reproducibility table — see `assets/textures.mdx`,
  and rules 4 and 5 in SKILL.md.

## 7. Status

**Exemplar:** `blackcrypt/status.md`

Purpose: one honest surface for open work, mirroring the repo's `TODO.md`.
**Every game section should have one.** Its absence was the single most common
gap when this standard was written — no game on the five-game middilgard site
had one, despite every game carrying open items in its `TODO.md`.

```
├─ "This page mirrors the repo's single status surface, docs/<game>/TODO.md.
│   Every genuinely open item gets one row here; the full evidence and
│   paths-tried tables live in the raw notes."
├─ ## Open items — | ID | Status | Question (one line) |
│   The ID is the TODO's own key. The question is phrased as a *question*,
│   with the specific evidence that makes it a question.
├─ ## Closed (accepted as final) — | Item | Result |
│   Including negative results: "an exhaustive search confirmed no indexed
│   bestiary table exists in the game's data."
└─ ## Where to read the full evidence — the raw note files by path
```

Do not duplicate the evidence tables from `TODO.md` here. One row, one question,
pointer to the notes.

## 8. Port / platform comparison

**Exemplar:** `blackcrypt/dos/comparison.md`, `dos/overview.md`,
`dos/clipper.md`

Purpose: when the game shipped on more than one platform, what differs and what
each version proved about the other.

```
├─ ## Rendering differences — | Property | Platform A | Platform B |
├─ ## File size comparison — | Data type | A source | A size | B source | B size |
│   with a sentence explaining any surprising delta
├─ ## Resource mapping — how the two file layouts correspond, explicitly
│   flagging where it is *not* 1:1
└─ ## What's identical — the strongest section: formats that match
    structurally, differing only in (say) endianness, with a worked
    byte example of the same value in both
```

The other port is usually the project's best oracle. Say where it confirmed
something ("100.000% silhouette agreement") — that belongs on the format pages
too.
