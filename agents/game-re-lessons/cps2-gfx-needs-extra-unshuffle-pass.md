# A byte-exact `gfx_layout` can still render as noise if the driver transforms the gfx region first

**When it bites:** you transcribed a tile/sprite decode field-for-field
from a reference emulator's `gfx_layout` and assembled the ROMs per the
driver's `ROM_LOAD*` macros, yet real data renders as uniform,
tile-grid-aligned noise (correct tile boundaries, no shapes) or
nibble-packed garbage, with no misalignment artifacts to chase.

## The trap

The `gfx_layout` describes the region **as the decoder sees it**, which
is after any `init_*()` / `DRIVER_INIT` / `*_gfx_decode()` /
`video_start` code has rewritten it. MAME drivers routinely permute the
raw region first: a bit shuffle, a recursive block unshuffle, a
PROM-driven address unscramble. Porting only the shared layout table and
the load macro misses that whole stage. The tell is
**structureless-but-grid-aligned** output. That means a missing stage, not
a wrong bit position inside the formula you already have.

## Check / fix

Before decoding, read the game's own `ROM_START` → machine config →
`init_*` chain in the driver and list every function that touches the gfx
regions before `GFXDECODE` uses them. Apply them in order, then the
layout. Siblings in the same driver family can differ: one may have an
init pass and another none. Check each game's init separately, and test
the transform on/off for each one.

Cheap oracle when you have no reference image: score neighbour-pixel
equality (smoothness) of the decoded tiles with the candidate transform
**on vs off**. The "off" score is your null control, and real art scores
clearly higher.

## Canonical example

D&D: Shadows over Mystara (CPS2, `kolbold`). CPS2 reuses CPS1's
`cps1_layout16x16` and a similar `ROM_LOAD64_WORD` interleave, but
`cps2_state::unshuffle()` (`src/mame/capcom/cps2.cpp`) first applies a
per-0x200000-bank recursive 8-byte-unit de-interleave that has no CPS1
analogue. Without it, all 196,608 tiles decoded as grid-aligned noise.
With it, the identical downstream code gave recognizable sprites.

## Variants

- **Konami `ROM_LOAD32_WORD` (tmnt):** `init_tmnt` applies
  `chunky_to_planar` (a `bitswap<32>` per little-endian word) to both gfx
  regions, plus a PROM-driven sprite word-address unscramble. Without
  them the data reads as nibble-packed garbage. Smoothness was 0.52 with
  the transform and 0.32 without it (null control). tmnt2 has no such
  init, so its ROMs decode as loaded. Never carry a sibling's init over,
  or its absence, without checking.

**History:** 2 instances (ddsom CPS2 unshuffle; tmnt Konami
chunky_to_planar, 2026-10). Raw logs: `_archive/cps2-gfx-needs-extra-unshuffle-pass.md`.
