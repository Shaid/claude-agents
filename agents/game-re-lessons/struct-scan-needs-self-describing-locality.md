# Blind struct-pattern scanning only converges when the format is self-describing

**When it bites:** about to blind-scan a whole file for a confirmed struct's byte signature (a known field value, e.g. a command/type word) to find more real instances of that record type.

A struct layout confirmed correct for one record *family* (e.g. validated
corpus-wide by reading a fixed relative offset from every hit an existing,
unrelated scanner already found — see the Method §4 technique for how cheap
that validation is) does not mean you can find *sibling* records of a
different variant the same way. Two properties have to both hold for a
blind whole-file scan to converge on real hits instead of drowning in false
positives from misaligned code/data:

1. **The struct's own signature value is rare enough** that a raw byte/word
   match isn't dominated by chance hits (a fixed 16-bit constant occurring
   at ~1-in-65536 density across a multi-MB file still produces hundreds of
   false positives once you count every possible alignment).
2. **The record has a self-describing locality or length convention** that
   lets you cheaply validate a candidate hit beyond "the signature matched"
   — e.g. a size field whose value matches the real distance to a
   plausible payload, or (as with a self-describing-length compressed
   format) a payload that itself decodes cleanly and to a round size.

Confirmed the failure mode this way: a Genesis resource-descriptor struct's
field offsets were validated corpus-wide (179/179 known instances reading
the same expected command value at the hypothesised offset — strong
validation). But a *different* command value of the same struct (referring
to a second, un-self-describing-length compressed format instead of the
already-corpus-scannable first one) produced **zero** real hits under blind
whole-file scanning, even after tightening filters using the *other*
variant's locality convention (a fixed small-distance offset between a
self-pointer field and its target, itself only discoverable because that
other variant's target format has a length header making it independently
scannable in the first place). 249 and 197 raw signature-word matches
across two ROMs, all with wildly implausible surrounding field values —
zero real records recovered.

The fix is not a tighter filter — no filter converges when the underlying
premise (payload has a discoverable locality/self-description) is false for
this record variant. Real instances have to be found via disassembly /
pointer-chase tracing from actual code (the struct's real callers, index
tables, etc.), the same way the *first* instance that let you infer the
struct layout was found — not by scanning for more of the pattern.

## Positive confirmation: the same principle also explains when a blind scan *does* converge

Carrier Command (Amiga, `hunter` project) had an earlier session's
whole-file scan for a per-vehicle 3D model stream, anchored only on one
weak field (`vertex_count == 60`, i.e. the raw byte pair `00 3C`) plus a
loose face-count/index-bounds check: 212 raw byte-pair matches, 69 passing
the loose secondary filter, with no way to tell real hits from coincidence
— exactly the "signature not rare enough + no real locality check" failure
this file describes. A later session replaced that anchor with the format's
**full recursive grammar** (a self-terminating BSP-tree walk requiring
every branch to resolve in-bounds, every face index below the record's own
vertex count, and zero degenerate faces) — i.e. added the missing
self-describing-locality property this file calls out as the deciding
factor. Same file, same general region, same underlying data: 69
uninterpretable candidates collapsed to exactly 4, all independently
verified real. The two cases aren't in tension — they're the same
principle from opposite sides: a scan without a self-terminating/
self-validating structure to check against cannot converge no matter how
much you tighten value-range filters (the Genesis case above), but a scan
*with* one (recursive parse success itself *is* the locality check) can
converge sharply even starting from a weak initial byte anchor.
