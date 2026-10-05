# siren — Final Fantasy VII, VIII, IX (PSX)

**Project root:** `~/Development/siren`

Three PSX-era Square RPGs sharing one browser-facing contract:
`tools/shared/summon-sequence.ts` publishes every game's summon/GF/eidolon
timeline as a single `SummonSequence` schema (models, camera keys, effects,
audio, per-field `completeness` booleans). Each game keeps its own
`docs/<game>/psx/*.md` + `docs/<game>/TODO.md`; TODO files are the
authoritative per-item status surface, not this summary.

## Ground-truth oracles

- **Memoria** (checked out ad hoc, e.g. `/tmp/siren-memoria`) — the
  community-decompiled FF9 PC-port source (C#/Unity). Strong oracle for
  **file-format byte layout** (PC and PSX share the same asset files) but is
  a clean-room reimplementation, not the original PSX code — its own control
  flow doesn't necessarily mirror the PSX overlay, and where it hits a
  proprietary/native boundary (see below) it goes no further than this
  project can from the PSX side alone.
- **Archived "Rɘverse FF9" fan viewer** (JS; two on-disk snapshots seen so
  far, one minified one pretty-printed — diff them, they can be byte-
  identical once un-minified) — an independent, partially-complete FF9
  format viewer. Useful specifically where Memoria doesn't reach (e.g. a
  static mesh sub-format Memoria's own runtime never decodes because it
  hands the whole resource to native code).

## Solved formats

- **AKAO sequenced audio** (`docs/akao-format.md`, `tools/shared/akao*.ts`)
  — Square's in-house sequenced-music/SFX format, shared across all three
  games but NOT byte-compatible between them. FF8/FF9 share a "v3" 0x40-byte
  header + track-offset table, byte-for-byte identical between the two
  games (the documented "3.1 vs 3.2" split lives entirely in the
  opcode/event grammar); FF7 uses an older, shorter "v1.0" 0x14-byte header
  (VGMTrans's version family). Both header families' sequence-body opcode
  grammars are corpus-confirmed at 100% zero-deviation byte-width decode
  (FF8+FF9: 9,832 real v3 tracks across both games' full 4-disc corpora;
  FF7: 17,672 real v1 tracks, Disc 1's full 613-field-DAT corpus). FF8/FF9
  additionally have a separate AKAO-magic "sample bank" sub-format (shared
  PADBUG/dir09 container) holding real PSX SPU 4-bit ADPCM waveform data +
  a per-instrument record table (`tools/shared/akao-sample-bank.ts`,
  standard non-AKAO-specific PSX codec). **FF7's own, structurally
  different global instrument bank** was located and substantially decoded
  this pass: `SOUND/INSTR.DAT` (128×64-byte records, 93 real, contiguous
  from index 0) + `SOUND/INSTR.ALL` (raw ADPCM waveform blob, its own tiny
  8-byte leading micro-header aside) — NOT inside any per-field `.DAT`, a
  disc-wide shared resource. Each record: `[u32 sampleStart][u32
  sampleEnd]` (absolute offsets into `INSTR.ALL`) + a 12-entry `u32`
  chromatic SPU pitch-register lookup table, confirmed via an aggregate
  whole-corpus ratio match to 2^(1/12) (5ppm) plus the PSX SPU's own
  literal `0x1000` unity-pitch constant appearing verbatim in a smaller
  sibling bank (`INSTR2.DAT`/`INSTR2.ALL`, 6 real records) — see
  `~/.claude/agents/game-re-lessons/aggregate-ratio-across-corpus-confirms-closed-form-constant.md`.
  Instrument selection is decisively confirmed (not just plausible): the
  already-known `PROGCHANGE` opcode's param byte falls in `[0, 92]` across
  24,487/24,487 real occurrences, exactly `INSTR.DAT`'s real record range.
  `DRUM_ON`'s self-relative offset is now confirmed to resolve to a LOCAL
  per-resource drum table (not the global bank) via a decisive
  multi-occurrence-convergence check (615/615 real occurrences in-bounds;
  see `~/.claude/agents/game-re-lessons/multi-occurrence-convergent-target-confirms-self-relative-pointer.md`)
  — that local table's own byte grammar remains undecoded.
  `tools/shared/akao-render.ts`'s debug renderer now covers all three
  games (`renderAkaoV3Sequence` for FF8/FF9, `renderAkaoV1Sequence` for
  FF7) — real audible renders confirmed via RMS/distinct/autocorrelation
  on decoded samples for all three, though FF7's short (1-2 ADPCM block)
  loop-seed records need tiling to fill a note's duration, or the render
  is >99% silent despite the underlying samples passing every per-sample
  audio-quality check — see
  `~/.claude/agents/game-re-lessons/sequencer-silent-despite-passing-per-sample-audio-check.md`.
  Open: FF7's local drum-table grammar, `INSTR2.ALL`'s sample-range
  discrepancy (only 1/6 real records validate against its own length),
  FF8/FF9's own instrument/drumkit table (`akao-instruments.ts`, a
  concurrent/separate pass), and both games' remaining per-record ADSR-
  shaped fields.
- **FF9 dir13 special-effect archive** (`tools/ff9/sfx.ts`,
  `docs/ff9/psx/sfx-format.md`): an IMG Type-3 folder, 511 logical slots,
  372 populated per disc, byte-identical across all 4 discs. Container:
  chunk table + sector counts at `0x000`, a 3-byte `(opcode,arg1,arg2)`
  command stream at `0x400` terminated by opcode 0, sector-aligned chunk
  resources from `0x800`. A resource with `id==2` is a small-file table
  (4-byte offset/flags entries; duplicate offsets alias, `flags==0xffff`
  means external). Ported from Memoria's `SFXBinaryFile.cs`. All 33 known
  eidolon variants (Shiva/Ifrit/Ramuh/Atomos/Odin/Leviathan/Bahamut/Ark/
  Carbuncle x4/Fenrir x2/Phoenix x2/Madeen, full/short/special forms)
  publish lossless `SummonSequence` timelines with real camera and audio
  decode.
  - **Model-effect dispatch (opcodes 0x80-0x87) is a closed-native-code
    boundary, proven not inferred**: Memoria's own `SFX.SFX_Play()` passes
    the *entire* raw archive, byte-for-byte, into
    `[DllImport("FF9SpecialEffectPlugin")]` — a closed DLL with no source
    in the Memoria tree. Memoria's own `SFXBinaryFile.cs` never reads an
    0x80-0x87 target resource's content. See
    `~/.claude/agents/game-re-lessons/native-plugin-dispatch-erases-resource-kind-signal.md`
    for the generalizable shape of this finding: the opcode, `arg2`, and the
    small-file table's `flags` all carry **zero** resource-kind signal —
    classification is only possible by sniffing each referenced resource's
    own leading bytes. Real corpus census (126 dispatch commands, 33
    variants): 108 opaque `native` parameter blocks (still unrecoverable
    without the closed overlay), 14 `"AKAO"`-magic audio cues, 4 `0x6f73`
    ("so")-tagged static meshes — the last independently corroborated by
    the Rɘverse viewer's own `type===0x6f73` check, and decodable by
    slicing past a tiny material-table header and feeding the remainder
    straight into the already-solved dir07 mesh reader below, unmodified.
- **FF9 dir07 battle mesh + animation** (`tools/ff9/model.ts`,
  `tools/ff9/gltf.ts`, `tools/ff9/vram.ts`): type-0x02 mesh + type-0x03 pose,
  TIM/VRAM material baking (`Ff9Vram`, `parseFf9MaterialInfo`), combat-name
  join via dir05 enemy records. 182 deduplicated skinned battle GLBs, 2,729
  source-owned clips (eight zero-sized alias exceptions, one malformed/
  incompatible clip, both evidence-based rejections not guesses). Type-C
  polygon records are a known, explicit unsupported case (both here and in
  the Rɘverse viewer independently) — not a bug to chase.
- **FF7 player summons** (`tools/ff7/summon.ts`): all 16 map to
  `SummonSequence` inventories with embedded rigid geometry; runtime
  timing/camera/VFX/audio still needs overlay emulation (`ff7-magic-model`,
  `partial`). FF7 battle models: 353 mesh-bearing ENEMY payloads export
  skinned GLBs with all 4,428 applicable clips (`ff7-battle-model`,
  `resolved`).
- **FF8** (`tools/ff8/*`): LZS/LZK compression, battle DAT model format
  (`lzk-format.md`), 16 junctionable GFs + 6 non-junctionable summons have
  `SummonSequence` source inventories with real file-based textured/skinned
  GLBs; the shared-cinematic bone-motion opcode VM (`MAG*.X` overlay) has
  its core, integrator, bone struct and generic bone-motion opcode family
  (10-23) solved and confirmed (`ff8-mag-opcode-vm`) via a prior
  `re-codebreaker` escalation — ~90 non-generic opcode handlers remain open.

See each game's `docs/<game>/TODO.md` for exact current per-item status —
this file is a map, not a mirror.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/siren` | Final Fantasy VII, Final Fantasy VIII, Final Fantasy IX (all PSX) — a unified `SummonSequence` contract (`tools/shared/summon-sequence.ts`) publishes every game's summon/GF/eidolon timelines; FF9's dir13 special-effect archive (chunk table + 3-byte command stream + small-file table) and dir07 type-0x02/0x03 battle mesh+animation (182 skinned GLBs, 2,729 clips) are solved, with the archive's opaque "native model-effect" majority proven (not just inferred) to require the closed original-platform SFX overlay via a P/Invoke trace in the community Memoria PC-port source; FF8's LZS/LZK compression and battle DAT model format solved. The shared Square in-house `AKAO` sequenced-audio format is solved across all three games (`docs/akao-format.md`) — FF8/FF9's "v3" header+opcode grammar and FF7's older "v1.x" header+opcode grammar are both corpus-confirmed (100% zero-deviation byte-width decode on 9,832 v3 tracks + 17,672 v1 tracks); FF8/FF9's separate waveform sample-bank sub-format is decoded (standard PSX SPU ADPCM, corpus-verified real audio) and, for FF7, a previously-missing GLOBAL (disc-wide, not per-field) instrument/waveform bank was located at `SOUND/INSTR.DAT`+`INSTR.ALL` and substantially decoded — 93 real instrument records, a well-supported 12-tone equal-temperament SPU pitch-register table (confirmed via an aggregate whole-corpus ratio match to 2^(1/12) to 5ppm, see `aggregate-ratio-across-corpus-confirms-closed-form-constant.md`), and a corpus-decisive `PROGCHANGE`-opcode→record-index binding (24,487/24,487 real occurrences in range) — giving FF7 field BGM its first real, audible debug render (`tools/shared/akao-render.ts`'s `renderAkaoV1Sequence`). Key oracles: the Memoria decompiled C# source (file-format-compatible PC-port reimplementation, not the original PSX code) and an archived "Rɘverse FF9" fan viewer covering some formats Memoria doesn't reach | `game-re-corpora/siren.md` |
