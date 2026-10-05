# wyrm — Dune, KGB (Cryo)

**Project root:** `~/Development/wyrm`

HSQ in-place LZSS (20-bit headers, checksum), bank/sprite/room formats, donor
palettes, `dir.0` catalogs, manifest-driven builds.

**Dune ships on both Amiga and DOS VGA, one shared Cryo container format
across both** (confirmed: identical frame directory, palette-command-stream
position, and character animation/place-list bytecode; `src/formats/cryo-image.ts`
`parseCryoImage(data, { endian: 'be' | 'le' })` decodes both from one
codebase). The two ports are **not** a pure byte-order flip of the same
struct, though — see
`~/.claude/agents/game-re-lessons/platform-port-swaps-adjacent-header-fields.md`:
DOS's 4-byte sprite frame header swaps the trailing `[height][paletteBase]`
byte order relative to Amiga's `[paletteBase][height]`, DOS's `paletteBase`
is a full unmasked byte (256-colour VGA palette) where Amiga's is masked to
a low nibble (32-colour hardware palette), and DOS's palette block list
ends on the `0xFFFF` word, not Amiga's `start >= 0x80` (see
`palette-block-terminator-inherited-from-narrower-palette-port.md`, sourced
here — the inherited rule dropped every 128+ block for weeks).

**DOS room scenes are solved end-to-end (2026-09).** DOS rooms are not
bitmaps: each is a `.SAL` script of dithered/gradient polygons, lines and
sprite placements, and the whole grammar plus render semantics were
re-derived from the game's own interpreter (`DUNEPRG.EXE 0x3fc8`/`0x3ff1`,
`DUNEVGA.HSQ` entries 5/19/35/36): two-chain polygon edge tables, an 8.8
gradient accumulator writing `colour−1` plus an LFSR dither, 9-bit sprite
indices with flip/reduction/palette-override bits, and a **room → bank
binding that is a function of the room number alone** (`slot = 0x13 +
((roomNo−1)>>4)`, `.SAL index = (roomNo−1)&15`) — the earlier "cross-file
sprite registry" blocker was a parser-desync artifact (see
`command-discriminator-on-wrong-byte-closes-byte-exact-fakes-registry.md`,
sourced here). `SKY.HSQ` carries 33 outdoor-scene palettes inside
zero-width frames; four rooms are structurally confirmed against real DOS
screenshots via the colour-invariant index-map metric in
`game-re-method/verification-techniques.md` (sourced here). All 48 rooms
ship composited (`tools/dune/dos-build-assets.ts` `buildSalRooms()`).
Specs and open items: `docs/dune/dosvga/room.md`, `sprite.md`,
`palette.md`, `docs/dune/TODO.md` (inferred bank bindings for 14 rooms,
runtime day/night tint, exact dither sequence). Amiga reference (already
solved, same container): `docs/dune/amiga/*.md`. DOS executable notes:
`DS:0` = file `0xEEF0` (`DS = loadseg + 0x0ECF`), see
`game-re-tooling/dos.md`'s "Anchor a derived DS base" section (sourced here).

**Amiga's ornithopter-flying-view runtime mechanism traced, then
CORRECTED by the game's own owner/player and re-verified (2026-09).**
A first pass (static disassembly only, no play experience) concluded
`ornycab.hsq` was a continuous cockpit backdrop, `dunes`/`dunes2`/
`dunes3.hsq` were a small unrelated world-map icon atlas, and `ornypan.hsq`
was a passive in-flight instrument panel with gauge needles — all three
wrong. A second pass, re-tracing under a corrected framing supplied by
someone who has actually played the game (treated as a strong prior, not
gospel — independently re-verified against the code), found decisive
code-level support for all three corrections, including one finding that
outright falsifies the first pass's central argument: **`ornycab`'s only
call site (`LAB_0319`/`LAB_0320`) is gated behind four independent
conditions** (active travel mode, an active-NPC/dialogue sentinel, a
proximity/heading state set by a 9-entry point-of-interest bearing scan
`LAB_03AD`/`LAB_04BA`, and a valid extracted event id) — it is a
dialogue-triggered narrative illustration ("passenger spots a landmark"),
never a per-frame backdrop. **`dunes`/`dunes2`/`dunes3.hsq` are real,
code-confirmed per-object scaled parallax scenery**: `LAB_047E` computes
each scenery object's screen X/Y *and* an inverse scale factor from a
travel-distance state on every redraw, and decrements each object's own
stored distance value every time — the literal "grows/shrinks as you
approach" mechanism, via a CPU-side `DIVU`-driven nearest-neighbour
scaling blit (`LAB_0485`), not a lookup icon. `dunes.hsq` (travel mode
byte `-4168(A6)&3 != 0`, e.g. ornithopter) and `dunes3.hsq` (mode `0`,
the default/on-foot state) are two files through the *same* renderer,
selected by the identical mode byte that gates `ornycab` — exactly "one
shared scenery mechanism, two travel modes." **The dunes-loading cluster
and the ornycab dialogue gate are called from the same shared function**,
`LAB_02B0` — a few instructions apart, refuting the first pass's "loaded
nowhere near each other" claim outright (that claim rested on not having
traced `LAB_02B0`, the routine both functions are steps of; asset-shape
inspection alone made "map-icon atlas" look plausible until the actual
consumer code was read). `ornypan.hsq` hosts a blinking selection-
highlight cursor (`LAB_03D9`/`LAB_03DB`, recomputed every tick) over its
opaque background picture, and its click-handler entries (`LAB_03C4`/
`LAB_03C5`/`LAB_03C6`) sit in the same generic menu-descriptor pool as 5+
other distinct handlers, with its 3-sprite place-list overlay
conditionally gated between two different entry handlers rather than
always-on — the shape of a multi-option travel/destination menu, not a
passive gauge readout. `orny.hsq`/`ornytk.hsq`'s already-solved mechanism
(4-frame subset vs. 23-frame full table, short repeating icon loop vs.
scripted 33-tick takeoff/landing arc) is unaffected, with one reinforcing
detail: the takeoff entry point (`LAB_03FA`) itself calls the
dunes-scenery redraw immediately before its takeoff loop, so the takeoff
animation plays out over real scaled desert scenery, not a bare backdrop.
The **"zero hardware scrolling anywhere" finding from the first pass
stands and is now better explained** — the scaling effect is real but
entirely software (a per-row `DIVU` scaling blit), consistent with, not
contradicted by, the zero-blitter/Copper-usage proof. Sourced a new
corollary to `same-name-cross-port-colour-mismatch.md` (asset shape/
classification, not just colour, can mislead when the real consumer code
is never read) and reaffirms `ira-label-name-is-not-a-literal-address.md`
(community-disasm label cross-referencing still not used as ground
truth). Full corrected trace, four-gate `ornycab` citation, `LAB_047E`
scaling-blit disassembly, and open items (raw `LAB_11BB` overlay-sprite
bytes, the two `ornypan` entry-handler screens' exact identity, the still-
untraced `LAB_0323` "worm mode" branch): `docs/dune/amiga/ornithopter.md`,
`docs/dune/TODO.md`.

**Amiga's strategic/world-map ("command the Fremen war against the
Harkonnen") subsystem is now first-traced end-to-end**, a whole previously
uninvestigated system (only raw filenames catalogued before this session):
`command1.hsq`'s directory+`0xFF`-terminated string-pool format is
confirmed byte-exact (319 strings — settlement names, faction tags,
territory activity/order types, war-casualty counters, plus a leftover
developer debug menu — verified two ways: all 319 directory offsets land
exactly on independently regex-found string starts, AND the string pool
is byte-identical to the DOS port at the same file offsets despite the
directory region itself differing), shipped via a new shared module
`src/formats/cryo-strings.ts` + a `type: "strings"` manifest/pipeline
branch. `map.hsq`/`map2.hsq` (two same-size 50,681-byte raw tile/state
grids, not images) are fed through a confirmed joystick-driven wraparound
("cylindrical planet") panning cursor with row width 398, matching
`tablat.bin`'s confirmed 99-row × 8-byte per-row geometry table
(`row×398` offset field, byte-exact across all 8 sampled records).
`onmap.hsq` (152 small marker-icon frames) and `attack.hsq` (the
already-known 51-icon combat sprite bank) are newly tied together — both
load through the *same* dedicated fast-path trampoline (`LAB_0BEA`),
whose own immediate operand is self-patched at runtime between the two
catalog IDs. `globdata.hsq`'s exact record format (a monotonic 0–99 ramp
terminated `00 FF`, hypothesized as a reverse position→map-row lookup)
and the map's own per-cell pixel decode (`LAB_0FCE`) remain open.
Discovered the cached screen loader's (`LAB_0BEC`) hard 86-entry cache
boundary (from its own cache-clear loop's trip count) marks a split
between it and a wholly separate uncached loader (`LAB_0C95`+`LAB_00D9`)
used for every catalog ID ≥ 86 — confirmed by backward-scanning all 74
`LAB_0BEC` call sites and finding none exceed the bound. Full trace,
byte-level tables, and paths-tried: `docs/dune/amiga/strategic-map.md`,
`docs/dune/TODO.md`.

## KGB (Cryo, 1992, aka "Conspiracy") — a sibling engine, substantially solved

Amiga + DOS. Cracked from `data/kgb/derived/kgb-decrunched.exe`/`.asm`
(`tools/kgb/decrunch-hunk4.ts` unpacks the shipped executable's bespoke
in-house self-decruncher — a distinct, forward-reading LZ77/Huffman hybrid,
not any public Amiga cruncher). Two decompressors solved and shared
(`tools/kgb/cryo-lz.ts`): `LAB_0547` (header-carrying, `.scr` cutscene
screens) and `LAB_0559` (headerless, `.32x`/`.anc`/PAC sprite banks) are one
codec family (shared bit reader, match encoding, differ only in symbol-class
signalling) — both fully verified byte-identical against an independent
Python re-implementation. **In-game rooms are not painted bitmaps at all**:
every location is composed at runtime from `PAC/chap{n}.pac`/`map{n}.pac` —
a hotspot table + `LAB_0547`-packed scene descriptors (sprite placements with
flip/tile/shrink/remap bits) + `.anc`-format sprite banks — verified
44,440/47,680 pixels index-exact against a real Amiga savestate's captured
framebuffer (`docs/kgb/room-rendering.md`). Colour is one fixed 32-entry
palette compiled into the executable, not per-file. DOS's `PAC` sprite-bank
pixel format (chunky, not planar; swapped frame-header field order matching
`platform-port-swaps-adjacent-header-fields.md`) is solved and cross-
verified (`tools/kgb/dos-pixel.ts`), as is DOS's `.SQX` container (same
`.32x`-style self-describing directory, little-endian, wrapped in the
packed-block codec above — 673/695 frames decode across the 20 character
basenames shared with Amiga `TETES/*.32x`, one decoded frame's dimensions
independently cross-checked against an unrelated earlier investigation's
already-established value for the same character).

**`.cma` (per-chapter scenario data) has a cracked container** (a 16-slot
BE16 offset header, no magic, sections tiled end-to-end and NOT stored in
header-slot order — sort by offset, never assume order) **and a newly
cracked generic "state-cell accessor"** (`LAB_04DA`/`LAB_04DB`, ~26 call
sites across the engine): a 16-bit cell value's top 3 bits (after a `ROL.W
#3`) select a class 0-7; classes 1-4 read/write a runtime-selected 16-byte
record in one of 4 parallel record-array sections, where the record index
is itself a **mutable state byte living in a separate, small "state"
section** at a per-class fixed offset (four consecutive cursor bytes, one
per class) — i.e. the format encodes "the currently selected NPC/object/
room" as a handful of scalar bytes rather than a stack or registers. Traced
by hand from raw 68k bytes, then independently re-verified with a from-
scratch Python line-by-line re-simulation of the same disassembly (see
`hand-traced-byte-shuffle-needs-independent-resimulation.md`, sourced
here) — the two agreed exactly, which is what made shipping the
byte-level spec safe. Cross-validated live: located the loaded `.cma`
file's true runtime base address in an Amiga savestate by a byte-exact
search across 5 independent *static* (non-runtime-mutated) byte ranges of
the source file — all landing on one address, with a smaller-needle-only
false-positive at a different address correctly rejected because it failed
the larger needles (see `multi-region-byte-search-needs-largest-needle-arbitration.md`,
sourced here) — then reading the live selector byte reproduced an
already-published-but-previously-unverified "which sections mutate at
runtime" claim byte-for-exact-byte, cross-validating both the base address
and the old claim in one shot. A 16-byte record array's byte-3 field was
confirmed as a 1-based scene/room id by testing directly against each
chapter's own independently-decoded PAC scene count (not by pattern-
guessing) — ~85-99% of records land in range, and records cluster into
contiguous same-id runs matching one room's own object list. A separate,
superficially identical byte-shuffle dispatch turned out to belong to an
already-documented, *different* hotspot/id-classification subsystem — kept
distinct rather than conflated just because the arithmetic pattern
matched (see `identical-byte-shuffle-arithmetic-may-be-two-subsystems.md`,
sourced here). Full spec: `docs/kgb/cma.md`, `docs/kgb/room-rendering.md`
§ "On-demand objects".

**`.cma`'s script bytecode is now fully solved** (a later session): sections
0-4 (five independently-entered top-level scripts) plus section 5's own
condition/trigger/response sub-grammars are a 26-opcode VM dispatched
through a genuine indirect jump table, with `GOTO`/`GOSUB`/`SELECT` control
flow and a full condition-expression grammar — verified with zero deviations
across all four shipped chapters (8290/8290 blocks consume their body
byte-exactly; every opcode is inside the 26-entry table; every jump target
lands on a block boundary). `SAY`/`SAY2` phrase operands resolve to real
`.phz` dialogue text for 96.9% of the corpus (the rest are two distinct
runtime-only cases, both correctly left unresolved rather than guessed).
`tools/kgb/cma-script.ts`, `docs/kgb/cma.md` § "Script bytecode".

A still-later session built a **combined room+hotspot+actor+dialogue-
bytecode graph** (`tools/kgb/dialogue-graph.ts`, one JSON per chapter, for a
planned `@xyflow/react` interactive viewer) purely by composing the
already-solved decoders above — no new format decoding, but building it
forced a full corpus-wide accounting (every hotspot, every block, every
actor) the individual formats' own spot-checks never required, and that
accounting caught a real gap in the "confirmed" PAC hotspot table: its own
offset table can run longer than the sibling scene-descriptor table's
declared count (55 real records corpus-wide were silently skipped by a
first-pass loop bounded on the wrong table's length — see
`documented-cross-table-pairing-is-not-a-length-bound.md`, sourced here).
The task's key open question — whether the `0xFF`-class hotspot's
`LAB_02C5` call links a room to a `.cma` actor/dialogue-script entry — is
now a **settled negative**, fully traced: `LAB_02C5` reads four fields from
whichever section 9-12 record a state cursor byte currently selects (via
the already-solved generic accessor, using fixed literal selectors baked
into each of the four call sites, not derived from the hotspot's own low
byte) and feeds a canned French-grammar UI-feedback text composer
(`LAB_02B2`/`LAB_02BA`) — never section 5's actor table. A genuine bonus
connection surfaced along the way: bytecode opcodes `0x18`/`0x19`
(`OBJ0`/`OBJ1`) call the *same* `LAB_0308`/`LAB_0309` on-demand-object-
toggle function the confirmed compound-id hotspot path already uses — real
engine-verified machinery linking dialogue bytecode to room objects, but
since the target room is never named in the bytecode itself (only in
whichever scene table happens to be loaded at runtime), this ships as a
labelled *candidate* edge, not a proof. Full spec + trace:
`docs/kgb/dialogue-graph.md`.

Still open: DOS `.M32` music (not standard ProTracker, decompresses
cleanly, no embedded text), a handful of `.cma` opcode effects (`PLACE`'s
operand bytes, the `LAB_052F` scaling transform, `LAB_0832`) — see
`docs/kgb/TODO.md`.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/wyrm` | Dune (Amiga + DOS VGA — one shared Cryo container; DOS's vector `.SAL` room scenes fully solved from the interpreter, 48/48 rooms composited, 4 screenshot-confirmed; Amiga's ornithopter-flying-view *runtime mechanism* now traced end-to-end from disassembly — corrects a DOS-derived working hypothesis rather than confirming it: `ornycab.hsq` is a single pre-baked opaque cockpit+desert picture on Amiga (no runtime layering, unlike DOS's transparent-window sprite variant of the same file), `dunes`/`dunes2`/`dunes3.hsq` are small world-map marker-icon atlases unrelated to the cockpit scene, `ornypan.hsq` is the instrument panel with 3 gauge-needle sprites recomposited live every tick, and `orny.hsq`/`ornytk.hsq` are a 4-frame menu-preview subset and the full 23-frame scripted takeoff/landing arc animation respectively — confirmed via a whole-binary proof that no blitter/bitplane-pointer/Copper register is ever referenced, so none of this scrolls, `docs/dune/amiga/ornithopter.md`; the strategic/world-map "command the Fremen war" subsystem is now separately first-traced end-to-end — `command1.hsq`'s directory+string-pool format confirmed byte-exact and cross-platform-verified, `map.hsq`/`map2.hsq`/`tablat.bin` mapped to a confirmed wraparound-width-398 panning cursor, `onmap.hsq`/`attack.hsq` tied together via a self-patched loader trampoline, `docs/dune/amiga/strategic-map.md`), KGB (Cryo, 1992, "Conspiracy" — a sibling engine, now substantially solved: both decompressors, the PAC-based in-game room compositor (verified pixel-exact against a live savestate, incl. hotspot `id` semantics and on-demand objects), a cracked generic `.cma` runtime "state-cell accessor" primitive, `.cma`'s own 26-opcode script-bytecode VM (sections 0-4 + section 5's actor/trigger/response sub-grammars, 8290/8290 blocks byte-exact corpus-wide) with `SAY`/`SAY2` phrase resolution to real `.phz` text, and DOS's `.SQX` portrait/`PAC` sprite-bank containers. A combined room+hotspot+actor+dialogue-bytecode graph (`tools/kgb/dialogue-graph.ts`, one JSON per chapter for a planned `@xyflow/react` viewer) is now built and corpus-verified (0 dangling edges; node counts match every already-published corpus stat exactly — 139 actors/8290 blocks/1751 hotspots). Tracing it fully resolved a previously-"not traced further" open question: the `0xFF`-class hotspot's `LAB_02C5` call is a settled negative — it does NOT enter `.cma`'s actor/dialogue table, it feeds a canned French-grammar UI-feedback text composer sourced from `.cma` sections 9-12; a genuine bonus finding along the way is that bytecode opcodes `0x18`/`0x19` (`OBJ0`/`OBJ1`) call the *same* room on-demand-object toggle function the confirmed hotspot compound-id path uses, though the target room is never named in the bytecode so it's only a candidate link. Open: DOS `.M32` music, a handful of `.cma` opcode effects (`PLACE`'s operand bytes, `LAB_052F`'s transform, `LAB_0832`)) | `game-re-corpora/wyrm.md` |
