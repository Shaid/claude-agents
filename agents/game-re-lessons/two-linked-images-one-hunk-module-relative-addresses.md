# One executable "hunk" can hold two separately-linked images with different addressing conventions

**When it bites:** a string pool or table in an executable looks completely
unreferenced after several *structurally different* reference scans (LEA/PEA,
every addressing mode, branch targets, the relocation table, raw longword
literals) — **and** the same binary contains a large population of
absolute-long `JSR`/`JMP` operands that are *not* covered by the relocation
table and hold implausibly small values (`JSR $0000008C`) that read as
low-memory or exception-vector calls.

Those two symptoms are the same root cause. The file is one container but two
independently linked images, and one of them stores addresses in its own
module-relative space. Every scan that searched for a *container-relative*
address was looking in the wrong address space, so no amount of broadening the
instruction *shape* could ever have found the reference.

Confirmed on Epic (Ocean, 1992, Amiga, `hunter` project). `EPIC` is a single
194,644-byte `HUNK_CODE` hunk, but:

| | Hunk range | Absolute-long `JSR`/`JMP` sites | Addressing |
|---|---|---|---|
| **World A** — DOS layer, hardware, disk I/O, Paula driver | `0x00000`-`0x0BFFF`, `0x24000`-`0x2F853` | 184, **all relocated** | normal, `HUNK_ABSRELOC32`-covered |
| **World B** — the game engine | ~`0x0CEEA`-`0x23FFF` | 678, **none relocated** | module-relative: `world_b = hunk − 0xCAB6` |

Zero exceptions, zero overlap. World B reaches World A only through a
**101-entry service jump table** (101 consecutive relocated pointers at hunk
`0x25E26`), so World B's small "absolute" operands are service *slot numbers*,
not addresses — which is exactly why they collide with plausible 68000
exception-vector addresses and send you chasing a low-memory jump table that
doesn't exist. Every filename-pointer table in World B stores `hunk − 0xCAB6`,
which is why three independent hunk-address scans across two prior sessions
found nothing and the content was written up as possibly dead.

**Diagnostic tells, cheapest first:**

1. The relocation table covers only part of the code — partition every
   absolute-operand call site by "is this operand in the reloc table" and check
   whether the two sets fall into contiguous, non-overlapping address ranges.
   Two clean regions means two images.
2. Absolute call operands cluster in an implausibly low or narrow range
   (they're table indices, not addresses).
3. A run of consecutive relocated pointers at a fixed 4-byte stride, whose
   count matches `maxOperand/4 + 1`, is the bridging service table.

**How to recover the delta (no disassembler required):** sweep candidate δ and
score how many of the suspect region's un-relocated absolute call targets land
on an address that *same region* also reaches via a position-independent
`BSR`/`JSR (d16,PC)`. Correct code calls the same routines both ways, so the
true δ spikes. On Epic, δ = `0xCAB6` scored 21 against 9 for the runner-up.
Then cross-check with an independent anchor before trusting it: take a known
string's container-relative offset and subtract the pointer value some table
stores for it — it must give the same δ exactly. (Epic: `"EXPL2"` at hunk
`0x159DE`, slot-1 pointer `0x08F28`, difference `0xCAB6`.)

Once δ is known, re-run every earlier failed scan with `target − δ` and the
references appear. Put δ, the base registers and the service table into a
shared module (Epic: `tools/epic/epic_worldb.py`) rather than re-deriving it —
every later question in that binary needs it.

See also `negative-from-addressing-root-not-shapes.md`: the control that would
have exposed this years earlier is running the identical scan against names you
already know are live.
