# A printable-ASCII string terminator byte defeats a "between two terminators" scan when it also appears as real content

**When it bites:** writing a "split the ROM into strings by scanning for
terminator byte X, everything between two occurrences of X is one string"
extractor, where X is itself a printable ASCII value (a period, `'@'`, a
punctuation mark) rather than a control byte like `0x00`/`0xFF` that never
legitimately appears mid-string.

A delimiter-PAIR scan (find occurrence N of the terminator, find occurrence
N+1, treat everything between them as one string) implicitly assumes the
terminator value never appears as legitimate content between two real
strings' worth of it. That assumption fails whenever the terminator is a
printable character that can also occur mid-string (or immediately after
one real string, before unrelated binary code, before the *next* real
string's own terminator) — the byte right after one real string's own
terminator is not necessarily the start of the next string; it can be
arbitrary binary (opcode bytes, padding, table data) that doesn't contain
another terminator for a long stretch. A delimiter-pair scan then reports
one giant "segment" spanning from a real string's terminator all the way to
the next actual terminator occurrence — which the caller then rejects
outright (fails an "is this substring mostly printable" gate) because most
of that giant span is genuinely binary, silently dropping BOTH the real
string that ended at the first terminator and the real string that starts
somewhere inside the span before its own terminator.

Confirmed on Black Tiger (`kolbold`): UI strings terminate on a literal
`0x40` (`'@'`) byte (`"CREDIT  0@"`, `"1UP@"`, etc.), but `'@'` is
ordinary printable ASCII (`0x20`-`0x7e`) that can also occur inside binary
code by coincidence. A first-pass extractor that split on "everything
between two `'@'` bytes" found only 13 hits across the entire fixed 32KB
program bank — almost all of them accidental matches inside an unrelated
*ciphered* text block elsewhere in the ROM (see the sibling lesson on
`multi-byte-code-second-byte-collides-with-terminator.md` for a related but
distinct collision class), while real, known-present strings like
`"CREDIT  0@"` and `"HIGH SCORE@"` were missing entirely — the segment
containing them spanned back to some much earlier, unrelated `'@'`
occurrence deep in binary code, failed the printable-ratio gate, and was
dropped.

**The fix:** scan for **maximal runs of printable bytes** (the classic
coreutils `strings` algorithm — accumulate consecutive printable bytes,
flush the run on the first non-printable byte, regardless of any specific
terminator value), then trim a single genuinely-trailing terminator
character from the end of each flushed run if present, rather than pairing
up terminator occurrences. This generalizes past `'@'` to any printable
terminator convention. It does **not** solve everything: a run like
`"CREDIT  0@A..."` where a real terminator sits mid-run with more printable
content immediately following can still merge two logically-distinct labels
into one reported string — that residual imperfection is a separate,
lower-priority cleanup (hand-curation or a smarter per-label boundary rule),
not a reason to fall back to the broken delimiter-pair approach.
