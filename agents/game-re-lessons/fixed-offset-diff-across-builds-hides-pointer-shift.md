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

**The same cancellation recurs one level deeper, inside a single resource's
own internal numbering, not just across a pointer table** — confirmed a
second time on the same FFVI US/JP comparison. A field-map raw tile bank
had one new tile inserted mid-bank in the JP release, shifting every later
tile's byte position by one tile-width; the paired tile-formation
("meta-tile") table's `tileNum` references into that same bank were
correspondingly bumped by exactly +1 for every affected reference (found by
printing the differing meta-tile entries directly — every one was a pure
`tileNum+1` with identical palette/flip/priority bits, not a coincidence).
A naive raw-byte diff of the tile bank, and a naive per-entry diff of the
tile-formation table, both looked substantially different (dozens of
differing entries out of a few hundred). But resolving *both* through the
real decode pipeline — each ROM's own tile bank together with that same
ROM's own tile-formation table — produced **pixel-identical** rendered
output (0 diff pixels across a 1024x1024 map render) for the two map
screens checked: the insertion and the renumbering exactly cancel out. Same
lesson, one more layer down: when a data table shows a byte/index-level
diff that has a plausible size-driven cause (one inserted tile, one added
string, one resized sub-record), check whether every other reference *into
or after* the changed region was correspondingly renumbered by the build
process before concluding the raw diff represents real content change —
the only reliable way to know is to render/resolve through the real
pipeline (both ROMs' own paired tables), not to eyeball the raw byte or
index diff in isolation. (A decoder itself — not just a manual diff — can
also fall victim to this same shift if it embeds one release's *code*
address as a bare constant; see
`decoder-address-reuse-across-rom-release.md` for that specific angle, and
`known-differences-list-not-exhaustive-without-full-diff.md` for why a
"known differences" list from targeted checks like these shouldn't be
assumed complete.)
