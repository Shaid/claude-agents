# valkyrie — Valkyrie Profile (PSX, PSP), Valkyrie Profile 2 (PS2)

**Project root:** `~/Development/valkyrie` · **Full history/evidence:** `game-re-corpora/details/valkyrie.md` (read on demand) · **Open work:** `docs/valkyrieprofile/TODO.md`, `docs/valkyrieprofile2/TODO.md`

## Games
- VP1 (PSX, `SLUS_011.56`/`.79`, 2 discs) — `valkyrieprofile`/`psx` — formats solved; 225+-round gameplay-logic campaign
- VP1 Lenneth (PSP `ULUS10107`, TOSE port) — `valkyrieprofile`/`psp` — PSX formats reused; audio/3D open
- VP2 Silmeria (PS2, `SLES-54644`) — `valkyrieprofile2`/`ps2` — formats solved; damage formula unlocated

## Solved formats → where documented
- VP1 PSX, `docs/valkyrieprofile/psx/data-structure.md`: SLZ LZSS (§4), XOR-encrypted TOC (§8), group directory (§9.3), STR video (§9.4), 3D/rooms/sprites (§9.6), subset-font text (§10), audio/BGM (§11), battle sprites (§13) — confirmed
- VP1 logic: `psx/battle-logic.md`, `battle-engine-spec.md`, `item-skill-system.md`, `dungeon-field-mechanics.md`, `scene-script-vm.md`, `save-system.md` → `src/engine/`, `src/battle/`
- PSP, `docs/valkyrieprofile/psp/data-structure.md`: `PSPVAL1.PFS` trailer dir, PSMF+ATRAC3+, CLUT8 art; PSX formats reused byte-for-byte at the same slot numbers
- VP2, `docs/valkyrieprofile2/ps2/data-structure.md`: XOR raw-LBA TOC, `SL`/SLE/LZSS16, resource dir, FIS textures, TAC audio, VIF1 meshes, `MINA` anim — confirmed; `IDOM`↔`MINA` binding open

## Engine-family / cross-project links
- SLZ identical on PSX/PS2/PSP; VP2 TOC from CUE's `triAce-PS2.c` (also SO3/Radiata, untested)
- BGM = Star Ocean 2 format (VGMTrans `TriAcePS1`); TAC via vgmstream `tac_lib.c`

## Reusable code in this repo
- `tools/shared/`: `psx-slz.ts`, `psx-tim.ts`, `psx-vp-*.ts`, `vp-group-directory.ts`, `ps2-*.ts`, `psp-vp-*.ts`; CD/STR/ISO/ATRAC3+ moved to `@seer-project/playstation` (docs citing `psx-cd.ts`/`psx-str.ts`/`psp-iso9660.ts` are stale)
- `tools/valkyrieprofile/vp-corpus.ts` — live disc extraction

## Know before you start
- Every `verify-*.ts` must read live disc bytes via `vp-corpus.ts` on BOTH discs; `build/cache/` has held stale artifacts
- 7/8 PSX overlays share base `0x8002f824` (field TOC 2292, battle 1490/1491); "slot N (0x…)" cites are call sites; SLUS base `0x8000f800`
- Grep all psx docs, module comments and tests before fresh disassembly — the answer was repeatedly already in-repo
- Censuses: base-register provenance, corpus-wide, both discs; "needs live capture" verdicts were often wrong — try `re-oracle`
- "CLOSED" rows get reopened; static backlog is exhausted — without a new lead, run a rigor audit of an unverified early closure
- Triad baseline is non-zero; concurrent sessions edit the tree — targeted `git add`
- User-confirmed: VP1 has no random encounters, and does use 3D (world map, arenas, effects)

## Key lessons
- `local-decode-cache-may-be-stale-reverify-fresh.md` — `build/cache/` held stale artifacts; verify from live disc bytes
- `call-site-address-misread-as-load-base.md` — "slot N (0x…)" cites are call sites, not load bases
- `shared-load-base-plus-scrollback-transcription-misattributes-address.md` — 7/8 PSX overlays share base `0x8002f824`
- `doc-self-cross-reference-before-fresh-disassembly.md` — the answer was repeatedly already in-repo — grep first
- `negative-from-addressing-root-not-shapes.md` — censuses need base-register provenance, corpus-wide, both discs
- `resource-id-in-strided-record-field-carried-by-callback-object.md` — "needs live capture" verdicts were often wrong
- `tracker-prose-is-not-evidence.md` — "CLOSED" rows get reopened; re-run, don't trust prose
- `genre-mechanic-asserted-by-tracker-needs-primitive-existence-check.md` — VP1 has no random encounters despite tracker claims
- `mips-delay-slot-instruction-always-executes.md` — PSP `BOOT.BIN` trailer-size trace tripped on a delay slot
- `lui-addiu-negative-low-half-borrows-from-high-half.md` — lui+addiu address reconstruction must sign-extend low half

Full list: `details/valkyrie.md` § "Lessons sourced from this corpus (full list)".
