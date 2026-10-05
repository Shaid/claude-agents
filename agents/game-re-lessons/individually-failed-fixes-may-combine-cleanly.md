# Individually-failed fixes on different axes — test the combination cells before escalating

**When it bites:** two or more candidate fixes have each been tried and
failed, they vary along *different* axes (an opcode-table revision vs. a
header/prefix strip; a stride vs. an endianness; a base address vs. a
record width), and you're about to escalate or write a settled negative on
the strength of those failures.

Attempts that each vary one axis while holding another — possibly wrong —
axis fixed are confounded, not independent. "N distinct failed
hypotheses" only rules out N *cells* of the axes' cross-product, not the
axes' values themselves; the correct value of every axis may already have
appeared in some failed attempt, just never all in the same run.

Confirmed on Treasures of the Savage Frontier (Amiga, SSI Gold Box,
`crawl` project): the ECL bytecode resisted three genuinely
different-looking attempts — v1.1 opcode table without a prefix strip
(271 unknown opcodes), v1.3 table without the strip (246 unknown), v1.1
table with the strip (1,836 unknown in the automated walk). That paths-
tried table honestly cleared the escalation bar, and a Fable-tier
`re-oracle` escalation was spent — whose near-first move was running the
one untested cell, **v1.3 table + strip: 0 unknown, 0 desyncs, corpus-
wide**. Two axes (table, strip), four cells, three tried. The answer was
the fourth. Each winning axis value had already been "refuted" once while
paired with the other axis's wrong value.

The fix is mechanical: when logging a failed attempt in the paths-tried
table, record it as a cell of an explicit axes-x-values matrix, and
before escalating, sweep every remaining cell of that matrix — for
decode-config axes this is minutes of compute (the same automated walk in
a loop), orders cheaper than any escalation. A cross-product sweep also
upgrades the eventual brief if the negative survives: "all 4 cells fail"
is real evidence; "3 hand-picked cells fail" is not.

Corollary for ranking sweeps: score cells by a corpus-wide error metric
(unknown-opcode count, desync count) and demand the winner be *cleanly*
separated, not merely best — and beware aggregate-ratio winners that
resolve everything to one identical degenerate value (see
`uniform-degenerate-hit-value-signals-wrong-decode-config.md`).

Second confirmed instance, this time on a container/codec problem rather
than an opcode table, and with the winning sweep run by an escalated
specialist rather than the calling session itself: Death Knights of
Krynn's `8x8d1.daa` (`crawl` project) resisted 5 structurally distinct
container hypotheses — the project's own already-confirmed "DOS DaxFile"
container as-is, a sibling title's own bespoke `.dax` codec, an inline
self-describing chain with no directory, and plain headerless 1bpp reads
at several header-skip amounts — all producing noise or outright parse
failure. A `re-oracle` escalation found the real container needed BOTH
axes flipped from the already-confirmed sibling format simultaneously:
directory fields **big-endian** (not little-endian) AND
`dataOffset = headerLen` **exactly** (not `headerLen + 2`). Every prior
pass's attempt had tried the LE reading with the `+2` offset, misreading
entry 0's own `rawSize` field as a spurious "tag byte" and finding no
clean single header-length winner at any offset 0-127 under either
endianness alone — exactly the confounded-axes signature this lesson
describes, just for a container header rather than an opcode-table
selection. Independently re-verified in a fresh Python re-implementation
(all 31 entries in the real 63,376-byte file decode byte-exact, chain
contiguous, EOF-exact) before promoting it to a committed TypeScript
decoder. The general point holds even when a specialist (not the base
loop) finds the combination: log failed hypotheses as cells of an
explicit axes-x-values matrix in the paths-tried table so the next pass
(human or escalated) can see which combinations are actually untested,
rather than "5 different things failed" reading as exhaustive.
