# A dimension, length, or count constant found anywhere is a join key against every *other* open item — including already-decoded fields' own observed value ranges

**When it bites:** a trace, subagent report, or disassembly pass yields a new concrete size — grid `(w, h)`, read length, stride, allocation, or a table's real record count — and you are about to file it under the current item and move on. Also: right before escalating a stalled item while a sibling trace on the same binary is still running.

Sizes are the cheapest cross-item join key in reverse engineering. Formats are opaque; **their dimensions are not**, and two things that share an exact size usually share a reason. Checking a new constant against every open item is a lookup, not an investigation.

## What to do

- **Keep the open items' sizes to hand.** `docs/<game>/TODO.md` rows plus an `ls -l` of the undecoded files is enough. Ask: does this constant, or a small product/factor of it, equal any of those?
- **Check products, not just the raw number.** Grids arrive as `(w, h)` or `(w, maxY)`; try `w*h`, `w*(h+1)`, `(w+1)*h`.
- **Allocation sizes especially.** A `malloc`/`pea` immediate is an exact payload size the game committed to.
- **Counts join against value ranges.** A newly confirmed record count N should be checked against the corpus-wide value range of every already-decoded byte/field parameter — a field ranging exactly `[0, N-1]` is probably the selector.

**Canonical example:** Phantasie III (Amiga, `nicodemus`): `D/pln1`/`pln2` (81 content bytes) and `pln4` (496) had defeated five approaches and been escalated to `re-codebreaker`. An unrelated subagent tracing the overworld map mentioned the map-switch routine installs "a 9×8 castle-interior grid and a 31×15 Netherworld grid" — `(width, maxY)`, i.e. 9×9 = **81** and 31×16 = **496**. The loader's read immediates (`#$51`, `#$1F0`) confirmed it within minutes and the escalation was stood down.

**Variant:** Final Fantasy VII (PSX field BGM, `siren`): a new instrument bank had 93 records (0–92); `PROGCHANGE`'s parameter, decoded in an earlier unrelated pass, ranged exactly `[0, 92]` across 24,487 occurrences — instrument selection settled with no new disassembly.

## The orchestration corollary

**Don't escalate while a sibling trace on a related subsystem of the same binary is still running.** It is producing constants for free. Wait for it to land, re-check its constants against the stalled item, then decide. If already escalated and the item resolves, stand the specialist down explicitly, and verify anything it volunteered like any other claim.

Related: `working-tree-may-already-solve-a-docs-open-item.md`.
