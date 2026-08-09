---
name: seer-website
description: Write or upgrade pages for a seer-framework project's Astro+Starlight docs site (the repo's `www/` — a reverse-engineering field guide to a game). Use when adding or editing anything under `www/src/content/docs/`, adding a sprite/asset gallery or a `_sidebar.json` entry, turning raw `docs/<game>/` research notes into curated public pages, documenting extracted assets on the site, or auditing an existing seer site against the quality bar. Triggers on "add a page to the site", "document this format on the website", "build out the <game> section", "make a gallery for these sprites", "the www pages need work".
---

You are writing a **curated, human-readable field guide** to a reverse-engineered
game — the public face of a seer project. The exhaustive byte-level evidence
already lives in the repo's `docs/<game>/`. Your job is not to restate it; it is
to turn it into pages a stranger can read, with every claim still carrying its
evidence.

The reference implementation is **`~/Development/crawl/www`** (Black Crypt): 33
pages, 7 sidebar groups, one page per file format, quantified claims throughout,
a published status page, and build-time components that read the extraction
pipeline's own manifests. When in doubt about depth, tone, or structure, open the
crawl page named in `references/page-types.md` for that page type and match it.

**Not this skill:** `~/Development/seer/wwwdocs` is the *framework's* own docs
site, not a game field guide — it is deliberately named `wwwdocs`, not `www`,
to keep that distinction visible. Its pages are generated from the real source
docs by `scripts/sync-docs.mjs` and must never be hand-edited; it has no game,
no extracted assets, and no `_sidebar.json`. If you are there, edit the source
`docs/*.md` or `packages/*/README.md` instead, and ignore everything below.

A seer *project's* site is always `www/` (that's what `create-seer-website`
scaffolds) — that one is this skill's territory.

---

# Orient first — three reads, not optional

Do these before writing a single line. They take two minutes and prevent the
three most common failures (wrong wiring, invented facts, a parallel taxonomy).

1. **The site's own `AGENTS.md` and `README.md`** (in `www/`). Every seer site
   is scaffolded from `create-seer-website` but they diverge: single-game
   (`crawl`) vs multi-game with per-game build modules (`middilgard`), different
   asset roots, different generated artifacts. This tells you where content
   lives, which files are generated (**never hand-edit `generated/sidebar.mjs`**),
   and how to run the build.
2. **The raw notes you are summarising** — `docs/<game>/**`, plus the repo's
   `AGENTS.md` and its `TODO.md`/status surface. **The raw notes are the source
   of truth.** Every number you publish comes from there or from a manifest you
   read; nothing comes from memory or inference. If a curated page and the raw
   notes disagree, the raw notes win and you fix the page.
3. **The existing `_sidebar.json`** for the game. New pages join the existing
   taxonomy. Do not invent a parallel grouping because it suits one page.

Also check what actually got extracted — `ls public/assets/<game>/**` and read
the manifests. Pages describe what exists, not what should exist.

---

# Two modes

**Author** (default) — write or upgrade pages. Continue below.

**Audit** — "check the site against the standard", "what's missing on the
website". Read `references/audit.md` and follow it. Audit mode **reports**; it
does not edit unless the user asks for fixes.

---

# The bar — ten rules

These are what separate a crawl page from scaffold filler. Full treatment with
worked before/afters in `references/evidence-and-voice.md`.

1. **Every claim carries a number.** "204 monster sprites across 13 dungeon
   levels", "685/685 references resolve exactly under this rule", "13/13, zero
   deviation", "3,950 bytes of `0x00`", "map 7 (47% of pixels)". Banned:
   *several*, *many*, *most*, *various*, *a handful of*, *a number of* — when
   you reach for one, you are missing a count you could have gone and got.
2. **Every number carries its provenance.** Where it came from: a file offset
   (`bcdfa` `+0x1B5B3`), a segment-relative address in a decompressed image
   (`bcdft` S_1 `+0x27B00`), a disassembly label (`bcdfp` `LAB_00BD`), a named
   routine (`OpenBcdfaFile`), or the manifest the page read at build time.
3. **Unresolved is stated, never rounded up.** A page that says "mostly solved"
   names what isn't. Open questions go on the status page as one-line
   *questions*, and are referenced inline where a reader would otherwise assume
   the format is complete.
4. **Images are real pipeline output, not illustrations.** If a visual is
   composited or rendered, it comes from the same verified code the project
   ships, and the build **fails** if that code fails — no silent fallback to a
   mockup. Where a page once showed mockups, say so and say what changed
   (`assets/textures.mdx` § "These are real game output, not illustrations").
5. **Generated visuals are reproducible.** Publish the exact inputs — crawl's
   textures page gives a `view / map / cell / facing / shows` table per tileset
   plus the harness URL params (`?map=1&x=57&y=1&facing=1`) that reproduce each
   frame pixel-for-pixel.
6. **Corrections are published, not silently patched.** When a previous claim
   was wrong, the page says it was wrong and why (`graphics/palettes.md` § "A
   common pitfall": *"The old `bcdfu` file offset `0x2C6` claim was wrong — that
   offset lands inside the library-name strings."*). This is what stops the next
   reader re-deriving a dead end.
7. **Pitfalls go at the top, before the reader can go wrong.** `files/bcdfs.md`
   opens with a blockquote: *"Use the verified walker, don't hand-roll a scan"* —
   and then says exactly which four details break naive walkers.
8. **State and honour the source-of-truth hierarchy.** The home page says the
   site is a curated summary of `docs/<game>/` and that the raw notes win. Every
   deep page points back at the specific note file behind it.
9. **Cross-link forward and back.** Overview → foundations → format pages →
   galleries → status. Every page ends knowing what the reader should read next;
   asset pages link to their format page and vice versa.
10. **No placeholder text survives.** The scaffold ships `index.mdx` containing
    *"replace this content with a real overview of the project once you have
    one"*. That paragraph in a committed site is a defect, not a page. Same for
    a sidebar label like `Bcdfa` where the page is about the game's biggest
    container.

---

# Authoring workflow

1. **Pick the page type** and read its playbook + named crawl exemplar in
   `references/page-types.md`. There are eight: game home (splash), project
   overview, foundations, one-per-format, asset index, gallery, status,
   port comparison.
2. **Read the raw-notes section it summarises.** Pull the real numbers, offsets,
   and confidence levels out. If the notes don't support a claim, the claim
   doesn't go on the page.
3. **Draft to the type's skeleton.** Frontmatter with `title` **and**
   `description` on every page — no exceptions; `description` feeds search
   results and social cards.
4. **Add the gallery/component** if the page is showing assets — read
   `references/components.md` first. Components read manifests at build time;
   they never carry hand-maintained frame lists.
5. **Add the `_sidebar.json` entry** with a label that means something —
   `bcdfa — The Big Container`, `bcdfx/bcdfy/bcdfz — Tilesets`, `Palettes &
   Accent Ramps`. Put it in an existing group unless the page genuinely opens a
   new axis.
6. **Re-run the build script** (`node scripts/build.mjs`) so the sidebar
   regenerates, then verify.

---

# Verification — required before reporting done

- `npm run build` in `www/` (this runs `scripts/build.mjs` first). It must pass.
  A build that only passes because a generator silently fell back to committed
  artifacts is not a pass — read the script's log lines.
- Start the dev server in background mode (`astro dev --background`; manage with
  `astro dev stop|status|logs`) and load the new page.
- **Every asset URL on the page resolves.** A 404 image is invisible in a build
  log. Check the actual paths under `public/assets/<game>/`.
- The sidebar entry appears, in the intended group, with the intended label.
- **Re-read your claims against the raw notes.** Any number you cannot point at
  a source for comes off the page.
- Report honestly: if a section is thin because the underlying research is thin,
  say so rather than padding it.

---

# Reference files — read when

| File | Read it when |
|---|---|
| `references/page-types.md` | Before drafting any page — pick the type, get its skeleton and exemplar |
| `references/evidence-and-voice.md` | Writing prose, tables, confidence statements, a status page, or fixing a vague draft |
| `references/components.md` | The page shows sprites/assets, or you're building or extending an `.astro` component |
| `references/audit.md` | Audit mode, or before a big content push, to know what "done" looks like |
