# Live-verifying a seer-framework browser viewer/engine (Playwright)

Applies whenever a task needs to confirm a fix or feature by actually
running a seer project's dev server and driving its browser UI (the live
engine, or the offline `tools/viewer` asset browser) — not just unit tests.

## No Playwright MCP tool? Check the session scratchpad first

Most environments running this agent do **not** have a `playwright` MCP
server registered, and the target project itself frequently has no
`playwright`/`@playwright/test` dependency at the repo root either (it's an
asset-pipeline project, not a web-app-with-e2e-tests project) — so
`npx playwright ...` fails with a bare `MODULE_NOT_FOUND`/prompt-to-install
in a non-interactive shell.

Before reaching for a fresh `npm install playwright` (slow — downloads a
full Chromium), check whether a **prior session in this same account** has
already installed it into a scratchpad directory:

```
find / -maxdepth 8 -iname playwright -path "*node_modules*" 2>/dev/null | grep -v /proc/
```

Session scratchpads (`/tmp/claude-*/.../scratchpad/node_modules/playwright`)
routinely turn up from earlier tasks in *other* projects too — any of them
works, since `playwright` itself is project-agnostic; just `node -e
"require('playwright').chromium.launch()..."` from a script placed anywhere,
no need for it to live in the target project's own `node_modules`. This is
the general `shared-scratchpad-has-sibling-agent-tooling.md` pattern applied
to a plain npm dependency, not just a bespoke disassembler/parser.

## Driving a custom pan/zoom canvas (map/scene viewers)

Seer viewers commonly implement their own mouse-driven pan/zoom canvas (a
map or scene viewer) with private `zoom`/`offsetX`/`offsetY` state and a
`clientX/clientY → tile` conversion buried in a component class — not a
DOM element with meaningful coordinates you can query directly. Two traps
specific to this shape:

1. **Don't try to hand-derive exact click coordinates from the component's
   own fit/zoom formula.** It's fragile (depends on the live container's
   `clientWidth`/`clientHeight` at the moment the view was fit, which you'd
   have to replicate exactly) for no real benefit. Instead: take a
   screenshot of the rendered canvas first, visually identify the target
   region from the actual pixels (a distinctive terrain/tile color cluster,
   a labeled landmark), then click an approximate on-screen point in that
   region and read the *resolved* result back from the app's own live state
   (a title/meta text field showing the tile coordinates or category it
   picked) rather than assuming your click landed exactly where intended.
   Iterate/screenshot again if the readback doesn't match what you meant to
   test.
2. **Re-navigate to the interactive canvas before every single click**, not
   just once at the start of a loop. Selecting a result (a scene, a
   resource) commonly replaces or hides the map/canvas element entirely to
   show the result's own view — so a second blind `page.mouse.click(x, y)`
   at the same screen coordinates after the first click silently lands on
   whatever replaced it (or nothing interactive at all) and *appears* to
   produce the previous result again, since nothing actually re-ran. If a
   test loop shows the exact same "resolved" output for several different
   click coordinates in a row, this is the first thing to suspect — add an
   explicit "switch back to the source tab/filter and re-select the base
   resource" step before each click rather than assuming state persists.

## `hasText` on a `<select><option>` is substring match, not exact match

`page.locator('#some-select option', { hasText: 'Cat' }).first()` matches
**any** option whose text *contains* `'Cat'` — including `'Catherine'` — and
silently returns whichever one sorts first in the DOM, not necessarily the
one you meant. Confirmed losing real time on this: a test meant to select
the character named exactly "Cat" in a dropdown actually selected
"Catherine" (which happened to appear earlier in the option list), and the
mistake was invisible until the two characters' underlying data was
compared directly — both looked like plausible, successfully-selected
results.

**Fix:** for an exact-name selection, resolve the exact `<option value>`
first — loop `await locator('option').all()`, compare
`(await o.textContent()).trim() === exactName`, and use that `value` with
`selectOption()` — rather than trusting a `hasText` substring locator's
`.first()` to be the intended match. This especially bites any game's
character/item/entity name list, where short-prefix collisions ("Cat" /
"Catherine", "Al" / "Alois" / "Alois Jr.") are common.

## A just-restarted Vite dev server can produce a stale-looking DOM snapshot that mimics a real app bug

Vite's cold-start dependency pre-bundling ("Re-optimizing dependencies")
can trigger a live page reload that races with a test's own navigation and
timing. A single `waitForTimeout(N)` followed by one DOM read can catch the
page mid-reload: text fields populated by an async render (a title, a
computed stat count) can show fully correct, final values while a sibling
element that same render also touched (e.g. a canvas/viewport container)
still shows its *pre-render* placeholder — looking exactly like a real
"some code path updates one element but not the other" bug. Confirmed:
this reproduced consistently against a just-restarted dev server (multiple
runs, several seconds of wait each) and vanished completely once the exact
same test ran against an already-warm server that had served at least one
prior successful request.

**Fix:** after any `npx vite --host &`-style (re)start, do a throwaway
first navigation and let it fully settle (or explicitly wait for the
`[vite] connected` websocket message) before running the real test
sequence — don't trust the very first navigation against a freshly
(re)started dev server. When in doubt, replace one fixed
`waitForTimeout` + single DOM read with a short polling loop (sample every
~500ms, check the condition you actually care about) so a transient
mid-reload snapshot can't be mistaken for final state, and confirm with an
actual screenshot (not just text-content assertions) before concluding a
render is broken.
