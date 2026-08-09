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
