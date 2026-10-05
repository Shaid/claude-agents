# An unrecoverable relocation/base register can be solved algebraically from one known-good content anchor, then validated by requiring the REST of the table to decode as real content

**When it bites:** a table of 16/32-bit offsets is resolved via
`baseRegister + tableEntry` (an `adda.l An,Am`-shaped self-relative/
resource-relative addressing scheme), the base register's absolute value
is never set within the disassembled routine itself (its caller supplies
it), and the caller can't be traced either — e.g. no literal `JSR`-
absolute call site to the routine exists anywhere in the file (indirect/
table-dispatched call, common in hand-written 68k engines), so the usual
"trace the caller to find the register setup" path is a dead end.

Confirmed on Millennium 2.2 (Amiga, `methanoid`): a Paula sound driver's
envelope-table select opcode resolved each of 16 table entries as
`a3 + wordTable[slot]`, but `a3` was never loaded anywhere in the
disassembled ~2,300-byte routine, and a literal-`JSR`-absolute census for
the routine's own entry point (both of its two independently-loaded
copies) came back with zero hits. Rather than trace the indirect caller,
`a3` was solved algebraically from a single already-known-good anchor: an
earlier session had independently located the envelope byte-data region's
start address purely by its byte *shape* (a monotonically-declining run
terminated by a flagged byte), with no addressing scheme attached. Setting
the envelope pointer table's first entry equal to that already-confirmed
address and solving for `a3` gave one candidate value. Applying that same
`a3` to **all 16** table entries (not just the anchor entry used to derive
it) decoded every one to a real, structurally sound ADSR-style
decay-to-sustain volume curve — clean numeric decays each properly
terminated by the format's own already-confirmed hold-marker convention.
That the *content*, not just the addresses, validated across the whole
table (15 entries with zero say in deriving `a3`) is what makes this a
real confirmation rather than a coincidental fit.

**The general technique:** when a base/relocation register's value can't
be recovered by tracing its setup code, and the table it indexes points at
data whose start you've *already* independently identified some other way
(byte-shape, structural scan, cross-reference from a different mechanism),
solve `base = knownAnchorAddress − tableEntry[knownAnchorIndex]` from that
one correspondence, then apply the solved base to *every other* entry in
the same table and require their decoded *content* — not just their
resolved addresses — to look structurally real (matching an
already-established grammar, not merely landing in-bounds). A base that
solves correctly reproduces real content across the whole table; a wrong
guess (off-by-one anchor index, wrong sign, wrong table) degrades into
garbage almost immediately past the one entry you used to derive it.

**Caveat — don't over-generalize the solved register to a sibling table
using the same addressing scheme without re-validating.** In the same
session, applying the identically-solved `a3` to a second, sibling
`a3`-relative table (an arpeggio-select table using the same
`adda.l a3,An` mechanism) produced less obviously "real" content than the
envelope table did — plausible in principle for the domain (SFX pitch
sweeps rather than musical intervals) but not independently confirmed. One
table validating decisively is strong evidence the *register value* is
correct; it is not automatically proof that every sibling table sharing
that register also shares your assumed field width/grammar/byte-alignment
— flag those separately as rendered, not confirmed, until each gets its
own content-level check.
