# An injected click that dispatches nothing is a gating or timing problem, not an inert control

**When it bites:** driving a game's own 2D UI from a harness (scripted
`click x y` into an emulated mouse) to reach state no static trace can
reach — and a click produces no handler call at all, dispatches only
intermittently, or every click looks dead after one particular action.

"No dispatch" reads like proof the region holds no control, so the region
gets documented as dead and the records behind it as unreachable. Five
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
5. **Press shorter than the game's poll cadence** — the main loop samples
   the mouse once per pass, so a synthetic press held for fewer slices
   than one pass is seen or missed purely by *absolute phase*: the same
   script flips between dispatching and not depending on what ran before
   it. This is the cause that manufactures fake *findings* rather than
   fake absences — intermittent hits read as position- or hover-
   dependence, and the one coordinate that happened to land gets written
   up as "the only live spot" of a control that is live across its whole
   rectangle.

**Check / fix:** instrument the real indirect dispatch site (the
table-indirect `jsr (An)` / call-through) and log every (slot, handler)
pair, so "did anything dispatch" stops being inferred from screen
contents. Dump the live hit table *with* its mask/enable word, not just
its geometry. Wait generously after any page change, and prefer a settle
condition over a tuned slice count. Make **press length a harness
parameter** from the start (not just a separate held-press primitive), set
it comfortably longer than one main-loop pass, and before believing any
position-dependent result re-run it at a second press length and after a
deliberate phase shift (an extra `run N` before the click). Then bound the
control with **null controls taken from its own geometry**: the hit
rectangle's exclusive edges (`x2`/`y2`) and one pixel outside must *not*
dispatch while every interior value does — that turns "it works at this
one coordinate" into a rectangle with a verified boundary. Treat a
non-dispatching region as a question about state and timing until the
instrumented dispatcher itself says otherwise.

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

**Variant — cause 5 caught a fake finding in the same harness.** A later
pass had documented "slot 98 dispatches only at x=620, y=114", a hover-
state mystery with no explanation. It was entirely the default 40-slice
press falling between hit-test passes: five clicks at the same settle gave
0/5, and merely inserting a leading `run 200` flipped one dispatch to zero.
With press length exposed as a parameter, a 200-slice press gave 5/5, and
the slot proved live at 11/11 y values across its full declared rectangle
(x 576..658, y 107..120) with nothing dispatching at the exclusive edges
(x 658/660, y 106/120) — the geometry had been right in the table all
along. Lengths 150 and 400 also dispatched the failing phase, so the
diagnostic is "does changing press length change the answer", not a magic
number.

**History:** 2 recorded instances (`methanoid`; raw logs in
`_archive/silent-no-op-clicks-in-driven-ui.md`).
