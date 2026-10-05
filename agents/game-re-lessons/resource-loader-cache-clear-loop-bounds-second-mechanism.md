# A cached resource loader's own cache-array init/clear-loop trip count is a free, cheap oracle for a hidden second loading mechanism

**When it bites:** you're investigating an unfamiliar resource-ID/catalog-
indexed loading system on a period game (any platform — this generalizes
past 68k), a doc already documents "an N-entry cache" for the on-demand
loader without explaining why N, and some catalog IDs never show up as a
literal or computed argument to that loader's own call sites no matter how
hard you search.

## What happened

Dune (Amiga, `wyrm`): `docs/game-load-order.md` already documented
`LAB_0BEC`'s "86-entry screen cache at `3112(A6)`" as a fact, with no
further significance attached. Tracing three data-table resources
(`map.hsq`, `globdata.hsq`, `command1.hsq`) that never appeared as a
literal `MOVEQ #id,D0`/`MOVE.W #id,D0` argument anywhere before any of
`LAB_0BEC`'s 74 call sites (confirmed by backward-scanning *every* call
site for its nearest preceding D0-setting instruction, not just grepping
for the three specific IDs — the exhaustive scan is what made the negative
trustworthy) led to disassembling the cache-clear loop itself:

```
LAB_00CA:
    LEA     3112(A6),A0
    MOVEQ   #85,D7        ; 86 iterations (0..85 inclusive)
LAB_00CB:
    CLR.L   (A0)+
    DBF     D7,LAB_00CB
```

86 wasn't an arbitrary "cache size" — it was the loader's own **addressable
range**, with **zero bounds checking** at the indexing site
(`LEA 3112(A6),A1 ; LSL.W #2,D0 ; ADDA.W D0,A1`). Every catalog ID at or
above 86 (dialogue/phrase/save/music tables, and the three target files)
turned out to route through a *completely different*, uncached loader
(`LAB_0C95`) with its own endianness-fixup helper (`LAB_00D9`) — a second
subsystem this project's docs had never mentioned, found in about ten
minutes once the boundary was suspected.

## Why this generalizes

Any indexed resource cache/table on any platform needs its backing array
sized somewhere — an init loop, a `.bss` reservation, a struct array
declaration. That size is frequently smaller than the game's full
resource-ID space, and the *overflow* IDs are handled by different code a
docs pass focused on "the main loader" would never stumble into by reading
forward from the loader itself. The technique transfers directly: whenever
a cached/indexed subsystem's capacity constant is known (from an init
loop, an allocation size, or a documented array length), check it against
the full ID/index space the game actually uses — a gap between them is a
strong, cheap signal that a second mechanism exists for the excluded
range, worth a few minutes of grepping before assuming the missing IDs
are simply unused or undecodable.

## The fix

1. Exhaustively census every call site of the suspected primary
   loader/dispatcher for its actual argument value (literal or computed) —
   not just a targeted grep for the specific IDs you're chasing. A
   negative ("no call site ever exceeds N") is only trustworthy once every
   call site has been checked.
2. Disassemble whatever function initializes the loader's own backing
   store (a clear loop, an allocation, a declared array) and read its real
   trip count/size as a hard capacity bound, independent of what any doc
   already claims about "the cache."
3. If the ID/index space you're chasing sits above that bound, search for
   a *second* loader (often reached from an early boot/init routine that
   was already partially documented but not fully traced) rather than
   assuming the resource is unreachable or the ID mapping is wrong.
