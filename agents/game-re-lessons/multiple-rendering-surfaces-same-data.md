# A bug report about "the page"/"the render" may name a different consumer than the one you know best

**When it bites:** a task describes a rendering bug in vague terms ("our X
renders are incorrect", "the Y page is tiny/static") in a seer-framework
project that has grown *more than one* consumer of the same extracted
assets — the live game engine (`src/engine/`), the interactive offline asset
browser (`tools/viewer/`), and (increasingly common as these projects mature)
a generated static docs/gallery site (a `www/` Astro+Starlight tree, or
similar) that independently renders `manifest.json`/`icons.json`/etc. through
its own component layer.

A real session spent a full investigation pass — reading `icon-mapping.ts`,
`EntityManager.ts`, `tools/viewer/viewer.ts`, two large format docs, then
launching the live game via Vite, driving it with Playwright, and cropping
screenshots of the strategic map — on the assumption that "our strategic icon
renders" and "the FRML page" meant the live engine and its interactive viewer,
because those were the most familiar, most-recently-touched surfaces. Both
turned out to already be correct (a prior commit had fixed the engine-side
icon mapping). The actual target was a `www/` static docs site added by a
*different, concurrent* agent session in the same repo minutes earlier — its
existence was visible in `git log` the whole time, but nothing prompted a
check for it before diving into the familiar code path.

**The fix:** before deep-diving into the most obvious/familiar rendering
surface, spend one cheap step confirming *which* surface a vague bug report
means, whenever a project could plausibly have more than one consumer of the
same data:

- `git log --oneline -20` (and `git status`) to see if another surface was
  added or touched recently — a concurrent session's new pages are exactly
  the kind of thing a stale mental model misses.
- Grep the bug report's exact nouns ("icon gallery", "FRML page", "strategic
  map") across `docs/`, page titles, and route/slug names — a static site's
  page title or an `.mdx` filename will often match a user's casual phrasing
  more literally than an internal function/class name would.
- If genuinely ambiguous and cheap to check both, do a quick empirical look
  at each candidate surface before committing to a deep read of any one's
  source.

Time lost this way isn't wasted if the "wrong" surface really did have a
latent bug (verify, don't assume, either way) — but confirm the *target*
matches the report before investing in a full read-and-trace pass.
