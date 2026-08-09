# A GTE opcode census showing only point-projection (`RTPS`, 0 `RTPT`/`NCLIP`/`AVSZ`) is not proof "no real 3D effect" — it can be a billboard/particle renderer

**When it bites:** a PSX (or similar sprite+GTE-era) GTE/COP2 opcode census
finds only single-vertex projection instructions (`RTPS`) with zero
polygon-shaped instructions (`RTPT`, `NCLIP`, `AVSZ3`/`AVSZ4`, `MVMVA`) in a
region you expect to draw visual effects, and the conclusion on the table is
"this is just placing 2D sprites/UI anchors in 3D-projected space, not real
3D content" or similar — especially when that conclusion is used to redirect
the search to a *different* code region/overlay in pursuit of "real"
geometry. Also when it bites: a real billboard/particle renderer has just
been confirmed via data-flow tracing, and a plausible semantic label (which
game system it belongs to) is about to be written up on the strength of the
render path alone, without tracing its looked-up index into that index's
*other* consumers.

## The trap

Point-projection-only GTE usage looks, by shape alone, like the weakest
possible "3D": no triangles, no clipping, no face-averaged depth. It's
tempting to read that shape as "trivial — just used to place a flat sprite
somewhere," dismiss it as UI/anchor placement, and go hunting elsewhere for
"the real" 3D geometry (a polygon mesh, a particle vertex buffer). This is a
domain-knowledge error, not a search-completeness error: **RTPS-only GTE
usage is exactly what a billboarded sprite/particle system looks like at the
opcode level**, and billboarding — projecting a sprite's anchor point through
real 3D transforms, then scaling/positioning the flat quad using the GTE's
own perspective-correction output — is a completely standard, first-class
PS1-era 3D visual-effects technique, not a degenerate or coincidental use of
the hardware.

Confirmed on Valkyrie Profile (PSX): the battle overlay's 28 confirmed `RTPS`
sites (0 `RTPT`/`NCLIP`/`AVSZ3`) were first documented as "the battle system
uses the shared matrix library to place 2D sprites and effect anchors in a
3D-projected space; it has no mesh buffer of its own" — a reasonable-sounding
but wrong conclusion that stood as a "confirmed negative" until the user
(who had played the actual game) reported that spell effects, even a basic
fire spell, are genuinely rendered in 3D. Tracing the actual data flow
through one `RTPS` cluster end to end found: a live entity's dynamic world
position feeding a world-to-screen projection; a per-instance resource
(texture) and a small 4-entry colour palette (indexed by ID, modulated by a
live fade timer) selecting what to draw; the `RTPS` itself saving both the
projected screen coordinate (`SXY2`) *and* the GTE's perspective-correction
factor (`IR0`) plus a depth value (`SZ`-derived) — the textbook recipe for a
perspective-scaled, depth-sorted billboard corner; and finally the resource
pointer merged into a real GPU primitive tag and queued for hardware
rendering, paired with an object-spawn trigger. Every opcode-shape fact in
the original census was correct (28 RTPS, 0 of anything polygon-shaped) —
the inference that this shape alone proves "not real 3D content" was wrong,
and the *mechanism* conclusion (real billboard/particle rendering exists)
held up under a second, independent pass.

**But the specific semantic label attached to that real mechanism was then
also wrong, and needed its own separate verification.** The natural next
guess — "4-entry colour palette + per-instance resource lookup, found while
chasing a user's report about spell effects" → "this must be the elemental
spell-effect renderer, and the 4 colours are elements (fire/ice/lightning/
poison)" — read cleanly and was *plausible*, but was never actually checked
against its own numeric consumers. A follow-up pass found the colour index's
real numeric consumer: a `{80, 60, 40, 0}` diminishing-returns table feeding
a 0-100 "combo gauge" field, whose 4th entry is exactly zero — the signature
of a **capped 4-step chain counter**, not an open element-id space. The
renderer was real; it turned out to draw Valkyrie Profile's "Purify Weird
Soul" chained special-attack effect (a combo mechanic capped at 4 chained
hits, one per party member), not a per-elemental-spell effect. The confirmed
*mechanism* (dynamic 3D position → per-instance resource/colour lookup →
depth-sorted perspective-correct billboard → GPU primitive) is a completely
generic template that both readings fit equally well from the render code
alone — resolving which one it actually is required following the looked-up
index into *its own* other consumer (here, the gauge/gain table), not just
confirming that a real renderer existed.

## The rule

Don't let an opcode/instruction-shape classification alone settle whether a
GTE (or equivalent fixed-function 3D-transform hardware) usage site is "real"
content versus "just placement." Trace what happens on both sides of the
transform:

- **Before**: is the input vertex a per-frame-varying value read from a live
  entity/state struct (dynamic), or a compile-time constant / fixed screen
  position (static)? Only the latter supports "this is just UI."
- **After**: which GTE result registers does the surrounding code actually
  save? Saving only the screen XY suggests placement; saving `IR0`
  (perspective scale) and a depth/Z value alongside it is the specific
  signature of a scaled, depth-sorted draw — i.e. a genuine visual element,
  not a placement anchor. Then follow that saved data forward: does it reach
  a GPU primitive submission call, and is a per-instance colour/texture
  resource selected by some ID before that submission? If yes, this is a
  real renderer, however few polygon-only opcodes it uses.

A point-projection-only shape is consistent with *either* reading — it is
evidence for neither on its own. Resolve it by data flow, not by opcode
census alone, especially before writing up a "confirmed negative" that a
user's first-hand report of the game directly contradicts. When a user (or
any oracle with direct experience of the shipped game) corrects a documented
negative, treat that as strong signal to re-open the trace, not just
re-verify the original scan.

**Then do the same discipline a second time for *what specific thing* the
now-confirmed renderer draws.** Finding a real mechanism that matches the
user's report in *kind* ("yes, this really is 3D-projected, positioned,
coloured content") is not the same as confirming it matches in *identity*
("and this specific instance is the thing they described"). A plausible,
context-fitting label for a looked-up index (an "elemental colour ID"
found while investigating a spell-effect report) is a hypothesis, not a
finding, until you trace that same index into its *other* consumers —
not just the render path that led you there. A capped/diminishing-returns
table (explicit small max index, a terminal zero/sentinel entry) at one of
those other consumers is a strong tell that the index is a bounded game
mechanic counter (combo chain, hit count, upgrade tier), not an open
content-selection id — check for one before finalizing the semantic label.
