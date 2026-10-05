# Re-serializing from an interchange format that copies shared table rows per consumer grows the native shared table — reuse the donor's rows to get byte-identity back

**When it bites:** building a native-format writer (G1M/any KT container,
any format with a shared matrix palette, string pool, colour table, vertex
declaration table) fed from an interchange format that stores one copy of
the shared data per consumer (glTF: one `inverseBindMatrices` accessor per
skin, one material per primitive), and the round-trip diff shows the
shared table LARGER than the original (rows duplicated) with every
downstream index/count field (FM1G-style header counts, `reserved`
fields that mirror the table size) differing as a consequence, while the
geometry itself is exact.

The interchange format has already flattened the sharing; naively
re-encoding "one row per consumer" cannot reproduce the original table no
matter how correct each row is. The fix is not a smarter dedup on the new
rows alone (which still cannot recover the original row ORDER) but a
donor-anchored reuse: whenever a re-encoded row equals a donor row within a
tight epsilon (float32 round trip: `<= 1e-6` per component), emit the
donor's index instead of appending. This restores byte-identity on the
shared table AND doubles as a free oracle — a row that fails to match any
donor row when the geometry round-tripped exactly means the decode/encode
chain for that table is not exact.

**Confirmed** on Fire Emblem Warriors hero packs (`~/Development/chimera`,
`docs/model-import-pipeline.md` Milestone 6 step 3): re-importing Lianna's
part blocks from their own glTF export grew slot 8's `MM1G` from 76 to 137
rows and shifted `FM1G` fields 13/14 and `reserved3` with it; reusing donor
`matrixId`s through a per-row match (`donorMatrixMap` in
`src/data/formats/gltf-g1m-parts.ts`) made `MM1G` byte-identical on every
part, leaving only the strip-to-list index growth the interchange format
genuinely forces.
