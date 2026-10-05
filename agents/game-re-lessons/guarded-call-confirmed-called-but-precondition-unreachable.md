# "Confirmed genuinely called" and "this dynamic effect can never happen" can both be true at once

**When it bites:** a static census (every `jsr`/`call` to a resource-load or
similar function, filtered by literal argument) finds a real, non-zero
caller for some index/id — "confirmed genuinely called" — but a separate
dynamic/data trace shows that call's effect (a name lookup, a file read)
can never succeed given the real on-disk data. Before writing this up as an
open contradiction or escalating it, check whether the call itself sits
behind a **guard condition** (an index bound, a threshold compare, a value
only produced by some upstream formula) that no reachable caller can ever
actually satisfy.

This is a distinct category from the already-common "zero xrefs, purely
dead descriptor-table entry" pattern (`CAP_SPR.PAK`-style: a resource named
in a descriptor table with *no* call site anywhere). Here the call site is
real, the function it calls is real and correctly decoded, and a naive
census correctly reports it as "called" — but it never actually fires
during play because its own precondition is unreachable. Both the static
finding ("called") and the dynamic finding ("would fail") are correct and
non-contradictory; the resolution is proving the precondition is
unreachable, not re-litigating either finding.

Confirmed on PowerMonger (Amiga): `LoadResource(7)` (`BITMAP.PAK`) had one
real call site inside a mode-dispatch function, itself guarded by
`walklen < 0x100` — true for exactly one MAPDATA record (#195) out of 196.
A disk-directory name-lookup trace showed neither shipped disk's directory
has an entry matching `BITMAP.PAK` (a genuine miss, confirmed down to a
`clr; retry` infinite loop on miss). Resolving this required proving
record #195 itself can never be *selected*: the level-select UI's
click-to-scenario-index formula (`row*13+col`) is bounds-derived from the
click handler's own coordinate range checks to a 15x13=195-cell grid
(indices 0-194), leaving index 195 permanently unaddressable — corroborated
by **four independent lines of evidence converging on the same bound**: the
click handler's own edge-adjacency special-casing (`row==14`, `col==12`),
an unrelated second routine (a territory-marker renderer) hardcoding the
identical `15x13` loop count from scratch, an independently-clamped scroll
offset whose maximum arithmetically implies the same 15-row content height,
and the game's own "is this the last kingdom" endgame check comparing
against index 194 (not 195). A parallel random-map generation path was also
checked and shown to have its own walklen floor (via every writer of its
override global) always above the threshold. Only after establishing *every*
writer of the relevant globals, and *every* caller of the guarding function,
were provably enumerated (not sampled) did the "unreachable" conclusion
become solid — a single un-checked writer/caller would have left the
"confirmed genuinely called, but should be dead" tension unresolved.

**The generalizable technique:** when a census confirms a call site exists
but its dynamic effect looks impossible, don't stop at "must be a bug" or
leave it as an open mystery — exhaustively enumerate every *writer* of every
global feeding the guard condition, and every *caller* of the guarding
function, the same way you'd enumerate callers of a resource-load function.
Look for independent corroborating evidence for any derived bound (a second,
unrelated consumer of the same limit; an arithmetic identity between a
clamp constant and the bound; an explicit "last valid index" check
elsewhere) rather than accepting a single derivation. If every path is
enumerated and all agree the guard can never trigger, the contradiction
dissolves without needing to determine what garbage would appear at the
target address if the unreachable call somehow did fire.

See `~/Development/powermonger/docs/powermonger/amiga/runprog-code.md`'s
"`LoadResource(7)`'s name-lookup miss — resolved" section for the full
byte-level trace.
