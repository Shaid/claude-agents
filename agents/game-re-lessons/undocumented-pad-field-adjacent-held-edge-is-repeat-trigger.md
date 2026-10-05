# An undocumented pad-state word next to a confirmed held/edge pair is usually the auto-repeat trigger, not dead data

**When it bites:** an already-solved digital-pad/controller polling system
has a confirmed "held" (level-triggered) mask and a confirmed "edge"/"newly
pressed" mask, and a THIRD sibling word or byte in the same per-pad record
sits documented as "unknown"/"not traced"/"unexplained" rather than actively
hunted — especially if it has stood that way across many sessions because
nothing forced anyone to revisit it (`named-blocker-may-be-an-untried-next-
step.md` applies here too: it's a concretely-named, cheap, never-executed
step).

**What happened:** Valkyrie Profile 1 (PSX)'s `dungeon-field-mechanics.md`
named `0x8007e620` "held" and `0x8007e622` "edge/newly pressed" on its very
first pass (2026-09-17), and left the very next halfword, `0x8007e624`, as
"third mask (release/repeat, not traced)" — flagged but never hunted, for 22
rounds. Tracing its producer found a fifth, previously-unnamed resident pad-
library function whose body is exactly the standard press-then-repeat idiom:
a per-port saturating "how many consecutive polls has this exact input been
held steady" counter, compared against a small fixed threshold constant; below
the threshold it returns the SAME array the confirmed "edge" reader returns,
and once the counter reaches the threshold it switches to returning the raw
per-poll input state instead (which then fires continuously while held,
because the edge array only ever pulses once per transition and would
otherwise go silent forever). Two independent consumers — a menu-cursor
direction dispatcher, and a script-VM pad-state-export routine that copies it
into the same struct as held/edge — confirmed it as live, consumed state, not
incidental engine plumbing.

**The generalizable signature, worth checking before reaching for a full
disassembly trace:** a "third field, sibling of held/edge, purpose unclear"
is a strong candidate for a key-repeat trigger whenever its producer
function's shape is "read a small per-port counter, read a small fixed
threshold constant, compare, branch to one of two DIFFERENT sibling arrays" —
landing on the SAME array the edge-reader uses in one branch, and a
raw/held-adjacent array in the other, is close to a fingerprint. This
generalizes well past PSX/VP1: nearly every console-era game with menu/list
navigation implements the identical press → delay → repeat UI convention, so
an unexplained sibling of held/edge in ANY platform's pad-polling struct is
worth checking against this shape first, rather than filed as "engine-
internal, no semantic role."

**Fix:** when a held/edge pair is confirmed and an adjacent field is still
unnamed, trace its own PRODUCER function's body first (not its consumers,
and not a semantic guess from the field's name) — the counter-vs-threshold-
vs-two-arrays shape is diagnostic on its own. Once found, a corpus-wide
search for the field's own READERS (not another guess) is what turns "not
traced" into a confirmed key-repeat trigger with real, live consumers.
