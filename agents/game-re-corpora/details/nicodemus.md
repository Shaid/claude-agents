# nicodemus — Phantasie I/II/III (SSI-published Amiga/Atari ST RPG series)

**Project root:** `~/Development/nicodemus`

Phantasie I (Amiga), Phantasie II (Atari ST — no Amiga port ever existed),
Phantasie III (Amiga). Dungeon/scripting formats documented in
`docs/phantasie/dungeon-format.md`, `docs/phantasie/scripting-engine.md`;
executable/monster/race/item table formats in `docs/phantasie/data-tables.md`.
**All three games have real, tested, end-to-end graphics + data-table
pipelines** (`tools/phantasie/`, `tools/phantasieii/`, `tools/phantasieiii/`,
all `supported: true`) — this is no longer a documentation-only project.
Dungeon/scripting is confirmed but not yet wired into the runtime engine
(`docs/phantasie/implementation-plan.md`'s Phase 3, "next" as of the last
status check).

**Phantasie I and II share one dungeon/scripting engine**, selected only by
a boolean flag; every offset, record format, and opcode below 0x14 is
byte-identical between them. Phantasie III uses a structurally-similar but
distinct engine (different header offsets, different grid size, messages
embedded in the dungeon file itself instead of a separate `MESSn` file, and
its own extended opcode range 0x14-0x1B).

Confirmed dungeon-file layout (P1/P2, grid 33×38 = 1254 B; P3, grid 24×30 =
720 B): fixed-position header fields (level byte, 10-byte encounter-index
table), a fixed-slot star (trigger) table immediately followed by the
action (script) table at an address that is *exactly* the star table's
declared capacity past its own start — confirmed as an arithmetic identity
between two independently-hardcoded constants in the reference source, not
a coincidence. P3 additionally chains a message-pointer table immediately
after its action table at the same kind of exact-capacity boundary, which
is why P3's action-table reader has no explicit terminator (P1/P2's does,
because P1/P2 keep messages in a *separate* file with nothing to bound the
action table against).

**A third-party fan tool's open-source parser was the primary oracle** for
this pass (a Windows dungeon/scripting viewer with full C# source,
fetched to an ephemeral scratch dir, never committed or reproduced
verbatim — see `romhacking-community-tools-first.md`, sharpened this
session to cover full-source fan tools generally, not just
compression-only reimplementations). Every offset and record-size formula
recovered from that source was independently re-derived byte-exact against
this project's own real `data/phantasie/amiga/dng*`/`mess*` and
`data/phantasieiii/amiga/D/dng*.dat` files before being written up as
confirmed — see the dungeon-format doc's "Confirmed" callouts for the
verification evidence (e.g. a message-pointer table's first resolved
address landing exactly at the pointer table's own declared end; a live
simulation of the action-table scan algorithm reproducing the reference
tool's terminator position across all ten P1 dungeon files).

The reference source's own inline comments flagged two real P2-vs-P3
engine divergences (a trap-damage formula left unfixed in P3 but corrected
in P2; an off-by-one message-index bug in P3's trap flavour-text lookup) —
preserved in the doc as confirmed original-game behavior quirks, not
reference-tool artifacts.

Six non-dungeon Phantasie I world/town files (`twns.int`, `maps.int`,
`out*.dat`, `scrolls.dtx`, `tamb.dat`) and five Phantasie III `D/`-folder
file types (`S1`-`S20`, `M0`, `M1`, `PLN1`-`PLN4`) have **no** reference-tool
coverage at all. Partial structure was recovered for several by inspection
alone (`twns.int`: a clean 292-byte town-record stride; `out*.dat`: a
confirmed null-terminated 40-byte-line point-of-interest text block at a
fixed offset; `scrolls.dtx`: a confirmed flat 40-byte-line text array).
Full inventory of what's solved vs. open: `docs/phantasie/dungeon-format.md`
§8-§9.

**Phantasie II is now fully byte-verified, not just extracted.** Its two
`.stx` Pasti floppy images were desectorized and extracted to
`data/phantasieii/atarist/extracted/disk{1,2}/` (59 files total; method,
container notes, full listing in `docs/phantasie/stx-extraction.md`; see
`game-re-tooling/atari-st.md` for the reusable extraction technique). A
follow-up pass then confirmed every P2-specific hypothesis carried from the
reference source against these real files:

- **`PHANT.PRG` executable tables** (`data-tables.md` §2): all five cited
  offsets (monster names, sprite offset/dimension tables, palette, race
  names) resolved byte-exact with **zero adjustment from the reference
  source's recorded values** — expected, since `PHANT.PRG` is the same
  Atari ST binary those offsets were originally recorded against, unlike
  P3's Amiga-vs-ST cross-binary mismatch (`data-tables.md` §4/§8; see
  `romhacking-community-tools-first.md`'s "same compiled binary" rule,
  sharpened this session).
- **`.pat` sprite plane layout** (`graphics-formats.md` §9): confirmed ST
  word-interleaved (interleave=2) for **both** `MSTR*.PAT` and `PARTY*.PAT`
  via pixel-level render (skeleton, orc, cobra, human/dwarf/ogre sprites
  all legible under Interleaved, all noise under P1's Planar) — including
  `PARTY*.PAT`, which an earlier pass had speculated might keep P1's raw
  layout because its file size matches P1's byte-for-byte. It doesn't;
  see `header-shape-ambiguous-pixel-encoding.md`'s sixth case, added this
  session, for why a cross-port size match can't settle a layout question.
- **`DNG1`-`DNG8`/`MESS1`-`MESS8`** (`dungeon-format.md` §7): the shared
  P1/P2 header/grid/star/action/message format decodes cleanly on all 16
  real files with zero failures, at the exact same offsets as P1. Also
  confirmed live in real data: P2's exclusive opcodes `0x14`-`0x17`
  actually appear in shipped `DNG*` action tables (up to `0x17`, "game
  won"), while all 10 real P1 `dng*` files' max decoded opcode never
  exceeds `0x13` — the documented P1/P2 opcode-space split is real
  behavior, not just an untested gate in the reference tool.
- **Save-vs-template question** (`stx-extraction.md` §6): resolved with
  direct evidence, not just the timestamp signal — see
  `save-file-not-asset.md`'s two sharpened techniques (byte-diffing a
  save file against its now-decoded pristine sibling format; a plain
  printable-string scan for player-chosen names). `DNG.SAV`/`DNGX.SAV`
  are confirmed near-byte-identical runtime copies of `DNG1` (6-10 bytes
  differing out of ~2048, matching documented one-use-deactivation/
  encounter-resolution semantics exactly); `GUILD.DAT` contains
  player-chosen character names; `TWNS.DAT` is a distinct smaller
  save-summary structure, not an overwrite of the still-pristine
  `TWNS.INT`. `OUT*.DAT`'s status stayed genuinely inconclusive (no
  sibling template to diff, no player-name signal found).

Phantasie II is no longer a "hypothesis carried from a reference source"
project for any of the above — it's independently byte-verified against
this project's own real data, the same bar P1/P3 already cleared.

**Item-name and monster-name tables, and the character-stat/combat
interpreter, are now independently located and code-level confirmed** —
previously only hand-transcribed from the reference tool's source, with
no cross-check against this project's own data at all
(`scripting-engine.md` §6, formerly flagged as a real gap blocking real
interpretation of several dungeon opcodes):

- **Item-name table** (181 sequential NUL-terminated strings, index 0 an
  empty-slot sentinel) located in **all three games' executables** by
  plain `strings`-grepping for common RPG item substrings
  (`SHIELD`/`SWORD`/`DAGGER`/...), then confirmed byte-exact by decoding
  every real opcode-`0x06` dungeon-script record across the project's
  full 29-file dungeon corpus (178 total distinct item-index references
  across P1/P2/P3, **zero out of range**). A cheap, general technique
  worth reusing on other engines with numeric-index item/entity opcodes:
  cross-reference a candidate string-table location against real
  script-driven index usage, not just plausibility of the strings
  themselves. `data-tables.md` §1.5/§2.6/§3.1, `scripting-engine.md` §6.1.
- **Monster-name table index space** cross-checked the same way (34
  distinct monster-index references across all three games, zero out of
  range) — the name tables themselves were already confirmed in a prior
  pass; this pass added the real-script cross-check. `scripting-engine.md`
  §6.2.
- **P1 `GetStat`/`SetStat`** (character-stat accessor) disassembled via
  the `amiga-disasm` agent, byte-verified against the real `game`
  executable: file offsets `0x116EA`/`0x11710`, a shared range-check
  resolver at `0x1142C` computing `charBase + charIndex*0x11A(282) +
  statIndex*2 + rangeConstant` — confirming the reference source's
  index-range hypothesis at the **code level**, not just against real
  script data. This also caught a real reference-tool limitation
  mistaken in a prior pass for genuine game-behavior ambiguity: P1
  opcode `0x12` ("Set character stat") is genuinely conditional and
  party-wide in the real game (`if GetStat(char,i) < v:
  SetStat(char,i,v)` for every living member); the reference tool's own
  interpreter just never implemented any mutation for this opcode. See
  `reference-tool-incompleteness-mistaken-for-game-ambiguity.md`
  (new lesson this session) and `scripting-engine.md` §6.3.
- **P1 combat hit/miss + damage application** — traced from data xrefs to
  combat message format strings (`"%s HITS"`/`"%s MISSES"`/`"%s TAKES %d
  DAMAGE"`) found via a plain `strings` scan. Hit/miss compare located and
  byte-verified at file offset `0xD782`; separate, structurally distinct
  player-damage (`0xEFF2`) and monster-damage (`0xF232`) functions
  confirmed, the player path reusing the same 282-byte character-record
  stride and `+0x18` alive-flag already confirmed for `GetStat`/`SetStat`.
  **A follow-up pass fully confirmed the RNG and both formulas**: the RNG
  is a plain LCG (`seed=(seed*3677+3) mod 32768`, file offset `0x2C874`)
  feeding a `0..100`-scaled roll wrapper; the to-hit compare and the
  damage-magnitude calculation both have every operation and operand
  *source* confirmed byte-exact (individual field/constant *semantics*
  are still open). `scripting-engine.md` §7.1a/§7.1b/§7.2a.
- **P2 (`PHANT.PRG`) and P3 (`PhantasieIII`) combat got their first
  traces too.** P2's hit/miss+damage block turned out **structurally
  near-identical to P1's** — same 58-byte monster stride, same `+0x2E`
  armor-field offset, same `*100/67` damage-scaling constants, byte-
  identical despite P2's different 318-byte character-record stride —
  strong confirmation that P1/P2's already-established shared dungeon/
  scripting engine extends to the combat formula itself; the specific RNG
  call site within that block wasn't pinned down. P3 (an independently-
  built engine variant, not a straight port) has its **own RNG fully
  confirmed** — a different concrete LCG (`seed=(seed*25173+13849) mod
  65536`, the well-known "quick and dirty" textbook constants) behind a
  parameterized `Random(range)` wrapper — and its hit/miss dispatcher is
  located, but its formula is visibly richer (multiple stat tables +
  difficulty-conditional adjustments) and wasn't fully enumerated.
  `scripting-engine.md` §7.4/§7.5.
- Two reusable Amiga HUNK-tracing techniques from this pass, folded into
  `game-re-tooling/amiga.md`: resolving a pre-relocation `JSR` operand to
  its real target hunk via the hunk's own `HUNK_RELOC32` list (settled an
  ambiguous "two candidate RNG call sites" lead definitively — one was
  the real LCG, the other's return value was provably dead before the
  next instruction that could read it); and a brute-force `PEA d16(PC)`/
  `LEA d16(PC)` xref scan for position-independent single-CODE-hunk
  binaries where `HUNK_RELOC32`-based lookup finds nothing at all (P3).
- Also folded into `game-re-tooling/amiga.md`: IRA's `-preproc` pass
  misclassified the `GetStat`/`SetStat`-containing function (raw hunk 99
  of this 240-hunk binary) entirely as `DC.L` data, with no `.cnf` even
  emitted — a fourth distinct `-preproc` failure shape beyond the three
  already documented there. Worked around by extracting that hunk's raw
  CODE bytes and disassembling standalone with `r2 -a m68k -b 32 -q -n`,
  cross-substituting IRA's already-resolved relocation-comment symbol
  names by hand.

**A follow-up pass fully disassembled the `GetStat`/`SetStat` resolver
end-to-end and found the mirror "monster attacks player" combat
branch.** Previously only the resolver's range *boundaries* were
code-confirmed; this pass extracted every branch's own formula, giving a
byte-exact `statIndex → character-record-byte-offset` table across the
whole valid domain (`1`-`164`, `scripting-engine.md` §6.3(c)). This let
five combat-formula fields that were previously bare, unplaced byte
offsets get bound to exact `statIndex` values without needing an English
name (`char.+0xC`→`7`, `+0xF6`→`56`, `+0xF8`→`57`, `+0xFA`→`58`,
`+0xF2`→`163`) — a reusable pattern: an abstract accessor's resolver, once
fully disassembled, can name *any* raw field offset found elsewhere in
the same binary, even without cracking the display routine that would
give it an English name. That display-routine search was itself
exhaustively tried this pass and came back conclusively negative:
`GetStat`/`SetStat` have exactly 2 call sites in the whole binary (found
via a whole-binary `HUNK_RELOC32` caller scan, `game-re-tooling/amiga.md`),
neither a display routine — the character-sheet UI reads character-record
fields directly, bypassing the abstract accessor entirely. The
mirror "monster-attacks-player" hit/miss+damage branch (previously "not
located") was found in the same dispatcher function (file offset
`~0xD91A`-`0xDCAA`, same hunk as the already-known party-attacks-monster
block) and is now fully formula-confirmed, reusing the same RNG/`roundedHalf`
helpers. `roundedHalf()` itself turned out to be a **Newton's-method
integer square root** (confirmed via full disassembly + hand-simulation),
not "roughly half the roll" as previously guessed — see
`helper-name-guess-vs-instruction-shape.md`, a new lesson from this pass.

Individual field-semantics still open: English names for the now-bound
`statIndex` values (7/56/57/58/163 for P1's core combat fields — a real
`re-codebreaker`-worthy gap now, not just unexplored), monster-side fields
(`+0x2E`/`+0x14`/`+0x38`/`+0x16`, not `GetStat`-addressable at all), the
`+0x146`/`+0x138`/`+0x132` per-character status-array semantics (narrowed
this pass to "small combat-stance/status codes," not fully enumerated),
and the `0x43`(67) damage constant — see `docs/phantasie/TODO.md`.

**P2 and P3's combat formulas are now both fully confirmed too**
(`scripting-engine.md` §7.4/§7.5/§7.5.1). P2's RNG call site (`JSR $FD40`
inside the shared combat block) turned out to be **a different concrete
algorithm from P1's**, not just a different LCG seed: a 7-word circular
buffer that sums all 7 current slots every call, rotates one slot with the
new sum, and returns half of it — despite P1 and P2 sharing the same
dungeon/scripting engine byte-for-byte otherwise (including this exact
combat formula's field offsets and constants). **"Shares the scripting
engine" does not imply "shares the RNG algorithm"** — worth checking
independently on any future shared-engine pair in this family, not
assumed from the engine link alone. P3's to-hit/damage formulas were
fully enumerated via a corrected `HUNK_RELOC32` call-target-resolution
technique (`target = rawOperand + 0x28`, the CODE hunk's own file base) —
this project's `HUNK_RELOC32` handling for single-large-CODE-hunk PIC-style
Amiga binaries generalizes beyond just resolving relocated call targets:
a genuine `re-codebreaker` escalation on this project also found that a
`HUNK_DATA` block's own declared size being *smaller* than the
`HUNK_HEADER`'s separately-declared allocation size for that hunk is SAS/C's
merged `data+bss` encoding, not a parse bug — see
`hunk-data-shorter-than-declared-is-merged-bss.md`, a new lesson from this
session.

**P3's race name table is now located and confirmed** (`data-tables.md`
§4.1, `readP3RaceNames()` in `exe-data.ts`) — 18 names (including a
"Random" character-creation menu option, not a real race, resolving the
prior pass's `Count=18` vs. "16+1 new race" arithmetic mismatch) found by
grepping the mixed-case string block directly, then the `HUNK_RELOC32`
"reversed" reverse-lookup technique (search every hunk for a stored
longword equal to the string's own known hunk-relative offset) to find
the pointer table addressing it — see `game-re-tooling/amiga.md`'s
sharpened reloc32 section for the general technique and how it
complements (not contradicts) the PC-relative brute-force fallback found
in an earlier pass on this same binary. The parallel per-race
bank-sprite-cell index table (the ST reference source's
`bankSpriteIndex*2`) remains **not located** — see `data-tables.md` §4.2
for the two search approaches tried.

**Two `monsinfo.dat` fields long assumed to be item-table indices turned
out to be raw combat stats instead** — `Weapon`/`Armor` (renamed
`weaponRating`/`armorRating`), diagnosed via cross-stat Pearson
correlation against already-confirmed `hp`/`attackRaw` (r=0.77-0.96) —
see `cross-stat-correlation-refutes-index-hypothesis.md`, a new lesson
from this session. The monster `spell1`-`spell3` fields, by contrast,
**are** confirmed real indices into a newly-decoded 58-entry P3 spell
name table (`0x4E74`-`0x513E`), with a thematically clean resolve across
all 80 monsters. `inititem.dat`'s per-item field semantics remain open
even after a full 181-row correlation pass; an earlier pass's "16-bit
paired field" reading was retracted as a sparse-data artifact — see
`sparse-table-creates-spurious-multibyte-field.md`, also a new lesson
from this session.

**`data/phantasieiii/` now holds the actual scanned 1987 SSI rule
book/manual** (no text layer), the strongest oracle this project has —
see `implementation-plan.md`'s primary-source addendum and
`scanned-manual-paraphrase-needs-reverify-and-diff.md` for the general
lesson it produced. Used this pass to: confirm P3's 181-entry item table
byte-for-byte against the manual's own 120-item catalogue (117/120 exact —
2 cosmetic spelling variants plus one genuine, non-cosmetic divergence at
indices 81/82, manual `"Knife +1/+2"` vs. game data `"Dagger +1/+2"`,
documented not resolved); confirm the 57-entry P3 spell table against the
manual's own spell table plus two independent body-text passages (naming
the table's own `53`="UNUSED SPELL (vision)" gap and `57`="Divine Aid");
and locate the P3 character record's 9 skill-pair names as **real
on-screen strings** in `PhantasieIII` itself (`Attack, Parry, Swimming,
Listen, Find Trap, Disarm Trap, Find Item, Pick Lock, Fire Bow`, found via
the same reloc-resolved string-by-ID pointer table used for the race
names) — binding those names to the specific `+0x30`-`+0x53` character-
record offsets is recorded as a strong hypothesis, not confirmed (the
draw-routine trace didn't complete). The manual's HP/MP-by-class-and-level
charts and body-location damage system (6 locations ×
Okay/Injured/Broken/Gone) were both tested directly against candidate P1
fields and refuted — see `scripting-engine.md` §7.5.2.

**Phantasie II's `.PIC` full-screen picture format is now solved** — six
files (`COVER1.PIC`, `COVER2.PIC`, `PELNOR.PIC`, `DECOR.PIC`, `FINAL2.PIC`,
`CROWD.PIC`) that had sat extracted-but-undecoded since the extraction
pass above. No reference-tool source exists for this format at all
(unique among every format in this project). Layout: the same ST
word-Interleaved-by-2 convention already confirmed for `.PAT` (not P1's
Planar layout, despite two files sharing P1's exact 32,000-byte size).
Palette: **three separate sources across two different executables**,
each found via disassembly, not analogy — `START.PRG` (a small
2,567-byte title-sequence bootstrap distinct from the main game engine,
governs `COVER1.PIC`/`COVER2.PIC`), and two distinct tables inside
`PHANT.PRG` itself (a town palette for `PELNOR.PIC`, and the
already-confirmed monster/race palette reused for the
`DECOR.PIC`/`FINAL2.PIC`/`CROWD.PIC` ending sequence — mirroring how P1's
own `decor.pic`/`final.pic` also reuse *their* monster/race palette, a
real cross-game authoring convention, not coincidence). One file
(`CROWD.PIC`, the only 3-bitplane file among six 4bpp ones) loads to a
runtime BSS buffer rather than the screen directly, with a file-exact
(not generic) read length — both signals it's composited differently
from the other five, though the exact compositing step wasn't traced.
Full evidence: `docs/phantasie/graphics-formats.md` §10. This pass also
established, for the first time in this project, **GEMDOS/TOS `.PRG`
disassembly via Capstone** as a working technique distinct from the
existing Amiga HUNK tooling — see `game-re-tooling/atari-st.md`'s new
section, plus two new general lessons:
`buffer-offset-arithmetic-confirms-partial-image-placement.md` (a
blit-target buffer-offset computation is a free, code-derived dimension
oracle for an ambiguous raw-picture byte count) and a sharpened
`tile-grid-dimension-needs-render-not-just-bytecount.md` (a wrong *width*
on a flat raw picture — not just a tile grid — can render as recognisable
content repeating in bands, a third failure mode beyond clean-render vs.
noise; a byte-level row-repeat check distinguishes it from genuinely
tiled source art).

**Phantasie I's town/world-map layer is now solved and code-confirmed** —
previously the project's largest open format question and (per its own
`implementation-plan.md`) a prerequisite for a playable slice, since the
real game flow is character creation → town → world map → dungeon, not
dungeon-first. `dungeon-format.md` §8.2/§8.3 now carries the full spec;
decoder + 14 real-byte tests at `src/assets/formats/outdoor.ts`.

- **`maps.int` (9,360 B)** is not a grid at all: **18 × 520-byte section
  grids**, block `k` byte-identical to the leading 520 bytes of the `k`-th
  `out*.dat`. A prior pass had it filed as "no clean square-grid
  factorization, open/unresolved" — see
  `oversized-file-may-be-concatenated-sibling-prefixes.md`. Block order is
  by *ordinal over files that exist*, so blocks 16/17 are sections **18/19**
  (there is no `out17.dat`).
- **`out*.dat` (2,500 B fixed record, read in one `Read()`)**: 20×26 terrain
  grid at 0 (`byteOffset = (25 - engineRow) * 20 + col`, stored bottom-up),
  15 × 5-byte POI records at 520, 10 × 40-byte text lines at 595, and a
  **map display list at 1000** (`u16 bg`, then `0xFFFF`-terminated
  `{count, iconIndex, count × {u16 x,y}}` groups) plotting 128-byte icons
  from a bank at `game+0x196BC`. The engine **saves these files back on
  every section exit** — they are live save state, and `maps.int` is the
  pristine master a separate `backup` utility restores.
- **Sections tile 4-wide with a one-cell overlap** (`newSection = section −
  4·dRow − dCol`; arrival coords 0/19/25), giving a 77 × 126 world;
  sections above 16 are walled off with a "THE RIVER STYX" refusal.
- **Tile byte = `class*10 + variant` consumed entirely by branch chains, no
  lookup table anywhere**, and `+120` is a fog-of-war flag written back by
  the reveal routine — *not* a graphics bank. Notably this diverges from
  P3's `.set`, where the same-shaped map byte **is** a rendering index; see
  `decomposable-data-byte-may-have-no-lookup-table.md`.
- **`twns.int`'s map-coordinate question is closed**: town position lives in
  the `out*.dat` POI record, not in `twns.int` (whose first 32 bytes are
  byte-identical across all 11 populated records — a shared shop/price
  template). Still open: the rest of that record, the outdoor icon bank,
  terrain-class English names, and the POI record's `+3` byte. See
  `docs/phantasie/TODO.md`.

Verification worth reusing: a 99/99 cell-for-cell bijection between
code-derived "event" tiles and the POI records, and a 31× rare-value
enrichment test that settled grid width/orientation/field order before any
disassembly — both written up in `game-re-method/verification-techniques.md`.

**Phantasie II's world-map layer is now solved too — and it is Phantasie I's
format with exactly two constants changed** (`dungeon-format.md` §8.6;
decoder `PHANTASIE2_OUTDOOR` in `src/assets/formats/outdoor.ts`, which now
carries both games behind one `OutdoorLayout` record, 17 new real-byte
tests). `MAPS.INT` = 17 × 520-byte grids, byte-identical to all 17
`OUT*.DAT` prefixes (17/17); `OUT*.DAT` is a fixed 3,000-byte record whose
first 995 bytes are byte-for-byte P1's layout. The only differences in the
entire format are the record size (3000 vs 2500) and the display-list offset
(1500 vs 1000) — everything else, traced by disassembling `PHANT.PRG` with
Capstone, is *instruction-for-instruction* identical to the Amiga `game`
binary: `GetTile`'s grid math, the 5-byte POI scan (including the same latent
over-read past the 15-record table), the 3-arm message-length encoding, the
`+120` fog flag, and `ChangeSection`'s `newSection = section − 4·dRow − dCol`
mosaic arithmetic. P2's 17 sections sit sparsely on a 4 × 8 mosaic (77 × 201
world); every edge facing one of the 15 absent slots is impassable ocean
(29/30 edges 100%), which is the mechanism that makes them unreachable. P2's
POI data also gives *cleaner* confirmations than P1's own for two shared
hypotheses: ten town cells with ten consecutive ids 1-10, and class-5
dungeon-entrance ids taking exactly 8 distinct values against exactly 8
shipped `DNG*` files.

This pass also **corrected a prior session's verdict on `OUT*.DAT`**, which
had been closed as "confirmed save-mutated, not pristine content — there is
no known pristine P2 counterpart". The residue evidence was real but all of
it sits in the 995-1500 gap the engine never reads back, and `MAPS.INT` is
the pristine master. See the sharpened `save-file-not-asset.md`.

**Phantasie III has no `out*.dat`/`maps.int` equivalent at all** — confirmed,
not merely unfound (`dungeon-format.md` §9.0). Its overworld is the single
global 50 × 75 `Graphics/phantasy.set` map array already documented in
`graphics-formats.md` §5; there is no per-section container, no mosaic, and
no section-transition arithmetic anywhere in `PhantasieIII`. An exhaustive
scan of the binary's `D/`- and `Graphics/`-prefixed strings yields the
complete resource-name list, and it contains no `OUT`, `MAPS` or `TWNS`.
**P3's overworld location metadata is now solved, and the "it's in the map
values" hypothesis is refuted in its mechanistic form** (`dungeon-format.md`
§9.0.5). P3 identifies every named town/dungeon/inn by a chain of ~34
**hardcoded `(x,y)` comparisons** at hunk-0 `0x9C6A` (`LocateSpecial()`),
which never reads the map array at all. The map byte reaches only two
consumers in the entire 137 KB CODE hunk — the 9×9 viewport blitter at
`0x9B82`, which pushes it **verbatim** to the tile blitter (this is the
first code-level confirmation of `graphics-formats.md` §5.3's
column-index reading, previously structural-only), and a terrain-class
range chain at `0xA4A6` whose 19 named classes (`Meadows`, `Forest`,
`Hills`, `Mountains`, `Desert`, `Pathway`, `Water`, `Ocean`, `A bridge`,
`Dense Fog`, `Bright mist`, `The River Styx`, `Lava`, `Black path`,
`Mist`, `Steam`, …) come from a pointer table at hunk-1 `0x1750`. The
distinctive cells *are* the 30 named locations one-for-one (values `25`-`52`
and `54`, bijection-verified against occurrence counts, one value shared by
two inns) — but as marker **artwork**, not as a lookup key; see the new
case (c) in `decomposable-data-byte-may-have-no-lookup-table.md`. All 30 are
now bound to concrete names, and the `a`-`k` dungeon-file letter mapping
(long recorded as "ordering assumed, not confirmed") is resolved from a word
table at hunk-1 `0x22AC`: indices 1-11 → `J H E D A C B K I F G`.

Four P3 `D/` file families were resolved or corrected on the way, all
code-traced in `PhantasieIII` (hunk-0 addresses; file offset = address +
`0x28`): `D/M0`/`M1` are **three-track music** (`0xFF` track separators,
830/659-byte declared reads, byte-exact — previously mis-filed as "a
border/divider graphic asset", see the new
`padded-file-tail-describes-padding-not-content.md`); `D/W0`-`W4.cmp` are
ordinary `.cmp` scene backdrops (two god-on-throne scenes, a town street,
shop doorways — rendered, and `w3`/`w4` share `phantasy.set`'s exact
palette); the `D/S1`-`S20` scroll loader reads 1,050 bytes with message ids
121-140 → 1-20 and **special-cases `S6`**, resolving that file's
long-standing outlier-size question; and `PLN3` is a two-byte flag file the
engine reads and writes.

> **Correction:** that pass also recorded `PLN1`-`PLN4` as "not terrain
> grids — refuted", on the strength of their byte values being disjoint from
> `phantasy.set`'s 196-value map space. **They are map arrays**, in exactly
> that format — see below. `value-space-disjoint-refutes-same-kind-table.md`
> has been rewritten around this failure: disjointness refutes "the same
> table", never "the same format", because a partitioned value space makes
> two instances covering different regions *expected* to be disjoint.

**`D/M0`/`M1` and `D/PLN1`/`PLN2`/`PLN4` are both now fully solved**
(`dungeon-format.md` §9.0.2-§9.0.2.6 and §9.0.3.4):

- **Music.** The driver is a genuine AmigaOS vertical-blank interrupt
  server, self-named `"VertB-Timer"` (`AddIntServer(INTB_VERTB=5, …)`,
  installer at hunk-0 `0x0D4A`, `is_Code` = `0x0DF8`, tick at `0x2192`), so
  one tick is one video frame. 24-command byte grammar with two nesting
  levels of loop; note events are `(note, duration)` where bit 7 of the
  duration byte is a **tie** flag and `frames = ((dur & 0x7F) + 1) ×
  multiplier`. The period table at hunk-1 `0x0640` is **ProTracker's,
  byte-identical**; waveforms are 8-sample cycles repeated 8×, which puts
  note 57 at A4 = 440.4 Hz under the NTSC clock. Four-phase ADSR, rate
  tables indexed by a master-volume row. Instrument 3 is 4,000 bytes of
  noise **generated at boot by the game's own already-documented LCG**
  (`seed*25173+13849 mod 65536`, hunk-0 `0x1C24`) — two subsystems traced
  from opposite ends of the binary landing on the same seed word is a free
  cross-check on both. Verification: all six tracks parse byte-exactly with
  0 unknown commands across 1,489 bytes, and all 705 notes' durations
  satisfy `dur+1 ∈ {1,2,4,6,8,10,12,16}` (powers of two plus dotted values)
  — a property only true under the correct reading.
- **`PLN*`.** `D/PLNn` is the map array for engine map id `n`: `PLN1` =
  Castle of Light and `PLN2` = Castle of Dark (9×9, 81-byte read), `PLN4` =
  the Netherworld (31×16, 496-byte read), loaded by the map-switch routine
  at hunk-0 `0x1EB1E`. Map id 3 is unused, which is why `PLN3` alone is a
  stray 2-byte flag. 100% of cell values fall in the terrain classifier's
  own bands, and 6/6 unclassified marker cells sit on `LocateSpecial()`'s
  hardcoded coordinates for that map.

Two general findings from that pass, both now folded into lesson files.
**The 128-byte padding filler is not arbitrary — `fillerByte ==
contentLength mod 128`, 58/58 files, zero deviations** (see
`padded-file-tail-describes-padding-not-content.md`), which reproduces every
code-traced read length in the game and handed over the two unknown ones.
And the `PLN*` item was cracked not by its `re-codebreaker` escalation but
by a *sibling* subagent's unrelated overworld trace mentioning the
map-switch routine's 9×8 and 31×15 grid geometries — 81 and 496 cells,
matching the two padding-derived content lengths exactly (see the new
`new-size-constant-is-a-cross-item-join-key.md`). The escalation was stood
down; the multi-session "these files are inert" negative failed because a
**second, live `D/PLNX` template string** existed at hunk-0 `0x6B4E`
alongside the dead utility's copy at `0x7253` (see the new
`filename-template-string-may-have-a-second-live-copy.md`).

**P3's `.cmp` palette semantics are now fully code-traced, and the previous
"embedded palette, decoded correctly" verdict was wrong for 6 of 13 files**
(`graphics-formats.md` §2 correction + §4.5, both dated 2026-08-11).
`loadCmp()` (file `0x1264`) reads *every* `.cmp` header palette into one
shared global scratch (`DATA+0x2AEE`); the caller decides its fate.
`loadBanks()` (`0x7F64`) copies that scratch to a per-bank slot for banks
0/1/2 only, and **only slot 0 (`heros.cmp`, `DATA+0x2BCE`) is ever
installed** — slots 1/2 have exactly one reference each in the binary
(their own store) and banks 3-6 aren't copied out at all. So all seven
monster/party sprite banks render under `heros.cmp`'s palette:
`giant1.cmp` is a grey-blue dragon and a green giant, not the purple/blue
pair previously documented. The full per-screen map (5 live slots, 2 dead)
came from counting callers of the palette primitive — `LoadRGB4` has
**exactly one** caller in the 175 KB executable, with no `SetRGB4` and no
`$DFF180` write anywhere, so `setPalette()`'s 13 call sites are the
complete answer to "what colours are on screen when". Verified pixel-exact
against Kroah's sprite-viewer PNGs: **0 mismatches / 384,000 pixels** for
the six banks, versus 36,487 under their own palettes, with four scene
`.cmp` files as a discriminating control group (0 under their *own*
palettes; 55,591 wrong under the substituted one). Two new/sharpened
lessons: `embedded-palette-not-the-installed-palette.md`, and a mixed-
addressing-root case added to `negative-from-addressing-root-not-shapes.md`
(this binary uses A4-relative *and* reloc-patched absolute addressing in
the same functions, so the dead-slot negative needed both censuses).

Same pass corrected P3's **channel ramp**: `setPalette()` (`0x11D6`) does
`(word & 0x0777) << 1` before `LoadRGB4`, so each 3-bit ST nibble `n`
displays as `2n/15` = 8-bit `34n`, **not** the Atari ST's own `n*36.43`
(brightest is `0xEE`, not `0xFF`). P3 is an Amiga port of ST data, so the
"ST-sourced containers keep the ST lookup" rule holds for P2 (a real Atari
ST binary) and fails for P3. The mask is lossless on shipped data —
288/288 palette words across 18 embedded P3 palettes have a zero high
nibble and all channel nibbles in 0-7 — which is itself a free structural
confirmation of the palette field layout. Carried open: `Anatomy2.csh` and
`Scroll.csh` are code-confirmed *never* to have their own palettes
installed, but their host screen wasn't traced (`docs/phantasie/TODO.md`,
`gfx-p3-csh-host-palette`).

Tooling note: `game-re-tooling/atari-st.md`'s Capstone `.PRG` disassembly
technique — established on a prior pass for the `.PIC` graphics subsystem —
transferred to an entirely unrelated subsystem (world-map loading, file I/O,
movement dispatch) with zero friction. The `file_offset = 28 + address`
identity and the shared-trap-trampoline caveat both held.

**P3's three non-overworld "plane" maps (`D/PLN1` Castle of Light, `D/PLN2`
Castle of Dark, `D/PLN4` Netherworld) are now wired into the asset pipeline
and viewer, not just decoded as grids.** Two things a prior pass had left
genuinely open are now settled:

- **Same 250-tile bank as the overworld — confirmed, not a separate art
  asset.** The prior doc's "their tile bytes index a different buffer
  (`$295C`), so whether they share `phantasy.set`'s bank is untested" had
  conflated two unrelated globals: `$295C`/`$2964` hold the raw map-**cell**
  bytes (genuinely different per map) while the tile-**art** bank pointer
  (`$290C`) is a separate global written exactly **once** in the whole
  137,352-byte CODE hunk — a one-time boot allocation, always filled from
  `Graphics/phantasy.set` — with its only two consumers (`LoadTile` at
  `0x3834` and a masked-overlay sibling at `0x378A`) each having exactly one
  caller, both inside the single shared 9×9 viewport blitter (`0x9B82`).
  See the new `doc-blocker-cites-wrong-buffer.md` lesson.
- **No fourth non-overworld map exists — confirmed by exhaustive write
  census, settling a domain expert's "there might be a fourth, it's been a
  while."** The active-map-id global (`$28C2`) is written by exactly seven
  call sites across the whole binary, and every one writes only `{0, 1, 2,
  4}` — `3` never appears, so `D/PLN3`'s stray 2-byte-flag-file status
  (§9.0.3) is provably not an accident of missing content. New worked
  example in `negative-from-addressing-root-not-shapes.md`.
- Two previously-unresolved computed `LocateSpecial()` name-index arms
  (flagged "not disentangled" — `dungeon-format.md` §9.0.5.5) are now both
  solved: the shared castle-arrival arm computes `14 + $28C2` → town index
  15/16 ("Light"/"Dark"), and a second, previously unnoted arm computes
  `9 + $28C2` → dungeon index 10/11 ("The Castle of Light"/"The Castle of
  Dark"), both confirmed byte-exact against the executable's own name
  tables.

New format modules `src/assets/formats/pln.ts` (grid decoder) and
`src/assets/formats/p3-planes.ts` (Netherworld terrain re-banding
classifier + plane-gated location table), a new pipeline step
`tools/phantasieiii/build-castle-maps.ts`, and 31 new real-byte tests.
`tools/viewer/map-viewer.ts` needed **zero** logic changes — its earlier
generalization for the overworld (mosaic fields optional, terrain-art
strip optional) already covered a 9×9/31×16 single-grid map with no
mosaic. Full evidence: `dungeon-format.md` §9.0.3.6.

**All three games' data tables (monsters, races, items, spells, skills) are
now published end-to-end, not just decoded.** Previously the decoded JSON
was stuck in Stage 1 (`data/extracted/`, gitignored, internal-only). This
pass: (1) added the two missing P1/P2 item-name decoders
(`readP1ItemNames`/`readP2ItemNames`, reusing the existing
`readSequentialCStrings` helper — zero new RE, the offsets were already
confirmed in `data-tables.md` §1.5/§2.6); (2) added a `readP3Items()` merge
helper that combines three separately-indexed P3 tables (name 0-180, stats
0-100, price 0-180) into one record set, correctly emitting `null` — not a
fabricated `0` — for the id range the stats table doesn't cover; (3) added
a new Stage 2 build step per game (`tools/<game>/build-data-tables.ts`,
following the existing `build-dungeons.ts` module pattern — independently
re-derives from raw game files rather than reading Stage 1's JSON, keeping
the two stages decoupled) that republishes every table into
`public/assets/<game>/<platform>/` with `type: 'data-table'` manifest
entries; (4) built a new generic `DataTable.astro` component for the `www/`
Starlight site (build-time `readFileSync` of a JSON manifest + a
`define:vars` search-filter script, modeled directly on the existing
`SpriteGallery.astro` pattern) and wired it into new/updated
`data-tables.mdx` pages for all three games. This `DataTable.astro`
shape (auto camelCase→Title-Case column labels, array-valued cells
rendered comma-joined, `null` rendered as an em dash rather than blank)
is reusable prior art for any other seer project's www site that wants a
generic browsable-table component — see `www/src/components/DataTable.astro`.

While wiring this, found and fixed real staleness in `www/`: five site
pages (data-tables, sprites, graphics, status, index for phantasieiii, plus
`docs/phantasie/implementation-plan.md`) still described the P3
race-sprite-cell table and `inititem.dat`'s field semantics as
open/unresolved, when the raw `docs/phantasie/data-tables.md` had already
resolved both in a prior session (§4.2, §6.4) — the public site simply
hadn't been updated to match. See the new
`curated-site-page-drifts-from-corrected-raw-docs.md` lesson.

## Lessons sourced from this corpus (full list)
`romhacking-community-tools-first.md`, `header-shape-ambiguous-pixel-encoding.md`, `save-file-not-asset.md`, `reference-tool-incompleteness-mistaken-for-game-ambiguity.md`, `helper-name-guess-vs-instruction-shape.md`, `hunk-data-shorter-than-declared-is-merged-bss.md`, `cross-stat-correlation-refutes-index-hypothesis.md`, `sparse-table-creates-spurious-multibyte-field.md`, `scanned-manual-paraphrase-needs-reverify-and-diff.md`, `buffer-offset-arithmetic-confirms-partial-image-placement.md`, `tile-grid-dimension-needs-render-not-just-bytecount.md`, `oversized-file-may-be-concatenated-sibling-prefixes.md`, `decomposable-data-byte-may-have-no-lookup-table.md`, `padded-file-tail-describes-padding-not-content.md`, `value-space-disjoint-refutes-same-kind-table.md`, `new-size-constant-is-a-cross-item-join-key.md`, `filename-template-string-may-have-a-second-live-copy.md`, `embedded-palette-not-the-installed-palette.md`, `negative-from-addressing-root-not-shapes.md`, `doc-blocker-cites-wrong-buffer.md`, `curated-site-page-drifts-from-corrected-raw-docs.md`
