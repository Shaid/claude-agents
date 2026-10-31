# An injected click that dispatches nothing is a gating or timing problem, not an inert control

**When it bites:** driving a game's own 2D UI from a harness (scripted
`click x y` into an emulated mouse) to reach state no static trace can
reach — and a click produces no handler call at all, or every click looks
dead after one particular action.

"No dispatch" reads like proof the region holds no control, so the region
gets documented as dead and the records behind it as unreachable. Four
independent causes, all live in a single game's UI:

1. **Masked hit tables** — a flag in the table's header means "record *i*
   is live only if bit *i* of a state word is set". The region exists, is
   hit-tested, and still dispatches nothing until the game sets the bit —
   while the very same table is fully live on another screen or later in
   the same session.
2. **Hover gating** — the press handler only dispatches once the
   hover/motion pass has filled its pending hit-key and slot words. Inject
   a move, let it run, *then* press; a press with no prior motion is
   discarded with no trace.
3. **Page not armed yet** — the new screen installs its table some way
   into its own setup, so a click sent too soon after the page opens is a
   no-op. A wait tuned to one observed run length then breaks silently
   when anything upstream changes the slice count.
4. **Modal loops needing a held press** — a handler that loops a
   tick/animation routine exits only if the button is *still* down after
   an iteration completes. A one-shot click can never leave it; a press
   held longer than one iteration can.

**Check / fix:** instrument the real indirect dispatch site (the
table-indirect `jsr (An)` / call-through) and log every (slot, handler)
pair, so "did anything dispatch" stops being inferred from screen
contents. Dump the live hit table *with* its mask/enable word, not just
its geometry. Wait generously after any page change, and prefer a settle
condition over a tuned slice count. Give the harness a held-press
primitive alongside click. Treat a non-dispatching region as a question
about state and timing until the instrumented dispatcher itself says
otherwise.

**Canonical example:** Deuteros (Amiga, `methanoid`): the click path at
`$222CE` dispatches only when the hover test has filled `$222A0`/`$222AC`;
the cockpit table `$21990` carries mask word `$222B4 = $83FD`, leaving the
"Land" slot dead until the vessel is orbiting; the Advance-Time handler
`$23F6E` loops its tick routine and needed a held press (`hold 200 100
15000`) where `click` never returned from it; and the Space Dock's build
slot needed roughly 15,000 further slices after the page opened before its
table answered (an 8,000-slice wait was a silent no-op). Fixing all four
turned "clicks are dead after Advance Time" plus several "dead region"
notes into 26 newly named UI slots and a complete build to launch to
flight trace.

**History:** 1 recorded instance (`methanoid`).
