# A "wrong scene for one tile" bug report can mean the trigger context is missing, not that the decode/dispatch table is wrong

**When it bites:** a user-reported bad instance of an already-confirmed
decode/dispatch mechanism (a wrong sprite/scene/sound picked for a specific
input) comes from a UI feature a *later* reimplementation session added on
top of an earlier, code-traced original mechanism — especially when that
mechanism's original code path is itself gated on some entity/state
condition ("is X actually here") that the new UI feature has no equivalent
check for.

## What happened

A prior middilgard (Spirit of Excalibur, Amiga) session traced and
reimplemented `_OpenScene`'s wilderness/terrain-backdrop dispatch: a 13-way
terrain category lookup into a 39-entry (13×3-variant) table of authored
`SCEN` resources, wired into a new "click any map tile to preview its
terrain backdrop" viewer feature. Both the terrain-category table and the
scene-dispatch table were independently confirmed byte-exact against the
executable. A later bug report said clicking an ordinary forest tile showed
a scene full of soldiers — read at first as "which one of the 28 scenes is
the wrong one for forest."

Rendering the *entire* 28-scene corpus (not just the forest case) instead of
debugging the forest lookup found 26 of 28 backdrops bake a standing troop
formation + banner directly into their authored object list — soldiers
weren't an outlier, they were the overwhelming majority. That ratio is the
tell: a real off-by-one/wrong-slot bug produces one or a few bad outputs
against a mostly-correct population; this was the *opposite* shape. Tracing
the original code one level further up (not the dispatch branch itself, but
what calls into it) found `_OpenScene`'s wilderness branch reads its (x, y)
from an *existing force's* position (`_aForces[i]`), with `i` set by
`_DoMobilIcon` — the handler for clicking a moving army icon on the
strategic map, never a bare unoccupied tile. The mechanism is "show the
force standing on this terrain," always with troops, because the original
game never reaches it any other way. The new UI feature faithfully ported
the *dispatch table* but not the *trigger gate*, so it showed the force's
own depiction for every tile regardless of whether anything occupied it.

## The fix

When a single reported bad instance of an already-confirmed decode/dispatch
table, applied by a *newly-added* UI/feature layer, turns out on rendering
the *whole* corpus to be the majority behavior rather than a true outlier,
stop debugging the table and go trace the **original code's caller
context** instead: what real user action/game state actually reaches this
branch in the source game, not just what the branch does with its inputs.
A mechanism that's unconditionally entity- or state-gated in the original
will look, from pure data-flow inside the branch, exactly like an
unconditional one — the gate only shows up one level up the call graph, at
the site that decides *whether* to take the branch at all. This is a
different failure class from a wrong table/category mapping (which a
rendered corpus would show as a few plausible-but-wrong outputs, not "the
special content is everywhere") and from `traced-calling-convention-
unverified-against-corpus.md` (a static trace vs. real data mismatch) — here
both the trace and the data were right, and the bug was a *newer* feature
applying an old mechanism outside the scope its original trigger context
implied. The fix is not to reject the reimplementation (the table is still
correct and the resource still exists) but to gate or filter its ungated
consumer to match the original invocation context, while leaving the
resource itself fully intact and browsable for a future feature that
implements the real gate.
