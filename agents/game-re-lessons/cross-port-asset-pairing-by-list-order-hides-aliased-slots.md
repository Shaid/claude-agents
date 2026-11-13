# Pair cross-port assets through a structurally-twin index table, not by list order

**When it bites:** one port's records name N slots per object (e.g. 3 view
tiers x 4 facings + poses), the other port stores M <= N distinct bitmaps,
and you pair them by walking both lists in order. It looks right wherever
N == M, because ordinal order happens to coincide there. Where N > M, the
surplus names get patched up as "aliased"/placeholder entries and every later
name in that record shifts onto the wrong bitmap. Nothing fails structurally,
so the mispairing survives.

## Check / fix

1. Look in the **source** port for its own per-slot index: a frame directory
   or blit-descriptor table where the same bitmap offset recurs for aliased
   slots and mirrored slots carry a flag rather than their own pixels.
2. If its shape matches the target's slot layout, pair **slot-to-slot through
   it**, and assert that each target name resolves to exactly one source
   bitmap.
3. Validate on entries both ports actually ship (dimension equality per slot)
   **with a rotated-pairing null control** — a real pairing should beat the
   rotated one by a wide margin.
4. Check that any per-slot geometry the target stores (draw offsets, widths)
   becomes plausible across *all* slots, not only the ones that already
   matched. A residue of outliers under list-order pairing is the tell.

## Canonical example

Black Crypt DOS `crypt.exe` creature records (12 named slots: N/E/S/W x 3
tiers + 2 poses) vs the Amiga per-level monster files. Each Amiga file's
42-entry directory turned out to be 3 creatures x 12 slots at `c*12+s`, plus
poses at `36+2c`, with W stored as a type-flagged mirror of E. Pairing through
that directory gave 14/14 dimension matches on shipped creatures (rotated
control 2/14), resolved all 11 "aliased" names exactly (e.g. one creature's
`1 N` is its `1 E` bitmap), and took draw-offset/width outliers from 21/276
under list-order pairing to 0/279.

**History:** 1 instance (crawl / Black Crypt DOS<->Amiga, 2026-11-13).
