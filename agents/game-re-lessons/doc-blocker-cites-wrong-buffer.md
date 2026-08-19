# A doc's "untested because it's a different buffer/pointer" blocker may cite the wrong buffer for the question being asked

**When it bites:** a prior doc pass flags an open question as blocked on
"it's loaded through/into a different buffer, pointer, or global than the
one already confirmed" — before spending more disassembly effort resolving
*that* buffer, check that it's actually the buffer the open question
depends on, not a superficially similar one that happens to share a
describing word ("buffer", "loaded from a different place") with the real
blocker.

Phantasie III (Amiga, `nicodemus` project): the docs correctly established
that the castle-interior/Netherworld map loader stores its raw grid **cell**
bytes into a buffer at hunk-1 `$295C`, distinct from the overworld's own
cell array at `$2964`. That's true and was real analysis. But the open
question — "do these maps share the overworld's tile-**art** bank, or a
separate one?" — depends on a completely different global, the tile-art
bank pointer at `$290C`, which has nothing to do with `$295C`/`$2964`. The
doc's "different buffer, so untested" phrasing conflated the two: it named
a real, confirmed fact about the wrong pointer and let that stand in for an
answer about a different pointer that was never actually investigated. The
open item sat unresolved for a full session cycle as a result, even though
answering it needed no new disassembly — just checking a raw byte census of
`$290C`'s own references (one write, ever, from the same source file both
the "old" and "new" cases already used; two consumers both reached through
one already-documented shared blitter).

**Fix:** when a doc's stated blocker for an open question is phrased as "X
is loaded via a different buffer/pointer than Y," write down explicitly
*which* buffer the open question's answer actually depends on before
treating that phrasing as a real blocker. If the cited buffer and the
decision-relevant buffer are not provably the same global, the "blocker" may
already be answerable from evidence the doc already has — check the
decision-relevant pointer's own write/read census directly rather than
re-deriving the buffer the doc did cite.
