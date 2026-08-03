# A fixed-address byte diff across two builds of the same binary can report near-total disagreement from one upstream size change

**When it bites:** comparing two builds of the same game (a US vs. JP
release, a 1.0 vs. 1.1 revision, two regional ROM dumps) at literal,
identical addresses, for a table that is itself a **densely packed array
resolved through a pointer/offset field** (a stencil-trimmed graphics
pointer table, a variable-length record array with no per-record padding) —
especially when the diff comes back "75-98% of bytes differ" for a table
you have independent reason to believe is otherwise unchanged between
builds.

A same-fixed-offset byte diff is only valid for tables whose absolute
address and stride are both provably identical in both builds. For a
tightly packed, pointer-indexed array, a **single** upstream change — one
resized resource, one added/removed instruction sequence, one changed
bitmask that alters a trimmed byte count — shifts every later record's
absolute address by a constant delta. Diffing at the same raw address after
that point compares record N in one build against a fragment of record
N-1/N+1 in the other, which looks like total disagreement even though every
record's actual, pointer-resolved content is byte-identical.

**Confirmed on FFVI (SNES), comparing the US and Japanese-original ROMs**
(`ceres` project): a fixed-offset diff of `MonsterGfxProp` (384 x 5-byte
packed gfx/palette/stencil pointer records) reported 88% of records
differing. Resolving each record through its own pointer field instead (the
same decode logic the project's confirmed extractor already used) showed
**377/384 (98%) were byte-identical** — the apparent divergence traced to
exactly one shared stencil bitmask gaining 2 extra tiles in the JP build,
which shifted every subsequently-packed monster's graphics offset by the
same constant delta. The same pattern hit a field-sprite pointer-table
family at a *different* granularity: the whole bank of code preceding it
was 206 bytes shorter in the JP build (a removed text-decompression
routine), so a raw fixed-address compare of the sprite tables showed
90-98% disagreement, while locating the tables via their own distinctive
byte-pattern signature (not a hardcoded address) and diffing from there
showed the tables — and the 208,896-byte graphics region downstream of
them — were **100% byte-identical**.

**The fix:** never trust a fixed-address diff across builds/revisions for a
pointer-indexed or variable-stride table without first checking whether the
apparent divergence rate matches the *count* of genuinely differing
records once each is resolved through its own pointer/offset field. If the
naive diff rate is suspiciously high (especially "everything after some
point differs" rather than "scattered records differ"), that shape itself
is the signature of a cascading address shift, not real content change —
re-diff through the pointer, not the raw address. This generalizes the
same-platform-cross-port case already covered by
`cross-platform-string-delta-reveals-stride-vs-offset.md` (which handles
"is the *table itself* at a different offset/stride on a different CPU
architecture") to the narrower, same-binary-format case of "two builds of
the identical container format, one resource resized, need the *records*
compared, not the table's own base address."
