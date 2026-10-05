# A dimension, length, or count constant found anywhere is a join key against every *other* open item — including already-decoded fields' own observed value ranges

**When it bites:** a trace, a subagent report, or a disassembly pass yields a
new concrete size — a grid `(width, height)`, a read length, a record stride,
a buffer allocation, or a resource's real (non-padding) element count — and
you're about to file it under the item you were working on and move on.
Also bites right before escalating a stalled item while any sibling trace on
the same binary is still running. The join key isn't limited to matching
against other *sizes*, either: a newly-confirmed element COUNT (e.g. "this
table has exactly 93 real records") is just as productive checked against
the observed VALUE RANGE of an already-decoded, unrelated opcode/field
parameter elsewhere in the same project — if some already-known byte-sized
field's real corpus-wide value range happens to be `[0, 92]` with zero
values above it, that's likely the selector for the new table, found for
free with no new search at all. Confirmed on Final Fantasy VII (PSX field
BGM, `siren` project): a newly-decoded global instrument bank's real record
count (93, indices 0-92) was checked against every already-decoded v1.x
opcode parameter's own real value range from a wholly earlier, unrelated
pass — `PROGCHANGE`'s param byte turned out to fall in exactly `[0, 92]`
across 24,487 real occurrences with zero exceptions, settling instrument
selection instantly without any new disassembly or opcode-search work.

Sizes are the cheapest cross-item join key in reverse engineering. They are
small integers you already know for every open item (file lengths, content
lengths after padding strip, byte counts that resisted factorization), and
comparing a newly-found constant against all of them is a lookup, not an
investigation. Formats are opaque; **their dimensions are not**, and two
things that share an exact size usually share a reason.

Confirmed on Phantasie III (Amiga, `nicodemus` project). `D/pln1`/`pln2`
(81 content bytes) and `pln4` (496) had defeated five genuinely distinct
approaches across multiple sessions and had just been escalated to
`re-codebreaker` as an unsolved encoding. In parallel, a subagent tracing an
entirely unrelated question — where the *overworld* map lives and how the
engine dispatches on it — mentioned in passing that the map-switch routine
also installs two other map geometries: "a 9×8 castle-interior grid and a
31×15 Netherworld grid." Those `(width, maxY)` pairs are 9×9 and 31×16
cells. **81 and 496.** The match was immediate and exact, the loader's own
read immediates (`#$51`, `#$1F0`) confirmed it byte-for-byte within minutes,
and the escalation was stood down before it reported. Nothing about the
overworld trace was aimed at the PLN files; the constant simply had to be
noticed against the other item's known numbers.

## What to do

- **Keep the open items' sizes to hand.** `docs/<game>/TODO.md` rows plus a
  one-line `ls -l` of the undecoded files is enough. The check is "does this
  new constant, or a small product/factor of it, equal any of those?"
- **Check products, not just the raw number.** A grid constant arrives as
  `(w, h)` or `(w, maxY)` — an off-by-one on the `max` convention is normal.
  Try `w*h`, `w*(h+1)`, `(w+1)*h` before deciding it doesn't match.
- **Do this for allocation sizes especially.** A `malloc`/`pea` immediate is
  an exact payload size the game itself committed to, and it is the single
  most reusable number a trace produces.

## The orchestration corollary

**Don't escalate an item while a sibling trace on a related subsystem of the
same binary is still running.** An escalation is expensive and starts without
your context; a running trace on adjacent code is producing constants for
free and may hand you the answer as a byproduct. Wait for in-flight sibling
work to land, re-check its constants against your stalled item, and only then
decide whether the brief is still needed. (If you have already escalated and
the item resolves, stand the specialist down explicitly rather than letting
it burn to completion — and fold back anything it volunteered, after
verifying it like any other claim.)

Related: `working-tree-may-already-solve-a-docs-open-item.md` (check what's
already there before starting) is the same instinct pointed at the repo
rather than at concurrent work.
