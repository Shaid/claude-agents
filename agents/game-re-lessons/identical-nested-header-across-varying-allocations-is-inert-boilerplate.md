# A nested sub-container header that's byte-identical across every sibling entry, regardless of real allocated span, describes a DECOMPRESSED image — it is not inert boilerplate

**When it bites:** a directory/index entry points at a span that itself
starts with what looks like a complete, self-describing nested-container
header (magic + declared total size + declared block/entry count), the
outer directory's own allocated span for that entry genuinely *varies* from
entry to entry, but the nested header's declared size/count fields come
back **exactly the same, byte for byte**, at every single entry — especially
if that declared size is sometimes larger than the outer span actually
allocated to it (which would be internally impossible for a container that
only occupies its own declared extent, *if* the header described the bytes
actually stored there).

> **Correction (2026-08-30):** this file previously concluded that a
> constant header repeated across varying real allocations must be inert,
> copy-pasted authoring/build-tool boilerplate that the game's own loader
> never reads. **That verdict was wrong** and cost a full pass before a
> `re-codebreaker` escalation (real disassembly of the games' own 68000
> loaders) found the true explanation, which was then independently
> re-verified against real corpus bytes. The header is genuine and IS read
> by the game — it just describes the container **after decompression**,
> not the bytes actually stored on disk at that span. Every wall bank in a
> given game decompresses to the identical shape (hence the identical
> `totalSize`/`blockCount` across all sibling entries), while the outer
> directory allocates each entry only as much *compressed* space as that
> specific bank happens to need (hence the varying, often-smaller, real
> span — and exactly why the declared size can legitimately exceed it).

## What happened

Confirmed on the SSI Gold Box "GLIB" container family (`crawl` project,
`docs/goldbox-glib-format.md`): each of Curse of the Azure Bonds, Secret of
the Silver Blades, and Pools of Darkness ships a "per-wall-id nested tile
bank" file (`8X8D.TLB`) whose outer directory gives each wall-id entry a
real, *varying* allocated span (e.g. Curse's entries range 1,634–2,010
bytes). Every one of those spans opens with what parses as a complete
nested-GLIB header — but that header's declared `totalSize`/`blockCount`
pair is **the identical constant across all 18 entries in the file** (Curse
and Secret both show `totalSize=3660, blockCount=70`; Pools of Darkness
shows a different but equally constant `totalSize=15488, blockCount=257`
across all of its own entries), and the declared size exceeds the real
outer-allocated span for several entries.

A first pass concluded this must be inert boilerplate and stopped there
(the verdict this file used to record — trusting the header as an offset
table produced garbage, and the "step back, don't trust it" instinct was
sound as far as it went). The real explanation needed one more step: the
high byte of the container's own `flags` word — a field the format doc had
*already parsed* and logged as "varies corpus-wide, no confirmed meaning" —
is the compression method id (`0` = stored, `3` = 10-bit LZW, `5` =
byte-oriented LZ77; both codecs confirmed by disassembling the games' own
68000 loaders). Decompressing each entry's payload BEFORE treating its
header as authoritative gives, for all 329 nested containers across the
three titles, a header that matches its own decompressed body exactly — 0
errors, every decompressed body a well-formed self-describing container. A
byte-exact cross-title check (the same tile bank shipped uncompressed in
one title and LZ77-compressed in another) confirmed the decompressed bytes
are correct, not just internally self-consistent.

## The fix / general rule

Before concluding a "self-describing" nested header is inert authoring
boilerplate because it stays constant across sibling entries with varying
real allocations, **check whether the payload is compressed** and the
header is actually describing the post-decompression image:

1. A header that's byte-identical across many entries whose *decompressed*
   content-shape is genuinely the same (same kind of resource, same table
   layout) is completely ordinary — that's just what a fixed decompressed
   record shape looks like. It's the *varying real allocation paired with a
   constant declared size* that's the tell, not the constancy alone.
2. Look for a compression-method discriminator hiding in a field you've
   **already parsed and dismissed** as "meaning not confirmed" or "varies,
   no known effect" — not a brand-new field you haven't looked at yet. Spare
   bits left over after the bits you've already decoded are a natural place
   for a format to smuggle in one more small enum, and are easy to overlook
   exactly because you already assigned that field a partial meaning and
   moved on. (See `flags-field-correlation-false-lead-vs-declared-size-
   check.md` for the same field, in this exact format, being investigated
   for an unrelated question first — it correctly ruled out "flags predicts
   truncation" without anyone yet asking what flags' high byte *does* mean.)
3. Don't stop at "the declared size doesn't match the physical container
   it's inside" — that's evidence of a size *mismatch*, not evidence the
   size is *meaningless*. A decompressed-image header is the single most
   common reason for that specific mismatch shape (declared size ≥ real
   allocation, by a game-title-consistent ratio) in any format that stores
   both a directory (with real, varying compressed lengths) and per-entry
   self-describing sub-headers (with the decompressed shape).

This is the mirror image of `self-describing-length-field-mistaken-for-
corpus-constant.md` (there, a field that looked constant in a small sample
turned out to be real per-record data that varies once the sample grows) —
here, a field that stays genuinely constant across a *large*, *varied*
sample is real too, just describing a different (later, decompressed) stage
of the data than the one you're looking at on disk.
