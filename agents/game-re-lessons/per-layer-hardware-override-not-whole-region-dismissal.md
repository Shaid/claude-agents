# A per-game/per-hardware-revision remap function can be overridden for ONE layer and still real for its siblings

**When it bites:** a shared multi-layer video/tile system (sprites plus
several tilemap layers, all reading one gfx ROM region) has a documented
remap/bank-select mechanism that a prior pass dismissed as "not applicable"
or "not yet ported" for the whole region, based on checking (or assuming)
its effect on just one layer (usually sprites, since that's the layer
whose content is most visually obvious) — and you're about to build a tile
categorization, atlas boundary, or "which bytes does layer X actually
read" answer without re-checking that dismissal per layer, from current
source, on a newer hardware revision than whatever the dismissal was based
on.

## What went wrong

CPS1 and CPS2 share one gfx-ROM tile-index remap function,
`gfxrom_bank_mapper()` (`src/mame/capcom/cps1_v.cpp`), used by both the
sprite renderer and all three tilemap-layer `get_tileN_info()` getters. A
prior ddsom (CPS2) investigation's own docs said this function was "a
per-game ROM-bank remap; not yet ported — irrelevant to ddsom/ddtod, which
use flat unbanked gfx" — true for *sprites* on CPS2 specifically, but
stated as if it settled the question for the whole gfx region. It doesn't:
CPS2 defines its **own** `cps2_render_sprites()` (`src/mame/capcom/
cps2.cpp`) that bypasses `gfxrom_bank_mapper()` entirely for sprites (and
adds an undocumented replacement — 2 bits stolen from the sprite's own
Y-position word extend the tile code past 16 bits), while the three
tilemap-layer getters are **not** overridden and still call
`gfxrom_bank_mapper()` exactly as CPS1 does. The dismissal was accidentally
right for sprites and silently wrong (by omission) for backgrounds/UI/font
— reading the current driver source directly (fetched fresh, not relied
on from memory or an old summary) showed the function still resolves a
real, load-bearing, fixed-offset formula for those three other layers, and
that a fully legible in-game font renders exactly where that formula
predicts.

## The fix / the generalizable lesson

When a gfx/tile region is shared by more than one hardware layer (sprites
+ N tilemap layers is the common shape), treat a remap/bank-select
mechanism's applicability as **per-layer**, not as one fact about the
whole region — especially across a hardware-revision boundary (CPS1→CPS2,
or any "v2 of a chipset" family) where the newer revision is known (or
suspected) to override *some* subsystems' rendering code while leaving
others shared/unmodified. Before trusting an old "not applicable here"
note: (1) fetch the current authoritative source for the *specific*
revision in play (not the shared base engine's docs alone), (2) check
whether that revision defines its own override for the *specific*
draw/render function the mechanism feeds, one function at a time (sprite
draw vs. each tilemap-layer info-getter are usually separate functions and
can be overridden independently), and (3) if a formula does apply, derive
its exact numeric effect from source and confirm with a real render at the
predicted location — a byte-exact match (e.g. a legible font landing
exactly at a derived offset) is far stronger evidence than either "the doc
already covered this" or a guess-and-check content scan.
