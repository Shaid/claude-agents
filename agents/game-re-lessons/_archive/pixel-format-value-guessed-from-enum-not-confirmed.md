# Archive: pixel-format-value-guessed-from-enum-not-confirmed.md

## 2026-11-20 — lucina (3DS): CTPK converse

Add a short "Converse" section:

The mirror error also happens: a doc asserts a format field is "NOT the hardware enums" (an SDK-private numbering) without testing it. Use the same structural oracle in both directions. For each candidate numbering, check per texture that the declared data size equals the mip-chain byte size implied by (width, height, mips, bpp of the named format). Whichever numbering fits every texture wins.

Example: 3DS CTPK texture packs. The format ids are the PICA200 hardware texture-format values (the same numbering as BCH GPU register 0x8E). `dataSize` matches the hardware mip-chain size on 2,863/2,863 loose FE Awakening textures (9,072/9,072 including arc-embedded ones). The shared library's comment saying "CT SDK numbering, NOT the hardware enums" was wrong. The decode tables were already right; only the label had misled readers.
