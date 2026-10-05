# Porting `x--; if (x != 0) { loop }` to `while (x > 0) { x--; loop }` shifts the iteration count

**When it bites:** hand-porting a decompressor/disassembler loop from
goto-heavy C (or a disassembly) into a modern language, especially one
whose entry decrements *before* testing, and the port overruns or
under-produces on exactly the streams that exercise the boundary.

The C pattern `Loop: d7--; if (d7 != 0) { body; goto Loop }` processes the
body **`count-1` times** for `d7 = count`. The "obvious" rewrite
`while (d7 > 0) { d7--; body }` processes it **`count` times** — off by
one, because the C form tests the *post-decrement* value while the while
form tests the *pre-decrement* value. The correct structured equivalent is
`for (;;) { d7--; if (d7 === 0) break; body }`.

Confirmed porting `Unpacker.Unpack` (Drakkhen, `drakkhen`): the symbol
loop `d7 = ReadWord(2)+1; LoopAA1: d7--; if (d7 != 0) CaseAA` became
`while (d7 > 0) { d7--; ... }`, which read one extra source byte per
block — a Huffman golden fixture failed with "symbol stream overruns
source" while the raw-copy fixture (which has no such loop) passed. The
Python reference port used the exact decrement-then-test form and handled
all 154 blocks; only the "cleaned-up" TS loop was wrong.

**Guard: golden fixtures must cover every loop shape in the codec.** A
raw-mode fixture exercises none of the tree loops; a Huffman fixture
exercises the symbol loop. One fixture per distinct control-flow path
caught this in two test runs; a single raw-mode fixture alone would have
shipped the bug. When transcribing fixture bytes from probe output, copy
the **complete** buffer (truncating e.g. to a preview length silently
corrupts the golden test and wastes a debugging cycle).

**A successful avoidance, confirmed on Dungeon Master II's `P41A` module
unpacker port (`crawl` project, see `romhacking-community-tools-first.md`):**
when the C source uses a plain `for`-loop with `continue`/`break` inside it
(not a `goto`-based decrement-then-test idiom), translating it into a JS/TS
`for` loop with the same `continue`/`break` statements in the same
positions — rather than manually flattening into a `while` loop — sidesteps
this whole class of bug by construction. JS's `continue` on a `for` loop
still runs the loop's own increment/re-test clause, matching C's `for`-loop
`continue` semantics exactly, so no manual reasoning about pre/post-
decrement ordering is needed. This doesn't help for the `goto`-based
decrement-then-test idiom this file's main example covers (there is no
`for`-loop shape to preserve) — it's specifically useful when the reference
source already uses a structured `for`/`continue`/`break` loop, which is
common in modern reference decoders (like `libxmp`) even when older/
disassembly-derived sources use `goto`.

**The same off-by-one has a native hardware-instruction form, not just a C
`goto` idiom: 68000 `DBF`/`DBcc` runs `initial_value + 1` times, not
`initial_value` times.** `DBcc Dn,label` decrements `Dn` *after* testing the
loop's exit condition on entry, and only stops once `Dn` underflows from `0`
to `-1` (`0xFFFF`) — so seeding `Dn = N` before the loop and reading "N" off
the seed constant alone under-counts the real iteration count by exactly
one, the same trap as the C `d7--; if (d7 != 0)` idiom, just baked into the
CPU instead of hand-written. Confirmed porting Midwinter 2's terrain
fine-expansion sub-passes (`hunter` project): `DBF D7,label` was seeded with
`D7 = 0x52` (82), which reads as "82 iterations" at a glance — but the real
loop runs **83** times (covering all 83 columns of the 83-wide coarse grid).
This wasn't caught by inspecting the loop alone; it only surfaced by
cross-checking against an independently-known constant elsewhere in the same
driver (the outer routine's own dest-pointer row-advance of 664 bytes =
2 x 332 B = 2 x 166 words, which only factors correctly if the sub-pass
writes 83 output pairs, not 82). **Guard:** never read a `DBcc` seed
constant as the literal iteration count — always add one, and where
possible, cross-check the resulting count against an independent constant
(a buffer size, a stride, a sibling loop's own bound) before trusting the
port. This generalizes to any decrement-and-test-after hardware loop
primitive across ISAs (6502's `DEX`/`BNE`, Z80's `DJNZ` — same underflow-at-
test-time shape), not just 68k.

Related: `c-integer-wraparound-vs-js-doubles.md` (another C→JS semantic
shift in decoder ports), `bytecode-trace-in-range-result-can-still-be-noise.md`.
