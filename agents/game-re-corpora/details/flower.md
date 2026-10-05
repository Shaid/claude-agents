# flower (`~/Development/flower`)

Games: **Drakengard 3** (PS3, unpacked disc dump primary + PSN digital
release for DLC), **Dragon's Crown** (PS3 + PS4, pkg files present, not
yet touched as of this writing), the earlier PS2 originals
**Drakengard** and **Drakengard 2** (first-pass recon done, see their own
section below — same developer, cross-game engine evidence gathered
together), and two unrelated Capcom PS2 titles, **Chaos Legion** and
**Devil May Cry** (first-pass recon done, see their own section below —
different developer/engine entirely from the Drakengard titles above, but
same console generation, so cross-game engine evidence was gathered
between the two of them the same way).

## Drakengard / Drakengard 2 (PS2)

Two direct-sequel PS2 titles by **Cavia Inc.** (published by Square
Enix; the PS3 Drakengard 3 above is a much later sequel by a different
studio, Access Games — no engine continuity expected or found between the
PS2 pair and the PS3 title). **Every major format is now confirmed and
decoded**: container, texture, mesh geometry (both the ordinary struct
encoding and a DG2-only PS2-VIF1-hardware-packet sub-format), skeleton,
animation, mesh↔texture material binding, and audio codec, all with
committed, tested shared decoders (`tools/shared/cavia-archive.ts`/
`cavia-wzim.ts`/`cavia-csfg.ts`/`cavia-csfg-vu1.ts`/`cavia-cjfg.ts`/
`cavia-cmff.ts`/`cavia-audio.ts`) as of a 2026-08 follow-up pass — see
below. (History: a 2026-08-07 first pass was recon-only; a 2026-08-08 pass
solved container/texture/mesh/audio; a later 2026-08-08 follow-up pass
solved skeleton/animation/materials/the VU1 mesh sub-format and, along the
way, found and fixed a real whole-corpus undercount affecting the
skeleton and animation formats — see below.) Both discs are the raw-LBA-
archive pattern the PS2 tooling notes warn about (`game-re-tooling/ps2.md`)
— ISO9660 only catalogs boot files + IOP modules + the main EE ELF; the
actual game data lives inside a handful of giant flat files (6 for
Drakengard, consolidated to 4 for Drakengard 2) via a proprietary
recursive container format, not as separate ISO9660 directory records.

**Confirmed: the container format, `fpk` (Drakengard) / `dpk` (Drakengard
2)** — a from-scratch, no-external-oracle reverse-engineering (WebSearch
quota was exhausted mid-session; no fan tool/QuickBMS script was found for
this format either). Pinned down by a byte-exact structural invariant
(`offset[i+1]-offset[i] == align_up(size[i], align)`, zero deviation
across every entry checked) rather than a disassembly trace or known-fan-
tool cross-check. `fpk`: magic + 128-byte header + flat 16-byte-entry
directory, recursively nestable (an entry's payload can itself be a
complete nested `fpk` container — confirmed 5 levels deep:
`image.bin`→`mmodel.bin`→`lodshp.bin`→`allpart.bin`→`allshp.bin`). `dpk`
(new in the 2005 sequel) wraps the same idea in a 32-byte hash-indexed
directory at the *outer* archive level only — inner/nested levels still
use plain `fpk` unmodified, and `dpk` can itself nest further `dpk` layers
too. Real evidence for what the `dpk` hash is *of*: a `sprintf`-style
`%s%s.dpk`/`sysres.dpk` path-construction string found in Drakengard 2's
executable. Full byte-level header/entry tables, verification method, and
the open items (hash algorithm untraced, one directory field's role
unresolved): `docs/drakengard-cavia-archive-format.md` (a shared doc, per
this project's own "container format shared by several games gets its own
doc" convention, referenced from both games' own specs).

**Confirmed, and genuinely useful for cross-game comparison: several
payload formats are byte-identical between the two games**, despite the
outer container format changing — strong evidence of a stable in-house
engine across the 2-year gap.

**Confirmed and decoded: `wZIM` textures** (`tools/shared/cavia-wzim.ts`).
Doesn't store a plain pixel-format struct — embeds a literal sequence of
real PS2 GS privileged-register write packets (`BITBLTBUF`/`TRXPOS`/
`TRXREG`/`TRXDIR`), located by scanning for the register-address byte
pattern rather than a fixed offset; see
`game-re-lessons/ps2-inhouse-texture-embeds-gs-register-packets.md` for the
general technique. Pixel data is linear/unswizzled; the 256-entry CLUT
needs the standard PS2 CSM1 index unswizzle. 130,378/130,464 (99.93%) of
Drakengard's full corpus (once `\0V3a`-compressed textures are included —
see below) and **12,348/12,348 (100%)** of Drakengard 2's decode cleanly —
verified visually (clean armor/hair/eye/cloth textures, and decisively a
real "PROJECT: DRAGONSPHERE" developer logo, the game's own working
title). Drakengard 2 adds a third, non-indexed direct-`PSMCT32` texture
shape absent from Drakengard 1. Drakengard 2's last 6 decode failures
turned out to be a register-group-scan bug (a coincidental byte match
inside a large pixel payload accepted as a real `BITBLTBUF` group, or a
multi-pixel-group particle-atlas shape the scanner's old "stop at exactly
2 groups" logic never looked past) — not the swizzle-variant bug it was
originally suspected to be; fixed by validating each candidate group's
`DPSM` against the format's known-real enum values and its declared
payload size against the remaining buffer, and by not hardcoding the
group-count stop condition.

**Confirmed and decoded: `CSFg` mesh geometry, both sub-formats**
(`tools/shared/cavia-csfg.ts` + `cavia-csfg-vu1.ts`) — positions, normals,
skin weights, UVs, triangle-strip topology, and world-space scale, cracked
via a `re-codebreaker` escalation after this project's own header-field-
stride and float-plausibility-scan approaches stalled.
**Drakengard 2's strip-header bit 15** (masking required to parse since it
was first found, semantics unresolved for a full session despite real
correlational evidence) turned out to be a backface-culling
reversed-winding flag, solved via a second escalation that reapplied this
same format's own already-validated face-vs-vertex-normal winding check
(see `game-re-method/verification-techniques.md`'s "Reapply an
already-validated technique" section) — gated by a *different*,
previously-"unresolved" sub-block `flags` bit (`0x400`) nobody had
connected to the strip question at all. The sibling `wZIM`
texture format's hardware-packet-embedding convention was a reasonable
first hypothesis for *ordinary* `CSFg` and was explicitly tested and
refuted there — see
`game-re-lessons/sibling-format-encoding-paradigm-not-transitive.md`. But
Drakengard 2 also has a genuinely distinct `CSFg`/`VU1` sub-format (tag
names starting `VU1`, ~2.4% of the DG2 corpus) that *does* embed literal
PS2 VIF1 DMA source chains (`STCYCL`/`UNPACK`/`FLUSH`/`MSCAL`, real
GIFtags forwarded to the GS) — solved via a second `re-codebreaker`
escalation, see that same lesson file's second-instance addendum for why
"ruled out for the format's main shape" doesn't transfer to every variant
sharing its magic. Triangle winding isn't stored at all in either
sub-format (derived from per-vertex normals instead, see
`game-re-lessons/vertex-normals-as-winding-topology-oracle.md`). 244/244
(100%) structural closure on Drakengard's corpus; whole characters render
as recognizable T-pose humanoids (glTF output, 0 Khronos validator
errors). On Drakengard 2, **12,938/12,938 (100%) whole-corpus closure**
(12,634 ordinary + 304 `VU1`, found via a real container-directory walk —
an earlier pass's raw magic-byte scan had found only 2,691 instances and
called 231 an unidentified sub-format, a ~4.8x undercount; see
`game-re-lessons/shallow-magic-scan-undercounts-sibling-magic-corpus.md`).

**Confirmed and decoded, byte-exact: PS-ADPCM audio**
(`tools/shared/cavia-audio.ts`) — the `"cavia stream format v1.01"` wrapper
+ `SShd`/`SSbd` Square-family chunk pair (`SShd` decodes directly to
44,100 Hz / 2-channel on BGM, 32,000 Hz / mono on voice, byte-for-byte
identical field layout in both games) wraps standard Sony PS-ADPCM.
Cracked via `vgmstream` prior art (its source has an explicit named parser
commenting "cavia games: Drakengard 1/2..." right at the magic check —
used only as an offline verification oracle, not a pipeline dependency).
Getting **byte-exact** agreement (0 sample deviations across 4 real files,
mono/stereo, looping/non-looping) needed matching the reference's exact
integer sequence, not just its formula — see
`game-re-lessons/byte-exact-adpcm-needs-exact-integer-sequence.md`.
995/995 (100%) of Drakengard's audio corpus and 1,900/1,900 (100%) of
Drakengard 2's decode successfully.

Mesh geometry (`CSFg` magic) and animation clips (`CMFf` magic) both carry
real embedded ASCII names readable straight out of the binary — mesh part
names like `CBASE`/`CWEAPON`-tagged `"nd5_hair3.basez_1_ZOFF1"`, and
animation clip names like `"COMBO01_KEN"` (剣/sword) — genuinely useful
for future per-character asset cataloging.

**Confirmed and decoded: `CJFg` skeleton/joint hierarchy**
(`tools/shared/cavia-cjfg.ts`) — joint names, parent hierarchy, world/
local bind positions, all in a plain little-endian struct (no hardware
packets). `CSFg`'s per-chunk bone-palette values were confirmed (by
regression against real rigidly-bound vertex clusters, not just index-
range plausibility) to be direct indices into this joint array — exact
left/right mirroring and exact head-to-toe ordering matching the joints'
own names, on two independently-shaped skeletons. **A real sibling magic,
`CJFd`** (same "last-byte variant" habit as `wZIM`'s `wZIMd`, but here a
completely different structure/decoder is *not* needed — byte-identical),
turned out to be far from rare: on Drakengard 1 it's 1 instance (Caim's
dragon companion's own skeleton — the "missing" 12th skeleton a shallow
`CJFg`-only scan couldn't find); on Drakengard 2 it's the *dominant*
skeleton magic, 524 of 528 total (a `CJFg`-only scan found just 4 — see
`game-re-lessons/shallow-magic-scan-undercounts-sibling-magic-corpus.md`
for the general lesson this produced). Whole-corpus: 12/12 (100%)
Drakengard 1, 528/528 (100%) Drakengard 2.

**Confirmed and decoded: `CMFf` animation clips**
(`tools/shared/cavia-cmff.ts`) — two parallel per-joint keyframe track
regions (a confirmed unit-quaternion rotation track, magnitude-verified
123,902/123,902 samples within 0.01% across a 200-clip sample; a second
3-component track structurally decoded but semantically unconfirmed).
Verified end-to-end with a from-scratch forward-kinematics pose render
(`CJFg` bind pose + `CMFf` per-frame rotation) producing visibly coherent,
non-jittery motion matching a clip's own name (a sword-combo clip: arm
swings, legs stay planted). Same sibling-magic story as `CJFg`: `CMFd` is
real and, on Drakengard 2, overwhelmingly dominant (4,233 of 4,251, vs.
18 `CMFf`). Whole-corpus: 1,241/1,241 (100%) Drakengard 1, 4,251/4,251
(100%) Drakengard 2.

**Confirmed: `CSFg` region-1 sub-block → `alltx.bin` texture binding** —
the per-sub-block `materialIndex` field (and a secondary "slot list"
field) are direct 0-based indices into the enclosing model's own texture
list, confirmed both structurally (769/769 whole-corpus index-validity)
and visually (a from-scratch textured render showing correct boots/
gauntlets/hair vs. a visibly-wrong control render using the wrong index).

**Confirmed via `ffprobe` (a real external oracle, not just a shape
match): `FACEUC.BIN` (Drakengard only) is standard MPEG-2 Program
Stream**, 96x128, no custom parsing needed at all — a close-up character-
portrait video overlay played during dialogue. Drakengard 2 has no
equivalent dedicated archive; whether the mechanic was dropped or merged
into the main movie archive is an open question
(`dod2-face-video-location` in `docs/drakengard2/TODO.md`).

**Confirmed, a real developer-debug-artifact find: Drakengard's per-movie
`mvNN.bin` containers hold a plaintext, Shift-JIS-commented CSV** of
subtitle frame/duration timing pairs, left in the shipped retail disc —
genuinely readable Japanese developer comments
(`# コメント表 は こんな 感じ で,,`). The actual subtitle *text* is in
neighboring same-container entries that are still compressed/unidentified
(`dod1-mvnn-subtitle-blob` in `docs/drakengard/TODO.md`) — the timing CSV
alone confirms where to keep looking, not the dialogue content itself.

**Solved (2026-08-08 pipeline-wiring pass): both games are real, registered
Seer games with a live, browsable asset pipeline** — `dod1-pipeline-not-
wired` is closed. `src/game-id.ts` now lists `drakengard`/`drakengard2`
(platform `ps2`) alongside `drakengard3`; `tools/shared/game-config.ts` and
`seer.config.ts` both carry real `GAME_CONFIGS` entries (`supported: true`);
each game has a real `buildAssets` step (`tools/drakengard/build-assets.ts`,
`tools/drakengard2/build-assets.ts`) built around a new shared pipeline
module, `tools/shared/cavia-pipeline.ts`. The concurrency-risk deferral from
earlier passes (another agent actively editing `tools/drakengard3/*`/
`tools/shared/ps3-pkg.ts`) no longer applies — re-checked via `git status`,
that work has settled.

The headline new work this pass wasn't registration — it was a
**from-scratch glTF 2.0 exporter** (`tools/shared/cavia-gltf.ts` +
`tools/shared/cavia-model.ts`, the latter grouping a flat container walk
into per-`mmodel.bin`-package structures via a purely path-structural key,
not a hardcoded slot-index assumption). Unlike Drakengard 3's PS3 pipeline,
there's no umodel/UE3 exporter to lean on for this engine, so mesh+skin+
baked-animation assembly (positions, normals, UVs, materials, `JOINTS_0`/
`WEIGHTS_0`, inverse bind matrices, baked `CMFf` rotation clips, a single
top-level coordinate-fix-up rotation node) is real new code, tested
(`tools/shared/__tests__/cavia-gltf.test.ts`, `cavia-model.test.ts`).

**Five real, generalizable bugs were found and fixed only by live browser
rendering, not by the Khronos glTF validator alone** — the validator stayed
"0 errors, 0 warnings" throughout even when the rendered character was
scattered across empty space and upside-down, because "well-formed glTF"
and "correctly posed" are different bars. In order of how much they
mattered visually: (1) mesh vertex positions were never divided by the
format's own `positionScale` while skeleton joint translations *were*,
putting every mesh part far from its own skeleton; (2) UV coordinates were
left in the format's native texel space (0..256 for a 256px texture)
instead of normalized to glTF's [0,1] range *per primitive* (different
sub-blocks of one part can reference differently-sized textures), which
looked like flat, undetailed grey despite `materialsTextured` correctly
reporting full resolution; (3) the engine's own coordinate convention has
"up" running toward *negative* Y (confirmed directly by dumping a real
skeleton's accumulated world joint positions — feet near the root at Y≈0,
head at Y≈-17), fixed with one proper 180°-about-X rotation on a synthetic
root wrapper node (not a bare Y-negation, which would silently invert every
triangle's winding); (4) a handful of real `CMFf` rotation samples are a
literal `(0,0,0,0)`, normalizing to an invalid zero-length quaternion; (5) a
real vertex normal at magnitude ~0.27 after the format's own fixed-point
conversion, not exactly unit-scaled. See
`docs/drakengard/ps2/data-structure.md` §10/§10.1 for the full byte-level
writeup of all five.

**Solved (2026-08-15 pass): `\0V3a`, an 81%-of-`IMAGE.BIN`-bytes compressed
leaf format that a prior session's plan had misattributed to a "297 total
`mmodel.bin` packages, only 12 reachable" framing.** That "297" figure was
simply wrong — no bug, just an unaudited/uncommitted probe from an earlier
session; a fresh recursive walk mirroring the real container-walking code
found the true uncompressed-portion count is **12**, already 100% covered.
The real missing content (readable fragments — `"mmodel"`, `"CJFg"`, a
literal byte-for-byte `fpk`-header-prefix match — found embedded in an
"unclassified leaf" bucket; see
`game-re-lessons/embedded-known-name-fragments-signal-compressed-sibling-content.md`)
was inside `\0V3a`: a proprietary 32-byte header wrapping a chain of
independent 262,144-byte **LZO1X** blocks (only the wrapper is custom, the
codec is stock LZO), solved via `re-codebreaker` and shipped as
`tools/shared/cavia-lz0.ts`. Both games use it byte-identically — 662/662
Drakengard 1 blobs and 1,225/1,225 Drakengard 2 blobs decompress
byte-exact. Wired transparently into `walkCaviaContainer`
(`tools/shared/cavia-archive.ts`) so every existing consumer (both games'
model/audio walkers) picks it up with zero per-caller changes — a shared-
code fix that benefits Drakengard 2's own pipeline automatically next time
it rebuilds. Also solved this pass: the `fpk` directory entry's "extra"
field (dual-purpose — a `\0V3a` blob's own decompressed size, confirmed
662/662 exact; or, in every non-`IMAGE.BIN` archive checked, a short
content-type tag, decisively reversed-ASCII for 3 of 4 archives against
real filenames already known from this game's own manifest text).

Real, whole-ISO pipeline numbers: Drakengard — **130,378 textures, 3,380
model packages** → glTF (918,091 verts, 980,565 tris, all 3,380 skinned,
1,040 with baked animation), 995 audio files, 135,745 manifest entries,
4.3 GB output (~20 min wall time — up from 1,046 textures/12
models/16,746 verts/~26s before `\0V3a` was wired in, a ~280x jump in
model coverage from one format crack). A random 15-glTF sample (spanning
both the original and newly-reachable character/prop names) passes the
Khronos validator with 0 errors each. Drakengard 2 — 11,117 textures,
**528 model packages** → glTF (716,082 verts, 869,285 tris, all 528
skinned, 310 with baked animation), 1,900 audio files (~100s wall time) —
**528/528 (100%)** of the skeleton corpus even before this pass's `\0V3a`
wiring reaches DG2's pipeline too (tracked as `dod2-v3a-textures-unwired`
in `docs/drakengard2/TODO.md` for its own texture corpus specifically; DG2
keeps most character/enemy packages directly at `D_IMAGE.BIN`'s top level
rather than nested inside compressed wrappers, unlike Drakengard 1). Live
Playwright verification on both games (pre-`\0V3a`, not re-run at the new
scale — the render logic is unchanged, only data volume grew): a real
character (`model_0000_CAIM` / `model_0024_EVENT_CAIM`) renders correctly
standing and fully textured; the baked sword-combo animation visibly plays
frame to frame (screenshot pixel-sampling showed real per-frame
differences, not a static image); real texture atlas browsing and real
`<audio>` playback (`currentTime` advancing) both confirmed; zero browser
console errors across both games.

Full findings, confidence-graded (confirmed/rendered/hypothesis) per the
project's own convention: `docs/drakengard/ps2/data-structure.md`,
`docs/drakengard2/ps2/data-structure.md`. Sequencing/status:
`docs/drakengard/plan.md`, `docs/drakengard2/plan.md`. Open items:
`docs/drakengard/TODO.md`, `docs/drakengard2/TODO.md` — what remains is
genuinely secondary: the compressed `mvNN.bin` subtitle-text blobs (ruled
out this pass as sharing `\0V3a`'s LZO1X codec — different header shape,
LZO1X fails at every offset tried — likely a separate custom scheme or
encryption), `CMFf`'s second per-joint track's semantics, DG2's
still-unidentified `kvm1.60` format (scoped — 75 instances via a full
walk, structured header, moderate entropy — but not decoded), `SPK0`
(10% of `IMAGE.BIN`'s bytes, a small container with a nested `DMT0` tag,
undecoded), wiring `\0V3a` into DG2's own texture pipeline
(`dod2-v3a-textures-unwired`), the `dpk` entry hash algorithm, and the
`fpk`/`dpk` magic-check code sites (untraceable via the radare2 MCP's
`search` tool in this environment — see `game-re-tooling/ps2.md`).

## Drakengard 3 (PS3)

Engine: **Unreal Engine 3**, internal codename `SQEX03GAME` (visible
throughout the shipped directory tree and dev-build manifest). Confirmed via
content inspection, not guessed — the `.XXX`-renamed files decode to
UE3's standard `PACKAGE_FILE_TAG` (`0x9E2A83C1`) chunk-compression wrapper,
`Coalesced.bin` (UE3's serialized-INI format) is present by name, and
`GLOBALPERSISTENTCOOKERDATA.UPK` is a raw (unwrapped) UE3 package.

**Two data sources exist — an unpacked PS3 disc dump
(`data/drakengard3/ps3disc/`) is the primary one**, not the PSN digital
pkg (`data/drakengard3/ps3/`). The disc ships all ~8,683 base-game asset
files as **plaintext** (no PKG container, no NPDRM at all) — only the DLC
(PSN-only, no disc equivalent) still needs the PKG/NPDRM route below. This
was a genuine pivot mid-session: substantial PKG/NPDRM decryption tooling
was built and confirmed *before* the disc dump was made available, and
remains fully correct/useful for DLC, but is no longer on the critical path
for base-game assets. If a future session sees only the PSN pkg (no disc
dump), the PKG/NPDRM route is the way in — check for a disc dump first.

This project's original ask ("aim high") includes a stretch goal beyond
asset extraction — a native recompiled PC port. See
`~/Development/seer/docs/ps3-recomp.md` for the landscape survey (Cell
BE/SPU difficulty, the `ps3recomp` prior-art project, RPCS3 as reference)
before assuming that's greenfield research; it isn't fully solved, but it
isn't unstarted either.

**Given the confirmed UE3 engine above, also read
`~/Development/seer/docs/engine-based-porting.md` before defaulting to the
Cell-BE-recompilation path** — it may be the higher-leverage stretch-goal
route for this specific title. Core idea: UE3 gameplay logic is commonly
written in UnrealScript, a portable VM bytecode interpreted by the engine
at runtime, not compiled PS3 machine code — meaning "rehost the recovered
assets/scripts on a real PC UE3/UDK build" could sidestep SPU-level
recompilation entirely for whatever fraction of the game's logic isn't
native C++.

**Checked, for real, this pass — the answer is yes, substantially.**
`umodel -list` (already vendored, no new tooling) against `SQEX03GAME.XXX`
(the game's own package, not `GAMEFRAMEWORK.XXX`/`ENGINE.XXX`, which turned
out to be 100% generic Epic stock UE3 script, 0% Drakengard-specific) shows
1,155 real `Class` exports, **1,150 of them (99.6%) `Sqex03`-prefixed
custom classes** — AI (`Sqex03AIManager`, `Sqex03GameAIController`), damage
(`Sqex03DmgType_Boss`, `Sqex03DmgType_DragonAttack`), targeting/combat
(`Sqex03GameHUDTargetGage`, `Sqex03Kismet_EventTakeDamage`), camera
(`Sqex03GameCamera`, `Sqex03Kismet_CameraLockon`), weapons
(`Sqex03AttachmentWeapon`, `Sqex03WeaponExchange`) — backed by 6,752 real
`Function` bytecode exports totaling 3,569,830 bytes of genuine executable
content (avg 529 bytes/function; one sampled AI function,
`Sqex03GameAIController::DrawDebugDetail`, alone is 5,678 bytes). A
contrast case (`SQEXSEAD.XXX`, licensed audio middleware) shows the
predicted opposite pattern — 12 `Class` exports, **0** `Function`/`State`
children, metadata-only stubs — confirming the classifier signal works in
both directions. Ordinary content packages (levels, UI) carry 0 local
script objects, as expected (they reference classes via Import, not
declare their own). **Real caveat found in the same pass**: `umodel`
itself cannot decompile the bytecode — `-dump`/`-export -uc` against a
`Function`/`Class` object confirms existence (right sizes, right names)
but produces no readable output (`Class`/`Function`/`State` aren't in its
"Supported resources for export" list at all). Full evidence, byte-exact
counts, and the exact reproducible `umodel` commands:
`docs/drakengard3/ps3/data-structure.md` §22.

**Checked, for real, the very next pass — yes, actual readable
UnrealScript source is recoverable, not just confirmable to exist.**
EliotVU/Unreal-Library (UELib) — the library UE Explorer itself is built
on, actively developed (targets `net10.0`), ships its own genuinely
cross-platform, GUI-free CLI project — decompiles `SQEX03GAME.XXX`'s
bytecode once two real, found-not-guessed fixes are applied: (1) UELib's
own `UnrealPackage.CookerPlatform` must be forced to `Console` before any
object deserializes, since its directory-name-based platform
auto-detection doesn't recognize `COOKEDPS3` and this game's packages
carry `LicenseeVersion=0` (no per-title `Build` table match either); (2)
native-function/operator names must be harvested from
`CORE.XXX`/`ENGINE.XXX`/`GAMEFRAMEWORK.XXX` and merged into
`SQEX03GAME.XXX`'s own `NTLPackage` *before* its first object
deserializes (a real ordering trap: `UByteCodeDecompiler`'s constructor
eagerly builds and permanently caches the native-token factory the first
time anything in a package is touched, not lazily at decompile time).
Both fixes live in a small, committed wrapper
(`tools/drakengard3/uelib-driver/`), not a patch to UELib itself (**a later
pass did need one real, deliberate, documented patch to the vendored UELib
source** — a hang-prone unbounded optional-header-array read, see the
Level/Map material-override paragraph below and
`game-re-lessons/vendored-parser-hang-needs-committed-source-patch.md`).
Real,
quantified full-corpus results, filtered to `SQEX03GAME.`'s own namespace
(matching §22's own umodel-derived counts exactly — 6,752 functions,
1,155 classes, byte-for-byte, via two independent parsers): **6,747/6,752
functions (99.93%) and 1,153/1,155 classes (99.83%) decompile to fully
clean, semantically correct UnrealScript source** — spot-checked functions'
logic genuinely matches their names (`GetEscapePoint` searches for the
nearest valid flee-to point; `GetDragonPawn` looks up the active dragon
pawn; a Kismet damage-trigger wrapper forwards to the real `TakeDamage`
event). The residual ~6 failures are narrow, well-isolated UELib
formatting bugs (a duplicated-switch tail-nest bug, an editor-only
`filtereditoronly` block, an inline-enum formatting bug) confirmed to
leave the surrounding real logic intact and readable — not
addressing/dataflow corruption. This directly unblocks
`engine-based-porting.md`'s "rehost recovered UnrealScript on a real PC
UE3/UDK build" path with real recovered source in hand. Full writeup,
verification methodology, and reproducible setup:
`docs/drakengard3/ps3/data-structure.md` §24.

**Solved, confirmed byte-exact:**
- The outer classic-retail-PS3-PKG container (not the Vita "finalized"
  variant — see `game-re-tooling/ps3.md` for why that distinction bit the
  first tool tried). Header layout, AES-128-CTR decrypt with the fixed
  public retail key, item table parsing. Needed for DLC only now.
- NPDRM `.EDAT` decryption using supplied RAP license files (RAP→klicensee
  transform + per-block AES-CBC, sourced from RPCS3's `Crypto/unedat.cpp`).
  Turned out to matter less than expected: in this game `.EDAT` is used
  **exclusively** for tiny DRM entitlement-check markers (a few hundred
  bytes, sometimes literally just the DLC's own id string as plaintext, or
  zero-byte payloads) — never for bulk asset content. An earlier pass of
  this doc/corpus wrongly assumed DLC bulk content was EDAT-wrapped
  (never actually checked past the first few filenames per DLC pkg) —
  corrected once actually decrypted. See
  `game-re-lessons/generic-bucket-hides-real-content.md`-adjacent lesson:
  a filename-suffix pattern (`.EDAT`) doesn't tell you the *size role* of
  what's inside without opening it.
- The UE3 "cooked seekfree" chunk-compression wrapper — **two real
  sub-formats**, not one (a later pass's correction: an earlier claim that
  one wrapper shape covered "every `.XXX`/`.TFC` file" was an overclaim from
  a sample that only ever included the 4 core/script packages). "Format A"
  (confirmed on `CORE.XXX`/`ENGINE.XXX`/`GAMEFRAMEWORK.XXX`/
  `SQEX03GAME.XXX`): the whole file, header included, is one contiguous
  tag + block table + per-block-zlib-stream wrapper, verified byte-exact
  against a `.UNCOMPRESSED_SIZE` sidecar with zero leftover bytes. "Format
  B" (confirmed on Level/Map packages and ordinary content packages —
  most of the corpus): UE3's own `FPackageFileSummary` header is stored
  *plain*, only the remaining data is split into a `CompressedChunks`
  array embedded in the header, each chunk itself shaped like a format-A
  entry — derived byte-exact from UEViewer's own C++ reference source, not
  guessed, and only discovered because a *second* consumer (UELib, which
  needs raw flat bytes) needed the same files umodel had already been
  handling transparently. Full derivation: `docs/drakengard3/ps3/
  data-structure.md` §27, and `game-re-lessons/single-working-consumer-hides-second-container-subformat.md`.
  `.TFC` texture caches are a *sequence* of format-A entries (one per
  streamed texture mip), not one wrapper for the whole file — confirmed on
  a 364MB real `.TFC`, framing only, pixel data still open.

Full writeup with byte tables and verification evidence:
`docs/drakengard3/ps3/data-structure.md`. Reusable, tested code:
`tools/shared/ps3-pkg.ts` + `tools/shared/ps3-edat.ts` (deliberately not
Drakengard-specific — applies to any `ps3` target in this project, including
Dragon's Crown's pkg once that's picked up).

**Solved: UE3's own package format (`FPackageFileSummary` + Name/Import/
Export tables), by shelling out to Gildor's UModel/UEViewer (`umodel`)
rather than hand-writing a native parser** — a deliberate architecture
decision, not a stall; see `docs/drakengard3/ps3/data-structure.md` §8 for
the full reasoning and `game-re-lessons/legacy-32bit-binary-missing-
shared-lib.md` / `wildcard-batch-tool-aborts-on-first-bad-file.md` for the
two operational traps that cost real time getting there. `umodel` parses
every SQEX03 `.XXX`/`.upk` package tried with **zero Drakengard-specific
config** — no `-game=` tag, no pre-decompression, no renaming — pointed
directly at `COOKEDPS3/` with the disc dump's native filenames. Wired into
the real pipeline (`tools/drakengard3/setup-umodel.sh` vendors the tool;
`tools/shared/umodel.ts` + `tools/drakengard3/build-assets.ts` do the
export + promote-to-`public/assets/` work; `seer.config.ts` /
`tools/shared/game-config.ts` both flipped to `supported: true`). A
full-corpus run (all 3,238 `COOKEDPS3/` packages) produced 61,244 real,
visually-verified `Texture2D`/`LightMapTexture2D` PNGs — 2,522/3,238
packages exported successfully; of the 716 "failures," 715 are confirmed
all-zero cut-content stub files (see
`game-re-lessons/all-zero-stub-file-inflates-failure-count.md`), leaving
exactly 1 genuine unexplained decode error (`BG41_SND_20_SOUND.XXX`,
`dod3-bg41-snd-zlib` in TODO.md). Texture pixel format is `PF_DXT1`,
confirmed via umodel's own `-dump` introspection. A **native**, dependency-
free byte-level parser for the Name/Import/Export tables remains genuinely
open (`dod3-upk-native-parser` in TODO.md, deferred not blocking) — the
header contains a second, nested §2-style zlib-compressed sub-block whose
internal offset-addressing scheme wasn't fully cracked by hand; full
paths-tried table in data-structure.md §8.

**Solved: mesh (`StaticMesh3`/`SkeletalMesh3`) → glTF 2.0**, via
umodel's own `-gltf` export flag for geometry/skin (**not** animation — see
below, corrected from an earlier pass's wrong claim here) — a real,
independent code path in umodel, not a rename of its ActorX `.psk`
exporter — plus a from-scratch post-processing step for materials/textures
— umodel's `-gltf` mode never embeds textures on its own (confirmed by
reading `Exporters/ExportGLTF.cpp`), so `tools/shared/gltf-patch.ts` +
`tools/drakengard3/mesh-assets.ts` cross-reference the glTF material
`name` against the `.mat` sidecar text files umodel's *plain* export
already produces (`Diffuse=<TextureName>` etc.) and resolve those against
the already-promoted texture manifest. Full-corpus run: 15,957 meshes
promoted (1.5GB), 0 umodel decode failures. Material/texture linkage rate
is real and quantified, not a bug when it's not 100%: 99%+ for
`SkeletalMesh3` (characters/weapons carry their own material array) vs.
originally ~10% for `StaticMesh3` (most environment kit pieces get their
material assigned per-instance in Level/Map actor-placement data — see
below, **later resolved to 76%/82.6%**). Also surfaced and fixed a real,
generalizable Node.js concurrency bug along the way (see
`game-re-lessons/blocking-execfilesync-defeats-promise-all-pool.md`) and
used the Khronos glTF validator (`npx @gltf-transform/cli validate`, zero
new dependency) as a free structural oracle. Full writeup:
`docs/drakengard3/ps3/data-structure.md` §10.

**Solved (later pass): Level/Map `StaticMeshComponent.Materials[]`
per-instance material overrides**, closing the gap the paragraph above
left open. The core insight: the generic UE3 tagged-property machinery
(`UDefaultProperty`/`DeserializeProperties()`) UELib's §24 UnrealScript
work already proved for `Class` `defaultproperties` blocks is **not
script-specific** — `UObject.Deserialize()` calls it for *any* object with
a class index, and `UObject`'s own base `Decompile()` gives a generic
per-object property dump for a placed `Actor`'s `StaticMeshComponent`
subobject too. No new property parser was needed — the real work was two
gaps: (1) Level/Map packages use the second on-disk chunk-compression
sub-format above ("format B"), needing byte-exact derivation from
UEViewer's own C++ source before UELib could read them at all; (2) UELib's
`ArrayProperty` element-type inference fails when the owning class
(`Engine.StaticMeshComponent`) is only imported, not loaded — fixed via
`UnrealConfig.VariableTypes`, an override hook UELib ships for exactly
this. A third, real robustness bug in UELib itself (not this game's
format) was also found and fixed with a deliberate, version-controlled,
idempotently-applied patch to the vendored source — see
`game-re-lessons/vendored-parser-hang-needs-committed-source-patch.md`.
Real full-corpus result: `StaticMesh3` mesh-level linkage rose from 12.9%
to **76.0%**, material-slot linkage from 10.3% to **82.6%** (1,881/1,898
Level packages scanned, 42,329 real placements found, 9,418 meshes gained
real texture coverage they had zero of before) — verified structurally
(referenced texture files confirmed present on disk) and visually (live
Playwright browser verification, three previously all-placeholder-material
meshes rendering with real, correct textures, 0 console errors). A real,
quantified 24% residual remains (open, not chased to zero — every
remaining mesh has a real `Materials` array, just none of its real
placements were found in the scanned corpus). Also surfaced: UE3 "cooked
seekfree" `Type'Package.Group.Name'` object-reference syntax does **not**
reliably name a separate file — `Package` is often just a synthetic
pre-cook namespace label for an asset inlined into the *referencing* file
itself, confirmed by `umodel -list` showing the referenced object as a
real export in the same package. Full writeup, byte-level format
derivation, and verification evidence: `docs/drakengard3/ps3/
data-structure.md` §27. Closes `dod3-mesh-material-level-overrides`.

**Solved: skeletal animation (`AnimSet`/`.psa`) → glTF `animations[]`**,
via a from-scratch `.psa` decoder — umodel's own `-gltf` CLI export cannot
embed animation at all (a deliberate, source-confirmed umodel limitation,
see `game-re-tooling/unreal-engine3-umodel.md`), so this decodes the
`.psa` (ActorX) files umodel's plain export pass already produces for
every `AnimSet` (1,397 files, zero new umodel invocations) and re-derives
the coordinate transform + bone-name-overlap AnimSet↔mesh matching umodel's
own (CLI-unreachable) animation exporter would have used. Real, wired-in
pipeline step + three.js `AnimationMixer` viewer playback, verified
end-to-end (byte-exact `.psa` parser, 0 new glTF-validator issues, real
quantified bone motion, live Playwright browser verification with 5/5
consecutive playback frames differing). Scoped deliberately this pass (16
of 1,054 `SkeletalMesh3` assets actually decoded+injected; the rest have a
cheap bone-match recorded for a future full-corpus pass). Full writeup:
`docs/drakengard3/ps3/data-structure.md` §13.

**Solved: Square Enix `.SCD` sound container → web-native `.mp3`/`.wav`**,
via a from-scratch, dependency-free TypeScript parser
(`tools/shared/scd.ts`) — not Drakengard-specific, SCD is used across the
whole SE catalog (FFXIII/XIV/XV, Type-0, Kingdom Hearts, Dragon Quest X).
**umodel has zero applicability to this format** — confirmed both by
reading its source (its `USoundNodeWave`/`CompressedPS3Data` handling is
for audio embedded *inline inside a UE3 package object*, a different,
simpler scheme, and irrelevant regardless since SCD files aren't UE3
packages at all — no `PACKAGE_FILE_TAG`) and empirically (`umodel -export`
against a real SCD file fails immediately with `Wrong package tag`).
`vgmstream` has real, working prior art for SCD (`src/meta/sqex_scd.c`,
explicitly names this game's own codecs in its source comments) and was
used as an **offline verification oracle only**, not wired into the
pipeline — cross-checking it surfaced a genuinely tricky, load-bearing
gotcha (`vgmstream-cli` silently falls back to a generic auto-probe and
gives wrong/failing results unless fed the file renamed to a literal
`.scd` extension — see
`game-re-lessons/multiformat-cli-silent-extension-fallback.md`, a new
lesson from this pass). 1,793/1,793 real SCD files on the disc dump decode
with 0 failures (1,790 MPEG/MP3, byte-for-byte passthrough, no
re-encoding; 3 PCM16BE, byte-exact against vgmstream's own decode). Wired
into both the pipeline and the viewer (`<audio controls>`, verified live
via headless-Chromium Playwright: real playback with `currentTime`
advancing, browser-native decode duration matching this pipeline's own
computed value). Full writeup: `docs/drakengard3/ps3/data-structure.md`
§14.

**Still open**: 1 of the original 10 `boss_font_*` boss names (Armisael)
remains unlinked to a mesh cluster, narrowed from 4 by a later pass that
mined the §24 UnrealScript decompile itself for a real, developer-authored
`Sqex03GameModel_Bs<NN>_<BossName>` class registry and followed its
`defaultproperties` object-reference chains to the actual mesh packages —
closed Gabriel and Zophiel (confirmed) and Phanuel (inferred); Armisael
reached a second, independent negative via the same technique (its own
referenced data packages have zero `SkeletalMesh3`/visual-asset content at
all). See `game-re-lessons/script-corpus-defaultproperties-reference-
chain.md` for the generalizable technique and its numbering-coincidence
trap. Tracked in `docs/drakengard3/TODO.md`.

**Solved: `Coalesced.bin`** (UE3 serialized-INI, `tools/shared/coalesced.ts`)
— byte-exact across all 4 real variants (main+patch × 2 languages), but a
real, verified negative: purely generic UE3 engine/editor config, zero
character/dialogue text for this game. **Solved: character display-name
aliases** for the §18/§19 character-identity clusters instead, sourced from
the game's own asset-name corpus (a `boss_font_<name>_en/jp` title-card
texture convention, 10 names exhaustively enumerated; descriptive package-
name substrings) plus one external+structural identification — see
`game-re-lessons/asset-name-string-mining-beats-empty-localization-table.md`
for the generalizable technique and its exact-match-correlation nuance.
14/124 clusters named (166 manifest entries) as of that pass; a later pass
mining decompiled UnrealScript (see "Still open" above) plus DLC-extended
clustering brought this to 26/135 clusters named (220 manifest entries,
`data-structure.md` §25) — wired into the viewer's search + list UI. Also
fixed a real dev-server environment blocker (see
`game-re-lessons/file-linked-local-package-needs-build-before-dev-server.md`)
and a real discoverability bug (aliased entries' package-derived category
didn't match where a character search would look — fixed by force-
reassigning `category` on any aliased entry). Full writeup: `docs/
drakengard3/ps3/data-structure.md` §20-21, §25.

**Solved: offline-viewer scale-up** for the ~79,000-entry combined
manifest (texture+mesh+audio) — real category taxonomy (9 categories
derived from an actual frequency analysis of all 78,956 names, not the
"obvious prefix" guess alone — `tools/drakengard3/asset-taxonomy.ts`),
category-based lazy manifest loading + a further group-level sub-shard for
the one dominant category (91% of the corpus) that's still too big after
one split (`tools/shared/manifest-sharding.ts` — zero game-specific
logic, written to be liftable into `@seer-project/pipeline` later), and list
virtualization in the viewer itself (fixes DOM cost independent of the
sharding). Measured, not estimated: 2,740ms→194ms page load,
78,956→99 initial DOM nodes, 0 fetch of the 21MB flat manifest on load.
Framework decision (local, not `@seer-project/pipeline`, yet — no proven second
consumer at this scale) documented in `docs/drakengard3/ps3/
data-structure.md` §16, alongside a real CSS layout bug the Playwright
verification pass caught (see `game-re-lessons/
manifest-scale-needs-lazy-category-load-plus-virtualization.md` and
`unconstrained-nav-element-starves-flex-scrollable-list.md`).

**Solved: full-corpus character-identity dedup + moveset merge.** UE3's
seekfree cooking (§8) bundles a scene-local copy of a character mesh per
cutscene, each with only that scene's animations. A Zero-only proof of
concept (60/63 scene-local copies byte-identical, a moveset merge via
`findAllAnimSetMatches()`) was generalized to the whole 1,054-mesh
`SkeletalMesh3` corpus using a *structural* signature (a hash of each
mesh's sorted joint-name set for "same character," a hash of its geometry
buffer for "byte-identical duplicate") instead of any hardcoded name
list or filename convention — real full run: 124 character clusters
found, 751 canonical viewer entries after collapsing 303 duplicates, 44
clusters (196 meshes, 4,373 clips) got a real merged moveset, Playwright-
verified on 4 characters including 3 beyond Zero. Also generalized the
by-eye "clean natural gap" ratio-threshold picking (§17's own technique)
into an algorithm, and caught + fixed a real content-signature
idempotency bug along the way (see `content-signature-source-must-
predate-pipeline-mutation.md` and `deepest-qualifying-gap-not-largest-
gap.md` in the pitfalls index). See
`docs/drakengard3/ps3/data-structure.md` §18.

**Solved: audit of the 80 declined moveset-merge clusters from §18** — not
a scope extension, a decision-boundary audit of every cluster §18 declined,
using real corpus evidence (actual ratio distributions, actual AnimSet
object names) rather than loosened thresholds. Found and fixed two real,
generalizable bugs: (1) a second instance of the "largest gap vs. deepest
qualifying gap" algorithmic blind spot — `findNaturalGapThreshold` never
considered a gap when only *one* distinct ratio value cleared the
confidence floor, even when that single value had an enormous, obvious
drop-off just below it (9/16 "no-confident-gap" clusters, including a
56-joint 3-headed creature with a dedicated 63-sequence AnimSet the old
code couldn't see); (2) a real secondary structural signal — UE3's own
package/object naming convention (`AS_<scene>_<character-id>`,
`ANIM_<id>_SF/<id>`) reliably disambiguates cases where bone-overlap ratio
alone is provably insufficient (18/18 "aliasing" clusters were all tied
between Zero's own general moveset and an unrelated boss's AnimSet at the
*identical* ratio, since both share the same 172-bone base rig) — a
longest-common-substring match against every candidate's own object name,
sorted by match ratio (not sequence count, which would let a richer but
less-precise same-family match crowd out the real one). Net: 32/80
clusters rescued (76/124 total merged, up from 44), 48/80 confirmed
correctly declined with real per-cluster reasoning (mostly legitimate
props/simple mechanisms; one narrow, verified exception — sub-rig
fragments of a multi-part boss encounter — found but deliberately not
pursued because a structurally identical false-positive case exists one
joint-count away and no available signal distinguishes them). Also found
and fixed a real, independent idempotency bug via the act of re-verifying
twice in the same session: the clip-injection loop capped only *new*
clips added per run, not a mesh's *total* clip budget, so re-running the
pipeline kept growing clip counts without bound (confirmed: some real
canonical meshes reached 75 clips against a 25 budget) — fixed, and a new
general-purpose `truncateGltfAnimations()` utility (`tools/shared/
psa-gltf-anim.ts`, the byte-exact inverse of repeated animation injection)
was used to repair the ~217 real meshes already over-inflated before the
fix landed. Playwright-verified live on 2 new characters (one per rescue
mechanism). See `docs/drakengard3/ps3/data-structure.md` §19.

**Solved: DLC extraction — all 19 PSN packs, full pipeline.** Extended the
§1/§2/§6 PKG/EDAT decryption (previously only listed/spot-checked, never
run end-to-end against real DLC) plus the umodel/SCD asset pipeline
(previously base-game-only) to `data/drakengard3/ps3/ALL DLC/*.pkg` — 19
files (6 scenario, 10 weapon/costume, 3 song packs; one file has a
misleading `v1.01`-suggesting filename but is a normal `ADDSCENARIO00001`
pack, not a patch or duplicate). Real numbers: 19/19 pkgs RAP-verified
(decrypting each DLC's own entitlement marker to its expected
self-referential id string, not just "a same-named `.rap` exists"),
970/970 umodel package exports ok, 43,487 new textures, 5,307 new meshes,
1,799/1,799 real audio files decoded, `manifest.json` 78,956 → 129,549
entries, 0 decode failures. Confirmed real, per the project's own ask: the
"weapon/costume" DLC packs are alternate-costume rig variants for Zero and
her dragon Mikhail (not new characters) and correctly cluster with the
base game's existing character-identity clusters via the existing
structural `boneSignature` system (`character-dedup.ts`, unmodified) — no
parallel DLC-only character list needed. DLC's own SCD audio turned out
**not** to need the §2 chunk-compression unwrap the open TODO item
theorized — every SCD source in this game (disc dump, main-game PSN pkg,
and now all 19 DLC packs) ships unwrapped. Also found and fixed two real,
generalizable pipeline bugs discovered only by running the DLC pass for
real: a manifest-merge correctness bug (see
`content-addressed-manifest-merge-needs-source-precedence.md`) and a
subprocess-export-output crash (see
`subprocess-export-leaves-truncated-output-file.md`). Live
Playwright-verified on 5 real DLC assets spanning all 3 pack kinds. Full
writeup: `docs/drakengard3/ps3/data-structure.md` §23.

**Solved: Level/Map placement transforms → real assembled 3D scenes.** The
natural next step after the material-overrides pass above, which read only
a placement's `Materials[]` override, not its spatial transform. Extended
`uelib-driver`'s existing `dump-static-mesh-components` mode to also read
each placement's real `Location`/`Rotation`/`DrawScale3D` (Actor) or
`Translation`/`Rotation`/`Scale3D` (Component) fields — real corpus data
confirmed exactly one of these two "legs" carries the real transform per
placement (an ordinary placed `StaticMeshActor` on the Actor; a
`StaticMeshCollectionActor`'s batched sub-components on the Component), never
both. New `tools/shared/ue3-transform.ts` converts `FRotator`→quaternion by
transcribing umodel's own `RotatorToAxis`/`Euler2Vecs` source, with two
numerically-verified subtleties (basis vectors are matrix columns not rows;
the UE3→glTF rotation conversion needs the same "root bone" parity fix
`psa.ts` already uses for skeleton root bones, not a plain Y/Z swap) — see
`game-re-tooling/unreal-engine3-umodel.md` for the generalized version of
this finding. Built a real, standalone scene-assembly pipeline
(`tools/drakengard3/build-scene-assets.ts`) over a representative 5-Level-
package sample: 3,142/3,143 real placements (99.97%) resolved to real
promoted mesh assets — the one exclusion a genuine corpus outlier (a
placement with a real, verbatim `DrawScale3D` of `(26, 4293, 7702)`,
almost certainly a disabled/debug placeholder actor) caught by a new,
real-data-derived `MAX_SANE_SCALE_AXIS` sanity filter (see
`game-re-lessons/single-outlier-defeats-bbox-camera-fit.md` — the same
outlier initially defeated the viewer's bounding-box camera-fit,
misleadingly making a correct decode look broken). Architecture: a small
JSON placement manifest (`{mesh, translation, rotation, scale}[]`)
referencing already-promoted per-mesh glTF assets unmodified, not a merged
glTF — avoids duplicating geometry for a Level's heavily-reused "kit"
meshes (confirmed: 1,089 real placements in one level resolve to only 76
distinct mesh assets). New viewer "scene" mode (three.js, sharing viewport
setup with the existing single-mesh viewer via a `createThreeViewport()`
extraction) — live Playwright-verified: two different assembled levels
render as recognizable, physically coherent rock/mountain-terrain clusters
with real textures, not piles of meshes at the origin, 0 console errors.
Full-corpus scaling (5 of 1,898 Level packages done) deliberately scoped as
a separate follow-up. Full writeup: `docs/drakengard3/ps3/data-structure.md`
§28.

Sequencing/status: `docs/drakengard3/plan.md`.

## NieR (2010, PS3)

Developed by **Cavia** — same studio as the PS2 Drakengard/Drakengard 2
pair above, but a genuinely different, much later console generation, and
**not the same engine as this project's other PS3 title, Drakengard 3**.
First-pass reconnaissance only (2026-08-09 pass), scoped to
`data/nier/ps3/` (PC and NieR:Automata — a different, unrelated
PlatinumGames/UE4 title — are explicitly out of scope for this project).

**Confirmed: NOT Unreal Engine 3**, despite the shared developer and same
console generation prompting that as the natural first hypothesis. A full
6,287-file directory walk (once the container was cracked, see below)
found zero `.upk`/`.XXX`/`.TFC` files and zero `PACKAGE_FILE_TAG` magic
anywhere — Drakengard 3's `umodel`/`uelib-driver`/UE3-specific tooling has
no applicability here. NieR predates Access Games' UE3-based Drakengard 3
by three years and was made by a different studio; the PS2-era Cavia
engine continuity (fpk/dpk/wZIM/CSFg) doesn't carry forward to this PS3
title either — this is a third, independent format family within the
project.

**Confirmed: a genuinely different top-level packaging strategy than
Drakengard 3's disc dump.** No `.pkg` files and no `EBOOT.BIN` exist
anywhere in this data set (the latter a real gap in this particular dump,
not a property of the retail disc). The entire base game's asset data is
one single 4.1GB NPDRM-wrapped file, `STABLE.SDAT` — not thousands of
individually-named plaintext files.

**Confirmed and extended: PS3 NPDRM `.SDAT`** (`NPD.license === 0`, no RAP
needed — a klicensee derived as `dev_hash XOR SDAT_KEY`, a second fixed
public constant distinct from the PKG layer's own fixed key) — a genuinely
new path added to the shared `tools/shared/ps3-edat.ts` module
(`decryptSdat()`/`sdatDevKey()`), which previously only handled RAP-based
`.EDAT`. **A real bug was found and fixed in the existing module along the
way**: RPCS3's real ERK-unwrap key selector is `NPD.version === 4 ?
EDAT_KEY_1 : EDAT_KEY_0`, not a hardcoded `EDAT_KEY_1` — silently correct
for every Drakengard 3 file (all version 4) but wrong for NieR's version
2/3 files, producing uniform high-entropy garbage rather than an error
(closely mimicking an undiscovered second crypto layer — see
`game-re-lessons/named-field-base-offset-mimics-second-crypto-layer.md`
and the sibling `format-field-width-unexercised-by-first-corpus.md`
addendum for the two distinct bugs this pass's "garbage output" chased
down before finding the real causes). Drakengard 3's own byte-exact
behavior is unaffected (regression-tested). Verified byte-exact against a
real `ICON0.PNG` entry's PNG signature and multiple `CRILAYLA` magic
matches, not just plausible structure.

**Confirmed and new: CRI Middleware's `CPK` archive + `@UTF` binary table
format** — a standard, publicly-documented third-party format (not Cavia-
specific), derived from a real reference implementation (vgmstream's
`cri_utf.c`) rather than guessed. New shared, reusable module:
`tools/shared/cri-cpk.ts` (unit-tested against synthetic fixtures,
`tools/shared/__tests__/cri-cpk.test.ts`). CRI Middleware is used
industry-wide across many Japanese console titles from the mid-2000s on —
worth checking for on any future project's PS2/PS3/PSP/Vita-era target
before re-deriving a `CPK`/`@UTF`/`CRILAYLA` decoder from scratch. Found a
genuine trap along the way, not a hypothetical one: a `Toc` row's
`FileOffset` field name suggests it's relative to the header's own
`ContentOffset`, but the real convention is `fileOffsetBase = TocOffset if
TocOffset >= 0x800 else ContentOffset` — using the wrong base produced
uniform garbage across every sampled content file, initially indistinguishable
from a genuine second encryption layer (see the new lesson file above).

**Real content survey (no extraction pipeline yet)**: 6,287 files, 22
top-level categories (`EVENT` dominates at 56%, mostly per-scene cutscene/
dialogue staging data), 34 extensions. Most payloads are CRI's own
`CRILAYLA` codec (public, undecoded by this project so far); a few are
custom Cavia container magics (`EMT`/`"EVMT"`, `"KPKy"`, `"ASDi"` — all
undecoded); a few are directly readable (localized `.CAP` subtitle text,
Shift-JIS `.TXT` credits).

**Blocked, correctly, not worked around**: the one DLC pack (`DLC01`,
`.EDAT`-wrapped, no `.pkg` at all unlike Drakengard 3's DLC) is
RAP-required (`NPD.license === 2`) and no `.rap` file exists anywhere in
this data set — a genuine missing-input blocker per the mission's autonomy
contract, not chased further.

**Update (2026-08-12 pass, `CRILAYLA` cracked and a real shipped pipeline
since the recon above was written)**: `CRILAYLA` is a standard CRI codec,
now fully decoded (`tools/shared/crilayla.ts`, corpus-wide byte-exact
verified, 1,679/1,679 entries). The three nested `AUDIO/NIER_*.CPK`
archives (BGM/English voice/English movie-audio-mix) are fully decoded and
shipped as a real MP3 pipeline, 4,501/4,501 clips, 0 failures
(`tools/nier/audio-assets.ts`, `tools/shared/cri-aax.ts`). **The game is
now registered** (`id: 'nier'`, `platform: 'ps3'`). `KPKy` (recursive
container), `MTMI`/`sall`/`CTFd`/`CPF*` (inner CRILAYLA magics) have
confirmed structural shapes but not full field-level decodes. **A focused
pre-rendered-video/FMV search this pass reached a definitive, evidenced
negative**: no CRI Sofdec/USM, Bink, ASF, or RIFF/AVI video container
exists anywhere in the decrypted base game — confirmed via four
independent full-corpus-coverage angles (size-outlier hunt, exhaustive
full-content magic-byte scan, `KPKy` leaf-name census, and a full `EVENT/`
subtree structural survey showing every cutscene is real-time in-engine
staging data, not monolithic video files — see
`content-type-absence-needs-multiple-independent-angles.md` for the
reusable technique). The negative is narrowly scoped: `EBOOT.BIN` (absent
from this dump) and the still-RAP-blocked `DLC01.EDAT` are the only two
unexamined pockets where video could still exist. A future session
shouldn't re-run this search from scratch — see
`docs/nier/ps3/data-structure.md` §10 before starting.

Full writeup, byte tables, and the paths-tried table for the still-open
custom Cavia formats: `docs/nier/ps3/data-structure.md`. Sequencing:
`docs/nier/plan.md`. Open items: `docs/nier/TODO.md`.

**Update (2026-08-16 pass)**: two real structural cracks, plus an X360
cross-verify closed. `.MDP`'s `"lzo\0"`-tagged wrapper's "probably plain
LZO1x" hunch was believed **refuted** by a decisive-looking control test (a
terminator-seeking decode variant's natural stop position was start-
offset-independent) — **this verdict was itself wrong, see the 2026-09-09
update below; the control test's blind spot is now documented in
`lzo-style-decode-start-offset-independence-refutes-stream.md`'s
correction block.** `KPKy`'s directory offset fields are now confirmed
**self-relative** to their own record's file position (15 independent
byte-exact target matches across 3 samples), and its `MESH` sub-chunk's
own TLV grammar is fully decoded end-to-end — a materials/shader library
(`TRSP`/`EFFE`/`CSTS`/`SAMP`/`MATE`/`VARI`), not raw geometry as originally
hypothesized; a real `"MergedGeometry0/1/2/..."` sub-mesh name table was
also found. `nier-x360-cpk-format-crossverify` closed: `CRILAYLA`
confirmed byte-exact via a genuinely independent cross-platform oracle
(0/640,689 bytes differ across 4 files where PS3 compresses and X360 ships
the same content raw — also revealing X360 doesn't CRILAYLA-compress these
file types at all).

**Update (2026-09-09, `re-codebreaker` + game-re)**: `.MDP` **is** plain
LZO1X after all — three independently-wrong framing premises (a 16-byte
page record that's really 12 bytes of three big-endian `u32`s, a per-page
match window that's really shared file-wide requiring decode into one
absolute-offset output buffer, and mandatory compression that's really
optional per file, 208/600 files stored raw) had each been independently
sufficient to make every earlier attempt fail (`tools/shared/nier-mdp.ts`,
reusing `cavia-lz0.ts`'s LZO1X state machine — real cross-generation Cavia
continuity with the PS2 Drakengard titles' own `\0V3a`/`lz0+` codec). On
top of the cracked codec, the `HEAP` GPU resource directory's `IXBF`/
`VXBF` records now decode to real triangle-strip index buffers and
interleaved vertex buffers whose stride is recovered arithmetically
(`rawSize / (maxIndex+1)`, `tools/shared/nier-heap.ts`). Both verified
whole-corpus with zero deviations (600/600 `.MDP` files, 17,981/17,981
geometry groups, 69.5M position floats) and cross-checked against the
independent X360 release. **Shipped as real assets**: a glTF 2.0 exporter
(`tools/shared/nier-gltf.ts`) and pipeline stage
(`tools/nier/mesh-assets.ts`, wired into the registered
`tools/nier/build-assets.ts` as a second content type alongside audio) turn
this into real character/weapon meshes — **304/304 `CHARA`/`WEAPON`
`.MDV`/`.MDP` pairs (171 characters + 133 weapons), 0 failures, 4.6M
vertices/3.8M triangles**, every sampled output file passing
`@gltf-transform/cli validate` with 0 errors/warnings/hints. Real,
recognizable renders confirmed across 3 content classes (a T-posed "Shade"
enemy, Yonah in her dress, the protagonist's 12-part clothing, a sword).
Open: `VXBF`'s packed normal/UV/colour attributes past byte 12 (blocks
textured/shaded meshes — shipped meshes are flat-grey geometry-only, no
skinning), `BG/` background geometry (not walked by this pipeline pass).
`docs/nier/ps3/data-structure.md` §4.4.5, §8.1.1.7; `docs/nier/plan.md`'s
sixth/seventh passes; `docs/nier/TODO.md`.

**Update (2026-09-10, game-re): real textured meshes.** `TX2D` (HEAP texture
records) are headerless BC1/BC3 (DXT1/DXT5) mip chains with no in-band
width/height/format field at all — `rawSize` alone determines dimensions via
`alignUp(mipChainBytes(w,h,bpb),128)===rawSize`, disambiguated where that's
ambiguous (96.7% of the corpus, since BC1-at-2w and BC3-at-w tie exactly on
byte count) by total-variation scoring of each candidate's decoded mip 0
(`tools/shared/nier-tx2d.ts`, reusing this project's existing `dds.ts`
BC1/BC3 decoder unmodified). `VXAR`/`VXBO` — the presumed `VXBF` vertex-
format descriptor — turned out to hold shader-parameter-name text
(`"gSampler0"`, the model's own name), not a field-layout struct: **no
in-band vertex-format table exists**, so `TEXCOORD_0` is instead *detected*
per geometry group by strip-adjacency smoothness (real triangle-strip-
adjacent vertices vary smoothly in UV space, random pairs don't — a 5x-32x
signal ratio, `tools/shared/nier-vertex-attrs.ts`). Both cross-validated by
rendering: a UV-scatter-on-texture overlay traces the real face/body
silhouette, and a from-scratch software rasterizer applied to the shipped
pipeline's own glTF output renders unmistakable, correctly-textured T-posed
`AMA020`/`YONAH010` characters. 260/304 (85.5%) models now ship a real
textured part (one shared "largest `TX2D`" diffuse per model — the true
per-part material binding, most likely in the already-solved `MESH` TLV
materials library, is still open as `nier-tx2d-material-binding`). See
`docs/nier/ps3/data-structure.md` §8.1.1.8-§8.1.1.9.

**Update (2026-09-10, game-re, two passes): real per-part material binding
at heuristic confidence for 175/304 (57.6%) of the corpus, then an
exhaustive follow-up that closed off every other data-only path without
extending coverage.** `MESH`'s `STRB`/`STRL` string pool gives real texture
*names* (index-paired with ascending-`TX2D`-id order), grouped into texture
"families" by channel-letter (`A`/`N`/`G`/`C`) cycling rather than base-name-
prefix matching (robust to real inconsistent numbering); `MATE`'s trailing
sampler-index field clustered by `SAMP`'s shared "identity" value gives the
family assignment. The missing link — binding a `MATE` record to a specific
`HEAP` geometry group — has no dedicated index field anywhere; the shipped
pipeline uses positional pairing (`MATE` record *i* == group *i*), gated on
the two counts matching exactly, which holds for 175/304 models (large
batched/merged models, where `MATE` count runs far below group count, keep
the older shared-texture fallback). A follow-up pass then opened `NODT` (a
`.MDV` `KPKy`-container chunk, offset-pair 1 of the type-5 record, entirely
unopened through every prior pass) for the first time — a real Collada-style
skeleton + node hierarchy plus a per-model "mesh instance" record that names
which geometry groups belong to the model (matching `HEAP`'s own naming
convention exactly), the first skeleton/joint-table find for this game — but
its one candidate material-binding field is a **corpus-wide-constant
sentinel** (checked across samples spanning 2 to 82 geometry groups), a
confirmed dead end rather than an unopened one. The same follow-up ruled out
a relaxed count-ratio heuristic (a 304-model corpus census found no clean
rule), and re-confirmed the type-5 record's still-unidentified "4th offset
slot" as shared boilerplate rather than per-instance data by diffing its
leading bytes across two structurally unrelated real models and finding them
byte-identical despite nothing else in common (see
`per-instance-file-set-may-be-duplicate-blobs.md`'s addendum — the same
"don't assume per-instance, diff before theorizing" principle applied to a
sub-region rather than a whole file). `MATE`'s own remaining fields (real
material names, e.g. `"ARMOR_2"`) were decoded as a side effect and shipped
as real glTF material names — an enrichment, not a coverage change.
**Net: this game's entire self-describing `.MDV`/`.MDP`/`MESH`/`HEAP`/`NODT`
format stack has now been searched for a per-geometry-group material index
and has none** — `VXSH`/`PXSH` RSX/Cg shader-bytecode disassembly is the
only remaining path to a *confirmed* (not heuristic) answer, not yet
attempted (a materially different, harder skill than this project's other
CPU-disassembly escalations — no RSX/Cg shader ISA work has been done
anywhere in this account yet, so a future escalation here would be
first-of-its-kind, not a rerun of an established technique). See
`docs/nier/ps3/data-structure.md` §8.1.1.10-§8.1.1.11.

## NieR (2010, Xbox 360)

**A fourth NieR-corpus platform, first pass.** Same 2010 Cavia game as the
PS3 original above — triggered by that PS3 pass's own open question
(`nier-video-blocked`: user reports a real ~3min intro on PS3 boot, but an
exhaustive PS3-dump search found zero pre-rendered video anywhere). This
pass used the X360 release (no NPDRM/PKG layer at all, fully readable) as
an oracle for "does the game even ship pre-rendered FMV" — **answer: yes**.

**Confirmed: real pre-rendered video, shipped.** All 4 real movie files
(`media/movie/*.sfd`) are plain, standard MPEG-2 Program Stream (magic
`00 00 01 BA`) — not Bink/WMV (the natural X360-era hypothesis) or CRI
Sofdec/USM. `TITLE_NIER_ALL.sfd` runs 184.83s (3:04.8), closely matching
the user's own ~3-minute report, and its decoded frames are visually
confirmed as NieR's real opening CG. ffmpeg's stock MPEG-PS demuxer reads
these directly — no custom container parser needed for the video itself.

**Confirmed: a real XDVDFS/GDF disc filesystem, parsed from scratch and
byte-exact verified** — new shared, general (not NieR-specific) module
`tools/shared/xdvdfs.ts`, reusable for any future Xbox/X360 title in this
project family. The computed partition-base offset lands on exactly
`0x0FD90000`, byte-identical to a known public constant
(`XboxDev/extract-xiso`'s `GLOBAL_LSEEK_OFFSET`, for hybrid video+game
discs) — strong independent confirmation, not a coincidence. Directory
entries are a standard in-place binary search tree (16-bit left/right
child offsets, ×4, relative to the table's own start) — cross-checked
against three independent real implementations (`extract-xiso`, `xbiso`,
`xbfuse`) before implementing from scratch.

**Confirmed cross-platform finding: the same CRI CPK toolchain as the PS3
release.** `media/layer1.cpk`/`layer2.cpk` are ordinary CRI `CPK`/`@UTF`
archives (identical packer version string, near-identical directory
taxonomy/file counts to the PS3 `STABLE.SDAT`'s own CPK) — `cri-cpk.ts`
applies completely unmodified via a trivial reader-adapter wrapping an
XDVDFS entry. Not opened further this pass (breadth census only); whether
the PS3 corpus's already-decoded inner formats carry over byte-identically
is a real, scoped, unconfirmed follow-up.

**A real, honestly-scoped audio finding, not shipped this pass.** The
movies' audio elementary stream is CRI AIX (magic `AIXF`), not plain ADX —
ffprobe/ffmpeg's shallow per-stream codec probe mislabels it `adpcm_adx`,
and only a full transcode attempt (not container-level probing) reveals
the mismatch (~99% packet decode error rate). Confirmed via vgmstream (a
scratch-copy byte-patch worked around vgmstream's own overly strict
format-recognition gate — see the pitfalls index for the general lesson):
1 segment, 3 stereo ADX layers, 6 channels total, byte-exact-matching
duration once opened. Which layer is the intended playback content is
undetermined, so the shipped MP4s are deliberately video-only rather than
risking an audibly wrong blind 6→2 downmix (overlapping languages).

Registered as a real Seer platform (`src/game-id.ts`: `'x360'` added to
`PLATFORM_IDS`; `tools/shared/game-config.ts`: new `platform: 'x360'`
entry under the existing `id: 'nier'` config). Full writeup:
`docs/nier/x360/data-structure.md`. Sequencing: `docs/nier/plan.md`. Open
items: `docs/nier/TODO.md` (`nier-x360-cpk-format-crossverify`,
`nier-x360-aix-audio`).

## NieR Replicant ver.1.22474487139 (PC, 2021 remaster)

**A third, unrelated NieR-branded title in this corpus** — same publisher
(Square Enix), but developed by **Toylogic**, not Cavia (the 2010 PS3
original, above) and not PlatinumGames (NieR:Automata, below). **Confirmed
zero format continuity with the PS3 original**: no CRI CPK/@UTF/CRILAYLA,
no PS3 NPDRM. Instead, a completely different in-house container: `.arc`
files are one or more concatenated whole-file **Zstandard** frames (public
RFC 8878 codec, standard magic `28 B5 2F FD`) wrapping a custom `PACK`
container (self-relative-offset directory of named, hashed sub-assets) and
a `BXON` typed-object header (the engine's own RTTI/reflection convention,
prefixing every structured resource with a magic + version + type-name
string). Engine confirmed via `.exe` string census: Audiokinetic Wwise
(audio) + embedded Lua 5.0.2 (scripting) + D3D11 (BC1-5 block-compressed
textures) — a consistent `tp`-namespaced in-house C++ codebase throughout
(`tpArchiveFileParam`, `tpXonAssetHeader`, `tpGxTexHead`), not shared with
either other NieR title's engine. **Registered as a Seer game**
(`src/game-id.ts`/`tools/shared/game-config.ts`, id `'nier'`, platform
`'pc'`).

**Real, high-quality prior art found and used**: the outer Zstandard
framing was independently derived from raw bytes first, then a
`WebSearch` surfaced
[`neptuwunium/kaine`](https://github.com/neptuwunium/kaine) (`yretenai`'s
tool, GitHub-account-renamed — the original URL 301-redirects) — a real
C++ extractor + plain-text format research notes covering this exact
game's `PACK`/`BXON`/`tpArchiveFileParam`/`tpGxTexHead` structs
byte-exactly. Every struct field is cited from that reference's actual
`.cpp` pointer arithmetic (not just its `.hpp`/prose notes — see
`game-re-lessons/self-relative-offset-needs-cpp-arithmetic-not-prose.md`).
For `data/sound/`'s Wwise `AKPK` container (a genuinely separate, later
format, see below), the reference was instead the community QuickBMS
script `bnnm/wwiser-utils/scripts/wwise_pck_extractor.bms` — same
"derived-from-reference, then independently re-verified byte-exact"
confidence discipline.

**Confirmed and shipped: `tpGxTexHead` textures, full corpus.**
18,320/18,474 real textures (99.2%) decoded — 19,635/19,635 archive
entries walked (base game + DLC), 0 read/decode failures. `.arc`'s master
index (`info.arc` → `BXON(tpArchiveFileParam)`) was verified via a real
cross-check: this project's own independently-derived raw zstd-frame count
per archive (zero knowledge of `info.arc`'s contents) agreed exactly with
`info.arc`'s own declared per-archive file counts, for all 6 base archives
+ the DLC archive. `ArchiveFileParam.hash` is standard FNV-1 32-bit,
solved via a systematic known-plaintext sweep, confirmed 100%
(19,635/19,635). Extractors: `tools/nier/build-assets.ts`,
`tools/nier/run-textures-batched.sh` (memory-safe batched runner —
`tools/shared/nier-pc-archive.ts`'s texture decode saw a real ~9GB-RSS
incident on one long-running process before this fix), `tools/shared/
nier-pc-archive.ts`, `tools/shared/dds.ts` (extended with BC2/BC5).

**Confirmed and shipped: `data/movie/` — `MARC`-wrapped standard ASF/
WMV2+WMA2 video, 9/9 files, 0 failures.** A trivial 24-byte custom header
(byte-exact `payloadSize === fileSize - payloadOffset` invariant, 0
deviations) wraps a genuinely standard Microsoft ASF container — no
game-specific video/audio codec work needed. Transcoded to H.264/AAC MP4
via ffmpeg's `subfile` pseudo-protocol (reads the payload directly from
its real byte range within the `.arc` file, no stripped-copy intermediate
needed even for the ~660MB largest source). A real, confirmed source-data
quirk (not a pipeline bug, see `game-re-lessons/container-declared-size-
may-be-stale-not-decoder-bug.md`): two attract-mode files' ASF headers are
stale, declaring the size/duration of an unrelated, much smaller sibling
file — ffmpeg correctly, cleanly respects the container's own (wrong)
metadata. `tools/shared/marc-container.ts` + `tools/nier/
movie-assets-pc.ts`.

**Confirmed and shipped: `data/sound/` — Audiokinetic Wwise `AKPK`
packages, 28,632/28,632 real clips decoded (100%), 0 failures, 0 name
collisions.** `AKPK` is a real, public, non-game-specific Audiokinetic
container format. A real structural discovery was needed to get to 100%:
Wwise's standard "streamed with prefetch" pattern means a minority of a
bank's embedded `DIDX` entries are deliberately truncated fragments (real
complete audio lives elsewhere, matched by numeric Wwise object id) rather
than complete streams — see `game-re-lessons/wwise-prefetch-fragment-vs-
complete-embedded-audio.md` for the local, self-contained discriminator
(compare a `DIDX` entry's own embedded `RIFF`-declared length against the
directory's declared size). Real breakdown: 17,233 `stream.pck` +
608 `stream2.pck` (plain standalone streams) + 10,791 `media.pck`-bank
entries (5,413 English + 5,378 Japanese genuinely unique complete
voice-line entries; a further 305 prefetch fragments correctly skipped).
Decoded via vgmstream-cli (reused, not re-derived) + ffmpeg. Extractors:
`tools/shared/nier-pc-akpk.ts`, `tools/nier/audio-assets-pc.ts`,
`tools/nier/run-audio-batched.sh` (batched/resumable runner — see
`game-re-lessons/batched-resume-reprobe-cost-linear-in-corpus-size.md` for
a real resume-path performance bug found and fixed on this exact corpus).

**A real, honestly-flagged cross-corpus lead, explicitly not claimed as
solved**: this remaster's `.cmfl` motion/animation payloads begin with
magic `KPK\x7f` — a sibling (shared 3-byte prefix, different terminal
byte, same "last-byte variant" pattern already seen twice in this
project's PS2 Cavia corpus) of the still-undecoded PS3 NieR corpus's own
`KPKy` format, above. Not assumed identical (different studio/engine/
console generation) — flagged as a two-directions-worth-checking lead,
tracked in both games' `TODO.md`. The outer `KPK\x7f` container structure
(chunk count + monotonic offset table) is itself confirmed, byte-exact,
across the whole real `motion/*` namespace (151/151); per-chunk internal
content (bone/keyframe data) is still open, as are `.rmesh` (mesh
geometry, 3,729 instances, magic confirmed `BXON` but type/layout
undecoded) and a long tail of other still-uncracked extensions.

Full writeup: `docs/nier/pc/data-structure.md` (a platform doc alongside
`docs/nier/ps3/data-structure.md`, sharing the top-level
`docs/nier/plan.md`/`docs/nier/TODO.md`).

## NieR:Automata (PC, Steam)

**A different, unrelated title from the NieR (2010, PS3) entry above** —
same publisher (Square Enix), same "NieR" branding, but developed by
**PlatinumGames**, not Cavia, and a much later (2017) release on a
different platform entirely. **Confirmed zero engine continuity with
Cavia's NieR (2010)** — zero `cavia` string hits anywhere in
`NieRAutomata.exe`. **Registered as a Seer game** (`platform: 'pc'`) as of
a 2026-08-10 second pass — first shipped asset type is textures, 2,632 real
`type: "texture"` entries decoded corpus-wide (all 24 `.cpk` archives,
2,969 `.wtp`/`.dtt` entries scanned, 0 read failures, 10 unsupported-
pixel-format failures) — see `docs/nierautomata/pc/data-structure.md` §16
and `tools/nierautomata/build-assets.ts`. A third pass the same day added a
second real asset type, meshes — see below. Chose textures over the first
(recon) pass's own "readable text is the fastest path" recommendation
because this project's viewer had no browsable text/data-table tab (unlike
`valkyrie`'s `data-view.ts`) — textures reused the already-built
`type: "texture"` PNG-atlas viewer path with zero new UI work, which won
out over a format that was genuinely faster to *decode* but would have
needed new UI to actually ship. Worth remembering as a general prioritization
rule for a "pick the faster of two viable first-asset candidates" call: weigh
existing-infra reuse, not just raw decode effort.

**Confirmed: PS3 NieR's CRI `CPK`/`@UTF`/`CRILAYLA` container work
transfers byte-for-byte unmodified** to this unrelated title —
`tools/shared/cri-cpk.ts`/`crilayla.ts` worked against real `.cpk` files
with zero code changes, including hitting the exact same `TocOffset >=
0x800` boundary-case `fileOffsetBase` rule (`TocOffset = 2048 = 0x800`
exactly, in both titles independently). CRI Middleware really is used
industry-wide across unrelated Japanese-publisher titles spanning multiple
console generations, not just within one developer's output — reinforces
checking for it on any new PS2/PS3/PC-era Japanese-publisher target before
re-deriving a container format from scratch. Unlike the PS3 release, the
PC release has **no NPDRM/encryption wrapper at all** — plain,
unencrypted files throughout, so `ps3-edat.ts`/`ps3-sdat-reader.ts` don't
apply here.

**Confirmed: a genuinely different, PlatinumGames in-house engine** — not
Cavia's, not Unreal Engine 3 — via direct C++ mangled-namespace evidence:
Audiokinetic Wwise and Geomerics Enlighten are both linked in directly
(their own public namespaces appear nested inside the game's own `lib`/`Hw`
wrapper layer), plus a literal linked-in CRI Middleware copyright string
and `CriFsBinder`/`CriFsGroupLoader` symbols confirming CRI's own
CPK-reading library is used directly, not reimplemented.

**Three new formats identified; two now decoded well past container shape**.
The generic PlatinumGames `DAT\0` resource-bundle container (wraps almost
the entire corpus regardless of file extension) now has 2 of its 3 previously-
unknown header fields decoded: a per-entry hash table and a per-entry real
(unpadded) size table, both found via the same style of arithmetic-invariant
sweep that first confirmed the outer `tableEnd = headerSize + count*4`
shape — see `game-re-method/verification-techniques.md`'s "header
count/table-start/table-end" technique entry, and `tools/shared/
nierautomata-dat-bundle.ts`. The `WTB`/`WTA`/`WTP` texture family
(PlatinumGames' own texture-archive format, shared with the studio's other
titles — Bayonetta, Vanquish, MGR:Revengeance, Astral Chain) is now decoded
down to a real per-texture/mip offset+size table whose format field matches
the actual Microsoft DXGI enum (`tools/shared/nierautomata-wtb.ts`) — but
turned out to be **unnecessary for pixel extraction**: the paired `.wtp`/
embedded-`DDS` payload is always a complete, standalone, spec-conformant
DDS file on its own, so the shipped pipeline decodes that directly via a
new general-purpose `tools/shared/dds.ts` (Microsoft DDS container + BC1/
BC3 block decompression, hand-rolled from the public spec — small,
deterministic block math, not a codec worth distrusting a reimplementation
of; verified via byte-exact mip-chain and cubemap face-major layout
invariants against real files, not just "renders look right"). `dds.ts` is
plausibly upstream-worthy (`game-re-tooling/seer-upstream.md`) — zero
game-specific logic, any project needing DDS/BC1/BC3 could reuse it as-is.
A real trap hit along the way: a sub-resource tagged `"XML\0"` inside the
`DAT` bundle turned out to be dense binary data, not literal text — see
`game-re-lessons/chunk-tag-name-mimics-unrelated-format.md`.

**Confirmed and decoded: `WMB3` mesh format, with real, game-specific prior
art** — a 2026-08-10 third pass found two independent, actively-maintained,
NieR:Automata-*specific* open-source Blender importer/exporter projects
(`WoefulWolf/NieR2Blender_2_8`, `ArthurHeitmann/Nier2Blender2NieR`) via a
plain `WebSearch`, cloned and read directly rather than hand-deriving from
scratch — both agree byte-for-byte on the struct layout independently, a
strong `romhacking-community-tools-first.md` win. Real corrections/
refinements past the prior art itself: a wrong per-vertex normal formula in
both reference tools (`byte*2/255`, never unit-length — neither tool's own
Blender importer actually reads the field, so the bug was never caught;
fixed via `byte/127.5-1`, verified against a real unit-length invariant —
see `game-re-lessons/reference-tool-field-never-consumed-by-its-own-
importer.md`); a used-vertex-set compaction for large world/terrain meshes
whose declared `vertexCount` is a loose, not tight, per-mesh bound (both
reference tools already solve this in their own `clear_unused_vertex()`
helper, which a naive struct-field port misses — see
`game-re-lessons/declared-range-field-loose-for-bulk-records.md`; also
fixed an 80s→1.1s performance cliff on the same file); and a general
`meshStart`-range form for mesh→material linkage past the reference tools'
own index-0-only assumption, which breaks on any multi-LOD file. Also fixed
a real gap in the already-shipped `WTB\0` texture-header parser (an
optional 4th texture-identifier table the original recon sample never
exercised — `game-re-lessons/format-field-width-unexercised-by-first-
corpus.md`'s pattern). Shipped a from-scratch glTF 2.0 exporter
(`tools/shared/nierautomata-wmb3-gltf.ts`, no umodel-equivalent exists for
this engine) — **1,819/1,867 (97.4%) of the real corpus decoded and shipped
as glTF**, 0 Khronos glTF-validator errors/warnings across ~83 real files
sampled. A real manifest name-collision bug between texture and mesh
entries sharing one source `.dtt` file was found and fixed along the way —
see `game-re-lessons/slugified-name-collision-overwrites-output.md`'s
second instance. Deliberately deferred, both real and scoped: skinning
(bones/boneMap/boneSet fully decoded, not yet baked into glTF `skins`) and
material→texture pixel linkage (a global identifier index resolves 99.97%
of real material texture refs to a `WTB\0` entry *location* corpus-wide,
but per-entry sub-texture cropping from a shared multi-texture `DDS`
payload needs a texture-pipeline extension not built this pass). Full
writeup: `docs/nierautomata/pc/data-structure.md` §18.

**Confirmed: audio moved from CRI ADX/HCA (PS3 NieR) to Audiokinetic
Wwise** — `BKHD` SoundBank chunks both embedded inside `DAT` bundles and as
standalone `.bnk`/`.wem`/`.wsp`/`.wai` files outside any CPK. Video is CRI
`USM` (own `CRID` magic, embeds the same `@UTF` table format as CPK).
Lighting is Geomerics Enlighten (`.enlMeta`/`.rss`, undecoded, licensed
third-party GI middleware, likely low priority).

Full-corpus TOC survey (cheap — never required reading a multi-GB file's
bulk content): 9,040 files across 24 real `.cpk` archives (corrected from
an initial miscount of 25), 22.4GB decompressed, only 11 distinct
extensions (a much flatter taxonomy than PS3 NieR's 34, since almost
everything funnels through the one `DAT` bundle container).

Full writeup: `docs/nierautomata/pc/data-structure.md`. Sequencing:
`docs/nierautomata/plan.md`. Open items: `docs/nierautomata/TODO.md`.

## Metal Gear Rising: Revengeance (PC, Steam)

**PlatinumGames**, 2013 — a different, earlier PlatinumGames title picked
up specifically to test whether NieR:Automata (PC)'s support transfers.
**Confirmed: it substantially does** — the CRI `CPK`/`@UTF`/`CRILAYLA`
container stack and the `DAT\0` resource-bundle container
(`tools/shared/cri-cpk.ts`/`crilayla.ts`/`nierautomata-dat-bundle.ts`) all
open real files unmodified. Genuinely different, all now solved: mesh is
`WMB4` (a real, restructured sibling of NieR:A's own `WMB3` — not a version
bump: 108-byte header vs. 140, a new `batchDescription` -> `batchData[]`
indirection; cracked via a real, game-specific 010 Editor binary template
in `Kerilk/bayonetta_tools`, `tools/shared/mgr-wmb4.ts` +
`mgr-wmb4-gltf.ts`, triangle winding confirmed via a real bimodal face/
vertex-normal histogram; 1,436 meshes shipped, 0 decode failures, 8.6M
vertices, 8.5M triangles, 5,101/6,119 materials textured — see
`fixed-stride-record-count-unverified.md`'s "stride confirmed against a
single-record file" addendum, sourced from this project's own `meshes[]`
stride bug), collision is standard third-party Havok (`.hkx`, not NieR:A's
own mesh-embedded BVH, not investigated further), and streamed Wwise audio
(`.wem`) is packed inside CRI CPK containers rather than sitting loose on
disk as NieR:A's own `.wem`/`.wsp` corpus does. Textures (`WTB`/`WTA`/`WTP`,
`tools/shared/mgr-wtb.ts`) are a genuinely different header revision from
NieR:A's own (`version` 0/1 vs. NieR:A's constant 3, a different low-field
layout, and two distinct container shapes NieR:A's corpus never exercised)
— 11,125 textures shipped; also surfaced a new standard DDS pixel format
(uncompressed 24-bit RGB, no FourCC) now supported in the shared
`tools/shared/dds.ts`. `WMB4` material textures resolve via a texture-
identifier index (`mgr-texture-index.ts`) whose resolution mechanism is
genuinely different from NieR:A's own: the `.wta`'s `(offset, size)` table
does NOT address real bytes in the paired `.wtp` here — resolution is by
POSITION, pairing the i-th `.wta` identifier with the i-th literal
`"DDS "` magic occurrence found by scanning the `.wtp`'s raw bytes (5,506
identifiers resolved corpus-wide, 0 unresolved). Video (CRI `USM`,
`tools/metalgearrising/video-assets.ts`, ported from NieR:A's own) is the
same container family, but MGR:R's cutscenes carry real embedded
`adpcm_adx` audio (two streams per file, which is "primary" unresolved) —
unlike NieR:A's silent-video-only corpus. `sound/bgm/BGM.bnk` is
reference-only (Wwise `HIRC` object hierarchy, no embedded audio, unlike
NieR:A's own `BGM.bnk`) — its `HIRC` chunk was hand-decoded (byte-exact
record framing; Music Segment/Track/SwitchContainer/RanSeq object types
cross-referenced against the extracted stream-ID corpus) to confirm a
real, structural instrumental/vocal music-layering mechanism (simultaneous
Track-child stem-layering within one Segment, not just whole-track
swapping).

A real, shipped **debug leftover** turned out to be the single best oracle
in this corpus: `GameData/data002.cpk` (a main data archive, unrelated to
`sound/`) ships a `Debug/sound/` folder of ~400 Wwise "SoundbanksInfo"-
style cue-sheet text exports (`CRILAYLA`-compressed like any other CPK
entry) that were never meant to reach retail. These directly join the
project's own extracted numeric Wwise stream IDs to real developer-
authored names — **142/334 (42.5%) of extracted music clips** and
**7,009/7,175 (97.7%) of extracted voice clips** now have a real, literal
name, no fuzzy matching needed (`tools/metalgearrising/wwise-cue-sheet.ts`
+ `bgm-cue-names.ts`/`voice-cue-names.ts`). ~1,055 of the named voice clips
further resolve to a real character/actor-model code (`pl0010` = Raiden,
`em0010a`-`em0010e`, etc.) via the cue sheet's own Wwise object-path
column — the dominant remaining 84% are Codec/radio dialogue under one
shared `radio` folder, named by a `<ChapterScene>_<Frame>` MessageID
convention rather than a per-character path (speaker not yet resolved,
`mgr-voice-radio-speaker`). The game's Codec-message container (`ckmsg/`,
`data000.cpk`) was investigated as the natural place a speaker tag would
live — real structure decoded (a generic `"BXM\0"` node/attribute table,
reusing the sibling `transformersdevastation` project's decoder
unmodified; a new `"RAD\0"` record format) but is a genuine, disclosed
dead end for text/speaker recovery: its largest sub-resource is opaque
low-entropy bytecode with zero readable strings in any locale checked
(English or German), and its `.dtt` sibling turned out to be a `WTB`
**texture** bank, not text at all — a real correction to the natural
"this must hold the subtitle text" assumption. Sourced
`sibling-text-files-mixed-encoding-silent-zero-match.md` (a real minority
of the cue sheets are UTF-16LE with a BOM, not the plain-ASCII the rest
of the corpus is) and `shared-parser-column-picker-scoped-to-first-
consumer.md` (the music-only cue-sheet parser's path-column pick had to be
re-derived, not reused verbatim, for the voice-line character-code
question).

Full writeup: `docs/metalgearrising/pc/data-structure.md`. Sequencing:
`docs/metalgearrising/plan.md`. Open items: `docs/metalgearrising/TODO.md`.

## Dragon's Crown (PS3 + PS4)

Not yet investigated. `data/dragonscrown/ps3/Dragon's Crown.pkg` is present
and is presumably the same classic-retail-PS3-PKG container as Drakengard
3 — `tools/shared/ps3-pkg.ts` should apply unmodified as a starting point.
If the PS4 release is ever pursued, note before assuming it's a smaller
version of the same PS3 problem: PS4 recompilation is architecturally a
*different kind* of problem (x86-64/GCN, not a foreign ISA to lift) — the
hard part is the Orbis OS/GNM layer, not CPU translation. See
`~/Development/seer/docs/ps4-recomp.md` before starting; short version, no
static recompilation project exists for PS4 at all (unlike PS3's
`ps3recomp`) — preservation effort there has converged on OS/driver-level
HLE emulation (`shadPS4`) instead, so this is a categorically different
task shape than the PS3 work above, not a variant of it.

## Chaos Legion / Devil May Cry (PS2)

Two unrelated-franchise **Capcom** PS2 titles picked up in the same pass:
**Devil May Cry** (2001, PAL disc, `SLES_503.58`) and **Chaos Legion**
(2003, NTSC-U disc, `SLUS_206.95`) — different games, same developer/
publisher and console generation, so the pass deliberately diffed formats
between them the same way the Drakengard/Drakengard 2 pass above did for
Cavia. **Zero engine continuity with the Drakengard titles in this
project** — different developer (Capcom vs. Cavia/Square Enix), no shared
formats found or expected. First-pass recon only (Method §1-§2), no
extractor code or `public/assets/` output yet — both games' own
`data-structure.md` have the full byte tables and verification evidence;
`docs/devilmaycry/plan.md` / `docs/chaoslegion/plan.md` have the
recommended build order.

**Confirmed, both games:** MetroWerks CodeWarrior for MIPS (`MW MIPS C
Compiler (2.4.1.01)`, literal build-stamp string, byte-identical toolchain
version across both 2001 and 2003 titles) compiling an in-house engine (no
licensed third-party engine/middleware strings found in either EXE) with
its own in-house audio driver in both cases (Devil May Cry:
`TSNDDRVM.IRX`; Chaos Legion: named by literal string `"S6 CAPCOM
SoundDriver"`, module `CAPSDRVD.IRX` — not confirmed to be the same driver
lineage, just both confirmed Capcom in-house). Chaos Legion additionally
carries a literal internal engine-name string, `"CAPCOM TOKYO P S 2
SYSTEM"`, not found in Devil May Cry's executable (inconclusive negative,
not proof DMC lacks an equivalent).

**Confirmed, shared texture baseline:** both games' primary texture format
is the industry-standard Sony PS2 SDK `TIM2` format (literal `TIM2` magic,
`version=4` header, matches the public spec) — this is normal PS2-wide
middleware, not Capcom-specific, and not new prior art for this project's
own corpus so much as confirmation neither title does anything unusual
here. Chaos Legion also has exactly one confirmed instance of `CLT2`,
**now fully solved (2026-08 follow-up pass)**: not a pixel/compression
variant at all — an exhaustive whole-disc magic scan confirmed there is
genuinely only one instance anywhere (so a second sample to diff, the
original pass's blocker, doesn't exist to find), and parsing its picture
header against the unmodified public TIM2 spec decodes byte-exactly as a
standalone CLUT-only resource (`image_size=0`, `clut_size=1024` = a
256-colour RGBA32 palette, `header_size+clut_size+image_size==total_size`
exactly). I.e. `CLT2` = "CLUT2," literally the same TIM2 struct with the
image component zeroed, not a new format — see
`game-re-lessons/sibling-magic-may-be-same-struct-zeroed-field.md` for the
generalizable lesson this produced. 0 `CLT2` instances found in the Devil
May Cry corpus either way.

**Confirmed, genuinely different disc-level asset organization (the
headline finding of this pass):** Devil May Cry (2001) ships every asset
as an individually-named ISO9660 file (566 files, 15 folders — the
filesystem tree *is* the catalog). Chaos Legion (2003) instead bundles
almost the entire game into one flat 403,369,984-byte archive
(`LEGION.DAT`) addressed by a separate 3,119-entry `u32` sector-offset
index (`LEGION.IDX`, sentinel `0xFFFFFFFF` for unused IDs) — verified
byte-exact via a structural invariant (`LEGION.DAT`'s size divided by 2048
is exactly 196,958, a whole number) plus magic-byte content verification
spanning the full ID range (TIM2/CLT2 magics, a literal `"Chaos
Legion"`+build-timestamp string at id=1, real script/config text at id=4).
This is the same general "flat archive + catalog table" shape flagged in
`game-re-tooling/ps2.md` and seen in this project's own Cavia Drakengard
work (`docs/drakengard-cavia-archive-format.md`), independently confirmed
a third time on a third, unrelated developer's title — worth treating as a
recurring PS2-era pattern worth checking for early on any new PS2 target,
not a coincidence specific to any one studio.

**Confirmed, a shared small-object container header on the Devil May Cry
side:** `.EMD` (enemy models), `.BND`, `.FSD` (per-room data), and `.PWS`
files share a byte-identical 32-byte header (`0x00000000`, a size-like
`u32`, `0x00000000`, `0x00000001`, 16 bytes of zero padding, then a second
directory-like region) — confirmed 100% match across all 4 extensions'
full sampled corpus (196 files). Most `.PLD` (player/Dante model) files
match too; 2 exceptions (`PL00.PLD`/`PL05.PLD`, Dante's base-costume
models) use a richer, different `count`+offset-table header instead —
plausibly reserved for multi-part assets. `.PWD` doesn't match at all
(its own distinct small directory format). Whether this same 32-byte
shape recurs anywhere in Chaos Legion's flat archive was **not**
conclusively tested this pass (partial negative only — the samples
examined in Chaos Legion's large "other"/unclassified bucket looked
differently shaped) — open, tracked as `cl-generic-wrapper-cross-check` in
`docs/chaoslegion/TODO.md`.

**Still substantially open on both sides:** the body/semantics of the
generic wrapper header above (Devil May Cry, `dmc-generic-wrapper-body`);
Chaos Legion's largest single unresolved item, a 201 MB/273-entry
unclassified "other" bucket in `LEGION.DAT` (49.8% of the whole archive by
bytes, almost certainly the bulk of the game's 3D models/animation/audio,
tracked as `cl-other-bucket`); and Chaos Legion's tagged `ALG`/`GCS`/`SYS`
sub-resources (`cl-tagged-subresources`), still a circumstantial-evidence-
only hypothesis, no magic bytes or disassembly trace confirmed.

**Solved (2026-08 audio-driver follow-up pass): Devil May Cry's `.XAG`
files, fully confirmed, closes `dmc-xag-audio-format`.** Codec was already
confirmed (raw headerless Sony PS-ADPCM); this pass nailed down channel
count, interleave, and sample rate by extracting DMC's own
`DATA/MODULES/TSNDDRVM.IRX` and finding it ships a **full, unstripped GCC
`.mdebug` with real stabs type info** — including the literal C struct
declaration (`_XAG_FILE_INFO`) Chaos Legion's own `CAPSDRVD.IRX` reads too
(same Capcom driver lineage; Chaos Legion's own copy of `.mdebug` is a
stripped stub with no type records, so DMC's shipped debug info is what let
*both* games' field layout be recovered). DMC's own 4-record `Tsnd_xag_tbl`
(count cross-confirmed two ways: the driver's own `Xag_load_max` symbol
reads 4, and the very next global symbol's address sits exactly
`4 × 36 = 144` bytes later with zero gap) reads uniformly across every
record: 2 channels, `0x4000`-byte-per-channel interleave, `pitch=0xeb3`
(the intended, designed rate is the standard 44,100 Hz CD-audio rate,
truncated to the nearest achievable SPU2 pitch-register integer).
Independently re-confirmed from the raw `.XAG` bytes: both real files'
sizes divide the stereo frame size exactly (zero remainder), and real
in-stream loop markers land exactly `0x4000` apart, whole-file scan, zero
exceptions. Full derivation: `docs/devilmaycry/ps2/data-structure.md` §6.

**Devil May Cry's `.PSS` movies: video is fully solved and needs zero
further work** — literal MPEG Program Stream marker (`00 00 01 BA`),
`ffprobe`-confirmed real MPEG-2 video (512×448, 25fps) — a standard
interchange format, not game-specific, so delegate to `ffmpeg` rather than
hand-decoding (per `game-re-lessons/standard-codec-delegate-to-trusted-
decoder-not-hand-reimplementation.md`). **Correction (same audio-driver
pass): the movies are not silent** — an earlier pass sampled only
`TITLEP.PSS` (the title loop), found zero audio streams under `ffprobe`'s
default probe, and recorded that as "plausibly silent." A raw byte-level
census (`00 00 01 BD` `PRIVATE_STREAM1` marker count + `SShd` occurrence
count) across the whole 18-file `.PSS` corpus found **every single
file**, `TITLEP.PSS` included, carries a real embedded audio track via the
same custom `SShd`/`SSbd` PCM framing already confirmed in Chaos Legion's
hidden FMV region (below) and Cavia's unrelated "cavia stream format
v1.01" container — a third independent confirmation this is shared PS2-era
streaming-audio middleware, not developer-specific. `ffprobe`'s generic
probe simply doesn't recognize the framing; decoding the raw PCM directly
and cross-checking duration against the same file's own independently-
reported *video* duration (63.926s decoded vs. 63.880s reported, 0.07%
error) is what actually confirmed it. New lesson:
`game-re-lessons/generic-demuxer-misses-custom-pes-audio.md`. Not yet
built into the pipeline (`docs/devilmaycry/ps2/data-structure.md` §9).

An initial pass concluded Chaos Legion ships **no**
FMV movies at all (0 MPEG-PS markers found across the full 3,024-entry
`LEGION.DAT` archive scan) — **this was wrong, see the correction
immediately below.**

**Correction (2026-08 follow-up pass): Chaos Legion does ship FMV —**
the "0 MPEG-PS markers, no FMV at all" negative above was real but
mis-scoped: it only ever scanned `LEGION.DAT`'s 3,024 catalogued entries.
~1.58 GiB of standard MPEG-2 Program Stream video (512×448, 29.97 fps —
same codec/resolution family as Devil May Cry's `.PSS` movies, differing
only in NTSC vs. PAL frame rate) lives in **raw, un-catalogued ISO9660
sectors** in the gap between `/MODULES/` and `/LEGION.IDX` — a region with
zero directory entries pointing into it. Found by laying every catalogued
file out by LBA (`xorriso -exec report_lba`) and noticing a ~1.9 GB jump
with no file in between; confirmed real (not padding) via an exhaustive
non-zero byte scan, then confirmed as MPEG-PS via a byte-exact structural
invariant (103,432 sector-aligned `00 00 01 BA` pack headers, 99.98% of
them exactly 8 sectors apart, with the region's true end independently
pinned down by a literal `PROGRAM_END_CODE` sitting exactly where the
pack-stride arithmetic predicted), `ffprobe`+`ffmpeg` (zero decode errors
across a full 64,559-frame decode), and — decisively — three real decoded
frames showing actual readable Chaos-Legion-specific content, including
the game's own "CHAOS LEGION" title/logo screen. This is a second
independent confirmation (after Valkyrie Profile 2 in the `valkyrie`
project) of the PS2-era "raw-LBA gap between catalogued files" pattern
in `game-re-tooling/ps2.md`/`iso9660-tree-near-empty-check-raw-lba-toc.md`
— genuinely distinct from that lesson's trigger condition, though, since
Chaos Legion's ISO9660 tree is **not** near-empty (22 substantial
catalogued files); the gap sat *between* two normal-looking catalogued
files, not in an otherwise-empty tree. New pitfall written up for this:
`game-re-lessons/catalogued-file-scan-misses-raw-lba-gap.md`. Full
write-up: `docs/chaoslegion/ps2/data-structure.md` § 9.

**Solved end-to-end (2026-08 follow-up pass): FMV per-clip split + audio +
web-native promotion, all real, all verified.** The ~1.58 GiB hidden
region is 17 discrete clips, not one blob — found via a real, generalizable
technique (MPEG-PS SCR-reset detection, no disassembly needed; see
`game-re-method/verification-techniques.md`'s new entry) and independently
cross-checked by every clip's own fresh sequence header landing at the
identical byte offset (51) 17/17 times. Each clip's FMV audio (previously
mis-identified by `ffprobe`'s auto-probe as `mp2`) turned out to be a
custom-framed 48 kHz/stereo PCM stream wrapped in `SShd`/`SSbd` chunks —
**the same chunk-tag convention already documented for Cavia/Square's
Drakengard** ("cavia stream format v1.01" above), now confirmed
independently in this unrelated developer's title too — real evidence
this is shared PS2-era streaming-audio middleware, not
developer-specific. A real methodology trap surfaced and got fixed along
the way: each audio packet carries a 2-valued toggle field that looked
like it might select between two duplicated streams; a raw byte-diff
between the two groups showed 64.6% disagreement (looked like "two
different things"), but the two groups are actually the *same* audio
sent twice for streaming reliability — decisively shown by a 0.99995
zero-lag cross-correlation, not the byte-diff. See
`game-re-lessons/redundant-transmission-needs-correlation-not-diff.md`.
All 17 clips promoted to real web-native H.264/AAC MP4
(`public/assets/chaoslegion/ps2/video/*.mp4`, 1.58 GiB → 152 MB, 0 decode
errors). Tooling: `tools/chaoslegion/fmv_common.py` (unit-tested core),
`split_fmv_clips.py`, `extract_fmv_audio.py`, `promote_fmv_assets.py` —
supersedes the original recon-only `extract_hidden_fmv.py` (kept for
compatibility). Full write-up: `docs/chaoslegion/ps2/data-structure.md`
§§ 9.1-9.5.

**`LEGION.DAT`'s "other"/unclassified bucket, advanced but not closed**: a
full-corpus structural classifier (entropy + ASCII-run + float-
plausibility + PS-ADPCM byte-shape heuristics,
`tools/chaoslegion/classify_legion_dat.py`) shrank the genuinely-
unclassified population from 273 entries/201 MB to 102 entries/47 MB.
135 entries (154 MB) score as real, above-random-baseline PS-ADPCM-shaped
data but resisted 2 different decode attempts (raw sequential VAG;
offset-table-segmented VAG) — an honestly-labelled hypothesis, not a
confirmed decode, and a good escalation candidate for a future pass. A
real classifier bug was caught mid-pass: an ungated ADPCM-shape heuristic
trivially flagged all-zero padding as false positives (zero satisfies
almost any small-range shape test) — see
`game-re-lessons/byte-shape-classifier-needs-entropy-gate.md`. The
`cl-id-to-purpose-map` disassembly trace itself (what numeric-ID constant
maps to what resource) remains untouched — a `host:`/`cdrom0:` string
search came back with only devkit debug paths and IOP module names, no
plaintext id/filename table, confirming the archive really is addressed
by baked-in numeric constants with no shortcut around tracing the loader.

Full write-ups, byte tables, and verification evidence:
`docs/devilmaycry/ps2/data-structure.md`,
`docs/chaoslegion/ps2/data-structure.md`. Open-item trackers:
`docs/devilmaycry/TODO.md`, `docs/chaoslegion/TODO.md`.

**Solved (2026-08 follow-up pass): `TIM2` pixel/palette decode, shared
between both games, both games now real registered/live-verified Seer
entries.** Closes `cl-tim2-pixel-decode`/`dmc-tim2-pixel-decode`. Cross-
checked against a real, fresh-cloned GPL2 reference implementation
(marco-calautti/Rainbow, C#) rather than hand-derived — byte-exact 48-byte
picture-header layout, 4/8bpp indexed (CSM1 CLUT unswizzle for 256-entry,
gated by a real `linearPalette` header bit; 16-entry never unswizzled) and
16/24/32bpp direct color, with one deliberate deviation from the reference
(32bpp alpha uses the PS2 GS 0-128 halving convention, confirmed by this
project's own already-solved `CLT2` evidence, not the reference's raw
passthrough). Shared code: `tools/shared/tim2.ts`. Real, decisive visual
verification across both titles and three bit depths: DMC's own Capcom
splash logo and title screen (32bpp), a font glyph strip (4bpp), a status
icon with correct alpha (8bpp); Chaos Legion real readable in-texture
Japanese lore text (4bpp) and — closing `cl-region-letter-mapping` — the
same UI tooltip string read in all four `IHS/IHJ/IHF/IHE.DAT` per-language
packs, confirming S=Spanish/J=Japanese/F=French/E=English directly from
content. A real sub-finding: `IH*.DAT` isn't one multi-picture `TIM2`
container as first assumed — each is a flat concatenation of 1,523
independent `TIM2` sub-files, individually sector-padded, walked via a
literal magic-byte scan (`parseTim2Bundle`). That same scan technique does
**not** transfer to every multi-`TIM2` bundle shape: 22 of Devil May Cry's
`.ITM` files use a different `count`+offset-table header, and a magic-scan
against those produces a 10x-inflated false-positive count (still open,
`dmc-itm-bundle-container`) — see the new `game-re-tooling/ps2.md` TIM2
section for the general lesson. Both games are now real `GAME_CONFIGS`
entries (`tools/chaoslegion/build-assets.ts`, `tools/devilmaycry/
build-assets.ts`) with live Playwright-verified browsing: Chaos Legion —
8,561 textures (2,468 `LEGION.DAT` + 1 `CLT2` + 6,092 language-pack) + the
17 already-solved FMV clips, 8,578-entry manifest; Devil May Cry — 59
`TIM2` + 122 `.T32` textures, 61 `.EMD`/`.PLD` meshes (bind-pose, first
chunk only), 2 `.XAG` audio previews, 244-entry manifest. A real,
previously-undetected bug was found and fixed along the way: Chaos
Legion's FMV `promote_fmv_assets.py` wrote video manifest entries with ad
hoc field names (`mp4`/`width`/`height`) instead of the viewer's real
`ManifestEntry` contract (`video`/`videoWidth`/`videoHeight`) — every clip
would have silently failed to play the first time this game was actually
opened live, never caught before because it had no pipeline registration
to view live until this pass. See `docs/chaoslegion/ps2/data-structure.md`
§12, `docs/devilmaycry/ps2/data-structure.md` §5.1, and two new pitfalls:
`texture-manifest-entry-needs-atlas-sidecar.md`,
`vite-dev-server-stale-public-dir-listing.md`.

**Solved (2026-08 model-decode pass): Chaos Legion's 3D models, found and
decoded** — closes this project's open "3D models/animation never
identified for Chaos Legion" question, for meshes (no animation data
found or claimed). They were never in a dedicated container — they're
inside `LEGION.DAT` catalog entries a prior pass's own structural
classifier had misfiled as `adpcm-like` audio (33 of 39) or
`other-unclassified` (6 of 39), a real byte-shape-classifier false
positive (packed per-vertex UV+alpha float32 data satisfying the same
narrow ADPCM nibble-range shape test padding does — see the sharpened
`game-re-lessons/byte-shape-classifier-needs-entropy-gate.md`). Container:
a small nested directory structurally self-similar to `LEGION.DAT`/
`LEGION.IDX` itself (`0`-sentinel offset table; sub-blocks tagged `TIM2`
texture / `u32==16` geometry / `u32==0,1` unidentified / a new `CLM\x1a`
tag). Geometry: fixed 448-byte preamble (header+AABB+axis points) then
48-byte float32 vertex records — plain world-space position (no scale
factor, unlike Cavia's `CSFg`) plus a `(u,v,1.0,128.0)` UV+alpha quad
whose `128.0` cross-confirms this game's own already-established PS2 GS
alpha convention. Real, structural (not id/size-heuristic) whole-archive
scan: 39 model packages, 41,838 decoded vertices, 78 embedded `TIM2`
textures. Honestly scoped as a **prefix decode** — the clean 48-byte
record run stops at a real, unexplained layout discontinuity partway
through some sub-blocks' declared byte range on 2/6 hand-checked packages,
tracked open (`cl-model-geometry-segmentation`), same for UV-to-texture
binding (`cl-model-uv-texture-binding`, likely lives in the undecoded
`CLM\x1a` tag). All 39 exported glTFs pass the Khronos validator with zero
errors (a real zero-length-`NORMAL` bug was caught by the validator, not
the visual render, and fixed with a unit-vector fallback for
degenerate/unweighted vertices). Live Playwright-verified: 4 packages
render as real, coherent, artist-plausible shapes (a helmet/vessel with a
spike, a radial blade fan, a curved armor-plate shell, a blade/wing
cluster), 0 console errors. Wired additively into
`tools/chaoslegion/build-assets.ts` via new `tools/chaoslegion/
legion-model.ts` + `legion-model-gltf.ts` (11 new tests). A real bug —
the nested directory's last sub-block size computed against the wrong
boundary field, silently negative — was caught only by a synthetic
round-trip unit test, never manifesting as a visible failure against real
corpus data (the affected block just silently decoded 0 vertices instead
of throwing). Full writeup: `docs/chaoslegion/ps2/data-structure.md` §13.

**Solved (2026-08-10 pass): the FMV audio "sounds wrong" bug report was
real, and its root cause was a byte-order bug invisible to every
structural check previously used to call this "confirmed."** The FMV
audio decoder assumed little-endian 16-bit PCM throughout; the game's own
raw bytes are big-endian on 15 of 16 audio-bearing clips (the 16th, an
externally-sourced logo/theme-song vanity card, is genuinely the
opposite — no header field distinguishes the two cases). Found via lag-1
sample autocorrelation (wrong order ≈0.00, right order 0.85-0.98, a
70-1,000x margin on every clip) and confirmed visually via spectrogram
(flat broadband noise → real harmonic/dynamic structure), fixed with a
per-clip data-driven auto-detector rather than a hardcoded byte order
(`detect_pcm16_byte_order()` in `tools/chaoslegion/fmv_common.py`),
re-verified end-to-end including on the shipped `.mp4` and live in the
browser. Also re-checked (per this pass's own brief) and downgraded the
original single-clip "0.99995 toggle cross-correlation" figure, which was
measured on the pre-fix decode and doesn't hold as a corpus-wide constant
(0.37-0.96 whole-clip, 0.20-1.0 by window, across 4 clips re-checked) —
the practical toggle==0-only dedup choice is unchanged, just now honestly
labeled "best available" rather than "proven." Same pass, real progress
(not full closure) on "more music": segmented the ~287 MB SE/voice region
beyond the 17 known BGM tracks into 525 short (<2.5s) SFX-shaped samples
(correctly *not* labeled music) plus 2 large (242.6 MB + 52.0 MB)
terminator-free spans confirmed as real structured audio via spectrogram
but left unshipped — channel count is genuinely unresolved (weak/
inconsistent 2ch/4ch correlation, unlike the confirmed BGM stereo
signal) and no internal track-boundary convention was found for them.
Also found and documented a new general pitfall along the way: reusing
the BGM region's stride-based multi-channel-grouping technique unmodified
on the much denser SE/voice region catastrophically false-merged
unrelated terminators into a bogus "8,843-second track" — see
`game-re-lessons/stride-grouping-false-merges-in-dense-marker-regions.md`.
Full writeup: `docs/chaoslegion/ps2/data-structure.md` §9.4 (correction
block) and new §9.7; open items: `docs/chaoslegion/TODO.md`
(`cl-xag-se-voice-long-spans`, `cl-fmv-toggle-not-uniform-duplicate`).

## ZOE2 / ANUBIS — Zone of the Enders: The 2nd Runner (PS2 + PS3, Konami)

**Project: `~/Development/flower`, game id `zoe2anubis`, platforms `ps2` +
`ps3`**

### PS3 — "ZOE HD Collection" build (2026-08-14, companion pass)

`docs/zoe2anubis/ps3/`, tools prefixed `ps3*` in `tools/zoe2anubis/`. Key
finding: **`STAGE.DAT` is MD5-identical to the PS2 disc's copy** — the same
still-open mesh-vertex/texture-pixel puzzles carry over unchanged (see
`byte-identical-cross-platform-archive-does-not-bypass-sibling-puzzle.md`).
`ZoE2/bin/*.bin` (130 per-stage files, initially hypothesized to hold
re-encoded mesh/texture data) turned out to be **compiled PS2 EE/MIPS
R5900 machine-code overlays** bound to one constant fixed load address
(`0x00261D80`) — confirmed via opcode-shape census + a byte-exact function
prologue/epilogue idiom + retained PS2 SDK debug strings (`libmpeg`,
`libipu`, `libscn.h`) — not assets at all (see
`script-files-may-be-native-code-bound-to-fixed-memory-map.md`). The
genuinely new, solved PS3-side asset: **HVSTEX compressed texture bank**
(`HVSTEX/Compressed/v2/*.tga.dxt5.zzd`, 325 files, UI/manual/logo art) —
`u32 LE` decompressed-size header + raw zlib → standard DDS/DXT5, opened
natively by Pillow, 325/325 verified. Also found: an accidental leftover
**CVS developer working-copy tree** at `ZoE2/stage/{init,ca01}/` (real
`CVS/Root`/`Repository` metadata) containing plaintext `.atr` skeleton/bone-
hierarchy files (real Jehuty bone names, e.g. `SKL_HIP`/`SKL_CHEST`/
`SKL_ARM_LU`) and `.tex` files that independently re-derive the PS2 model
container's `{magic,c2,off,size}` chunk grammar + `hi16*0x10+lo16` offset
formula on unrelated, uncompressed bytes (pixel decode still open) — see
`shipped-disc-leftover-vcs-tree-plaintext-oracle.md`. Full detail:
`docs/zoe2anubis/ps3/data-structure.md`; open items:
`docs/zoe2anubis/ps3/TODO.md`.

### PS2

(registered as a Seer game alongside the Cavia/Capcom titles; docs at
`docs/zoe2anubis/ps2/`, tools at `tools/zoe2anubis/`). Konami MGS-family
engine, **not** Cavia — same console generation as Drakengard 1/2 but a
completely different developer/format family; the Cavia shared decoders
have zero applicability here.

**Solved (2026-08-12 .. 2026-08-16, passes 1-9):**
- **STAGE.DAT cipher** — the Konami MGS2-family STAGE cipher: root keystream
  (`keyX' = LO32(keyX*0x02E90EDD)+keyY`, the R5900 **3-operand `mult rd,rs,rt`**
  that capstone/radare2 both misdecode as "invalid" — the decoder needs to
  know the EE writes the product-low to `rd`), per-folder re-seed from a
  folder-name hash, per-file re-seed from the first u16 (`^0x9385`); payloads
  are raw deflate. Cross-validated byte-exact against `kellymoen/MGDecrypt`
  (its ZOE2 path is buggy — real folder-table tags are at +0x00, not +0x04).
- **VOX.DAT** — 1922 flat PS-ADPCM clips (`00 7F AC 44` anchors), mono
  voice + stereo music, 44.1 kHz; byte-exact C decoder vs MGS2-Audio-Tool.
- **Stage model container** — folder-table `tag` = hash of the resource's
  file *extension* (`hash("mdz")==0x003B12FB`, `hash("tex")==0x001E5452`;
  the early "mesh/bbox/skeleton" class labels were wrong), entry field 2 =
  full-filename hash resolved against ELF strings; runtime resource
  registry (16-byte `{hash,0,ram_ptr,1}` records) resolves blob hashes to
  EE RAM in the PCSX2 savestates.
- **`.tex` texture format** — chunk records are GS `TEX0` values, payload
  is a `PSMCT32` staging rect, `PSMT4`/`PSMT8` views by `TBP0` delta,
  per-desc CLUT pointer; desc's first two words are one 64-bit GS `CLAMP`
  register giving every sub-rect origin+size (the loader's in-place vertex
  UV rewrite reproduced byte-exact, 36,741/36,741). 10,656 views decoded.
- **`.mdz` model format (pass 7, vertex record corrected pass 9)** — header
  FLAGS word + 0x80-byte world-space node records + 0x20-byte batches +
  s16 triangle-strip vertices in **three VU1-verified layouts** selected by
  header flags: lit 18 B `{uv, adc|scalar, unit normal ×4096, position ×16}`,
  prelit 18 B `{uv, adc|scalar, RGB 0-255, position ×1}`, short 12 B
  (bit2). Positions plain node-local × absolute node matrix; node bbox is a
  containment AABB (100.000% corpus-wide, 2,501 blobs / 4.23M vertices;
  ADC strip invariant exact 412,318/412,318). Field roles proved by
  decoding the load-time-built VIF packet chains in EE RAM and
  disassembling the VU1 kernels in `vu1MicroMem.bin` (see
  `game-re-tooling/ps2.md`, savestate-VU1 section). Passes 7/8 had the
  unit normal decoded as the position — the placement layer still rendered
  a convincing mech (see `game-re-lessons/
  model-silhouette-render-confirmed-by-placement-layer.md`). 48 models
  ship as glTF with NORMAL/COLOR_0.

Tools: `stagedec.py`/`stageextract.py`, `voxextract.py`+`psadpcm_fast.c`,
`texdecode.py`+`ps2gs.py`, `mdzdecode.py`, `vudis.py` (VU microcode
disassembler, reusable on any PS2 title), `mdzverify.py` (re-runnable
corpus proof), `modelprobe.py` (legacy names). Ground truth: three PCSX2
savestates at `data/zoe2anubis/{vr-menu,running-ingame,in-vr-mosquito}`.

**Open:** stream-header record semantics, VOX clip→dialogue mapping, the
`.mdz` batch `+0x0C` bitfield's per-bit meaning and the vertex `+0x04`
scalar (see `docs/zoe2anubis/ps2/TODO.md`). Docs:
`docs/zoe2anubis/ps2/data-structure.md` (§4.10 pass-9 correction block).

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/flower` | Drakengard 3 (PS3, UE3), **Drakengard + Drakengard 2** (PS2, Cavia in-house `fpk`/`dpk` container family — container, `wZIM` textures, `CSFg` mesh+VU1 sub-format, `CJFg` skeleton, `CMFf` animation, PS-ADPCM audio, and the `\0V3a` LZO1X compressed-blob wrapper all solved and registered; 3,380/528 model packages, 130K+/12K textures shipped both games), NieR 2010 (PS3, Cavia in-house + CRI CPK — not UE3; registered, nested-CPK audio shipped 4,501/4,501 clips, plus `.MDP`'s `"lzo\0"` wrapper cracked as plain LZO1X — three independently-wrong framing premises had made it look uncompressed, see `lzo-style-decode-start-offset-independence-refutes-stream.md`'s correction — and real character/weapon meshes shipped as glTF, 304/304 `CHARA`/`WEAPON` pairs, 0 failures, `gltf-validator`-clean, now with real `TX2D` BC1/BC3 texture decode — dimensions recovered purely from `rawSize` via a mip-chain-size+128-align formula, disambiguated by total-variation scoring where that's ambiguous (96.7% of the corpus) — and a heuristic per-group `TEXCOORD_0` detector (no in-band vertex-format table exists; found instead via strip-adjacency UV smoothness), 260/304 models textured, both cross-verified by rendering real recognizable characters, 175/304 with a real per-part material binding via `MATE`/`SAMP`; a later pass's RSX shader-bytecode-disassembly escalation for the remaining 42.4% settled as a real negative rather than an unexplored lead — the shader-family `id` space is corpus-wide disjoint from the geometry-group `id` space (0/304 exceptions) and the fragment-shader record's own descriptor region carries no group index, so full NV40 ISA decode couldn't have closed this gap either; found and fixed a real, related addressing bug along the way (vertex-shader records address a second raw pool living inside the `.MDV` file itself, not the paired `.MDP` stream — see `offset-field-collision-with-confirmed-sibling-reveals-wrong-pool.md`, sourced from here)), NieR:Automata (PC, PlatinumGames in-house + same CRI CPK family — registered, textures+audio+video+mesh shipped), Metal Gear Rising: Revengeance (PC, PlatinumGames — confirms NieR:Automata's CRI CPK/CRILAYLA/`DAT` container stack transfers unmodified across a different, earlier PlatinumGames title; `BGM.bnk`'s Wwise `HIRC` object graph hand-decoded confirming real instrumental/vocal stem-layering, and a shipped debug leftover — `data002.cpk`'s `Debug/sound/` Wwise cue-sheet exports — named 142/334 music clips and 7,009/7,175 (97.7%) voice clips with real developer text, ~1,055 of the latter further resolved to a real character/actor-model code (`pl0010`=Raiden, etc.); the `ckmsg` Codec-message container decoded structurally but is a confirmed dead end for subtitle/speaker text; textures+video+mesh now also shipped — `WMB4` is a genuinely restructured sibling of NieR:A's own `WMB3` (not a version bump), cracked via a real game-specific 010 Editor template in `Kerilk/bayonetta_tools`, 1,436 meshes/8.6M vertices/8.5M triangles/0 decode failures; `WTB`/`WTA`/`WTP` textures are a different header revision needing their own parser, 11,125 shipped, plus a new standard DDS RGB24 pixel format found and added to the shared `dds.ts`; CRI `USM` video ported from NieR:A's own module unmodified, with a real confirmed difference — these cutscenes carry real embedded `adpcm_adx` audio unlike NieR:A's silent-video corpus), Dragon's Crown (PS3+PS4, not yet touched), ZOE2/Anubis (PS2, Konami MGS-family — STAGE cipher, PS-ADPCM VOX, stage model container + strip-index layer solved), Chaos Legion + Devil May Cry (PS2, shared Capcom in-house engine/`XAG`-family PS-ADPCM audio driver — TIM2/CLT2 textures, FMV, 3D model+UV/texture-binding, and code-derived audio id→LBA directory tables all solved for Chaos Legion; registered) | `game-re-corpora/flower.md` |
