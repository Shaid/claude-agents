# A bit-packer test fixture must give refill words MORE usable bits than the seed word, not the same count

**When it bites:** building a synthetic bit-packed test fixture for a
backward-reading/bit-oriented LZ decompressor whose real decoder treats the
first "seed" word specially (a sentinel bit marking how many lower bits are
valid payload, found by scanning for the highest set bit) versus every later
"refill" word (a fixed bit count, no sentinel) — especially when the fixture
decodes correctly for single-word payloads but throws an overflow/bounds
error only once a payload spans two or more words.

## What happened

Writing a vitest regression fixture for AGOS's `simon_decr` (a backward-
reading bit-oriented LZ77 codec, `crawl`'s Elvira/Elvira 2/Waxworks family)
required a `SimonDecrFixtureBuilder` that packs a hand-built bitstream into
32-bit big-endian words, mirroring the real decoder's own `getbit()`. A
single-token fixture (one word) passed immediately. A two-token fixture
spanning 106 bits (4 words) threw `simonDecr: match offset overflow` — not a
bug in the shipped decoder (already verified byte-exact-clean-decode against
628 real files with zero errors), but in the fixture builder itself.

The real decoder's `getbit()` has an asymmetry easy to miss when
skim-reading it: the seed word's usable-bit count is computed once, up front,
by scanning for its highest set bit (`bits` ends at that bit's index — call
it `L`), consuming exactly `L` payload bits below the sentinel before the
next refill. But the REFILL branch (used for every subsequent word) sets
`bits = 31` and *also* returns a bit in that same call, without a
decrement-before-read step first. Tracing the call sequence shows a refilled
word actually yields 32 total `getbit()` calls (local bit positions 0-31)
before the *next* refill fires — one more than the seed word's `L`-bit
budget when `L = 31`. The fixture builder had capped every word's chunk size
at 31 bits uniformly (seed and refill alike), which silently dropped one bit
of payload at every word boundary past the first, desyncing the whole
downstream bitstream by one bit per non-seed word — read far enough and a
literal-token flag bit gets misread as a match-token flag bit, producing the
overflow error deep into the stream, nowhere near the actual bug.

## The fix

Diagnosed by writing a standalone simulation of the exact `getbit()`/refill
logic against the raw in-memory `words` array (bypassing the file
byte-serialization step entirely — reading straight from the JS number
array in *consumption* order) and diffing it bit-for-bit against the
intended bitstream. This isolated the mismatch to a specific bit index
inside the second word, confirming the bug was in word-chunking, not
file-byte order or the shipped decoder.

The general rule for any such "seed word carries a sentinel, refill words
don't" bit-oriented codec: a test-fixture packer must special-case the
FIRST word's capacity as `N-1` bits (one bit reserved for the sentinel,
`N` = word width) and give every SUBSEQUENT word a full `N` bits — because
the refill consumes a bit in the same call that resets the bit counter, so a
refill word's usable-bit count equals the word width, not width-minus-one.
Getting this right requires literally tracing the decoder's refill branch
call-by-call (as above), not inferring it from the seed-word logic by
analogy — the two branches are genuinely asymmetric.
