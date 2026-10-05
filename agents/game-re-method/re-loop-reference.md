# The RE loop — full reference and worked examples

> Moved verbatim from the always-loaded `game-re.md` during the 2026-10 restructure. `game-re.md` keeps the condensed rules; this file holds the full worked examples behind them. Read the section you need.

**1. Inventory & triage.** File sizes, magic bytes, strings, entropy profile,
repeating-structure scan (fixed-size record detection), header candidates.
For "strings found scattered through a region" with no known table
structure yet, histogram the gaps between consecutive string *start*
offsets before disassembling anything — a dominant stride value is a fast,
cheap test for a fixed-size record array (confirmed a 64-byte galaxy
name-table stride in FE2 this way, purely from string offsets).
Diff sibling files (13 per-level files that differ only in payload are a gift).
Classify: container vs flat payload, compressed vs raw, code vs data. Look for
a file catalog (`dir.0`-style: fixed-size entries of id + filename) — it maps
IDs to files and files to purpose. For a large or unfamiliar file/doc set,
delegate the first skim to `Agent: explorer` (see Tooling map) before
spending your own reasoning on it. **On any target with a code/data split
in its encryption or compression** (opcode-only ciphers — CPS2's, any
custom-CPU protection scheme — are common on arcade boards, but the same
logic applies to any format where code and plain data are stored/decoded
separately), run plain `strings` on the assembled, un-decrypted/
un-decompressed *data* view specifically hunting for game content (stat
labels, character/monster/item names, dialogue) before doing any
disassembly for that purpose — it's zero-cost relative to tracing code,
and finds real, human-authored content a disassembly-first pass can spend
much longer reaching only to land on more engine plumbing instead.
Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`): a `strings`
pass over the plain (undecrypted — CPS2 only encrypts opcode fetches)
maincpu data region found a complete 6-class D&D character stat-block
table and a 39-entry monster/bestiary name roster in under an hour, where
a prior session's much larger disassembly-tracing effort over the same
ROM only turned up more hardware register/palette plumbing. Disassembly
is still the right tool for engine *mechanisms* (loaders, dispatch,
register writes) — this is specifically about finding game *content*.

**2. Find the reader, not the format.** The game's own loading code is the
authoritative spec. Locate file opens (OS calls, filename strings), follow the
buffer to the decompressor and then to the consumer (blitter setup, DMA
pointers, struct field reads). Decompression loop structure tells you the codec;
blit/render setup tells you dimensions and layout. Screen-ID dispatch tables
tell you load order and file roles. Guessing dimensions by rendering at every
plausible width is the *last* resort, not the first.

**Follow the buffer past the read.** Loaders routinely transform data in place
between "bytes arrive" and "the consumer reads a field" — endian fixups,
relocation, in-place decompression, index rebasing — often gated on a "freshly
read from disk vs. cache hit" flag that makes a universal, once-per-load fixup
look like a rare conditional you can skip. The stored bytes are not necessarily
the bytes the field-extraction code sees. See
`partial-resolution-rate-is-noise.md`.

**On Amiga, check for a `HUNK_SYMBOL` block before doing anything else.** Many
commercially-released executables shipped with their symbol table intact (SAS/C
and Lattice both emitted one by default); parsing it gives every symbol's name
and exact file offset in one pass — vastly cheaper and more precise than
counting bytes through a large disassembly, and it often makes a binary close to
self-documenting. If the block is present, start there and let it name your call
sites for you. Parser trap and layout: `game-re-tooling/amiga.md`. This isn't
limited to proper multi-hunk executables: a **raw, headerless** blob extracted
verbatim by a custom trackloader (no `HUNK_HEADER` at all, just opcodes from
byte 0) can still carry a leaked `HUNK_DEBUG` source-line block if the
original build embedded one and the loader's own `DoIO` reads the file's
declared byte range as-is, with no hunk/debug stripping — confirmed on
Desert Strike (Amiga)'s loader, where a ~5.4 KB run of literal, readable 68k
assembler source (real labels, tabs, CR line endings) sat mid-binary and
source-confirmed a directory-record layout plus named several embedded
assets by their original path. A byte-classification scan (find every run
of 20+ consecutive printable bytes) is a cheap first move on *any* Amiga
binary, hunk-wrapped or raw, before assuming "no header block, so it's just
code."

**When the basic approach stalls** — raw overlays with no load address, tracing
a decrunch call to recover a runtime base, naming anonymous A4-relative `JSR`
calls through the SAS/C jump-table stubs, and copper-list data misread as code:
`Read ~/.claude/agents/game-re-method/finding-the-reader.md`.

**3. Hypothesis probes.** Small, throwaway Python scripts (numpy + PIL) in the
scratchpad — never committed. Render candidates as **greyscale first**; only
apply colour once the palette is independently confirmed. A wrong palette makes
a correct decode look wrong.

**4. Ground truth before "decoded".** Nothing is *confirmed* until it matches
an external oracle. Prefer the cheap ones first:
- a byte-exact structural invariant, e.g.
  `len(decompressed) == max(data_off + n_planes * plane_size)` holding across
  every file with zero deviation — or a blind, boundary-agnostic forward walk
  (accept each chunk only if its own internal indices/counts are
  self-consistent, no lookahead) that independently reproduces a boundary
  already confirmed by a code xref found some other way. A monotonically-
  incrementing-by-exactly-1 integer field inside a repeating block is an
  unusually strong version of this signal specifically for keyframe/
  frame-sequence animation data (unlike vertex/palette/index arrays, whose
  fields don't predictably increment) — scanning for the longest run where
  that field starts at 0 and increments by 1 each block finds the real
  keyframe array's start/length without knowing a variable-size header in
  advance, and correctly returns "no animation here" (zero-length) rather
  than garbage when a candidate block has no such run (confirmed on
  Valkyrie Profile 2 (PS2)'s per-bone quaternion keyframe arrays),
- the same asset from another platform's port, **or from an earlier session's
  own live capture** — a newly-decoded static structural format (e.g. a
  face/topology list) applied directly to real coordinate/field data an
  earlier, unrelated session already captured live, checked for zero
  degenerate output (repeated indices, zero-area triangles) and a plausible
  resulting shape, confirms both the new static decode and the old capture
  without a further live session (Carrier Command, Amiga: a static BSP-tree
  face list found a session after amiberry access was withdrawn was applied
  to a prior session's already-captured 60 real ship vertices, 0 degenerate/
  zero-area triangles, plausible hull silhouette),
- **the project's own already-shipped decoded tables in the same coordinate
  space** — for any new *spatial* structure (nav grid, tile map, zone
  partition, height field), the cheapest strong oracle is usually a table a
  prior pass already extracted, not anything external. Two shapes, both
  confirmed on FE Warriors (Switch): sparse gameplay markers must land
  *inside* the decoded region (53/54 `EventPoint` markers on walkable cells
  vs a ~17% walkable-fraction baseline; and 97.7% of 19,682 `ObjInfo`
  placements inside the sector partition's bounding box), while dense prop
  placements should trace its *outline* — plotting all 19,682 props over the
  grid drew the walkable boundary, which is a far stronger visual result
  than mere containment. Always pair it with a **null control**: re-run the
  same test on a deliberately wrong variant and require it to collapse to
  chance (transposing the grid took 53/54 to 26/54) — an oracle that can't
  fail isn't confirming anything. For a *field-role* claim the sharpest null
  control is the **sibling field**: run the identical oracle on the
  neighbouring fields of the same record, at the same position. Confirmed on
  Valkyrie Profile (PSX): a container record's effect byte was claimed to
  select an ambush, verified as 18/18 records naming a real enemy bundle at
  that effect value vs 0/326 at the other seven values *and* 0/347 for each
  of three sibling operand fields read in the payload field's place —
  reproduced independently on disc 2 (17/17). Note the oracle itself too:
  "does this integer land on a container slot carrying the format's own
  marker regions" is far stronger than range membership and usually costs
  nothing once the container is parsed. **When the "chance" baseline itself is a
  theoretical constant (e.g. mean|cos|=0.5 for uniformly-random 3D unit
  vectors), check the null control actually lands there before trusting
  a real-vs-theoretical comparison** — a real reference population is
  often not uniformly distributed (a face mesh's vertex normals cluster
  directionally, not spherically), which can make the theoretical
  baseline wrong on its own. Confirmed on Valkyrie Profile 2 (PS2)'s
  facial morph-target deltas: a single shuffle control landed at `0.351`,
  nowhere near the theoretical `0.5`. Fix: build a proper **empirical
  null** from 100-200 independent shuffles of the real pairing (mean +
  sd), then z-score the real value against that distribution instead —
  this is what turned an already-suggestive `0.101`-vs-`0.5` reading
  into a decisive, trustworthy `34.7`-sigma result,
- **two independently-located tables agreeing on a specific, non-trivial
  number** — e.g. a count, an index range, or a set of IDs derived from two
  different regions of a binary (or two different files) via unrelated
  methods, landing on the exact same value. Cheap and strong specifically
  because a coincidence this precise is astronomically unlikely: confirmed
  on Knights of the Round (CPS1)'s OKI MSM6295 sample directory — a Z80
  sound-program table (found via disassembly) and the OKI sample ROM's own
  hardware phrase table (found via a completely different, container-level
  scan) both independently came out to "exactly 78 valid entries, numbered
  1..78, zero gaps." Use this to validate a third-party tool's *structural
  hypothesis* (a table offset, a record layout) without trusting that tool
  as ground truth outright — re-derive the same number from the target's
  own bytes two separate ways and require them to match. **Scaled up, this
  is the strongest confirmation available with no external oracle at all:
  a container that stores the same facts twice.** An archive directory and
  its members' own per-record headers typically restate id, type, size and
  compression flag independently, making every single record a free
  cross-check — confirmed on FE Warriors: Three Hopes' Koei Tecmo RDB,
  where all five redundant fields agreed across **161,563/161,563** records
  with 0 deviations, settling the format without an emulator, sibling port
  or reference decoder. Whenever a format has both a directory and
  self-describing members, check them against each other before reaching
  for anything external. The same logic covers a **partition** as well as a
  number: if two or three unrelated signals sort a corpus into exactly the
  same subsets with 0 deviations, the classification is confirmed — Three
  Hopes' 583 G1A resources split 227/356 identically under a header enum,
  the spline opcode used, and whether the file shares a package with a
  model, three signals with no reason to agree unless the split is real.
  **The agreeing signals can be in the *code* rather than the data**, and
  that variant is cheaper to find: several independent consumers of one
  field each carrying their own hardcoded skip/special-case list for the
  same value set confirms the enumeration *and* the field's offset at once.
  Confirmed on Valkyrie Profile (PSX)'s room collision primitives — three
  functions with no call relationship each single out exactly `{4,5,6,8}`,
  written in different orders, one reading the byte from a scratchpad copy
  of the record and two straight from the record itself, so the offset is
  cross-checked by the disagreement in *how* they read it while the value
  set is cross-checked by the agreement in *what* they read (a fourth
  consumer zeroes the byte outright, pinning the offset a third way). No
  handler needs decoding for this to land.
  **When a resource resolves to an empty/reserved slot in an already-solved
  numeric-index archive, check a sibling container format already named in
  your own project's docs for the same id space before concluding the
  content must be hardcoded in the executable** — the second table is
  often not somewhere new, it's a format you already have a name for but
  never cross-referenced against the one it seems to duplicate. Confirmed
  on FE Three Houses (`chimera`): four DLC characters' `AssetIdTable`
  body/head fields resolved to genuinely-empty `DATA0.bin` slots, and a
  whole-decompressed-executable string search for their names came back
  completely empty (ruling out hardcoding) — but the project's own
  already-documented `INFO0.bin` LayeredFS-style patch index (a filename-
  keyed sibling format, never previously checked against `DATA0`'s
  numeric space) turned out to share `AssetIdTable`'s exact
  `BODY_BASE`/`HEAD_BASE` arithmetic (`entryId` 3233/3234/3684/3685
  matching one character's already-derived indices character-for-
  character), settling the resolution as fully data-driven. **The same
  logic needs no disassembly or container directory at all when both
  tables are plain content strings found by a `strings`-style scan**: two
  order-aligned string tables (e.g. a narrative/flavor-text table and a
  name/roster table) confirm each other exactly like two numeric ID
  tables do, PLUS confirm the extraction technique itself, PLUS can be
  cross-checked against an external domain fact for a third signal.
  Confirmed on Midwinter (Amiga, `hunter`): a 32-entry character-bio
  paragraph table and a separately-positioned 32-entry `"<title> <first>
  <last>"` roster table, both found by the same NUL-delimited printable-
  ratio scan with no code trace, matched 1:1 in identical order (bio\[i\]'s
  subject is always roster\[i\]'s name) with zero deviations — and matched
  Midwinter's well-documented "exactly 32 playable characters" design fact
  as a third, independent check,
- a third-party reimplementation or fan decoder (ScummVM, dunerevival,
  **vgmtrans** for arcade/console sound-chip and music-sequence formats
  specifically — its `src/main/formats/<Family>/` modules ship real,
  byte-for-byte ports of chip-emulation reference code (confirmed: its
  OKI MSM6295 ADPCM decoder is a direct port of MAME's own
  `oki_adpcm_state`) plus a per-game database (`bin/mame_roms.json`) of
  sound-driver table offsets/format versions across dozens of titles — a
  whole-format-family corpus, not a single-game reimplementation, so check
  it before hand-deriving any arcade/console sound format from scratch,
  etc.) —
  diff against its output; search for the **exact game**, not just its engine
  family, since a source-port's disassembly can hand you the algorithm
  outright (cracked FE2's cipher via `gbin/fe2` + `Frontier-1337`'s `fe2.s`).
  When the reimplementation is a project that **rebuilds a byte-identical
  ROM from source** (the `everything8215/ff4`/`ff5`/`ff6` family), don't stop
  at a CRC32 match on its declared build target — clone it fresh and run its
  own extractor (`make rip` / `tools/extract_assets.py`) against your actual
  ROM file. This is stronger than diffing against its checked-in source: it
  re-derives every offset from your literal bytes and gives an independent
  cross-check corpus for free (confirmed 3 times now — FFV, and both the
  FFIV-J and FFVI-J Japanese-original comparisons — each session's own
  from-scratch decoder was diffed against that fresh extraction, not just
  eyeballed against the project's prose). The technique isn't limited to
  ROM-rebuild projects — any reference extractor whose CLI happens to
  accept the same file layout your own `dumpsxiso`/equivalent extraction
  already produces can be run directly, with zero adaptation, against your
  real data files for a full independently-produced decoded corpus:
  confirmed on Parasite Eve II (PSX, `parasite`), where
  `GabeRealB/parasite-eve-2-decomp`'s Python `extract.py` took this
  project's own `STAGE0.HED`/`STAGE0.CDF`/`STAGEn.CDF`/per-disc-executable
  paths as literal CLI arguments and decoded all 448 real on-disc LZSS room
  packages; a fresh from-scratch TS port was then verified by comparing the
  SHA-1 *set* of its own decoded output against the SHA-1 set of that real
  run's output — 448/448 byte-exact, 0 mismatches, 0 unmatched extras,
  stronger than a spot-check diff since it also proves the port found
  every package the reference tool did and no spurious ones,
- a published fan walkthrough/bestiary claiming **data-table** (not just
  gameplay-observed) provenance — decisive for stat-block-shaped fields
  (HP, damage, price, resistance) that survive repeated disassembly-only
  negatives; see `published-walkthrough-numeric-oracle.md`,
- for a licensed-property stat-block table (D&D, a sports league, any
  source material with public, well-known rules) with no walkthrough
  available: **domain archetype plausibility** — cross-check every row
  against the license's own well-known archetypes, not just "do the
  numbers look plausible." See `domain-archetype-plausibility-oracle.md`,
- a public screenshot gallery for the **exact platform** (abandonware sites,
  longplay stills) — cheaper than an emulator capture and a stronger oracle
  than a sibling port for platform-specific artistic choices like colour
  (`WebFetch` on a raw image URL won't describe it, but does save the binary
  to a local path quoted in its response text, which `Read` then opens
  directly as an image; confirmed cracking a false "wrong DOS colour" bug
  report on Dune this way — see
  `same-name-cross-port-colour-mismatch.md`). When the game applies a
  runtime palette transform (day/night tint, fade), raw pixel matching
  scores ~0 even for the right asset — use the colour-invariant index-map
  consistency metric in `verification-techniques.md` instead,
- **an RE site's own viewer-generated asset PNGs, diffed pixel-exact** —
  when a fan tool ships rendered output (sprite sheets, map tiles, item
  icons) alongside its source, those images are ground truth for the *whole
  decode chain* (container → codec → pixel layout → palette): fetch one
  small asset and require 0/0 differing pixels on the visible ones (mask +
  colours) before trusting anything downstream. Confirmed on Drakkhen: the
  reference viewer's 16×8 dagger PNG verified mask 128/128 and colours
  27/27 against a fresh port of its own `Unpack` + sprite reader — and
  instantly discriminated the correct sprite palette from an embedded
  decoy one. Caveat: the site's images come from the tool's *own* data
  revision (see `reference-tool-data-revision-mismatch.md`),
- **an ordinal embedded in the game's own asset filenames** (`231_C_Evildragon.bin.gz`,
  `cha_icon_007_00.g1t`) — a number and a name in one string is free ground
  truth for any ID-space alignment, needs no executable and no statistics,
  and `ls` shows it to you in a second. Confirmed pinning FE Warriors'
  model-ID base (32/32 at a constant delta, 0 deviation). Where the ID space
  itself needs deriving rather than checking, use the exhaustive
  base-search-plus-shift-sweep in `verification-techniques.md`
  ("Self-verifying index-base alignment") — the search succeeding *is* the
  evidence, and shipping the search instead of the constant it found makes
  every later pipeline run re-assert it,
- or, **last resort** (real token cost to set up — see the amiberry entry in
  the Tooling map), an emulator screenshot of the real game showing the
  asset.
- **a factory debug/test menu's own "memory viewer" or "object list" label
  text, cross-checked against a structurally-derived address/offset** — a
  RAM-region name table (e.g. "PLAYER 1", "ENEMY WORK", "ITEM WORK") is
  cheap to find with the same plain `strings`-on-data-space pass that finds
  other game-content tables, and gives free, human-readable names for
  otherwise-anonymous structures when its own addresses land exactly on
  ones already derived from real code (a base register + struct
  offset/index). Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`):
  a factory "GAME WORK" debug menu's `[3-byte address][ASCII label]` table
  matched all 10 independently-derived object-pool base addresses
  (`stateBase + a5Offset`, with `stateBase` itself confirmed from a real
  boot-time `lea.l $addr.l,a5`) with zero deviation. **Caveat, not a
  contradiction:** a debug menu's own label is real data but is not
  automatically more authoritative than an already-traced consumer's
  semantic identification of the same region — see
  `debug-menu-label-vs-traced-consumer-conflict.md` when the two disagree.
- **for decoded audio, a quantitative "real signal vs. noise/bug" check
  when no emulator/human listening is available**: RMS + peak (not
  clipped-flat against the format's max range), distinct-sample-value
  count (not stuck at one repeated value), and lag-1 sample
  autocorrelation — real audio is strongly self-correlated sample-to-
  sample (|r1| far from 0, either sign), uncorrelated noise/a decoder bug
  scores near 0. Confirmed on Knights of the Round (CPS1)'s OKI MSM6295
  ADPCM: every decoded phrase passed, including one with a strongly
  *negative* r1 that looked suspicious at first — hand-dumping its raw
  sample values (not just trusting the summary statistic) showed a real
  decaying high-frequency buzzy hit/explosion SFX, not a decoder runaway.
- **a bidirectional save/restore mirror (loader code that copies a data
  region OUT to a backup location before a reload and back IN afterward) is
  direct evidence the region holds live/mutable runtime state, not static
  content** — static content needs no such preservation, since a fresh disk
  read always reproduces it identically; only state that changes during
  play must survive a reload. Confirmed on Deuteros (Amiga, `methanoid`):
  an already-documented `$66000->$13006` restore stub was believed
  one-directional (structural/arithmetic inference only, no disassembled
  copy loop); real disassembly (cross-verified with a second, independent
  disassembler — see `single-disassembler-src-dst-order-trusted-unverified.md`)
  found a second, previously-undocumented `$13006->$66000` commit routine
  gated on an already-confirmed low-memory sentinel, forming a genuine
  bidirectional mirror pair — narrowing an open "12-byte record format,
  unknown content class" item from "static table? script? stats?" to
  "live/mutable engine state (save-shaped), not a static content table."
- when the *output* format is a standard interchange format (glTF, PNG, WAV)
  rather than something game-specific, run its own reference validator as a
  free structural conformance check before calling the conversion done —
  e.g. `npx @gltf-transform/cli validate <file>.gltf` (Khronos's own
  validator, zero project dependency) caught a real umodel-sourced
  `ACCESSOR_MIN_MISMATCH` bug (declared accessor bounds were a lower-
  precision reparse of the exact float32 buffer values) that a "does it
  render" visual check alone wouldn't have surfaced (Drakengard 3 mesh→glTF
  pipeline, `flower` project).

A ~70% shape match is **not** decoded — record it as open with the best result.
Quantify verification: "0 RGB mismatches across 65,070 opaque pixels", "0
unknown palette indices across 864,128 rendered pixels" — not "looks right".

**Techniques for meeting this bar when the cheap oracles aren't available** —
raw byte-pattern censuses that confirm a struct without code/data
classification, validating constant tables against an already-confirmed corpus
manifest, numeric tables as their own oracle, and index/ID array validation:
`Read ~/.claude/agents/game-re-method/verification-techniques.md`.

**When every asset is addressed by a hash of its name** (KTGL KTIDs, Unreal
FNames, Wwise short IDs, most in-house `.rdb`/TOC designs) and no name table
ships: don't sweep known hash algorithms and don't guess candidate strings.
Harvest literal `(name, hash)` anchors from the engine's own property/
descriptor registration code, derive the algorithm algebraically from them,
and *measure* whether the real names are even recoverable before spending a
pass on it — `Read ~/.claude/agents/game-re-method/name-hash-recovery.md`.

**5. When hand-reimplementation fails, emulate.** For hostile custom
decompressors (backwards-reading LZ77 with embedded state, in-place LZSS with
relocation, self-modifying code), stop debugging your translation and run the
game's *own* routine under an emulator core, feeding it the compressed section
and dumping the output buffer. Worked example: `crawl/tools/bcdft_decompress/`
(musashi 68k core + ~200-line C harness runs the game's 496-byte engine after
multiple hand-ports failed). If that stalls too, escalate to `re-codebreaker`.
**This scales past one hostile resource to a whole open-ended runtime system**
(a proprietary sound driver, scripting VM, or similar you'd otherwise be
reverse-engineering mechanism-by-mechanism forever) — when the target runs on
documented, emulatable hardware, porting a full CPU + hardware core and
executing the real program can replace the whole reimplementation effort at
once. Worked example (FFVI SNES's AKAOSNES sound driver, `ceres`): `Read
~/.claude/agents/game-re-method/cpu-emulation-boot-harness.md` for when to
make this switch and the boot-harness techniques it needs (idle-loop
detection, load-handshake bypass, fixed-buffer resource placement) that a
plain decompressor harness doesn't. **A third shape sits between hand-porting
one routine and emulating whole hardware**: when per-unit behaviour ships as
hundreds of small compiled code blobs that call back into the engine (enemy AI
modules, spell scripts, per-actor state machines), interpret the CPU faithfully
and hook only the calls that leave the blob. `Read
~/.claude/agents/game-re-method/bounded-interpreter-with-hook-table.md` for
scoping it by census, why unsupported instructions and unrecognised call
targets must *raise* rather than no-op (that is what makes "this blob ran to
completion" a proof your hook table covers its call surface), and why first
execution doubles as a verification pass on the census itself.

**6. Promote.** Turn the verified probe into a committed extractor using the
project's shared libraries, regression-check its output **pixel-exact** against
the probe's, update the docs (including corrections), and keep the repo green
(`npm run lint`, `npx tsc --noEmit`, `npm test`, or the project's equivalents).
Delegate the lint/type-check pass on new/changed files to `Agent: reviewer`
(Tooling map) before calling it done — still run the test suite yourself,
that's outside its scope.

**7. Re-audit, periodically.** On a long-running campaign, closures made
early — before the project's own verification discipline matured, often
before dedicated per-finding verify scripts were standard practice —
are a real liability class, not a one-off risk. When a project's own
`TODO.md` runs dry of fresh candidates, pick an old `resolved` row whose
evidence is prose-only (no committed `verify-*` script re-deriving it from
raw bytes, or one checking only a handful of things on one disc/file) and
re-disassemble its whole cited claim fresh, from scratch, on every
platform/disc the project has. Confirmed worth doing repeatedly, not just
once, on `~/Development/valkyrie`: a first pass over the campaign's
earliest closure (`vp1psx-battle-damage-formula`) found 5 real,
previously undocumented or wrong mechanics; a second pass over a
different early row (`vp1psx-battle-cp-two-tables`) found the opposite —
every structural claim held up byte-exact, with exactly one small address
citation error (a hand-derived `lui`/`addiu` pair mistranscribed) to fix.
Both outcomes are useful: a clean re-confirmation is real signal too, not
a wasted round, and running the audit fresh (not diffing the old prose)
is what catches citation slips a same-technique re-read would just repeat.
**When even *that* pool runs dry** — every `resolved` `TODO.md` row has
either been audited already or already has a real from-bytes verify
script — widen the candidate pool past `TODO.md` entirely: a claim closed
with enough confidence on first pass never gets a row at all (nothing was
ever "open" to track), so `TODO.md`'s own row population is not a
complete inventory of under-verified claims. Grep the format spec itself
for confirmed sections with no cited `verify-*` script and an early
closure date; a 5th `~/Development/valkyrie` pass this way picked its
EXP/leveling system (closed 2026-08-22, no row ever opened, its only test
a synthetic fixture copied from the same doc prose) and, alongside a
clean re-confirmation, caught a real citation gap: a source-code comment
claiming a doc section established a resource's cross-disc byte-identity,
when that section actually established something else entirely
(`doc-self-cross-reference-before-fresh-disassembly.md`'s 26th instance).
