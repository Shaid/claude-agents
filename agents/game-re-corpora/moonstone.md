# moonstone — Moonstone, Shadow of the Beast 1/2/3 (Amiga)

**Project root:** `~/Development/moonstone` · **Full history/evidence:** `game-re-corpora/details/moonstone.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` (`moonstone`, `shadowofthebeast`, `shadowofthebeast2`, `shadowofthebeast3`); older open threads still scattered in `docs/gameplay-recon-todo.md`, `docs/visual-asset-reinvestigation-queue.md`, `docs/sotb/amiga/` (`sotb-docs-consolidate`) · **Last audit:** `docs/<game>/audit-2026-11-18{,-changes}.md`

## Games
- Moonstone — `moonstone`/`amiga` — 50 CEL banks, backgrounds, tile maps, terrain, voices, music shipped; gameplay recon of `mog`/`program` deep (research checks under `tools/moonstone/research/`)
- Shadow of the Beast (Psygnosis/Reflections) — `shadowofthebeast`/`amiga` — player/hostile banks, one native-colour scene, screens; 43-entry extent table mapped through LOADROUT
- Shadow of the Beast II — `shadowofthebeast2`/`amiga` — level-plane atlas, player bank, intro visuals, 3 ST15 music modules; enemy pixels withheld (no static descriptor producer)
- Shadow of the Beast III — `shadowofthebeast3`/`amiga` — 81 directory files, 70-entry runtime resource table, level rows, player banks, FLT4 music modules

## Solved formats → where documented
- Moonstone disk: hand-rolled **AmigaDOS OFS** reader (name hash ×13 `&0x7FF` mod 72, root 880, 488 B/block), not a custom trackloader; LZ77 + RNC depackers — `docs/moonstone/amiga/data-formats.md` "Trackloader"
- Moonstone CEL banks (`.cel/.c/.f/.ob/.font`): records at 0x0A `{u32 off,u16 w,u16 h,u8 hi,u8 planeMask}`; field 0x02 = packed length, 0x06 = 8 × decompressed length (meaning open); **stored plane k → k-th set bit of the mask** (2,329/2,329) — same doc "Cel Banks", `tools/moonstone/cel-format.ts`
- Moonstone `.stile` = headerless 10×48 tile map (960 B); `.piv`/`.p` backgrounds (16/32-word palettes); `.a` HUNK-wrapped 8SVX voices; `.cmp` RNC music; `.hit` collision; `.t` terrain — same doc
- SotB1: `Disk.1/2` are RawDIC dumps of `0x1838`-byte decoded tracks; `Init` = boot block; Rob Northen protected streams with checksum + strict "A.R.Bond" trailer; resource-005 extent table uses **logical** offsets via LOADROUT (`mapBeast1RuntimeLoad`; ordinals 0–32 Disk.2, 33–42 Disk.1, inferred from tiling) — `docs/shadowofthebeast/amiga/probe-recon.md` + correction
- SotB2: 1,008,000-B images (12 × 512 + 13 B custom sectors, trackdisk.device boot); sample tables are **15-sample Ultimate SoundTracker modules** (lengths in words; `600 + 1024·pat + 2·Σ`) — `docs/shadowofthebeast2/amiga/probe-recon.md`, `parseBeast2St15Module`
- SotB3: RawDIC side-major, 70-track logical disk; directory at raw `0x3000`; `main` decruncher (`$70BBC`) = ByteKiller-variant main pass + RLE second pass; **decoder selected by runtime table field +0x0c low 2 bits** (`roundup4(size) | kind`: 0 second-pass only, 1 main+second, 3 `beast3p3` decoder, unimplemented); 66/70 records reproduce — `docs/shadowofthebeast3/amiga/probe-recon.md` item 6 correction, `decompressSotb3ByTableKind`

## Engine-family / cross-project links
- Psygnosis owl "Presents" screen: SotB1 Disk.1 r001 is byte-identical to SotB3 `fz0` after decode — use one title to verify the other; SotB1 Disk.1 r007 == Disk.2 r026
- Tracker parsers exist in both `tools/moonstone/moonstone-formats.ts` and `tools/shadowofthebeast2/beast2-format.ts` (not yet shared)
- SotB1/SotB2 WHDLoad CRC tables audited (109/109, 158/158); SotB3 has no CRC audit and its decrunchers have no integrity check

## Reusable code in this repo
- `tools/moonstone/cel-format.ts` (plane-mask scatter), `moonstone-formats.ts` (stile, PIV, tracker)
- `tools/shadowofthebeast/raw-format.ts` (`mapBeast1RuntimeLoad`, stream scanner), `beast1-format.ts`
- `tools/shadowofthebeast2/beast2-format.ts` (`parseBeast2St15Module`), `tools/shadowofthebeast3/sotb3-format.ts` (main/second pass, `decompressSotb3ByTableKind`)
- `npm run verify-assets`, `verify-moonstone-*`, `verify-sotb1-visual` research checks; repo root `m68kops.c` (Musashi)

## Know before you start
- Data is a WHDLoad install: `Disk.N` are RawDIC/DIC images, not ADFs; read the install ReadMe and slave first
- Directory/extent tables may hold logical offsets: run them through the game's loader mapping before reading physically
- Size-like table fields may pack a codec kind into low bits; header "packed" bits are not the selector
- Don't derive sample bodies as `EOF − Σlen`; compute forward from the module header (word lengths)
- "Confirmed" screens in `resource-classification.ts` were list membership; geometry only
- No IRA on this machine at last audit; `mog` citations need a reproducible HUNK-offset listing (`moonstone-mog-listing`). Don't put listings in `data/` without updating the source-inventory test (it counts files)
- Audit figures in the changes files are marked "on trust" where not re-run — re-measure before building on them (SotB3 second-pass-only count: 31 re-counted vs 48 claimed)

## Key lessons
- `plane-mask-byte-stores-only-named-planes.md` — Moonstone CEL `0x1B`/`0x17` frames
- `logical-offset-excludes-reserved-region.md` — SotB1 LOADROUT-mapped extent table
- `unexamined-bits-of-parsed-field-hide-a-discriminator.md` — SotB3 field +0x0c = size | decoder kind
- `check-that-cannot-fail-is-not-evidence.md` — SotB2 `EOF − Σlen`; SotB3 exact consumption on bit-flipped input
- `cross-platform-decode-oracles.md` — SotB1 ↔ SotB3 shared owl screen

Full list: `details/moonstone.md` § "Lessons sourced from this corpus (full list)".
