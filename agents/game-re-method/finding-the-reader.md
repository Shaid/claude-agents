# Finding the reader — worked techniques

`Read` this when Method §2's basic approach (disassemble the loader, trace what
it does with the pointer) isn't enough: no hunk header, no load address, a
symbol table you haven't checked for, or a loader you can't locate.

**Raw code overlay with
no known load address (no hunk header):** a full disassembly pass is
expensive without a base address. First choice: disassemble the *loader*
(it usually has a hunk header, so it's cheap) and trace its decrunch call
for this overlay specifically — the destination address it passes is the
overlay's runtime base; confirm you traced the right call by matching its
crunched-size immediate against the overlay file's own known crunched size
byte-for-byte (zero guessing). Confirmed Jungle Strike AGA's `JS` (230KB
headerless overlay) loads at `$100000` this way, then `ira -binary
-offset=<base>` disassembles it correctly and its own embedded data
(including copper lists, next paragraph) becomes readable at real
addresses. Fallback if the overlay's own loader isn't traceable: check
whether a *different* small loader elsewhere in the corpus embeds its own
sample instance of the same data format next to code you can trace instead
(Jungle Strike AGA: `JStrike`'s depacker carries an embedded `JUNK`-format
boot screen next to a copper list, confirming the palette register layout
before `JS`'s own base address was known).

**Amiga palette hunting via copper-list trace (once a code base address is
known):** when blind corpus-wide searches fail (`LoadRGB32` header scan,
12-bit-word-run scan, absolute-`$DFFxxx`-address scan — all prone to false
positives against ordinary bitplane/code data), look for `COP1LC`/`COP2LC`
install sites instead: `MOVE.L #<addr>,128(A5)` (or `132(A5)`) after a
`MOVEA.L #$00dff000,An` custom-chip-base load. Decode raw bytes at `<addr>`
directly as copper instructions (don't trust a disassembler's code/data
guess there): 4 bytes/entry, first-word bit0 clear = `MOVE reg,val`, bit0
set = `WAIT`/`SKIP`. A real palette is 16-32 consecutive `MOVE`s to
`COLOR00`-`15`/`31` (`$180`-`$1BE`) with plausible non-zero `0x0RGB`
values; an all-zero-COLOR copper list nearby is usually a boot/blank
placeholder red herring, not the real one — check more than the first list
you find. Cracked Jungle Strike AGA's long-missing palette this way after
several blind-search phases failed, confirmed by full-colour renders.

**Naming anonymous `JSR -N(A4)` calls in a SAS/C Amiga binary (small-code
model):** an A4-relative `JSR` does *not* jump into data, and its displacement
is not a data offset you should try to interpret. SAS/C's small-code model
routes cross-hunk calls through a **jump table of 6-byte `JMP.L abs` stubs at
the head of the DATA hunk**. To resolve one: compute the DATA offset
(`A4 = DATA_start + 0x7FFE`, so `offset = 0x7FFE + displacement`; every such
offset is a multiple of 6 — a free sanity check that you're looking at the
table), read 6 bytes there, confirm they start `4E F9`, take the absolute
target from the following longword, and look *that* up in the executable's
`HUNK_SYMBOL` block. One pass turned a wall of anonymous
`JSR -31992(A4)`-style calls in Vengeance of Excalibur's `ExcalII` into
`_OpenImag` / `_OpenFrml` / `_GetObject` / `_DrawPrim` / `_GoThroughDoor` /
`_ManipObject` / `_ColorReMap` / `_SectRect`, making a scene-drawing routine
self-documenting — and **corrected two claims a prior pass had recorded exactly
backwards** (`-31992` had been guessed as "a static single-image object" and
`-32004` as "a multi-frame animated object"; they are `_OpenFrml` and
`_OpenImag` respectively).

Two practice upgrades from a five-run campaign (Spirit/Vengeance combat +
exploration, 2026-08) where this technique was decisive every single time:

- **Script it at session start, don't resolve by hand.** A ~30-line scratch
  resolver (parse `HUNK_SYMBOL`, walk the stub table, map every
  `displacement → symbol`) settles *all* anonymous A4 calls in one pass —
  one run resolved ~40 call targets before starting its trace, and every
  subsequent claim inherited ground-truth naming for free. When the
  committed `.asm` lacks file-offset comments, `amitools`'
  `binfmt.hunk.HunkReader` reads the DATA-hunk bytes directly.
- **Never assume a displacement transfers between binaries of the same
  engine family.** Spirit's `Excal` and Vengeance's `ExcalII` share symbol
  names but not stub-table layouts; every displacement must be re-resolved
  per binary (same lesson class as `decoder-address-reuse-across-rom-release.md`).

Then **confirm from the call, and use the symbol only to find it.** Each of
those two functions carried its own FourCC literal in its body
(`PEA $46524d4c` = `'FRML'`, `PEA $494d4147` = `'IMAG'`) feeding a
`GetResource` call — so the resource class was provable from what the function
actually does, independent of whether the linker's symbol name was accurate or
the stub table was resolved correctly. A symbol name is a lead; the call it
makes is the evidence.

**No-symbols 3D code:**
census every `MULS`/`MULU` past the real entry point (filter out pre-entry
data misdecoding as garbage instructions); tight clusters of 3 multiplies
2 bytes apart mean dot-/cross-product, multiply-then-divide means perspective
divide (`x/z`, `y/z`). Found Carrier Command's projection + backface-cull
this way, purely statically (`docs/explore/CarrierCommand/`).

**Finding sibling compression algorithms via xref-up:** once one
compressor's entry point is confirmed, trace *its own caller(s)* — often a
generic resource-loader dispatch (jump table keyed by a command field in a
descriptor struct) with several sibling cases: raw copy, the known
algorithm, no-ops, and one or more *other*, previously-unknown algorithms.
A reliable way to find a second/third codec with zero blind entropy
scanning. Confirmed byte-for-byte structurally identical (different
addresses) across two sibling ROMs this way (Strike project's Genesis
Jungle Strike/Urban Strike, a second "Strike RLE" codec found behind a
`width*height`-computing dispatch case).
