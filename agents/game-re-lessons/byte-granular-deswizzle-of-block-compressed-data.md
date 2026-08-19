# Tegra/GOB block-linear deswizzle must operate in the compressed format's own block granularity, not per-byte

**When it bites:** a Nintendo Switch (Tegra X1) block-linear deswizzle call
site passes `blockWidth=1, blockHeight=1, bpp=1` (or otherwise treats the
surface as one "block" per raw byte) ahead of a block-compressed format
(BC1-7, ASTC) rather than that format's real block shape (4x4 pixels, 8 or
16 bytes/block) — especially when the call "works" in the sense of decoding
without an exception, and especially when the affected texture type is
small enough (single-GOB, low mip count) that the visual corruption from lost
data reads as a plausible sparse/faded image rather than obvious scrambling.

Confirmed in Chimera's `g1t.ts` (Koei Tecmo G1T textures, Fire Emblem
Warriors: Three Hopes): the Morton/block-linear branch called
`deswizzle(width, height, 1, 1, 1, 1, 1, 0, 0, slice)` — byte-granular
(bpp=1, 1x1 "blocks") — for BC1/BC4/BC5/BC7 data. `deswizzle`'s internal
GOB-address math computes a surface byte-count from `width * height * bpp`;
for BC1 (8 bytes per 4x4=16-pixel block, i.e. 0.5 bytes/pixel) that's **2x**
the real compressed data length `(width/4)*(height/4)*8`. The `slice`
buffer handed in is correctly sized to the real (smaller) count, so roughly
half of the block-linear address computation's read offsets land past the
end of the source `Uint8Array` — which returns `undefined` for an
out-of-bounds numeric index, and `undefined` assigned into another
`Uint8Array` silently coerces to `0`. No exception anywhere in the chain:
the decode "succeeds" and produces an image with roughly half its block
data zeroed, which for a lossy 4-color/8-color block format can look like a
merely sparse or faded texture rather than obviously broken tiling — easy to
mistake for correct output on a quick look, especially against a plausible
subject (a foliage/leaf texture with "gaps" reads as intentional alpha).

**The fix:** deswizzle at the format's real block granularity — `blkWidth`/
`blkHeight` = 4 (or the format's actual block dimensions), `bpp` = 8 or 16
(the real per-block byte count), matching whatever the same codebase's
block-size-for-this-format function already computes for buffer sizing.
Getting `blockHeightLog2` right matters too but is a distinct, second bug —
if the format has no header field for it (unlike e.g. Astral Chain's WTB
`textureLayout`), derive it structurally: `computeBlockHeightLog2` grows the
block height to the next power of two (in GOBs, 8 rows each) covering the
surface's block-count height, capped at 16 GOBs — the standard Nvidia rule
also used by BNTX-Extractor/Ryujinx. Verify by rendering a real, distinctively
-shaped (not solid-color) texture and confirming a clean, non-tiled,
non-cut-off image — "decoded without throwing" is not evidence here, per the
general verification bar; get a second oracle where possible (a before/after
comparison on a texture whose corruption produces visible banding, like a
normal/roughness map, is unusually diagnostic — BC5 in particular tends to
show clean horizontal GOB-row banding under this bug where a BC1 color
texture might just look sparse).

**Corollary — Morton/needs-deswizzle membership is per-type-code, not
per-platform, and not always uniform even within one engine's own games on
the same platform.** Don't assume "this is a Switch title so its textures
need Tegra deswizzling," and don't assume a MORTON/swizzled-type-code set
confirmed for one game in an engine family transfers unchanged to a sibling
game. Two Koei Tecmo Switch titles sharing `g1t.ts` (Three Houses and Three
Hopes) use *different* real-content type codes: Three Houses' dominant type
(`0x59`, 13,448/13,467 of its textures) reports `platform = 10` (NSwitch)
but decodes correctly completely linearly — confirmed by decoding a real
512x512 sample both ways and viewing the result (as-is: clean continuous
image; deswizzled: scrambled blocky grid) — while Three Hopes' real content
uses several genuinely-swizzled type codes (`0x60`/`0x63`/`0x64`/`0x66`) that
do need the fixed deswizzle path above. The type byte, not the platform
field or the game, is what determines whether a given texture instance needs
deswizzling; check the real census for the specific game and specific type
codes in front of you rather than inheriting a MORTON-membership decision
from a sibling game or from the platform field alone.
