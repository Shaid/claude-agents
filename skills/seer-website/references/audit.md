# Audit mode

Score an existing seer `www/` against the standard and report a prioritised gap
list. **Audit mode reports; it does not edit** — unless the user explicitly asks
for the fixes to be applied, in which case audit first, show the list, then fix.

---

## Procedure

1. **Inventory.** Read every `src/content/docs/**/_sidebar.json` and every
   `.md`/`.mdx` under `src/content/docs/`. Note line counts — a 12-line page in
   a site whose good pages run 80–130 lines is a signal, not proof.
2. **Read the ground truth.** `docs/<game>/**` and the repo's `TODO.md` /
   status surface. This is what tells you what the site is *missing*, as opposed
   to merely what it says badly. A solved format with no page is the highest-value
   finding an audit produces.
3. **Inventory the assets.** `public/assets/<game>/**` — every sprite atlas,
   screen, palette and rendered view. Assets extracted but never shown are a gap.
4. **Score each dimension below**, collecting concrete findings with file and
   line references.
5. **Report** in the format at the bottom.

---

## Rubric

| # | Dimension | Fail looks like |
|---|---|---|
| 1 | **Coverage** | A format solved in `docs/<game>/` with no page; an extracted atlas with no gallery or asset-index entry; a whole platform port undocumented |
| 2 | **Placeholder text** | The scaffold's "Welcome to the X documentation" / "replace this content with a real overview"; a hero action or `<Card>` linking to a page that doesn't exist; a sidebar label that is just the capitalised filename |
| 3 | **Quantification** | Hedges (*several/many/most/a handful*) where a count exists in the notes or a manifest; claims with no number at all |
| 4 | **Provenance** | Numbers with no offset, address, label, routine, or manifest behind them; "confirmed" with no statement of *how* |
| 5 | **Open-work surface** | No status page for the game; open questions from `TODO.md` invisible on the site; a format page presenting a partial decode as complete |
| 6 | **Frontmatter** | Missing `description`; a title that doesn't say what the page is about |
| 7 | **Cross-linking** | Orphan pages (in the sidebar, linked from nothing); no "how to read this site" ladder; asset pages that don't link to their format page |
| 8 | **Gallery data-drivenness** | Hand-maintained frame lists in a page or component; names invented rather than sourced; a manifest read with a hardcoded variant list |
| 9 | **Correctness & a11y** | Hardcoded colours instead of `--sl-color-*`; missing `image-rendering: pixelated`; interactive cards with no keyboard path or `aria-label`; broken asset URLs |
| 10 | **Source-of-truth statement** | Home page never says the site summarises `docs/<game>/` and that the raw notes win |

## Severity

- **High** — the site is *wrong or misleading*: a claim contradicting the raw
  notes, a broken/404 asset, a page presenting an open question as solved,
  committed placeholder text on a page a visitor lands on.
- **Medium** — the site is *incomplete*: solved format with no page, extracted
  asset never shown, no status page, missing `description` frontmatter,
  orphan page.
- **Low** — the site is *weaker than it should be*: hedged prose where a count
  exists, a thin section, a sidebar label that could carry meaning, a11y polish.

Rank High → Medium → Low; within a tier, rank by how many readers hit it (home
and overview pages before a deep format page).

## Verify before reporting

Every finding must be checkable. Before it goes in the report:

- Quote the offending line, or name the file that should exist and doesn't.
- For a "missing page" finding, name the section of `docs/<game>/` that supplies
  the material — if you can't, it isn't a finding, it's a wish.
- For a "wrong claim" finding, quote both the page and the raw note.
- Don't report the *absence of a thing the project never had*. A game with no
  DOS port doesn't need a comparison page.

## Report format

Open with two or three sentences: overall state, the single highest-value fix,
and roughly how much work the list represents. Then one table:

| # | Sev | File | Finding | Fix / exemplar |
|---|-----|------|---------|----------------|
| 1 | High | `src/content/docs/wime/index.mdx:5` | Ships the scaffold placeholder ("replace this content with a real overview") as the game's landing page | Rewrite as a splash home — model on crawl's `blackcrypt/index.mdx` |
| 2 | Med | — | No status page for any of the 5 games; `docs/wime/TODO.md` has open items | Add `wime/status.md` — model on crawl's `blackcrypt/status.md` |

Close with a short **suggested order of work** — usually: kill placeholders,
then add the status pages, then fill coverage gaps, then tighten prose.

If the site is in good shape, say so plainly and keep the list short. An audit
that manufactures findings to look thorough is worse than useless.
