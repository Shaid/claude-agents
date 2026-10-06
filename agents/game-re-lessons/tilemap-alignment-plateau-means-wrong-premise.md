# A tilemap reconstruction that plateaus around half the cells matched has a wrong premise, not a wrong offset

**When it bites:** you are rebuilding stage/level maps from metatile and
attribute tables and scoring them against a reference (VRAM dump,
screenshot, emulator capture). The offset/stride/base search climbs to
about 50% of cells matching and then stops improving, whatever you tune.

## The trap

A stuck partial score feels like being close, so the natural move is to
keep sweeping offsets and strides. But an offset error usually scores
near 0% or near 100%. A stable middle plateau means the *shape* of the
model is wrong in a way that happens to agree on part of the data,
typically on symmetric, blank, or single-tile cells. More offset search
cannot fix it.

## Check / fix

Stop tuning numbers and audit the premises, ideally with an execution
oracle. Run the game's own map init/stream routine under a bare CPU core
(Method §5: flat memory, a sentinel return, unknown calls raise), then
diff the VRAM/name-table cells it writes against your reconstruction cell
by cell. The pattern of mismatches points at the broken premise. Common
wrong premises:

- **Row order.** The map is stored bottom-up, and flips apply per
  metatile, not per tile.
- **Attribute granularity.** There is one attribute byte per metatile,
  not one per tile.
- **Record size.** There is more than one record size, for example
  variants that carry extra collision bytes.
- **Dimensions.** Row count is not stored. Derive it from the gap
  between the map and the next table.
- **Index width.** A `.w` index past `0x8000` sign-extends
  (`moveq-sign-extend-lsl-w-wraps-negative-index.md`).

The harness only needs to be bounded to one routine. It is a static
oracle, not a boot.

## Canonical example

A 68k stage-map streamer (2026-10). Alignment search plateaued at about
50%. Running the real stream routine in a Musashi flat-memory harness
and diffing VRAM settled five independent premises in one pass: bottom-up
storage with per-metatile flip, one attribute byte per metatile, 17-byte
and 33-byte record sizes, row counts taken from map-to-table gaps, and a
sign-extended `d8(An,Dn.w)` index splitting reads past `0x8000`. None of
these was an offset error.

**History:** 1 instance (2026-10).
