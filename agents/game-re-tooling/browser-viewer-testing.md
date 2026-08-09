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
