# moonstone — corpus notes

Project: `~/Development/moonstone`. Games: **Moonstone** (Mindscape/Rob Anderson) and **Shadow of the Beast I/II/III** (Psygnosis/Reflections), all Amiga WHDLoad installs. Byte-level evidence lives in `docs/<game>/amiga/{data-formats,probe-recon}.md`; this file is a pointer and history summary.

## History

- **2026-11-19 — first curation**, from the 2026-11-18 codebreaker audit round (`docs/<game>/audit-2026-11-18{,-changes}.md`). Corrections applied at commits 7ac6d33 (Moonstone CEL plane-mask scatter, `mog` blitter re-read; OFS-reader reclassification of the "trackloader"), 7788b73 (SotB1 extent table through LOADROUT: 35/43 exact starts vs 0 for the swapped-disk null; verified extents 16 → 35), 1f28315 (SotB2 ST15 module parser, word lengths, residual 0 on 3/3), cf8575a (SotB3 decoder chosen by table field +0x0c low bits, 66/70; second-pass-only count re-measured 31 vs 48 claimed).
- SotB3 decrunchers carry no integrity check: 27/40 bit-flipped inputs still decode with exact consumption. SotB1/SotB2 sources are authenticated against WHDLoad CRC tables (109/109, 158/158); SotB3 is not.
- SotB "confirmed" screens in `resource-classification.ts` were whitelist membership; relabelled as geometry-only.
- Cross-title oracle: SotB1 Disk.1 r001 == SotB3 `fz0` after decode (owl screen); SotB1 Disk.1 r007 == Disk.2 r026.

## Lessons sourced from this corpus (full list)
`plane-mask-byte-stores-only-named-planes.md`, `logical-offset-excludes-reserved-region.md`, `unexamined-bits-of-parsed-field-hide-a-discriminator.md`, `check-that-cannot-fail-is-not-evidence.md`, `cross-platform-decode-oracles.md`; tooling: `game-re-tooling/amiga.md` (OFS-reader fingerprint, tracker module size formula)
