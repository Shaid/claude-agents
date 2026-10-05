# A command-stream grammar with its type discriminator on the wrong byte can still close byte-exact — and its garbage index fields impersonate a cross-file registry

**When it bites:** a variable-length command/record stream parser closes
byte-exact on every file (0 slack, every stream ends on its terminator),
yet one of its decoded index fields (sprite number, resource id, tile
index) "regularly exceeds" the natural target array (e.g. sprite numbers
up to 126 against banks of 32-47 frames) — and the write-up is heading
toward "these index a shared, cumulative table built across several
resident banks" with a TODO to reconstruct that registry. Also fires when
a stop rule for a repeated sub-list (a threshold on an accumulator, a
magic count) was fitted to one worked example rather than read from the
loader.

Dune (DOS VGA, Cryo, `wyrm`): `.SAL` room scenes are a stream of 5-byte
sprite placements and variable-length polygon/line shapes. A first-pass
parser took the type from the **first** byte (`>= 0x80` = shape), masked
the colour with `& 0x7f`, and ended a polygon's point list when a running
`acc += highByte(rawX) & 0xf0` crossed `0xb0` — a numerology fit to one
rectangle. It closed byte-exact on all 4 files and drew plausible walls,
so it was documented as confirmed, and the out-of-range sprite numbers it
produced were theorised as a cross-file registry: a TODO row, a doc
section and an escalation brief were all built on that premise. The game's
own interpreter (`DUNEPRG.EXE 0x3ff1`: `lodsw; cmp ax,0xffff; je end; js
shape`) tests bit 15 of the first *word* — bit 7 of the **second**
(modifier) byte. Every shape whose colour byte was `< 0x80` had been
misread as a sprite command, and the desynchronised bytes that followed
became "sprite numbers". Under the real grammar all 1,022 sprite commands
in 48 rooms resolve inside ONE bank chosen by the room number (0
out-of-range), and no registry exists anywhere in the executable.

Why the closure didn't catch it: the misread commands plus the fitted
accumulator rule happened to consume the same total byte count as the real
grammar, and a stream with no invalid byte sequences can't fail a walk —
the same weakness as `rle-decode-succeeds-on-garbage.md`'s corpus-scale
variant and `self-consistent-chain-wrong-unit.md`'s phase-shift case.
Byte-exact closure validates *lengths*, not *which byte means what*.

**The fix, in order of cost:**

1. Treat "decoded index regularly exceeds its natural target" as evidence
   against the parse first, and only then against the target — cf.
   `partial-resolution-rate-is-noise.md` (a wrong whole-field reading lands
   on valid ids by chance) and `locally-indexed-substructures.md` (index
   scope is an independent question, but only once the field is real).
2. Any stop/discriminator rule fitted to a worked example is a hypothesis:
   find the loader's own dispatch (`cmp`/`js`/`test` on the first
   word/byte) and read the flag bit from it. Here the real rules were two
   flag bits (bit 14 = end of chain A, bit 15 = end of polygon) the fan doc
   had already described and the fit had papered over.
3. Re-run the closure under the corrected grammar AND a second, independent
   count that the wrong grammar cannot satisfy — here "0 out-of-range
   frames" plus six rooms whose maximum sprite number equals their bank's
   exact frame count.
