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

Related: `c-integer-wraparound-vs-js-doubles.md` (another C→JS semantic
shift in decoder ports), `bytecode-trace-in-range-result-can-still-be-noise.md`.
