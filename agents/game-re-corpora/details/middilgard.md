# middilgard — War in Middle Earth, Spirit/Vengeance of Excalibur, Conan, Warriors of Legend

**Project root:** `~/Development/middilgard`

**Melbourne House / Synergistic engine family** — all five share a classic Mac **resource-fork** container, differing only in endianness and byte-reversed FourCCs per platform (`IMAG`/`GAMI`, `FRML`/`LMRF`, `MMAP`/`PAMM`). IMAG/FRML have 28/27/6-byte header variants across games; PackBits **and** LZSS, auto-detected. Also: SMUS/Sonix audio, DOS GAMI/LMRF, CDTV Red Book audio driven by both track-number *and* MSF-range addressing.

**`SCEN`/`NECS` scene format — solved for Vengeance, Spirit, *and* Conan; the single most useful worked example here.** Still re-derive per game (Vengeance's per-object bitfield is 10/9/8/1/4 with `+0x320`/`-0xbe`/`-0x32` biases and a trailing global descriptor; Spirit's is 11/9/8/1 with no biases and no global entry; Conan's is 11/9/8/1/3 with **no** `refId` bias, a 4-byte header, and an 8-word trailer instead of a global descriptor). Conan's own two Amiga executables have no static 68k code left to trace (see the `bcdft`-shared-hunk-shape note below) — its SCEN was cracked instead from the **DOS port's `START.EXE`**, a Borland C++ MZ executable that had been wrongly written off as "LZEXE-rejected" (a crack-tampered `e_ip`/`e_cs` in the MZ header, not an unsupported codec — patch `e_ip`→`0x000e`, `e_cs`→`0x14a2`, refresh `e_cblp`/`e_cp` to the real packed size, then stock `unlzexe` works). Worth checking in any DOS-era game whose "launcher" `.exe` search comes back empty: the real engine may be a *different*, separately-packed executable one directory-listing entry away. Verified 6,513/6,513 (later 6,542/6,542) Conan object entries with zero cross-class contamination and 6,372/6,372 cross-platform (DOS vs Amiga) field agreement. **Two things transfer and are worth checking first in any game in this family**:

1. **The entry longwords are stored byte-reversed on disk**; `_LoadScene` reverses all four bytes of each of the `(count+1)` entries in place after reading, gated on the resource loader's "freshly read from disk vs. cache hit" flag. Confirmed in both Vengeance's and Spirit's own `_LoadScene`. Missing this is what left Vengeance's `refId` field sitting at a coincidental 51.7% resolution for a long time, mis-read as an unmapped second id space — see `partial-resolution-rate-is-noise.md`, which this project sourced. With the fixup: Vengeance 4911/4911 = 100% (4537 `IMAG`, 100 `FRML`, 265 synthetic door rectangles, 9 entity anchors), all 266 scenes composite to real PNGs; Spirit 24.2% → 99.9%.
2. **`refId` is multi-class, dispatched on a flags byte** (`_aCharFlags[typeIndex] | flagBit`), not on the id: bit 6 = entity anchor (not drawn — the entity loop reuses the entry's x/y), bit 5 = `FRML` id, else `id > 0x707` = a synthetic door/exit rectangle from the `_idDoorRect`/`_wDoorRect`/`_hDoorRect` tables (no resource opened at all), else `IMAG` id.
3. **A `SCEN` resource id is itself computed, not authored per-location** — `_LoadScene` takes a single "location" byte (an index into the game's own locations table) and multiplies a second scalar into it: Spirit is `subScene*100 + loc` (subScene = a fixed 0-6 view-type enum); Vengeance is `scenario*100 + loc` for `loc` in a 40-74 window, plain `loc` otherwise (scenario = the current episode number, 1-8). Same shape, different second axis — expect a third variant, not the same constant, in any other game in this family. Both verified as a zero-deviation structural classification of the *entire* real `SCEN` id corpus (Spirit 138/138, Vengeance 266/266) before being trusted.
4. **Spirit's 28 reserved "terrain-backdrop" `SCEN` ids (901-928) are army/force-encounter scenes, not plain wilderness art.** Rendering all 28 found 26/28 bake a standing troop formation (IMAG #1065) + a colour banner (#1066-1071) directly into their object list; tracing further up from the already-confirmed dispatch found `_OpenScene`'s wilderness branch sources its (x,y) from an *existing* `_aForces[i]` position, with `i` set by `_DoMobilIcon` — the handler for clicking a moving force icon on the map, never a bare tile. A click-any-tile viewer feature that faithfully ported the terrain-category dispatch table (both tables remain byte-exact, unmodified) but had no "is a force actually here" gate therefore showed a false army encounter for ordinary wilderness. See `docs/spirit/amiga/engine.md` § "Why does clicking a forest tile show soldiers?" for the fix (filter the force objects on the ungated tile-click path only) and the new `corpus-wide-render-reveals-trigger-scope-not-decode-bug.md` lesson this sourced — check whether Vengeance's own equivalent terrain-backdrop mechanism (same reserved 901-928 id block, independently traced) has the same shape before trusting its click-any-tile viewer either; not yet checked.

**Engine-family lever: these executables ship `HUNK_SYMBOL` blocks** (`ExcalII` ~1168 real C names; Spirit's CDTV builds 1,147 and 559) that name the DATA-hunk tables outright — `_aCharFlags`, `_idDoorRect`/`_wDoorRect`/`_hDoorRect`, `_apPaletteIndex`, `_apCoReMapTbls`. Combined with resolving A4-relative `JSR` displacements through the SAS/C jump-table stubs at the head of the DATA hunk (see `game-re-method/finding-the-reader.md`), the whole scene-drawing path becomes self-documenting in one pass.

**FRML/LMRF codec selection is a second, independent decode axis from the header shape** — `decompressFRML()` tries PackBits and LZSS and, when both hit the exact declared output length, must tie-break with a downstream structural check (frame 0's implied bitplane depth, `dataSize/(bytesPerRow*height)`, dividing to a clean 1-8 integer under the right codec and not the wrong one) rather than a fixed codec preference. Wrong-codec decodes aren't obviously broken: the frame count and total length can both read back correct by coincidence while the frame table itself is silently corrupted. Cost Vengeance 3 "endOffset overflow" FRMLs that were misdiagnosed as a recovery-formula bug for a long time when the real defect was upstream, in codec choice.

**Conan the Cimmerian's `Game`/`Conan` executables share their compressed-DATA-hunk shape with Black Crypt's `bcdft`** (a different game, `crawl` corpus) almost exactly — an identical 7-hunk layout (CODE bootstrap / 3× BSS decompression targets / CODE engine / DATA compressed input / BSS window), right down to the smallest BSS target being exactly 4 bytes in both. What was believed to be Apple PackBits (decompressed by the project's generic `packBitsDecompress`, which ran to completion at a plausible size) is actually the same class of custom backwards-reading LZ77 engine as `bcdft` — cracked by disassembling the executable's own small CODE hunk directly and running it under a musashi emulator (`tools/conan/decompress-data-hunk/`), the same solution `bcdft_decompress` already used. If a fourth game in this family (or a sibling corpus) turns up the same hunk-size fingerprint, try this route before assuming a new codec. The correctly-decompressed DATA hunk also yielded Conan's real scene and loader/splash-screen palettes (a second `re-codebreaker` escalation, `Game` hunk2 offset `0xe8c` for four 32-color in-game scene variants, `Conan` (loader) hunk2 offset `0x7cc` for six 32-color per-screen splash palettes, traced to their screen assignments via the DOS port's `CONAN.EXE` — a single global `curPalette` pointer set by literal immediate-operand writes at 7 exhaustively-found call sites, the operand being the IMAG resource id about to be displayed). **The palette block had already been found once, one 4-byte record too early (`0xe88`)** — an immediately-preceding index/enumeration ramp's tail bytes coincidentally decoded as a plausible-looking leading colour entry; only proving the block's boundary on *both* sides (preceding ramp vs. following filler, exact on both a 4-byte-record Amiga port and a differently-packed 3-byte-record DOS port) caught the shift. See the new `adjacent-ramp-table-masks-off-by-one-record-start.md` lesson this sourced. Separately, **`.L32`/`.L16` loader-asset files are a false-cognate, not a use of this same LZ77 engine**: despite looking undersized for raw pixel data, they are ordinary big-endian Mac-style resource forks (the exact same container every `.res` file uses) — a first `re-codebreaker` escalation found the "16-byte header" fields a prior pass had read as `imag_off`/pixel-region-size were actually the resource-fork's own `mapLength`/`mapOffset` under different names. See the `emulator-harness-input-boundary-not-algorithm.md` lesson this sourced.

**Conan's 101 `FRML` sprite-animation resources (ANIM32.RES/ANIS32.RES/INTFM32.RES) are now partially segmented into named animation states** (`src/assets/formats/conan-frml-animations.ts`, wired into `tools/conan/build-assets.ts`'s manifest as an `animations` array per resource). 23/101 are code-confirmed single-clip scene-decoration loops (torch flicker etc. — see the already-solved `SCEN` `typeIndex 4/5` dispatch above, cross-referenced against the full `FRML` id space as a free classifier for an unrelated question). The other 78 (`ANIS32.RES` 55-89 combat sprites, `ANIM32.RES`'s 14 player poses) have **no code-level frame-range table findable anywhere in `START.EXE`** — direct resource-id immediate loads, the scene-FRML-renderer function itself, a DGROUP byte-value census, and filename-string xrefs all came up empty or too noisy to use, consistent with these ids being looked up from a still-uncracked monster/entity data table rather than hardcoded per call site. A render-derived geometric heuristic (a trailing frame run that's much shorter and about as wide as the resource's own tallest/widest frame reads as a death collapse) fills the gap, graded `confidence: 'hypothesis'` throughout — see `docs/conan/amiga/engine.md` § "FRML Animation Segmentation" for the full paths-tried table, and `game-re-method/verification-techniques.md`'s new geometric-collapse-heuristic entry for the general technique.

**Warriors of Legend's `restart.dat` also holds a character/party table** (10 fixed 210-byte records at offset 0, id `0x07d0+n` sequential, id/name confirmed) and `res32/sfx.res`'s `XFSD` digital sound effects are resolved 26/32 (an 8-byte header — `u16` decompressed size, `u16` sample rate with real DOS-era values `{4000,5000,6000,8000,11000}` Hz, a constant format tag — then the *existing* `packBitsDecompress()`, no new codec needed). The character table's record boundary was initially misread as variable-stride because the *next* record's id (and sometimes name prefix) is duplicated a few bytes before the true boundary, at the *current* record's own tail — see the new `next-record-preview-defeats-stride-detection.md` lesson this sourced.

**Warriors of Legend (DOS VGA) — GAMI/LMRF fully resolved (1069/1070, 162/162), PAMM map dimensions and atlas pairing resolved for all 5 regions, `wofl.exe` is a Borland-style in-file-overlay executable that stalled static tracing.** A stale format description ("ff-only RLE") had been folded into this game's docs from WIME DOS's unrelated `BSCENE.RES`-specific variant and never actually matched what the pipeline decoded — Legend's GAMI/LMRF use the same PackBits/LZSS + 6-byte-header planar convention as Spirit/Vengeance/Conan. Root-cause bugs, all now fixed in the shared `imag.ts`/`frml.ts`/`resource-fork.ts`: (1) the LE byte-swap fixup for GAMI/LMRF's size-prefix header was applied uniformly and corrupted 12 resources stored *uncompressed* with no such prefix (see `optional-per-record-compression.md`'s fixup-vs-decompressor addendum); (2) the FRML PackBits-vs-LZSS tie-break false positive (already documented above for Vengeance) recurred here too, on 18 `ani2.res`/`ani3.res` resources; (3) `frameCount === 0` means "single full image" (a plain 6-byte IMAG header), not "no content" — the logic is real but its one known live example (`extra.res` #2000) turned out to be a resource-fork id-pairing artifact (see next paragraph) and decodes as an ordinary animation once fixed, so no confirmed real trigger remains; (4) the resource-fork reference-list layout bug below. Legend's 5 PAMM map regions (none matching any Amiga-typical width) were solved by rendering every factor-pair/atlas-pairing candidate and picking the sole comb/shear-free result — see `tile-grid-dimension-needs-render-not-just-bytecount.md`. `wofl.exe` itself (no symbol table, a `"Runtime overlay error"` string, an oversized `0x1800`-byte MZ header) stalled static tracing for entity/location/item data; `restart.dat` (a canned restart-state file) turned out to hold a clean plaintext item-type table instead — see `canned-save-state-mirrors-exe-struct.md`. Separately, `scenes.res`'s `NECS` scene names (not the still-unsolved object-list body) decode via a period-9 byte-discard interleave — see `text-field-periodic-interleave-byte.md`.

**Warriors of Legend's `NECS` scene format is now fully solved (was the
last major undecoded format for this game) — it is LZSS-compressed, the
same `u32-LE-size-prefix + stream` convention as the game's own `PAMM`/
`GAMI`/`LMRF`, and every prior "structural" reading of it (a 32-byte header
with an irregular type marker, a period-9 name interleave, `byte@1`/`byte@7`
length correlations with no exact stride) was an artifact of analysing the
*compressed* bytes — see `undecoded-format-may-be-compressed-with-known-
codec.md`, sourced this session via a `re-codebreaker` escalation. The real
decompressed format is a 32-byte scene header + N 32-byte object records
(discriminated by a `u16` resource-reference id into three classes: sprite,
a flat quadrilateral primitive at a fixed `id==1999`, and unresolved markers
at `id ∈ {1504,1512,1514}`) + a length-prefixed name field; all 316 scenes
render as recognisable, correctly-coloured locations. The same suspicion
applied to this game's still-open `TAPM` tile-patch format found 37 of 84
resources are *also* LZSS-compressed (the other 47 genuinely raw) — a
second, independent confirmation of `optional-per-record-compression.md`'s
pattern in the same project. Also this session: Legend's VGA palette offset
was wrong (`wofl.exe+0x1180`, inside the exe's own MZ header, not the load
image) and is corrected to `+0x16B33`, found while ground-truthing the NECS
render; and the character/party table's 5 base attributes (Strength/Wisdom/
Intelligence/Agility/Stealth, 0-20 range) are confirmed via a *gameplay-
observed* (not data-table-sourced) fan review as the numeric oracle — see
`published-walkthrough-numeric-oracle.md`'s second worked example.

**Warriors of Legend's `LMRF` frame-index → named-animation mapping (idle/
walk/attack) is now recovered structurally** for 34/162 resources
(22 render-confirmed, 12 more via a cross-resource exact-frame-dimension-
prefix match), the rest hypothesis-level — `wofl.exe`'s untraceable overlay
structure (see above) ruled out an executable-derived table, so this came
from frame bounding-box geometry alone: a sustained width/height
discontinuity, and pairs of resources whose whole frame-dimension sequence
is an exact prefix of a longer sibling's. See
`sprite-frame-geometry-reveals-animation-segments.md`, sourced this
session, and `docs/legend/plan.md` § "LMRF animation segments" for the
per-resource evidence.

**The shared resource-fork container parser (`src/assets/formats/resource-fork.ts`) had two bugs affecting every DOS/LE-platform game in this project, found and fixed while re-verifying a Conan-specific TODO item.** (1) On little-endian files, a reference-list entry's `{attributes, dataOffset}` word is byte-reversed as a *whole unit* relative to the BE/Amiga layout (`dataOffset:u24 LE` then `attributes:u8`, not attributes-first) — the parser read the BE field positions unconditionally, silently mis-pairing ids with the wrong data blocks for the minority of entries whose bogus offset happened to look plausible (most were masked by a "stale offset → sequential scan" fallback that ignores per-entry offsets entirely). Confirmed structurally (monotonic-offset test) across Conan DOS `SCENES.RES`, Legend `furn.res`/`sfx.res`, and WIME `ASCENE.RES`, and by a byte-exact cross-platform SCEN field-agreement check (6,372/6,372) after the fix. Fixing it retroactively resolved several previously-recorded Legend findings that turned out to be built on mis-paired data, not real decode failures. See `port-reverses-whole-header-word-not-per-field.md`, sourced this session. (2) `swapSizeHeaderIfNeeded()`'s "is this an uncompressed IMAG?" guard checked only a single marker byte (`data[0] === 0x02`), which a genuinely-compressed resource's real LE size-prefix low byte can coincidentally equal — confirmed on one resource each in Conan (`RES32/DUNG32.RES` #1422) and Legend (`res32/walls.res` #2166). Fixed by requiring the full exact-length structural invariant the project's own `isUncompressedIMAG()` already implements. See `byte-value-collision-defeats-marker-only-guard.md`, sourced this session.

**WIME Amiga's `SynthSceneObjects` (the `BScene` zoomed-scene procedural
object generator, `sub_00D3C`/`LAB_0281`) is fully solved and reimplemented**
after four-plus prior static-tracing sessions had progressively found more
runtime dynamism (PRNG-branched building variants, cross-object X reads,
dynamic flags) without ever reaching a complete model — escalated to
`re-codebreaker`, which wrote a symbolic 68k executor over the real
disassembly text (see the "selective branch-forking" technique this
sourced in `re-codebreaker/SKILL.md`) and enumerated all 276 feasible
execution paths across the 31 handled terrain values, finding three
mechanisms the escalation brief never asked about: a 3rd calling argument
reused as an output parameter, an object-array cursor that can rewind-in-place
or reset-to-zero (not just append), and a 13-terrain bijective return-value
determination gating a second caller-side object. See
`docs/wime/amiga/bscene-format.md` § SynthSceneObjects for the full
derivation and per-terrain table — worth reading before assuming a
similarly-branchy dispatch function elsewhere in this engine family (or any
other) needs the same treatment.

**Vengeance of Excalibur's DOS VGA port (`data/vengeance/dosvga/`) confirms two coexisting, independently-verified kinds of cross-platform table difference in the same `episode*.dat` file**, found with zero disassembly (no symbol table exists for the x86 `game.exe`): the entity table carries over byte-identical offset/stride from Amiga, differing only in numeric-field endianness (native x86 LE vs 68k BE); the location and item-type tables are genuinely 1-byte-narrower per record *and* start at a different absolute offset; the item-placement table keeps the same stride as Amiga but shifts its start offset only, with one field staying big-endian on **both** platforms (confirmed byte-identical, not just structurally equivalent). Found via string-searching known names and checking whether the byte delta to the already-known Amiga offset stays constant across consecutive records — see `cross-platform-string-delta-reveals-stride-vs-offset.md`, sourced this session. A task-brief premise ("DOS VGA ships only 2 episode files") was simply wrong — it ships all 7 + `finish.dat`, exactly mirroring Amiga; always `ls` the directory yourself rather than trusting a stated inventory. Also this session: Vengeance's terrain factor/type tables (`_bTerrainFactor`/`_bTerrainType`, 256 bytes each) are statically compiled into `ExcalII`'s DATA hunk, **not** runtime `EPISODE*.DAT` buffers as a TODO item's opening hypothesis assumed — refuted by comparing raw content richness against the executable's own confirmed-runtime-buffer table (`_aForces`, all-zero at rest) and a byte-exact absence search across all 7 episode files (see `verification-techniques.md`'s "Content richness distinguishes..." addendum). And a shared-decoder bug (`decodeIMAG()`'s too-small guard checked a compressed resource's raw on-disk length against a decompressed-header-size threshold) closed the last open IMAG/GAMI failures in **both** Vengeance (2 of its original 20) and Warriors of Legend (1) simultaneously — see `pre-decompression-guard-uses-decompressed-threshold.md`, sourced this session.

**Vengeance's DOS VGA `game.exe`/`vex.exe` turned out to be LZEXE v0.91-compressed** — the reason an initial known-content byte search (using the Amiga `ExcalII`'s confirmed 20×32-byte remap tables and 256-byte terrain factor/type tables as a search oracle) found nothing but noise-level 4-6-byte coincidences. Decompressing first (`tools/shared/lzexe.ts`, a TypeScript port of the classic `unlzexe.c`, verified byte-exact — 0 diffs across 223,248 bytes — against the reference C tool's output, and cross-checked against Conan's own `CONAN.EXE` too) and re-running the same search finds all three tables **byte-identical** to the Amiga corpus, zero transformation needed. **The entity-class bytecode VM (`entityClasses`, 34 classes) was initially declared unrecoverable this way for a *structural* reason — wrongly.** A later session overturned that verdict: the bytecode is a 16-bit-word stream, big-endian on Amiga (68k) vs little-endian on DOS VGA (x86); re-running the identical search with adjacent byte pairs pre-swapped found all 34 classes byte-exact and contiguous, independently triple-confirmed by a matching `_prgm`-equivalent far-pointer dispatch table (same 34-entry order on both platforms) and identical `disasm-bytecode.ts` output. See `vm-bytecode-embeds-platform-addresses.md` (corrected this session) for the full story and the general lesson: a disassembler's own address-shaped label naming for a sibling platform's dispatch table is not proof the *stored values* are non-portable machine addresses on the platform you're actually searching.

**A later session fully decoded the FSME entity-animation VM's instruction encoding** by tracing `_DoAnim`/`_DoFrmlScript`'s own fetch-decode loop directly (rather than pattern-guessing an opcode table from disassembled bytecode content, which is what left Spirit's own `docs/spirit/amiga/bytecode-vm.md` opcode survey unverified for years): every word is `(opIndex:4 << 12) | operand:12`, opIndex selecting one of 16 `_pFuncToDo` handlers confirmed by symbol name; `_Anim_Draw` (opIndex 0) encodes a literal frame index (bits 0-4) plus a tick delay (bits 5-11); `_Anim_Ctrl` (opIndex 6) is a full call/return/goto/class-switch instruction set with a real 5-deep per-object return stack, and the class's "64-byte dispatch header" is now known to be 32 raw `_Anim_Ctrl` words, not a separate pointer table. A reachability walker (`tools/vengeance/fsme-vm.ts`) demonstrates distinct, code-derived frame groupings per class entry point (worked example: `knight`/FRML id 700) — but **no caller was found anywhere that assigns a semantic name (idle/walk/attack/death) to an entry-slot index**, and cross-checking the traced `_OpenScene → _GetObject` calling convention (which struct offsets carry an entity's resource id/class/remap index) against the real `EPISODE*.DAT` corpus found the pose-set and remap fields are `0` for all 92 real entities and the resource-id field doesn't fit the confirmed FRML range under any bias tried — a solid instruction trace that doesn't generalize to real data, see the new `traced-calling-convention-unverified-against-corpus.md` lesson this sourced. Both open questions are tracked in `docs/vengeance/TODO.md`. A geometry-only classifier (reusing Warriors of Legend's `detectGeometricBoundaries`, see `sprite-frame-geometry-reveals-animation-segments.md`) gives full 55/55 FRML corpus coverage in the meantime, wired into the manifest pipeline at `confirmed`/`rendered`/`hypothesis` confidence exactly like Conan's and Legend's own equivalents. `tools/vengeance/fsme-vm.ts` is a strong candidate to promote to `tools/shared/` if Spirit (same VM, confirmed identical opcode set) ever needs the same reachability-walk analysis — flagged, not yet done.

**A follow-up session cracked exactly the naming problem the Vengeance paragraph above left open, for Spirit specifically** — not via a generic reachability walker, but by manually tracing each hero class's own bytecode word-by-word in program order and reading off the literal `_Anim_Draw` frame sequence a real execution path draws. This also corrected two mistakes in the pre-existing model: (1) `_Anim_Draw`'s two bit-fields had their roles **inverted** in `docs/spirit/amiga/bytecode-vm.md` for years ("bits 5-11 = frame, bits 0-4 = duration") — the reverse of the truth (bits 0-4 select the real FRML frame-table index, confirmed by tracing `_DoFrmlScript`'s frame-address arithmetic; bits 5-11 are a timing delay) — caught because decoding a real walk-cycle script under the old roles produced a static frame redrawn with only its "duration" field changing, which isn't a real animation; see the new `adjacent-subfield-roles-swapped-despite-correct-bit-boundaries.md` lesson this sourced. (2) The "64-byte dispatch table, separate from bytecode" model (also in Spirit's own docs, independently) is fully retired: `_GetObject`'s spawn-init code (`CLR.B 39(A0)`) proves a fresh object's PC starts at word 0 of the whole class, and the leading ~26-32 words are themselves ordinary executable `_Anim_Ctrl` goto trampolines, not a separate table — see the new `addresses-landing-in-reserved-region-means-wrong-boundary-model.md` lesson (several real goto targets landing inside the "reserved" region were the tell, not an anomaly to explain away) and `boring-resolved-call-can-be-a-real-noop.md` (a third finding this session: the entity's `iPoseSet` field is forwarded through an A4 jump-table stub that resolves to `_toupper` — a real, working no-op for every value in the actual corpus, 0-10, confirming `iPoseSet` **is** the `_prgm` class index directly, not just correlated with it). Result: confirmed walk-cycle frame ranges for all 10 hero/character FRML sprites, plus a full attack/death/guard breakdown for `knight` (`PLAYA32A.RES#700` — frames 0-5 walk, 6 idle, 7-13 attack, 14-16 death ending in a freeze-current-frame sentinel, 17-18 a 2-frame guard pose) and guard poses for `necromancer`/`enchantress`/`damsel`. See `docs/spirit/amiga/bytecode-vm.md` § "Animation-frame ranges — confirmed per character class (2026-08)", wired into the pipeline at `src/assets/formats/spirit-frml-animations.ts`.

**WIME DOS VGA's `START.EXE` (a different, Microsoft-EXEPACK-compressed executable of the same name from Conan's own LZEXE-rejected one two paragraphs up — don't conflate the two) hid a 196-entry entity table's real fixed 37-byte stride behind what looked, for two full sessions, like a genuine variable-length record format.** `NumRelocs == 0` plus the canonical `"Packed file is corrupt"` string plus an 18-byte EXEPACK header (signature word `0x4252`, "RB") 18 bytes past `CS:0000` confirm the packing; a `re-codebreaker` escalation cracked it by censusing the suspicious "residue" byte motif *file-wide* rather than just within the entity table, finding it recurring 107 times in code contexts where no entity data could exist. Unpacked, the entity table is a plain uniform stride, verified 4,624/4,624 fields exact against Amiga — see the new `packed-exe-mimics-variable-length-records.md` lesson this sourced, and `docs/wime/dosvga/exe-gameplay-data.md` / `docs/reference/eliminated/wime-dosvga-entity-frontsection.md` for the full story. New shared decoder: `src/assets/formats/exepack.ts` (`unexepack`/`isExepack`) — a good first place to look before hand-rolling another DOS packer detector in this family.

**WIME's Apple IIGS `PAMM` (in `FINAL1.RES`, a battle-scene file) turned out to be the same world terrain grid as Amiga's `AMaps.res` `MMAP`** — found via a byte-value histogram match (0x21 plains at 40.3% vs. Amiga's confirmed ~41%) before any dimension-guessing, then verified 99.7% cell-exact against Amiga's own rendered map (160 cols × 103 rows on IIGS vs. 101 on Amiga, grid-then-trailing-filler on both). See `cross-platform-decode-oracles.md`'s new histogram-oracle paragraph, sourced this session. The sibling `RAHC` (an IIGS `CHAR`-equivalent tileset) is genuinely blank — the entire 32,768-byte raw resource is the literal fill byte `0xAA` repeated, not a failed decode of real content.

**WIME Amiga's per-race 252-byte FRML animation bytecode table (`DATA+0x95E`,
already confirmed as an 8-way `extra`-dispatch VM in an earlier session) had
its remaining open question — semantic naming of ~9 entry-point constants —
resolved this session without live/amiberry verification or a further
escalation.** The key that unlocked it: `LAB_0345` (the FRML sprite object
constructor) writes the *exact same* value it opens the FRML resource by
into the render object's own raceVar field with no transformation — proving
the table's row index is the FRML resource id directly, not the 38-byte
gameplay entity's own `race` field (which can differ; this also caught and
corrected a real, years-old error in this doc's own "race → FRML resource"
table, which had wraiths at `race`=5 when the real value is 8). With that,
decoding all 16 races (not just the 2 a prior session sampled) at every
entry point cleanly separated idle(0)/walk(10)/attack(24)/death(84).
**Trusting the death-entry trace at face value was a real mistake, caught
only by a same-project independent oracle**: an ungated first pass produced
a wrong, huge, in-range frame span for orcs by wandering through unrelated
zero-filled table bytes before hitting a real terminator — caught by
cross-checking against troll, whose actual collapse frame this same
project's *pre-existing* geometry-based classifier had already confirmed by
rendering. See the new `bytecode-trace-in-range-result-can-still-be-noise.md`
lesson this sourced. New shared module:
`src/assets/formats/wime-frml-anim-vm.ts` (`traceWimeAnimRow`), wired as the
primary classification source in `classifyWimeFrmlAnimationsFromBytecode()`
ahead of the pre-existing geometry heuristic, which remains as a documented,
lower-confidence fallback both per-resource (Balrog, confirmed atypical —
its own `walk` entry point is an immediate `RET`) and per-segment (death,
for the several races whose table row has no trustworthy death content).
See `docs/wime/amiga/frml-colour-variants.md` § "Entry-point semantics —
confirmed".

**A follow-up session resolved 3 of 5 further ground-truth claims about this
same VM (turning, wraith/Balrog magic attack, pay-respect) and narrowed the
other 2 (sitting, sleep-reusing-death) with real new content but unconfirmed
triggers.** Row offset 230 (previously mislabeled "despawn/cleanup") is a
real turn entry point with genuine transitional frames for 8/16 races,
confirmed triggered (so far) only inside a duel-outcome resolution cutscene,
not ordinary movement. Wraiths and a Balrog were confirmed (via ground
truth) to have a coded magic attack distinct from their physical swing,
found by searching every race's already-known two-frame-family swing region
for a reserved bytecode opcode (a real targeting/effect-resolution routine)
instead of trusting the wizard-only frame-geometry check ("wider AND
taller") that had originally found the wizard's own spell-cast — see the new
`sprite-frame-geometry-reveals-animation-segments.md` addendum this sourced.
The already-known "shared post-outcome reaction block" (offsets 160/184)
was traced to a real duel-resolution reaction pose (a previously-
uncatalogued shared frame index), matching "pay respect", but its only
confirmed trigger reads as a general duel-outcome cutscene, not specifically
camp/conversation (sitting) — left genuinely open, since reusing one pose
across multiple "at ease" contexts is plausible but unproven. A death-reuse
"sleep" pose was found immediately after `death`'s own `RET` (same
structural shape as the confirmed segments) but no caller reaching it could
be found, the same "indirect command-queue dispatch, caller unidentified"
class of gap already flagged for the attack-swing region's own trigger. Also
this session: adding these three new fields to the classifier's existing
`isWimeAnimVmWellFormed()` gate broke an otherwise-correctly-classified
10-frame resource (one field draws a hardcoded frame index from the shared
table region, out of range for a shorter-than-usual resource) — caught only
by re-running the full manifest build, not by the unit test suite. See the
new `constant-valued-field-poisons-shared-wellformedness-gate.md` lesson
this sourced, and `docs/wime/amiga/frml-colour-variants.md` § "Pay-respect,
sitting, turning and sleep" for the full derivation.

**DOS VGA's own animation code was found and disassembled (2026-08-09
session), confirming the previously byte-matched copy of this same table is
genuinely read, not just present.** `START.EXE`'s render-object constructor
(unpacked-image offset `0x8612`, DOS's `LAB_0345`) and per-tick VM step
(`0xEA0E`, DOS's `LAB_07E1`/`LAB_082E`) are a field-for-field x86 port:
same table base (`DS+0x15E6` = unpacked offset `0x18D06`), same
race/stateVar render-object field offsets (`+9`/`+0xA`), same `extra`/`code`
opcode split, same `DELAY` formula (`clock + code*25 + rnd(code*25)`) and
`0xFFFF` HALT sentinel, same `JMPFAM` `code==0x1F` RET case — closing a gap
an earlier session had explicitly flagged as "byte-matched, not
disassembly-confirmed." Re-tracing the table (corrected entry-point names)
against real FRML frame geometry via an LCS alignment (not positional diff —
see the new `sprite-frame-geometry-reveals-animation-segments.md` point 6)
found DOS's "extra" hero-race frames are genuinely new content **inserted
mid-sequence** (an extra attack-swing variant + a conversation talk-gesture
pose for elves/men/dwarves/men-at-arms), not tail-appended as a prior
session's positional read of "man" had concluded — that prior conclusion
was wrong about *which* frames were new, though right that new content
existed. Wraith/Balrog's extra frames remain confirmed tail-appended and
unreferenced by any entry point, now via a real interpreter trace rather
than a byte-diff. See `docs/wime/dosvga/frml-extra-frames.md` and
`game-re-tooling/dos.md`'s new "Validating a medium-model executable's
far-pointer addressing model cheaply" section (the technique that made a
*scoped*, non-full-binary x86 disassembly pass cheap enough to do here).

**WIME's combat system is completely decoded AND reimplemented (2026-08)** —
resolver arithmetic (`docs/wime/amiga/game-logic.md` § Combat System: two
power pools, warded capacity/overflow, both casualty paths, the split
hp-damage model), presentation (`battle-screen-presentation.md`: slots,
army stacks, orders Charge/Engage/Withdraw/Retreat from the order-bar
string, 300/180-tick pacing, verbatim message cluster at file offsets
79450–80155, attended-vs-ignored sub-mode split), and a tested headless
port (`src/engine/BattleSystem.ts`) plus viewer battle sandbox/stage. The
resolver never reads `unitClass`/`morale`/`armor`; the Balrog 7-slot cap
is display-only. The Ring is donned mid-battle by a wounded surviving
bearer (attended battles only) and removed post-battle ("suddenly
reappears" — no wear limit); the undying (Nazgûl/Balrog *index ranges*)
are "driven from the field" in ignored-battle summaries.

**Spirit AND Vengeance combat + scene exploration are completely decoded
(2026-08 campaign)** — `docs/spirit/amiga/{game-logic,battle-screen-presentation,exploration}.md`
and the Vengeance twins. Key transferables: both share the 40-slot force
model, `_Reaction` grudge memory, duel champion-swap, click-gated army
rounds with a 36px front-line march gate — but the divergence catalogue is
the moral: Vengeance hits on threshold 40 vs Spirit's 50, **swaps the two
`dmgThreshold` field roles**, shifts the render-object struct +4 bytes,
and generalizes Spirit's one-off multi-door table into per-location
4-slot door arrays. Exploration: scenes are static backdrops with fixed
hotspots — no free in-scene movement exists. The A4-trampoline→symbol
resolver (see `game-re-method/finding-the-reader.md`) was decisive in all
five campaign runs; displacements never transfer between `Excal` and
`ExcalII`.

**WIME's Commodore 64 and Amstrad CPC releases are separate 8-bit games
(6502 / Z80), not `.res` ports — both substantially cracked in one 2026-08
push** (docs: `docs/wime/c64/engine.md`, `docs/wime/cpc/engine.md`;
extractors/renderers under `tools/wime/c64|cpc/`; open items as
`wime-c64-*`/`wime-cpc-*` rows in `docs/wime/TODO.md`). **C64:** NIBTools
raw-GCR dumps, custom sector headers over a bone-stock CBM filesystem (both
platform traps now in `game-re-tooling/c64.md`); the extractor's unhonoured
final-sector byte count masqueraded for two sessions as an RLE mystery —
sourced `extracted-file-sizes-all-multiples-of-block-payload.md`. PORT
portraits (20×25 cells, row-major) and BLOCK scene backdrops (10×8 cells,
column-major) are both the multicolor bitmap+screen+colour-RAM three-part
payload — the "unknown palette" never existed (sourced the attribute-RAM
bullet in `palette-storage-quirks.md`); portraits verified 33/33 against the
game's own TEXT name files. **CPC:** Extended DSK + "Laser Load" fastloader
whose five load-call argument sets are the entire disk map (verified by
rendering the title/victory screens raw at predicted addresses — big CPC art
is uncompressed screen dumps; don't assume the C64's RLE container
transfers); 168 8×8 mode-0 tiles stored serpentine, read off the game's own
blitter after a wrong 34×16×32 "confirmed" decode — sourced
`serpentine-row-order-mimics-mirrored-rows.md` and
`shared-prefixes-at-guessed-stride-fake-animation-frames.md`, plus
`game-re-tooling/cpc.md`. Both ports share the strategic-map grid
(102×130, ~92% cell agreement).

Sourced `header-shape-ambiguous-pixel-encoding.md`, `byte-scan-tag-byte-vs-wrong-stride.md`, `bitfield-spans-multiple-addressable-bytes.md`, `negative-from-addressing-root-not-shapes.md`, `seeded-prng-stable-not-random.md`, `runtime-only-value-often-static.md`, `audio-byte-order-measurable.md`, `optional-per-record-compression.md`, `partial-resolution-rate-is-noise.md`, `bitfield-residue-unread-past-cited-trace-window.md`, `rle-decode-succeeds-on-garbage.md`, `emulator-harness-pc-range-completion-defeated.md`, `text-field-periodic-interleave-byte.md`, `canned-save-state-mirrors-exe-struct.md`, `tile-grid-dimension-needs-render-not-just-bytecount.md`, `emulator-harness-input-boundary-not-algorithm.md`, `next-record-preview-defeats-stride-detection.md`, `port-reverses-whole-header-word-not-per-field.md`, `byte-value-collision-defeats-marker-only-guard.md`, `hand-computed-test-fixture-vs-real-run.md`, `producer-fix-inert-without-consumer-audit.md`, `adjacent-ramp-table-masks-off-by-one-record-start.md`, `pre-decompression-guard-uses-decompressed-threshold.md`, `cross-platform-string-delta-reveals-stride-vs-offset.md`, `vm-bytecode-embeds-platform-addresses.md`, `traced-calling-convention-unverified-against-corpus.md`, `packed-exe-mimics-variable-length-records.md`,
`undecoded-format-may-be-compressed-with-known-codec.md`, `bytecode-trace-in-range-result-can-still-be-noise.md`, `constant-valued-field-poisons-shared-wellformedness-gate.md`, `extracted-file-sizes-all-multiples-of-block-payload.md`, `serpentine-row-order-mimics-mirrored-rows.md`, `shared-prefixes-at-guessed-stride-fake-animation-frames.md`.

Docs are structured per game/platform under `docs/<game>/<platform>/`, with a strict convention worth copying: **format docs carry only confirmed information, and every eliminated theory is written up in `docs/reference/eliminated/`** so no search is ever repeated.

**This project now also has a `www/` Astro+Starlight static docs site** (a
third consumer of the same `public/assets/wime` pipeline output, alongside
the live engine and `tools/viewer/`) with its own gallery components
(`SpriteGallery.astro`, `FrmlVariantGallery.astro`, `FrmlCharacterGallery.astro`)
and its own asset-curation script (`www/scripts/build.mjs`, which mirrors a
curated subset of `public/assets/wime` into `www/public/` since CI never has
the original game files). A user's casual "the X page"/"our Y renders" may
mean this site rather than the live game or the offline viewer — see
`multiple-rendering-surfaces-same-data.md`, sourced here. Also confirmed:
this project runs with **multiple concurrent agent sessions committing to
the same working tree** (not separate worktrees) — expect `git log`/`git
status` taken at task start to be stale by the time you commit; see
`bare-git-commit-sweeps-concurrent-stage.md`.
