# A byte gap between a root header and its first named sub-section can be a pointer/offset table, not a repeat of the sub-section's own header shape

**When it bites:** a container format's sibling sub-format (already solved
for one instance — its sub-sections are a chain of `magic+version+size`
blocks summing exactly to the container's declared size) is marked
"identified but internally unresolved" for a second instance, on the
grounds that the byte region right after the shared root header doesn't
match the first sub-format's known sub-header shape (wrong field width, no
ASCII version where one was expected, etc).

The byte-count match is real, but the *interpretation* can be wrong: that
region can be an **offset table** — `sectionCount` fixed-size slots of
`{tag, absoluteOffset}` — that *points at* the real sub-section headers
located elsewhere in the file, rather than being the first sub-section's
own header. A raw scan for the expected header shape at that fixed gap
position then correctly finds "wrong shape" and stalls, because it's
looking at a pointer, not the pointee.

Confirmed on Fire Emblem Warriors: Three Hopes's `MN1G` container
(`chimera` project, `docs/few-threehopes.md`, `linkdata-g1x.ts`). Its
sibling `TB1G` closes by literally walking `magic+version+size` blocks
starting right after the 32-byte root header. A prior pass tried the same
thing for `MN1G` at the same offset, found an 8-byte-repeating shape with
no 4-ASCII-digit version field, and correctly concluded "this variant's
sub-header shape doesn't match TB1G's — sub-section offsets unresolved."
The 8-byte repeat *was* real structure — just not a header: it was
`sectionCount` (from the root header) x `{magic[4 ASCII], u32
absoluteOffset}` slots, each pointing at the real 12-byte
`magic+version+size` section header located later in the file (which *did*
use the exact same shape as `TB1G`'s sub-sections, version field included).
The chain closed byte-exact — `slot[i].offset + slot[i].size ===
slot[i+1].offset`, 0 deviation across 24/24 real instances — once the
target offsets were followed instead of parsing the gap region in place.

**The general move:** when a candidate sub-header position in a gap region
doesn't match the shape you expect, before concluding the sibling variant
uses a genuinely different/unresolved header format, check whether the gap
region's fields look like `{tag, offset}` pairs (a short tag followed by a
plausible-looking byte offset — sanity-check it against the file's own
size) rather than `{tag, version, size}` triples. If so, dereference each
offset and re-run your already-working header check *there* — the sibling
variant may use the exact same inner header shape as the one you already
solved, just reached through one extra level of indirection the first
instance didn't need.
