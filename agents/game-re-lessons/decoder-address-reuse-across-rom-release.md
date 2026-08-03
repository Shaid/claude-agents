# A confirmed decoder's hardcoded code-region address can silently resolve to the wrong bytes on a second ROM release

**When it bites:** reusing an already-confirmed decoder (same game) against
a second ROM release, revision, or region dump — especially when that
decoder's addresses point into game **code** (a field-program bank, an
engine routine's inline data table) rather than a fixed, code-independent
data table. Running the decoder without a thrown error, or eyeballing a
plausible-looking rendered thumbnail, is not evidence it decoded correctly.

A decoder's module-level address constants are only valid for the exact
binary they were derived from. If a second release's *code* differs in size
from the first anywhere before that address (a removed routine, a patched
bug fix, a different compiler/optimizer pass), every inline table living
after that point shifts by the resulting delta. Reading at the original
(unshifted) address doesn't fail — it's still valid, in-bounds bytes — it
just silently returns data from the wrong table, wrong pointer, or wrong
record. This is the same "cascading address shift" mechanism documented in
`fixed-offset-diff-across-builds-hides-pointer-shift.md`, but from the
opposite direction: that file is about *diffing* two builds at a fixed
address being misleading; this is about a *decoder* actively producing
wrong output when pointed at a second build without re-deriving its
addresses first.

**Confirmed on FFVI (SNES)** (`ceres` project, comparing the US release
against the Japanese original): a prior session had already found and
documented that the JP ROM's bank-`C0` field-program code is 206 bytes
shorter than the US ROM's (it lacks a DTE-decompression routine the JP
release doesn't need), and that every inline table in that bank shifts by
that constant delta. A later session ran the existing, already-confirmed
field-sprite decoder unmodified against the JP ROM — exactly the call the
US pipeline uses — and it completed with no error, producing a
plausible-*looking* 15-sprite atlas (recognisable as roughly humanoid
shapes at thumbnail scale). Only a full byte-exact RGBA diff against the US
render (expected identical, since the underlying raw graphics bank
independently needed zero shift) revealed 4,701 of 6,144 bytes wrong across
14 of 15 sprites — the decoder's pointer-table addresses were reading 206
bytes into the wrong place. The fix: parameterize the decoder with an
addresses argument (default = the original hardcoded constants, so every
existing call site keeps working unchanged) and a second constant set
derived from the already-known shift; verify byte-exact (not just "looks
like a sprite") against a value already independently confirmed to need no
shift.

**The fix, generalized:** before trusting *any* decoder call against a
second release/revision/region ROM of the same game — even one whose data
tables are otherwise confirmed identical — check whether its address
constants point into code, not just data. If they do, and any code between
the file's start and that address could plausibly differ in size between
releases (a removed feature, a bugfix patch, a different assembler/compiler
version), verify byte-exact against an oracle that's independently known to
need no shift (a data bank in a different, code-independent memory region;
a cross-checked reference extractor's own output for that release) — never
treat "it ran without throwing" or "the render looks plausible" as
sufficient verification for a second-release reuse.
