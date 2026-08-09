# A byte size recurring across many unrelated resources can just be a known encoder's fixed-dimension output — not proof of shared/template content

**When it bites:** several *exact* decompressed/decoded sizes recur dozens
or hundreds of times across otherwise-unrelated resources or containers,
and that recurrence is being read as evidence the resources share content,
a template, or a common asset pool (e.g. "these bundles must reuse a
common rig/texture/part, that's why the sizes match") — before any of the
actual bytes at those sizes have been decoded and classified.

Valkyrie Profile (PSX)'s `raw-other` TOC slots bundle several `SLZ`
sub-blocks behind a small header; a set of `decompressedSize` values
(1,014 / 33,312 / 5,844 / 52,852 bytes, and later found to extend to
147,476 / 98,324 / 30,740 / 16,928 / 3,616 bytes and others) recurred
across dozens to hundreds of unrelated slots. Read at face value, this
looked like strong support for a "shared model + texture bundle" theory —
many different bundles reusing the same rig, the same texture page size,
the same part inventory. Actually decoding and classifying a representative
sample at *every* recurring size refuted this: the large recurring sizes
were confirmed PSX TIM textures at a handful of common fixed pixel
dimensions (256×128 4bpp, 128×240 8bpp, 64×48 8bpp, ...) — completely
different, unrelated pixel content at each instance, coincidentally
identical in byte count only because `width × height × bpp / 8 + headers`
is a deterministic function of *dimensions*, not of *content*. A game that
standardizes on a handful of texture dimensions will produce the same
handful of encoded sizes thousands of times over, with zero relationship
between any two same-sized instances beyond "happened to use the same
canvas size." (The smaller recurring sizes in the same corpus turned out to
be genuine, unrelated MIPS machine code and small metadata records —
further evidence the size clusters were a mix of unrelated content types
that happened to collide numerically, not a coherent "shared asset"
family.)

**The generalizable move**: treat a recurring exact size as a *lead*, never
as *evidence of shared content*, until representative samples at each
recurring size have actually been decoded and classified. If the resources
in question are known (or suspected) to pass through an already-solved,
general-purpose encoder elsewhere in the same corpus (a texture format, a
compressor with fixed block sizes, anything whose output size is a
function of a small parameter space rather than of content), check that
hypothesis *first* — it's usually cheaper to rule in/out than a new
"shared template" theory, and it's a common enough coincidence that it
should be the default suspect before a more exotic explanation. This is
the sibling trap to `decoded-classified-blob-never-tried-as-pixels.md`
(an already-classified blob nobody rendered) and
`tile-grid-dimension-needs-render-not-just-bytecount.md` (a byte-count
alone can't disambiguate multiple valid dimension pairs) — this one is
about the size *itself*, recurring across many different resources, being
mistaken for a content-relationship signal before any bytes were opened.
