# ceres — Final Fantasy VI (SNES), FFIV (SNES), FFV (SNES)

**Project root:** `~/Development/ceres`

First-pass session, `data/ffvi/snes/Final Fantasy III (USA) (Rev 1).sfc`
(US retail title — Nintendo renumbered FFVI to "III" for the US SNES
release). Confirmed HiROM+FastROM, no copier header, 3,145,728 bytes,
checksum valid, CRC32 `0xc0fa0464`.

**The session's real find wasn't a format — it was the oracle.** That CRC32
is an exact match for the "Final Fantasy III 1.1 (U)" build target of
`github.com/everything8215/ff6`, a mature disassembly that **rebuilds this
exact ROM byte-for-byte** from source + a `make rip` step against a
user-supplied vanilla ROM. This is the strongest form of the "byte-identical
binary" case already documented in
`romhacking-community-tools-first.md` — not a hypothesis to re-check, a
guarantee: every offset, table, and algorithm the project's own build
process consumes is provably correct for this literal file, because building
it and diffing against the real ROM is exactly how that project stays
correct. Every claim taken from it was still independently re-verified
against this project's own ROM bytes before being marked confirmed (per the
mission's verification bar), but none of those re-checks ever failed except
one (see below) — this is about as good as an external oracle gets for a
commercial ROM with no ground-truth save states or screenshots needed.

Confirmed session 1: DTE (dual-tile/digraph) text compression for
dialogue (128-entry table read live from ROM at HiROM `C0/DFA0`, each entry
a pair of *codes into the dialogue alphabet table*, not raw ASCII — the
session's one wrong hypothesis, caught by a 128/128 byte-exact mismatch
against the reference table, fixed to 0/128); a separate non-DTE
fixed-length name-table text encoding (different code-range alphabet for
the same glyphs, used by monster/character/item/spell name tables); a
classic ring-buffer LZSS graphics decompressor (2-byte compressed-length
header, 8-bit-flag/8-token lines, 2KB circular window) verified via a
structural invariant — the stream's own embedded length reproduced an
externally-documented resource boundary exactly (1465 bytes, zero
deviation) — and by rendering a legible font from its output; 19 character
portraits (uncompressed 4bpp tiles + a tile-formation reorder table + BGR555
palette) rendered as unambiguous, recognisable FFVI character faces —
sourced `tile-formation-table-not-raster-order.md` (naive raster-order
render of the same confirmed-correct tiles produced scrambled,
unrecognisable output); the small dialogue/menu font (256 uncompressed 2bpp
tiles) and the LZSS-compressed ending/credits font. `tools/shared/
snes-ppu.ts` ported in verbatim from `sorcery`/`strike` (third project to
use it, still fully project-agnostic — no changes needed).

Confirmed session 2: **monster/Esper battle graphics** — corrected the
prior session's "LZSS-compressed" hypothesis (wrong: that guess came only
from a community bank-map prose label; the reference project's own
extractor script only LZSS-decodes `.lz`-suffixed rip targets, and the
monster-gfx target has no such suffix). The real format is raw uncompressed
4bpp/3bpp tiles, *stencil-trimmed*: a per-monster bitmask (8 bytes/64-tile
or 32 bytes/256-tile canvas) drops all-zero tiles before storage, resolved
via a packed gfx/palette/stencil pointer table (`MonsterGfxProp`, 384 x 5
bytes) plus a same-format sibling table for Espers (`EsperGfxProp`, 32 x 5
bytes) that a first pass over `MonsterGfxProp` alone missed — walking only
the monster table found 148/176 distinct graphics; the other 28 turned out
to be Esper-only entries in the adjacent table. Verified via a byte-exact
structural invariant (`trimmedLength == popcount(stencilBits) * tileSize`,
176/176 exact) and an unambiguous 176-sprite render (Guard/Soldier/Templar,
dragons, all named Espers, Kefka's final form, etc. — all correctly
coloured via the resolved palette pointer, zero garbled entries). Also
confirmed this session: `MonsterProp` (battle stats, 384 x 32 bytes — field
offsets/widths from the actual `LoadMonsterProp`/`LoadRageProp` 65816 code,
including two fields the source comments mislabel as single bytes that the
code actually reads as 16-bit word pairs); `MagicProp` (spell data, 256 x
14 bytes — offsets from the `mvn` block-move destination plus the
community's own bit-level RAM-map notes); the large/variable-width font
(232 glyphs, non-8x8-tile 1bpp, 22 bytes/glyph = 11 rows x 2 bytes, glyph
index = character multiplied by the SNES hardware multiplier's own `$16`
operand — a literal instruction operand, not a guess); and that world-map
graphics use the *exact same* LZSS codec as §4 (zero-deviation header-match
across 4 independent resources — no new codec needed, just confirmation).

Confirmed session 3: **field maps/tilesets and the world map** (new
territory, not previously started). Field maps (towns/dungeons/interiors)
use four resource families plus a per-map header (`MapProp`, 415 x 33
bytes) — a "tile formation" meta-tile table (`MapTileset`, 75 LZSS
resources, the *same* codec as §4, decompressing to a fixed 2048 bytes
each with a low-byte/high-byte-split-then-interleaved word layout
transcribed straight from the loader's WRAM-port copy loop), a per-layer
tilemap (`SubTilemap`, 350 LZSS resources, a flat `width*height` byte grid
with **no** stored dimensions — width/height come from the owning
`MapProp`'s class fields), raw uncompressed 4bpp tile graphics (`MapGfx`,
82 variable-size banks), and 48 x 256-byte (8x16-colour) palettes
(`MapPal`). `MapProp`'s two packed bitfields (naming which
graphics/tile-formation/tilemap resources a map uses) were independently
re-derived bit-by-bit from real 65816 code (`LoadMapGfx`/`LoadTileset`/
`TfrBG3Gfx`/`InitScrollClip`) rather than trusted from the community's own
RAM-map prose, which — read literally MSB-first per byte — would have
given the wrong field order; the real packing is LSB-first across the
whole multi-byte span, caught by checking 7 independent bit-extraction
instructions one field at a time. One mid-session correction: an initial
`SubTilemap` decoder asserted decompressed length exactly equalled the
referencing `MapProp` record's declared `width*height`, which failed for
24/350 resources — some tilemaps are shared by several rooms declaring
*different* (smaller) height classes for them, tolerated at runtime because
the game's row-copy loop simply never reads the extra rows into the visible
region; fixed by deriving height from the decompressed byte count instead
of trusting any one caller. **Verification**: byte-exact LZSS
declared-span structural invariants (zero deviation across the *entire*
75-resource tile-formation corpus and *entire* 350-resource tilemap
corpus — not samples), plus an unambiguous, screenshot-quality,
byte-exact-named render (`MapProp` record 20 decodes `nameIndex` ->
`"NARSHE"` independently of the graphics pipeline, and its BG1-over-BG2
composite render is an unmistakable view of Narshe — snowy mountain
cliffs, timbered building roofs, bridges, waterfalls). All 415 `MapProp`
records dedupe to 203 distinct visuals; every one decodes and renders
without throwing (full-corpus regression, not just the showcase map) —
spot-checked beyond Narshe: a large shared interior-room atlas, several
cave/dungeon layouts, and an airship exterior, all clearly identifiable.

The **world map** picks up where session 2 left off (that session only
confirmed the LZSS codec applied, not the content). Unlike field maps, the
world map's tile-formation table, raw pixel tiles, and a per-tile
palette-select nibble table are bundled into **one** LZSS resource per
world (`WorldGfx1`/`WorldGfx2`, always exactly 9344 decompressed bytes:
1024+8192+128), paired with a separate flat 256x256-byte tilemap
(`WorldTilemap1`/`WorldTilemap2`, always exactly 65536 bytes). The palette
is an 8-bit (256-colour) index — confirmed directly from
`TfrWorldMapGfx`'s own `(paletteNibble<<4)|pixelValue` arithmetic, a
classic SNES Mode 7 "EXTBG" trick — resolved by **concatenating** two
separate 128-colour tables (`World{1,2}BGPal` + `World{1,2}SpritePal`,
i.e. the *entire* CGRAM, not just one half like every other palette in
this project); this wasn't documented anywhere in the community's prose
and was inferred from the 8-bit index range, then confirmed by a correctly
(non-garbled) coloured render. **Verification**: LZSS declared-span
invariant against each resource's known next-address (community's own
`src/gfx/world_gfx.asm` label comments), zero deviation across all 4
resources checked; unambiguous full-resolution (4096x4096) renders of both
the World of Balance (three-continent coastline, the circular South
Figaro desert) and World of Ruin (the fragmented, shattered coastline, the
swirled crater near Thamasa/Kefka's Tower) — both instantly recognisable.

Open: field-map BG3 (overlay/parallax effects) graphics and its embedded
tile-formation table, per-tile priority-bit compositing (whole-layer
BG1-over-BG2 already renders every checked map correctly), `MapTileProp`
(collision data, not visual), and world-map secondary layers (minimap,
animated sprites, Mode 7 cloud backdrop) — plus the pre-existing opens:
bit-level semantics for several `MonsterProp`/`MagicProp` flag bytes
(offsets confirmed, individual bit meanings not fully mapped), and the
character-code mapping for large-font glyphs 96-231 (pixel format
confirmed; 0-95 confirmed to map to the `DIALOG_TABLE` alphabet). See
`docs/ffvi/snes/data-structure.md` and `docs/ffvi/TODO.md`.

Confirmed session 4: **Item Data** (`ItemProp`, 256 x 30 bytes, HiROM
`D85000`) and **field/overworld character sprites** (`MapSpriteGfx`, 165
objects, HiROM `D50000`-`D82FFF`) — both genuinely new territory, neither
previously scoped. Item Data's 30-byte stride was confirmed twice from real
code (two independent `#30`/`#$1e` multiply sites in two different program
banks), and its field offsets cross-checked against **three** independent
sources agreeing exactly: the actual `lda f:ItemProp+N,x` disassembly,
`everything8215/ff6tools`' self-describing `ff6/ff3u-sfc.json` rip
definition (its `begin`/`mask` packing convention independently re-derived
from `rom/romtools.js::ROMProperty.disassemble` rather than trusted as
prose), and the separate `ff6hacking.com` community wiki's byte-offset
table. Verified via ten independent, well-known real-FFVI-mechanic bit
checks, all exact (Genji Glove dual-wield, Economizer 1-MP spells, Gale
Hairpin preemptive strike, Excalibur's Holy element, and four field-effect
relics whose names literally predict which bit of a per-relic flag byte is
set) — a stronger oracle than hunting for a published GP-price list, whose
several fetchable sources gave inconsistent numbers for the exact same
items (see `published-walkthrough-numeric-oracle.md`'s caveat about
provenance; this session leaned on gameplay-mechanic bit facts instead,
which are much harder to misremember than an exact price). One field
(`fieldEffect`) was initially misread as a plain enum before the first
four-relic check failed 0/4 and a "value = `1 << tableIndex`" re-reading
passed 4/4.

Field sprites (`MapSpriteGfx`) are a **third, previously-undecoded tile
format family** distinct from portraits (§6, tile-formation-reordered) and
monster/Esper battle graphics (§8.1, stencil-trimmed): flat, uncompressed,
variable-length runs of raw 4bpp tiles, no header. Located via a from-
scratch byte-pattern search (not the reference project's rip list): the
game's own `TopSpriteHFlip` table (a distinctive 128-byte flip-flag
pattern) has exactly one match in the whole ROM, and that address plus
each subsequent table's own confirmed size chains byte-exactly through
`BtmSpriteHFlip` -> `MapSpriteTileOffsets` (the shared 57-entry animation-
frame table) -> the `MapSpriteGfxPtrsLo`/`Hi` object-pointer tables — every
step re-derived from this project's own ROM bytes and cross-checked
against the community disassembly's debug labels and declared bank-range
boundary (`C00000-C0CD39`, "field program" — this table starts the very
next byte). Frame composition (which 6 of an object's tiles form the
16x24px standing pose, and in what screen arrangement) was resolved
**empirically by render**, the same method that cracked the portrait
tile-formation table in session 1: a literal reading of the DMA
destination-address grouping in the loader code (`TfrObjGfxSub`) predicted
one tile arrangement, which rendered as visibly scrambled output (a torso
patch floating above disconnected legs); simple top-to-bottom raster order
of the object's first 6 tiles rendered an immediately recognisable Terra on
the first try, and generalized cleanly to Locke/Cyan/Edgar/Sabin/Mog/all 14
party members + Esper Terra with zero further correction — confirming a
render-based empirical check can out-perform a literal disassembly reading
when the exact hardware VRAM-addressing semantics aren't fully modeled.
Palette resolution was intentionally scoped down: there is no static table
pairing all 165 graphics objects to one of 32 shared palettes (that
assignment happens at the field-object-*instance* level, not the graphics-
bank level), so only the 15 objects whose palette-group *names*
unambiguously self-identify (`terra`, `locke`, `cyan_shadow_setzer`,
`edgar_sabin_celes`, `strago_relm_gau_gogo`, `mog_umaro`, `esper_terra`)
were rendered and confirmed, rather than guessing at the other 150.

Open (session 4): item-effect numeric-id-to-name value tables (`targeting`,
weapon/item special-effect ids); the other 150 `MapSpriteGfx` objects'
correct palettes; all field-sprite frames beyond frame 0 (walk cycles,
other facing directions, the located-but-unapplied h-flip tables); and
character *battle* sprites (the animated in-battle party graphics) were not
investigated this session — deliberately scoped in favour of field sprites,
which had a cleaner, more tractable, code-derivable format. See
`docs/ffvi/snes/data-structure.md` §12-14 and `docs/ffvi/TODO.md`.

Session 5: **Japanese-original-vs-US comparison**
(`data/ffvi/snes/Final Fantasy VI (J).smc`, CRC32 `0x45ef5ac8`, confirmed
match for `everything8215/ff6`'s "Final Fantasy VI 1.0 (J)" build target —
this session went past a CRC32 match and actually cloned the repo + ran its
own `tools/extract_assets.py` against this exact ROM as an independent
cross-check, the same technique already used for FFV). Every already-
confirmed US data table (`MonsterProp`, `MagicProp`, `ItemProp`, `MapProp`,
`MonsterGfxProp`/`EsperGfxProp`, palettes, stencil tables, portrait/field-
sprite graphics, world-map LZSS resources) lives at the *exact same* HiROM
address in both builds. A fixed-offset byte diff initially made
`MonsterGfxProp` and the field-sprite pointer-table family look 75-98%
different; resolving each record through its own pointer/offset field
(instead of the raw address) showed both were ~98-100% identical — the
apparent divergence was a cascading address-shift artifact from one
upstream size change each (a 2-tile stencil-bitmask difference; a 206-byte
shorter field-program code bank in the JP build) — see the new
`fixed-offset-diff-across-builds-hides-pointer-shift.md` pitfall this
session sourced. Genuine, small, deliberate content differences confirmed:
Raise/Arise's `Status 4` flag byte differs; Ultima Weapon's "Heavy Item"
flag is set in JP but not US; a shared monster stencil retains 2 extra
tiles in JP; and — the session's other new pitfall,
`localized-signage-baked-into-tile-graphics.md` — a handful of field-map
background-graphics resources differ only because they contain literal
painted-in town signage (Narshe/Zozo/Vector/etc.), independently confirmed
by the reference project's own `_en`/`_jp` file-naming convention isolating
exactly that same resource set. Also confirmed real Woolsey-era character
renames (Tina->Terra, Cayenne->Cyan, Mash->Sabin, all decoded directly from
ROM bytes, not looked up).

JP text itself is a genuinely different, more complex system than the US
DTE digraph scheme — no DTE at all (the US DTE table's address holds
stale/uninitialized filler in the JP ROM, not repurposed data) but a
word/phrase MTE dictionary *plus* a real 2-byte kanji table for dialogue.
This closes out a 3-data-point pattern across the whole `ceres` project:
FFIV-J uses no text compression at all (flat kana), FFV-J uses an MTE
dictionary (kana only, no kanji), and FFVI-J uses MTE *and* kanji — each
game's JP-original text system is strictly more complex than the last,
tracking each engine's later release date and heavier text/script load.
**Don't assume a JP-original's text-compression scheme transfers from the
previous game in the same series** — each was independently re-derived
from that game's own ROM bytes/rip output, not carried over. Session 5
decoded only FFVI-J's fixed-length name/label tables (character/monster/
item/spell/monster-special names, `tools/ffvi/jp-text.ts`); full dialogue
(needs the MTE dictionary + kanji table, both located but not wired into a
decoder at the time) was left open — closed out in session 9 below.

Session 6: **JP sprite extraction** (`tools/ffvi/build-assets-jp.ts`, a
standalone script deliberately *not* wired into `game-config.ts` — output at
`public/assets/ffvi/snes-jp/`, sibling to the US `.../snes/` output rather
than a new registered platform). Ran the confirmed monster/Esper-graphics,
portrait, and field-sprite decoders against the JP ROM per session 5's
"identical HiROM layout" finding — 2/3 needed no changes (portraits and
monster/Esper graphics decode and render correctly unmodified), but the
third (field sprites) had a **real bug**, not a hypothetical: its `C0`-bank
pointer/frame-table addresses are US-only constants, and the JP ROM's
206-byte-shorter bank-`C0` code (session 5's finding) means those addresses
resolve to the *wrong* graphics pointers if used unmodified — silent wrong
output, no thrown error. Caught only because this session diffed the
JP render byte-exact against the (confirmed-should-be-identical) US render
instead of trusting a plausible-looking thumbnail; fixed by parameterizing
`field-sprites.ts` with a `FieldSpriteAddrs` argument (`FIELD_SPRITE_ADDRS_US`
default / `FIELD_SPRITE_ADDRS_JP` = each US address minus the confirmed
`0xCE` shift). This sourced the new
`decoder-address-reuse-across-rom-release.md` pitfall: "same confirmed
decoder, same HiROM address, different ROM release" still needs its own
byte-exact verification, not just a rendered-thumbnail glance, when the
decoder's constants point into game *code* rather than a fixed data table.

Also ran an **exhaustive** (not sampled) pixel diff of all 176 unique
monster/Esper graphics between releases (each independently decoded through
its own per-ROM pointer record) and found 4 previously-undocumented content
edits beyond session 5's 2 known stencil-count differences — all 4 have
byte-identical stencil bit-sets (ruling out a tile-count explanation) and
are tightly localized to the chest or groin region of a humanoid figure;
two are named `Chadarnook` and `Goddess`, both independently well-known in
FFVI's real-world release history as Nintendo-of-America-era content edits.
Sourced the new `known-differences-list-not-exhaustive-without-full-diff.md`
pitfall. Separately investigated the Narshe field-map signage difference
flagged in session 5 (§15.6) and found the two `NARSHE`-named `MapProp`
records render **pixel-identical** between releases despite real underlying
raw-byte/meta-tile-id differences — traced to a single-tile insertion in a
shared tile bank whose effect exactly cancels against a corresponding `+1`
shift in every tile-formation reference into that bank, the same "additive
index shift, not real content" mechanism session 5 found for pointer
resolution, now confirmed one level deeper (within one resource family's
own internal numbering) — folded into
`fixed-offset-diff-across-builds-hides-pointer-shift.md` as a second
example. See `docs/ffvi/snes/data-structure.md` §15.8 for full details.

Session 7: **field-sprite walk-cycle frames, facing directions, and
h-flip mirroring** (`tools/ffvi/field-sprites.ts` §13.2) — the two
located-but-previously-unapplied session-4 tables (`TopSpriteHFlip`/
`BtmSpriteHFlip`) finally traced and wired in, plus the frame-selection
logic (`src/field/player.asm`'s facing-direction button handlers,
`src/field/obj.asm`'s `ObjStopTileTbl`/`ObjMoveTileTbl`) for the 14 party
members + Esper Terra. Confirmed Right-facing frames are never separately
stored — Left's own raw selector values plus `0x40` (the h-flip bit),
byte-exact-verified against a naive whole-image mirror (0/1536 RGBA
mismatches, 15/15 objects; see `verification-techniques.md`'s new
whole-image-mirror-invariant entry). The h-flip tables' top/bottom
tile-group split was resolved by a **geometric** argument (a real SNES
16x16 OAM sprite is always two spatially-adjacent tile rows) rather than
by literally reading `TfrObjGfxSub`'s own DMA-destination tile grouping
— the *same* routine session 4 already found misleading for frame
*composition* (`tile-formation-table-not-raster-order.md`), now confirmed
misleading a second time for a different purpose (h-flip grouping), which
that lesson file's third addendum generalizes into "once a routine's
grouping is shown to be a VRAM-addressing artifact, distrust it for every
downstream question, not just the one that first caught it." Also
corrected a session-4 documentation error: frame 0 (still used unchanged
by `renderFieldSprite`/`decodeAllPartyFieldSprites`) was mischaracterized
as "standing/facing-down" — tracing the real selection code showed it's
actually Down-facing walk-cycle step 3, which only *looks* like standing
because that step happens to be visually near-neutral. Sourced the new
`plausible-render-not-semantic-label.md` pitfall (a render can confirm a
pixel decode without confirming the semantic label attached to it, unless
the actual selection logic was traced). New animated-sprite-sheet asset:
`public/assets/ffvi/snes/field-sprites-anim.png` (300 frames: 15 objects
x 4 directions x [standing + 4-step walk]).

Session 8: **battle-engine Mode 7 verification** (a pure investigation
task, no new asset pipeline) — confirmed "does the battle engine use Mode
7" (community knowledge, previously unverified). Real usage exists, but
narrower than the claim: not a rotating battle-arena background (no
evidence found), but a per-attack scripted Mode-7 zoom/rotate BG1 overlay,
gated by live jump-table entries (`$80/$40`-`$80/$42`) in the attack-
animation-script bytecode, pushed to the real PPU registers every frame by
the battle engine's own NMI handler. Exactly 6 named attack animations
trigger it (found via an address-agnostic byte-pattern scan, not hand-
parsed disassembly addresses — see the new
`ca65-label-suffix-address-arithmetic-mx-flag-blind.md` pitfall this
session sourced, after hand-deriving instruction addresses from the
disassembly's local-label suffixes silently broke on three M/X-flag-
sensitive opcode handlers): Odin's Atom Edge and Raiden's True Edge
(render the summoned Esper's *own* sprite as the Mode-7 layer), plus
Strago's S.Cross/Overcast Lores, H-Bomb, and Purifier/Crusader (a shared
abstract effect texture instead). Located the battle-*graphics* program
(`src/btlgfx/`, HiROM banks `$C1`/`$C2`) as the real home of this code —
the battle-*logic* program (`src/battle/`) that the task brief suggested
starting from doesn't touch any PPU register at all, a useful reminder
that a same-genre "battle" directory name doesn't guarantee it owns
rendering. See `docs/ffvi/snes/data-structure.md` §17.

Session 9: **FFVI-J full dialogue text** (kana + genuine 2-byte kanji +
the word/phrase MTE dictionary), `tools/ffvi/jp-dialogue.ts` — closes out
session 5's `ffvi-jp-dialogue-text` open item. The rip-list JSON gave
locations/alphabets but not the actual byte-stream grammar; the missing
piece was the community `everything8215/ff6` project's own reference
*codec* source (`tools/romtools/text_codec.py::TextCodec`, not just its
rip-list) — see `romhacking-community-tools-first.md`'s new section on
finding a reference project's codec/algorithm module when locations are
confirmed but the decode still won't crack. That source revealed a clean
two-byte-lookup-tried-first-then-one-byte-fallback discriminator (kanji
lead byte `0x1C`-`0x1F` is the only 2-byte-coded range) and that control
codes with a `:b`/`:w`-suffixed name (`{wait:b}`, `{key:b}`) consume 1/2
trailing raw bytes as a parameter — a rule this project's own existing,
previously-"confirmed" **US** dialogue decoder (`text.ts`) turned out to
be missing too, undetected until the JP work's stricter zero-escape-rate
check surfaced it by contrast (see the new
`escape-code-parameter-bytes-silently-misdecoded.md` pitfall). Verified:
the MTE dictionary decoded live from this project's own JP ROM bytes
matches the community's own hand-curated table 24/24 entries byte-exact;
the full dlg1/dlg2/monster-dialogue/battle-dialogue corpus (3,596 lines,
~147,600 characters) decodes with zero unmapped-byte escapes; and the
opening Narshe/Magitek-Armor scene lines up beat-for-beat with the
already-confirmed US `dialog.json` at matching line indices. Item/spell/
lore-description-style JP text pools (no MTE, same base kana+kanji system)
remain undecoded — see `docs/ffvi/snes/data-structure.md` §15.10 and
`docs/ffvi/TODO.md`'s `ffvi-jp-desc-text` entry.

Session 10: **world-map secondary layers** — minimap, animated overlay
sprites (airship/chocobo/ship/Esper Terra/birds), and the Mode 7 cloud/sky
backdrop, closing out most of `ffvi-world-map-secondary-layers`
(`tools/ffvi/world-map.ts` §10.4-10.6). The animated sprites turned out to
share **one 512-tile OBJ sprite VRAM bank** built from 4 separate LZSS
resources concatenated in loader order (two variants — `'default'` for
foot travel/flying, `'chocobo'` for riding — matching two different
decompression sequences in `InitWorld`/`InitAirship` vs `InitChoco`), plus
a 108-entry frame table of OAM-style sprite descriptors. The frame table's
program-bank base address (bank `$EE`, no explicit linker-config offset)
was derived indirectly — by finding the *next* segment in the same bank
pinned at a known offset and confirming zero gap — then confirmed
byte-exact 106/106 against the disassembly's own per-frame address labels,
a strong independent cross-check for an address that was never directly
stated in any HiROM-address comment. Verified via unmistakable airship/
chocobo/ship/Blackjack renders. The minimap (OBJ sprite tiles, palette row
read off a `ShowMinimap` OAM-attribute constant) was verified by a
structural land/ocean silhouette match (81.7%/82.6%) against the already-
confirmed full terrain render, rather than by eye alone. The backdrop's
ambiguous two-orientation tilemap (64x32 vs 32x64 — both rendered
plausibly, since the source data is naturally periodic in both directions)
was settled by finding the authoritative `BG2SC` PPU register value
instead of trusting either render. Sourced a reusable disambiguation
technique for "which of several candidate resource-bank variants pairs
with this record, with no direct code trace of the runtime binding":
render against every candidate, score by opaque/non-default-pixel
fraction, keep the max — reproduced the disassembly's own comment-named
pairings on every case checked (`chooseWorldAnimVehicle` in
`world-map.ts`). One item still open: the `$26-$2d` "character" animation-
frame group (on-foot walking-party icon) renders blank under both known
vehicle-bank variants — a third, unidentified VRAM/decompression context,
tracked as `ffvi-world-anim-character-frames`. See
`docs/ffvi/snes/data-structure.md` §10.4-10.6 and `docs/ffvi/TODO.md`.

Session 11: **music/sound driver identification** (`ffvi-music-sound`,
investigation only — no player built). Confirmed FFVI's SPC700 sound
driver is **not** Nintendo's `N-SPC`/"Kankichi-kun" engine despite loose
community terminology calling the whole family "N-SPC-family" — it's
Square's own in-house driver authored by Minoru Akao (his 4th of 4 SPC700
drivers), classified by the `vgmtrans/vgmtrans` open-source SPC-to-MIDI
converter as `AKAOSNES_V4`, minor version `AKAOSNES_V4_FF6`. Identified
via a genuinely new oracle technique for this project (see
`romhacking-community-tools-first.md`'s new "signature/version-
classification database" section): cloned `vgmtrans`, pulled its
`AkaoSnes` format module's own literal byte-signature constants (a
60-byte per-opcode argument-length table specific to the FF6 build, plus
5 SPC700-instruction byte-patterns), and found each with a single,
unambiguous whole-ROM byte-exact search hit — no disassembly needed,
and every hit landed inside the community bank-map's already-hypothesized
`C50000`-`C5FFFF` sound bank, upgrading that hypothesis to confirmed for
several sub-addresses. Cross-checked the same way against FFIV (`AKAOSNES
V1`) and FFV (`AKAOSNES V3`) — a clean one-driver-family-per-release
progression across the trilogy. Resolved the sequence-format question
(free-running per-track event stream, confirmed both from
`ff6hacking.com`'s MML-tooling wiki prose and from `vgmtrans`'s own parser
source having no pattern/phrase indirection layer) — matches
`@seer-project/smus`'s shape, not `@seer-project/tracker`'s, settling this
project's `seer/docs/common-tooling-candidates.md` §19 open question.
Also confirmed the 85-song `SongScriptPtrs` table (HiROM `C53E96`) and
walked all 85 headers/581 real track pointers with zero out-of-bounds
addresses. Hit one tooling dead end worth noting: radare2's native SNES
plugin silently returned unmapped (`0xFF`) memory for HiROM bank
addresses outside the header window — see `game-re-tooling/snes.md`.
See `docs/ffvi/snes/data-structure.md` §18 and `docs/ffvi/TODO.md`.

## FFIV (SNES)

First-pass session, `data/ffiv/snes/Final Fantasy II (USA) (Rev 1).sfc` (US
retail title — same Nintendo-of-America renumbering pattern as FFVI/"Final
Fantasy III": Japan's FFIV shipped in the US as "Final Fantasy II").
Confirmed **LoROM** (unlike FFVI/FFV, both HiROM) — standard-conforming
header, no copier header, 1,048,576 bytes, checksum valid, CRC32
`0x23084fcd`.

**Same oracle pattern as FFVI, one level stronger.** `0x23084fcd` is an
exact match for "Final Fantasy II 1.1 (U)" in `github.com/everything8215/ff4`
— same author as the FFVI corpus's `ff6` oracle, same rebuild-from-source
guarantee. The FFIV project goes further than FFVI's: instead of requiring
disassembly reading to find offsets, it ships `vanilla/ff4-en-rip.json`
(~9800 lines), a **fully self-describing JSON data-rip definition** —
every table's CPU address, record stride, pointer-table shape, and text
encoding rule is declared data, consumed by the project's own generic
`tools/romtools/rom-decoder.js`. This made the whole session dramatically
faster than a disassembly-reading pass: read the JSON, compute the
predicted file offset, decode with a from-scratch TS port, cross-check
against the JSON's own decoded reference strings (or just check for
legible output), done — no 65816 tracing needed anywhere this session.
**When a target's reference project ships this shape of asset, prefer it
over disassembly reading — it's strictly cheaper and just as strong an
oracle**, per the general `romhacking-community-tools-first.md` lesson but
worth calling out as its own case: a self-describing rip *definition* file
(not just a rip *script*) turns "read disassembly to find offsets" into
"read structured data" entirely.

**One real trap, caught and fixed in-session**: the rip definition's array
`range` fields are LoROM **CPU addresses that still need mapping**, not
pre-resolved file offsets, even though small ones (e.g. `0x0FA710`) look
enough like a plausible in-file offset to be mistaken for one at a glance —
a naive read against raw file offset 0x0FA710 produced 100% garbage for
every table tried, while the same address run through the LoROM formula
(`((addr&0xFF0000)>>1)+(addr&0x7FFF)`) decoded 14/14 character names
byte-exact (`Cecil, Kain, Rydia, Tellah, Edward, Rosa, Yang, Palom, Porom,
Cid, Edge, FuSoYa, Golbez, Anna`) on the first retry. Two other pointer-table
resolution shapes were reverse-engineered directly from the reference
project's own `rom-decoder.js::decodeParentObject` (not guessed): a `flat`
form (pointer offset pre-mapped, raw pointers added directly — event/map
dialogue) and a `banked` form (`pointerTable.isMapped: true` — raw pointer
added to a CPU bank base *before* mapping, sum mapped afterward — battle
dialogue/messages, status names).

Confirmed this session: one shared base text alphabet (`TEXT_TABLE`,
0x01-0xC9) used by *every* text pool — a structural difference from FFVI's
two-disjoint-alphabet scheme — with per-resource variation limited to
whether a ROM-resident DTE digraph table applies (only the `dialog`
encoding covering event/map dialogue; battle dialogue/messages/item
descriptions/status names decode DTE-free, confirmed by zero unmapped
bytes across every one of those pools without it) and which small
padding/terminator/space extra-codes get merged in. The DTE table (CPU
`$13:9700`, 128 slots, code = `0x80+index`) byte-exact matched the
reference project's own 107 populated digraph strings 0/107 mismatches —
the other 21 slots in that 128-slot storage region are inert filler
(overlap TEXT_TABLE's own digit/punctuation codes, never dispatched to DTE
by the game; the fix was checking TEXT_TABLE before DTE at every code, not
just building the map from all 128 raw ROM slots unconditionally). Also
confirmed: a 2-byte speaker-name insertion code (lead byte `0x04`, second
byte 0x00-0x0D indexing the 14-entry character-name table) resolved by
decoding real event dialogue to grammatically-correct named lines
(`"{Golbez}:We defeated him."`); 14/17 character portraits (uncompressed
3bpp tiles, already in raster order — no FFVI-style tile-formation reorder
table needed — plus an 8-colour-per-portrait BGR555 palette) rendered as
unambiguous, individually recognisable named FFIV characters; the full
256-tile menu-window graphics bank (uncompressed 2bpp) rendered as a
complete, legible font (A-Z/a-z/0-9 + exact punctuation set) plus
window-frame and item/weapon icon tiles, self-confirming both the tile
format and the TEXT_TABLE glyph-order hypothesis simultaneously. ~72,000
characters of decoded dialogue/name text across 12 resource pools came back
with a combined 5 unmapped-byte escapes total (0.007%) — 4 are one genuinely
undefined control code (`0x02`, undefined even in the reference project's
own char table) and 1 is a single stray byte in one fixed-length record's
padding run.

One portrait-palette wrinkle, left open rather than force-resolved: the 3
transformation-status portrait frames (Pig/Small/Toad) don't decode cleanly
against their own-index palette slot (near-solid-black render); trying
another character's palette against the same graphics produces an
unambiguous grey pig/toad, strongly suggesting a runtime recolour effect
(the frame is tinted with whichever character's palette is active) rather
than a wrong offset — flagged as open rather than guessed at.

`tools/shared/snes-ppu.ts` reused verbatim again (4th project) — no changes
needed; FFIV portraits/font only needed its existing `decodeTile3bpp`/
`decodeTile2bpp`/`decodeCgramPalette` primitives.

Open: monster graphics (needs more involved per-resource stencil logic than
time allowed this pass), world-map tile graphics (declared `linear4bpp` — a
bitplane layout `snes-ppu.ts` doesn't implement yet, unlike the
row-interleaved `snes4bpp`/`snes3bpp`/`snes2bpp` already covered), and
every numeric stat table (offsets known from the rip definition, field
layout not transcribed). See `docs/ffiv/snes/data-structure.md` and
`docs/ffiv/TODO.md`.

**Follow-up session: battle/field playable-character graphics**
(`characterGraphics`, LoROM `1A8000-1AFC3F`, 31,808 bytes 4bpp + a 512-byte
`characterPalette`) — resolves the item left open above. The rip JSON gave
the *shape* (17 variable-size blobs, two named tile-formation reorder
templates, `"Default"`/`"Golbez/Anna"`) but not the *selection logic*
between the two templates or the exact byte offsets for the two characters
(Golbez, Anna) whose data doesn't fit the array's own uniform per-record
stride — both resolved by cloning `everything8215/ff4` and reading its
actual disassembly (`ReloadCharGfx`/`GetExtraCharGfxPtr`/
`UpdateCharSpritesheet` in `btlgfx/*.asm`, plus `UpdateCharPalID` for the
palette-group remap rule), not just its declarative rip JSON — see
`romhacking-community-tools-first.md`'s sharpened caveat on this exact
case. Verified by render: all 17 characters (Cecil DK/Paladin, Kain, Rydia
child/adult, Tellah, Edward, Rosa, Yang, Palom, Porom, Cid, Edge, FuSoYa,
Pig, Golbez, Anna) unambiguous and correctly coloured, including two
predicted-then-confirmed out-of-declared-range spillovers — Pig's higher
tile indices bleed into Golbez's real graphic bytes (visible blue/gold
armour fragments in the piglet render), and Anna's highest indices read
past the entire resource's own end — both predicted from byte arithmetic
*before* rendering, the same technique already used for FFVI's Gestahl
battle sprite; see `game-re-method/verification-techniques.md`'s new entry
for the general form. See `docs/ffiv/snes/data-structure.md` §9 and
`docs/ffiv/TODO.md` (closed `ffiv-battle-char-gfx`, opened three narrower
items: per-pose/action semantics not subdivided, Anna's palette-group
confidence weaker than Golbez's, and battle-status "mini"/"toad" spritesheet
variants not located).

**Follow-up session: Japanese-original-vs-US comparison.** A dump of the
original `data/ffiv/snes/Final Fantasy IV (J).smc` (CRC32 `0xCAA15E97`) was
added alongside the already-confirmed US ROM for a comparative-RE task
("how similar is the JP original"), not a fresh decode. `everything8215/ff4`
turned out to ship self-describing rip definitions for **both** releases
(`ff4-jp-rip.json` alongside the already-used `ff4-en-rip.json`), keyed by
CRC32 in the same `romInfoListFF4` table as the US oracle — `0xCAA15E97`
matches its declared `"Final Fantasy IV 1.1 (J)"` build target exactly.
Cloned the repo, dropped this ROM into its `vanilla/`, and ran its own
`node tools/decode-ff4.js` directly (same "clone + run the reference
project's own rip, not just read its source" discipline as the FFV
corpus's `everything8215/ff5` session below) — matched CRC32, produced a
full JSON decode used as a byte-exact comparison oracle.

Confirmed by direct byte-diff at the reference-confirmed CPU addresses
(not just "same declared range" — every byte compared): graphics/palettes
(portraits, battle sprites, all 5 monster-graphics banks) and most numeric
stat tables (`CharProp`, `LevelUpProp`, `itemEquipability`) are **byte-
identical** between the two releases; the only graphics difference is the
font-glyph portion of the window/text tile bank (expected — different
alphabet). Text-pool **pointer tables shift as a side effect of packing**,
not a restructure: fixed-length name tables keep the same start offset but
a narrower field width (JP kana names are shorter), and any pointer table
packed *after* one of those tables in the same bank shifts down by however
many bytes were saved — one table's pointer sub-table even ended up
immediately after a *different* neighboring table than in the US ROM,
because the localizers used the space the newly-added DTE table needed to
shift the surrounding layout, not just append it. FFIV-J's text system
itself is a flat, uncompressed single-byte kana alphabet occupying the
exact same code positions as the US `TEXT_TABLE` for every structural code
(control/name-insert/punctuation) — genuinely simpler than both the US
ROM's own DTE addition *and* FFV-J's kana+72-entry-MTE-dictionary scheme;
confirmed no `dte`/`mte` char table exists in the JP rip definition at all,
and the CPU range the US DTE table occupies decodes to real, structurally
sane `npcProperties` records in the JP ROM — decisive evidence DTE was
added for the English text specifically, not present in inert form
originally. Verified two ways per resource: recognisable real content
(character names, a correctly-worded opening-crawl paragraph) and a
byte-for-byte content cross-check against the reference project's own JP
rip output, matching exactly (186/186 exact on `battleDialog`, similar
on every other pool once cosmetic escape-rendering conventions are
normalised). Also confirmed a genuine, non-textual **difficulty rebalance**
between releases (161/224 monster stat records differ, overwhelmingly
JP-higher HP averaging ~1.44x where they differ; US consumable-item prices
raised; a real character rename, JP `ギルバート`/Gilbert -> US Edward, not a
transliteration artifact) — the commonly-cited "Woolsey-era US SNES version
was easier" claim confirmed at the byte level rather than assumed, with the
doc explicitly declining to claim whether the changes trace to the US
localization team directly or an intermediate JP revision (no JP "Easy
Type" dump was obtained to check). See `docs/ffiv/snes/data-structure.md`
§8 and `docs/ffiv/TODO.md` for the full comparison and the two items left
open (an Easy Type source ROM, and whether FFIV-J becomes its own
pipeline target).

A real landmine surfaced by simply having two same-extension ROM files in
one `data/` directory: the existing `loadRom()` helper (any single
`*.sfc`/`*.smc` file, no further check) would have silently picked whichever
file `readdirSync` listed first — fixed by making ROM selection CRC32-based
instead (`loadRomByCrc`, an explicit expected-CRC32 allowlist, exactly one
match required) — see `multi-region-dir-ambiguous-rom-pick.md`.

**Follow-up session: numeric stat tables** (`tools/ffiv/char-data.ts`,
`monster-data.ts`, `attack-data.ts`) — `CharProp` (14 x 32 bytes) and
`AttackProp` (256 x 6 bytes) confirmed as genuinely flat/fixed-stride
exactly as `everything8215/ff4`'s rip JSON declares, with field widths
independently re-derived from real `longa`/multi-byte-arithmetic code
(`LoadCharProp`, `LevelUp`/`LevelUpHPMP`, `LoadArrayItem`). `MonsterProp`
(224 records) is where the rip JSON turned out to describe the wrong record
shape entirely — pointer-indexed (via a separate `MonsterPropPtrs` table)
with deliberately overlapping, variable-length records (10-19 bytes of real
content in a fixed 20-byte read window), gated by a real bitmask byte the
JSON mislabels as a fixed `attackElements` field — see the new
`romhacking-community-tools-first.md` addendum this session sourced (a
correct table address doesn't guarantee a correct record shape, even from
an otherwise-reliable rip definition; two sibling tables in the same
session, same JSON, were correctly flat). Verified via values an earlier,
unrelated session had already independently established by JP-vs-US byte
diffing (Cave Bat/Treant/RocLarva HP, exact match via a completely
different decode technique), an iconic well-known value (Zeromus, FFIV's
final boss, HP 60000-65000 across its 3 battle forms), and — for `CharProp`
— every character's decoded `class` byte resolving to their real,
already-known FFIV class via the game's own already-confirmed `className`
text table (13/13 exact). `itemProperties` turned out not to be one table
at all (`ItemPrice` + `weaponArmorProperties` + a third code-confirmed
`ItemProp` battle-item-effects table) — left open rather than folded into
a rushed guess. See `docs/ffiv/snes/data-structure.md` §10-§12 and
`docs/ffiv/TODO.md`.

## FFV (SNES)

First-pass session, `data/ffv/snes/Final Fantasy V (Japan).sfc` (Japan-only
— FFV never got an official US SNES release). Confirmed HiROM, no copier
header, 2,097,152 bytes (16 Mbit), checksum valid, CRC32 `0xc1bc267d`.

**Same oracle strength as FFVI, one step further.** CRC32 exactly matches
the "Final Fantasy V 1.0 (J)" build target of `github.com/everything8215/ff5`
(same author as the FFVI/FFIV disassemblies — a third title from this
author, same "rebuilds the exact ROM byte-for-byte" guarantee). This
session went past reading the source: cloned the repo, initialized its
`tools/romtools` submodule, dropped this exact ROM into `vanilla/`, and ran
the project's own `make rip` (`tools/extract_assets.py`) against it —
matched CRC32, ran to completion with zero errors, and produced full JSON
text decodes plus every raw/LZSS/RLE resource the project catalogs. That
extraction output (not just the source) was then used as a byte-exact
diffing oracle for this project's own from-scratch TypeScript decoders,
independent of the reference project's own decode *code* — e.g. the
dialogue decoder was diffed against `dlg_jp.json`'s 2160 lines, not
re-derived from `romtools.TextCodec` by inspection alone.

Confirmed this session: an LZSS decompressor structurally similar to
FFVI's (same 2KB ring-buffer / 8-token-line shape) but **not
byte-compatible** — the length header is the *decompressed* size (FFVI's is
the compressed size including itself), and the back-reference token's
offset/length bit-packing is byte-order-reversed relative to FFVI's
little-endian packing (verified SHA256-byte-exact against the reference
project's own `ff5_compress.py` on 5 sampled ROM resources, run on this
project's ROM bytes); a from-scratch text codec covering FFV's genuinely
different text-compression scheme — not FFVI's DTE (2-character digraphs)
but a 72-entry MTE **word/phrase** dictionary (place names, particles,
character-name-plus-quote-mark idioms), independently re-derived by
locating and reading three parallel ROM tables live (length/low-byte/
kanji-bank-flag, HiROM `C0/8541`/`C0/858F`/`C0/87F7`) rather than hardcoding
the reference project's pre-resolved `mte.json` — 69/72 entries derive
purely from raw bytes (0 mismatches against the reference's independently-
built table), 3 residual codes have an unresolved second-kanji-bank
high-byte value (`2`, not just 0/1) left as an open TODO rather than
guessed at; the MTE re-derivation cross-validated `KANJI_TABLE` codes
independent of trusting the table's own provenance (codes for 風/神/殿
resolved via the raw-byte path to spell "Wind Shrine", a real FFV
location); dialogue decoding verified 2150/2160 lines (99.5%) byte-exact
against the reference tool's own extraction of this ROM, with the 10
divergences traced to a reference-tool pointer-boundary heuristic
truncating a minority of messages early (this project's terminator-based
decode is a strict superset, not a bug); and monster battle graphics —
same conceptual stencil-trimmed-tile-canvas scheme as FFVI's (packed
gfx/palette/stencil pointer record, 384 entries) but a **big-endian**
15-bit graphics-pointer packing (opposite of FFVI's little-endian one) and
different bit positions for the 3bpp/large-stencil flags, re-derived from
this game's own `btlgfx-main.asm` disassembly rather than reused from
FFVI's field layout — verified via a zero-out-of-range structural
invariant across all 384 records and an unambiguous 48-sprite render
(lion, elephant, dragons, an armoured knight, a robed mage, all correctly
coloured via the resolved palette).

`tools/shared/snes-ppu.ts` reused verbatim again (5th project) — no
changes needed.

Open: 3 MTE dictionary codes' exact high-byte-flag semantics (probable
second kanji bank, `0x1F00`-range, no character table mapped); the small
kana font's (`D1F000`, 2bpp, pixel format confirmed) text-code-to-tile-
index formula (naive code-minus-0x20 hypothesis contradicted by the
rendered tile order); overworld/vehicle sprites, kanji font graphics
(1bpp, likely non-tile-aligned), and world-map graphics (not independently
confirmed as the same LZSS codec, only inferred from the reference
project's rom map). See `docs/ffv/snes/data-structure.md` and
`docs/ffv/TODO.md`.

**Second session: playable-character battle sprites (`BattleCharGfx`,
confirmed).** 110 contiguous 1536-byte blocks (5 characters x 22 jobs,
HiROM `D20000`-`D49400`) — the loading routine itself (`_c124e2` in
`btlgfx-main.asm`, `ldx #$0600 ; graphics for each job are $0600 bytes`)
gave both the block stride and the per-character/per-job indexing
directly, no guessing needed. Each 1536-byte block is 48 raw 4bpp tiles
with **no stencil/formation table** — resolved to 3 frames of 4x4 tiles
(32x32px) purely by rendering candidate grid widths {2,3,4,6,8} and
picking the one producing clean, non-scrambled poses (same empirical
method as FFVI's field-sprite tile-formation crack). The job-index-to-
`JobName`-table-index correspondence (direct, unshifted) was resolved two
independent ways: a **comment on an unrelated pointer** (`_c12607`'s
dead-sprite palette pointer computes `CharPalBase + 0x2A0` with the
disassembly's own comment "pointer for freelancer (for dead sprite)" —
`0x2A0 = 21*32`, and `JobName[21]` independently decodes to `すっぴん`/
Freelancer, confirming job-slot 21 = Freelancer without tracing the
graphics-loading code's own job-index semantics at all); and unmistakable
renders (job 9 = White Mage, job 10 = Black Mage, both iconic enough to
identify by colour scheme alone). A genuinely useful corroborating
signal turned up for free: exactly 1 of the 110 (character,job) slots
(Galuf's Mimic sprite) renders fully blank, and that's narratively
correct — Galuf leaves the playable party before Mimic unlocks in FFV's
story, so the game never needed art for it. Overworld/vehicle sprites
(`MapSpriteGfx`/`VehicleGfx`) got recon only: the community disassembly
has zero xrefs to these tables anywhere outside their own declarations
(nobody traced their consumer either), but searching `field-main.asm` for
loader-name patterns (`Tfr*Gfx`) instead of the resource's own symbol
name found `TfrPartyGfx` and two real pointer tables (`_c01e02`,
`VehicleGfxPtrs`) — addresses are solid, tile-arrangement/frame-width
still open. See `docs/ffv/snes/data-structure.md` §9, §11.1 and
`docs/ffv/TODO.md` (`ffv-overworld-sprites`, `ffv-job-sprite-oam-frames`).

**Third session: battle-stat tables (`MonsterProp`/`WeaponProp`/
`ArmorProp`/`AttackProp`/`ConsumableItemProp`, confirmed).** Byte ranges
were already known from the reference project's `rip_list_jp.json`; this
session traced each table's real per-field layout from
`everything8215/ff5`'s own load-routine disassembly rather than any prose
byte-offset table. The key technique, reusable on any FF-family (or
similarly-shaped) disassembly: several of these tables are read into WRAM
via a **flat, byte-for-byte copy loop with no per-field branching**
(`MonsterProp`'s `CopyMonsterStats`, `WeaponProp`/`ArmorProp`'s
`ApplyGear`/`CopyOneItemData`) — this proves the destination WRAM struct's
field offsets are *identical* to the source ROM record's own byte offsets
by construction, so the struct's real field-named consumers elsewhere in
the code (`lda MonsterStats::HP,X`, `lda RHWeapon::Properties,X`) become
valid offset citations for the ROM layout even though no code ever
directly indexes `MonsterProp+N,x` by name. 8-bit vs. 16-bit field width
was independently re-derived from `longa`/`shorta0` directives around
those same reads, not from the struct's own `.res 1`/`.res 2`
declarations. `AttackProp` (256 x 8 bytes) turned out to back **both** the
87-entry spell-name table and the 169-entry attack/ability-name table
(`87 + 169 == 256` exactly, confirmed at the exact boundary record); this
elegant unified-array design is worth checking for on any two same-shaped
"count A + count B == round total" table pair — a byte-exact boundary
record decode is a strong, non-overlappable confirmation.

Verification leaned entirely on well-known, memorable real-game facts
spanning independent stat categories rather than one favourite value:
Goblin's HP/Level, Magic Pot's famously absurd HP/Level (the single
strongest check — a joke stat every FFV player remembers), two summon-boss
HP values, Excalibur's attack power, and black-magic MP-cost tiers (2/5)
all matched exactly on the first correct field-offset attempt. See
`docs/ffv/snes/data-structure.md` §10 and `docs/ffv/TODO.md`
(`ffv-battle-stat-bitfields` for the still-open per-bit flag semantics).

**FFV's AKAOSNES V3 sound driver** (a later session, building on FFVI's own
V4 sound-driver work in this same corpus, §18 above) is now decoded to a
working sequence decoder + offline WebAudio-style renderer — genuinely new
work, not a copy of FFVI's V4 findings, since V3's header field *order*,
opcode set, note/duration table size, and instrument-table shape all differ
from V4 in real, confirmed ways. Method: `vgmtrans/vgmtrans`'s
`AkaoSnesScanner.cpp`/`AkaoSnesSeq.cpp` source (cloned fresh, not trusted
from memory of the earlier FFVI pass) supplied V3-specific SPC700
byte-pattern signatures, each searched whole-ROM with wildcards for
game-specific operands (every pattern: exactly one hit); a real 65816
disassembly trace (`r2 -a snes -n`, raw file-offset reads) directly located
`SongScriptPtrs` (`LDA $C43B97,X` in the "play song" dispatch path, X =
songId*3); `NumSongs=72` and the sample-table boundary were derived by
"packed tightly with zero address slack" arithmetic closure, the same
technique FFVI's own session used. Two genuinely new findings worth
carrying to any future AKAOSNES-family game: (1) the confirmed 6-entry
`InitTfrSrcTbl`/`InitTfrDestTbl` boot-upload-table *shape* (byte-identical
order: driver code/SFX-ptrs/SFX-BRR/SFX-loop-DIR/SFX-ADSR/SFX-tuning, each
2-byte-length-prefixed) carried over completely unchanged from V4 to V3,
letting a blind byte-pattern search for the literal destination-address
sequence (`0x0200,0x2c00,0x4800,0x1b00,0x1a80,0x1a00`) locate the whole
table before any disassembly — likely shared driver-family convention, not
FF6-specific; (2) a corpus-wide census of every real `PROGCHANGE` event
across all 72 songs revealed a two-bank instrument-numbering
split (`srcn` 0-7 = boot-resident SFX table, `srcn` 32-65 = a separate
34-entry music-instrument table via `srcn-32`) that no source or doc
stated (the split conclusion survived a later header-model correction —
see below — though the census count itself shrank from 4,384 to 1,438
real events once track pointers resolved to the right data) — the real usage data was the only oracle for this indexing
convention, found only by walking the whole corpus rather than trusting the
scanner's own "srcn 0-63 direct" description literally. Also: `vgmtrans`'s
source has real, per-driver-version behavioral differences beyond the
opcode table itself — a `PAN_8BIT` flag makes V1/V3 read `PAN` as a full
0-255 byte while V2/most-V4 double a 0-127 value internally — found only by
reading the event-handler *bodies*, not just the opcode-name/length tables
the earlier FFVI pass had already mined. See
`docs/ffv/snes/data-structure.md` §12 and the sourced
`boot-upload-blob-delta-not-driver-wide.md` pitfall for the one real trap
hit along the way (a driver-code blob's own ARAM<->file delta does **not**
apply to a separately-uploaded data table's ARAM addresses, even when they
"look" plausible).

**FFIV's AKAOSNES V1** driver segment (LoROM file `0x20000`) and its full
46-entry opcode table (`0xD2`-`0xFF`, a different assignment than V3's own
46-entry table at the same numeric range) were confirmed the same session,
via the same method, as a deliberate, explicit stopping point (per that
session's own scope guidance to finish one game before starting a second) —
sample tables, song-table location, and a renderer were **not** attempted.
Worth noting for a future pass: V1's boot-upload table reads via two
*separate* byte arrays (`LDA table_lo,X` / `LDA table_hi,X`, a
structure-of-arrays split) rather than V3/V4's single interleaved 2-byte-LE
array — the shared boot-table *shape* finding above does not extend
backward to V1 unchanged. **A later session took this all the way to a
working real-hardware renderer** — see the "FFIV gets its own real SPC700
boot harness" entry near the end of this file. See
`docs/ffiv/snes/data-structure.md` §13 and `docs/ffiv/TODO.md`.

A later FFVI-only session (`docs/ffvi/snes/data-structure.md` §18.16) did a
systematic audit of the whole renderer against `vgmtrans/vgmtrans`'s
*complete* `AkaoSnesSeq`/`AkaoSnesInstr` reader (not just the opcode
table/argument-length shape earlier sessions had already mined) and found 6
more real, ROM-byte-verified gaps this way: three `_FADE` VCMDs
(`VOLUME_FADE`/`PAN_FADE`/`TEMPO_FADE`) that were complete no-ops despite
heavy real usage, a decoded-but-never-applied `ONETIME_DURATION`, a
`MASTER_VOLUME` scaling bug (copied `VOLUME`'s confirmed `AND #$7F`/127
convention by unverified analogy — the real handler is unmasked 0-255), and
`ADSR_AR`/`DR`/`SL`/`SR`/`DEFAULT` being no-ops despite real per-track
envelope-override usage. Reused, rather than rebuilt, a from-scratch SPC700
disassembler + raw uploaded-driver-blob dump a concurrently-dispatched
sibling agent had already built and validated in the same session's shared
scratchpad (see `shared-scratchpad-has-sibling-agent-tooling.md`). Also
confirmed VGMTrans's vibrato/tremolo/pan-LFO/pitch-slide/pitch-envelope code
(`AkaoSnesModulation.cpp`/`AkaoSnesTrackPitch.cpp`) is pure MIDI/SF2-export
cents/dB math throughout, not a hardware model, despite living in the same
"reader" source directory as the genuinely-accurate opcode/argument
parsing — see `reader-side-may-still-be-export-target-math.md`. Likely
worth the same style of audit for FFV's/FFIV's own AKAOSNES ports before
assuming their earlier, shallower VGMTrans cross-checks caught everything.

**§18.16's "pure MIDI/SF2-export noise" verdict above was itself corrected
in a following session** (`docs/ffvi/snes/data-structure.md` §18.19) — it
had only read 2 of the `AkaoSnes/` reader directory's files and missed a
third, `AkaoSnesTrackLfo.cpp`, which (read this session alongside the other
two) contains real, version-aware (`AKAOSNES_V1`-`V4`) driver-parameter
decoding the export math sits downstream of. This session read the whole
`AkaoSnes/` directory, then — rather than trusting VGMTrans alone —
cross-checked every claim against `everything8215/ff6`'s own
`src/sound/ff6-spc.asm`, a hand-labeled full SPC700 driver reconstruction
shipped by the same "rebuilds the ROM byte-for-byte" oracle project already
used elsewhere in this corpus, spot-verified byte-exact against this
project's own `SPCCode` disassembly before being trusted. Result: vibrato/
tremolo (a real triangle-wave LFO, `CalcVibratoRate`/`UpdateVibratoTremolo`,
with a genuine confirmed hardware quirk — tremolo's consumer silently drops
negative LFO swings instead of subtracting, so "negative"-direction
tremolo is near-inaudible while the identical direction mode on vibrato is
fully audible), pan-LFO ("pansweep," a simpler real bipolar triangle with
no smoothing layer), and `PITCH_SLIDE` (a real one-shot linear pitch ramp,
armed by the VCMD and consumed at the next NOTE/TIE dispatch) are all now
implemented in `akao-render.ts`, verified via 10 new hand-derived unit
tests (`akao-render-lfo.test.ts`) plus the existing 85-song corpus smoke
test — 155/155 project tests, `tsc`, and lint all clean.
`PITCHMOD_ON`/`OFF` turned out to be a *different* mechanism entirely — the
real S-DSP `PMON` hardware register (cross-voice frequency modulation from
the immediately-preceding voice's own output), identified by elimination
against two already-confirmed sibling registers (`ECHO_ON`→`EON`,
`NOISE_ON`→`NON`) cached in the same cold-boot init block in register-map
order — confirmed but left an explicitly documented no-op (real usage
28/85 songs vs. vibrato's 369/85; implementing it well would need
reordering the render loop's per-voice mixing to strict ascending order).
Sourced two new pitfalls: `adjacent-cache-slot-elimination-identifies-register.md`
(the register-by-elimination technique) and
`parallel-lfo-vcmds-may-clamp-asymmetrically.md` (the tremolo asymmetry).

**FFV gets its own real SPC700 boot harness** (`tools/ffv/akao-spc-render.ts`,
mirroring FFVI's §19 architecture but for AKAOSNES V3). Real progress beyond
§12's earlier boot-table-only identification: `everything8215/ff5` turned out
to ship a **full labelled SPC700 disassembly** (`src/sound/ff5-spc.asm`) and
65816-side driver source (`sound-main.asm`/`song-data.asm`) the earlier FFV
session hadn't consulted — every address/mechanism in the new renderer was
read from that source then independently re-verified against this project's
own ROM bytes. Found and fixed a real, previously-undocumented off-by-one in
the existing `akao-samples.ts` (`MUSIC_ADSR_ADDR` was 1 byte late,
`MUSIC_COUNT` was 34 instead of the real 35) via a 5-hop, zero-slack
arithmetic-closure chain from the already-confirmed `SongScriptPtrs` through
five further tables ending at FFV's own real `SongSamples` (the exact
structural analogue of FFVI's own `SongSamples` mechanism, §19.10) — also
newly wired in for correct per-song instrument resolution, and two
newly-found real tables (`MUSIC_LOOP_START_ADDR`/`MUSIC_FREQ_MULT_ADDR`) that
resolve the earlier session's "no confirmed tuning table" open item.

Two genuinely new boot-harness gotchas this game's driver surfaced (neither
present in FFVI's own equivalent, sourced as their own pitfall files —
`boot-injection-entry-still-calls-bypassed-blocking-transfer.md` and
`session-persistent-channel-state-has-no-cold-boot-default.md`): (1) FFV's
real "load song" entry point (`PlaySong`, ARAM `$0DA8`) is NOT directly
force-callable the way FFVI's `$0A92` is — its own first third calls the same
generic port-protocol transfer routine (`TfrData`) the bypassed main-CPU
handshake uses, which hangs forever without a real main CPU; the harness
instead force-calls `$0DD4`, the instruction right after that call would have
returned. (2) Per-channel volume/pan (`wChVol`/`wChPan`) are session-persistent
state FFV's driver never resets across a song load by design (real hardware
inherits it from whatever played before) — confirmed via live DSP
register-write tracing (`KON`/`PITCH`/`SRCN` all correctly populated,
`VOL(L)/VOL(R)` permanently `0x00`) after `InitCh`'s own full body was traced
and found to never touch either register (unlike the sibling `PlaySfx` path,
which sets an explicit `0x60` SFX default — confirming the asymmetry is real,
not an oversight). Seeding both to a defensible default (full volume, center
pan) — an honest, flagged approximation, not a traced value — took several
songs from flat silence to real audio (peak 0 → 0.4-0.8). That session also
flagged an apparent "slow-tempo bootstrap" mystery (`PlaySong` resets tempo
to ~1 BPM and many songs' first `TEMPO` VCMD seemed unreachably deep) —
**resolved by a later re-oracle session as a misdiagnosis**, see the next
paragraph. Verified end-to-end at the time: 72/72 songs construct with zero
exceptions, live Playwright browser check against the actual viewer (song
16, peak 0.441, zero console errors, real `blob:` URL on the `<audio>`
element), full existing FFV/FFVI/shared test suite green (284 tests).

**FFV renderer fully working after a re-oracle escalation** (closed
`ffv-spc-slow-tempo-bootstrap`): the real root cause of 46/72 songs
rendering silent was the **song-header model reading every field 2 bytes
early** — it had been transcribed from VGMTrans's `parseHeader()`, which
parses *SPC rips* (post-upload ARAM images); the ROM blob prepends a
2-byte transfer byte count that the 65816 upload loop (`sound-main.asm`
`@0242`-`@0271`) consumes and never uploads. Real at-rest blob header: 22
bytes, `[transferLen][scriptBase][8 track ptrs][endAddr]`, data at +22;
resolution is mod-65536 (song 4's pointer space genuinely wraps through
`$FFFF`). Structural closure invariant, 72/72 exact: `(endAddr - base)
mod 2^16 == transferLen - 20`. Every song's whole upload fits ARAM
verbatim (corpus max `0x14AC` bytes, window `$1C00`-`$4800`), so the
harness's `walkSongData` packer + romBase-neutralization trick was
deleted outright in favour of a verbatim copy relocated by the driver's
own `PlaySong`/`UncondJump` `addw` arithmetic. The old model had passed a
397k-event corpus walk with zero errors (AKAO's grammar has no invalid
byte sequences — walk cleanliness is a near-zero-power oracle there), and
the emulated driver had faithfully executed the misplaced bytes,
"corroborating" the wrong tempo theory with consistent timing. After the
fix: **71/72 songs render real audio within 1.5s** (the exception, song
17, is the literal "Silence" placeholder — 7/8 null tracks, empty
`SongSamples`); 71/72 songs have a `TEMPO` VCMD at zero elapsed ticks
(`PlaySong`'s `zTempo=1` + `zSongTickCounter=#$FF` reset is a deliberate
*fast* bootstrap — the first tick fires ~4.5ms after load and executes
every track's leading VCMD run including its `TEMPO`); the earlier
`wChVol`/`wChPan` seeding is now defense-in-depth (every real track opens
with its own `VOLUME`/`PAN` VCMDs). Sourced
`reference-tool-parses-runtime-image-not-rom-blob.md` and the
corpus-scale addendum to `rle-decode-succeeds-on-garbage.md`. Docs:
`docs/ffv/snes/data-structure.md` §12.2-12.4 + §13.6-13.9 correction
blocks; 348 tests green across all three games after the fix.

**FFIV gets its own real SPC700 boot harness** (`tools/ffiv/akao-spc-render.ts`,
the last of the three games to get one — completing the trilogy's music
pipeline). Real progress beyond the earlier driver-identification-only pass
(above): a fresh clone of `github.com/everything8215/ff4` turned out to ship
the same kind of asset FFV's own session found in `ff5` — a **full labelled
65816 + SPC700 disassembly** (`sound/sound.asm`, `notes/ff4-spc.asm`,
`notes/ff4-spc-ram-map.txt`), not just the self-describing JSON data-rip
this project's other FFIV modules had already been using from that same
repo. **Worth checking for on any "everything8215"-shaped disassembly repo
before assuming only the JSON rip exists**: grep the tree for a `sound/`
directory or `notes/*-spc.asm` file — the JSON rip and the disassembly are
two independent assets the same repo can carry, and earlier sessions
touching only the JSON side (FFIV's own text/graphics work in this same
corpus, e.g.) don't rule out the fuller disassembly also being there.

Two genuinely new findings, both source-verified against real ROM bytes,
not carried over from V3/V4:

1. **FFIV's boot upload is the plain, documented SNES/SPC700 IPL protocol
   directly** (`[count:u16][dest:u16][payload]*` blocks, terminated by
   `count=0` + entry address) — not FFV/FFVI's shared, driver-family
   `InitTfrSrcTbl`/`InitTfrDestTbl` 6-block convention. Found by a byte-exact
   search for the real ARAM `$0800` code's own leading bytes (from the
   disassembly), which hit exactly once in the whole ROM; walking the block
   sequence from there gave 8 blocks, every one landing byte-exact, zero
   slack, on a ram-map-documented region. **A shared engine/driver family
   does not guarantee a shared boot-upload convention** — verify each
   game's own `InitSound` routine rather than assuming the sibling games'
   already-confirmed table shape carries over (the existing FFIV entry
   above already flagged the "structure-of-arrays" difference as a hint of
   this; this session found the full mechanism).
2. **FFIV's song/sample tables use ca65 `.faraddr (label - base)` signed
   relative offsets, not literal far pointers** — resolved at runtime by a
   65816 routine (`AddPtrOffset`) with real piecewise bank-selection
   arithmetic. That routine did NOT need porting: LoROM banks only use their
   upper `$8000`-`$FFFF` half for ROM data, and consecutive banks' upper
   halves map to *exactly* contiguous file offsets, so a link-time
   `label - base` byte distance is numerically identical to a **file-offset
   delta** — confirmed byte-exact, zero slack, five ways at once (the base
   table's own header predicts five sibling tables' real file offsets, each
   independently cross-checked against that table's own source-cited CPU
   address). Worth remembering for any other `ca65`/LoROM-linked driver
   using this exact macro pattern (`make_ptr_tbl_far`-style relative-offset
   tables): the runtime relocation routine is a red herring for a static
   decoder, not a thing that needs reimplementing.

A genuinely tricky boot-harness bug, root-caused only by single-step
tracing (sourced as `idle-loop-frequency-detection-can-select-a-subroutine-
interior.md`): FFV/FFVI's established "most-visited PC over a long sampling
window" technique for finding a safe SPC700 idle-loop re-entry point
**silently picked an unsafe address** for FFIV's driver. FFIV's `Main` loop
nests a busy-wait that calls a subroutine (`CheckInt`) every single spin
iteration; that subroutine's own interior PCs (reached via a real `CALL`,
with a return address already on the stack) rack up *more* hits than
`Main`'s own top-level loop head and dominated the histogram. Force-calling
a new target from inside `CheckInt` corrupts the stack once its own natural
`RET` eventually fires — every song rendered exactly **zero** audio (not
quiet, `peak=0` across the whole 70-song corpus), with no exception and no
obvious symptom pointing at the cause; a naive listener would plausibly
blame the volume/pan cold-boot gap (§ below) instead. A single-step
`pc`/`sp` trace (print every instruction) immediately showed the real
desync. Fixed by targeting `Main`'s own real, source-confirmed loop head
directly (a known-good address from the disassembly) instead of detecting
one heuristically — verified by re-tracing: the injected call now reaches
its own natural return at the exact same step count every time, with `sp`
constant throughout. **This heuristic is only safe for a flat, 2-3
instruction idle loop** (FFV/FFVI's own shape); any driver whose idle loop
nests a subroutine call inside a busy-wait needs a source-confirmed target
address instead, not the frequency histogram.

Also hit FFV's own `wChVol`/`wChPan` gap again — independently
re-confirmed by direct trace, not assumed by analogy (per-channel
volume/pan has no cold-boot default; §
`session-persistent-channel-state-has-no-cold-boot-default.md` generalizes
across all three games' drivers now). Verified end-to-end: 70/70 songs
construct with zero exceptions, 11/11 spot-checked songs produce real
non-silent audio (peak 0.12-0.85) with 7 fully-silent and 1 near-silent song
independently confirmed as genuine "no music"/tie-only content (not a
renderer gap, via a corpus-wide null-track scan), live Playwright browser
check against the actual viewer (song 1, peak 0.496, zero console errors,
real waveform + playable `<audio>` element), full FFV/FFVI/FFIV/shared test
suite green (345 tests) after the change. No VCMD-level renderer was built
for FFIV at all — a deliberate scope call, not a gap: with the opcode table
already confirmed and the disassembly oracle available from the start
(unlike FFV/FFVI, whose VCMD renderers predate their own `everything8215`
disassembly discoveries), going straight to the real-hardware harness
avoided re-deriving pitch/envelope semantics by hand for a driver version
this project had no prior renderer for.
