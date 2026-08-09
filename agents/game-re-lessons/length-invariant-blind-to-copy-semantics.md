# A "0 bytes left over" length invariant only verifies an LZ-style decoder's length grammar, not its copy semantics

**When it bites:** an LZ77/ring-buffer-style decompressor has been marked
CONFIRMED on the strength of a corpus-wide length-conservation check ("every
file/group decodes to exactly the target byte count, 0 leftover, N/N"), and
you're about to trust its *content* (not just its length) for a new,
independent use — especially when a second, differently-shaped oracle for
that same decoder starts failing on a majority of its inputs despite a
structurally sound model of the new thing being decoded. Also bites when a
prior corpus-wide pattern/shape scan (looking for a palette, a specific
struct, any content-shaped target) came back negative and predates a fix to
a shared decoder in its dependency chain — see the second instance below.

## What went wrong

Wings (Amiga)'s Mode-B BOLT group decompressor was verified "0 leftover
bytes across all 352 real frame-bearing groups" using only each group's
directory-declared total output length as the target — no fudge factors,
and it held with zero deviations. That check, plus one legible rendered
bitplane (a title-screen logo), was treated as sufficient to call the codec
CONFIRMED. It shipped with two real bugs: the back-reference "distance"
field was resolved as an absolute ring-buffer position instead of a
*relative* offset (`(curpos - distance) & windowMask`), and one control-byte
range's copy direction was documented as backward when its actual handler
left the direction register at the shared forward default. Both bugs
corrupt copy **content** while leaving every emitted byte **count**
untouched — an LZ copy's length is fixed by the control byte alone,
completely independent of *where* it copies from or *which way* it walks.
A length-conservation check is therefore structurally blind to this entire
class of bug: it can prove the grammar (how many bytes each control byte
consumes/produces) is right while saying nothing about whether the *bytes
themselves* are right.

The bugs were caught only when unrelated, subsequent work — decoding a
different frame type's own byte-count identity (a struct's self-described
field lengths summing to its container-declared size) — kept failing for
~83% of a large, structurally sound corpus despite the field model itself
checking out on every axis that didn't depend on decoded byte *values*. A
full premise audit of the *shared decoder* (not the new frame-format code
being blamed) found both bugs in under an hour.

## Fix

Treat "N bytes in, N bytes out, 0 leftover" as proof of an LZ-style
decoder's **length/grammar** correctness only, never its **copy semantics**
(direction, absolute-vs-relative distance resolution, window indexing).
Get an independent, *content-shaped* oracle before calling the decoder done
— a legible render is one, but only for the code paths it happens to
exercise; a single successful render does not clear code paths a small
input sample doesn't reach (here, most of the corpus never used the two
buggy control-byte ranges' problematic combination until a much larger,
diverse frame population was decoded through them). If a second, unrelated
decode built on top of an already-"confirmed" codec keeps producing
plausible-shaped-but-wrong values across a large population despite a
structurally sound model, audit the codec's own copy semantics before
assuming the new model is at fault — the tell is a real, population-level
correlation (e.g. success rate splitting cleanly on some input field) with
*no possible mechanism in the code you're building*, which means the
mechanism is upstream, in bytes you're trusting as already-correct input.

## Second confirmed instance — a corpus scan run against corrupted output looks like a clean negative

A follow-up Wings session ran a corpus-wide RGB4-palette-shape scan against
this exact decoder's output *before* the distance/direction bugs above were
fixed — 5 different search angles, all negative, documented as "palette
not found anywhere in the corpus." The palette (a `flags1=0x00` BOLT frame
type never even considered a candidate) was sitting in the same corpus the
whole time; every byte range the scan checked was silently corrupted by the
same two content-preserving-length bugs. Re-running the *same class* of
scan — broadened to cover every group's full decompressed output, not just
the specific frame types/sizes the first pass suspected — against the
corrected decoder found it on the first pass. Lesson: a "scanned the whole
corpus, found nothing" negative that predates a shared decoder's own
bugfix is not evidence the target is absent — it's evidence the decoder was
still broken when the scan ran. Don't just re-run a stalled corpus scan
after fixing a shared upstream decoder; broaden it too, since the earlier
negative may also have been scoped by a guess (e.g. "the palette must be in
frame type X, size Y") that a genuinely fresh, wider pass wouldn't repeat.
