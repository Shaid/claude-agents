# A corpus scanner's code-likelihood pre-filter permanently excludes the pure-data blocks a later investigation needs

**When it bites:** a whole-corpus census (over decompressed archive
blocks, overlays, or any large heterogeneous file population) that
searches for consumers of a suspected data table — a literal-immediate
scan, an opcode-idiom scan, an xref scan — is scoped to a subset of blocks
a *prior* pass already filtered by a "does this look like real code"
heuristic (a MIPS/68k/etc. function-prologue-density threshold, a
disassembly-succeeds check, an entropy/opcode-plausibility score). Every
subsequent investigation of the *same* item keeps reusing that filtered
subset without re-examining what the filter was originally built to do.

## What went wrong

Valkyrie Profile (PSX, `valkyrie`): a code-1 "Auto Item" static lookup
table's address was known (from disassembling its consumer), but its
containing file/overlay was not. The project's established technique
(`scanSlzBlocks()` over both discs' full archive, ~26,911 decompressed
blocks) filtered to the ~1,642 blocks scoring above a
`addiu $sp,$sp,-N` prologue-density threshold — a sensible way to make a
"does any code reference address X" census fast and low-noise. Every
subsequent census for this table across three separate investigative
passes (a struct-field-write scan, an access-idiom scan, a main-executable
check) searched only within that pre-filtered 1,642-block subset — because
that subset was already sitting there, proven to work, and reused by
convention. All three came back negative, each treated as meaningful
progress narrowing the search.

The table itself is 396 bytes of pure data. A 396-byte data table scores
approximately zero on a function-prologue-density filter — it *cannot*
appear in the ~1,642-block "looks like code" subset, no matter which of
the ~26,911 blocks actually holds it. Every one of those three passes was
therefore searching for **code that references the table**, not **the
table's own bytes** — a structurally different question the filtered
subset was incapable of answering, regardless of how many times or how
carefully it was re-run. The blind spot survived three separate sessions
because each treated "the established scan technique found nothing" as
evidence about the target, rather than checking what class of content the
scan's own pre-filter was built to admit.

## Fix

Before reusing an established "whole-corpus scan" technique for a new
target, ask what the scan's pre-filter selects *for* and whether the new
target is even a member of that class. A code-density/prologue filter
answers "is this code" — reusing its output to hunt for a target that is
data (a lookup table, a string pool, a palette, a struct array) is a
category error baked into the setup, not a weaker version of the same
search. When the target's category is uncertain or known to be
non-code, run a second, *unfiltered* pass over the full block population
(or the complementary "excluded" subset) with structural constraints
appropriate to data (record stride, field-value ranges, a discriminant
byte pattern) — this is a different search, not a more thorough version
of the code-reference search, and the two do not substitute for each
other no matter how exhaustively either one runs. Confirmed on the same
Valkyrie Profile investigation: running the unfiltered, whole-corpus
byte-content structural scan (both the SLZ-decompressed corpus with no
code filter, and the raw undecompressed byte stream) is what actually
tested "is the table's data present anywhere" for the first time across
several prior sessions — it returned a genuine, well-verified negative
where the code-filtered censuses had returned three superficially-similar
but categorically uninformative ones. Always verify a scanner's own logic
against a synthetic positive control matching the exact structural
hypothesis before trusting a corpus-wide zero-hit result as decisive —
otherwise a boundary or off-by-one bug in the new scanner itself is
indistinguishable from a genuine absence.
