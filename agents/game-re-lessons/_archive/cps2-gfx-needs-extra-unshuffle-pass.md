# A byte-exact planar tile formula can still render as noise if a hardware-generation-specific deinterleave pass is missing

**When it bites:** you've confirmed a tile/sprite pixel-decode formula
against a trusted source (a reference emulator's own `gfx_layout`/planar
decode function, transcribed field-for-field) and correctly assembled the
container per its own documented ROM-load/interleave scheme, yet rendering
real data produces uniform, structureless static — not obviously-wrong
garbage with visible misalignment artifacts, just even, tile-grid-aligned
noise with no recognizable shapes at all.

## What went wrong

CPS1 and CPS2 share the exact same 4bpp planar tile pixel format
(`cps1_layout16x16` in `src/mame/capcom/cps1.cpp`, reused verbatim by
CPS2's own `GFXDECODE` table) and a superficially-similar mask-ROM
interleave (`ROM_LOAD64_WORD`, a 4-way 16-bit-word interleave across 4
chips forming 64-bit-wide reads). Porting *only* those two pieces —
interleave the 8 CPS2 gfx mask ROMs, then apply the CPS1 planar formula —
looked complete and produced tile-grid-aligned output (correct dimensions,
correct-density "blockiness"), but every tile decoded to unstructured
noise, not art.

The missing piece: CPS2 (unlike CPS1) applies an **additional, per-2MB-bank
recursive de-interleave** to the assembled "gfx" region before the planar
decode ever runs — `cps2_state::unshuffle()` / `cps2_gfx_decode()`
(`src/mame/capcom/cps2.cpp`), a self-inverse permutation of 8-byte units
(recursively halve, unshuffle each half, swap the 2nd/3rd quarters),
applied once per 0x200000-byte bank. It has no analogue in the CPS1 driver
at all and is easy to miss if you only look at the shared `gfx_layout`
struct and the (also-shared-looking) `ROM_LOAD64_WORD` macro.

Confirmed on D&D: Shadows over Mystara (ddsom): decoding without the
unshuffle gave uniformly-noisy 16x16 blocks (correct tile boundaries,
wrong content) across the whole 196,608-tile gfx region; applying the
unshuffle first, with the *identical* downstream planar-decode code,
immediately produced clearly recognizable sprite/creature silhouettes.

## The fix / the generalizable lesson

When two platforms/hardware generations in the same engine family
(CPS1→CPS2, or any "v2 of a chipset") share a pixel-plane *format* and a
superficially-matching ROM-load *macro*, don't assume the full pipeline —
container assembly → pixel decode — transfers unchanged. Check the
*generation-specific* driver/init code (not just the shared decode table)
for an extra pass the newer hardware's larger/differently-wired ROMs need
that the older one didn't — search the driver source near wherever gfx
decode is invoked (`init_*_video()`, `*_gfx_decode()`, or equivalent) for a
transform applied to the raw region *before* the shared decode table is
used. "Structureless, tile-grid-aligned noise" (not obviously-scrambled
garbage) from an otherwise byte-exact-verified formula is the tell that a
whole deinterleave *stage* is missing, not that a single offset/bit
position within the existing formula is wrong.

---

## Instance 2026-10-06 (inbox candidate, verbatim)

# Konami gfx ROMs can need an init_* bit shuffle before any gfx_layout applies

When it bites: MAME `ROM_LOAD32_WORD` Konami tile/sprite ROMs decode to noise or nibble-packed garbage with the documented layout (tmnt).
Lesson: read the driver's `init_*` first: tmnt applies `chunky_to_planar` (bitswap<32> per LE word) to both gfx regions, and a PROM-driven sprite word-address unscramble. Oracle: neighbour-equality smoothness with the transform off as the null control (0.52 vs 0.32). tmnt2 has no init, so its ROMs decode as loaded; always test both.
