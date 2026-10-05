# kolbold — Capcom CPS1/CPS2 + Sega System 16 arcade brawlers

Repo: `~/Development/kolbold`. First MAME/arcade-ROM-set corpus project in
this account (every sibling project is an Amiga/DOS home-computer title).
Original data ships as MAME-format ROM-set ZIPs
(`data/<game>/<platform>/<name>.zip`), not a single executable — see
`game-re-tooling/mame-arcade.md` for the general container-identification
workflow this project's work established.

## Games

| Game id | Platform id | Title | Status |
|---|---|---|---|
| `ddsom` | `cps2` | D&D: Shadows over Mystara | Container fully identified; 68000 encryption solved + verified; tile graphics solved + verified. **Tile-code categorization solved (coarse)**: fetching MAME's real `cps1_v.cpp`/`cps2.cpp` source directly (rather than trusting the earlier "flat unbanked, `gfxrom_bank_mapper()` irrelevant" note, which was only true for sprites) found CPS2 defines its own `cps2_render_sprites()` with an undocumented Y-bit tile-code extension (`code = word2 + ((word1&0x6000)<<3)`), while the three tilemap layers still use the shared, unmodified `gfxrom_bank_mapper()` — deriving its exact per-game formula gives a real, zero-guesswork 3-way split of the already-shipped 196,608-tile atlas (sprites-only / shared background-UI-font / sprites-only), visually confirmed by a byte-exact-aligned legible ASCII font rendering exactly at the derived offset (now shipped as its own atlas); see `per-layer-hardware-override-not-whole-region-dismissal.md`. **Per-boss sprite identity SOLVED**: large-pool types 14 ("Green Dragon")/19 ("Black Dragon") each own a type-exclusive 20-animation bank, reached by unconditional fall-through from their own state-0 body into a `cmpi.b #$13,$2(a0)`-gated table selector whose every call site lies inside the dragons' own dispatch-table-derived routine window (0 external callers) — renders as an unmistakable winged dragon (wings/body/tail/claws across 5 frames, shipped `sprites/dragon-green.png`/`dragon-black.png`). Two full prior passes (a "`$7e`/`$80` drive sprite selection" claim, then a corrected-raster-order-plus-real-palette render) both failed on the same undecoded byte: the sprite-definition blob's `flag` field (previously "priority/z, not decoded further") is actually a **tile-code BANK extension** — `realCode = blobCode + (flag&3)*0x10000`, the software-blob equivalent of this same game's already-solved hardware OBJ_BASE Y-bit extension above — so both renders decoded real, plausible, non-degenerate content from the WRONG one of the atlas's 3 code-banks (an unrelated humanoid sheet) instead of erroring; see `undecoded-metadata-byte-is-tile-code-bank-extension.md`. The escalation that solved it also caught its own predecessor's caller-census overreach (a "15+ callers, engine-wide shared mechanism" conclusion that was actually 20/20 callers still inside the dragons' own ~0xA4C-byte routine — the census was never bounded against the dispatch table's own next-entry address); see `unbounded-caller-census-crosses-sibling-routine-boundary.md`. A real, engine-wide sprite-animation VM (start-animation/advance-tick/build-OBJ_BASE-record primitives, `opcodes+0x1a32`/`+0x1a56`/`+0x1e062`) and the real CPS2 multi-tile block-sprite raster-order formula (ported from `cps2_render_sprites()`'s own source, including its "pgear fix" per-row nibble-wrap quirk) are both confirmed and shipped along the way. 8 real 16-color palette banks confirmed (which bank is active on-screen still open — the dragons' own live in-game colour is the one open sub-question left here); Z80 sound driver mailbox protocol + register map + QSound PCM sample format (signed 8-bit, x256) all confirmed (note/event grammar still open); **real D&D game-content data confirmed** — 6-class playable-character stat blocks (LEVEL/AGE/HP/6 ability scores) + a 39-entry monster/bestiary name roster, found as plain ASCII text. **Monster/enemy numeric stats solved** (a `re-codebreaker` escalation found a real flat 51-row starting-HP table indexed by object type id, plus the ten per-pool behaviour-dispatch tables sharing that index). **Type-id → monster-NAME bridge solved for the large/boss pool** (21/23 types; a previously-missed boss health-bar-and-name UI object's own type-id-indexed name-pointer table — found by widening an earlier PC-relative-only xref scan to also cover absolute-long constants, see `narrow-opcode-form-census-false-negative.md`). The regular/22-slot pool's names remain open — a 3rd session confirmed **no on-screen name display exists for it at all** (exhaustive all-register census + a traced factory debug menu, both negative) and traced a real but non-name `$2e(a0)` "creature id" mechanism (reach-point tables, not sprites/names) yielding 2 hint-tier matches to already-named bosses. **All 10 object pools named for real** via a factory debug-menu label table (zero-deviation address match, including a confirmed dedicated `ITEM WORK` pool) and **real per-stage-node level data found** (a second table paired with the difficulty-rank table, feeding a class-gated `BOX WORK` treasure/encounter generator, not a monster-type table). **A genuine monster-spawn mechanism is now found separately**: 131 real, scripted "spawn into pool P with literal type T" call sites across 3 object pools (not a lookup table — each placement's monster type is a literal operand baked into its own trigger code), 22/22 cross-named for the large/boss pool against the type-id→name bridge above (notably, "Green Dragon" has zero placements here — it spawns some other, unlocated way). Item/weapon *names* and room/dungeon layout proper are still open. See below. |
| `ddtod` | `cps2` | D&D: Tower of Doom (ddsom's prequel) | Container fully identified; 68000 encryption solved + verified; tile graphics solved + verified; real 512-color palette page 1 confirmed (pages 0/2/3 runtime-indexed, still open); Z80 sound driver + QSound PCM format confirmed independently against ddtod's own bytes (different, older driver revision, same protocol) — confirmed by reusing `tools/shared/cps2/*` and `src/assets/formats/qsound.ts` completely unchanged, exactly as predicted. **Monster/player combat-stat tables solved** (`re-codebreaker` escalation: two monster HP-init entries — active-player-count-scaled large/boss types, difficulty-rank+PRNG-scaled regular types — plus 4 per-class player HP-by-level tables; needed a corrected, chain-validated 9-pool inventory since ddsom's stricter pool signature silently drops 4 of ddtod's pools). See below. |
| `knights` | `cps1` | Knights of the Round | Container fully identified; 68000 program confirmed unencrypted; tile graphics solved + verified; boot-time palette confirmed by traced code path (real 512-color/32-bank table, real hardware register/mechanism — a genuine advance over ddsom/ddtod/goldenaxe's still-open or unconfirmed palettes), per-tile bank assignment + runtime palette updates still open (a candidate palette-selector mechanism was found and downgraded, see below). Z80 sound driver disassembled + 68000→Z80 command latch confirmed (both directions now: Z80-side intake AND 68000-side enqueue, ~125 distinct command IDs); OKI MSM6295 ADPCM codec + 78-phrase sample directory solved + verified (real decoded audio, plausibility-checked) — a genuine advance over ddsom/ddtod's still-open QSound equivalent. Confirms the CPS1/CPS2 split predicted from the ddsom/ddtod work — same planar `cps1_layout16x16` decode, `ROM_LOAD64_WORD` interleave, no CPS2 unshuffle pass. **A real 16-slot cooperative-multitasking kernel (TCB array, `TRAP#0` "register task" syscall, round-robin dispatcher, register-indirect `jmp (a1)` task invocation) confirmed and fully traced** — this is what a fully-traced boot/(re)init routine with zero direct ROM callers turned out to be reached through; 77 real task-registration sites enumerated as the concrete path to per-stage logic. A 25-entry enemy/object name table (maincpu `0x5562`) confirmed as real game content (roster matches published boss/enemy lists); one of its two 25-entry index arrays now has a fully-traced consumer too — a per-object handler (maincpu `0x52aa`) that draws a 4x3-tile enemy portrait + name into scroll1 RAM, found only after widening a reference scan past the array's own documented address to a small fixed-byte alias exploiting the record format's zero sub-field (see `table-reference-address-is-a-small-fixed-offset-alias.md`) — resolves the name table's previously-unexplained `wordA`/`wordB` fields as portrait tile-code bases, with a clean cross-check against the boss roster (all 8 bosses, and only those 8, have a 2nd animation frame). The sibling index array and the handler's own caller remain open. A later session RENDERED the portraits for real (corrected the tile size from an assumed 16x16 to the real 8x8, 33 frames shipped) and then CONFIRMED their temporal play order (traced the object's own init routine's initial-vs-steady-state hold-timer values, see `game-re-method/verification-techniques.md`'s new FSM-init-decides-frame-order technique) — first frame `wordB`, alternates to `wordA` every 3 frames, settles permanently on `wordA`. The same session decoded (not just structurally confirmed) a previously-mischaracterized string-table consumer's actual text and found it's a multiplayer character-select tie-break message, not intro/ending narrative as previously assumed (see `render-mechanism-confirmed-content-category-guessed.md`), and found the first content-confirmed point of any kind in the still-otherwise-unexplored 32,768-tile 16x16 sprite atlas (a literal HUD-gauge-shaped OBJ-RAM sprite write, rendered but not semantically proven). See below. |
| `goldenaxe` | `sys16` | Golden Axe | Sega System 16, unrelated engine family to Capcom CPS. Romset/board confirmed; tile + sprite graphics solved + verified; 68000 boot code disassembled and traced. **Memory map fully solved**: a `re-codebreaker` escalation found the 315-5195 mapper's own register file (`$FE0000`) and a literal 16-byte configuration table in ROM (`maincpu.bin+0x564A6`) that gives all 8 mapper regions' physical bases directly from data, not instruction-operand census — this overturned two earlier "confirmed" claims (paletteram and spriteram had been swapped: **paletteram = `$140000`**, **spriteram = `$200000`**, not the reverse; the two hardware records are coincidentally the same 16-byte size, which is what let the swap go undetected until the field *values* were checked). Text/tile RAM (`$100000`/`$110000`), work RAM (`$FFC000`), and I/O (`$C40000`) were separately confirmed via a system-wide LEA/PEA absolute-address census (see `game-re-tooling/mame-arcade.md`). **Real palette data confirmed and shipped**: the same escalation traced the boot-time palette upload (`maincpu.bin+0x3C64`) to its ROM source (`maincpu.bin+0x66E90`, 4 variants x 512 colors, selected by `$ec95.w & 3`) — a follow-up session wired this into the pipeline (`tools/goldenaxe/palette.ts`), replacing the tile atlas's placeholder greyscale ramp with real ROM colour, and replaced the palette word decoder's linear RGB approximation with a direct port of MAME's real resistor-ladder DAC formula (`compute_resistor_weights`/`combine_weights`, `src/assets/formats/segas16-gfx.ts`) — verified by a full-atlas re-render reproducing a legible real arcade PSA ("WINNERS DON'T USE DRUGS") in correct black/white/blue. Sprite palette remains genuinely open (the confirmed boot upload only covers palette entries 0-511, the tile-layer range, not the sprite palette area at 1024-2047). Intro narration + level build-log + UI text confirmed real via plain `strings` (no character/monster names found, likely tile-graphic-only); credits/stage-select UI-text boundaries fully traced and confirmed (no data-driven index table exists — boundaries are literal per-call-site LEA+MOVEQ operand pairs in the draw code, and the stage-select labels turned out to be a fixed-8-byte-stride array, not an undelimited pool); a co-located "font remap table" hypothesis was traced and refuted (real consumer is an unrelated boot-time RAM-clear parameter pair) and the `0x7d`/`0x7e`="apostrophe" readability hypothesis was refuted via a direct tile-ROM render (real apostrophe tile is 0x27). See below. |
| `blktiger` | `arcade` | Black Tiger | A materially OLDER, unrelated hardware generation for this project (1987, pre-dates CPS1) — dual Z80 (unencrypted main CPU + sound CPU driving 2x YM2203, no sample chip) + a real Intel 8751 (MCS-51) protection MCU (internal program now fully disassembled and its algorithm confirmed, see below), no CPS-ASIC/68000 at all. Romset confirmed byte-exact (20/20 CRC32 to `ROM_START(blktiger)`, the parent "Black Tiger (US)"/`mcu` set); main-CPU non-encryption confirmed both from source (`empty_init`) and empirically (clean radare2 z80 disassembly from address 0). All 3 `gfx_layout` tile formats (8x8 2bpp text, 16x16 4bpp background/sprite, both regions sharing one layout) solved + verified by render (legible font+katakana, dungeon scenery, recognizable skeleton/knight/dragon sprites) — reusing `tools/shared/cps2/gfx.ts`'s `decodeTile()`/`GfxLayout` **completely unmodified**, confirming that decoder is genuinely engine-agnostic (a verbatim port of MAME's own `gfx_element::decode()`, not a CPS-specific abstraction). Palette hardware FORMAT confirmed from `palette_device::xBRG_444` source (a new, non-CPS-B palette family: 1024 colors/2 bytes-per-entry, no brightness nibble); a 1st-pass byte-scan for a boot COPY LOOP found only a false-positive data table (incoherent garbage, not code), but a later session found real color VALUES anyway via a different Z80 idiom — see below. **Real game-content data confirmed**: a 27-line NPC "sage" dialogue-text corpus originally documented as a simple +1-letter-shift substitution cipher (confirmed via 3 independent full-sentence decodes plus a domain-archetype match — the decoded text names "zenny", Black Tiger's real currency, and "Spinning Scull", a real weapon, both independently confirmed via an adjacent plain-ASCII string pool) plus 168 plain-ASCII UI strings (31 hand-curated as real, see below). A later session disassembled the real drawing routine and found this is NOT a runtime cipher — a raw unmodified tile-code byte copy into a font ROM holding a 2nd dedicated dialogue alphabet at a different page (page selected by 3 bits of a per-line attribute byte, the same "steal bits from an attribute/position word" idea as CPS2's Y-bit sprite-code extension, confirmed from source for all 3 gfx layers here) — this correction fixed 2 wrong punctuation-byte mappings the original symmetry-guess had gotten wrong and fully traced the block's 4-byte record header to real dispatch code. Also: `audiocpu`'s Z80 sound driver (command-latch protocol + 68-entry dispatch table, AND — a later session — the full note/instrument event grammar for its "BGM" 6-channel mechanism, reverse-engineered from scratch with no reference implementation and verified via a whole-corpus 0-unrecognized-byte closure check plus a real decoded track; a structurally distinct "unconditional-play"/single-voice mechanism was found but not traced) fully disassembled and confirmed. Surfaced four generalizable pitfalls (plus, for the sound-driver work: two new verification techniques in `verification-techniques.md`, a chromatic-ratio pitch-table self-check and cross-stream loop-target convergence): `rgn-frac-total-field-fraction-scales-tile-count.md` (a `gfx_layout`'s `total` field can itself carry a non-(1,1) `RGN_FRAC`, silently doubling a naively-computed tile count), `printable-terminator-byte-defeats-delimiter-pair-scan.md` (a `'@'`-terminated string scan must find maximal printable runs, not "everything between two `'@'` bytes", since `'@'` is itself valid printable content), `apparent-cipher-is-duplicate-alphabet-at-different-tile-page.md` (a confirmed byte-substitution "cipher" for tilemap text may really be a raw tile-code copy into a ROM page holding a shifted alphabet, not a runtime transform — trace the drawing code before calling it a cipher), and `shared-tile-bank-page-selector-is-per-record-not-uniform.md` (a shared tile bank's per-record page-selector attribute byte must be read per record, not reused from a similar sibling record). **A 7th session, prompted by direct user visual feedback ("black and white", "partial sprites in noise"), CONFIRMED real palette color VALUES for 3 ranges** (SPRITES group0 pens0-9 x5 variants, TILES groups6-11 x6 "scene" variants, TILES group1 x12 fade-animation frames — 122/1024 total entries) via a DIFFERENT Z80 idiom than the earlier boot-loop search: `ld de,<paletteAddr>` immediates paired with a following `ldir` block copy, found by grepping a per-region LINEAR disassembly (fixed ROM + each of 16 banked pages independently, each from its own verified-good start). Re-rendering the sprite/tile atlases with the recovered colors was a decisive, non-marginal visual confirmation (flat grey geometry became an immediately recognizable colored cast). The same session also CONFIRMED a real composite (multi-tile) hardware-sprite mechanism exists — despite the confirmed hardware OBJ record having no group/link/size field at all (a genuine, source-confirmed hardware difference from CPS2) — by grepping for `ld ix/iy,<absolute-spriteram-address>` and finding 2 hardcoded 2x2 player-icon composites (rendered, recognizable) plus a separate generic animation-table-driven composite builder (found but not fully traced to a specific object). Surfaced 2 more generalizable pitfalls: `register-immediate-plus-block-copy-finds-non-loop-palette-writes.md` and `absolute-hw-register-load-signals-software-composite-sprite.md`. **An 8th session extended palette VALUES from 122/1024 to 896/1024** by generalizing the `ldir` search past literal-immediate destinations to also trace `pop de` and ROM-data-table (`ld e,[hl]`) header-read destinations — found a shared bank-6 "palette script" state machine (7 confirmed-reachable call sites) covering ALL of TILES, ALL of SPRITES, and ALL of CHARS (the UI/dialogue-text layer, previously 0% covered — now real red/white/blue text, not greyscale), plus a TILES-group9 fire-flicker animation; only an unused 128-entry index gap remains open. See `copy-destination-may-be-data-not-operand.md` for the generalizable technique and below. |

## blktiger (Black Tiger, arcade) — solved formats

Full byte-level spec: `docs/blktiger/arcade/data-structure.md`. Open items:
`docs/blktiger/TODO.md`. No escalation used across any session.

- **Container.** `data/blktiger/arcade/blktiger.zip` is the MAME parent
  "Black Tiger (US)" `blktiger` romset (20 files, `mcu` machine config),
  CRC32-matched against `ROM_START(blktiger)` in
  `src/mame/capcom/blktiger.cpp` — **confirmed**, 20/20. Distinct from
  `blktigera` (older US revision, different maincpu files), the bootleg
  `blktigerb1`/`blktigerb2` sets (no MCU region — protection removed), and
  the Japan "Black Dragon" release `blkdrgon`/`blkdrgonb` (different
  `chars`/`tiles` gfx content, same everything else).
- **CPU architecture + encryption — confirmed.** Z80 main CPU (24MHz/4 =
  6MHz), confirmed unencrypted both from source (`GAME(blktiger, ...)`
  uses `empty_init`, no decrypt handler) and empirically (a clean,
  zero-decode-error radare2 `-a z80` disassembly from address 0: `di`/
  `im 1`/`jp`, a standard `rst 0x38`-filled IM1 vector table, real code
  resuming at the vector target). Z80 sound CPU (3.579545MHz) drives 2x
  YM2203 with **no separate sample chip at all** — unlike every other
  title in this project (QSound/OKI/uPD7759), Black Tiger's audio is
  entirely live FM/PSG synthesis, so there is no sample directory to find.
  A real Intel 8751 (MCS-51) protection MCU (4096-byte internal ROM,
  `bd.6k`) is present, gated on `MCS51_INT1_LINE` at Z80 I/O port 0x07.
  **A 4th session fully disassembled the MCU's own MCS-51 program**
  (radare2's native `8051` arch plugin — a 3rd distinct ISA from either
  Z80 in this game, first use in this project) and CONFIRMED its
  protection algorithm byte-exact, not a hypothesis: a whole-ROM scan
  found only 83 of 4096 bytes are not `0xFF` (the rest unprogrammed),
  accounting for a reset vector, the external-interrupt-1 (IE1) vector —
  the only MCS-51 interrupt slot populated, matching
  `MCS51_INT1_LINE` — a 30-byte boot/init routine, a 32-byte interrupt
  handler, and a 16-byte data table with zero residue. The algorithm: on
  each interrupt, mask the received byte to its low nibble (`ANL
  A,#0x0F`), index a fixed 16-byte table, write the result back as the
  reply — no checksum, no per-session state. Decisively confirmed by
  finding the Z80 side independently builds its OWN copy of the same
  table by reading the literal bytes of its own following instruction
  stream (a self-referential code-as-data trick — see
  `protection-check-table-hidden-as-following-instruction-bytes.md`) at
  two separate call sites, both byte-identical to the MCU's table (3
  independent locations, zero deviation) — the Z80 hangs forever on any
  mismatch, consistent with the bootleg sets shipping no MCU region at
  all. Also surfaced `r2-arch-flag-before-dashdash-file-separator.md` (a
  CLI arg-order bug that initially made the real, valid, mostly-erased
  MCU ROM read back as falsely all-`0xFF`/blank). Shipped:
  `tools/blktiger/mcu.ts` (+8 tests against real ROM-byte fixtures),
  `mcu-protection.json` in both pipeline stages.
- **Tile/sprite graphics — confirmed (decode).** Two `gfx_layout` tables
  ported field-for-field from `blktiger.cpp` (`charlayout`: 8x8, 2bpp;
  `spritelayout`: 16x16, 4bpp, shared by both the "tiles"/background and
  "sprites"/object GFXDECODE regions). Verified by render: chars ->
  legible ASCII font + katakana; tiles -> dungeon/cave scenery + "EXIT"
  UI tiles; sprites -> clearly recognizable skeleton-warrior/knight/
  dragon/chest art. Notably, `spritelayout`'s `total` field is
  `RGN_FRAC(1,2)` (not the `(1,1)` every prior CPS1/CPS2 game in this
  project used) — see `rgn-frac-total-field-fraction-scales-tile-count.md`
  for the generalizable gotcha this surfaced (2048 real tiles per region,
  not the naive 4096 `region_bits/charIncrement` alone would give).
- **Palette — format confirmed, VALUES confirmed for 896/1024 entries.**
  `palette_device::xBRG_444` (`src/emu/emupal.h`/`.cpp`, ported directly,
  not guessed): 1024 colors, 2 bytes/entry, R from the low byte's high
  nibble, G from the low byte's low nibble, B from the high byte's low
  nibble, no brightness nibble (unlike CPS1/CPS2's `cps1_build_palette()`
  12-bit-RGB+4-bit-brightness format — a genuinely different palette
  family, first seen in this project). Palette RAM has **no** static
  ROM-backed initial content in the confirmed memory map (plain `.ram()`,
  so no boot-time copy LOOP exists to find), but real color values ARE
  recoverable via LDIR block copies: a 7th session found 3 sites (122
  entries) via a literal `ld de,<addr>`+`ldir` grep; an 8th session
  generalized this to trace EVERY `ldir` in the corpus back to its real
  destination — including cases where the address is stored as DATA and
  loaded via `ld e,[hl]`/`ld d,[hl]`, invisible to a literal-operand text
  search (see `copy-destination-may-be-data-not-operand.md`) — and found
  a shared bank-6 "palette script" state machine (5 entry stubs, 7
  confirmed-reachable fixed-ROM call sites, 12 record lists) covering
  ALL of TILES, ALL of SPRITES, ALL of CHARS (the UI/dialogue-text layer
  — the flagship result, `chars.png` went from greyscale to real
  red/white/blue text), plus a TILES-group9 fire-flicker animation. Only
  idx 640-767 (an unused index gap) remains without a confirmed source.
  See `docs/blktiger/arcade/data-structure.md` §4 for the full trail.
- **Real game-content data — confirmed, mechanism corrected by a later
  session.** Same "run `strings` on the confirmed-unencrypted program
  ROM" technique that cracked ddsom/knights/goldenaxe's game content,
  transferred cleanly to a 4th, materially older hardware generation.
  Found a 27-line NPC "sage" dialogue-text corpus (dungeon advice/shop
  screens) — first documented as a "+1 letter-shift substitution cipher"
  (letter mapping confirmed via 3 independent full-sentence decodes,
  cross-checked against real Black Tiger content: "zenny", the real
  in-game currency, and "Spinning Scull", a real collectible weapon, both
  independently confirmed via an adjacent plain-ASCII string pool). A
  later session disassembled the actual Z80 drawing routine and found
  it's **not a cipher at all** — a raw, unmodified `LD (HL),A` byte copy;
  the "+1" is a font-ROM authoring choice (a 2nd, dedicated dialogue
  alphabet at a different tile-code page than the plain-ASCII page HUD
  text uses, page selected by 3 bits of a per-line attribute byte — see
  `apparent-cipher-is-duplicate-alphabet-at-different-tile-page.md`).
  Re-deriving the punctuation cluster from the font ROM's own pixels
  (rather than the original session's arithmetic-symmetry guesses)
  corrected 2 byte mappings (`0x5a`: period, not space — confirmed
  across 10 real occurrences with zero exceptions, including a real
  3-byte ellipsis; `0x7d`: dash, not period) and added one new one
  (`0x5c`: forward slash). The block's 4-byte record header (`0xFF` +
  destAddr + attribute) is now fully traced to real dispatch code (every
  one of 17 real headers has its own confirmed `CALL` site), and the
  short "icon" segments between some headers are confirmed as real
  small icon/kanji graphics on a different tile-code page (not a
  portrait-ID lookup) — see
  `shared-tile-bank-page-selector-is-per-record-not-uniform.md` for the
  render-mistake this surfaced along the way. Plus 168 plain-ASCII UI
  strings (HUD labels, warning screen, bonus-stage text) — found via a
  maximal-printable-run scan, not a naive delimiter-pair scan; see
  `printable-terminator-byte-defeats-delimiter-pair-scan.md` for why the
  naive approach silently drops real strings on this ROM specifically —
  hand-curated down to 31 real strings via a vowel/code-smell-character
  heuristic (168 raw runs are mostly Z80 opcode bytes that scan as
  printable). Also: a 2nd session fully disassembled the `audiocpu`
  sound driver (command-latch protocol, 68-entry command-dispatch table,
  YM2203 Timer A/B IRQ structure byte-exact cross-checked against
  `ymfm_opn.h`) — see `docs/blktiger/arcade/data-structure.md` sec 2.1.
  **A 6th session then solved the note/instrument EVENT GRAMMAR itself**
  for the `bit7=0` ("BGM", 6-channel) mechanism — reverse-engineered from
  scratch with no reference implementation (vgmtrans has zero coverage of
  this game or engine family): control commands (tempo/transpose/mute/
  instrument-select/3 independent nested-loop slots/end-of-track),
  tie-legato and sustain modifiers, and the note/rest byte format (3-bit
  duration code x 5-bit pitch index). The real YM2203 F-number/block pitch
  table was confirmed purely from its own numeric structure — consecutive
  entries' ratio clusters at 2^(1/12) (the real chromatic semitone ratio)
  and the octave field increments by exactly 1 every 12 entries, no
  emulator or external oracle needed (see
  `game-re-method/verification-techniques.md`'s new "synthesizer pitch
  table confirms itself" section) — and a 41-byte instrument table was
  confirmed via an exact register-field-width match (a 6-bit mask landing
  on YM2203's real 6-bit algorithm+feedback register). Verified with a
  whole-corpus closure check (148 real channel streams across the entire
  ROM, ~173,800 decoded events, zero unrecognized bytes) and one fully
  decoded real track with a strong cross-channel corroboration — two
  independently-decoded channels' own loop targets converge on the exact
  same byte address, both remaining grammatically valid past that shared
  point (see verification-techniques.md's new "two independently-decoded
  streams converging" section). Also found, but not traced: a
  STRUCTURALLY DISTINCT single-voice "unconditional-play" mechanism
  (`bit7=1` headers, 40/65 track commands, its own priority-state pair and
  a different per-voice struct layout) — open. Implementation:
  `tools/blktiger/sound-driver.ts`. **Per-layer tile-code
  composition confirmed from source** for all 3 gfx layers (chars/tiles/
  sprites each combine an 8-bit byte with 3 extra bits from a sibling
  attribute byte — the same idea as CPS2's Y-bit sprite-code extension,
  first confirmed on this older, unrelated hardware generation); which
  sprite-code ranges are which enemy and which bg-tile-code ranges are
  which dungeon area remain uncatalogued.
- **PROMs — `bd02.9j` CONFIRMED (structural), `bd03.11k`/`bd04.11l`
  confirmed (structural), `bd01.8j` open.** A 5th session read all 4
  Signetics 82S129 (256×4-bit) PROMs' raw bytes directly. `bd02.9j`'s
  content is a strict 32-byte-quantized step function using the exact
  4-value set `{0,1,2,3}` — collapsing both it and `blktiger.cpp`'s own
  hand-guessed bg-tile priority `split_table` (source-flagged as *"a
  guess... not derived from a PROM"*) to matching 8-bin granularity gives
  an EXACT structural match (same 3 non-zero bins, same 5 all-zero bins,
  identical 0.125/0.125/0.125/0.625 byte-count fractions) — confirming
  the real hardware source behind MAME's own admitted guess, one step
  further than the driver itself. `bd03.11k`/`bd04.11l` independently
  structurally confirm the driver's "pure video timing" hardware notes (a
  classic sync/blanking-PROM shape: one long constant run + a few short
  localized pulse/transition regions, including a real-looking composite-
  sync equalizing-pulse glitch on `bd04.11l`). `bd01.8j` remains
  genuinely unexplained (different value set/shape from both). See
  `game-re-tooling/mame-arcade.md`'s "driver's own source-commented
  'unverified guess' table" technique — third instance in this project
  after Golden Axe's real DAC and Knights' real palette.
- **NPC shop price/item gate — CONFIRMED (disassembly).** The same
  session found a prior pass's "2 unparsed ASCII digit runs, looks like a
  bonus/extra-life score table" lead was a misidentification: full
  disassembly of `maincpu 0x6670-0x67ea` found a real shop-purchase gate,
  not a score system. A hardware DIP switch (`mem[0xe022]`, confirmed
  byte-exact as `blktiger.cpp`'s own `PORT_DIPNAME(0x1c,...,Difficulty)`
  mask — see `game-re-tooling/mame-arcade.md`'s new DIP-switch-as-value-
  oracle technique) selects one of 8 difficulty-scaled tiers from a
  16-record price table and a companion 16-record item-id table, tested
  against the player's zenny (currency) stat and wired to two of the
  ALREADY-decoded dialogue lines ("Sorry, you don't have enough / zenny
  for that item." / "You can't carry it any more.") — closing the loop
  between two previously-separate findings. The original 2 ASCII digit
  strings turned out to be an inert, never-code-referenced programmer
  documentation comment that independently restates the real binary
  table's 4 price columns with ZERO deviations across all 16 records —
  see `unreferenced-doc-string-numeric-match-wrong-role.md` for the
  generalizable misidentification pitfall this surfaced (a numeric
  string's shape/position is not evidence of a live table's semantic
  role; the string's own address having zero code references is itself
  a strong signal it's inert).

## ddsom (D&D: Shadows over Mystara, CPS2) — solved formats

Full byte-level spec: `docs/ddsom/cps2/data-structure.md`. Open items:
`docs/ddsom/TODO.md`.

- **Container.** `data/ddsom/cps2/ddsom.zip` is the MAME parent/World
  `ddsom` romset (21 files), identified by CRC32-matching every file
  against mamedev/mame's own `ROM_START(ddsom)` in
  `src/mame/capcom/cps2.cpp` — **confirmed**, zero guessing needed. See
  `game-re-tooling/mame-arcade.md` for the general technique.
- **68000 program encryption — confirmed, solved generically.** CPS2's
  two-Feistel-network opcode cipher, ported from radare2's own
  `libr/muta/p/muta_cps2.c` (mechanically extracted via brace-balanced
  regex parsing of ~1500 constants, not hand-transcribed — see
  `tools/shared/cps2/decrypt-tables.ts`'s header comment for the
  provenance note). The 20-byte battery-backed key format (`bit = (317 -
  b) % 160` bit-descramble, also yielding the encrypted address range and
  a documentary watchdog-instruction cross-check) is decoded in
  `tools/shared/cps2/decrypt.ts`'s `decodeCps2Key20()`, cross-verified
  against `historic-mame`'s independent hardcoded per-game key table.
  **Two non-obvious pitfalls hit and now documented**: the cipher needs
  the *raw, un-byteswapped* ROM dump (see
  `game-re-lessons/cps2-decrypt-input-must-be-raw-rom-bytes.md`), and the
  68000 RESET vector (SP/PC) is opcode-space while every other exception
  vector is data-space (see
  `game-re-lessons/m68k-reset-vector-is-opcode-space-other-vectors-are-data-space.md`).
  Verified via a plausible reset vector, 60+ consecutive valid/coherent
  disassembled instructions at the entry point (including the exact
  independently-decoded watchdog opcode), and byte-identical agreement
  with radare2's own `cps2` muta plugin.
- **Tile/sprite graphics — confirmed (decode); palette — confirmed (8 real
  16-color banks, fixed-address ROM copy sites).** CPS1's
  `cps1_layout16x16` 4bpp planar `gfx_layout` (ported from MAME's
  `gfx_element::decode()` in `src/emu/drawgfx.cpp`) plus the
  `ROM_LOAD64_WORD` 4-way mask-ROM interleave — but CPS2 needs one more
  step CPS1 doesn't: a per-2MB-bank recursive "unshuffle" pass
  (`cps2_state::unshuffle()`/`cps2_gfx_decode()` in
  `src/mame/capcom/cps2.cpp`) applied to the assembled region before the
  shared planar decode runs. Without it: uniform, tile-grid-aligned noise.
  With it: all 196,608 tiles render as clearly recognizable sprite/
  creature/character art. See
  `game-re-lessons/cps2-gfx-needs-extra-unshuffle-pass.md`. Palette: a
  targeted byte-exact scan for `knights`' confirmed `ori.l
  #$f000f000,Dn`/`adda.l #$f000f000,An` brightness-forcing idiom found 9
  real matches in ddsom's decrypted opcode stream, 8 with fixed-literal
  ROM sources (the 9th is real but runtime-indexed by a per-monster/
  character attribute byte) — decoded via a new
  `decodeCps1PaletteWordsForced()` helper, all 8 banks coherent/varied,
  non-monotonic color data. Shipped (`tools/ddsom/build-assets.ts`,
  bank 0 as an arbitrary-but-real atlas default; all 8 in
  `palettes/confirmed-banks.json`), replacing the old placeholder
  greyscale ramp. Which bank/site is active on any given real screen
  remains open (`docs/ddsom/TODO.md`'s `ddsom-palette-values`).
- **Tile-code range categorization — confirmed (coarse, code-derived);
  per-boss sprite identity — still open.** A follow-up session fetched
  MAME's real `cps1_v.cpp`/`cps2.cpp` source directly (rather than
  trusting an earlier doc's "flat unbanked, `gfxrom_bank_mapper()`
  irrelevant" dismissal, which was only ever true for *sprites*) and found
  two things: CPS2 defines its own `cps2_state::cps2_render_sprites()`
  that bypasses `gfxrom_bank_mapper()` and instead extends the 16-bit tile
  code with 2 bits stolen from the sprite's own Y-position word (`code =
  word2 + ((word1 & 0x6000) << 3)`); the three tilemap layers
  (scroll1/2/3), by contrast, still call the shared, unmodified
  `gfxrom_bank_mapper()`. Deriving that function's exact per-game formula
  (ddsom/ddtod fall back to the generic `"cps2"` config row) gives a real,
  zero-guesswork 3-way split of the already-shipped 196,608-tile atlas —
  codes 0-65535 and 131072-196607 are sprite-only (structurally
  unreachable by any tilemap layer), codes 65536-131071 are the only range
  scroll1 (8x8 font/UI)/scroll2 (16x16)/scroll3 (32x32) can ever address —
  visually confirmed by a fully legible ASCII+kana font rendering exactly
  at the derived offset, byte-exact aligned with real ASCII at codes
  0x40-0x7f. See
  `game-re-lessons/per-layer-hardware-override-not-whole-region-dismissal.md`.
  Shipped: `tools/shared/cps2/gfx.ts`'s `cps2ScrollBankMap()`/
  `cps2SpriteCode()`/`CPS1_LAYOUT_32X32`, `tools/ddsom/tile-categories.ts`,
  a new `sprites/font.png` atlas (256 glyphs) and `data/tile-categories.json`.
  **Per-boss sprite identity remains open**: a prior session's claim that
  `$7e(a0)`/`$80(a0)` "drive per-type sprite selection" was traced to its
  one real consumer (a small ring-buffer shaped like an SFX/animation-
  event queue, not a tile-code path) and directly refuted by rendering the
  tile-code range its own observed values imply (renders as the
  player-character's sprite, not any boss).
- **Z80 sound driver (mailbox protocol + register map) — confirmed;
  QSound PCM sample format — confirmed; note/event grammar — open.**
  Ground truth: MAME's `qsound_device` (`src/devices/sound/qsound.cpp`),
  a modern low-level emulation that runs the DL-1425's real DSP16A
  microcode, so its `dsp_sample_r()`/`qsound_w`/`qsound_r` necessarily
  match the real chip's external-ROM read path and command mailbox
  exactly. PCM format: the `qsound` ROM stores plain **signed 8-bit
  linear PCM**, scaled x256 (`<<8`) to a 16-bit sample — no ADPCM, no
  compression (`dsp_sample_r()`'s `u16(byte)<<8`, read back as signed
  downstream, is arithmetically identical to a signed-8-bit
  reinterpretation) — confirmed both from the C++ semantics and
  empirically (sample-to-sample delta 4-9x smaller under the signed
  reading than an unsigned-with-128-bias reading, across 6 sampled
  regions of real ROM data). Mailbox protocol (Z80 `qsound_sub_map`,
  `src/mame/capcom/cps1.cpp`, shared verbatim by cps2.cpp): writes to
  `0xd000/0xd001/0xd002` (data-high/data-low/address), ready-poll at
  `0xd007` — confirmed via Z80 disassembly (radare2 `-a z80`; **note:**
  its z80 plugin prints a `jr`/`djnz`'s raw displacement byte as the
  operand text, not the resolved target — always recompute branch
  targets independently) of a boot-time "silence all 16 channels"
  routine whose real disassembled address arithmetic (`RLC`x3 = `<<3`,
  `+0xba`/`+0x06`/`+0x02`) lands exactly on qsound.cpp's documented
  per-channel register formula — an independent structural match, not
  just reading the comment. Decoder + register-map constants:
  `src/assets/formats/qsound.ts` (browser+Node safe, tested); raw
  `qsound` ROM region shipped as `public/assets/ddsom/cps2/audio/
  qsound.bin` (`tools/ddsom/build-assets.ts`), per this project's "raw
  bytes ship as-is, decode client-side" audio convention (same as
  `oki-adpcm.ts`'s established pattern for knights' OKI chip). Envelope
  dispatch register-write targets (`QSOUND_REG.volume`/`playbackRate`)
  also confirmed via direct disassembly. **Music-sequence format
  (song table + track event grammar) — confirmed.** `~/Development/
  vgmtrans`'s `CPS2Seq.cpp`/`CPS2TrackV1.cpp`/`CPS2Instr.cpp` ship a
  complete reference decoder with a ddsom-specific `mame_roms.json` entry
  (`fmt_version: "CPS2_V1.15"`, byte-exact match to this driver's own
  disassembled boot string) and two ddsom-specific bug comments — used as
  the starting hypothesis, then every constant/shape independently
  re-derived against real ddsom bytes (not trusted blind). vgmtrans's own
  `seq_table`/`instr_table`/`samp_table` literal values matched real ROM
  bytes exactly once the addressing-space mismatch between vgmtrans's own
  naive-file-concat ROM loader and this project's MAME-gap-preserving
  `buildAudioCpuRegion()` was reconciled — see
  `game-re-lessons/reference-tool-own-loader-address-space-differs-from-yours.md`.
  Result: 923 real songs found (921 valid), **100% (1846/1846) of tracks
  decode to a clean terminator** with zero out-of-bounds reads/loop
  desyncs; the sample-info table (the SAME table already shipped at a
  conservative 256-record cutoff) extends to a real **344 records**,
  independently reproducing vgmtrans's own "sample with end_addr <
  start_addr at index 290" bug comment byte-for-byte; the table's
  previously-open byte-7 field is now identified as a MIDI unity
  (reference) playback key; and 5 decoded program-change events resolve
  end-to-end through the instrument table to real, non-degenerate PCM
  audio. A real promotion-time bug (an opcode consolidation silently
  dropping a `noteState` mutation, invisible to structural/termination
  checks — caught only by checking actual decoded note-key values) is
  documented in `game-re-lessons/opcode-case-consolidation-drops-hidden-state-mutation.md`.
  Shipped: `src/assets/formats/qsound.ts`'s CPS2 sequence-format section
  + `tools/ddsom/sequence.ts` (all unit-tested against synthetic
  fixtures) into `public/assets/ddsom/cps2/audio/sequences.json`. See
  `docs/ddsom/cps2/data-structure.md` §4.2.6. **A same-day follow-up
  session then fully resolved the note record's remaining open `flags`
  clamp**: simulating real Z80 flag semantics for the `cp 0x6c`/`jr c`/
  `jp m` idiom across all 256 input bytes found a real, asymmetric
  boundary (`[0x6c,0xeb]->0`, `[0xec,0xff]->0x6b`, not a plain two-sided
  clamp — see `game-re-lessons/two-branch-clamp-idiom-tests-sign-not-range.md`),
  cross-checked exactly against an independently-found `0x6bff`
  note-trigger clamp constant from an earlier session. Traced the full
  downstream vibrato/pitch-bend delta formula and its 4 embedded ROM
  tables, one of which is a real 12-tone-equal-temperament curve matching
  `128*2^(idx/12)` to within 0.5%. Separately confirmed a real ADSR
  envelope-timing mechanism (3 ROM rate tables) **byte-exact (256/256)**
  against vgmtrans's own hardcoded CPS-family constants
  (`attack_rate_table`/`decay_rate_table`/`sustain_level_table`,
  `CPS2Instr.h`) — a strong two-source cross-check (this session's own
  disassembly-derived addresses vs. vgmtrans's hardcoded values) that
  both are correct for ddsom specifically. As a capstone, rendered one
  full real song (index 59, 104 notes) end-to-end to a WAV using the
  confirmed timing/sample-selection/ADSR-timing chain (pitch mapping and
  envelope curve shape explicitly labeled approximations, not confirmed)
  — quantitative plausibility checks (RMS, peak, distinct-value count,
  zero-crossing rate, lag-1 autocorrelation, smooth per-segment RMS
  envelope) all pass. **Still open**: ddsom's primary per-note pitch-
  SELECT mechanism (the newly-confirmed vibrato table is a modulation-
  depth layer on a base pitch, not the base-pitch selector itself), and
  the ~0x900-byte volume-scaling chain's RAM-flag semantics (structure
  now characterized as 3 gated multiplies + a final counter-scaled
  multiply). See `docs/ddsom/cps2/data-structure.md` §§4.2.7-4.2.8.
- **Real D&D game-content data — confirmed.** All the above is engine
  plumbing (container/decryption/pixel formats/hardware registers); a
  follow-up session specifically hunted actual game *content* and found it
  via the cheapest possible technique — plain `strings` on the assembled,
  undecrypted maincpu **data**-space region (CPS2 only encrypts opcode
  fetches, never data reads) — no disassembly needed to locate the tables.
  Found: 6 playable-character D&D ability-score stat blocks (LEVEL/AGE/HIT
  POINTS/STRENGTH/DEXTERITY/INTELLIGENCE/CONSTITUTION/WISDOM/CHARISMA, one
  per class: fighter/cleric/elf/dwarf/magic user/thief), verified via (1)
  proximity to their own column-label string, (2) record order/count
  agreeing with an independently-read class-name table, and (3) every
  single class matching its real D&D archetype (fighter=highest HP/STR,
  magic user=lowest HP/STR+highest INT, thief=highest DEX, dwarf=highest
  CON, elf=highest AGE at 101) — see
  `game-re-lessons/domain-archetype-plausibility-oracle.md`. Also found: a
  39-name monster/bestiary roster plus a 21-name secondary/alternate
  boss-name list (likely an ending-credits variant). Shipped via
  `tools/ddsom/game-data.ts` (unit-tested), wired into both pipeline
  stages. Full write-up: `docs/ddsom/cps2/data-structure.md` § 6.
- **Monster numeric stats + type-id→name bridge — confirmed** (two
  follow-up sessions). A `re-codebreaker` escalation found the per-type
  starting-HP table (`data+0x458c`, 51 rows × 0x100 bytes, indexed by the
  object record's type byte) and the ten per-pool behaviour-dispatch
  tables sharing that same index — the type/HP side was solved, but no
  alignment from numeric type id to the 39-name text roster survived
  (the escalation's own suggested next step, sprite rendering, was never
  needed). A later session found the real bridge for the **large/boss
  pool** instead: every boss type's spawn code (`jsr $d5f30.l`) installs a
  pointer to itself into a small "boss health-bar-and-name" UI object,
  whose own draw routine reads that pointer's type-id field back and
  indexes a genuine 21-entry name-pointer table (`data+0xd6232`,
  immediately adjacent to — and ending with zero slack at — the
  already-confirmed alternate boss-name string data). This consumer was
  invisible to a whole-image xref scan that only checked PC-relative
  references (it's reached via a plain absolute-long `movea.l #imm,aN`);
  a short literal byte-pattern census for the confirmed `'@'`
  string-terminator compare instruction found it directly instead — see
  `game-re-lessons/narrow-opcode-form-census-false-negative.md`'s 4th
  worked example. 21/23 large-pool types now have a confirmed name,
  cross-checked with zero contradictions against the HP-magnitude and
  shared-behaviour-routine facts the escalation had already established
  (e.g. the two dragon pairs sharing one routine turned out to be
  disambiguated by an internal type check inside that shared code, not a
  simple recolour). Shipped via `tools/ddsom/combat-stats.ts` (unit-
  tested). A third session then exhausted the regular/22-slot pool's own
  name search: an all-8-data-register generalisation of the terminator
  census (see `game-re-lessons/narrow-opcode-form-census-false-negative.md`'s
  reinforcement note) and a traced factory "OBJECT TEST" debug menu both
  came back negative (the debug menu is a raw hardware sprite/color/flip
  browser with no names, unlike `knights`' own object-test screen) —
  **confirmed: the regular pool has no on-screen name display at all.**
  That session did trace a previously-flagged, never-explained per-object
  field (`$2e(a0)`, 33 distinct values) to a real consumer: three parallel
  creature-id-indexed pointer tables (`data+0x11bffa`/`+0x11c11a`/
  `+0x11c23a`) holding per-move reach/anchor-point data for a two-
  character grab/combo-attack calculation — not names or sprite codes,
  but real, and it yields 2 moderate-confidence "shares this id with an
  already-named boss" hints (regular type 18 ~ large-pool "Manticore",
  type 27 ~ large-pool "Ogre"; both are independently already-flagged HP
  outliers/probable mid-bosses). Tracing it also surfaced a genuine
  pitfall — see `game-re-lessons/per-object-field-dual-role-identity-vs-transient-scratch.md`
  (the same field offset is reused elsewhere as an unrelated countdown
  timer). **Not yet decoded:** the regular pool's own monster identity
  (only the 2 hints above); the Z80 note/event-stream grammar; item/
  weapon/spell *names* and room/dungeon layout data proper (not found as
  text at all — likely drawn as sprite/tile graphics rather than stored as
  strings, matching this era's beat-em-up convention). Full write-up:
  `docs/ddsom/cps2/data-structure.md` §§ 6.8-6.9 (6.9.6 for the 3rd
  session).
- **All 10 object pools named for real, and real per-stage-node level
  data found** (a follow-up session, `docs/ddsom/cps2/data-structure.md`
  § 6.10). A factory "GAME WORK" debug-menu memory-viewer label table
  (found via the same plain-`strings` technique as the rest of § 6) gives
  every one of the 10 structurally-derived object pools (§6.8.2) a real
  name, cross-checked byte-exact against `0xFF8000 + pool.a5Offset`
  (`0xFF8000` independently confirmed from a real boot-time `lea.l
  $ff8000.l,a5`) with **zero deviation across all 10 pools** — a strong
  two-independent-methods oracle (68000 instruction-signature scan vs.
  plain text scan). Directly confirms a real, dedicated `ITEM  WORK` pool
  exists (38 slots, `a5+0x549e`, 92 dispatch entries — one entry traced
  and shows genuine player-proximity pickup-trigger code), plus `BOX
  WORK`/`SET   WORK`/`EFFCT WORK`/`SOBJ  WORK`/`PEFF  WORK`/per-player
  `P1-4WEAPON F/B` regions. **Open, unresolved tension:** the debug
  menu's own labels for the two already-well-evidenced character pools
  (`BOSS  WORK` for the 22-slot "regular enemy" pool, `ESHL  WORK` for
  the 3-slot "large/boss" pool with the confirmed name-table consumer)
  appear to invert the doc's existing, consumer-traced role
  identification — reported side by side, not resolved either way, see
  `game-re-lessons/debug-menu-label-vs-traced-consumer-conflict.md`.
  Separately, tracing the already-confirmed stage-node index's (`$34(a5)`)
  code site further found a **second, previously-undocumented parallel
  per-stage-node table** (`data+0x21bb0`, exactly 120 bytes after the
  already-confirmed difficulty-rank table with zero slack — length
  derived from the two `lea` targets' own spacing, not hardcoded) whose
  own consumer (traced independently) selects which 64-entry block of a
  monster-spawn table applies per stage node — real, new level/stage
  design data. See `game-re-lessons/confirmed-index-shared-by-second-
  parallel-table.md`. Shipped via `tools/ddsom/game-data.ts`'s
  `extractWorkAreaLabels()` and `tools/ddsom/combat-stats.ts`'s
  `findStateBaseRegister()`/`namePoolsFromWorkAreaLabels()`/
  `extractStageNodeTables()` (all unit-tested) into
  `data/extracted/ddsom/pool-names.json`+`stage-nodes.json` and their
  `public/assets/ddsom/cps2/data/` equivalents.
- **Z80 QSound envelope-state register targets confirmed** (follow-up
  session): the per-voice 6-state ADSR-style dispatch (`ix+0x33`, jump
  table at `audiocpu+0x1925`) was traced past its counter/threshold
  comparisons into the two real mailbox writes it drives —
  `QSOUND_REG.volume` (a counter-driven fixed-point multiply,
  `audiocpu+0x1e47-0x1e5c`) and `QSOUND_REG.playbackRate` (the pitch
  accumulator ramped per-tick, `audiocpu+0x1faf-0x1fbe`, gated by
  per-voice flags). The note-select table's `flags` byte (previously
  "purpose open") is confirmed to feed the playbackRate path as
  `0x3c - flags`, clamped — a real pitch-bend/vibrato-depth mechanism,
  though the exact clamp bit semantics weren't fully pinned down.
  Shipped: `src/assets/formats/qsound.ts`'s
  `parseQsoundEnvelopeDispatch()` + `tools/ddsom/rom-map.ts`'s
  `extractQsoundEnvelopeDispatch()` into `audio/envelope-dispatch.json`.
  See `docs/ddsom/cps2/data-structure.md` sec 4.2.5.
- **Top-level game-mode dispatcher enumerated** (same session): the
  fire+skin-tone palette pair (§ palette above) was previously pinned to
  a single mode value; enumerating the dispatcher's full ~50-entry table
  found **6** different mode values all resolving to different entry
  points into **one shared, unbroken linear routine** (confirmed via a
  full linear disassembly showing zero branches out of that span before
  the shared tail) — a hub-screen shape, still not text-confirmed. See
  `game-re-lessons/jump-table-distinct-targets-may-be-shared-routine-
  entry-points.md` for the generalizable pattern this surfaced, and
  `docs/ddsom/cps2/data-structure.md` sec 3.5's "3rd follow-up session"
  block.
- **Real, engine-wide sprite-animation VM found and traced** (3rd
  follow-up session): resolving large-pool type 14/19's ("Green Dragon"/
  "Black Dragon") state-0 body one level past its already-documented
  shared prologue found a real, non-type-specific "start animation #N"
  (`opcodes+0x1a32`) / "advance one tick" (`+0x1a56`) / "build OBJ_BASE
  hardware sprite record(s) from the current sprite-definition blob"
  (`+0x1e062`) mechanism — confirmed engine-wide via a 524-site byte-
  pattern census (also used by the unrelated `BOX WORK` chest-reveal
  code). Applied to the dragon pair's own real animation data: a real
  20-tile composite decodes cleanly from real ROM bytes (tile codes
  `0x5210`-`0x53d4`), and the previously flagged-then-downgraded
  `$2a(a0)`/`$2b(a0)` fields are now explained as a genuine per-object
  palette-bank-override mechanism. **Rendered (greyscale) but
  inconclusive** as a visual dragon match — see
  `game-re-lessons/shared-subroutine-reached-from-inside-type-body-not-
  entry-stub.md` (the census-scope pitfall this surfaced) and
  `game-re-lessons/hold-cmd-means-permanent-not-invisible.md` (a decode
  pitfall hit mid-trace: the animation's "hold forever" sentinel frame is
  the real idle pose, not an invisible placeholder). Shipped:
  `tools/ddsom/sprite-render.ts` (unit-tested). See
  `docs/ddsom/cps2/data-structure.md` sec 3.8.
- **Correction: the per-stage-node "monster-spawn-block index" is a
  class-gated treasure/encounter-box selector** (same session): finishing
  an explicitly-flagged "not traced further this session" pointer
  (`opcodes+0xbb22`'s object-allocation call) found it always allocates
  into the confirmed `BOX  WORK` pool (10 types, `a5+0x62de` — a zero-
  deviation address match to the independently-derived object-pool
  table), gated mostly by which player classes are present, not a
  monster-type roster. Real, valuable level-design data either way. See
  `docs/ddsom/cps2/data-structure.md` sec 6.10.4's correction block.
- **Item icons SOLVED, room/dungeon background tilemap-fill mechanism
  SOLVED** (follow-up session, pushing on the 3-item task brief that also
  found §6.11's spawn triggers and the 5th-pass dragon confirmation
  above): (1) generalized the confirmed sprite-animation-VM technique
  (`movea.l/lea.l #TABLE,a4` + `jsr $1a32.l` inside a per-type dispatch
  routine's own window, previously confirmed only for large-pool boss
  types) to the `ITEM WORK` pool's 92-entry dispatch table — 55/92 types
  resolve to a real table, and rendering several produced unmistakable
  D&D item icons (a treasure chest, a ring, an ornate sword, a spiked
  mace, a food item), directly confirming the standing "items are
  sprite-drawn, not named as text" hypothesis. (2) Following the task
  brief's own hint ("does the confirmed stage-node index `$34(a5)` have
  other consumers?"), a plain absolute-address scan for the
  already-confirmed `SCROLL3_BASE` physical register (`0x918000`, from an
  earlier session's MAME-driver-sourced palette/video-register work)
  found a THIRD consumer gating real SCROLL3 background-fill code
  (`opcodes+0x32190`) — the first room/dungeon-layout content found for
  this game. Fully disassembled the fill routine (`opcodes+0x2766`): a
  24-entry per-stage block table → 32-byte "set records" (16 chunk
  indices) → 16-byte "chunk info" records (4 packed tile-pair longwords),
  and RENDERED a coherent, recognizable tiled background scene from real
  ROM data (stone/cloud texture + tree-canopy silhouettes) — end-to-end
  verified, not just structurally plausible. A structurally analogous but
  less-resolved SCROLL2 mechanism was also found (its own 4-way
  bank-select table, real addresses) but its data-cursor register's
  origin wasn't traced (the containing function has zero static callers
  found by either an absolute-address or `bsr` census — see
  `game-re-lessons/engine-implements-cooperative-task-kernel.md`).
  Shipped `tools/ddsom/item-icons.ts` + `tools/ddsom/room-layout.ts`
  (both unit-tested against synthetic fixtures AND real ROM data). See
  `docs/ddsom/cps2/data-structure.md` sec 6.12/6.13.
- **Green Dragon (large-pool type 14) spawn mechanism — escalated to
  `re-codebreaker`** (same session): 5 total independently-shaped static
  searches (the original §6.11 census plus 4 more — a whole-ROM
  literal-write scan, a `bsr`-call census, an all-register direct-pool-
  reference census, and a self-mutation/computed-write census) all found
  zero spawn sites for this type, despite it being a real, fully-
  implemented monster (own HP row, own dragon-art bank, named in the boss
  table) that external community material describes as a real, played
  boss encounter. One of the negative searches (the literal-write scan)
  is a clean real-world reconfirmation of
  `game-re-lessons/locally-indexed-substructures.md`'s exact failure mode
  — every raw byte-pattern hit for "type 14" belonged to a DIFFERENT,
  unrelated object pool's own local type-14, not this one. See
  `docs/ddsom/cps2/data-structure.md` sec 6.14 and `docs/ddsom/TODO.md`'s
  `ddsom-green-dragon-spawn` row for the outcome once the escalation
  returns.

## ddtod (D&D: Tower of Doom, CPS2) — solved formats

Full byte-level spec: `docs/ddtod/cps2/data-structure.md`. Open items:
`docs/ddtod/TODO.md`. Confirmed the ddsom entry's prediction exactly: same
container/encryption/gfx-format story, `tools/shared/cps2/*` reused
completely unchanged — only `tools/ddtod/rom-map.ts` +
`export-game-data.ts` + `build-assets.ts` (game-specific file lists/
offsets, mirroring `tools/ddsom/`'s shape) needed writing fresh.

- **Container.** `data/ddtod/cps2/ddtod.zip` is the MAME parent/World
  `ddtod` romset (17 files, smaller than ddsom's 21 — 5 maincpu ROMs not
  8, no second audiocpu file), CRC32-matched against `ROM_START(ddtod)`
  in `src/mame/capcom/cps2.cpp` — **confirmed**.
- **68000 program encryption — confirmed.** Same cipher/key-decode code
  as ddsom, zero changes. Master key and watchdog instruction both match
  `historic-mame`'s hardcoded `ddtod` row exactly (64-bit exact match).
  One field did **not** match: the key-derived encrypted-range `upper`
  computed `0x200000` vs. `historic-mame`'s hardcoded `0x180000` — the
  modern per-key-byte formula (a byte-exact port of current mamedev/
  mame's own `init_cps2crypt()`) is trusted over the older table, which
  predates the real bit-descramble discovery and was apparently
  hand-tuned for that one field. See
  `game-re-lessons/historic-oracle-table-fields-have-different-evidence-classes.md`
  for the generalized lesson. Verified via a plausible reset vector
  (`SP=0x00ff0e6a, PC=0x0000089a`) and 60+ coherent disassembled
  instructions including the exact watchdog opcode.
- **Tile/sprite graphics — confirmed (decode); palette — confirmed (one
  real 512-color page, table-indexed ROM copy, no brightness-forcing).**
  Identical gfx pipeline to ddsom (same fixed 0x200000-byte unshuffle bank
  size regardless of region size, confirmed directly from
  `cps2_state::cps2_gfx_decode()`'s source). 98,304 tiles decoded; sampled
  ranges across the tileset render clearly recognizable armored-knight/
  creature sprite art. Palette: ddtod does **not** use ddsom's `ori.l
  #$f000f000` idiom at all (0 hits, exhaustive scan) — a structurally
  different mechanism, found via r2 (`radare2`) `aaa` recursive-descent
  disassembly (linear capstone sweep desynced and found nothing; see
  `game-re-lessons/linear-disasm-desyncs-through-inline-data.md`'s
  "Alternative fix" note) + `axt` xref analysis: 4 sibling per-page loader
  functions, table-indexed, no brightness transform. The page-1 loader is
  unconditionally reachable (9 confirmed `bsr` call sites, source
  hardcoded independent of caller) — its 512-color (32-bank) table is
  fully decoded and shipped (`tools/ddtod/build-assets.ts`,
  `palettes/confirmed-palette-page1.json`); its source ROM address sits
  *inside* ddtod's encrypted opcode range, so it had to be read from the
  plain `data` image, not the decrypted `opcodes` image — a live example
  of `game-re-lessons/m68k-reset-vector-is-opcode-space-other-vectors-are-data-space.md`'s
  broadened lesson. Pages 0/2/3's sibling loaders are real but
  runtime-state-indexed (`(a5+0x56)` byte); a candidate fixed-index "load
  all 4 pages" boot call was found but has no confirmed caller. See
  `docs/ddtod/TODO.md`'s `ddtod-palette-values`.
- **Z80 sound driver + QSound PCM format — confirmed, independently
  verified against ddtod's own bytes** (same session as ddsom's
  equivalent finding above, not just assumed to transfer). ddtod's
  `audiocpu` is a genuinely different, older driver build (embedded
  version string `"version 1.04 /CPS2     1993 / NOVEMBER"` vs. ddsom's
  `"1.15  /CPS2       1996  /JANUARY"` — only 12.1% byte-identical in the
  first 0x8000 bytes) but the same protocol family: identical boot
  handshake (`0x77` written to shared-RAM offset `0xcfff`), the same
  `0xd000-0xd002`/`0xd007` mailbox helper (byte-exact shape), and
  **byte-identical default DSP register init values** to ddsom's
  (`0xde=0, 0xdf=0x2e, 0xe0=0, 0xe1=0x30, 0xe4-e7=0x3fff`). PCM format
  confirmed the same way as ddsom (signed 8-bit x256), independently on
  ddtod's own `dad.11m`+`dad.12m` bytes. Shipped:
  `public/assets/ddtod/cps2/audio/qsound.bin` via the same shared
  `src/assets/formats/qsound.ts` decoder, zero game-specific code needed.
  **Not yet decoded:** the note/event-stream grammar (same open item as
  ddsom), and runtime data tables (priority, per-level scripting) beyond
  what §3.5/§3.6 already confirm.
- **Monster/player combat-stat tables — confirmed** (`re-codebreaker`
  escalation, after this project's own search stalled on 4 independent
  paths). ddtod's HP-init does **not** share ddsom's exact byte shape —
  both entry routines write via `lea $60(a0),a4 / move.w dN,(a4)+ ×2 /
  move.w dN,(a4)` (a post-increment write through a scratch address
  register), which is why an otherwise-complete displacement-operand
  census (every `move.w X,$60(An)` in the whole 4MB image) found only 6
  irrelevant hits — see `narrow-opcode-form-census-false-negative.md`'s
  newest example. Two shared monster HP-init routines: **entry A**
  (`opcodes+0x457a2`, 13 large/boss types, scaled by active player count
  only) and **entry B** (`opcodes+0x45842`, 16 regular types, scaled by a
  dynamic difficulty rank `$7730(a5)` plus a 16-step PRNG draw through a
  two-level table) — plus a **player** max-HP setter (`opcodes+0x44176`)
  driven by 4 per-class HP-by-level tables and 4 per-class level-by-stage
  tables. A real, chain-validated **9-pool** object inventory (not 5 —
  ddsom's stricter `POOL_LOOP_SIG` silently rejects 4 of ddtod's pools,
  including the character pool the HP tables belong to) was needed before
  the correct pool could even be checked; a prior pass had dismissed the
  real entry-A call sites as "a different pool" on the strength of the
  *incomplete* 5-pool inventory — see
  `negative-from-addressing-root-not-shapes.md`'s newest example for the
  general "validate an inventory's completeness before using it as a
  negative filter" lesson. Every escalation claim was independently
  re-verified against real ROM bytes before shipping. Shipped via
  `tools/ddtod/combat-stats.ts` (its own pool finder, deliberately not a
  change to ddsom's `combat-stats.ts` — see `ddtod-shared-pool-finder` in
  `docs/ddtod/TODO.md`), unit-tested. **Not yet decoded:** 3 of 28
  character types' HP-init provenance (coherent HP rows, no traced call
  site — one demonstrably copies HP from a sibling object instead), the
  `$50` HUD/bestiary-name-id → glyph-draw path (the id field and its
  0..24 range are confirmed; the name text itself is a strong,
  zero-contradiction but untraced mapping), and what dispatches a
  near-duplicate second copy of the character behaviour bank at
  `opcodes+0x14c000`-`+0x15c000`. Full write-up:
  `docs/ddtod/cps2/data-structure.md` § 7.

## knights (Knights of the Round, CPS1) — solved formats

Full byte-level spec: `docs/knights/cps1/data-structure.md`. Open items:
`docs/knights/TODO.md`. The first CPS1 title in this project — confirms
(from real data, not by analogy alone) the CPS1/CPS2 split predicted in
the ddsom/ddtod entries above: no program-ROM encryption, no gfx
bank-unshuffle. `tools/shared/cps2/*` (misnamed but genuinely CPS1/CPS2-
shared) needed zero changes; only `tools/knights/rom-map.ts` +
`export-game-data.ts` + `build-assets.ts` were written fresh.

- **Container.** `data/knights/cps1/knights.zip` is the MAME parent/World
  ("911127") `knights` romset (23 files), CRC32-matched against
  `ROM_START(knights)` in `src/mame/capcom/cps1.cpp` — **confirmed**, all
  23/23. Notably smaller maincpu ROM count than ddsom/ddtod (2x 0x80000
  files via plain `ROM_LOAD16_WORD_SWAP`, not 5-8x) — bigger individual
  EPROMs, same byte-order transform.
- **68000 program — confirmed unencrypted.** Verified empirically rather
  than assumed from the task brief: the plain (word-swapped, no
  decryption) maincpu region disassembles at its reset vector
  (`SP=0x00ff81d6, PC=0x000005fe`) into 60+ consecutive valid, coherent
  68000 instructions with zero decode errors — watchdog-kick writes,
  hardware register init, RAM-clear loops targeting `$ff0000` work RAM and
  the `$900000-$92ffff` "gfxram" range (scroll1/2/3, palette shadow,
  object RAM — see the CPS-A/CPS-B register map below). No `"key"`-shaped
  ROM region exists in `ROM_START(knights)` at all, and the CPS1 driver's
  init is `empty_init` (not a decrypt-calling handler like CPS2's).
- **Tile/sprite graphics — confirmed (decode); palette — confirmed
  (boot-time table), open (per-tile bank assignment).** Same
  `cps1_layout16x16` 4bpp planar layout and `ROM_LOAD64_WORD` 4-way
  interleave as CPS2, reused verbatim from `tools/shared/cps2/gfx.ts` —
  but **no** `cps2UnshuffleGfx()` call. Verified by render: the plain
  planar decode with no unshuffle pass, sampled at tile range
  ~20000-22048, produces unambiguous, clearly recognizable castle/scenery
  art (turrets, stone walls, gates, mountains) with zero visible
  block-noise. 32,768 tiles total.

  A real, code-path-confirmed palette was recovered (a genuine advance
  over ddsom/ddtod's still-open equivalent, and over goldenaxe's
  unconfirmed gradient-only candidate — see
  `monotonic-integer-table-mimics-smooth-color-gradient.md`): MAME's own
  `cps_state::cps1_build_palette()` (`src/mame/capcom/cps1_v.cpp`) gives
  the palette-word format (12-bit RGB + 4-bit brightness,
  `tools/shared/cps2/palette.ts`'s `decodeCps1PaletteWord()`) and the
  exact CPS-A/CPS-B register names/offsets; byte-scanning the assembled
  ROM for those two registers' literal absolute addresses found exactly 2
  hits each, and disassembling around them showed **unconditional**
  writes (same hardcoded constants `palette_control=0x3f`,
  `CPS1_PALETTE_BASE=0x90c0` at both boot and every VBLANK interrupt, no
  runtime-state branch) — this is what elevates the finding from
  "plausible ROM data" to genuinely confirmed. Tracing the boot-time copy
  loop's source pointer located a 512-word/32-bank real color table at
  maincpu ROM offset `0x1554`; decoded, it's coherent hand-authored-looking
  data (grayscale/yellow/blue/fire/skin-tone ramps), not a monotonic
  counter. This is the **boot/attract-mode** palette specifically —
  whether gameplay overwrites the palette RAM shadow (`$90C000`) with
  per-level data, and which of the 32 banks each tile/sprite uses, remain
  open (`docs/knights/TODO.md`). Also corrected two mislabeled RAM
  addresses a prior session had guessed rather than traced: the real
  object/sprite RAM base is `$920000`, not `$900000`; the real palette
  shadow is `$90C000`, not `$904000` (those are actually scroll1/scroll2
  tilemap RAM). Full write-up: `docs/knights/cps1/data-structure.md` §§
  2.3, 3.3. See `game-re-tooling/mame-arcade.md` for the generalized
  technique (emulator-source register semantics + literal-address byte-scan
  + unconditional-write check).
- **Audio — Z80 sound driver + OKI MSM6295 ADPCM samples — confirmed** (a
  genuine advance over ddsom/ddtod's still-open equivalent items, which
  use CPS2's proprietary QSound instead of this chip). Z80 program
  (`audiocpu`, `kr_09.11a`) disassembled from the reset vector with
  radare2's native `z80` arch mode: boot sequence, the fixed IM1 interrupt
  vector at `$0038`, and the full 68000→Z80 sound-command latch mechanism
  (MAME's `cps1_soundlatch_w`/`cps1_soundlatch2_w` at `$800180`/`$800188`
  on the 68000 side; Z80-mapped read ports `$f008`/`$f00a`, serviced from
  the IM1 ISR with edge-detection + an 0xFF idle sentinel + a ring-buffer
  command queue) all traced and cross-checked byte-for-byte against
  mamedev/mame's own `cps1.cpp` memory-map declarations. The OKI MSM6295
  two-phase sample-trigger protocol (write phrase number, then write a
  channel-trigger byte with bit7 set, gated by a busy-status poll) is
  disassembled and confirmed at `audiocpu+0x6ca-0x6de`. The OKI 4-bit
  ADPCM codec itself (`src/assets/formats/oki-adpcm.ts`) is a direct port
  of MAME's own `oki_adpcm_state` (BSD-3-Clause) — sourced via a local
  vgmtrans checkout (`~/Development/vgmtrans`), whose CPS1 format module
  (`src/main/formats/CPS/`) also supplied the *starting* hypothesis for
  the sample directory (standard 128-entry MSM6295 phrase table at the
  start of the `oki` ROM) and a per-game MAME-romset database entry naming
  knights' exact sound-driver `tables_offset` (`0x1100`) — all independently
  re-verified against knights' own real ROM bytes rather than trusted
  blind: the `oki` region decodes to exactly 78 valid, tightly-packed,
  non-overlapping phrases, and the Z80 program's own sample-instrument
  table (parsed fresh from real bytes, not copied from vgmtrans) lists
  exactly 78 valid entries with matching phrase numbers 1..78 — two
  independently-located tables agreeing exactly. Decoded-audio plausibility
  verified quantitatively (RMS, peak, distinct-value count, lag-1
  sample autocorrelation — real audio is strongly self-correlated,
  uncorrelated noise is not), not just "decodes without error". Shipped as
  raw per-phrase ADPCM byte assets (no pipeline transcoding, per this
  project's audio convention — decode happens at runtime via the shared
  browser-safe module) plus machine-readable evidence
  (`data/extracted/knights/audio-info.json`). Full write-up:
  `docs/knights/cps1/data-structure.md` § 5. **Reusable lesson**: this
  project's earlier corpus-scan work
  (`~/.claude/agents/game-re-tooling/mame-arcade.md`) didn't know about
  vgmtrans's format-module corpus specifically — worth checking a local
  vgmtrans checkout for *any* future arcade/console sound-chip or
  music-sequence format in this family before hand-deriving from scratch;
  it ships real, cross-game-verified decoders and a per-game address
  database for dozens of chip families, not just OKI/CPS1.
- **Runtime data tables — a follow-up session traced all 4 of VBLANK's
  previously-untraced per-frame subroutines** (`$c68`/`$2364`/`$1b1e`/
  `$104c` — input-port polling, the 68000-side sound-command ring-buffer
  dequeue, a BCD digit-counter/carry routine, and DIP-switch decode; none
  is a level/entity data loader, all confirmed engine subsystems) and
  confirmed the 68000-side sound-command **enqueue** mechanism (~125
  distinct command-ID trampolines, complementing the already-confirmed
  Z80-side intake above) — a real advance on the dispatch-table open item,
  though which specific game event invokes which of the ~125 IDs is still
  untraced. That session also found and confirmed one genuine static ROM
  data table (50 records x 12 bytes at maincpu offset `0x113a`, copied to
  RAM via a fully-traced loop with a zero-slack boundary check; two fields
  are zero-deviation self-consistent — a smooth BCD arithmetic sequence and
  a BCD sequential 1-50 index — but its semantic role and true consumer
  remain open, complicated by the same destination RAM later being reused
  for an unrelated dynamic object-pointer list) and pinned down the state-
  RAM base register's literal value (`a5 = $FF8000`, via a 68000
  absolute-short-addressing sign-extension trap — see
  `game-re-lessons/m68k-absolute-short-sign-extends-base-register.md`).
  Also found and then downgraded a candidate "per-level palette selector"
  mechanism after decoding its actual target data (a screen-flash/
  transition-effect frame sequence, not per-stage palettes) — see
  `game-re-lessons/struct-analogy-needs-pointer-target-census.md`'s third
  variant. Full write-up: `docs/knights/cps1/data-structure.md` § 2.4.
  **Still open:** which Z80 command byte maps to which music
  sequence/phrase (only the intake/latch, the OKI trigger primitive, and
  now the 68000-side enqueue mechanism are traced, not the Z80-side
  dispatch table); the tilemap word format inside scroll1/2/3 RAM; whether/
  where gameplay overwrites the palette shadow per-level (a candidate
  mechanism was found and refuted, see above); and the 50-record boot
  table's semantic role. No live emulator/capture was available for either
  session (checked again, still absent) — every finding above comes from
  pure static disassembly (radare2 + Python capstone) plus programmatic
  self-consistency checks on decoded byte tables.
- **The `$f4a` "no direct caller anywhere in 1MB of ROM" mystery — solved.**
  A follow-up session found the actual mechanism: knights implements a real
  16-slot cooperative-multitasking kernel in its 68000 program — a runtime
  Task Control Block array (base `$FF804C`, 16 slots x 16 bytes), a
  `TRAP#0`-vectored "register task" syscall (`jsr $e72.w`, 77 real call
  sites found and enumerated), a round-robin dispatcher loop, and — the
  missing link — a **register-indirect `jmp (a1)`** (maincpu `0xe30`) that
  invokes each ready task's function pointer, loaded from that task's own
  TCB entry in RAM, never from a literal ROM operand. `$f4a` is simply
  "task slot 0", registered at exactly 2 real sites (boot, and a runtime
  re-init reached from inside an unidentified object's own per-object AI
  state machine — itself a THIRD independent instance of the same
  "PC-relative, state-byte-indexed local jump table" idiom used by the
  scheduler itself, confirming it's a pervasive toolchain code-generation
  pattern, not a one-off). The decisive technique, after the prior
  session's exhaustive direct-branch scan legitimately found nothing: a
  targeted `LEA $4c(a5),An` byte-pattern scan (guessing the task array's
  base-register displacement from the already-partly-understood TRAP#0
  handler) rather than more branch-target scanning — see
  `game-re-lessons/negative-from-addressing-root-not-shapes.md`'s Carrier
  Command `JSR (A2)` case for the same failure mode on a different
  platform, and the new
  `game-re-lessons/engine-implements-cooperative-task-kernel.md` for the
  full "how to recognize and crack an in-engine OS-like scheduler"
  technique this session established. Full write-up:
  `docs/knights/cps1/data-structure.md` § 2.5.
- **Also found and fixed while testing this game's pipeline (not
  knights-specific — a pre-existing bug affecting ddsom/ddtod/goldenaxe
  too):** every game's `export-game-data.ts`/`build-assets.ts` used a
  suffix-only `isStandalone` check that fired for *every sibling game's*
  script whenever any one game's script was run directly, since
  `tools/shared/game-config.ts` imports all of them into one module graph.
  Fixed across all 8 files (4 games x 2 stages) with a precise
  `import.meta.url`-based guard. See
  `game-re-lessons/cli-script-main-fires-on-import.md`.
- **Real game-content data — confirmed** (a further follow-up session,
  same "find content, not more plumbing" brief that cracked ddsom's D&D
  tables). Same technique, transferred cleanly to a second, unrelated
  engine generation: plain `strings` over the entire assembled `maincpu`
  region — here needing no data/opcode split at all, since knights (CPS1)
  has zero encryption of any kind (confirmed earlier). Found a 25-entry
  enemy/object name table at maincpu file offset `0x5562`, record grammar
  `[u16 wordA][u16 wordB][u16 flags][ASCII name]['/'][1 pad byte iff
  name.length is even]` — derived by strict forward parsing (not tuned to
  fit) and confirmed by landing exactly on a genuine end-of-table sentinel
  (an empty name) with zero parse errors across the whole table. Semantic
  confirmation: all 25 names cross-checked against two independent
  published Knights of the Round boss/enemy rosters (WebSearch) — all 8
  documented bosses (Scorn, Braford, Arlon, Phantom, Balbars, Muramasa,
  Iron Golem, Garibaldi) and all 12 documented common enemies (Soldier,
  Sword Man, Fat Man, Mask Man, Sky Walker, Bird Man, Tall Man, Buster,
  Magician, Barbarian, Mad Tiger, Bad Falcon) present, 3 extra real
  entries kept as unconfirmed-role rather than dropped (see
  `game-re-lessons/published-walkthrough-numeric-oracle.md`'s roster-
  matching variant, added this session). Also found (structure confirmed
  via zero out-of-table hits, consumer NOT traced): two adjacent 25-entry
  `[u16 pointer][u16 zero]` index arrays at maincpu `0x5110`/`0x5178`
  referencing that same table, preceded by a few code-address entries
  (a small dispatch header) — plausibly the factory "OBJECT TEST"
  self-test menu's cycling list(s) (that menu's own strings, `"OBJ MOVE
  TEST/"`/`"NUMBER="`/`"PATTERN="`, were found in the same scan), but
  untraced. Extensive narrative/UI text (full intro story, ending, dip-
  switch/self-test menu, region-warning legal text) was also located and
  documented in place but not extracted into JSON — no fixed per-entry
  shape to key an array on, unlike the name table. No separate ALL-CAPS
  player-character (Arthur/Lancelot/Parceval) name table exists — those 3
  names appear only inside prose. Shipped via `tools/knights/game-data.ts`
  (unit-tested) into both pipeline stages, `data/game-data.json`. Full
  write-up: `docs/knights/cps1/data-structure.md` § 6.

## goldenaxe (Golden Axe, Sega System 16) — solved formats

Full byte-level spec: `docs/goldenaxe/sys16/data-structure.md`. Open items:
`docs/goldenaxe/sys16/TODO.md`. Unrelated engine/hardware family to the
Capcom CPS games above — no shared code with `tools/shared/cps2/*`.

- **Container + board revision — confirmed.** `data/goldenaxe/sys16/
  goldnaxe.zip` is exactly MAME's `goldnaxe` set — "Golden Axe (set 6, US)
  (8751 317-123A)" — all 15 files CRC32-matched against `ROM_START(
  goldnaxe)` in `src/mame/sega/segas16b.cpp`. **Unencrypted 68000** (System
  16B, ROM board 171-5797), protected by a socketed **Intel 8751 MCU**
  (317-0123a.c2, 4096 bytes — its exact file size is itself the tell, see
  `game-re-tooling/mame-arcade.md`), **not** an FD1089/FD1094 encrypted CPU
  — that only applies to other Golden Axe sets in the same MAME driver
  (`goldnaxeu`/`goldnaxej`/`goldnaxe3`/`goldnaxe1`).
- **Tile graphics — confirmed.** MAME's `gfx_8x8x3_planar` GFXDECODE entry:
  8x8 tiles, 3 full non-interleaved bitplanes (one per ROM chip, 16,384
  tiles total). Implemented in `src/assets/formats/segas16-gfx.ts`'s
  `decodeSega16Tiles8x8()` (generic over plane count — reusable for other
  System 16-family games, not Golden Axe-specific). Verified by rendering
  all 16,384 tiles and finding perfectly legible English text, a full
  A-Z font strip, and Japanese katakana — see
  `game-re-method/verification-techniques.md`'s "Legible in-game text as a
  free geometry oracle" for why this is strong evidence despite no
  emulator/screenshot being available.
- **Palette word format — bit layout AND RGB scale both confirmed.**
  `sega_16bit_common_base::paletteram_w` (`src/mame/sega/segaic16.cpp`) —
  shared across the whole System 16-family generation, see
  `game-re-tooling/mame-arcade.md`. Independently cross-checked bit-for-bit
  against Charles MacDonald's community System 16B hardware notes
  (`https://jammarcade.net/images/2024/04/s16b.txt`) — two unrelated
  sources agree exactly. `decodeSega16PaletteWord()` in the same formats
  module now looks up MAME's real resistor-ladder DAC curve
  (`computeResistorWeights()`/`combineWeights()`, ported verbatim from
  `src/emu/video/resnet.cpp`/`.h`, driven by `segaic16.cpp`'s `{3900, 2000,
  1000, 500, 250, 0}` ohm "normal pen" resistor set) instead of an earlier
  linear approximation. The two curves turn out to agree almost everywhere
  and differ by at most 1 LSB elsewhere — a binary-weighted resistor ladder
  is inherently near-linear, unlike an R-2R ladder; see
  `binary-weighted-resistor-dac-near-linear.md`.
- **`maincpu` 68000 disassembly — confirmed clean, real code, ~55%
  auto-analyzed (930 functions).** Reset vector + boot sequence (hardware
  init, RAM clear, I/O setup) traced `0x408`-`~0x790`. **I/O region
  physical base = `$C40000` confirmed** by matching the boot code's
  hardware-register addresses byte-for-byte against MacDonald's hardware
  notes (same doc as the palette cross-check above) — a strong worked
  example of using a *second, independent* community hardware-notes
  document (not just MAME's own source) as a code-tracing oracle.
  **Text/tile RAM (315-5195 mapper region 4) physical base = `$100000`
  also confirmed**, this time via a different technique: a system-wide
  census of every `LEA`/`PEA` absolute-long-addressed instruction in
  `maincpu.bin`, bucketed by 64 KB bank — only 6 banks are ever referenced
  this way in the whole program, immediately surfacing `$100000` (tile
  RAM, 57 hits) and `$110000` (text RAM, 155 hits) exactly matching
  MacDonald's "text RAM is mapped 64K higher than tile RAM base"
  convention, corroborated independently by a disassembled boot-time RLE
  tile-RAM clear routine. See `game-re-tooling/mame-arcade.md`'s
  LEA/PEA-census addendum. **Memory map now fully solved (all 8 mapper
  regions), superseding the instruction-operand census approach for the
  remaining regions.** A `re-codebreaker` escalation found the 315-5195
  mapper's own register file (`$FE0000`, `regidx = (byteaddr>>1)&0x1f`)
  and a literal 16-byte configuration table in ROM
  (`maincpu.bin+0x564A6`) that gives every region's physical base directly
  — on this i8751-MCU board the **MCU**, not the 68000, programs the
  mapper, so the bases exist only as inert data as far as any 68000
  instruction-operand census can see (textbook
  `negative-from-addressing-root-not-shapes`). This **overturned** the
  session's own prior "confirmed" claim that `$140000` was spriteram: the
  16-byte sprite-attribute record and the 16-byte 8-colour palette bank
  are the same size, so the earlier "writes land at documented field
  offsets" evidence was equally consistent with either interpretation,
  and nobody had checked the field *values* (all well-formed colours, not
  scanline/X-position data) until this escalation did. Correct bases:
  **paletteram = `$140000`**, **spriteram = `$200000`** (independently
  corroborated by `move.w #$ffff,$200004.l`, MAME's documented
  end-of-sprite-list bit). Work RAM (`$FFC000`) was separately confirmed
  via an absolute-short-addressing census + a disassembled boot-time
  RAM-clear loop.
- **Sprite ROM pixel format — confirmed.** System 16 sprites are
  variable-width/height runs (not tiles): 4 bits/pixel, 4 pixels/word
  (big-endian, MSB-first), 0=transparent, 15=end-of-line marker. Ground
  truth: MacDonald's hardware notes (same doc), which also documents the
  full 16-byte sprite-RAM attribute record (position/pitch/palette/zoom) —
  real per-sprite frame boundaries need that *runtime* attribute RAM,
  absent from the static ROM dump, so only an unsegmented raw pixel-dump
  filmstrip is shipped. Verified two ways: a nibble-value histogram
  matches the documented semantics closely (43.9% value-0/transparent,
  14.7% value-15/end-marker, smooth 2-4% spread for values 1-14), and a
  64px-wide render of the raw decode shows clearly recognizable art (a
  complete humanoid punching-pose figure, rounded boulder/head shapes).
  `assembleSprites()` (`tools/goldenaxe/rom-inventory.ts`) +
  `decodeSega16Sprites4bpp()` (`src/assets/formats/segas16-gfx.ts`).
- **Palette *data* — confirmed and shipped.** The `re-codebreaker`
  escalation traced the boot-time palette upload
  (`maincpu.bin+0x3C64`: `movea.l #$140000,a0 / movea.l #$66e90,a1 /
  [256x move.l (a1)+,(a0)+]`, 4-way variant select via `$ec95.w & 3`) to
  its real ROM source: **`maincpu.bin+0x66E90`, 4 variants x 512 colors**.
  This **refuted** the previous pass's `+0x3811C` candidate (fire/
  explosion-style gradient) — its only absolute reference turned out to
  be a 28-byte-stride per-character record table, not colour data; the
  earlier "smoothness looks like a gradient" read was a
  `monotonic-integer-table-mimics-smooth-color-gradient.md`-style false
  positive after all. `tools/goldenaxe/palette.ts` (new) decodes all 4
  variants/64 8-colour banks; `tools/goldenaxe/build-assets.ts` now ships
  variant 0/bank 0 as the tile atlas's real palette (replacing the
  placeholder greyscale ramp) plus all 4 variants in
  `palettes/confirmed-variants.json`. Verified by re-rendering the full
  16,384-tile atlas and getting legible black/white/blue text — a
  recognizable real arcade-era anti-drug PSA ("WINNERS DON'T USE DRUGS")
  — not noise. Covers only palette entries 0-511 (the tile/text-layer
  range); the sprite palette area (entries 1024-2047) remains open.
  Tiles/sprites: only sprites still ship with a placeholder greyscale
  ramp.
- **Embedded ASCII game-content text — confirmed.** A plain `strings` scan
  over the assembled, unencrypted `maincpu.bin` (same technique as ddsom/
  ddtod/knights above — this time generalizing across manufacturers, not
  just CPS1↔CPS2) found: a 30-line attract-mode intro/ending narration
  ("OUR SWORN ENEMY... DEATH ADDER IS IN HIS CASTLE... WE'LL TAKE A
  SHORTCUT THROUGH THE TURTLE VILLAGE...") matching real, documented
  Golden Axe plot beats (domain-archetype plausibility — the giant-turtle-
  ride and "Fiend's Path" giant-eagle-flight bonus stages are genuine parts
  of the 1989 game); a 3-entry level-name + build-date debug log (UENO
  FOREST/TURTLE VILLAGE/AXE CITY + B.C.1989.1.27-29) cross-confirmed
  against the narration ("TURTLE VILLAGE" independently agreeing between
  two tables — the "two independently-located tables agreeing" oracle);
  plus UI/attract/warning/stage-select strings. **Confirmed absent**: no
  playable-character names (Ax Battler/Tyris Flare/Gilius Thunderhead) or
  monster roster anywhere as ASCII — likely tile-graphic-only, a real
  negative not a search failure. Two of the UI-text spans turned out to be
  genuinely undelimited string pools (zero separator bytes between
  distinct labels, e.g. `"STAGE 8BONUS STAGE"`) sitting right next to
  individually NUL-terminated strings in the same ROM — see
  `undelimited-string-pool-coexists-with-terminated-strings.md`.
  Extractor: `tools/goldenaxe/game-data.ts`.
- **UI-text pool boundaries — confirmed, no index table exists.** A
  follow-up disassembly pass traced every credits/stage-select draw call
  site directly: boundaries are compile-time `LEA(pc)+MOVEQ` literals
  baked into the calling code (12 credits labels), and the stage-select
  labels turned out to be a fixed-8-byte-stride array (9 stage names +
  2 trailing labels), not an undelimited pool needing an index table at
  all — the original "font-remap table" hypothesis for the two ~72-byte
  blobs right after the level-name/build-date log was traced and
  **refuted** (real consumer is an unrelated boot-time RAM-block-clear
  parameter pair); those blobs' real role is still unknown. The
  `0x7d`/`0x7e`="apostrophe" readability guess was also separately
  **refuted** by rendering the confirmed tile ROM directly (real
  apostrophe tile is `0x27`; `0x7d`/`0x7e`'s true identity is unknown).
- **Sound subsystem (Z80 + YM2151 + uPD7759) — first audio work on this
  game, largely confirmed.** Z80-disassembled `epr-12390.ic8` (radare2
  `-a z80`, flat 0x8000-byte program, no container) end-to-end. Confirmed
  the 68000→Z80 command latch (315-5195 mapper register 0x03/`$FE0007` →
  `pbf` line → Z80 `INT0` → `in a,($c0)`, matching `315_5195.cpp`'s
  `write_to_sound`/`pread`), the command-byte dispatch split (`$41`-`$54`,
  20 values, enqueue into an 8-byte FIFO feeding the uPD7759; `$00`-`$40`/
  `$80`-`$FF` dispatch immediately, identified as almost certainly YM2151
  music-track selection but not further decoded), and the YM2151
  register-write helper (busy-wait + reg-select + data-write, ~20 call
  sites). **Found and decoded a 20-entry uPD7759 sample directory**
  entirely inside the Z80 program (three parallel tables: u16 bank-
  relative start offset, u8 bank number 0-7, u16 always-zero "gate"
  field) — necessary because this chip's SLAVE mode (confirmed via a
  boot-time mode-select write, corroborated by the total absence of the
  chip's own standalone `nn 5a a5 69 55` ROM header) has no ROM-resident
  directory at all; see `upd7759-slave-mode-directory-lives-in-driving-cpu.md`.
  Ported MAME's `upd775x_device` ADPCM state machine byte-for-byte
  (`src/assets/formats/upd7759-adpcm.ts`) including the discovery that
  every sample is preceded by a 5-byte discard preamble the driving CPU's
  dumb NMI streamer blindly emits (same lesson file). Verified all 20/20
  samples decode to a natural termination with non-degenerate amplitude
  and one confirmed real cross-bank span, with no MAME/emulator
  available — natural-termination + amplitude/distinct-value statistics
  as the oracle. Shipped as raw ADPCM (client-decodes) via
  `tools/goldenaxe/upd7759-phrases.ts` + `build-assets.ts`. YM2151 music/
  note-sequence data remains open (mechanism confirmed, sequence table
  not located) — see `docs/goldenaxe/sys16/TODO.md`.
- **Not yet decoded:** the remaining ~45% of `maincpu`'s data tables
  (a second ~18 KB candidate tilemap/level-layout region at
  `maincpu.bin+0x4D04A` — repeated tile-index byte patterns — still not
  decoded against the confirmed tile-RAM word format), spriteram/
  paletteram/workram's physical mapper-region addresses (see above), a
  small pointer-table structure at `maincpu.bin+0x7440` addressing the
  intro/ending narration text (consumer not traced), the real palette
  *data* (candidate found, not code-confirmed — see below), and the
  YM2151 music/note-sequence data (see sound subsystem bullet above).

## Reusable shared code (no game-specific logic — proven reused verbatim for ddtod and knights, check before reinventing for any future CPS1/CPS2 title)

- `tools/shared/mame-zip.ts` — minimal MAME-romset ZIP reader (stored +
  deflate, TorrentZip-compatible), no project dependency needed (Node's
  built-in `node:zlib` handles both compression methods MAME/TorrentZip
  ever emit).
- `tools/shared/cps2/decrypt.ts` + `decrypt-tables.ts` — the full CPS2
  68000 decryption cipher + key decode, parameterized only by the 64-bit
  master key and encrypted-range bounds (both derived from a game's own
  `.key` file) — zero game-specific constants; proven working unmodified
  for a second title (ddtod) after ddsom.
- `tools/shared/cps2/rom-regions.ts` — generic `ROM_LOAD16_WORD_SWAP`/
  `ROM_LOAD64_WORD` byte-copy primitives, reusable for any CPS1/CPS2
  region-assembly task.
- `tools/shared/cps2/gfx.ts` — the CPS1/CPS2 shared planar tile decoder
  (`decodeTile()`/`CPS1_LAYOUT_16X16`) plus CPS2's extra
  `cps2UnshuffleGfx()` bank-deinterleave (call it for CPS2 gfx regions;
  skip it for CPS1 — see the ddsom entry above for why the two differ).
  `decodeTile()`/`GfxLayout` themselves are misnamed-but-genuinely
  engine-agnostic (a verbatim port of MAME's own `gfx_element::decode()`,
  shared by the whole emulator, not a CPS-specific abstraction) — confirmed
  by reuse, completely unmodified, for blktiger (a materially different,
  pre-CPS Z80 board with its own from-scratch `gfx_layout` tables). Worth
  checking here before writing a new planar-tile interpreter for any
  future MAME-driver title, CPS-family or not.
- `tools/shared/cps2/palette.ts` — `decodeCps1PaletteWord()`/
  `decodeCps1PaletteWords()`, a direct port of MAME's
  `cps_state::cps1_build_palette()` palette-RAM word format (12-bit RGB +
  4-bit brightness). Confirmed for CPS1 (knights); **not yet verified
  against real CPS2 data**, but `cps1_build_palette()` is defined once in
  `cps1_v.cpp` and shared by both the CPS1 and CPS2 MAME drivers, so this
  is worth checking against ddsom/ddtod before re-deriving a palette word
  format from scratch for them.
- `src/assets/formats/qsound.ts` — Capcom QSound (DL-1425/DSP16A) PCM
  sample decoder (`decodeQsoundPcm()`) + the Z80 mailbox protocol/
  per-channel register-address constants (`QSOUND_REG`/`QSOUND_PORT`).
  Zero game-specific constants; proven working unmodified for a second
  title (ddtod) after ddsom, same pattern as the cps2/decrypt.ts
  precedent above. Not CPS2-specific either — QSound shipped on other
  Capcom boards (some CPS1 titles too), so this is reusable beyond this
  project's current two games. Browser+Node safe (no platform imports),
  same convention as `oki-adpcm.ts`.
- `src/assets/formats/upd7759-adpcm.ts` — NEC uPD7759 ADPCM speech-chip
  decoder (`decodeUpd7759Slave()`), a direct port of MAME's
  `upd775x_device` state machine (block-header grammar + step/state
  tables). Zero game-specific constants (the game-specific part — the
  sample directory itself — lives in `tools/goldenaxe/
  upd7759-phrases.ts`, same producer/consumer split as `oki-adpcm.ts` +
  knights' `rom-map.ts`). This chip is a commodity late-80s/early-90s
  arcade speech chip used across many boards (not Sega-specific), so
  worth checking here before re-deriving it for a future title in this or
  a sibling project. Browser+Node safe, same convention as
  `oki-adpcm.ts`/`qsound.ts`.
- `tools/ddsom/rom-map.ts` / `tools/ddtod/rom-map.ts` / `tools/knights/
  rom-map.ts` are the genuinely game-specific files (which filenames go in
  which region, at what offsets, and whether the CPS2-only unshuffle
  applies) — this is the only thing a future CPS1/CPS2 title in this
  project should need to write fresh, from its own CRC-matched
  `ROM_START` block. knights confirms this held for the CPS1 side too:
  writing its `rom-map.ts` needed zero changes to any shared module.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/kolbold` | D&D: Shadows over Mystara + Tower of Doom (Capcom CPS2), Knights of the Round (Capcom CPS1), Golden Axe (Sega System 16), Black Tiger (Capcom, 1987, pre-CPS Z80+i8751 hardware) — first MAME/arcade-ROM-set corpus project (not Amiga/DOS). ddsom/ddtod (CPS2): romset container fully identified (CRC32-matched to mamedev/mame's own `ROM_START`), CPS2 68000 Feistel encryption solved + verified, CPS1/CPS2 4bpp planar tile format + CPS2's extra bank-unshuffle solved + verified (196,608 / 98,304 tiles render as recognizable sprite art); palette now has real, confirmed, shipped ROM color data for both games (ddsom: 8 fixed-address 16-color banks via the `ori.l #$f000f000` idiom; ddtod: one always-reachable 512-color page via a different table-indexed mechanism with no brightness-forcing — ddtod does not use ddsom's idiom at all), though which bank/page is active on any given real screen is still open for both; ddsom's monster/enemy numeric stats (a flat 51-row per-type starting-HP table + its ten per-pool dispatch tables) and its large/boss-pool type-id→name bridge (21/23 types, via a previously-missed boss-HUD name table found by widening a PC-relative-only xref scan to absolute-long constants) are both now solved too (regular-pool names still open); ddtod's own monster/player combat-stat tables are now solved too, via a differently-shaped HP-init a `re-codebreaker` escalation found after this project's own search stalled (see `narrow-opcode-form-census-false-negative.md` and `negative-from-addressing-root-not-shapes.md` for the two generalizable pitfalls this surfaced); a later session named all 10 of ddsom's object pools for real via a factory debug-menu label table cross-checked byte-exact against their independently-derived addresses (confirmed `ITEM WORK`/`BOX WORK`/`SET WORK`/etc. pools — a genuine advance on item/level data — plus an unresolved `BOSS`/`ESHL` naming tension against the already-traced pool roles, see `debug-menu-label-vs-traced-consumer-conflict.md`), and separately found a second, previously-undocumented per-stage-node table (paired with the already-confirmed difficulty-rank table at the identical code site, see `confirmed-index-shared-by-second-parallel-table.md`) that selects a monster-spawn-table block; a later follow-up SOLVED item icons (generalizing the confirmed sprite-animation VM to the `ITEM WORK` pool — a treasure chest, ring, sword, mace, and food item all render unmistakably) and SOLVED a real room/dungeon background tilemap-fill mechanism (a third consumer of the stage-node index gates SCROLL3 chunk-based background code, rendered as a coherent real tiled scene), while the "Green Dragon" boss's own spawn site remains unlocated after 5 independently-shaped searches and is escalated to `re-codebreaker` — see `game-re-corpora/kolbold.md` for the full chain. knights (CPS1): romset container confirmed byte-exact (23/23 CRC32), 68000 program confirmed **unencrypted** (verified empirically, not assumed — CPS1 predates CPS2's opcode cipher), same 4bpp planar tile format solved + verified with **no** bank-unshuffle needed (32,768 tiles; confirms the CPS1/CPS2 split predicted from the CPS2 work); boot-time palette **confirmed** by a traced 68000 code path (real 512-color/32-bank ROM table, real CPS-B hardware register/mechanism, cross-checked against MAME's own `cps1_build_palette()` — a genuine advance over ddsom/ddtod/goldenaxe's still-open or unconfirmed palettes), though per-tile bank assignment and whether gameplay overwrites it per-level remain open; **scroll1/2/3 tilemap RAM word format confirmed** both from source (`cps1_v.cpp`'s `get_tile0/1/2_info`, genuinely CPS1/CPS2-shared, re-verified from a fresh source fetch) and from real, disassembled, live knights code that builds and writes the exact word shape to scroll1 RAM — one call site's decoded string-table content matches the game's own already-documented self-test menu text byte-exact (see `gfx-region-shares-multiple-tile-granularities-per-layer.md` and `attribute-word-spare-bits-hold-game-logic-metadata.md` for two pitfalls this surfaced); **real game-content data confirmed** — a 25-entry enemy/object name roster found the same way as ddsom's (plain `strings` over the assembled ROM, here needing no data/opcode split at all since CPS1 has zero encryption), verified via a self-terminating variable-length record grammar plus exact-set-membership against two independent published Knights of the Round boss/enemy rosters (20/25 names matched, 5 extra plausible-but-unconfirmed kept) — see `published-walkthrough-numeric-oracle.md`'s roster-matching variant; two adjacent pointer-index arrays referencing that table were also found (structure confirmed, consumer not traced). goldenaxe/sys16: romset + board revision confirmed byte-exact (unencrypted 68000 + i8751 MCU, not FD1089/FD1094), 8x8 3bpp planar tile format + 4bpp variable-width sprite pixel format both solved + verified (16,384 tiles via legible text; sprites via nibble-histogram statistics + a recognizable humanoid figure render), 68000 boot code disassembled (930 r2-auto-analyzed functions, ~55% coverage) with the I/O region's and the text/tile RAM mapper region's (`$100000`/`$110000`) physical addresses both confirmed — the latter via a system-wide LEA/PEA absolute-address census, bucketed by 64 KB bank, that also generalizes past this one game (see `game-re-tooling/mame-arcade.md`); spriteram/paletteram/workram bases still open. **Real game-content text confirmed** via plain `strings` over the assembled ROM, finding a 30-line attract-mode intro/ending narration matching real Golden Axe plot beats (domain-archetype plausibility) plus a small level-name+build-date debug log cross-confirmed against it ("TURTLE VILLAGE" independently agreeing between two tables) — see `undelimited-string-pool-coexists-with-terminated-strings.md` for a distinct pitfall hit along the way (some adjacent UI-text spans in the same ROM are genuinely undelimited pools, not NUL-terminated like the rest); playable-character names (Ax Battler/Tyris Flare/Gilius Thunderhead) and any monster roster confirmed absent as ASCII (likely tile-graphic-only); UI-text pool boundaries (credits + stage-select) fully traced and confirmed **without a data-driven index table** — every label boundary is a literal per-call-site `LEA(pc)+MOVEQ` operand pair in the draw code, and the stage-select labels turned out to be a fixed-8-byte-stride array, not an undelimited pool; a co-located "font remap table" hypothesis was separately traced and refuted (see `no-remap-draw-path-is-free-glyph-oracle.md`). **Superseding the above:** a `re-codebreaker` escalation later found the 315-5195 mapper's own register file + a 16-byte config table in ROM giving the full memory map from data (not instruction-operand census, since the i8751 MCU — not the 68000 — programs the mapper), overturning a paletteram/spriteram swap and locating real, DAC-accurate palette data (`maincpu.bin+0x66E90`, 4 variants x 512 colors, MAME's real resistor-ladder DAC ported verbatim — see `binary-weighted-resistor-dac-near-linear.md`), now shipped. **Sound (this session):** Z80-disassembled the sound driver end-to-end — 68000→Z80 command latch via the same mapper (register 0x03), YM2151 register-write mechanism confirmed, and a 20-entry uPD7759 speech-sample directory found *inside the Z80 program itself* (the chip runs in slave mode, which has no ROM-resident directory — see `upd7759-slave-mode-directory-lives-in-driving-cpu.md`); MAME's ADPCM state machine ported byte-for-byte and verified against all 20 real samples (natural termination, non-degenerate amplitude, no MAME available). Music/note-sequence data remains open. **Sprite asset-quality pass (later session):** the shipped raw sprite atlas (one arbitrary fixed-64px filmstrip reshape) was user-flagged as unusable; a HEURISTIC (not confirmed) static-analysis segmentation now ships alongside it, using the confirmed end-of-line pixel marker for real per-row width plus a corpus-tuned long-blank-run heuristic for candidate inter-sprite gaps (1,305 candidate chunks recovered from 463,140 real rows, spot-checked as real non-random structure by render) — see `terminator-plus-blank-run-heuristic-segments-uncapturable-sprite-dump.md` for the generalizable technique and the ROM-gap sanity-cap trap it surfaced; a secondary check also confirmed applying any real (even wrong-bank) ROM palette measurably aids visual inspection of greyscale index data. **goldenaxe headless CPU-emulation harness (later session):** built a Musashi 68000 boot/runtime harness (`tools/goldenaxe/emu/`, vendored fresh from `github.com/kstenerud/Musashi`, MIT) that boots the real `maincpu.bin` from its own reset vector and runs it for real — the first program-scale (not single-subroutine) CPU-emulation harness in this project, following the pattern already proven at subroutine scale in `crawl/tools/bcdft_decompress/emu.c`. On this i8751-MCU board the mapper is configured by the MCU before releasing the 68000 from reset, so the harness doesn't emulate the MCU's mapper-config step at all — it hard-wires the already-confirmed live physical address map directly into the memory callbacks (see `game-re-tooling/mame-arcade.md`). Found and stubbed 2 genuine i8751-dependent spin-wait blockers (a status byte and a 4-word hardcoded-checksum compare, both confirmed all-reads/zero-writers in 68000 code via exhaustive `/x` scans — see `coprocessor-status-byte-all-reads-no-writes.md`), then ran 900 simulated frames to real steady-state execution, **dynamically confirming a separate static-analysis session's sprite-template-pool-writer finding byte-for-byte** (a PC-tagged write-address log matched the static disassembly's own cited field-write instructions exactly) and producing the first-ever real per-frame sprite-attribute values for this game. Also corrected a writer entry-address citation via an `axt` xref census, and hit a real pool-boundary bug along the way (a shared boot-clear loop's iteration count over-clears past each pool's real size — see `shared-clear-loop-overclears-past-real-pool-boundary.md`). blktiger/arcade (first-pass session): a materially OLDER, unrelated hardware generation (dual Z80 + a real Intel 8751 MCU, no CPS-ASIC) — romset confirmed byte-exact (20/20 CRC32), main-CPU non-encryption confirmed (source + empirical disassembly), all 3 `gfx_layout` tile formats solved + verified by render reusing `tools/shared/cps2/gfx.ts`'s `decodeTile()` **completely unmodified** (confirms it's genuinely engine-agnostic, not CPS-specific — see that file's corpus entry), `palette_device::xBRG_444` palette format confirmed from source (a new, non-CPS-B palette family; boot-time color values still open, no static ROM table found), and a 27-line NPC dialogue-text corpus decoded via a simple +1-letter-shift cipher (confirmed via 3 full-sentence decodes + a domain-archetype match on "zenny"/"Spinning Scull") — surfaced two new generalizable pitfalls, `rgn-frac-total-field-fraction-scales-tile-count.md` and `printable-terminator-byte-defeats-delimiter-pair-scan.md`. blktiger (4th session): the Intel 8751 MCU's own 4096-byte internal program is now fully disassembled (radare2's native `8051` arch plugin -- a 3rd distinct ISA in this project after both Z80s) and its protection algorithm CONFIRMED byte-exact, not a hypothesis -- a trivial 16-entry static substitution table (mask received byte to its low nibble, table lookup, reply), decisively cross-checked against the Z80 main program's own embedded copy of the identical table (two independent call sites build their "expected reply" table by reading their own following instruction bytes as data -- see `protection-check-table-hidden-as-following-instruction-bytes.md` -- byte-identical to the MCU's table at all 3 locations, zero deviation); surfaced `r2-arch-flag-before-dashdash-file-separator.md` (a CLI arg-order bug that made the real, valid, mostly-erased MCU ROM look falsely blank). blktiger (5th session): `bd02.9j` (one of 4 PROMs) CONFIRMED structurally as the real hardware source behind the driver's own source-flagged "unverified guess" bg-tile priority table (exact 8-bin match, zero deviation — see `game-re-tooling/mame-arcade.md`'s new "driver's own guess table" technique); a prior "bonus/score table" lead was corrected to a real NPC shop price/item gate gated by a hardware Difficulty DIP switch (confirmed byte-exact against the driver's own `PORT_DIPNAME` mask — see that file's new DIP-switch-value-oracle technique), closing the loop to two already-decoded dialogue lines — see `unreferenced-doc-string-numeric-match-wrong-role.md` for the misidentification pitfall this surfaced. ddsom (follow-up): the Z80 QSound envelope-state dispatch's register-write targets (volume + playbackRate, plus the note-select table's `flags` byte's real role) are now confirmed, and the top-level game-mode dispatcher's full table was enumerated, finding 6 mode values converge on one shared routine (see `jump-table-distinct-targets-may-be-shared-routine-entry-points.md`). ddsom (3rd follow-up): a real, engine-wide sprite-animation VM (keyframe script → sprite-definition blob → verbatim OBJ_BASE tile-code write) was found and traced end to end by resolving a boss type's state-0 body one level past its shared prologue (see `shared-subroutine-reached-from-inside-type-body-not-entry-stub.md`), applied to the Green/Black Dragon pair's own real spawn data (rendered greyscale: a coherent creature silhouette, not conclusively dragon-shaped — `hold-cmd-means-permanent-not-invisible.md` documents a decode pitfall hit along the way); separately corrected an earlier "monster-spawn-block index" hypothesis to a class-gated treasure/encounter-box selector by finishing an explicitly-flagged incomplete trace to its real object-allocator call. ddsom (4th follow-up, Z80 music-sequence format): vgmtrans's CPS2Seq/CPS2TrackV1/CPS2Instr reference decoder — with a ddsom-specific `mame_roms.json` entry and two ddsom-specific bug comments in its own source — was used as a starting hypothesis then independently re-verified against real ROM bytes: 923 real songs found (921 valid), 100% (1846/1846) of tracks decode cleanly, the already-confirmed 256-entry sample table extends to a real 344 entries (reproducing vgmtrans's own "index 290" bug comment byte-for-byte), the table's open "flags" byte is now identified as a MIDI unity-key, and 5 decoded program-change events resolve end-to-end to real, non-degenerate PCM audio — surfaced two new generalizable pitfalls, `reference-tool-own-loader-address-space-differs-from-yours.md` (vgmtrans's own ROM-loader uses a different, gapless addressing convention than this project's MAME-faithful region assembly) and `opcode-case-consolidation-drops-hidden-state-mutation.md` (a real bug caught during promotion). ddsom (5th follow-up): generalized the sprite-animation-VM composite-render technique to a SECOND, separate object pool (the regular/22-slot enemy pool, 28 types, never attempted before) — found a third VM-entry shape this pool needed (the shared trampoline used as a literal direct-call target, plus `jmp` alongside `jsr` to the same literal target, see the sharpened `narrow-opcode-form-census-false-negative.md`) and shipped 25/28 types as non-degenerate renders; two of them (regular types 18/27) resolved to animation tables BYTE-IDENTICAL to two already-named large-pool boss types (Manticore/Ogre), confirming a pre-existing moderate-confidence cross-pool hint (found via a wholly different mechanism, a reach/hitbox creature-id field) via a second independent structural signal — a fresh worked example of the "two independently-located tables agreeing on a specific number" oracle. blktiger (8th session): extended real palette VALUES from 122/1024 to **896/1024** by generalizing the already-proven `ldir`-destination search past literal immediates to also trace `pop de` and ROM-data-table (`ld e,[hl]`) header-read destinations, invisible to a text/regex scan — found a shared bank-6 "palette script" state machine (7 confirmed-reachable call sites) covering ALL of TILES, ALL of SPRITES, and ALL of CHARS (the UI/dialogue-text layer, previously 0% — now real colored text, not greyscale), plus a TILES-group9 fire-flicker animation; only a 128-entry unused index gap remains open (see `copy-destination-may-be-data-not-operand.md`) | `game-re-corpora/kolbold.md` |
