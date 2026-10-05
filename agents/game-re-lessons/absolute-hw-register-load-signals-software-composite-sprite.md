# Absolute hardware-spriteram address loaded into an index register signals a software composite

**When it bites:** the confirmed hardware sprite/OBJ record for a target has
NO group/link/size field (a flat, single-tile-per-entry format — common on
pre-1990s arcade hardware), and the task is to find whether the game
composes multiple hardware tiles into one bigger logical sprite (a "big
monster made of several small tiles" question) with no generic hardware
mechanism to decode structurally.

## The trap

Confirming "the hardware record has no composite field" (straight from a
MAME driver's `draw_sprites()`/equivalent) is not the same as confirming "no
composite sprites exist" — that's a common conflation, and stopping there
produces a premature "still open / needs live capture" verdict. Multi-tile
composition on flat-OBJ-list hardware is virtually always done by GAME CODE
writing several independent hardware records with hand-placed relative
offsets, which is real, findable, static content — it's just not addressed
by re-reading the (already-confirmed) hardware record layout again.

## The fix

Grep the disassembly for an ABSOLUTE (not indexed/computed) load of a
hardware-sprite-RAM address into an index/pointer register (`ld ix,
0xfeXX`/`ld iy, 0xffXX` on Z80; the equivalent absolute-address-into-base-
register idiom on other CPUs). This is a strong, cheap signal: code is about
to write several fields at small constant offsets from that one base — i.e.
build more than one record from one call site. Follow each hit forward a
short distance and check whether the literal position bytes written (X/Y)
form a real NxM grid (consecutive slots at position deltas matching the
tile size) and whether the literal tile-code bytes written to each slot are
close together (`base`, `base±1`, `base±(rowStride)`, ...) — both are
independent confirmations that a real multi-tile block, not several
unrelated single objects, is being built.

## Confirmed instance

Black Tiger (Capcom, 1987, `kolbold`): `blktiger.cpp`'s `draw_sprites()` is
source-confirmed to have a flat 4-byte OBJ record (code/attr/sy/sx) with no
group/size field at all — genuinely no hardware composite mechanism, unlike
CPS2's `cps2_render_sprites()`. Grepping for `ld ix/iy, 0xfeXX/0xffXX` found
2 real hardcoded 2x2 composites (4 hardware records each, confirmed by their
literal SX/SY bytes forming a 16px-pitch 2x2 grid and their tile codes being
`{base,base±1,base+8,base+8±1}`) plus a THIRD, genuinely generic, animation-
table-driven composite builder (a real 3-level frame/tick/color pointer
chain resolving to the same block-write pattern) — none of which the
hardware record format alone would ever reveal. Rendered with the game's
own confirmed real palette, the hardcoded composites decode to an
unmistakable, non-degenerate small humanoid figure.

This mirrors, at the hardware-sprite level, an earlier same-project finding
at the TILEMAP level: a CHARS-layer "shop icon" 2x2 block built by writing 4
literal `[rawByte,attr]` pairs from one small record — the same "small
literal record → 4 tile writes at fixed relative offsets" shape, just two
different memory targets in the same engine. Whenever one such convention is
found in one engine layer, check whether the sibling layer(s) (tilemap vs.
hardware sprites, or vice versa) reuse the same idea before assuming it's
layer-specific.
