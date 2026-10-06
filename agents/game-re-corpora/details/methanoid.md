# methanoid — corpus notes

Project: `~/Development/methanoid`. Games in this one repo: **Millennium
2.2** (Novagen Software), **Deuteros** (Novagen Software), and **Reunion**
(Amnesty Design) — all Amiga. Full byte-level evidence lives in each game's
own `docs/<game>/<platform>/data-structure.md` — this file is a
pointer/summary for cross-project reference, not a duplicate of those specs.

> **Correction:** an earlier pass of this file placed Deuteros in a separate
> repo, `~/Development/deuteros`. That directory does not exist — Deuteros's
> data (`data/deuteros/amiga/`) and docs (`docs/deuteros/`) live inside this
> same `methanoid` repo, alongside Millennium 2.2 and Reunion. Fixed below.

## Status — Millennium 2.2

- Data: `data/millenium22/amiga/Disk.1` (754688 B — non-standard, 67 of 80
  cylinders present) and `Disk.2` (5632 B — one track).
- Confirmed **unrelated at the boot-loader level** to this same repo's other
  Novagen-era-adjacent Amiga game, Deuteros (see below — no shared strings/
  code/protection scheme found at the boot-block level; treat any assumed
  engine sharing between historically-adjacent titles as a hypothesis to
  verify, never a given). Both games' mini-loaders do independently exhibit
  the same "Disc Company" illegal-vector-hijack anti-debug technique though
  (see Deuteros's status below) — plausible evidence of a shared licensed
  protection toolkit even where the surrounding boot-block code differs.
- `Disk.1`'s boot-block loader chain **solved end to end**: `BB_ENTRY`
  confirmed at file offset `0xC` (RKM-derived — see
  `amiga-bb-entry-offset-is-12-not-4.md`), a self-relocating stub copies a
  974-byte second stage from `Disk.1[0x32,0x400)` to absolute `$66032` and
  jumps in (see `self-relocating-boot-stub-invalid-past-jmp.md`, first
  documented from this game). That stage hand-builds `trackdisk.device` I/O
  structures directly (no exec.library convenience calls beyond raw LVOs:
  `FindTask`, `AddPort`, `OpenDevice`, `DoIO`, all offset-cross-checked
  against the RKM), then does two literal, disassembly-confirmed on-disk-1
  reads: one loading a "mini-loader" to `$41000` (source disk block 880,
  ~27 tracks), one loading the final program to `$68000` (source disk block
  179, 2 tracks, permanent tail-jump). Both reads source `Disk.1` itself —
  **the boot block never reads `Disk.2`**.
- The mini-loader (`$41000`) begins by installing a handler on the CPU
  illegal-instruction vector (`$10.l`), deliberately executing an `illegal`
  opcode to trigger it, then restoring the original vector — a multi-vector
  (also `$20.l`/`$24.l`, privilege-violation/trace) anti-debug armor
  technique. Structurally confirmed; handler bodies not semantically
  decoded this pass.
- **`TDIC` track**: disk track 1 (blocks 11–21, `Disk.1+0x1600`–`0x2C00`) is
  filled with exactly 1408 repeats of the 4-byte ASCII tag `"TDIC"` — one
  full track, immediately after the boot track. `io_Command` `$8002`/
  `$8003`/`$8004` turned out to be the **standard** `trackdisk.device`
  extended commands (`ETD_READ`/`ETD_WRITE`/`ETD_UPDATE`), not a private
  scheme — an earlier "unexplained private command" reading came from a
  wrong `CMD_READ` constant, corrected by a `re-codebreaker` escalation.
  **Consumer question settled by exhaustive static search AND a real
  dynamic trace**: a structurally near-perfect candidate routine exists
  (`$6628C` — reads one track through a private staging buffer, then
  unconditionally copies exactly 1408 longwords out, matching TDIC's own
  repeat count exactly) but is confirmed to have **zero callers**
  anywhere in the present 754,688-byte dump — 0 literal `JSR`-absolute
  hits, 0 raw-address-as-data hits, and (a later pass) 0 register-indirect
  calls either (a full linear disassembly of the entire 975-byte, not
  974 — `dbra` loop-count arithmetic — boot blob found only 2 indirect
  calls total, both resolving to already-known literal targets, not this
  routine). No other code anywhere in the file ever issues a track-1 read
  via any of the 8 known track-I/O primitives either. A later session
  closed the remaining static-analysis gap with a purpose-built Musashi
  boot-chain harness (`tools/millenium22/emu/`, generalizing the Deuteros
  harness pattern to run the *whole* boot chain as real executed
  instructions, not a hand-spliced subroutine call): across 3+ billion
  real emulated instructions, `$6628C` is never reached and never written
  to. That same harness also found and fully reconstructed a second,
  previously-undocumented self-decrypting-code region in the mini-loader
  (mem `$0410FE`–`$0415A6`) using the identical "DISC COMPANY"
  trace-vector technique already documented for Deuteros — a new,
  dynamically-confirmed engine/protection-family link between the two
  games despite no shared boot-block string marker — and searching its
  reconstructed plaintext found zero references to `$6628C` either.
  Residual uncertainty: the harness's synthetic hardware stub can't fully
  satisfy the mini-loader's real CIA-B disk-index-pulse timing gate, so
  it never escapes that retry loop to reach boot-time read #2 or the main
  game image at `$68000`+ — a caller living past that point, or in the
  still-missing truncated tail, remains open. See
  `~/.claude/agents/game-re-lessons/m68k-trace-vector-decrypt-needs-emulate-trace-on.md`
  for the plaintext-reconstruction technique and
  `~/.claude/agents/game-re-lessons/mistyped-base-constant-underflows-capture-buffer-bounds-check.md`
  for a real bug hit while building it.
- **`Disk.2` resolved, not a bad dump**: its only non-zero content is 4
  bytes (`0x3FC`–`0x3FF`, value `0x16C65710`) — this exact constant is what
  `Disk.1`'s own code checks via a masked `cmp.l` immediate at
  `Disk.1+0x35A0`/`0x35D4`, right alongside the UI strings `"FORMAT M2.2"`,
  `"DISK FORMATTER"`, and `"NOT AN M2.2 DISK"`. Millennium 2.2 is known to
  ship an in-universe disk-formatter feature; `Disk.2` is a blank disk
  stamped by exactly that feature, not corrupt/incomplete data. This is a
  clean worked example of the "cross-file magic-number correlation" oracle
  — a mostly-blank sibling file's one nonzero region, searched for
  byte-exact in the main file's own code, decisively explains what the
  blank file is for.
- **Truncation status still open, assessed as likely real data loss**:
  `754688 = 134 × 5632` — an exact track boundary (67 of 80 cylinders),
  consistent with a deliberate "captured N cylinders" dump, but the file's
  last 4096 bytes are 3987/4096 non-zero with no blank-tail taper (dense
  content right to the literal last byte) — weighing against "benign,
  unused tail dropped." A later pass added corroborating (not new-proof)
  evidence: high tail entropy (~7.04 bits/byte, no long printable run) and
  confirmation that the game routinely issues large runtime reads deep
  into the disk (two newly-catalogued reads at tracks 24 and 110, both
  inside the present dump) — raising the prior that the missing 13
  cylinders held real content too. **Not resolvable by further static
  analysis; needs a fresh disk image.**
- **First confirmed content-asset format**: two real 16-colour `amiga12`
  palette tables (`Disk.1+0x2c2c`, `Disk.1+0x181a8`), each fed to a
  disassembly-verified `LoadRGB4(vp, colors, count=16)` call (LVO `-0xC0`,
  same convention as Deuteros) — found via a whole-file raw-byte scan for
  the LVO call opcode, then A6-provenance-traced back to a real
  `OpenLibrary("graphics.library")` return-value store (not just an
  opcode-pattern match — see `lvo-byte-pattern-false-positive.md`). No
  picture/bitmap format is confirmed yet, so these ship as viewer
  "Data"-tab records (`public/assets/millenium22/amiga/data/
  palette_{a,b}.json`) rather than `manifest.json` sprite/screen entries —
  worth reusing as a pattern on other still-picture-less games in this
  family: ship a confirmed non-picture decoded table via the Data tab
  instead of forcing a fake atlas entry.
- **Confirmed audio content and a fully decoded sound-driver command
  grammar**: a real, disassembly-verified 4-channel Paula software audio
  driver (two byte-identical copies at different load addresses) feeds two
  confirmed digitized-PCM sample blobs (`sample_bank_1` 109,844 B,
  byte-identical across both driver copies; `sample_bank_2` 3,308 B,
  found only in the second copy, apparently cut off by the disk's own
  truncation) — shipped as the game's first `manifest.json` audio entries.
  A later session fully decoded the driver's per-voice command-byte-stream
  opcode grammar (notes; a 12-entry sub-command jump table covering
  vibrato/rest/portamento/transpose/sequence-splice/full-stop; arpeggio-
  table-select and envelope-table-select, 16 slots each; instrument-select,
  48 slots; note-duration-set, 32 levels) and the envelope-table byte
  grammar (0-127 magnitude, bit-7 = permanent hold/sustain marker),
  confirmed byte-exact by resolving all 16 real envelope curves via the
  driver's own otherwise-untraceable base register (solved algebraically
  from one already-known content anchor — see
  `unrecoverable-base-register-solved-from-single-content-anchor.md`,
  sourced from here) into real ADSR-style decay-to-sustain shapes. Shipped
  as two new "Data tab" tables, `note_pitch_table.json` (36 entries,
  confirmed) and `envelope_curves.json` (16 entries, confirmed). The
  arpeggio-table's own byte-stream *content* resolved less cleanly via the
  same base register and is flagged rendered, not confirmed. The
  instrument-table's 12-byte record *format* (absolute sample ptr / loop
  offset with a no-loop sentinel / length / tuning) is confirmed from
  consumer disassembly, but its on-disk *content* past 5 legitimately-empty
  slots is confirmed placeholder/uninitialized-at-rest — proven by byte-
  identical content across the two differently-loaded driver copies, which
  would need different absolute pointers if the data were real (see
  `relocation-invariant-content-across-copies-proves-placeholder.md`,
  sourced from here) — so exact per-instrument sample segmentation remains
  open pending a traced runtime init path or a dynamic capture. A separate
  structural pass on the ~400 flavour-text strings found no centralized
  string table at all (a gap-histogram over 1,831 candidate strings found
  no dominant stride, and sampled strings are individually NUL-terminated
  with no shared header) — settled as "scattered literals referenced
  per-call-site", not an open search.
- **Pipeline registered**: `tools/millenium22/export-game-data.ts` +
  `build-assets.ts`, `supported: true` in `tools/shared/game-config.ts`.
- **Confirmed NOT a Mercenary-style 3D/2D wireframe vector engine** (an
  earlier session's reframe investigation, prompted by the shared Novagen
  developer): a whole-file LVO byte-scan for every graphics.library line/
  polygon-drawing primitive (`Move`/`Draw`/`AreaMove`/`AreaDraw`/`PolyDraw`/
  `RectFill`/etc.) plus a BLTCON0 hardware-register scan both came back
  zero hits — see `engine-family-shared-decoder-not-shared-container.md`'s
  3rd instance. What the game does have instead: a runtime polar-coordinate
  (sine/cosine lookup table) point-plotter, and a genuine 39-record
  object-record table (position/size/4-bit colour/visibility flag) —
  **corrected in a later session**: this is not a custom box-fill renderer
  but a real **draggable hardware-sprite cursor/slider** (traced past the
  dispatcher to 4 independently-resolved LVOs, `GetSprite`/`FreeSprite`/
  `ChangeSprite`/`MoveSprite`, all argument-consistent against the
  confirmed live screen's own `ViewPort`); the "exceeds 320x200" puzzle
  was an axis-transposition-plus-scale artifact, not a second canvas —
  recomputed correctly, 0/39 records fall outside the real screen. A
  second, 61-record, line-segment-endpoint-shaped table (Finding C) still
  has no traced consumer after 4 independent exhaustive search techniques.
  See `docs/millenium22/amiga/data-structure.md` § "Vector/geometry
  investigation".
- **Compressed pixel-art bank — SOLVED** (a later session, hunting by
  direct analogy once Deuteros' own hidden-art corpus turned up in this
  same repo): confirmed Millennium 2.2 carries a **byte-for-byte copy of
  Deuteros' own RLE-over-16-bit-words codec** (same token grammar, and the
  identical `heightWord >= 0xC8` plane-layout threshold constant occurring
  exactly once in the whole file) — found not by re-deriving from scratch
  but by a **register-linked opcode-word scan** for the exact instruction
  shape of Deuteros' token-dispatch prologue (`MOVE.B (An)+,Dr / MOVE.B
  Dr,Dc / ANDI.B #$C0,Dr / Bcc`, checked across every register combination,
  not disassembly-alignment-dependent). The container is a raw disk block
  (`Disk.1+0x21000`: 4-byte header + 160-slot directory + record pool)
  loaded fresh at runtime via `AllocMem`+`ETD_READ`, so it decodes straight
  from the flat file with no emulation needed — 135/136 real image slots
  decode byte-exact against the shared container invariant, rendering as
  unmistakable real game art (a labelled space-station management screen
  with `LIFE SUPPORT`/`ENERGY`/`RESEARCH`/etc. panel buttons, a `PROBE`
  schematic, a moon-surface texture, a console-room interior). Also
  **corrected** a prior session's "zero references to the screen buffer,
  therefore no static picture" verdict: that census only checked `DoIO`-
  destination references and missed the art renderer's own general
  compositing reference to the same buffer — a second corroborating
  real-world instance of `disc-io-census-blind-to-already-loaded-data-
  consumer.md`'s lesson, this time for a buffer-reference census rather
  than a disc-I/O-call census. A separate, more-exhaustive whole-file
  literal scan for the `DoIO`/`SendIO`/`CheckIO`/`WaitIO`/`AbortIO` LVO
  opcodes themselves (not scoped to an assumed 8-primitive caller list)
  independently confirmed **no** Deuteros-style uncatalogued disk reader
  exists in this game — the hidden art is reached through the
  already-documented `ETD_READ` wrapper, not a new reader. The shared
  codec was refactored out of `tools/deuteros/graphics.ts` into
  `tools/shared/amiga-rle-gfx.ts` with zero behaviour change (Deuteros' own
  pipeline re-verified byte-identical: 211/211, 30/30, 6/6 records), and
  shipped for Millennium 2.2 via `tools/millenium22/graphics.ts` as
  `public/assets/millenium22/amiga/sprites/gfx_main.png` (135 images). See
  `docs/millenium22/amiga/data-structure.md` § "Compressed pixel-art bank
  — SOLVED".

## Where to look next (Millennium 2.2)

- `docs/millenium22/amiga/data-structure.md` — full byte tables, LVO
  cross-checks, and the paths-tried table.
- `docs/millenium22/TODO.md` — current open items.

---

# Deuteros (Novagen Software), Amiga

Project: same repo, `data/deuteros/amiga/Disk.1`+`Disk.2` (two standard
880K/1760-block floppy dumps, 901120 B each). Full byte-level evidence:
`docs/deuteros/amiga/data-structure.md`; open items (ID-based table):
`docs/deuteros/TODO.md`.

## Status

- **Disk.1's boot-block loader chain traced end to end from BB_ENTRY through
  real game-engine code.** `BB_ENTRY` confirmed at file offset `0xC` (RKM-
  derived, matching `amiga-bb-entry-offset-is-12-not-4.md` — a prior pass's
  claim of offset 4/RTS-at-`0x92` was independently re-checked and found
  wrong, corrected in place to `0xC`/RTS-at-`0x9C`). Chain: boot block
  (blocks 0-1) → mini-loader (blocks 22-43, loaded to `$12800`, entered via
  the RKM's D0=0/A0=completion-function boot-success convention) → its
  6-entry mode-dispatch jump table → track-4 blob (blocks 44-76, loaded to
  `$20000`) → confirmed real game-engine code (direct writes to hardware
  `$DFF096`/`$DFF09A`, DMACON/INTENA). The `io_Command` scheme driving every
  read is **standard AmigaOS trackdisk.device**, not private (`$8002`=
  `ETD_READ`, `$8003`=`ETD_WRITE`, `$8005`=`ETD_CLEAR`, all `TDF_EXTCOM`-
  flagged extended commands — an earlier "private/non-standard" read was
  overturned by a `re-codebreaker` escalation this session, see below).
- **No real HUNK executable exists on either disk** (2 coincidental
  `0x000003F3` byte matches per disk, all false positives — the required
  following-longword-must-be-0 check fails every time). The whole game is a
  chain of raw flat 68k blobs loaded to fixed memory addresses. `ancient
  identify` found no compression on either whole disk or 2 sampled blobs.
- **The mini-loader's illegal-instruction-vector-hijack (see
  `illegal-vector-hijack-anti-debug-desyncs-disasm.md`) is fully decoded —
  SOLVED, not just structurally confirmed.** A `re-codebreaker` escalation
  built a real headless Musashi 68000 emulation harness
  (`tools/deuteros/emu/`, vendored fresh, `M68K_EMULATE_TRACE`/
  `M68K_INSTRUCTION_HOOK`/`M68K_EMULATE_ADDRESS_ERROR` all turned on — see
  the new pitfall this surfaced, `m68k-trace-vector-decrypt-needs-emulate-trace-on.md`)
  that ran the real routine (Disk.1's `$131AE`, the actual "DISC COMPANY
  010991" copy-protection check) instead of hand-disassembling it, and
  dumped a 2,094-line decrypted disassembly
  (`build/cache/deuteros/amiga/protection-decrypted.asm`). Mechanism: a
  3-layer CPU-identification probe → a self-decrypting trace-vector-driven
  loop (each single-stepped instruction XOR-decrypts the next few bytes,
  which is exactly what defeated linear/static disassembly) → a direct CIA
  floppy-hardware timing measurement compared against magic constant
  `$DA8DBFDB`. **Independently spot-verified this session** (not just
  trusted): the magic constant is byte-exact at `Disk.1+0x3EDA` and
  genuinely absent from all of Disk.2 (0 hits) — a real structural
  discriminator; the emu harness, vendored Musashi, and decrypted-asm
  output all exist on disk exactly as claimed; the Musashi config flags
  are set exactly as claimed; and 4 claimed writer sites for global
  `$12FFC` (`Disk.1+0x72A6`, `+0x92F9E`, `+0x93066`, `+0x93096`) all
  contain the literal immediate `$12FFC` byte-exact — overturning the
  original "written once, by the boot block only" claim (index 1 of the
  mode-dispatch table, gated by this handler, IS reachable during normal
  play, not just at cold boot).
- **"Disc Company"** (the boot block's own embedded string,
  `"DISC COMPANY 010991"`) has no external documentation — a `WebSearch`
  this session found nothing beyond unrelated Rob Northen Copylock material.
  Treat as an undocumented/bespoke or obscure protection scheme. The shared
  raw-trackdisk-open idiom and the illegal-vector-hijack technique, both
  also present in Millennium 2.2's unrelated loader, are circumstantial
  evidence it's a shared licensed toolkit rather than bespoke-per-game code
  — not proof.
- **Disk.2**: not DOS-bootable (`"DEU\0"` tag only). Confirmed to carry
  genuine confirmed swap-prompt strings and `/CHNG`-polling code (who calls
  the re-load is still open, see `docs/deuteros/TODO.md`); also a real
  second copy of the I/O-library bring-up code on its own track 1, and a
  `$16C65710` magic longword at `Disk.2+0x1604` matching a constant
  Millennium 2.2's own code independently checks (cross-project coincidence,
  not pursued further — plausible evidence of a shared in-house
  disk-tooling chain, not proof). The mode-dispatch index-1 track-80 read
  was originally hypothesized as the Disk.2 access point; corrected
  arithmetic (`80×0x1600=0x6E000`, ending at `0xDAA00`, exactly one track
  short of Disk.1's own `0xDC000` extent — independently re-derived and
  confirmed this session) refutes that: the read never leaves Disk.1.
- **The repeating short-record table (Disk.1 track 0 + tracks 138-142,
  Disk.2 tracks 0/6/10) is refuted as protection-tool template padding.**
  A 12-byte dominant autocorrelation period, a cross-check finding zero
  matching markers on the sibling Millennium 2.2 project's own Disk.1 (no
  shared-vendor-template signature), and a byte-identical 780-byte match
  between the track-0 region and a location inside the actually-loaded
  track-80 payload (`Disk.1+0xC10F0` → memory `$66000`, resolving a
  previously-unexplained fixed source address) together show this is real
  (stale-duplicated) game data, not padding. Content class still unknown.
- **The track-8 320x200x4bpp title/credits picture's palette is SOLVED and
  shipped as Deuteros' first confirmed asset.** Disassembling the mini-
  loader's deinterleave subroutine (file offset `0x1442`, memory `$13C42`)
  found a `LoadRGB4(vp=$12E12, colors=$20000, count=16)` call — LVO
  `-0xC0`/`-192`, argument order and count cross-checked against both the
  RKM autodoc and a published graphics.library LVO table — reading exactly
  the 16 big-endian `amiga12` words (32 bytes) the deinterleave loop itself
  skips at the front of the source buffer. Decoding with this palette
  renders a fully legible, domain-correct title/credits screen ("DEUTEROS
  THE NEXT MILLENNIUM", Ian Bird/Tai Redman/Matt Bates, "AN ACTIVISION
  PRODUCTION") — strictly stronger than the prior session's index-histogram-
  only render, and satisfies the ground-truth bar outright (no emulator
  needed; found statically, per an explicit project-owner instruction to
  avoid Amiberry for this round). Shipped:
  `public/assets/deuteros/amiga/screens/title.png` +
  `palettes/title.json`.
- **A real `exportGameData`/`buildAssets` pipeline is now registered**
  (`tools/deuteros/export-game-data.ts` extracts Disk.1 block 88 (`0x8400`
  bytes) to `build/cache/`; `build-assets.ts` decodes the picture above).
  `supported: true` in `tools/shared/game-config.ts`. Registering it
  surfaced two real bugs, both fixed project-wide: the
  `cli-script-main-fires-on-import.md` suffix-guard bug (Reunion's own
  scripts were already latently affected, only triggered once Deuteros
  became a second game sharing the config module's import graph), and a
  `@seer-project/pipeline` gotcha where a raw-boot game with no HUNK
  executable needs an explicit non-executable anchor file
  (`executable: 'Disk.1'`) or the export stage is silently skipped.
- **Disk.2's swap-back reload mechanism SETTLED (not just traced)**: the
  full handler at `$219F8`-`$21AAA` was disassembled end to end from the
  already-located swap-detection polling site. A whole-disk literal-address
  census of global `$219F4` (its only 3 references anywhere) proves it can
  only ever be written `1` or `5` — both already-documented dispatch
  indices that read only track 80. **Disk.2's mini-loader and its track-1
  I/O library are never reloaded**; the game re-enters the resident
  mini-loader via mode-index re-entry, full stop.
- **`Disk.1+0x8A64E`'s dynamic (runtime-track-number) reader SETTLED via a
  structural proof, not exhaustive tracing**: its computed disk offset is
  always `$29400 + (non-negative term)`, which structurally excludes track
  0/1 regardless of what value the runtime track-number table ever holds.
  Cross-checked against a whole-disk opcode census: the only other
  `mulu.w #$1600,d0` site belongs to the already-solved index-5 mechanism.
- The repeating short-record table's content class remains open, but
  advanced: it's now confirmed **loaded into live game memory** (not stale
  disk residue) because it sits on the confirmed-reachable index-5 load
  path. An image/graphics-format hypothesis was tested this session (byte-
  per-pixel and 16x14x4bpp-icon renders) and set aside — both gave pure
  noise; per-column byte statistics instead support a record/table
  interpretation. True semantic class (stats? entities? script?) still
  undetermined.

- **Breadth-first asset sweep (later session)**: shipped Deuteros' first
  audio assets and 3 more confirmed palette tables. An exhaustive whole-disk
  `LoadRGB4` opcode scan (28/28 hits on both disks structurally verified via
  GfxBase/ViewPort provenance, not just opcode match) found 4 new confirmed
  UI palette tables (a base 8-colour HUD palette + its 3-frame blink-cycle
  table, and a 16-colour "alarm" palette pair differing only in its first 4
  colours) — shipped via the Data tab, `millenium22`'s "confirmed palette,
  no picture" precedent. Found and structurally confirmed a real, installed
  4-channel Paula sound/music driver (VBlank-vector-hooked, tracker-module-
  shaped: sample-header table + pattern/command stream) — "Music by Matt
  Bates" is a real working subsystem, not vestigial; its module base
  pointer/sample table location is not yet pinned (open,
  `deuteros-sound-driver-module`). A real-signal audio oracle (RMS/distinct-
  values/autocorrelation) plus an FFT tonal-peak/mean ratio check (vs. a
  known-code control) found 13 audio-shaped candidate regions (304 KB total
  across both disks), shipped as WAV with an explicit approximate-rate
  caveat (`sample rate 8287 Hz`, same convention as this file's own
  Millennium 2.2 sample-bank entries). IFF/8SVX/ILBM/ANIM scan: conclusive
  negative (2 coincidental `FORM` substring hits inside plain text, no real
  IFF anywhere). Also found a genuine, previously-undocumented multi-
  language (French + German) UI string table filling most of the disk
  region between the title picture and the track-80 payload — no traced
  loader read reaches that region, which turned out to mean "not yet
  traced," not "filler" (see the new `no-traced-reader-region-is-not-proof-
  of-filler.md` lesson). Full account: `docs/deuteros/amiga/data-
  structure.md` § "Breadth-first asset sweep"; open items:
  `docs/deuteros/TODO.md`.

## Where to look next (Deuteros)

- `docs/deuteros/amiga/data-structure.md` — full byte-level boot-chain
  trace, LVO cross-checks, the `$131AE` protection-routine section, the
  `LoadRGB4` palette trace, the swap-back handler listing, the dynamic-
  reader structural proof, and the paths-tried table.
- `docs/deuteros/TODO.md` — current open items (ID-based table): CIA
  hardware-measurement value recovery (deferred to `re-codebreaker`, needs
  real CIA/Paula emulation), and the repeating-record content class.
- `tools/deuteros/trace-boot-chain.ts` — reproducible extractor for every
  raw blob cited in the spec (`npx tsx tools/deuteros/trace-boot-chain.ts`).
- `tools/deuteros/export-game-data.ts` / `build-assets.ts` — the registered
  pipeline (`npm run extract-data`).
- `tools/deuteros/emu/` — the vendored Musashi 68000 emulation harness that
  cracked the copy-protection routine (`emu.c`, `build.sh`, `musashi/`).
  Reusable pattern for any other trace-vector-driven self-decrypting code
  in this corpus; flag as an upstreaming candidate per
  `game-re-tooling/seer-upstream.md` if a second game needs the same
  technique.

---

# Reunion (Amnesty Design), Amiga AGA — solved end to end; OCS/ECS floppy release — substantially solved

Project: same repo, `data/reunion/amigaaga/` (an already-unpacked AGA install
tree, not raw floppy images — `game.exe`/`intro.exe` + ~20 Hungarian-named
data subdirectories). Full byte-level evidence:
`docs/reunion/amigaaga/data-structure.md`; open items:
`docs/reunion/TODO.md`. Unrelated to Millennium 2.2/Deuteros above beyond
sharing this repo and the AGA-era Amiga platform.

## Status

- **Container, both stages, fully solved and shipped.** All 511 original
  files decompress via one code path: `ancient` auto-detects RNC1 (both
  `.exe`s, confirmed Hunk executables post-unpack) vs. IMP!/File-Imploder
  (507 data files) from magic bytes alone, no extension-based branching
  needed. 2 files (`save/SaveGame.000`, `sound/RESOUNDS.075`) turned out
  genuinely raw/uncompressed despite one being previously mis-documented as
  IMP!-wrapped (its real first 4 bytes are literal ASCII `"dumm"`, not
  `"IMP!"` — corrected in place in `data-structure.md` with a `>
  **Correction:**` block, not silently edited away).
- **Asset formats fully solved and shipped**: IFF `ILBM` (planar) and `PBM `
  (chunky) → 277 PNGs, covering every masking (0/2) and compression (0/1)
  combination present; IFF `8SVX` → 80 WAVs, verified quantitatively (no
  emulator/listening test available: RMS≈17.4, peak=85 unclipped, 139
  distinct sample values, lag-1 autocorrelation≈0.94 — real audio, not
  noise); ProTracker `MOD` confirmed byte-exact on all 9 files (both the
  `M.K.` tag and a clean `@seer-project/tracker` `Module` parse) and shipped
  raw for in-browser synthesis, closing a prior session's open "hypothesis,
  not directly verified" item.
- Added a new genuinely reusable primitive to the framework, not
  project-local: `decodeByteRun1()` in `@seer-project/iff`
  (`packages/iff/src/byterun1.ts`) — the standard EA IFF-85 ByteRun1 RLE
  codec, format-generic (any ILBM/PBM/etc BODY chunk, any project), with its
  own test suite. Use this instead of hand-rolling RLE for any future IFF
  container in any sibling project.
- **File extensions in this corpus are actively unreliable, both as format
  AND as content-category signals** — not just "wrong extension, right
  category" but "extension actively misleads which pipeline branch a file
  belongs in": a `.BAT` file is a real `8SVX` audio sample (an extension
  that reads as "not game data at all" to a naive classifier); `.RDA` files
  are chunky `PBM `, not planar `ILBM`, despite living alongside `.CHR`
  ILBMs; numeric "extensions" (`ATVEZETO.002`-`.016`, `RESOUNDS.001`-`.079`)
  are animation/sequence frame numbers, not real extensions — treating them
  as strippable extensions collapsed 15 and 80 distinct files onto one
  output name each (silent overwrite, caught only by comparing claimed vs.
  actual on-disk file counts). Fixed by dispatching purely on decompressed
  magic bytes and keeping the full basename (dots → underscores, nothing
  stripped) as the asset name.
- **Disassembly beachhead established** via the `amiga-disasm` agent, then
  independently spot-verified byte-for-byte (via `strings`, `xxd`, and a
  second independent `amitools hunktool info` run — this cross-check caught
  and fixed two minor hex-transcription typos in the subagent's own report
  before anything was written into docs as confirmed). Neither executable
  ships a `HUNK_SYMBOL` block. Confirmed: entry point/startup.o chain for
  both exes; full developer credits ("Amnesty Design") and error/UI strings;
  a confirmed asset-filename table indexing every data subdirectory at
  `game.exe` file offset `0x4DAEE`, **with its real consumer chain now fully
  traced too** (two record-index entry points → a shared DOS Open/Read/Close
  loader → a `"BMHD"`-magic scan for picture-bearing assets). `intro.exe`'s
  originally-under-explored `-preproc` pass was fixed this session: a
  hand-edited `.cnf` (`CODE $DC-$2A44` for its DATA-typed hunk 1) grew its
  disassembly from 2,026 lines/8 code islands to 4,442 lines/387 labels,
  unblocking real code-level analysis of that executable for the first time.
- **Found and fixed a real, generalizable IRA gotcha this session**: IRA's
  printed `;NNNNNN` address column is a synthetic "IRA virtual address" (each
  declared hunk's payload concatenated from 0), not the real file offset,
  whenever a `.cnf` declares more than one CODE/DATA range across more than
  one hunk — confirmed on both exes, three different per-hunk deltas
  (`game.exe` CODE hunk1 `+0x58`, DATA hunk2 `+0x8900`; `intro.exe` CODE
  hunk1 `+0x50`), each verified independently by raw byte-pattern search.
  This corrected several pre-existing `game.exe` file-offset citations in
  `data-structure.md`'s EFT!ANIM section (the container/codec logic itself
  was unaffected — see `file-offsets-vs-segment-relative.md`'s 4th
  manifestation and `game-re-tooling/amiga.md`'s IRA section for the
  generalized writeup).
- **`"EFT!ANIM"` custom animation container SOLVED end-to-end** (28 files,
  all shipped): Amnesty's in-house key-frame + delta animation. Container:
  8-byte magic, u32 BE key-chunk payload length (header-exclusive), then
  delta chunks each with a u32 BE length that INCLUDES its own 4 bytes —
  asymmetric length conventions, both traced from `game.exe`'s own two
  players. Key codec: byte RLE (`0`=end, `1..7F`=literal run, `80..FF`=
  repeat next byte op-0x80+2 times). Delta codec: BE word stream (`0`=end,
  `>=0x8000`=skip n words, else copy n words), applied to the frame from
  TWO frames back (double-buffered interleave-2). Region geometry lives in
  the player, not the file: full-screen 320x200x8 interleaved planes
  (atalk/intro) vs a 160x152x8 window at screen x=160 stored linearly
  (spwar). Decisive oracle: chunk counts from the container walk match
  frame counts hardcoded in the exe's own player parameter tables 25/25
  (21 spwar + 4 atalk), plus exact-EOF tiling and coherent renders in all
  three families. Also resolved: the atalk `SPPALI00.00n` CMAP-only ILBMs
  and the intro raw `256 x u32 00RRGGBB` `.PAL` tables are these
  animations' palettes; `SPANIM22.ANM` is a duplicate of `SPANIM14` plus
  1,692 bytes of leftover 68k code, unreferenced by the traced player.
  Decoder: `tools/reunion/eft-anim.ts` (+ tests); spec:
  `docs/reunion/amigaaga/data-structure.md` § `"EFT!ANIM"`.
- **`"AMN0"` 3D wireframe vector-model format SOLVED end-to-end** (35/37
  files; the 2 exceptions are degenerate all-`0x0101`-header placeholder
  stubs): magic + `maxVertexIndex`/`edgeCount`/2 unknown i16 header, then a
  vertex array (`{x,y,z}` i16 BE triples) and an edge array whose indices
  are stored as byte offsets pre-multiplied by 4, not raw indices. No
  reader/consumer was ever traced (the `AMN0` magic itself isn't checked
  anywhere in `game.exe`) — verified purely structurally (byte-exact size
  match + in-range edge indices, zero deviation across the corpus) plus
  coherent orthographic-wireframe renders (a ship silhouette, a dish/
  station structure, a boxy freighter hull). Shipped as
  `amn0-models.json` (hunter/carrier-command's `{verts,edges,faces:[]}`
  polygon-json convention) + per-model wireframe preview PNGs. Decoder:
  `tools/reunion/amn0.ts`.
- **`pmain/*.DAT` planet-terrain grid tables SOLVED (layout), rendered
  (semantic role)** — all 47/47 files: `u8 width, u8 height`, then a flat
  `width*height` byte grid, byte-exact zero-deviation structural match.
  Colorized renders show a coherent dithered-background + vein/deposit-
  block tile structure consistent with a planet-mining minigame, but no
  reader was traced, so semantic role stays at "rendered" not "confirmed".
  Decoder: `tools/reunion/pmain-terrain.ts`.
- **`stmap/STMAPn00.CHR` (n=1-8) raw 1bpp raster format SOLVED**, refuting
  a prior session's "raw hardware colour-word data" hypothesis: these are
  plain 1bpp bitmaps at 32 bytes/row (256px), an ordered-dither circular
  gradient pattern, found via a vertical-Hamming-distance row-width
  coherence metric and confirmed visually across 2 independent files. 8
  files, not the originally-scoped 4. Decoder: `tools/reunion/
  stmap-raster.ts`.
- **`intro.exe`'s own EFT!ANIM player traced end-to-end** (5 routines,
  matching the already-documented codec/driver shapes instruction-for-
  instruction) — confirms `intro/ANIM0054.EFT`/`ANIM0055.EFT` are played by
  a real, independently-implemented copy of the same codec inside
  `intro.exe`, not merely decodable by coincidence.
- **`grwar/GRKIEG00.CHR` SOLVED** — a second, standalone instance of the
  `stmap/STMAPn00.CHR` 1bpp dither-atlas raster format (same 256px/32
  bytes-per-row convention, same "systematic dither-stamp atlas" visual
  signature), found by re-testing the already-solved sibling format
  against it rather than inventing a new hypothesis. Shipped through the
  same `tools/reunion/stmap-raster.ts` decoder (no format-specific code
  needed).
- **`spwar/SPANIM22.ANM` CONFIRMED live, not authoring residue** — its
  1,692 "leftover" trailing bytes are a real, deliberately-executed
  native-code overlay: `game.exe` loads the file via its own asset-table
  index at a separate call site (not the already-traced animation
  player's 21-entry table), then `JSR`s directly into the loaded buffer
  at the exact byte offset the trailing bytes start — real 68k code
  implementing a save-file-creation routine (`OpenLibrary("dos.library")`
  + `Open(mode=MODE_NEWFILE)`). See
  `game-re-lessons/duplicate-asset-trailing-bytes-may-be-executed-code-overlay.md`.
- **`local/ALIEN*.CHR` species-portrait gallery + `pinfo/FAJ*LBM.PAL`
  recolor palettes — rendered, real consumers traced on both sides.**
  `ALIEN001.CHR` (the sole near-greyscale outlier among 16 uniformly
  96×145px portrait files) is confirmed as the likely shared recolor
  template: a traced portrait-blit consumer (`LAB_0C62`, real Blitter DMA
  writes) and a traced FAJ-palette-load consumer (two sites, driven by a
  per-record species-id field) both exist and are live, and applying 4
  different FAJ palettes directly to `ALIEN001`'s pixel-index buffer
  produces 4 distinct, plausible alien-skin-tone recolors of the
  identical silhouette. No single instruction ties the two together yet
  — stays at "rendered", not "confirmed".
- **SAS/C small-data (`A4`) addressing CONFIRMED NOT the primary
  data-access model** — full-corpus census (5,056 absolute-addressing
  instructions vs. 76 total `d16(A4)` accesses, 141 `A4` reloads to
  distinct targets, 65 `(A4)+` post-increment uses) settles what was
  previously a 2-data-point impression. See
  `game-re-tooling/amiga.md`'s new bullet on the reload/auto-increment
  census technique (more diagnostic than raw displacement counts alone).
- **`SECSTRT_1` (the true entry point) traced past "6,673 undifferentiated
  labels"**: CLI-argument-string setup, a triple bitplane-pointer
  Copper-list-template init (8-bitplane double/triple buffering), an
  `AddIntServer`/`RemIntServer` pair installing the game's Copper+VBlank
  interrupt-driven subsystem, a separate `graphics.library`-bypass/
  Copper-list-takeover routine, and the real boot-to-first-screen handoff
  (`LAB_026B`: raster-sync wait, installs the custom Copper list, loads
  asset index 0). Not exhaustive — the top-level game-state dispatcher
  itself isn't traced yet.
- Still open (see `docs/reunion/TODO.md` for the full list): the specific
  call site (if any) pairing `ALIEN001.CHR` with a `FAJ*LBM.PAL` index.

## Reunion — Amiga OCS/ECS floppy release

Project: same repo, `data/reunion/amiga/` — 6 raw 880K `.adf` floppy dumps
(NOT the already-unpacked AGA install tree above; a completely different
distribution: `Main.exe`/`Intro.exe`/`Text.exe`/`Install` on a standard
AmigaDOS Disk 6, plus a custom self-describing block container occupying
Disks 1-5 from file offset `0x200`). Full byte-level evidence:
`docs/reunion/amiga/data-structure.md`; open items: `docs/reunion/TODO.md`.

- **No `HUNK_SYMBOL` block on any executable** — the whole investigation
  worked from a from-scratch `HUNK_RELOC32` walk plus a `strings` pass.
- **`Install`'s 390-entry asset catalog SOLVED**: three parallel
  fixed-stride tables at hardcoded file offsets (name/18B, length/4B,
  disk+block/2B, packed as `(diskNum<<12)|blockIndex` with a `0→disk 1`
  special case). Confirmed byte-exact: `blockOffset*512` lands exactly on
  each block's own magic-tagged start for 297/298 sampled `2AM`/`1AM`
  entries. `Install` itself does zero decompression, only verbatim block
  copies. This catalog is the ONLY way to learn the exact byte length of
  the 92 `AMN`-tagged entries, which carry no on-disk length field —
  a sequential chain-walk census of the block chain silently stalls the
  first time it meets one (see
  `game-re-lessons/block-chain-walk-stops-at-unknown-sibling-block-magic.md`'s
  "Variant" section, added from this project).
- **Manual-code copy-protection prompt SOLVED**: an RNG picks a page 1-20;
  a rolling checksum of the typed (space-stripped, uppercased) answer is
  compared against a 20-entry table at `Main.exe` file offset `0x67B0`;
  verified byte-exact by hashing the real scanned manual's OCR'd
  page-footer words (all 20 match).
- **Both in-house LZ77 block-compression codecs (`1AM` backward, `2AM`
  forward) SOLVED, byte-exact** — a `re-codebreaker` escalation found both
  decompressors live in `Main.exe`'s own CODE hunk (dispatcher at file
  offset `0x7DB4`, branching on `cmpi.w #$3141`/`#$3241` — only the
  **leading 16-bit word** of the 4-byte magic, which is why an earlier
  full-3-byte-magic search across the executable had found zero literal
  references; see `game-re-lessons/magic-search-must-not-be-wider-than-codes-real-comparison-width.md`).
  Both decompressor bodies were located via a carry-chain opcode census
  (`roxr`/`addx`) after a general read-through of the plausible code
  region had missed them (see
  `game-re-lessons/carry-chain-opcode-census-locates-hand-written-bit-readers.md`).
  Verified: 48/49 outputs byte-identical to same-named files from the AGA
  release; 297/297 real blocks decode to exactly their catalog-declared
  length. Ported to `tools/reunion/amn-lz.ts`.
- **`AMN`-tagged block sub-type census fully classified, 0 unknown**: using
  the `Install` catalog's exact length as ground truth (not a bound
  heuristic) resolves all 92 entries into 4 real kinds — 35 `AMN0`
  wireframe models (reusing the AGA decoder unmodified), 21 `EFT!ANIM`
  animations (reusing the AGA decoder unmodified), 32 `pmain/*.RDA`
  chunky-bitmap icons (new decoder, width cross-referenced from AGA's
  decompressed same-named files), and 2 raw `music/*.hin` blobs (new open
  format). An earlier "maybe a terrain grid" hypothesis for one entry was
  wrong — it's actually a `pmain` icon.
- **IFF `8SVX` audio SOLVED for a new container pattern**: `SOUND/*.BAT`/
  `SOUND/*.NOR` decompress to **multiple concatenated `FORM`/`8SVX` files
  back-to-back** (not one sample per file, unlike AGA's convention) — a new
  multi-FORM walker (`tools/reunion/ocs-audio.ts`) handles it, reusing
  AGA's VHDR/BODY decode logic locally (not imported, to avoid touching
  the AGA-platform decoder file at all). 8 real WAVs shipped, all passing
  the project's real-signal audio oracle (RMS 20.8-43.5, 124-249 distinct
  values, lag-1 autocorrelation 0.90-0.95).
  - `RMAIN/OPTIONS0.CHR` (a raw planar `.CHR` screen) decoded and rendered
    as a **legible "NEW GAME / LOAD GAME" menu** (320×151px, 5 bitplanes,
    row-interleaved) — confirms the codec crack end-to-end on real
    visual content, independent of the byte-count/cross-platform oracles
    above.
- **A real `exportGameData`/`buildAssets` pipeline shipped**
  (`tools/reunion/{export-game-data-ocs,build-assets-ocs,install-catalog,
  ocs-container,pmain-icon,ocs-audio,amn-lz}.ts`, registered in
  `tools/shared/game-config.ts`, `supported: true`): 96 real assets (35
  models, 21 greyscale animations, 32 greyscale icons, 8 decoded audio
  samples) to `public/assets/reunion/amiga/`; the remaining ~290
  compressed-but-inner-format-open entries decompress cleanly to
  `build/cache/reunion/amiga/decompressed/` (389/390, only the
  known-stale `ATALK/ATVEZETO.TST` duplicate fails) for future format
  work but aren't shipped yet.
- Still open: raw planar `.CHR` screen dimensions across the corpus
  (`OPTIONS0`'s geometry is confirmed but NOT corpus-constant — only
  87/229 decompressed `.CHR` payloads even divide evenly by it);
  `GYART`/`SAVES`/etc `.DAT` tables (83 entries); `MUSIC/*.pin`/`.tbl`/
  `.hin` note-sequence format; which game/menu state gates the
  manual-code check; and the OCS/ECS palette source for `EFT!ANIM`
  playback (`SPWARSSC.CHR` turned out to be a raw planar `.CHR`, same
  open problem as the screens). See `docs/reunion/TODO.md`.

## Where to look next

- `docs/reunion/amigaaga/data-structure.md` — full byte tables, BMHD/CMAP
  offsets, disassembly citations, paths-tried table (AGA release).
- `docs/reunion/amiga/data-structure.md` — the same for the OCS/ECS
  floppy release, including the `1AM`/`2AM` codec disassembly.
- `docs/reunion/TODO.md` — current open items for both platforms.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/methanoid` | Multi-game Amiga repo (one repo, not separate ones — a prior corpus-note error placing Deuteros in its own `~/Development/deuteros` was corrected): Deuteros, Millennium 2.2 (both solidly past first-pass now — boot chains solved, pipelines registered, at least one confirmed content asset each), **Reunion** (AGA release solved end-to-end; OCS/ECS floppy release now substantially solved too, see below). Millennium 2.2's boot-block loader chain is solved end to end: a self-relocating stub copies a 974-byte second stage to a fixed absolute address and jumps into it (see `self-relocating-boot-stub-invalid-past-jmp.md`, first found here); that stage hand-builds `trackdisk.device` I/O structures (no library helpers beyond raw exec LVOs, using the **standard** `ETD_READ`/`ETD_WRITE`/`ETD_UPDATE` extended commands — an earlier "private io_Command scheme" misread was corrected by a `re-codebreaker` escalation), does two direct on-disk-1 reads (a mini-loader plus the final program, both confirmed via literal operand disassembly), and the mini-loader installs+deliberately-triggers an illegal-instruction exception as an anti-debug vector-patch trick (see `illegal-vector-hijack-anti-debug-desyncs-disasm.md`). A full disk track (blocks 11–21) is filled with 1408 repeats of the ASCII tag `"TDIC"` — a raw non-filesystem "signature track" whose consumer question is now **settled by exhaustive static search AND a real dynamic trace**: a structurally near-perfect candidate routine (reads one track via a private staging buffer, unconditionally copies exactly 1408 longwords out) is confirmed to have zero callers by any literal, absolute-data, or register-indirect reference anywhere in the 754,688-byte dump, **and** — a later session, a purpose-built Musashi boot-chain harness (`tools/millenium22/emu/`, generalising the Deuteros harness pattern to run the *whole* boot chain as real executed instructions) — confirmed via 3+ billion real emulated instructions that the candidate is never executed and never written to, and found + fully reconstructed a second, previously-undocumented self-decrypting-code region in the mini-loader (same "DISC COMPANY" trace-vector technique as Deuteros, see `m68k-trace-vector-decrypt-needs-emulate-trace-on.md`) that likewise contains no reference to it. Residual uncertainty (a caller past the mini-loader's still-unresolved CIA-timing retry gate, or in the still-missing truncated tail) is out of reach without a faithful CIA/disk-timing model or a fresh dump. `Disk.2`'s only non-zero content (a 4-byte magic `0x16C65710`) was matched byte-exact against a `cmp.l` immediate in `Disk.1`'s own code, alongside `"FORMAT M2.2"`/`"NOT AN M2.2 DISK"` UI strings — resolving it as a blank disk stamped by the game's own in-universe disk-formatter feature, not a bad dump. Truncation status open (not resolvable by further static analysis, needs a fresh image): the file ends on a clean track boundary but with dense non-zero data and high entropy right to the last byte (no blank-tail taper), and the game is confirmed to issue large runtime reads deep into the disk as routine behaviour — both weigh against "benign truncation." First confirmed content asset: two real 16-colour `amiga12` palette tables, each fed to a disassembly-verified `LoadRGB4()` call with A6 provenance traced to a real `OpenLibrary("graphics.library")` call (not just an opcode-pattern match — see `lvo-byte-pattern-false-positive.md`); shipped via the viewer's Data tab. A real `exportGameData`/`buildAssets` pipeline is now registered, `supported: true`. A later session found Millennium 2.2 hides a compressed pixel-art bank byte-identical in codec to Deuteros' own (same RLE-over-16-bit-words token grammar, found by a register-linked opcode-word scan for Deuteros' exact decoder-prologue shape rather than re-deriving from scratch, not a literal byte-pattern match) — 135/136 real images confirmed via a real space-station UI screen, a probe schematic, and other unmistakable art; the shared codec now lives in `tools/shared/amiga-rle-gfx.ts` (see `game-re-corpora/methanoid.md` for the full derivation). A later asset-sweep session found the game's first audio content (a real 4-channel Paula driver + two confirmed PCM sample blobs), and a follow-up fully decoded that driver's whole command-byte-stream opcode grammar and its envelope-table byte format (16 real ADSR-style curves, resolved via an otherwise-untraceable base register solved from a single known-content anchor — see `unrecoverable-base-register-solved-from-single-content-anchor.md`) — shipped as `note_pitch_table.json`/`envelope_curves.json` Data-tab tables; the instrument table's record format is confirmed but its content is confirmed runtime-populated, not static (byte-identical across two differently-loaded driver copies that would need different absolute pointers if it were real — see `relocation-invariant-content-across-copies-proves-placeholder.md`), so exact per-instrument sample segmentation stays open. **Deuteros (Novagen)**: boot-block loader chain traced end to end (`BB_ENTRY` re-confirmed at `0xC`, correcting a prior pass's wrong offset-4 claim — a second worked instance of `amiga-bb-entry-offset-is-12-not-4.md`), through a mini-loader using standard AmigaOS trackdisk.device extended commands (`ETD_READ`/`ETD_WRITE`/`ETD_CLEAR`, overturning an earlier "private io_Command scheme" misread), into confirmed real game-engine code (direct `$DFF096`/`$DFF09A` hardware writes). No real HUNK executable exists on either disk (verified: false-positive magic only); the whole game is raw flat-binary-loaded. The mini-loader's illegal-instruction-vector-hijack anti-debug technique (same "Disc Company" scheme as Millennium 2.2, still undocumented externally — a `WebSearch` found nothing) is now **fully solved, not just structurally confirmed**: a `re-codebreaker` escalation built a real Musashi 68000 emulation harness (`tools/deuteros/emu/`) that ran the actual copy-protection routine (`Disk.1+0x131AE`) instead of hand-disassembling it, decoding a 3-layer CPU-probe → self-decrypting trace-vector loop → CIA hardware-timing check against magic constant `$DA8DBFDB` — independently spot-verified this session (magic constant byte-exact on Disk.1, absent from Disk.2; 4 claimed `$12FFC` writer sites confirmed byte-exact; harness/vendored-Musashi/decrypted-output all confirmed to exist as claimed). Getting the harness to actually decrypt the loop needed a non-obvious Musashi config fix, see `m68k-trace-vector-decrypt-needs-emulate-trace-on.md`. The repeating-record region (Disk.1 boot-track table + tracks 138-142, Disk.2 tracks 0/6/10) was refuted as protection-tool padding (autocorrelation + a byte-identical 780-byte match to the real track-80 payload) — it's real, stale-duplicated game data, confirmed this session to be **loaded into live game memory** (not stale residue, since it sits on the confirmed-reachable index-5 load path) but still of unknown content class after an image/graphics hypothesis was tried and set aside. A later session SOLVED the 320x200x4bpp title/credits picture's palette statically (no emulator — a `LoadRGB4(vp,colors,count)` disassembly trace, LVO `-0xC0`, cross-checked against the RKM and a published LVO table), rendering a fully legible real title/credits screen and shipping Deuteros' first confirmed asset (`public/assets/deuteros/amiga/screens/title.png`); registered a real `exportGameData`/`buildAssets` pipeline (`supported: true`), which surfaced and fixed a `cli-script-main-fires-on-import.md` suffix-guard bug latent in Reunion's own scripts too; and SETTLED (not just advanced) two more open items via static disassembly: the Disk.2 swap-back reload (traced end-to-end + a whole-disk literal-address census proving the mini-loader/track-1 I/O library are never reloaded, only mode-index re-entry) and the `Disk.1+0x8A64E` dynamic track-number reader (a structural proof its offset is always `>= $29400`, excluding track 0/1 regardless of runtime data). A follow-up session traced the track-80 payload's own real engine entry (same SuperState/UserState + DMACON/INTENA bring-up idiom as the track-4 blob) and found a SECOND, previously-undocumented `$13006->$66000` commit routine (gated on the already-confirmed low-Chip-RAM sentinel) running the opposite direction from the already-known `$66000->$13006` restore stub — the two form a genuine bidirectional save/restore mirror pair, corrected via two independently-cross-checked disassemblers (see `naive-byte-window-address-scan-crosses-instruction-boundary.md` and `single-disassembler-src-dst-order-trusted-unverified.md`, both surfaced this session) — direct evidence the record data is live/mutable engine state, not a static table, though its specific field semantics remain open. Also found (not yet linked) a separate 24-byte-stride per-object task/timer dispatch table resident in the track-4 blob. Open: the CIA hardware-measured value itself (deferred to `re-codebreaker`) and the repeating-record data's specific semantic class. **Reunion (Amnesty Design, Amiga AGA, 1994)**: container fully solved — RNC1-wrapped Hunk executables plus 509 IMP!-wrapped (or, for 2 files, genuinely raw) data files, `ancient decompress` auto-detecting both from magic with zero extension-based branching; asset formats fully solved and shipped (IFF `ILBM`/`PBM ` -> 277 PNGs, IFF `8SVX` -> 80 WAVs, confirmed-byte-exact ProTracker `MOD` x9 shipped raw for live in-browser synthesis) via a new generic `decodeByteRun1()` added to `@seer-project/iff` (the EA IFF-85 RLE codec, verified on every ILBM/PBM compression/masking combination present). File extensions in this corpus are actively unreliable in both directions — a `.BAT` is really an `8SVX` sample, `.RDA` files are chunky `PBM ` not planar `ILBM`, numeric "extensions" (`.001`-`.079`) are animation-frame sequence numbers — so the whole pipeline dispatches on decompressed magic bytes only. Disassembly confirmed the entry point/startup.o chain, the asset-filename table (`game.exe` file offset `0x4DAEE`) **with its consumer chain now fully traced**, and full credits/error strings. The `"EFT!ANIM"` custom key-frame+delta animation container is solved end-to-end and shipped (28 files) — **and now also independently confirmed inside `intro.exe`'s own player**, whose previously-under-explored DATA-typed hunk was unblocked this session via a hand-edited IRA `.cnf`. Also newly solved this session: the `"AMN0"` 3D wireframe vector-model format (35/37 files, verts+edges+render-verified), `pmain/*.DAT` planet-terrain grids (47/47 byte-exact), and `stmap/STMAPn00.CHR`'s raw 1bpp raster (refuting an earlier wrong "colour word" hypothesis). This session also found and fixed a generalizable IRA disassembler gotcha — its printed address column is a synthetic per-hunk-concatenated address, not the real file offset, once a `.cnf` spans more than one hunk (see `file-offsets-vs-segment-relative.md`'s 4th manifestation). A later session resolved most remaining open items: `grwar/GRKIEG00.CHR` turned out to be a second instance of the already-solved STMAP dither-atlas format; `spwar/SPANIM22.ANM`'s "leftover" trailing bytes are a real, live, deliberately-executed native code overlay reached via a direct JSR into the loaded asset buffer (not authoring residue — see `duplicate-asset-trailing-bytes-may-be-executed-code-overlay.md`); the standalone `.PAL` palette family got real traced consumers plus a render match against `local/ALIEN001.CHR`'s greyscale portrait; SAS/C small-data (`A4`) addressing was conclusively confirmed NOT the primary model via a full reload/auto-increment census; and `SECSTRT_1`'s boot sequence (graphics buffer init, interrupt-server install, display takeover, first-screen load) is now traced past the entry point. Still open (AGA): the exact `ALIEN001`+`FAJ` pairing call site and most deeper game-logic tracing. **Reunion OCS/ECS floppy release (`data/reunion/amiga`, 6 raw 880K ADFs)**: a from-scratch investigation (no `HUNK_SYMBOL` block) fully solved `Install`'s 390-entry asset catalog (three parallel fixed-stride tables giving each file's name/exact decompressed length/disk+block location — packed as `(diskNum<<12)|blockIndex` with `0→disk 1`), the manual-code copy-protection prompt (a rolling checksum of the typed answer against a 20-entry table, verified byte-exact against the real scanned manual's OCR'd page footers), and — via a `re-codebreaker` escalation, independently re-verified — both in-house LZ77 codecs (`1AM` backward/`2AM` forward, decompressors live in `Main.exe`'s own CODE hunk, found via a carry-chain opcode census after a general read-through stalled; 48/49 byte-identical against same-named AGA files, 297/297 whole-corpus decodes match declared length exactly). A real `exportGameData`/`buildAssets` pipeline ships 96 assets (35 `AMN0` wireframe models, 21 `EFT!ANIM` animations, 32 chunky icons, 8 decoded IFF `8SVX` audio samples via a new multi-FORM-per-file walker, a pattern not seen in AGA's one-sample-per-file convention). A later pass fully solved every item once flagged still-open here: all 242/242 `.CHR` raw planar screens now have confirmed/render-verified geometry (a Blitter `BLTSIZE` register-write census plus an AGA-cross-reference-`BMHD` oracle for the last 42), the `EFT!ANIM` palette for OCS/ECS spwar animations (a `re-codebreaker` escalation — a generic 32-colour installer invisible to earlier copy-loop censuses because the shell arrives in a data register with a 10-byte, not 4-byte, descriptor stride; 22/22 colours byte-exact against AGA's own `CMAP`), and `MUSIC/*.pin`/`.tbl`/`.hin`'s whole note/effect/instrument grammar (a near-complete ProTracker-family command set traced from the CIA-timer row dispatcher — including, in a later follow-up, a SECOND row/channel-trigger-time dispatch table resolving Position-Jump/Set-Volume/Pattern-Break/Set-Speed, and the real per-sample Paula playback rate via a byte-exact standard ProTracker 16x36 finetune-period master table feeding `hz = 3,546,895/period` with no software scaling). The manual-code check's own gating question is SOLVED too, via a `re-codebreaker` escalation that is this project's clearest worked example yet of `relocated-base-plus-displacement-hides-call-target.md`: the re-armer routine's only caller used a relocated base pointer deliberately pointing into adjacent filler bytes plus a small `jsr (d16,An)` displacement, so its real address never appeared anywhere in the file under any literal or jump-table search — found instead by parsing the `HUNK_RELOC32` table as a completeness proof and pairing every indirect-displacement call site against every reloc-validated absolute `LEA` base in the same hunk. Still open: a small 7-11 byte unexplained non-zero residual inside `.tbl` between two otherwise-fully-decoded regions. See `docs/reunion/TODO.md` and `docs/reunion/amiga/data-structure.md`. | `game-re-corpora/methanoid.md` |

## Lessons sourced from this corpus (full list)
`amiga-bb-entry-offset-is-12-not-4.md`, `self-relocating-boot-stub-invalid-past-jmp.md`, `illegal-vector-hijack-anti-debug-desyncs-disasm.md`, `m68k-trace-vector-decrypt-needs-emulate-trace-on.md`, `mistyped-base-constant-underflows-capture-buffer-bounds-check.md`, `lvo-byte-pattern-false-positive.md`, `unrecoverable-base-register-solved-from-single-content-anchor.md`, `relocation-invariant-content-across-copies-proves-placeholder.md`, `engine-family-shared-decoder-not-shared-container.md`, `disc-io-census-blind-to-already-loaded-data-consumer.md`, `cli-script-main-fires-on-import.md`, `no-traced-reader-region-is-not-proof-of-filler.md`, `naive-byte-window-address-scan-crosses-instruction-boundary.md`, `single-disassembler-src-dst-order-trusted-unverified.md`, `file-offsets-vs-segment-relative.md`, `duplicate-asset-trailing-bytes-may-be-executed-code-overlay.md`, `block-chain-walk-stops-at-unknown-sibling-block-magic.md`, `magic-search-must-not-be-wider-than-codes-real-comparison-width.md`, `carry-chain-opcode-census-locates-hand-written-bit-readers.md`, `relocated-base-plus-displacement-hides-call-target.md`
