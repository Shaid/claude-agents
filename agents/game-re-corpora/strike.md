# strike — Desert / Jungle / Urban Strike (Amiga OCS/AGA, Mega Drive, SNES)

**Project root:** `~/Development/strike` · **Full history/evidence:** `game-re-corpora/details/strike.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` (`desertstrike`, `junglestrike`, `urbanstrike`)

## Games
- Desert Strike (`desertstrike`: `amiga`, `megadrive`) — Amiga object atlas, tiles, MODs, entity templates + spawn binding confirmed; no Apache sprite found
- Jungle Strike (`junglestrike`: `amiga` OCS, `amigaaga`, `megadrive`) — AGA screens, `weapons`, `objects1-9`/`sprites1-9` confirmed
- Urban Strike (`urbanstrike`: `megadrive`, `snes`) — MD tilemap + overlay bank; SNES tilesets/screens/text shipped; sprites open

## Solved formats → where documented
- Amiga compressors: LR88 (= renamed PowerPacker PP20) on AGA; RNC1 directory + nested RNC2 on Desert Strike/OCS — confirmed — `docs/desertstrike/amiga/data-structure.md`, `tools/junglestrike/decrunch-corpus.ts`
- Desert Strike Amiga trackloaded disk format, 96×72 6-plane object atlas, 16×16 5-plane tileset + u8 tile-index maps, ProTracker `M.K.` cues, `DMCA` sample bank (sample rate inferred, not confirmed) — `docs/desertstrike/amiga/data-structure.md`, `tools/desertstrike/object-atlas.ts`
- Desert Strike per-mission entity templates (61/62/66/59) bound 100% to sprites; spawn = bank-header manifest at `+0x50` (live-confirmed); spawn-grid leaf fields still open — same doc "Twelfth session", `tools/desertstrike/entity-{templates,sprites}.ts`
- Jungle Strike AGA screens (shared scratch copper-list palette patch), `weapons` HUD/projectile bank, `statmapN` palette, `worldNblks`/`worldNmap`, `objectsN`/`spritesN` HUNK-wrapped tables — confirmed — `docs/junglestrike/amigaaga/{data-structure,js-code-structure}.md`, `tools/junglestrike/objects.ts`
- Mega Drive: Strike LZSS + RLE, shared tilemap container (Urban + Jungle), overlay-tile bank (`format=0x1A`), fourth codec `cmd=18` tile-delta (129/129), level↔tileset association (29/29) — confirmed; `cmd=18` CRAM palette open — `docs/strike-megadrive-tilemap.md` (§7.6-§7.9), `docs/<game>/megadrive/data-structure.md`
- Urban Strike SNES: splash-only 6-op tag-byte codec; main graphics = Okumura LZSS (`$9F:EBD4`) storing **chunky 4bpp** (converted to planar at DMA time); tilemap descriptor (raw/RLE); 883-string ASCII text table; OAM sprites in use — confirmed (67/67 tilesets, 97 screens) — `docs/urbanstrike/snes/data-structure.md`, `tools/urbanstrike/snes-{tagbyte-codec,lzss,gfx,tilemap,text}.ts`

## Engine-family / cross-project links
- Desert Strike Amiga tileset/tilemap is byte-identical in shape to Jungle Strike AGA's (u8 → u16 indices); MD tilemap reader is identical across Urban and Jungle Strike (different addresses).
- Urban Strike SNES is an unrelated toolchain/codec from the MD/Amiga builds.
- SNES DMA-register census (`STA $420B/$4342/$4345`) should crack `sorcery`'s open Wizardry 6 SNES graphics.

## Reusable code in this repo
- `tools/shared/hunk-wrapper.ts` — strips Jungle Strike's single-hunk `LoadSeg` data wrapper + `HUNK_RELOC32`
- `tools/shared/strike-lzss.ts`, `strike-rle.ts`, `strike-tile-delta.ts` — the MD codecs
- `tools/shared/megadrive-{tilemap,overlay-bank,level-tileset}.ts` — MD tilemap/overlay bank/VRAM base-tile solver
- Moved upstream to seer packages: RNC1/RNC2/PP20 (`@seer-project/pipeline`: `decompressRnc1`, `decompressRnc2`, `decrunchRenamedPp20`); general HUNK parser (`@seer-project/amiga`; Desert Strike's linker puts MEMF flags in-stream, mask `&0x3FFFFFFF`); SNES PPU helpers (`@seer-project/snes`)

## Know before you start
- SNES: radare2 is blind to M/X flag width; use a flag-aware 65816 disassembler with the correct per-entry state (wrong state in bank `$A8` caused a false "no resource table") — `r2-snes-flag-width-blind.md`.
- SNES graphics resources are per-subsystem far-pointer "handle" arrays in DP `$20`/`$22`, not one global catalog; a planar decode of ROM bytes looks coherent but is wrong (check out-of-palette pixel rate).
- Census both direct-page and absolute hardware-register forms — `narrow-opcode-form-census-false-negative.md`.
- Verify a byte-consumption invariant against the *decrunched* size; HUNK_RELOC32 presence separates pointer tables from flat pixel data.
- Cached Musashi boot RAM dumps go stale past their checkpoint — take a live capture for later routines.
- Re-verify an escalation's "leads" (bank `$A8` sprite leads were wrong).

## Key lessons
- `r2-snes-flag-width-blind.md` — wrong M/X state in bank `$A8` faked "no resource table"
- `narrow-opcode-form-census-false-negative.md` — census both direct-page and absolute hardware-register forms
- `crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md` — byte-consumption invariants must use the decrunched size
- `hunk-wraps-non-code-data.md` — Jungle Strike data is HUNK-wrapped; RELOC32 marks pointer tables
- `cached-runtime-image-stale-past-boot-checkpoint.md` — cached Musashi RAM dumps go stale past their checkpoint
- `verify-escalation-artifacts-not-just-claims.md` — escalation's bank `$A8` sprite leads were wrong
- `header-shape-ambiguous-pixel-encoding.md` — Urban Strike SNES stores chunky 4bpp; planar looks coherent
- `shared-scratch-copper-list-palette-patch.md` — Jungle Strike AGA screens patch a shared scratch copper list
- `legible-text-render-weak-palette-oracle.md` — legible text screens don't prove the palette chain
- `shared-tool-session-clobbered-by-fork.md` — forks/sibling sessions can clobber the shared r2 session

Full list: `details/strike.md` § "Lessons sourced from this corpus (full list)".
