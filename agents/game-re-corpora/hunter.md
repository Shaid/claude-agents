# hunter — Carrier Command, Hunter, Epic, Frontier: Elite II, Wings, Gunship 2000 AGA, Midwinter, Embryo

**Project root:** `~/Development/hunter`

RNC1 pure-Python decompressor (`tools/hunter/rnc1.py`, byte-verified); Amiga locally-indexed vector-icon chunks; CC's 3D pipeline (transform/project/backface-cull + a confirmed BSP-tree traversal with attribute-byte leaf data, matching the DOS port's format closely) confirmed code-level, plus a live-captured 60-vertex title-screen ship instance (amiberry IPC) **and, as of a later static-only session, a real static per-vehicle model-stream region** (`file+0x3B000`-`0x44000`ish in the decompressed image, never previously disassembled) — a strict recursive BSP-tree+visibility-plane grammar scan (self-terminating parse, zero degenerate faces) found exactly 4 real records there, one of which (`file+0x3D004`, 60 vertices/44 faces) cross-matches the earlier live capture: applying its face list to the already-captured real vertex coordinates yields 0 degenerate/zero-area triangles and a plausible hull silhouette, filling in that asset's previously-empty face list without any further live capture. The same static-only session also mapped a previously-undocumented entity allocation/init subsystem (a 320-byte main entity pool at absolute runtime address `$5FADA`, a 64-byte sub-entity pool embedded per-entity, shared allocators found via a whole-image `BSR`/`JSR`-target scan) but did **not** find vehicle-launch spawn code or a literal `callback_fn` address for the setup-function pointer — that remains the one item needing a live capture (register `A2` at `file+0xB748`'s `JSR (A2)`). CC music is raw signed-8-bit PCM, no header, plus a separate confirmed 4-channel Paula note/instrument (SFX) engine — neither is `disk.2`'s specific reader, which remains open. **Watch out:** the originally-committed `data/explore/CarrierCommand/carrier.asm` disassembles the wrong (RNC1-compressed, not decompressed) file — use `carrier-decompressed.asm`/`.cnf` instead (multi-entry-point `.cnf` seeded at every confirmed routine address; see the amiga.md tooling file's "runtime-populated dispatch table" IRA entry for why single-entry `-preproc` couldn't reach most of it — and see `static-xref-misleads.md` for why "not a valid pointer array" at that same table address didn't mean the bytes there were meaningless: they turned out to be real, uncalled entity-spawn code). FE2 savegame container fully solved (self-keying cipher + zero-RLE) at `docs/formats/fe2-savegame.md`. Shared `amigagames/` WHDLoad library and amiberry configs are reusable across sessions.

Hunter's "OB" 3D object format (Amiga + Atari ST, both platforms share the
byte layout) is fully confirmed code-level: 20-byte header, 4-byte
`[attr][s8 x][s8 y][s8 z]` vertices scaled by a per-object `scaleShift`, an
edge table, and polygon records that reference edge indices (resolved into
a closed vertex ring) rather than vertex indices directly — no separate
"delta/extrusion" section exists (an earlier session's model that assumed
one was wrong; see the correction trail in `docs/3d-object-format.md`).
Verified against 8 named engine routines (`OB_SCAN`/`OB_SETUP`/`OB_XFORM`/
`OB_BBOX`/`OB_EDGES`/`OB_POLYS`/`OB_LINES`/`OB_MATRIX`) in the decrypted
Amiga binary, plus 0 out-of-range vertex indices across 2,873 resolved
polygon rings. The per-vertex `attr` byte and header `effectId` are also
now fully traced: `attr` bits 4-6 (0-2 observed) dispatch a jump table
inside `OB_XFORM`'s rotation branch implementing an articulation/pivot
mechanism for a sub-part that rotates independently of the whole object
(bits 2-3 select the axis); `effectId` gates a per-object 20-byte-stride
effect-parameter interpreter in `OB_MATRIX`, called back-to-back with
`OB_SETUP`/`OB_XFORM` by a real per-object dispatcher. Shared decoder:
`tools/hunter/ob-format.mjs`. Full spec: `docs/formats/hunter-ob.md`.

**Atari ST file landscape — corrected 2026-08-07 after a `re-codebreaker`
escalation.** The disk `Hunter (1991)(Activision)[cr Paper Bag].st` is a
cracked **compilation** disk, not a single-game image — file `100`
(previously documented as "Hunter's main executable, LZH! compressed") is
actually a *different game*, Cybercon III (The Assembly Line/U.S. Gold,
1991), confirmed by credits strings in its decompressed payload. Hunter's
real Atari ST main executable is file `800` (FIRE-compressed, depacks to
71,684 bytes, loads at `$800`; HUNTER.TOS's own boot chain confirms this).
FIRE is a **backwards LZ77 with escalating fixed-bit-width code ladders**
(literal-run/offset/length, three small constant tables) — despite the old
docs, there is **no Huffman table anywhere**; working decoder
`tools/hunter/fire-depack.py`, transcribed instruction-for-instruction from
the depacker embedded in `HUNTER.TOS`. The root-cause diagnosis for the
whole file-100-vs-800 mixup — a load-base-vs-random-baseline test — is now
its own lesson: `confirmed-call-target-off-instruction-boundary.md`.

**Every numeric filename on the disk is a resource *number*, not an
arbitrary label — a second `re-codebreaker` escalation (2026-08-08) found
Hunter's own 22-entry file descriptor table inside file `800`** (32-byte
stride, one entry per file `00`-`15`: track/length-in-longwords/flags/
content-type/24-byte original dev path — e.g. `A:main`, `A:\externs\
objfile`, `A:\externs\musfile`), which named every file's real role and let
every declared length be checked against the actual file (20/21 exact). This
overturned two file identities a prior pass had gotten wrong from
filename/content sniffing alone: files `10`-`15` (previously "entity/object
template definitions" for `rob`/`Allied HQ`/`ally stores`/`fuel dump`) are
actually Hunter's **six save-game slots** — those strings are live
world-state text copied from game RAM at save time, identical across saves
because the six snapshots came from nearly the same world, not because
they're a shared template; and file `00` (previously "Martin Walker's sound
driver plus its embedded sample bank," on the strength of real
instrument-name strings inside it) is actually an **unused developer RAM
dump** — the real, loaded sound files are `04` (the YM2149 driver) and `03`
(a GEMDOS-PRG-shaped module carrying the replayer + sample bank); `00`
merely happens to contain a snapshot that includes a copy of both, plus a
copy of the save directory, which is why the instrument strings and
`rob`/etc. strings both showed up in it. Two checksum algorithms were
reverse-engineered and verified byte-exact on every real file
(`CHKSUM_SAVE`/`CHKSUM_SAP`: seed a 16-bit accumulator, overwrite the
checksum field with a fixed placeholder, sum every big-endian word — 9/9
files matched). **Lesson for cracked/compilation disks generally:** don't
trust a numbered/generic filename's role from content-sniffing or an
in-file string match alone when the game's own file-descriptor table (or
equivalent) is findable — see `crack-redirects-io-to-resident-loader-stub.md`
for why the loading code for these files was so hard to find in the first
place (the crack redirects it into a *different*, resident binary). The
escalation's own verifier is a good regression check to promote:
`docs/data-format-reference.md` §2.8 names its script; re-run it before
trusting any future change to file `800`'s parsing.

**Cross-platform anchor-matching mapped Hunter's whole "OB" 3D-object
subsystem from the confirmed Amiga binary onto the (structurally
unrelated-looking) Atari ST binary in one pass** — an 8-byte sliding-window
index technique, generalized and added to `cross-platform-decode-oracles.md`
("Scaled-up version" paragraph). Both platforms load their main executable
at the same base (`$800`) and compile from one shared source per developer
interviews, so most of the OB rendering subsystem is byte-identical between
platforms modulo a per-region relocation offset.

Epic (Ocean, 1992, Amiga — flight combat, not Epic Games): `.3D`/`.IGD`
objects are **not** a face-record array — an initial same-session pass read
them that way (variable-length "face" records + an interleaved "hardpoint"
type) and got a plausible-looking but wrong grammar; a `re-codebreaker`
escalation found the real structure by disassembling the game's own model-
compile pass (`EPIC.asm`, full-hunk IRA disassembly): a 3-parallel-array
header (`lod[]`/`type[]`/`offset[]`, one entry per LOD section) followed by,
per section, `vertex_count` (stored in the file — an earlier pass wrongly
concluded it wasn't recoverable) then a vertex table then an **executable
display-list bytecode** (25 opcodes: polygons, a perspective-scaled-disc
primitive, jumps/calls, and conditional skips used for a per-octant
backface-cull decision tree — the "hardpoint" reading was opcode 21, a
backface test, not a data record). Verified with 0 unexplained words across
all 28 known `.3D`/`.IGD` files, 85/85 section-chain boundaries and 245/245
skip-target alignments — reference parser `tools/epic/epic_oplist.py`,
full spec `docs/explore/Epic/epic-3d-format.md`. Lesson: see
`second-record-type-shifts-primary-counts.md` and, more importantly, treat
a "second record type that almost-but-not-quite fits" as a signal to
re-audit the *primary* grammar (count location, base offset, record shape)
before inventing a new record type — three separately-plausible wrong
premises compounded here. Separately confirmed and still standing: the
game's real 16-colour RGB4 palette lives byte-identical across all 25
`.IGD` files, not the executable (which has no CPU palette-upload loop —
see `palette-storage-quirks.md`); a `.LBM`-extension file family is a
custom raw `[palette][bitmap]` layout, not IFF ILBM (see
`familiar-extension-not-proof-of-standard-format.md`); `.3DL` container's
section count and DEATHTAB.3DL's offset directory are confirmed; GR3D2
renders as a real gradient image at a confirmed width via autocorrelation.
Open: display-list colour-argument resolution (indices into a runtime-
patched stride table, not necessarily the palette directly), `.3DL` LOD
header-length semantics, GR3D3/5/19/20 — see `docs/explore/Epic/TODO.md`.

Wings (Cinemaware, 1990, Amiga — combat flight, WHDLoad-installed overlay
executable): fresh-start session cracked Cinemaware's custom `.BOLT` asset
archive format from scratch (no public spec existed anywhere — see
`docs/explore/wings-zeewolf-hunter-web-research.md`). The container's real
directory (magic `"BOLT"` + `u16` entry count + 12-byte-stride entries) is
**not at file offset 0** — it's located via the file's own last 4 bytes
read as a big-endian file-offset pointer (verified 0 deviations across all
11 shipped `.BOLT` files; see `trailer-offset-locates-real-header.md`).
Directory entries pack a 1-byte flags/8-bit-type-tag + 24-bit value twice
per 12-byte record; `flags0` bit 0 distinguishes GROUP entries (whose
24-bit fields are a literal, code-confirmed `[offset,length)` byte range in
the file, contiguous/gapless across 359 entries in 11 files, 0 deviations)
from FRAME entries (a *different*-unit nested running-sum chain — internally
0-deviation self-consistent but NOT bytes-within-the-group for multi-frame
groups, see `self-consistent-chain-wrong-unit.md`, the general lesson this
session produced). Exactly one extra, uncounted 12-byte entry always
follows the declared table (structurally confirmed 11/11 files). 4 of 357
group blobs are standard IFF FORM/8SVX instrument samples (confirmed via
`file(1)`, byte-identical extraction, `tools/wings/extract-wings-audio.py`)
— named `Motor8K.snd`/`Piano2.iff`/`Horns1.iff`/`Strng2.iff`, matching
readable instrument-name strings elsewhere in the executable. Format
cracked entirely from the executable's own `LoadBoltGroup`/`OpenBoltLib`
routines (hunk0 CODE+0x7590/+0x6c0c) — `WingsHD.s` (the WHDLoad slave
source, the only public code touching this game) turned out to contain
**no** `.BOLT`/data-structure information at all despite web research
flagging it as the best lead; it only patches `Open`/`Lock`/`LoadSeg`.
`Wings` itself is a `blink OVERLAY`-style multi-segment executable (7
hunks/5 physical load units) that defeated both a hand-rolled hunk parser
and IRA outright — see the amiga tooling doc's `HUNK_OVERLAY`/`HUNK_BREAK`
entry, worked out this session via `amitools.binfmt.hunk.HunkReader`.
Shared decoder: `tools/wings/bolt_parse.py`. Full spec:
`docs/explore/Wings/data-structure.md`.

**Follow-up session cracked the Mode-B group compression codec** (a
hand-rolled LZ-style scheme, `LAB_66B0`/hunk0 CODE+0x66b0: 1024-byte ring
buffer, 3 copy directions including a byte-*reversed* "mirror" mode
plausibly for symmetric sprite art, 9 control-byte ranges each trading off
distance/length bit budgets) — see
`jump-table-longword-entries-misdisassembled-as-branches.md` for how its
dispatch table was derived (IRA mislabeled 2 of its 16 raw-address slots
with wrong branch-target names). Verified 0 leftover bytes decoding all 352
real Mode-B groups to their directory-declared total length, and
independently confirmed by rendering a single bitplane (no palette needed)
of a `flags1=0x05` frame, which read "WINGS" — the title-logo art. Also
cracked `pilot.dat` (the save file): a 41×88-byte "hall of fame" pilot
roster under a trivial per-byte bit-rotation cipher (key = a header field
mod 8) plus a sum+XOR checksum, both confirmed byte-exact — see
`high-entropy-trivial-cipher.md`'s Wings addendum. A prior session's claim
that a specific trampoline call was DOS `Read()`/`Write()` was wrong (it was
a `TestBit` helper); see `trampoline-role-guessed-not-resolved.md`.

**Third session decoded `flags1=0x12`** (Amiga-blitter-driven sprite
content, 36% of all frames, the single largest bucket) end to end —
**and, via a `re-codebreaker` escalation, found and fixed two real bugs in
the "confirmed" Mode-B codec itself**: back-reference distances are
*relative* (`(curpos-distance) & 0x3FF`), not absolute window positions as
the prior session's citation claimed (see
`resume-entry-citation-drops-setup-arithmetic.md` for exactly how that
citation went wrong), and control range `0x90-0x9F` copies *forward*, not
backward. Both bugs corrupted copy content while conserving byte counts
exactly, so the codec's only prior verification (0 leftover bytes,
352/352 groups) could never have caught them — see
`length-invariant-blind-to-copy-semantics.md`, the general lesson this
produced. Fixed, `flags1=0x05` went from 17/21 to 21/21 and `flags1=0x12`
from 162/932 (a wrong per-offset-scan fit to corrupted bytes) to **932/932
(100%)**, with legible renders (a pilot-ability-scores panel with text and
bar gauges, a "REVIEW PILOTS" menu button, WWI biplane sprites). Decoder:
`tools/wings/bolt_decompress.py`; classifiers/renderers:
`tools/wings/classify-and-render.py` (screens),
`tools/wings/render-blitter-sprites.py` (sprites). Extractor:
`tools/wings/extract-pilot-dat.py`. Open (at that point): the real Amiga
palette (5 search angles tried, all negative), `flags1=0x06`/`0x0a` content
semantics, `pilot.dat`'s per-slot stat-byte write sites, `HUNK_OVERLAY`'s
residual 24 bytes, `OSEmu.400`.

**Fourth session solved both of that session's headline open items.** The
real Amiga **palette** was found by re-running the same corpus-wide RGB4-
shape scan against the now-*corrected* Mode-B decoder (the prior negative
predated that session's own codec bugfix — every candidate byte range it
checked was corrupted) — see the second instance in
`length-invariant-blind-to-copy-semantics.md`. `flags1=0x00` (previously
just "self-referencing header+payload struct," 29 real corpus frames) is a
32-entry Amiga RGB4 colour table, `[u32 count][u32 self-patched
pointer][32x u16 RGB4]`, one per screen/context (not one shared global
palette — OCS's 32-colour-per-screen limit makes a per-context palette the
sane design). Verified decisively: rendering the already-confirmed "WINGS"
title-logo bitplane with its adjacent same-group palette frame produces a
fully legible, correctly-composed real Amiga title screen, independently
cross-checked against a real third-party screenshot (`lemonamiga.com`).
21/21 confirmed `flags1=0x05` screens and 503/932 `flags1=0x12` sprites
(the rest lack a local palette frame in-group) now render with real
colour. Shared decoder: `tools/wings/bolt_palette.py`.

**`pilot.dat`'s stat-field write sites were solved via `re-codebreaker`,
and the escalation found the prior sessions' "confirmed" record layout
itself was wrong by 46 bytes** — the classic case this session's
`leading-header-equal-to-field-offset-masks-record-start.md` lesson
generalizes: a record boundary "confirmed" only by a name string landing
on `slot*88+46` is arithmetically blind to "header of 46 bytes, name-first
record" vs. "no header, name at record-relative +46," since both predict
the identical absolute name position for every slot. The real layout: a
46-byte file header, then 41 name-FIRST 88-byte records (3 sub-arrays:
staging/table-A-squadron/table-B) starting at body+46. The stat-generator
routine (`LAB_348E`, hunk3 CODE+0x348e) is now fully confirmed —
byte-exact against DATA-hunk constants for a hardcoded roster entry, plus
a 180-predicate/0-deviation structural-invariant check on the generator's
implied arithmetic (`tools/wings/verify-pilot-generator.py`). Extractor
`tools/wings/extract-pilot-dat.py` updated to the corrected layout.

Still open, low priority: `flags1=0x12`'s minor struct fields (`+2/+3/+4/
+10/+12/+24`) — this session confirmed exhaustively that the LOAD handler
never reads any of them, so their consumer (if any) is an unfound separate
DRAW/composite routine; the palette's own hardware-application mechanism
(very likely a self-built Copper list, given a `MOVE.L ...,COP1LCH` write
found this session, but the code that populates it from a `flags1=0x00`
frame wasn't isolated); `HUNK_OVERLAY`'s residual 24 bytes; `OSEmu.400` —
see `docs/explore/Wings/TODO.md`.

**Fifth session tested and refuted a "Wings has a hidden 3D vertex/polygon
model format" hypothesis** (motivated by ground-truth knowledge that Wings'
main gameplay loop is true 3D dogfighting, unlike the top-down-bombing and
isometric-strafing modes) — `flags1=0x06` ("composite struct", 516 frames,
20% of the corpus) was the natural suspect (3 internal pointer fields
patched at load time, structurally resembling CC's `callback_fn +
vtx_program + face_list` model header). A corpus-wide pointer-target
census (**516/516 frames, 0 exceptions**) instead shows it's a fixed
30/54-byte **2D animation/cel-sequencing linked-list node**: one pointer
field is a literal "next frame" link (83% of active instances are exactly
`self+1`) resolving 100% of the time to another `flags1=0x06` node, a
second is a "shared context" link also always to another `0x06` node, and
the third resolves 100% of the time to a `flags1=0x12` sprite (the
already-fully-confirmed 2D blitter format) — **zero** connections to
`flags1=0x0a` (the type that would hold a vertex/index array) anywhere in
the corpus. Code-side corroboration: 0 occurrences of `MOVEM.W (An)+`
(CC's vertex-stream-read shape) and no perspective-divide-shaped `DIVS.W`
anywhere across all 5 disassembled hunks (~218K lines) — but a genuine 3×3
rotation-matrix build+apply routine *does* exist (hunk4 CODE+`0x10668`/
`0x10752`, same `MULS`+`ASR`+`ADD` dot-product shape CC's confirmed corner-
rotation code uses), rotating only a small fixed 16-point instrument-gauge
shape (compass rose/attitude indicator) by a heading angle — real 3D math,
scoped to cockpit instrumentation, not exterior vehicle/world geometry.
Independent supporting evidence: `DDD.BOLT` (previously an unexplained
filename) is 89% `flags1=0x12` sprites including a clean monotonic
12-frame size-scaling bank of the same subject, confirmed via a real
recovered palette to be a WWI biplane — consistent with Wings achieving
"3D" dogfighting through **scaled 2D sprite banks** rather than real-time
polygon rendering, though the runtime frame-selection code (which picks a
sprite by computed range/bearing) wasn't traced. See
`docs/explore/Wings/data-structure.md`, "`flags1=0x06` composite struct
(CONFIRMED — 2D animation-chain node, not a 3D model)".

Gunship 2000 AGA (MicroProse, 1993, Amiga AGA port, JOTD WHDLoad): fresh-start
project, docs at `docs/explore/Gunship2000AGA/` (`data-structure.md`,
`TODO.md`). Load chain is 3 cooperating executables (`Gunship 2000` bootstrap
-> `gs` main flight-sim engine, MANX-compiled, 131 tiny hunks -> `gs2.run`
front-end/menu). `.PIX` screens are RNC1-compressed standard IFF ILBM (320x200
8-plane AGA, this project's existing `tools/hunter/rnc1.py` decoder reused
unmodified) — fully confirmed both structurally (0 deviation across 67 files)
and via the game's own embedded RNC1 unpacker traced end-to-end in `gs.asm`.
`flight.cat`/`object.cat`/`gs2end.dat`/`gs2frt.dat` share one directory-then-
payload catalog container (u16 count + fixed 24-byte name/reserved/length/
offset records, contiguous payload, 0 deviation across 257 entries/4 files) —
code-confirmed against `gs.asm`'s own loader/lookup routines. `roster.dat` is
7 fixed 296-byte flight records; rank/status/missions/score/self-index fields
confirmed by disassembling the game's own "DUTY ROSTER" UI code (not a
third-party editor, which was blocked by an Aminet-hosting outage) — several
fields remain open, blocked on a live amiberry capture of an MIA/medal event
(not attempted, needs explicit user permission per this agent's hard gate).
Sound: `flt_snd.bin` is raw signed-8-bit PCM (audio.device-driven, variable
pitch via a runtime accumulator, no fixed sample rate); `fe_snd.bin` is a
self-contained 4-channel Paula SFX engine (7 trigger stubs, one per dispatch
thunk in `gs.asm`, exact 14-byte-stride offsets `0x00/0x0E/0x1C/0x2A/0x38/
0x46/0x54`) with its own portamento pitch synthesizer (floors at the
hardware-minimum period 124) — the trigger-ID -> waveform-byte-offset chain
is fully resolved end-to-end (dispatch table -> instrument template table ->
waveform-pointer table -> raw sample bytes), but the exact seed/step
accumulator values (needed only for precise Hz, not for locating samples)
remain untraced, characterized as low-value. `gs.asm`'s `.cnf` had two
separate `-preproc` code-as-data misclassifications, both fixed by hand-
merging fragmented `CODE` islands (same technique as `game-re.md`'s "runtime-
populated dispatch table" Amiga tooling entry): the roster-UI region, and a
sound-trigger-dispatch region — the second fix revealed the fragmentation
issue recurs elsewhere in the same 435 KB binary even after ~430 pre-existing
narrow `CODE` ranges (see `committed-ira-asm-silent-coverage-gap.md`'s
"many islands" variant). `gscopy` (a bundled disk-copy/install utility) and
`FONTS/gsfnt*.font`+`FONTS/GS2000/*` (standard AmigaOS `FontContentsHeader`/
on-disk `TextFont` bitmap fonts) are both confirmed structurally, closing out
this project's "unexamined files" item — `gscopy`'s strings are stored
byte-reversed per fragment, a trivial anti-`strings`-scan trick (see
`reversed-text-fragment-anti-strings-trick.md`).

Midwinter (Rainbird/Microprose, 1989, Amiga — open-world skiing/combat
survival game, designer Mike Singleton; not Epic/Midwinter developer "The
Edge"): fresh-start session, docs at `docs/explore/Midwinter/`
(`data-structure.md`, `TODO.md`). `Disk.1` is a raw "NDOS" custom track image
(129 tracks x 5,120 bytes, no AmigaDOS filesystem) — track size confirmed
three independent ways (file-size arithmetic; the WHDLoad slave's hardcoded
`$1400` load-geometry constants; and the *real, unpatched* track-0 boot
code's own `MOVE.W #$1400,D0` plus a `$4489` DSKSYNC write, i.e. a hand-
rolled raw-hardware trackloader bypassing `trackdisk.device` entirely).
Exactly two `HUNK_HEADER`-magic hits exist on the whole disk (byte-scan): a
28 KB single-CODE-hunk loader at `file+0x1400` (track 1) and a 183 KB
single-CODE-hunk main executable at `file+0x33996` (track 41.28, not
track-aligned) — both are "hunk-shaped blobs" read by a hardcoded 32-byte
header skip, not real hunk parsing, confirmed by the WHDLoad slave's boot
stub jumping to exactly `load_address + 0x20` and the real boot code
reproducing the identical load-then-jump sequence independently. The main
executable carries no DATA/BSS hunk, consistent with a resident engine that
streams game data from scattered tracks on demand rather than one static
data segment. Save file `df0:midsave0` (a normal AmigaDOS device-path open,
distinct from the NDOS main-disk loader) was found as a literal string, but
no save file was provided this session so its layout is undecoded. 3D/terrain
data is **not yet cracked**: a 22-byte fixed-stride record run with a
constant tag word and nibble-quantized fields was found at one narrow
`file+0x93878`-`0x93954` span (track 118) but is unverified against any
oracle, and the bulk of the disk (~176 KB between the loader and main exe,
~144 KB after it) resisted both chunky-bitmap rendering (7 widths) and an
int16-smoothness check — open, see `TODO.md`. The installed WHDLoad slave is
StingRay's v2.2 recode, whose own changelog says it consolidated an
originally-2-floppy release into this single disk image — treat "not found
on `Disk.1`" as inconclusive, not "absent from the game," until that's
settled.

Embryo (Beyond Arts/Black Legend, 1994, Amiga — 3D shoot-em-up, Croatian
developer; "EmbryoHr" is just the TOSEC `Hr` language tag, not a person):
fresh-start session, docs at `docs/explore/EmbryoHr/` (`data-structure.md`,
`TODO.md`) — genuinely unbroken ground, no public RE existed anywhere for
this game beforehand. Cracked the container format wrapping ~all data files
(`.pic`/`.mp`/`p60.*`/`miss*`/`Kraj*`/`Fly*`/`link*`/`Intro*`): it's the
well-known **Crunch-Mania ("CrM2"/"Crm2") LZH cruncher**, but the loader
XOR-obfuscates the first 14 header bytes with 4 fixed constants
(`0x13132e59`/`0xfacd`/`0xdeadface`/`0xfadeabcd` over the magic/field4/
unpacked-len/packed-len fields) so the real "CrM2" magic never appears in a
raw scan — it shows as "PaCk"/"Pack" instead. Found by disassembling the
loader's own file-read routine (IRA, single-CODE-hunk executable, default
pass), then cross-checked independently: de-XOR one file's header, write it
out with the original payload unchanged, and `ancient identify`/`decompress`
(already vendored at `tools/hunter/ancient`) recognizes it as genuine
Crunch-Mania and reproduces the exact decompressed length recorded in the
(still-obfuscated) on-disk header — 114/115 files, 0 deviations. The one
exception (`Intro03`) is explained by the executable's own embedded **file
catalog** (a found-for-free 80-record, 16-byte-stride directory at
`Embryo+0x506c`: 1-byte loader-dispatch type tag + 1-byte disk number [1-5,
confirmed byte-exact against the WHDLoad install script's per-disk file
lists] + 14-byte `/`-padded name, with `miss`/`missc`/`link`/`linkc` present
only as un-numbered template stems the loader suffixes at runtime) —
`Intro03`'s type tag differs from its siblings', meaning the loader takes a
different, non-CrM2 path for it specifically. 119/122 catalog entries
(expanding templates) match a real shipped file; the 3 that don't are all
explained (a deliberate blank separator record, `ger.txt` since this
package is the non-German release, and an unused `stores.pic` name). Inside
the decompressed corpus, `Kraj05`/`06`/`07` (the ending sequence) turned out
to be genuine standard **IFF `FORM ILBM`/`FORM ANIM`** (a non-standard
`COLS` chunk — 2 bytes/colour native 12-bit RGB — in place of `CMAP`,
otherwise standard; rendered `Kraj05`'s static first frame end-to-end to a
legible Earth-from-orbit globe image), and `Fly02`/`FlyN02` each embed a
genuine **IFF `FORM 8SVX`** sample (`NAME`="PROTUAVIONAC.SMPL", Croatian for
"anti-aircraft [sample]"; `ANNO`="Protracker 3.15" — independently
confirmed by `file(1)` itself). Also confirmed: the main executable
`Embryo` is **loader-only** — zero blitter-register references anywhere in
its disassembly — so the real texture-mapped 3D engine (and thus the exact
width/height of the `.pic` level-background textures, still undecoded
despite a clean palette-shaped 32-entry header) lives in a separate,
not-yet-located executable, almost certainly loaded from one of the
still-uncharacterized large blobs (`Kraj02` and/or `miss*`/`link*`, which
show code-shaped/sparse-offset-table structure respectively). Shared
decoder: `tools/embryo/crm2.py`; catalog extractor:
`tools/embryo/parse_catalog.py`; promoted pipeline:
`tools/embryo/extract_embryo_data.py`. See `docs/explore/EmbryoHr/TODO.md`
for the full open list (`.pic`/`.mp`/`p60.*`/`missc*`/`linkc*`/`miss*`/
`link*`/`Kraj00`-`02` all still open — none escalated yet, the highest-value
next step is finding the real engine executable, which would likely settle
several of these in one pass).

Zeewolf (Binary Asylum, 1994, Amiga — helicopter combat, Zarch/Virus-lineage
rendering): fresh-start session cracked `Disk.1`'s undocumented custom
trackloader disk layout from scratch (no public spec — only a WHDLoad
install ReadMe describing, not specifying, a "longtrack" protection). The
disk (901,120 bytes, standard AmigaDOS DD capacity, `"DOS\0"` bootblock but
**not** a real AmigaDOS filesystem — root block position holds real data,
not a valid OFS/FFS root) boots via a hand-rolled loader: block 0/1's code
does two `AllocMem()` calls (0x48000 bytes each, one MEMF_CHIP one MEMF_ANY)
with chip-mem-size-dependent load-address arithmetic, then a **4-file
boot-time catalog** embedded in the boot code itself (32-byte records:
11-byte 8.3-style name + record index + reserved + flag byte [0x80=more
follow] + 8x consecutive `u16` LE logical-block numbers; `block*512` = a
direct byte offset into the flat image, confirmed via real 68k code/English
text at every boundary; a whole-disk scan for the exact record shape found
only the 43 hits belonging to these 4 files, confirming no second catalog
of this shape exists anywhere else). `STARTUP.68K` (blocks 4-272, ~134 KB)
is the headerless main executable (no `HUNK_HEADER` at all — a byte-
classification scan found ordinary embedded UI strings, no `HUNK_DEBUG`
source fragments). `WOLFNEW.DAT` and `TITLE.MOD` share an unresolved
pointer/parameter record grammar (a small set of ~10-15 distinct clustered
`0x0001xxxx`-range values recur heavily across both files, structurally
reminiscent of Carrier Command's `callback_fn`-headed entity records but
**not** semantically confirmed — the dynamic `AllocMem`-based load address
means these can't be resolved to real code offsets without a live capture
or a loader-relocation trace). `TITLE.MOD` and `TITLE.DRV` are both
confirmed **not** what their extensions suggest (no IFF/ProTracker module,
no device driver — see `familiar-extension-not-proof-of-standard-format.md`):
both hold a mission-briefing text database (byte-exact 3-byte tag `0x0C
0x00 0x08` precedes 94/95 real "Mission " occurrences disk-wide) that starts
partway through `TITLE.MOD`'s own catalogued range and continues seamlessly
past the catalog's declared end into un-catalogued disk space with no
transition marker — see the new `bootstrap-catalog-boundary-not-content-
boundary.md` lesson this produced. The disk's last 264 blocks (132 KB) are
confirmed **not** game data at all — a synthetic 4-byte-stride counter fill
pattern that a naive entropy/byte-diversity sweep initially misread as real
content; see the new `patterned-fill-defeats-naive-entropy-scan.md` lesson.
No 3D vertex/polygon model format was found this session (checked
explicitly, both structured resources examined show the pointer/parameter
grammar above, not a CC/Hunter-OB-style small-signed-byte vertex shape).
Open: blocks 369-1495 (577 KB, ~64% of the disk) are real but uncatalogued
content of unknown structure — the primary target for a follow-up session;
`WOLFNEW.DAT`/`TITLE.MOD`'s record grammar; full `STARTUP.68K` disassembly;
no music/sound file identified yet (no standard IFF audio magic anywhere on
disk). See `docs/explore/Zeewolf/data-structure.md` and `TODO.md`. Music/SFX
for both Zeewolf games confirmed **Allister Brimble** (a prior Adrian
Cummings attribution was checked and is wrong).
