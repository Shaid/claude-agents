# A manifest past ~10-20k entries makes the offline viewer unusable — one DOM node per row and one big fetch don't scale, and neither fix alone is enough

**When it bites:** a project's pipeline has matured to the point its
`manifest.json` crosses tens of thousands of entries (several asset types
extracted, or one type at real scale — texture-heavy/audio-heavy titles get
here fast), and the scaffold-standard offline viewer (`docs/viewer.md`'s
`tools/viewer/viewer.ts`) becomes slow enough to load or interact with that
it's reported as "takes ages" rather than a specific bug.

Confirmed on Drakengard 3 (PS3, `flower` project) once texture+mesh+audio
extraction all landed: 78,956-entry manifest, 21MB. Profiled directly
(Playwright + `performance.getEntriesByType('resource')` + wall-clock DOM
timing) before writing any fix — don't guess which of the two obvious
suspects is the real bottleneck, measure both:

- `manifest.json` fetch itself: only ~58ms transfer on localhost (network
  cost is real on a slow connection but wasn't the dominant term here).
- `renderList()` building one real `document.createElement` `.item` div per
  filtered entry, appended directly to the live DOM with no batching: 378ms
  **synchronous**, main-thread-blocking, for a single re-render (e.g.
  clicking a type filter or typing one search character).
- Combined wall time, page nav → interactive list: **2,740ms**, with
  **78,956 DOM nodes** created on the very first load.

**Both mechanisms need fixing, and they're independent — confirm this
before assuming one alone is sufficient.** Fetching less data doesn't fix
DOM cost (a still-huge filtered/category shard renders exactly as slowly),
and rendering fewer DOM nodes doesn't fix a large unconditional fetch on
every load. Tested each independently by toggling the other off:

1. **List virtualization** (only materialize `.item` DOM nodes for the
   currently-visible scroll window, via a fixed-row-height sizer div +
   an absolutely-positioned, `transform: translateY()`-shifted viewport
   div holding just the visible rows) fixed the DOM-cost term **on its
   own**, independent of fetch size — confirmed by temporarily removing
   the manifest-splitting feature entirely (simulating an unmigrated
   sibling project) and re-measuring: the full 78,956-entry
   `manifest.json` still fetched in full, but load-to-interactive dropped
   to 314ms and DOM node count to ~30, because rendering was virtualized
   regardless of how much data got fetched.
2. **Category-based lazy loading** (a tiny top-level index — categories'
   `id`/`displayName`/`count` only, a few KB — fetched instead of the full
   manifest on load; a category's own shard fetched only once the user
   picks it) fixed the fetch-size term. For a corpus with one dominant
   category (91% of this one), category-level splitting alone wasn't
   enough on its own (that category's own flat shard was still 22MB) — a
   further split by a natural sub-grouping (a `group` field, cheap since
   it's already computed per-entry) above a size threshold gave real
   sub-shards in the low single-digit MB, each independently fetchable.

**Net result, real measurement, not estimated:** 2,740ms → 194ms
page-load, 78,956 → 99 initial DOM nodes, and even the largest single
opt-in "load everything in this category" fetch (71,986 entries, 22MB)
rendered in 226ms with only ~23 DOM nodes live at once, because
virtualization doesn't care how large the underlying array is.

**Do this before it's reported as "slow"**, not after — the tell is
knowable in advance: `wc -c public/assets/<game>/<platform>/manifest.json`
crossing roughly 5-10MB (tens of thousands of entries) is the point past
which a flat-fetch-and-render-everything viewer starts costing multiple
seconds of dead time on every load. A fixed-row-height virtualized list is
cheap to build proactively; retrofitting it after the fact is no harder,
but there's no reason to wait for the complaint.
