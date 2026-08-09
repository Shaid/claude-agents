# Components and galleries

When a plain `![atlas](…)` is enough, use one. Reach for a component when the
reader needs to see **individual frames** with **real names**, when there are
enough of them to need search, or when the asset only makes sense in motion.

Exemplars: `~/Development/crawl/www/src/components/` (`SpriteGallery`,
`MonsterZoomGallery`, `EffectAnimGallery`, `DungeonViewCycle`) and
`~/Development/middilgard/www/src/components/` (`SpriteGallery`, `Lightbox`,
`SceneGallery`, `FrmlCharacterGallery`, `MapExplorer`, `GameCardGrid`).

---

## The core rule: read the pipeline's manifests at build time

Astro component frontmatter runs at build time in Node, so a component can read
the extraction pipeline's own JSON and derive everything from it. **Never
hand-maintain a frame list in a page or component.** If the extraction changes,
the gallery must change with it — silently, with no edit.

```astro
---
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Prefer the repo's live extraction output; fall back to this site's own
// committed mirror (which is all CI ever has — it never gets the original
// copyrighted game files).
const repoAssetRoot = resolve(process.cwd(), '..', 'public', 'assets', assetPath);
const assetRoot = existsSync(repoAssetRoot)
  ? repoAssetRoot
  : resolve(process.cwd(), 'public', 'assets', assetPath);
const manifest = JSON.parse(readFileSync(resolve(assetRoot, `${name}.json`), 'utf8'));
---
```

**Invert that preference for site-generated assets.** `DungeonViewCycle` prefers
the *local* root, because the rendered views are written by the site's own
`scripts/render_dungeon_views.ts` straight into `www/public/` and never exist at
the repo root. Getting this backwards yields a stale or missing asset with no
error. Both crawl components carry a comment explaining which way round they go
and why — do the same.

**Names come from real extracted name data**, not from the component:
`data/monster-names.json`, `data/item-names.json`, a sidecar written by the
render script (`dungeon-<tileset>-views.json`). Which variants exist is read,
not assumed — bcdfy genuinely has no alcove art, and a hardcoded variant list
would have invented one.

---

## The scaffold `SpriteGallery` contract

`create-seer-website` ships a game-agnostic `SpriteGallery.astro`. Prefer it,
and push game knowledge into the calling page:

```mdx
import SpriteGallery from '../../../components/SpriteGallery.astro';

<SpriteGallery
  manifest="items"
  assetPath="wime/amiga/sprites"
  label="item"
  hoverPairs={{ item010: 'item011' }}
  clickChains={{ item020: ['item020', 'item021', 'item022'] }}
  labels={new Map([['item010', { visible: 'Fire Wand', hover: 'Fire Wand (lit)' }]])}
/>
```

| Prop | Meaning |
|---|---|
| `manifest` | Manifest basename; reads `<assetPath>/<manifest>.json` + `.png` |
| `assetPath` | Full directory under `public/assets/` — the component has no opinion on your layout |
| `label` | Singular noun for the filter UI ("Filter items", "Search items") |
| `hoverPairs` | `frame → frame`; one card, swaps to the second on hover |
| `clickChains` | `frame → [frames]`; one card, advances per click, latches on the last |
| `labels` | `Map<frameName, { visible, hover? }>` built **by the page** from whatever name data exists |

Crawl's fork instead reads `monster-names.json` / `item-names.json` itself and
hardcodes its pair/chain tables. That's the right call *there* (the tables carry
paragraphs of RE evidence), but for new work prefer passing data in — fork only
when the behaviour is genuinely game-specific and the evidence needs to live
next to it.

---

## Interaction patterns worth copying

- **Hover-swap for two-state art.** Dim/activated icon pairs render as one card
  with a small badge (`title="Hover to reveal an alternate state"`) rather than
  two confusingly-unlabelled cards. Implemented as a `background-position` swap
  on the same sheet, not a second image.
- **Click-to-cycle for ladders.** Latch on the last frame for one-way sequences
  (a water skin's full/half/empty, a split gauntlet pair); **loop** for
  camera-style cycles with no natural endpoint (floor items' near/mid/far view
  depths). `data-click-loop` distinguishes them.
- **Hover to pause** for anything animating, and say so in the page prose.
- **Search/filter toolbar** with a live frame count (`{frames.length} frames`);
  filter by both display name and raw frame name.
- **Uniform card slot sizing.** Compute one slot size across the manifest's
  visible frames so captions align across a grid row — otherwise a manifest with
  varying frame sizes gets a ragged caption line.
- **A representative still.** For animated cards, pick the largest-area frame
  for the pre-hydration / reduced-motion view; frame 0 is often the smallest
  zoom step and misrepresents the creature.
- **`<Lightbox />` for click-to-enlarge.** Drop it **once per page** (single
  modal, fixed id), then add `data-lightbox` (+ optional `data-lightbox-label`)
  to any `<img>` or background-cropped element. Event-delegated, so it works for
  cards shown/hidden by a search filter.
- **Undocumented easter eggs are fine** where they're discoverable and harmless
  — crawl's water-skin click chain is deliberately not documented in the UI.
  Keep them out of load-bearing paths.

## Every non-obvious grouping carries its evidence in a comment

Crawl's `SpriteGallery.astro` explains, in source, why 16 icon pairs collapse to
one card ("same weapon silhouette, differing only by an added glow/particle
overlay… no placed map record ever references it directly — it's a second render
state for the same object, not a separate item") and how the gauntlet/bracer
triples were confirmed by eye, frame index by frame index.

Do this. A grouping is a *claim about the game data*, and the next person needs
to know whether it was confirmed or guessed.

---

## Correctness and accessibility checklist

- `image-rendering: pixelated` on every scaled sprite layer. Integer-ish scale
  factors (`Math.min(3, 160 / w, 160 / h)`) keep pixel art honest.
- **Starlight theme tokens only** — `var(--sl-color-gray-3)`, `--sl-color-gray-5`,
  `--sl-color-gray-6`, `--sl-color-accent`. Hardcoded hex breaks dark mode.
- Background-cropped frames need `role="img"` + `aria-label={frameLabel}`; they
  are not `<img>` and carry no implicit semantics.
- Interactive cards need `tabindex="0"`, an Enter/Space handler alongside the
  click handler (`event.preventDefault()` on Space), and a `:focus-visible`
  outline with `outline-offset`.
- Give every card a stable caption line: display name, then a `<small>` with the
  index and real pixel dimensions (`#042 · 24×24`). The dimensions are data.
- Scoped `<style>` in the component; no global selectors.
- Grids: `grid-template-columns: repeat(auto-fill, minmax(9rem, 1fr))` and
  `height: 100%` on the card, so rows stay even.

---

## Traps

**A manifest without top-level `width`/`height` silently renders the whole
atlas in every card.** `SpriteGallery` computes CSS `background-size` from them;
missing, it evaluates to the literal string `"NaNpx NaNpx"` — an invalid value
the browser ignores, falling back to the sheet's native size. No console error.
If every card looks like the full atlas tiled small, check this first, and fix
it in the *pipeline* (add both fields to the manifest builder), not in the
component. (Real case: `wime`'s `icons.json` carried `iconSize`/`columns`/`rows`
but no `width`/`height`.)

**MDX: never put a bare comment line immediately before an object- or
array-literal `export const`.** `export const A = {x:1};\n\n// comment\nexport
const B = {y:2};` fails to parse (`Could not parse expression with acorn`).
Primitive-valued exports are unaffected; `//` vs `/* */` makes no difference.
Fix: move the comment inline on the opening-bracket line, put further lines
*inside* the array, or fold the explanation into surrounding Markdown prose.
Astro reports only `line:col` with **no filename** — and on a multi-game site
the reported position drifts between builds as sibling files change. Bisect with
`@mdx-js/mdx` directly instead, run from inside `www/`:

```js
import { compile } from '@mdx-js/mdx';
compile(readFileSync(path, 'utf8'), { jsx: true }); // reports e.place/e.line/e.column
```

**A port collision looks exactly like a broken-asset bug.** If another
`astro dev`/`preview` already holds the default port, yours silently binds the
next one up (logging "Port XXXX is in use, trying another one…" to its own log)
— `curl`/browser traffic aimed at the default port then hits the *other*
server's content. Before debugging "my images 404", check `ps aux | grep astro`
and read your own command's startup log for the port it actually bound.

**Build-time `readFileSync` fails the build, which is correct.** Don't wrap
manifest reads in a try/catch that renders an empty gallery — a missing manifest
means the asset pipeline didn't run, and the build should say so loudly.
