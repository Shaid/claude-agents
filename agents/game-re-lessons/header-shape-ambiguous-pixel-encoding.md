# A header/size match doesn't prove the pixel encoding — or the right decompressor

**When it bites:** a byte-count formula (header w/h × bpp, or a bare file size) exactly fits more than one pixel-encoding hypothesis, or you're about to accept the first that fits. Also: two decompressors both hit the declared output length. Also: a same-named file on two ports is exactly the same size, and you infer the same layout.

Total byte count fixes at most the *bit depth*, never the arrangement or meaning of the bits. It can't tell planar from chunky, contiguous planes from word-interleaved, Amiga-style rows from IIGS packed-nibble rows (both give 16 B/row at 24–25 px, depth 4), pixels from tile indices (`w*h` bytes either way), or BC1 at `2w×h` from BC3 at `w×h`. A header's offset/endianness shape and the pixel encoding it carries are independent facts. A length match is necessary, not sufficient, and so is a visual render when the wrong reading has its own source of smoothness.

**Check / fix:**
- When an autodetector matches on byte count, **decode every structurally plausible candidate** and check shape coherence or an independent oracle before trusting the first match.
- Prefer the formula that divides evenly, all else being equal, but never let it stand in for a render. An uneven remainder doesn't disprove a candidate, and an exact fit doesn't prove one. Try plane order both ways (plane-major vs row-interleaved).
- A corpus that is uniformly planar elsewhere is a prior, not a proof. DOS CGA/Tandy-family formats lean packed/chunky (`game-re-tooling/dos.md`).
- **Tilemap vs image:** tile indices are spatially smooth, so they render as a plausible greyscale scene. If the "image" uses an encoding no other confirmed format in the corpus uses, and there is an unsolved, similarly sized blob that could be its tileset, decode that blob and try composing the two before trusting the flat-pixel reading.
- **Competing decompressors:** decode with both and score a downstream structural invariant (a frame's implied bitplane depth `dataSize/(bytesPerRow*height)` comes out as a clean integer 1–8, plus implied table counts and directory offsets). Never use a fixed per-format tie-break.
- **Whole families of tied candidates and no structural invariant:** decode them all and pick the lowest **total variation** (mean absolute delta between adjacent pixels). It's cheap enough to run corpus-wide. Near-ties occur on flat content, where any pick still looks right.
- **Across ports:** a same-size file is as weak a layout signal as a same-size candidate header. Render both layouts.

**Canonical example:** War in Middle Earth, DOS EGA. Two small resources (24×12, 25×13) had a 27-byte IIGS-shaped header (LE u16 w/h at the IIGS offsets) and carried IIGS *packed-nibble* pixels. Every other image on that platform uses Amiga-style planar data under a 28-byte BE header. Both readings fit the size. Rendering both showed a coherent filled icon for packed-nibble and noise for planar.

**Variants:**
- Wizardry 6 Amiga `.EGA` (32,768 B, no header): the exact-fit 256×256×4 rendered noise, while 320×200×4 (a 768 B remainder still unexplained) rendered "BANE OF COSMIC FORGE" plane-major.
- Wizardry 6 DOS `.CGA`/`.T16`: half or equal the size of the planar `.EGA` siblings. Planar rendered noise and packed/chunky was correct.
- Desert Strike (Amiga) `disk3-00/04/07/11`: "u16 w, u16 h, w*h 8bpp pixels" held exactly and rendered as plausible terrain, but the bytes are 16×16 tile indices into a separate tileset.
- Vengeance of Excalibur `ANI32.RES` FRML #714/#900: PackBits also hits the LZSS output length and gives garbage frames (implied depth 2.49 and a negative value, vs a clean 5 under LZSS). A "prefer PackBits" tie-break was wrong for years.
- Phantasie II (ST) `PARTY*.PAT` is the same 8,192 B as P1 Amiga's, yet uses the ST word-interleaved layout, like the larger `MSTR*.PAT`. NieR PS3 `TX2D`: 1,488/1,539 BC1/BC3 records had 3–12 size-tied candidates, resolved by TV (best ≈2–11 vs runner-up ≈60–120).

**History:** 7 recorded instances (WIME, Wizardry 6 ×2, Desert Strike, Vengeance of Excalibur, Phantasie II, NieR): full log in `_archive/header-shape-ambiguous-pixel-encoding.md`.
