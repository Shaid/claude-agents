# lucina — corpus notes

Seer-framework project (`~/Development/lucina`), Nintendo 3DS titles only.
One cross-title format spec, `docs/3ds-formats.md`, plus per-game
`docs/<game>/TODO.md` and audit pages. Generic 3DS codecs (`lz`, `ctpk`,
`ctr-texture`) were moved upstream into `@seer-project/3ds`; lucina is its
only linked consumer.

## History

**2026-11-18 audit / 2026-11-20 corrections.** A re-codebreaker gap audit per
title (`docs/<game>/audit-2026-11-18.md`) was applied title by title
(`audit-2026-11-18-changes.md`), with `> Correction (2026-11-20)` blocks in
`docs/3ds-formats.md`. Findings that became knowledge-base lessons:

- **Stored `.lz` wrapper hidden by pass-through.** Fates has 31 `.lz` files
  (30 `field/*_t.bch.lz` plus `TextEditor.bin.lz`) that are `00` + u24
  (= fileLength − 4) + raw bytes, 31/31. The shared `decompressLz13`
  returned them unchanged with the header attached. Fixed upstream (seer
  `8ea058d`), gated on the exact size relation, with a null control.
- **LZ13 outer size.** `0x13` + u24 + LZ11 stream: the outer u24 differs from
  the inner LZ11 size on 853/4,914 Awakening and 1,480/13,455 Fates files,
  always larger and ≥ fileLength − 4 — an in-place decompression buffer size.
  The decoder already used the inner size; only docs were wrong.
- **CTPK format ids** are PICA200 hardware values: dataSize matches the
  hardware mip-chain size on 2,863/2,863 loose Awakening textures
  (9,072/9,072 with arc-embedded). Seer `87627ab` fixed the comment.
- **G1T per-texture header** (FE Warriors) is 20 B when byte+7 bit `0x10` is
  set, else 8 B: 13,604/13,648 (misfits are span artefacts of one
  container); constant-20 null control fits 0/526.
- **`.bfnt`**: u16@0x1a is the sheet count, the pixel format is u16@0x18.
  The original four-font sample all had one sheet; System and Debug fonts
  decoded wrongly.
- **MH4 MOD**: a stride filter (≥ 36) dropped 5,203 of 8,749 models;
  triangle strips needed unrolling; ARC entry names corrected.
- **Bravely Second `.fs` members** are `0x60` + u24 zlib-wrapped (Bravely
  Default members raw); multi-model CGFX had been overwriting outputs.
- **README "gltf-validator, 0 errors"** had no validator anywhere in the repo;
  marked unverified with TODO rows.
- **Bravely Default** corpus is a fan-patched dump (Undub v2.0 &
  Uncensored); its `Sound.bcsar` is 0 B.

## Lessons sourced from this corpus (full list)
crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md, material-texture-name-not-embedded-lives-in-companion-file.md (Awakening battle colour maps), register-write-parser-must-honour-byte-enable-mask.md (PICA uniform scale), decoder-passthrough-fallback-hides-wrapper-variants.md, formula-check-small-sample-misses-conditional-rounding-term.md, partial-hunk-commit-leaves-head-uncompilable.md, pixel-format-value-guessed-from-enum-not-confirmed.md, tracker-prose-is-not-evidence.md, whole-corpus-count-is-scoped-to-reader-coverage.md (Fates header-slot variant)
