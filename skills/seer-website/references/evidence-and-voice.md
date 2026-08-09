# Evidence and voice

The ten rules from SKILL.md, in full, with real before/afters. Everything quoted
is from `~/Development/crawl/www/src/content/docs/blackcrypt/`.

---

## 1. Every claim carries a number

A seer site's whole value is that the numbers are real. Vagueness reads as
"nobody actually counted", which is usually true when it appears.

> ❌ The game contains many monster sprites spread across several dungeon files.
>
> ✅ **All 204 monster sprites** across the 13 dungeon levels extract
> byte-exactly. *(game/overview.md)*

> ❌ Most of the item name references resolve correctly with this rule.
>
> ✅ 685/685 references in the shipped `bcdfs` resolve exactly under this rule.
> *(files/bcdfs.md)*

**Banned hedges:** *several, many, most, various, a handful of, a number of,
some, roughly, approximately* (unless the figure genuinely is approximate and
you say why), *a few*, *plenty of*.

**Allowed and encouraged:** exact counts, byte sizes with thousands separators
(`171,005 bytes`), fractions that show completeness (`13/13, zero deviation`,
`92 of 95`, `90/204 sprites named`), percentages with their basis (`map 7 (47%
of pixels)`, `100.000% silhouette agreement`), dimensions (`24×24 @ 6 sequential
bitplanes`), and arithmetic that shows the number is understood
(`147 sprites = 49 items × 3 view depths`, `3,950 bytes of 0x00`,
`plane pitch $1F40 = 8000 = 320×200/8`).

When a count would be tedious to get, get it anyway — the manifests are right
there (`jq '.frames | length' public/assets/<game>/.../items.json`).

## 2. Every number carries its provenance

The reader must be able to go and check. Acceptable provenance forms, all in
active use on crawl:

| Form | Example |
|---|---|
| File offset | `bcdfa` `+0x1B5B3` |
| Segment-relative address in a decompressed image | `bcdft` S_1 `+0x27B00` |
| Disassembly label | the copper list is built in `bcdfp` (`LAB_00BD`) |
| Named routine | `OpenBcdfaFile`, S_1 `+0x1DBD2`; `SetDungeonPalette(index)`, S_1 `+0x26900` |
| Runtime address in a savestate | resident in chip RAM at `$7D918` in three savestates |
| Cross-port confirmation | confirmed 100% against the DOS port's `clipper.clp` |
| A manifest the page reads at build time | geometry comes from a 147 × 10-byte blit-descriptor table at `bcdft` S_1 `+0x271B6` |

A number with no provenance is a rumour. If the raw notes don't give you one,
that's a signal the finding is weaker than it looks — say so instead.

## 3. Unresolved is stated, never rounded up

Four confidence tiers, and where each belongs:

| Tier | How to phrase it | Where |
|---|---|---|
| **Confirmed** | "byte-exact", "13/13, zero deviation", "code-confirmed via their consumer routines", "verified 100.000% against 43 placements in 10 real screenshots" | Anywhere |
| **Traced but unverified** | "traced to `LAB_…` but no consumer has been found", "the mapping is not 1:1" | Format page, with the gap named |
| **Hypothesis** | "the old reading was wrong; no consumer of the frame's own `+0x0C` has been traced" | Status page; on a format page only if flagged as open |
| **Open** | one-line question on the status page | Status page, linked from the format page's "The open bits" |

Every format page that is not complete gets a short **## The open bits** section
naming what's missing and linking to `/…/status/`. `files/bcdfa.md` does exactly
this in three lines.

Negative results are results. Publish them: *"an exhaustive search confirmed
**no indexed bestiary table exists** in the game's data."*

## 4. Images are real pipeline output, not illustrations

The strongest single section on the crawl site is `assets/textures.mdx` §
"These are real game output, not illustrations", which:

- admits what the page used to be ("a script picked plausible-looking dest
  positions and stacked a fixed 'corridor + centrepiece' layout together by
  hand"),
- says what makes the current images real (the walker "reproduces the game's own
  view-geometry walk (`buildViewList`), draw order (`compositeDrawList`/
  `paintOrder`) and indexed palette compositing byte-for-byte"),
- and names the guarantee: *"this page's build now fails if the real renderer
  fails."*

If you add generated imagery, wire it so the build fails when the generator
fails. A generator that silently falls back to a committed artifact is fine as a
**CI-without-game-files** path (that's what `scripts/build.mjs`'s
`hasLiveAssetSrc` gate is for) — but never as a "renderer broke, ship a mockup"
path.

## 5. Generated visuals are reproducible

Publish the inputs. Crawl's per-tileset tables:

```
| view | map | cell | facing | shows |
|---|---|---|---|---|
| corridor | bcdfb (`map=1`) | (57, 1) | E | open corridor, side walls receding to a far wall |
```

plus the sentence that makes them actionable: *"run the interactive harness …
and open `tools/walker/index.html` with these query params
(`?map=1&x=57&y=1&facing=1`) and it renders the identical frame
pixel-for-pixel."*

Also publish the *reason* for an absence when it looks like a bug: bcdfy's set
shows a floor item instead of an alcove because "this tileset's own atlas (46
sub-images vs. 83 for bcdfx/bcdfz) has no alcove or plaque art at all — a real
fact about the tileset's art, not a gap in the walker."

## 6. Corrections are published, not silently patched

Two live examples:

> There is **no separate "monster palette"**. Monsters and walls necessarily
> share one EHB palette. The old `bcdfu` file offset `0x2C6` claim was wrong —
> that offset lands inside the library-name strings. *(graphics/palettes.md)*

> The word `+0x0C` of a Door-frame (`0x11`) record is unmapped. The old
> "structure-present / occupancy flag" reading was wrong. *(status.md)*

Pattern: **what was believed → that it was wrong → what the offset/value
actually is → (optionally) what misled everyone.** A silent edit costs the next
reader the same dead end.

## 7. Pitfalls go at the top

Use a blockquote immediately after the identity paragraph, before any structural
detail:

> **Use the verified walker, don't hand-roll a scan.** Records are a fixed 20
> bytes, monsters are two of them, every action record is 8 bytes, and empty
> rows are encoded `40 FF` with **signed** column bounds — which is what breaks
> naive walkers on maps 11–13.

It names the mistake, then gives the four specifics that cause it. A pitfall
that doesn't say *which* input triggers it isn't a pitfall, it's a mood.

Foundations pages instead close with **## A common pitfall** — the wrong belief
the page exists to kill.

## 8. Source-of-truth hierarchy

On the home page, verbatim in spirit:

> The raw, exhaustive notes live in the repository: `docs/<game>/…`. These pages
> are a curated summary. When they disagree with the raw notes, the raw notes
> win — they carry the full evidence, paths-tried tables, and corrections.

On deep pages, point at the specific note: *"See the raw notes for the full
table."* Give a path, not a gesture. And note the corollary for your own work:
when you find a page contradicting the notes, **fix the page**, never the notes.

## 9. Cross-link forward and back

- Overview ends with a "How to read this site" ladder.
- Asset index links to every gallery it summarises; galleries link back to the
  format page (`[bcdfx/bcdfy/bcdfz](/blackcrypt/files/bcdfxyz/)`).
- Format pages link "The open bits" to the status page.
- Links are absolute site paths with a trailing slash
  (`/blackcrypt/assets/screens/`), matching Starlight's route shape.

## 10. No placeholder text survives

Delete on sight, in any site you touch:

- "Welcome to the X documentation." / "replace this content with a real
  overview of the project once you have one" — the scaffold's own `index.mdx`
  placeholder. It survived in middilgard's flagship game section for months
  before being rewritten, which is how long a placeholder can sit on a public
  landing page unnoticed.
- Sidebar labels that are just the capitalised filename.
- A `<Card>` or hero action pointing at a page that doesn't exist yet.
- Lorem-ish connective tissue: "This page describes the format." — say what the
  format *is*.

---

# Formatting choices

**Code fence vs table.** Both, for anything with a bit layout:

- **Code fence** for byte-offset maps and bit layouts — fixed-width alignment is
  the point:
  ```
  +0  3 bytes  unknown (usually 0)
  +3  1 byte   vertical first row (on the 64×64 grid)
  ```
  ```
  Byte 0: [type:4b][0xF]
  Byte 2: [wall_flags:4b][uniq_hi:4b]
  ```
- **Table** for field semantics and enumerated values —
  `| Field | Bits | Description |`, `| Offset | Size | Field |`,
  `| Offset | Size | Content | Status |`.
- **Both** when a format has bitfields: fence for the layout, table for what
  each field means (`files/bcdfs.md` § Square format).

**Inline colour swatches** for palette tables — a `<span class="sw">` with an
inline `background`, plus one scoped `<style>` block on the page:

```html
<span class="sw" style="background:rgb(187,51,0)"></span>`0b30`
```
```html
<style>
.sw { display:inline-block; width:0.8em; height:0.8em; border-radius:2px;
      vertical-align:-0.1em; margin-right:0.15em;
      border:1px solid rgba(128,128,128,.45); }
</style>
```

The border is what keeps near-black and near-white swatches visible in both
themes. Show the raw 12-bit/hex value **next to** the swatch — the swatch is an
aid, the number is the data.

**Emphasis** carries meaning, not decoration: **bold** the subject of a
quantified claim and the one word that changes everything (*"the word at `+2` is
a **tagged** reference, not a bare offset"*). Don't bold whole sentences.

**Headings** are noun phrases describing content ("The accent ramp varies per
dungeon level", "Entity placement", "The tileset ↔ ramp correlation"), not
"Introduction"/"Details"/"More info".

---

# What never goes on the site

- **Original game files or anything reconstructible into them.** The site ships
  extracted, derived assets (sprite atlases, palettes as JSON, rendered views).
  Never the original copyrighted data files, disk images, or an executable.
- **Raw dumps that belong in `docs/`** — full paths-tried tables, hex dumps,
  disassembly listings, exhaustive per-record enumerations. Summarise and link.
- **Speculation stated as fact.** If it's a hypothesis, it's on the status page
  phrased as a question.
- **Invented names.** An unattributed sprite is unnamed or omitted, never
  plausibly labelled.
- **Numbers you didn't verify this session** if you're editing a page whose
  underlying data changed. Re-read the manifest.
