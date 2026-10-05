# A hand-rolled register-linked opcode-word scanner needs its own fixed/variable bitmask per instruction *encoding*, not one reused across steps that share a mnemonic

**When it bites:** writing a multi-instruction opcode-word pattern scanner
(matching a whole-file byte stream against several consecutive fixed-width
instruction words, allowing any register combination, to find "the same
decoder" in a sibling binary without relying on disassembly alignment or a
literal byte-for-byte match) — and the scan comes back with zero hits despite
good reason to expect the pattern exists, while a much cruder fallback (a
single-instruction literal scan, or manual disassembly of a small candidate
set) finds real matches.

Millennium 2.2 (Amiga, `methanoid`): hunting for a copy of Deuteros' RLE
image-codec decoder by its exact instruction shape — `MOVE.B (An)+,Dr` /
`MOVE.B Dr,Dc` / `ANDI.B #$C0,Dr` / `Bcc` — a register-linked scanner checked
each 16-bit word against a `(fixedBitsMask, template)` pair, intending to
allow any register numbers while still requiring the right opcode/addressing
form. The scanner used the identical mask constant `0xF1F8`... except it was
actually written as `0xFE38` and reused for both `MOVE.B` steps. That mask is
only correct for `MOVE.B (An)+,Dn`, whose source-addressing-mode field (bits
5-3) is fixed at `011` (post-increment) — encoding `0001 DDD 000 011 AAA`.
`MOVE.B Dn,Dn` has a *different* fixed field in the same bit position: its
source-addressing-mode bits are fixed at `000` (data-register-direct) —
encoding `0001 DDD 000 000 SSS`. Reusing the first instruction's mask against
the second silently forced its variable source-register field to match only
`000`, because those bits fell inside the (wrongly reused) "fixed" portion of
the mask instead of the "variable" portion. The scan consequently rejected
every real instance where the second `MOVE.B`'s source register wasn't D0,
returning 0 hits across the whole file even though the technique itself was
sound and real matches existed.

**Fix:** derive the fixed-bits mask and template for *each* instruction word
in a multi-step scan independently, from that step's own specific addressing
mode — never assume two steps sharing a mnemonic (`MOVE.B`, `ADD.W`, etc.)
share a bitmask just because they "look like the same kind of instruction."
Different addressing modes for the same mnemonic place fixed vs. variable
bits in different positions even when the overall word width and opcode
class are identical. Before trusting a zero-hit result from such a scanner,
sanity-check it against at least one instruction you can hand-verify bit by
bit (decompose the known-good word's fields against both the mask you used
and a mask you re-derive from scratch) rather than concluding the pattern is
absent. When the scanner is expensive to debug and the pattern search is
narrow enough, a simpler single-instruction literal/immediate scan (here: a
plain `ANDI.B #$C0,Dn` search, 11 raw hits, 4 manually confirmed real) is a
fine, faster substitute for getting unblocked — fix the register-linked
scanner later if it's still needed for a broader search.
