# An identical minimal header shape can belong to two structurally different container formats

**When it bites:** a byte-header census across a directory of unfamiliar
`.bin` files finds many files sharing one small leading field shape (e.g.
`<u32, u32, u32, u32>`), and you're about to assume they're all the same
container just because the first N fields have the same types/widths.

Fire Emblem Warriors (2017, `~/Development/chimera`): a census across
`common/action/etc/`/`nx/action/etc/` found ~20 files all opening with four
little-endian `u32`s. Fitting them to "flat fixed-stride record array"
(`count`, `stride`, then `count x stride` bytes back-to-back) worked for
15/20 — confirmed byte-exact via `16 + count*stride === fileLength`, and
independently corroborated by a monotonic leading-record-ID census
(348/349 consecutive `id, id+1` pairs in one file). The other 5 files share
the *identical* leading four-`u32` shape but are a completely different,
already-known container (`slotCount`, `firstBlockStart`, then a
`{length, cumulativeEnd}` slot table) — their first field even happens to
look like a plausible small "count" (2), and their second field a
plausible small "stride" (20), so a header-shape match alone would have
silently misparsed them.

**The generalizable move**: when two candidate container interpretations
share the same leading field *types*, don't let header-shape agreement
stand in for confirmation — apply each format's own strict, whole-file
invariant (here: `16 + count*stride === fileLength` for the flat-array
reading vs. the slot table's own `cumulativeEnd[i] - length[i] ==
cumulativeEnd[i-1]` chain for the pack reading) and require it to hold
before committing to either parse. A parser for the newer/rarer format
should return `null`/reject rather than silently succeed on bytes that
belong to the other one — exactly what let the two populations be told
apart automatically here (15 files failed the pack chain-validation, 5
failed the flat-array size check, with zero files passing both).
