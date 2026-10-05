# A fixed-stride scan starting from a computed anchor offset silently misses the real target when the anchor isn't itself aligned

**When it bites:** writing (or reviewing) a scan that walks a byte gap
between two known anchors in fixed steps of N (commonly 4, for a
self-length-prefixed or word-aligned record) to find where a real
structure starts — especially when the scan's starting offset is `gapStart`
itself (the end of a preceding variable-length block: a compressed span, a
variable-length header, anything whose length isn't guaranteed to be a
multiple of N) rather than a value already known to be N-aligned. This is a
**false-negative** trap, not a false-positive one: the scan reports nothing
found (or silently finds nothing where something real exists), with no
error, no crash, and no obviously wrong output — just quiet absence.

Stepping `off` by N starting from an unaligned `gapStart` only ever tests
offsets congruent to `gapStart mod N` — it can never land on the true
N-aligned target if `gapStart mod N != 0`. Whether the bug manifests
depends entirely on an accident of the preceding block's own length, which
makes it exactly the kind of bug that "works for some inputs, silently
fails for others" and survives code review and even partial verification
undetected.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project,
`docs/valkyrieprofile/psx/data-structure.md` §13.7.1c): a shared decoder's
raw-record gap scan (`decodeBattleBundle` in
`tools/shared/psx-vp-battle-bundle.ts`) searched a bundle's byte gap for a
self-length-prefixed §13.3a animation-record block, stepping by 4 from
`gapStart` (`i + 16 + header.compressedSize` — an SLZ span's end, only
coincidentally 4-aligned since `compressedSize` depends on the LZSS-family
codec's output). Of 26 structurally-identical playable-character bundles
whose animation record was independently proven present in **every one**
of them by a separate, correctly-aligned probe, the buggy scan found it in
**exactly the 5** whose preceding span happened to already end on a
4-byte boundary (`gapStart % 4 === 0`) and silently missed it in the other
21 — including the specific character (Lenneth) a downstream bug report
was filed about. The downstream report concluded she had a unique,
missing-texture "engine gap" needing a new cross-slot compositing feature;
the real cause was one shared-decoder alignment bug affecting 81% of an
already-solved, self-contained-by-design population. A prior documentation
pass had even re-derived and written up the *symptom* ("not the right
record shape") as if it were new structural evidence, because it inherited
the same buggy decoder rather than re-deriving the check independently —
see `sibling-field-comment-as-free-semantic-oracle.md` for the general
shape of trusting an inherited negative without re-deriving it.

**Fix:** never start a fixed-stride scan from a computed/derived offset
directly — snap it to the next true boundary first:

```ts
const alignedStart = anchor + ((stride - (anchor % stride)) % stride);
for (let off = alignedStart; /* ... */; off += stride) { /* ... */ }
```

Add a regression test that deliberately constructs a preceding
block/anchor whose length is **not** a multiple of the stride (e.g. an
SLZ/compressed span with an odd payload length), so the aligned-vs-
unaligned distinction is exercised by the test suite rather than only by
whichever real files happen to hit it.

**Two related but distinct failure shapes**, for disambiguation:
`naive-byte-window-address-scan-crosses-instruction-boundary.md` is a
scan that checks *every* offset and produces **false positives** from
misaligned coincidental byte concatenation; `terminator-scan-must-be-
record-aligned.md` is a variable-stride *record walk* (not a fixed-N
scan) whose blind terminator search finds a **false positive** inside
live record data. This lesson is the mirror case: a fixed-stride scan
whose *starting point*, not its step size or per-record logic, is
mis-anchored, producing a **false negative** — quiet absence, not a
wrong match.

**Broader lesson about the downstream report:** when a bug report frames
a defect as unique to one instance of a large, structurally-identical
population ("this one character's data is special/missing"), check the
population-wide pass/fail rate for the same signal before accepting a
per-instance explanation. A shared-decoder bug that only manifests for a
byte-count-dependent fraction of a corpus looks, from any single failing
instance's point of view, exactly like a real per-instance content gap.