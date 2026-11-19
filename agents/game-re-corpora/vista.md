# vista — Vista Pro 3.05, World Construction Set 2.04 (Amiga terrain software)

**Project root:** `~/Development/vista` · **Full history/evidence:** `game-re-corpora/details/vista.md` (read on demand) · **Open work:** `docs/vistapro/TODO.md`, `docs/worldconstructionset/TODO.md` · **Spec:** `docs/rendering-algorithms.md` (all format facts, generator reconstruction, projection/shading, parity table) · **Last audit:** `docs/<title>/audit-2026-11-18{,-changes}.md`

## Titles
- Vista Pro 3.05 (Virtual Reality Laboratories) — `vistapro`/`amiga` — DEM decode, fractal generator and material passes reproduced word-for-word against the native code; browser renderer; camera/lens controls are placeholders (`vista-camera-lens`)
- World Construction Set 2.04 (Questar) — `worldconstructionset`/`amiga` — `.elev` elevation tiles decoded (layout corrected 2026-11-19); `.frd` read as byte depth maps; objects/params/executables untracked

## Solved formats → where documented
- Vista DEM (`Vista DEM File`): 2,048-B header; dimension gate bit 0 of BE u32 @132, w/h @136/@140 (0 → 258); +0x80 compression flag (1 = row RLE; else raw words, unimplemented); +0x84 bit 0 also enables `Seek()`ed extra sections; +0xA4.. origin (30 m spacing); +0x400 0RGB colour map; rows from 0x800 = u16 length + PackBits-like RLE (0x80 = 129-byte repeat) + delta-word predictor (0x80 escape = absolute word) — `rendering-algorithms.md` §1 "Vista DEM files" (header table)
- Vista `GenerateFractal`, Fractalize, relief/gradient materials, Lyap2DEM (unverified) — §1
- WCS `.elev`: 68-B header, size `68 + (f4+1)·f8·2`; **signed** int16; `f4+1` west→east lines of `f8` south→north samples (returned transposed); header 52–67 = MaxEl, MinEl, cell count, two floats — §1 "WCS elevation files", `src/terrain/formats.ts`
- WCS `.frd`: 180,000-B byte fractal-depth maps (0–8, 0xFF); grid layout still hypothesis (`wcs-frd-layout`)

## Engine / cross-project links
- None to game corpora. Native-code oracle approach (Unicorn M68000, relocated HUNKs, stubbed OS calls, word-for-word Vitest comparison) mirrors other Amiga projects' Musashi harnesses — see `game-re-method/cpu-emulation-boot-harness.md`

## Reusable code in this repo
- `tools/vistapro/native_harness.py` — native differential oracle (needs `lha`, `amitools`, `unicorn`; `npm run test:native`)
- `src/terrain/` — DEM/`.elev`/`.frd` parsers, Vista fractal reconstruction (`vista-fractal.ts`, `vista-native-fractal.ts`); `src/terrain/__tests__/wcs-retail.test.ts` (real-data seam/geography test, skips without the cache)

## Know before you start
- Retail archives live in gitignored `data/`; WCS files were staged by hand into `build/cache/worldconstructionset/extracted/` (no committed ADF→LZH extractor: `wcs-extractor`)
- Doc offsets: `VistaPro.000` code is hunk-relative (file offset − 0x28); state the base on every address; the `.881` FPU build is separate
- A seam test on square `.elev` tiles cannot detect transposition; use the non-square `Deformatio.elev` and header origins
- Synthetic round-trip tests only check the code's own assumption; add retail-file tests
- Unused oracles: 30 `extras/script/*.script` camera paths (4,884 frames); 10 `cmap/*.dem` colour-map DEMs
- `test:native` spawns 48 subprocesses against a 30 s budget (`vista-native-test-fragility`)

## Key lessons
- `game-re-method/verification-techniques.md` § Seam continuity — square-tile seam test blind to transpose
- `check-that-cannot-fail-is-not-evidence.md` — synthetic round-trips of the code's own `.elev` layout
- `file-offsets-vs-segment-relative.md` — mixed file/hunk offsets in the doc

Full list: `details/vista.md` § "Lessons sourced from this corpus (full list)".
