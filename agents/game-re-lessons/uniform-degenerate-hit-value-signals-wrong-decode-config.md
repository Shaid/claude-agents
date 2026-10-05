# 100% resolution with an identical value on every record is a stronger red flag than a low resolution rate

**When it bites:** a config/table-selection sweep (engine revision, opcode
table, base address, wallset-load convention, etc.) is ranked by an
aggregate goodness metric (unknown-opcode ratio, visited-instruction count,
match percentage) and the top-ranked candidate resolves **100% of records**
— but every single one resolves to the exact same value, or the same
sentinel-shaped tuple, regardless of how varied the records plainly are
otherwise (different levels, different files, different sizes).

## What went wrong

Death Knights of Krynn's ECL wallset-slot binding was swept across engine
revisions using the corpus's own established technique (rank candidate
`{base, opcodeTable, wallsetLoad}` configs by unknown-opcode/visited-
instruction ratio, requiring a real minimum visited count to rule out
false positives from out-of-range starts). `OPCODE_TABLE_POOLS_V13` +
`{opcode: 0x21, mode: 'fill-all-from-second-operand'}` won decisively on
that metric (ratio ~0.008-0.016 vs. ~0.08-0.14 for the default v1.1 table)
and resolved **100% of levels across all 3 campaign banks (19/19)**. That
looked like a clean win. But every one of those 19 resolutions was the
identical `{slot1:127, slot2:127, slot3:127}` — no variation at all across
19 structurally-independent dungeon levels.

Manually disassembling the raw bytes at one real hit position (byte-level,
against both the winning and the default config) showed why: under the
"winning" v1.3 table, the wallset-load opcode (`0x21`) consumed only 2
operands (5 bytes) before the scanner moved on — but the very next byte was
a real, structural continuation of a *different*, correctly-3-operand
instruction. The scanner desynced immediately after the wallset-load
instruction, landing squarely on a genuine `0x00`/`0xff` byte pair that then
read as an "unknown opcode." Under the plain **default** v1.1 table (no
override needed at all), the identical bytes decoded as a clean, coherent
sequence: opcode `0x21` "LOAD FILES" with 3 operands, immediately followed
by opcode `0x37` "LOAD PIECES" with 3 operands — exactly Pool of Radiance's
own established pattern — yielding real, varied, non-degenerate `slot1`
values (1 through 7 observed) across the corpus.

The ratio metric silently rewarded the wrong table: an aggregate
unknown/visited ratio only measures *whether decoding desyncs into garbage
somewhere*, not *whether the specific field you care about was extracted
correctly*. A desync one byte after your target field, right into a plausible-
enough continuation, can still leave the overall ratio looking better than
the correct config if the correct config's own table happens to have a less
complete opcode set elsewhere in the same file.

## The fix

Treat "100% resolution, but the resolved value is identical (or a fixed
sentinel-shaped tuple) across every record" as a bigger red flag than a
lower, varied resolution rate — the latter can be an honest partial success;
the former usually means the extraction landed on the same wrong-but-stable
byte offset every time. Before accepting it:

1. Pick one real hit position from the "winning" config.
2. Manually decode the raw bytes at that position under **both** the
   winning config and the simplest/default config the module already
   supports (its own documented default is usually the cheapest, most
   likely-correct baseline, not a fallback of last resort).
3. Compare instruction-by-instruction: does one desync into an implausible
   opcode ("unknown") a few bytes after the field of interest, while the
   other continues as a clean, semantically coherent sequence matching a
   pattern already confirmed elsewhere in the same engine family? The clean
   one is very likely correct regardless of which one "won" the aggregate
   ratio sweep.

Related, and worth checking before treating a fixed value as a bug at all:
module-documented sentinel values (e.g. `0x7f`/`0xff` meaning "don't touch
this slot") are a real, intentional part of the format, not a decode
failure — check the decoder's own doc comments for a documented sentinel
before assuming a repeated small value is noise.
