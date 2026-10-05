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

**Sixth session traced the runtime frame-selection code the fifth session
left open** — `DDD.BOLT` is file ID 6, loaded only by hunk4 (the dogfight-
mode overlay) at 2 call sites. Found a real, code-confirmed 3×3 world-to-
camera rotation + dual perspective-divide pipeline (hunk4 CODE+`0x1129a`,
overturning the fifth session's own "no perspective-divide anywhere"
negative — the earlier `DIVS` grep window was simply too narrow) feeding a
discretized "closing" state machine that drives the already-confirmed
12-frame zoom-scale bank with 0 slack against its clamp range. Also traced
the shared blitter draw routine (hunk0 CODE+`0x7c8a`, resolved via the
project's A4-trampoline formula) that every sprite-draw call site funnels
through. See `docs/explore/Wings/data-structure.md`, "DDD.BOLT enemy-plane
sprite-selection pipeline".

**Seventh (follow-up) session corrected a subsequent summary that
overstated confidence** ("we understand how dogfight mode works" was true
only of sprite *selection*, not screen *composition*) — traced forward
from the same confirmed call sites and found DDD.BOLT's group 42 is
mixed-purpose, not a pure enemy-plane bank: the previously-unexplained
"tunnel/hangar-interior" frames (idx 49-59) are **static cockpit canopy-
strut/window-frame HUD chrome**, confirmed by call sites that push a
literal `(0,0)` position (letting each frame's own baked-in anchor place
it) and by the same two frames being blitted into *both* halves of the
double-buffered display once at dogfight-mode init (drawn once, never
redrawn — the standard Amiga trick for unchanging content); a small
crosshair/gunsight reticle (idx 72) is drawn the same way; and a pilot
head-turn portrait sub-bank (idx 100-111) turned out to be a **proximity-
triggered scripted "close pass" reaction cue** (a real bounding-box test
against the tracked enemy position kicks off a state sequencer that also
draws a small close-range biplane-detail sub-bank), not a continuous
player-driven look-around mechanic. Also found (not fully closed) a
likely resolution path for the long-open palette-hardware-write question:
a real per-colour fade routine and a `SetColour`-shaped hunk0 helper
(CODE+`0x8750`). **Still open:** which specific asset (if any) the
confirmed general-purpose full-`BitMap` blit call actually draws as the
sky/world backdrop (the `BitMap*` pointer it reads is populated by
generic, non-DDD-specific hunk0 code, not traced back to its trigger), and
whether the player's own plane/cockpit exterior is ever rendered (no
evidence found either way — absence-of-evidence, not confirmed absence).
Both are flagged as needing a live amiberry capture, not attempted this
(static-only) session. The "2D scaled sprites, not real 3D" conclusion is
reaffirmed, not undermined — see `docs/explore/Wings/data-structure.md`,
"Dogfight screen composition", and `docs/explore/Wings/TODO.md` for the
itemized open list.

**Eighth session, triggered by 3 user-supplied Amiberry `.uss` savestates +
screenshots (parsed offline, no live emulator), found the "2D scaled
sprites, not real 3D" conclusion above was too broad**: the dogfight
ground/sky visual is a genuine, code-confirmed **live polygon renderer**,
not a static asset or a sprite. A fixed world-space quadrilateral (hunk4
CODE+`0xddd6`) is rotated by the same heading/pitch/roll triple and
rotation-matrix routine (`LAB_10668`, CODE+`0x10668`) previously thought
scoped only to the small cockpit compass gauge, projected via a point-
transform trampoline, clipped against the viewport with a real
Sutherland-Hodgman-style algorithm (CODE+`0x10264`), and its edges drawn
with hand-written octant-specialized Bresenham EOR line rasterizers
(CODE+`0xf886` etc.) — plus a separate Amiga-blitter flat-colour fill
(CODE+`0xf698`, real `BLTCON0`/`BLTCON1`/`BLTSIZE` register writes) for the
solid ground/sky split underneath the lines. This resolves the session's
long-open `wings-ddd-backdrop-asset` mystery (the backdrop isn't a loaded
BOLT frame at all) and narrows the enemy-plane sprite-scaling finding to
what it was actually shown to cover: the enemy plane and all HUD/cockpit
chrome are still 2D sprite art, but the ground/horizon element is real,
live 3D geometry. **Two generalizable technique findings** came out of the
savestate work: recovering a hunk's runtime load address via byte-signature
matching against inflated savestate RAM chunks (works cleanly, 0
deviation across all 3 saves), and a real gap — the `"CPU "` savestate
chunk's internal layout could not be reverse-engineered this session (see
`game-re-tooling/amiga.md`'s "Offline `.uss` savestate analysis" section),
so the whole finding is a **static-disassembly-confirmed mechanism**,
cross-checked only indirectly against the screenshots' visual content, not
a live-PC-confirmed trace.

**A follow-up (offline, still no live emulator) session then closed both of
that gap's two open pieces.** Disassembling the shared trampoline landing
pad (hunk0 CODE+`0x907C`/`0x908E`) found it's the AmigaDOS/`blink`
`OVERLAY`-linker's own lazy-binding resolver (`OpenLibrary("dos.library")`
+ `Seek()`+`LoadSeg()` + self-modifying-code patch), not projection code —
and byte-inspecting the two ground-renderer trampoline slots' own 8-byte
hunk1 metadata (`[BSR.W cascade][1-byte segment#][3-byte BE hunk-relative
offset]`) resolved them to real, previously-undisassembled hunk4 targets: a
full 3×3-rotate-plus-perspective-divide projection routine, and a *second*,
independent hardware-blitter line-draw-mode setup distinct from the CPU/EOR
rasterizer. Separately, the `"CPU "` chunk format was fully cracked (not
just gapped-around) by fetching `tonioni/WinUAE`'s and `midwan/amiberry`'s
(exact `v8.2.2` tag) `newcpu.cpp` and hand-deriving `save_cpu()`'s byte
layout per CPU model — the chunk is a **68060** (not 68030) dump, whose
128-line/4-way split I+D cache arrays make it ~22.7 KB, an exact byte-count
match confirming both the model and the field layout simultaneously; all 3
savestates' extracted PC lands outside every Wings hunk (`$4FF8xxxx`-
`$4FFAxxxx`), a genuine finding (these captures land inside WHDLoad's
`OSEmu` resident interrupt-trap layer, not Wings' own code) rather than a
decode failure.

**A further LIVE session (amiberry MCP, explicitly user-approved) then
tested the whole mechanism against a running emulator** — and got a clean
split result. **Worked decisively**: reading real emulated RAM at the
ground-fill FULL/PARTIAL config global (`-10322`/`-10324` off the confirmed
small-data base, itself independently re-verified live at all three
savestates as `$00012346`) while the emulator sat paused at each of the 3
supplied captured moments gave a byte-exact match to the doc's own
FULL/PARTIAL constants (`default-9`=PARTIAL, `default-10`=FULL,
`default-8`=uninitialized/non-dogfight-scene), upgrading that mapping from
plausible-inference to live-confirmed. The live-debugging *attempt* itself
also motivated a closer static re-read of the ground-quad setup routine
that found real structure two prior sessions' summaries had glossed over:
it internally calls the second (hardware-blitter) line rasterizer 3
separate times with distinct coordinates, directly confirming the two
rasterization mechanisms genuinely co-occur in one call chain rather than
being alternate paths. **Failed instructively**: breakpoint-based
execution tracing (the task's primary suggested method) hit a real,
twice-reproduced tooling wall — `resume_emulation` with any breakpoint
armed permanently kills the amiberry IPC socket even in the previously-
documented "safe" call order, and `debug_continue` alone doesn't reliably
advance a CPU that's paused inside a WHDLoad/OSEmu interrupt-wait loop
(interrupts likely freeze along with scheduling while paused) — see
`amiberry-live-capture-workflow.md`'s sharpened breakpoint bullet for the
generalized lesson. See `docs/explore/Wings/data-structure.md`, "Dogfight
screen composition" §§7-8 (§8 is the LIVE-DEBUGGED session, clearly marked
off from the static-only work above it), and `docs/explore/Wings/TODO.md`.

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

**A follow-up static-only session (amiberry explicitly banned by the repo
owner for this and future sessions) resolved that consolidation doubt and
unblocked the main-executable work.** The scanned manual's own "SAVING AND
LOADING GAMES" section, the installer ReadMe's singular "disk", and
independent community text all agree the single-disk release genuinely is
the complete game — so a future "not found on `Disk.1`" finding should now
be read as really absent, not as evidence of a missing second floppy. The
long-blocking "no runtime<->file-offset mapping for `mainexe`" gap is also
closed: the installed WHDLoad slave's hardcoded patch-target addresses plus
its `jmp $800.w` boot-stub entry point are a free, verifiable oracle for
this (see the sharpened `whdload-slave-no-format-info.md`) — 5/5 addresses
confirm `runtime_address = file_offset - 0x331B6`. Applying it converted
the previously-promising 22-byte fixed-stride record run at
`file+0x93878`-`0x93954` (track 118, nibble-quantized fields, a plausible
height/slope-table candidate) to a runtime address past `mainexe`'s own
CODE hunk end, meaning it isn't statically resident there after all, and
converted a "middle region" candidate to a negative runtime address
entirely (ruling it in-mainexe out too) — both real, if deflating, findings
rather than an extraction bug. `mainexe.asm`'s own IRA refine pass remains
genuinely blocked in this environment (the `ira` binary isn't present on
this filesystem, checked at every path a prior session used it from).
Terrain architecture is narrowed, not solved, but more substantially now: a
whole-disk structural scan found 16 real instances of a `[u16 N][N×u32
offsets][W][H]+nibble-stream]` sprite/image container — the SAME container
shape independently derived for Midwinter 2's `.cmp`/`.bin` (below) —
spanning most of the previously-unclassified ~320 KB (`file+0x309e`-
`0x946a4`), and a Ghidra-traced `mainexe` on-demand disk resource loader
(`FUN_0000d82c`, a 16-byte-record `(track, offset, length)` table) cross-
confirms 5/16 of those containers by exact `(track, offset)` match, with no
heightmap-shaped record found among ~65 sampled table entries — real,
code-level evidence for "procedural, not stored," on top of the earlier
capacity argument. This also resolved the `ira`-binary-unavailable blocker
for `mainexe`: a Ghidra-equipped `amiga-disasm` agent (its real multi-hunk
HUNK loader, not IRA's forced-single-`CODE`-range `.cnf` trick) reached the
loader without needing `ira` at all. The pixel codec inside those 16
containers is itself not yet decoded (expected to transfer directly from
Midwinter 2's own now-solved `.cmp`/`.bin` nibble-RLE codec, below — same
container shape, byte-identical codec unconfirmed). Separately, a
`strings`-style NUL-delimited scan found a genuine narrative-text island
packed directly inside `mainexe`'s own CODE hunk (`file+0x55a2a`-`0x5a850`
— consistent with "no separate DATA/BSS hunk" above): 32 character-
biography paragraphs, CONFIRMED via a clean, cheap cross-table oracle — a
second, independently-purposed 32-entry `"<title> <first> <last>"` roster
a few KB later matches the bios 1:1 in identical order, zero deviations,
also matching the well-documented external fact that Midwinter has exactly
32 named playable characters — plus 608 total narrative/UI strings
(recruitment dialogue, a procedural place-name generator, victory/defeat
endings, disk/UI prompts). First real assets now ship to
`public/assets/midwinter/amiga/` (a structural 16-container sprite catalog,
the 32 CONFIRMED character bios, 608 rendered strings); the game is
registered in `src/game-id.ts`/`tools/shared/game-config.ts`
(`supported: false`, bespoke Python pipeline). See
`docs/explore/Midwinter/TODO.md`.

**Terrain architecture is now SOLVED (later session, static-only + a
`re-codebreaker` escalation).** The "16 sprite/image containers, no
heightmap-shaped record among ~65 sampled entries" negative above was
real but incomplete — it stopped one indirection short. A forced Ghidra
linear-sweep disassembly (default recursive-descent auto-analysis under-
covers this binary the identical way IRA does — 566/~1046 functions until
a word-aligned linear-sweep-plus-2-byte-resync pass, then `analyzeAll()`,
reached 92%/1046) traced the real landscape renderer end to end and found
two load-bearing bugs in the resource-table reading used by the earlier
pass: the record's length field is the **`+12` longword, not `+10`** (the
two happen to be numerically equal for every single-track record, which
is why they passed every earlier spot-check — see
`sibling-field-values-alias-in-dominant-case.md`), and disk-selector `1`
means **`+78` tracks on this same image**, not a separate/missing floppy.
Re-reading the table this way makes all 61 resource records chain byte-
contiguous with 0 gaps, and resource **index 27** (`Disk.1` file+`0x3026A`,
exactly 10,000 bytes) resolves to a **50x50 coarse seed grid** (4 bytes/
cell: s16 BE height + u16 BE deterministic XOR-propagated noise word, NOT
a PRNG), fractally subdivided ONCE per mission by an iterative (not
recursive — a fixed 50-iteration row loop, which is exactly why an earlier
self-recursive-function census found nothing, see
`narrow-opcode-form-census-false-negative.md`) altitude-scaled midpoint-
displacement kernel into the 100x100 grid the renderer samples every
frame (roughness genuinely scales with altitude, `(avg<<3)+5000` in the
kernel — matching a since-verified independent DOS-port fan decode's own
prose claim of "10KB seed, zero randomness, roughness scales with
altitude" exactly). Verified 5 independent ways with 0 deviations
(resource-chain contiguity, 3 independent size/count identities, and a
2.4-3.7x smoother-than-shuffled-null spatial-correlation check); the
calling session independently re-derived the same record struct from the
doc's prose alone and re-decoded it directly against raw bytes, getting
every cited offset/length back exactly, rather than trusting the
escalation's report at face value. Ships `public/assets/midwinter/amiga/
data/terrain-heightmap.json`, `screens/terrain-{coarse,fine}.png`, and a
real triangulated 3D mesh `meshes/terrain-fine.glb` (10,000 verts, 19,602
tris, 0 errors under `@gltf-transform/cli validate`). Also corrected in
the same pass: the previously-documented "terrain tile cache"
(`FUN_00018D6C`/`FUN_00018E82`) is actually a 320x200 4-bitplane **screen**
delta codec, unrelated to terrain — its caller sets explicit bounds
`[0,319]x[0,199]`, the literal full screen, not a tile-cache window. Open
now: the 3D **vehicle/object vector models** (the same transform/clip
pipeline's other input, still unlocated) and 4 resource-table records
(57-60) that resolve past the end of this 660,480-byte image, narrowing
"this disk is the complete game" to "complete except ~9.2 KB of tail
content." See `docs/explore/Midwinter/data-structure.md` "Terrain
heightmap — CONFIRMED" and `TODO.md`.

**Midwinter 2: Flames of Freedom** (Microprose, 1991, Amiga sequel — a
genuinely different codebase from Midwinter 1, standard AmigaDOS floppies
via `amitools`, not a custom trackloader): the same session cracked Disk.3's
**directory-file format** byte-exact — `missdir`/`progdir`/`grafdir` are all
one shared grammar, `[u16 BE fileSize][u16 BE unknown][ASCIIZ filename]`
records (fixed 18-byte stride for `missdir`'s 42 island files, variable
stride for `progdir`), verified by matching every declared `fileSize`
against the real extracted file's actual byte length (42/42 + 2/2, 0
deviations; `tools/midwinter2/parse_directory_file.py`). This directory is
also the **real DOS-level island/program loader**, traced end-to-end in
`mwII.asm`: `LAB_0A44`/`LAB_0A43`/`LAB_0A45` (LoadFile/SaveFile/a third
helper) plus a string-pool-driven filename-concatenation helper
(`LAB_10A4`) resolve a directory record's name into a real `dos.library`
`Open()` call — closing a previously-"not yet located" gap. Along the way,
a systematic address-citation bug was found and corrected in this project's
own prior `data-structure.md`: `mwII.cnf` forces one whole-executable
`CODE $0-$353B8` range through IRA, but `$353B8` is only hunk0's size while
the fed file is the whole 4-hunk, 505,488-byte executable — so `ORG+0x2C`
(the file-offset formula, confirmed 13/13 inside the declared range) is
**not valid past that boundary**; a label the doc had cited at
`file+0x443ac` was actually 60 KB away, at `file+0x53030` in hunk1 DATA
(found by string search, not trusted arithmetic) — now its own lesson,
`forced-code-range-address-comments-unreliable-past-boundary.md`. A
follow-up session cracked all three of this game's sprite/screen pixel
codecs at the instruction level, all still inside hunk0 CODE (so
`ORG+0x2C` stayed valid — a Ghidra HUNK-loader pass planned for this work
turned out unnecessary, and Ghidra was in fact never actually installed
in this environment): **`.cmp`/`.bin`** is a 4-bit nibble-RLE (`LAB_0B8E`,
file+0x1c358) with a genuine two-sub-grammar escape scheme (a "repeat one
value N times" case and a structurally distinct "N fresh literal values"
case sharing one read/toggle primitive but differing in which label their
terminating DBF loop targets — flattening the two on a first port produced
a plausible-looking but wrong decode, caught only by a corpus-wide
byte-consumption-vs-declared-length check, not by any crash; now its own
lesson, `loop-reentry-label-decides-reuse-vs-refetch-subcase.md`),
validated byte-exact on 312/415 real frames (100% on `collar.cmp`/
`weap9.cmp`/`eyes.cmp`/`level.cmp`, 15/16 on `hair.cmp`) and visually
confirmed (`eyes.cmp` -> 24 distinct eye shapes, `weap9.cmp` -> a dagger,
`collar.cmp` -> a necklace outline); a residual bit-30-flagged sparse-patch
variant (`LAB_0BAF`) covering ~11 files/103 frames (icon banks like
`mapicon.bin`/`fletters.bin`) is structurally identified but not decoded.
**`.mcp`** is a fixed-320x200 1bpp polarity-run RLE (`LAB_04FF`,
file+0x0b842). **`.fsd`** is fixed-320x200 4bpp planar via a word-level LZ
front-end (`LAB_0EE5`-family) feeding the SAME 8-step `ADD.B`/`ADDX.W`
chunky-to-bitplane bit-transpose that `.cmp`'s own pipeline uses after its
RLE stage (`LAB_0B88`/`LAB_0B8A`) — one shared two-stage graphics pipeline
(decompress to a chunky byte-per-pixel intermediate buffer, then
transpose to planar) reused across two structurally different compression
front-ends in the same executable. `.mcp`/`.fsd` are confirmed code-level
only, no Python port yet. 57 sprite atlases now ship (greyscale — no
Amiga palette confirmed yet for any grafix content) to
`public/assets/midwinter2/amiga/sprites/`, `tools/midwinter2/
cmp_format.py`/`export-cmp-sprites.py`; the game is registered in
`tools/shared/game-config.ts`/`src/game-id.ts` (`supported: false`, bespoke
Python pipeline, same pattern as Midwinter 1). A separate `strings`-style
scan (same technique as Midwinter 1's `mainexe` find above) found a second
narrative-text island packed inside `mwII`'s own hunk1 DATA
(`file+0x53000`-`0x57a00`, 908 strings): a 3-theme procedural place-name
generator that shares VERBATIM suffix wording with Midwinter 1's own
generator (`?Fjord`, `?Straits`, `The Sea of`, byte-identical — shared
string-table content between the two games' otherwise-distinct codebases),
full real end credits (director Mike Singleton, producer Hugh F.
Batterbury, "THE MAELSTROM TEAM"/"THE MICROPROSE TEAM" real developer
names), and a rich NPC helper/informer/traitor relationship-interaction
text system — exported (rendered) to `public/assets/midwinter2/amiga/
data/narrative-strings.json`. A later follow-up session (2026-09-03) resolved the palette,
`.mcp`/`.fsd` Python ports, and — the main new result — traced
`islandNN.bin`'s section 2/3/4/6 record consumers end-to-end via
`mwII.asm` (a header-resolution routine, `LAB_0B1C`/`LAB_0B21`, resolves
the container's 14-entry offset directory into absolute buffer pointers
in a 24-entry array anchored at `LAB_196A` — finding this needed
correcting a real self-inflicted error, reading a label's real address
from its raw hex-byte/definition-line comment rather than its own
`LAB_XXXX` name, now `ira-label-name-is-not-a-literal-address.md`).
Section 2 (276×8B, CONFIRMED stride, 3 independent `MULU #$0008` sites)
is named/typed point features, not vertices — offset+4 is a packed
sign-selector into either a 32-entry building pointer table or a byte
natural-feature type table, both routed through the same `LAB_0E97`
32-entry name-lookup mechanism already confirmed for the island-name
table. Section 3 (variable count×80B, CONFIRMED stride — corrects an
earlier "multiple of 8" guess; 0/42 divide by 8, 42/42 by 80) is
buildings/bases with a world position (+48/+52, u32 BE) and active/
status flags. Section 6 (CONSTANT 800B, CONFIRMED as 50×16B via both a
consumer `MULU #$0010` and a boot-time default-init `ADDA.L #$10` loop
— corrects an earlier wrong "100×8B" render that happened to match only
on total byte count) is spawn/insertion points, world position feeding
the live player-position globals directly. Section 4 (16B records,
CONFIRMED stride) is sentinel-terminated (`TST.W`/`BMI`) rather than
count-terminated, explaining why its declared byte size never divides
evenly by 16 across the 42-file corpus (0/42). **Conclusion: no stored
terrain/landscape mesh exists anywhere in the container** — every
section is now accounted for as small scalar/text/flag data or one of
these four discrete-object-placement arrays, none vertex/polygon-shaped,
and file sizes are far too small for a stored 3D landscape — strong
(structural, not disassembly-of-the-generator-itself) evidence
Midwinter 2's terrain is generated procedurally at runtime; the
generator routine itself remains unlocated. Section3-active-building vs.
section6-spawn-point world-position bounding boxes were cross-validated
as overlapping on all 42 islands (two independently-traced consumer
paths landing in the same coordinate space). Shipped 42 building+
spawn-point marker GLBs (`public/assets/midwinter2/amiga/meshes/
islandNN-markers.glb`, `@gltf-transform/cli`-validated clean) as the
confirmed-placement visualization — explicitly not a terrain mesh, since
none exists to export; `tools/midwinter2/build-island-markers-gltf.mjs`
+ `verify-island-sections.py` (structural regression: constant record
counts, stride divisibility, cross-validation bounding-box overlap,
42/42 clean). Open: the `LAB_0BAF` variant, `cods.bin`'s internal
`u32`-table grammar, `disk.4`'s copy-protection check site, sections
1/5/7-12's own record consumers, several still-unresolved individual
fields within sections 2/3/4/6.

> **Correction (follow-up session, 2026-09-03):** "the terrain-generator
> routine itself remains unlocated" above is superseded — it WAS located
> (in an earlier pass than this correction) and this session finished
> porting it. The generator is a shared, single `grafdir` resource
> (`mw2map.bin`, 8798 B = 83x53 s16 BE cells, grafdir index 96/0x60,
> resolved via the same `LAB_0AB3` mechanism `islandNN.bin` uses) that ALL
> 42 islands read as one common base landscape — per-island distinctiveness
> comes entirely from the already-confirmed section 2/3/4/6 placement
> records, not unique terrain geometry. On top of that coarse seed,
> `LAB_096D` (calling 53x `LAB_0939`, itself 3 sub-passes `LAB_093A`/
> `LAB_093C`/`LAB_093E`) is a single full-map 3-sub-pass diamond-square
> fractal expansion doubling both dimensions to 166x106 — structurally
> identical to Midwinter 1's own 3-sub-pass expansion (`tools/midwinter/
> terrain.py`), but MW2 computes its per-cell noise term on the fly via a
> coordinate hash (`LAB_0A33`) rather than reading a stored per-cell noise
> word like MW1. Ported byte-for-byte to Python
> (`tools/midwinter2/terrain.py`'s `expand()`), verified via a row-0
> raw-column cross-check (0/83 mismatches) and a smoothness-vs-shuffled-
> null-control ratio (4.50x vs. the coarse grid's own 3.78x), and shipped
> as `public/assets/midwinter2/amiga/meshes/terrain-fine.glb`
> (`@gltf-transform/cli validate`: 0 errors). Surfaced a real, generalizable
> 68k gotcha along the way — a `DBF D7,label` loop seeded `D7=0x52` (82)
> actually runs 83 times (`DBcc` semantics: seed+1 iterations), only caught
> by cross-checking an independent constant (the outer driver's own
> 664-B/row = 2x166-word dest-pointer advance) — see
> `decompressor-port-loop-condition-iteration-shift.md`. A SECOND,
> structurally distinct mechanism also exists and was traced but NOT
> ported: a recursive, roughness-halving LOCAL re-expansion keyed to a
> moving camera/vehicle position (`LAB_0963`/`LAB_0967`/`LAB_096B`/
> `LAB_096E`+`LAB_0965`) — position-dependent runtime LOD refinement with no
> single well-defined whole-map artifact to export statically. A plausible
> adjacent hypothesis was tested and REFUTED: the `control` grafdir
> resource (idx 87, 2048 B, loaded next to the seed) is NOT a terrain
> roughness/scale parameter table — the driver's real roughness sequence is
> hardcoded immediates in `LAB_0938`, and `control`'s own destination
> buffer symbol has zero other references anywhere in the disassembly;
> `control`'s real content/purpose is still completely unknown. The same
> follow-up session also found (but did not fully crack) a real 4-channel
> Paula sound driver in `mwII` — a voice allocator, per-voice pitch-slide/
> vibrato state machine, attack+loop sample instrument model, and a
> 68-entry jump-table bytecode sequencer, overturning a prior shallow
> magic-scan-only "no audio found" negative — but the actual static PCM
> sample-bank location is still open: voice-block sample-pointer/length
> fields are zero-filled at rest (runtime-only), the instrument table holds
> envelope/vibrato params not sample pointers, `cods.bin` was checked and
> refuted as a candidate, and a lag-1-autocorrelation sliding-window scan of
> hunk1 DATA found only false positives (already-known text/coordinate
> tables) — see `byte-shape-classifier-needs-entropy-gate.md`'s third
> confirmed instance. See `docs/explore/Midwinter2/data-structure.md` and
> `TODO.md` for full detail and the current open-item list.

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

Frontier: Elite II (David Braben/Frontier Developments, 1993, Amiga —
David Braben's next game after Virus below, on a distinct but lineage-
related engine): the FE2 savegame container (5 shipped "Data Disk" files)
was solved via `re-codebreaker` — self-keying word-stream cipher +
zero-RLE, byte-exact round-trip; see `docs/formats/fe2-savegame.md`. A
later session cracked the **3D ship/station/object model format**
end-to-end: a 300-slot `u16` BE self-relative pointer table at
`file+0x28804` (stop condition: 2 consecutive zero slots past index 2 —
reading past the real end walks into the first real model's own header
bytes, since small header fields coincidentally look like more valid table
offsets), each model a 15-field header + a vertex table (8 encodings:
literal + 7 computed-from-other-vertices forms including two genuinely
dynamic ones, `rand`/`lerp`) + a normal table + a **32-opcode display-list
bytecode** (opcode = low 5 bits of a `u16`; TRI/QUAD/MIRRORED_TRI/
MIRRORED_QUAD/LINE are the geometry-producing subset, `MODEL`/
`MODEL_SCALE` are submodel references — the single most common non-trivial
opcode at 1,255 hits corpus-wide, not expanded into an assembled scene
graph this pass). Cracked by finding a **real, actively-maintained
community project with a from-scratch decompiler/recompiler for this exact
bytecode**, `watsonmw/fe2-intro` (confirmed to actually exist by cloning
it, not just trusting the `WebSearch` citation — see
`websearch-cited-repo-may-not-exist.md`); its `assets.c` declared table
offsets for an `AssetsRead_Amiga_Orig` executable variant that matched this
project's real binary byte-for-byte (cross-confirmed via two independent
offset coincidences with prior sessions' own findings before trusting it).
Its shipped CLI hardcoded a *different*, newer exe variant's table
locations, so a small (~12-line) patch was needed to add an `-orig` flag
selecting the offsets its own `assets.c` already declared for our variant
— then its `-dump-game-models`/`-dump-intro-models`/`-dump-galmap-models`
flags ran headless (`SDL_VIDEODRIVER=dummy`) directly against the real
executable with **zero parse errors** across 230+109+12 models. Since the
repo states no license, its source was read as a **specification only** (no
code copied/vendored) to write a fully independent from-scratch Python
reimplementation (`tools/frontier/frontier_models.py`) — a control-flow
walker following both sides of every conditional branch, verified
byte-exact against the oracle's own text dump across the *whole* corpus:
1,402/1,402 face+line instructions, 2,619/2,619 literal vertices, 929/929
normals, including confirmed-real edge cases (negative "parent-relative"
vertex indices that looked like decode bugs until they turned up
byte-identical in the independently-produced oracle output too).

A follow-up session cracked **submodel scene-graph assembly**
(`tools/frontier/frontier_scenegraph.py`): the full matrix stack
`MODEL`/`MODEL_SCALE`/`MATRIX_SETUP`/`MATRIX_TRANSFORM`/`MATRIX_COPY`
imply, derived from fe2-intro's own `render.c` (the *renderer*, not just
its decompiler — confirmed buildable on Linux via manual `-lSDL2 -lm`
linking, since its CMakeLists.txt has no Linux target block). Along the
way, found and fixed two real bugs in the *base* (previously "confirmed")
decoder: (1) the vertex-table length field was misidentified —
`(normalsOffset - vertexDataOffset) / 4` is the real count (229/229 exact
vs. the oracle; the old field matched 0/229 and silently over-read into
adjacent normal/code data as "extra vertices" no existing check ever
inspected); (2) face/line vertex-index fields use the SAME doubled
comment-index + odd/even mirror-slot scheme as avg/add construction args,
not raw record indices (30.8% of all face refs are odd — impossible under
a raw scheme; this fix alone raised flat face resolution from 73.9% to
98.3%). Submodel assembly itself is confirmed at the instruction-decode
level (1,025/1,025 MODEL/MODEL_SCALE + 237/237 MATRIX_TRANSFORM fields
exact vs. the oracle) and via a 111/111 zero-submodel-model regression
check (assembled output must equal the flat export exactly); composed
multi-submodel *geometry* has visual/bounding-box sanity only (no live
amiberry capture this pass — see `frontier-submodel-live-verify` in
`docs/explore/Frontier/TODO.md`). `public/assets/frontier/amiga/meshes/`
ships composed, multi-part OBJ meshes (169/230 models) superseding the
flat per-model export. **A follow-up session wired the assembled meshes
into this project's real, generic glTF-based 3D viewer** (the same
`type: 'mesh'`/`modelFormat: 'gltf'` convention Hunter/Carrier
Command/Epic already used) via a clean language bridge, with zero changes
to the already-verified decoder/assembler: the Python exporter
additionally writes a non-web geometry cache (`build/cache/frontier/
assembled/model_NNN.json` — resolved world-space face points + Amiga
12-bit colour + primitive kind, since plain OBJ can't carry per-face
colour), and a new `tools/frontier/build-gltf.mjs` (closely templated on
`tools/epic/build.mjs`) reads that cache and writes real `.glb` files
(161/169 — the other 8 resolve only `line`-kind records, no polygon
surface) plus merges the generic manifest fields in place (Frontier's
manifest already lived at the exact path the viewer's `${ASSET_BASE}`
convention expects, unlike Epic, so no second manifest file was needed).
The game itself had never been registered in the shared viewer at all
(`src/game-id.ts`'s `GAME_IDS` / `tools/shared/game-config.ts`'s
`GAME_CONFIGS`) despite substantial existing `public/assets/frontier/`
output — a distinct, easy-to-miss gap from the already-known "pipeline step not registered" trap. The largest station model (54,
12,587 submodel instances, 342,154 vertices) needed `UNSIGNED_INT`
glTF indices, not `UNSIGNED_SHORT` (Epic's objects never approached the
65,535-vertex cap). Live-verified with a Playwright sweep against
`npm run dev` (0 failed requests, 0 console errors across a 12-model
index sweep + 4 named spot-checks) and the full 161-file corpus through
the *real* Khronos glTF validator run in-process (`validateBytes()`,
not a CLI sample) — 0 errors/warnings. Full spec:
`docs/explore/Frontier/data-structure.md`.
Open: the `COMPLEX` opcode's bezier-surface interior mini-VM, a
`LINES`-mode glTF fallback for the 8 line-only models, and 7 of 15
header fields — see `docs/explore/Frontier/TODO.md`.

Virus (Firebird/Telecomsoft, 1988, Amiga — Braben's earlier Zarch-derived
title, the fractal-landscape engine Frontier's own terrain lineage traces
back to): confirmed **no stored 3D object/model format exists at all** —
unlike Frontier's ships/stations above, Virus's landscape (and, per the
disassembled code, its only other rendered content) is 100% procedural:
an explicit, code-confirmed bounded work-queue recursively subdivides
quads via fractal midpoint displacement (a shared 2-longword
additive-recurrence PRNG perturbs each new point in full 3D, reused
verbatim for particle/spore placement) with adaptive screen-space-size LOD
termination and a standard fixed-point perspective-divide draw path. See
`docs/explore/Virus/data-structure.md`. This is a useful engine-lineage
data point for the family: needing (Frontier) vs. not needing (Virus)
explicit stored vertex/polygon data tracks directly with whether the game
has discrete objects to render at all, not with shared engine ancestry —
don't assume one Braben-lineage title's asset format (or absence of one)
transfers to another without checking. Disk image structure (raw
non-AmigaDOS custom track dump, ~8000-byte track-slot pitch) and two
still-unidentified data regions remain open — see
`docs/explore/Virus/TODO.md`.
