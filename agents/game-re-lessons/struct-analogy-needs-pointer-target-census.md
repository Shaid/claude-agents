# Cross-project struct-shape analogy needs a pointer-target census, not just field-count matching

**When it bites:** A newly-found record type has the same coarse shape as
an already-confirmed format from a sibling project or engine family — most
commonly "N internal pointer/offset fields patched or resolved at load
time" resembling a known 3D model header (`callback_fn + vtx_program +
face_list`-style) — and the temptation is to assign it the same semantic
role on the strength of that shape alone, especially when the sibling
format is well-documented and the new one isn't. Same trap, code side: a
disassembly grep for a known pipeline's distinctive instruction-sequence
signature (e.g. a `MULS`+`ASR`+`ADD` dot-product/rotation-matrix idiom)
gets a real hit, tempting the conclusion that the whole pipeline it
belongs to (e.g. full 3D scene rendering) is present too.

## What went wrong

Wings (hunter project) has a content type (`flags1=0x06`, "composite
struct") that decompresses to a small struct with exactly 3 internal
pointer fields, patched at load time via the same generic pointer-fixup
helper a sibling content type also uses. This coarsely matches Carrier
Command's confirmed 3D model header shape (3 pointers: callback/vertex-
table/face-list) and Epic's LOD-section vertex/display-list chain — both
already-solved formats in the *same* project family's corpus. Given
independent ground-truth knowledge that Wings' main gameplay mode is true
3D dogfighting (unlike its other, confirmed-2D, modes), "this is the 3D
model record" was the obvious hypothesis to test first.

It was wrong. Resolving every one of the 516 real corpus instances'
pointer fields to their TARGET frame's own content-type tag (cheap: only
the target's *type*, not its payload, needs decoding) showed 100% of
active pointers at every one of the 3 field offsets resolve to either
ANOTHER instance of the *same* record type (a "next"-pointer linked list,
83% literally `self+1`) or to an already-confirmed unrelated 2D sprite
format — zero references, in 516/516 instances, to the bulk numeric-array
type that would actually hold vertex/face data. The struct's size was also
fixed (only 2 possible sizes in the whole corpus, never scaling with
content complexity) — a fact that alone should have been a yellow flag,
since a real per-model geometry header's size doesn't stay constant
across simple and complex vehicles.

## The fix

Treat a cross-project (or cross-format) structural shape match as a
hypothesis to test cheaply, not as evidence on its own. The decisive test,
when the format already has *some* pointer/index/reference mechanism (most
container formats do, once even partially reverse-engineered), is a
**corpus-wide census of what every instance's reference fields actually
resolve to** — their target's type/role, not a handful of manually
inspected samples. A real 3D model header's pointers should overwhelmingly
target vertex/index-array content; if instead they target the *same*
record type (a chain/list) or something already known to be unrelated
(here, an already-fully-confirmed 2D sprite format), the analogy is wrong
regardless of how compelling the field-count/offset shape looked at the
outset. This generalizes past 3D formats: any time "record X looks like
already-solved format Y because it has the same number/shape of
pointer-ish fields" is the basis for a semantic label, resolve the
pointers corpus-wide before writing the label down.

**A third variant needs the pointed-to bytes actually decoded, not just
resolved to a type/role.** Knights of the Round (CPS1, `kolbold` project):
a mechanism found while tracing a boot-init routine looked like a strong
candidate for "the per-level palette selector" this project had been
searching for — structurally, it paralleled an already-confirmed in-game
palette-copy pathway almost exactly (an index register selecting one of
several ROM addresses from a pointer table, each address landing inside
the assembled ROM, each feeding the same kind of copy-to-hardware-palette-
RAM loop already confirmed elsewhere). Decoding two of the pointer table's
actual targets with the project's own already-confirmed palette-word
format showed near-uniform pure-white blocks with one distinct terminal
color — the shape of a screen-flash/transition-effect frame sequence, not
distinct per-stage color schemes — and the index register itself turned
out to be generic scratch reused by 100+ unrelated call sites elsewhere in
the ROM (see `locally-indexed-substructures.md`), not a stable "current
stage" variable. No sibling-project or cross-format shape was involved
here at all — the false lead came purely from within-game structural
parallelism to an already-solved mechanism. The fix is the same: resolve
and decode what the candidate mechanism's own data actually *is* (using
formats/decoders already confirmed for this exact game) before writing up
a semantic hypothesis, even when the surrounding structure looks like an
obvious fit for what you were hoping to find.

**The same trap has a code-side twin: a matched instruction-sequence
signature isn't proof of the same scope either.** The same Wings session
also grepped all disassembled code for the exact `MULS`+`ASR`+`ADD`
dot-product/rotation-matrix shape that confirmed Carrier Command's real
3D transform pipeline. It found a genuine match — a real 3×3
rotation-matrix build-and-apply routine, same instruction shape, same
fixed-point scale-down idiom. But tracing its actual inputs and caller
showed it only ever rotates a small, fixed 16-point hardcoded shape by a
heading angle — a cockpit instrument gauge (compass rose/attitude
indicator), not a streamed vertex buffer or exterior vehicle geometry
(confirmed absent by a separate, complementary check: zero
`MOVEM.W (An)+` sequential-vertex-read instructions and zero
perspective-divide-shaped `DIVS.W` anywhere in the binary). A matched code
signature tells you a *technique* is present somewhere in the binary; it
doesn't tell you *what data* it's wired to without tracing the actual
caller/inputs — same discipline as the data-struct case above, just
applied to instructions instead of fields.
