# A multi-variant resource's contiguous id span can be addressed by a different encoding in each consumer

**When it bites:** an already-solved indirection resolves "id N doesn't
exist directly, but N is exactly one past (or a small multiple past) a
sibling entry with `variantCount > 1`" for one consumer (a renderer, a
texture-bank index), and a *second*, independently-discovered consumer of
the same underlying resource (a script/bytecode reference, a different
directory, another table) produces ids that don't exist directly either —
before concluding the second consumer's ids are a decode error, check
whether they're the same contiguous-span phenomenon under a *different*
arithmetic encoding.

A resource that legitimately expands into several stored variants (a wall
texture with more than one "wallset," a sprite with more than one palette
revision) still needs exactly one id per logical reference elsewhere in the
game. Different subsystems built by different code paths (or different eras
of the same codebase) are not obligated to encode "variant K of base id N"
the same way. Confirmed on the SSI Gold Box engine (`crawl` project): the
already-solved WALLDEF texture-render side encodes a multi-wallset entry's
variants as `10*baseId + (variantIndex+1)` (`resolveCompositeWallId`), a
composite decimal scheme. The ECL bytecode's own wallset-slot-binding
values for the *same* multi-wallset entries turned out to use a completely
different, simpler convention: a flat, contiguous id range
`[baseId, baseId+variantCount)` — id 17 (2 wallsets) claims ids 17 AND 18,
with no `10*` multiplication at all. Seeing "18" in the ECL trace and not
finding it in `WALLDEF.GLB`'s own directory looked identical to a decode
bug until the multi-wallset-entry pattern was recognized from the
already-solved side.

**Fix:** when a second consumer's resolved ids don't exist directly in a
table you've already fully catalogued, don't just distrust the new
decode — cross-check every "missing" id against the *positions* of any
already-known multi-variant entries in that table (their base id + variant
count), under more than one plausible arithmetic (composite/decimal
encoding, a flat contiguous span, a bit-packed index) before concluding
it's wrong. Generalize the existing resolver to a shape both consumers can
share (here: `resolveFlatWalldefId`, built from the already-established
`wallsetCount` field, sitting alongside — not replacing — the older
composite-id resolver) rather than maintaining two independent,
un-cross-checked interpretations of the same underlying table.
