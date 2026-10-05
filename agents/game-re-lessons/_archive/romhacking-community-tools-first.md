# Search the romhacking community for the exact game before decoding blind

**When it bites:** starting to reverse-engineer an unfamiliar compression
scheme or binary format for a commercially-released, pre-2000-ish game —
before writing the first entropy scan or hypothesis probe.

Most such games have an active romhacking/speedrun/preservation community,
and that community routinely publishes exactly what you're about to spend
hours re-deriving: standalone C/Python compressor-decompressor tools with
the algorithm already reverse-engineered from disassembly, often bundled
with a same-game test suite listing dozens of known-good ROM/file offsets
and their exact decoded sizes — a near-zero-cost, high-confidence ground
truth oracle, not just a hint.

Jungle Strike (Genesis): a plain WebSearch for `"Desert Strike" OR "Jungle
Strike" OR "Urban Strike" Genesis EA compression format disassembly` found
`infval/StrikeLZSS` on GitHub — a public LZSS reimplementation for exactly
these three games, complete with a documented execution breakpoint per game
(PC address + which register holds the source pointer) and a test suite
listing 34 known-good compressed-block ROM offsets for this exact ROM. All
34 decoded cleanly against the project's actual ROM file with the exact
declared size, and the same routine was then found and disassembled at the
documented breakpoint address, matching the reference implementation's
constants exactly (window size, initial window position, control-byte
refill logic). This turned what could have been a multi-day blind-scan +
disassembly effort into roughly an hour of verification, and gave a
34-offset ground-truth list that a blind structural scan would have had no
way to produce with equal confidence.

This is a distinct, higher-value move than the general "check other
platform ports for the same game" oracle strategy (see
`cross-platform-decode-oracles.md`) — it's specifically about searching for
*standalone romhacking-community compression/format tooling* (GitHub,
romhacking.net utilities, SGDK/dev-community docs), which frequently exists
even when no full source port or disassembly does. Do this search **before**
starting blind entropy/structural scanning, not as a fallback after it
stalls — it's cheap (one WebSearch) and, when it hits, is strictly better
evidence than anything a from-scratch static analysis pass can produce on
its own.

## A multi-game reimplementation's own signature/version-classification database identifies which variant you're looking at, byte-exact, with zero disassembly

When the target is one of a *family* of closely-related formats/engine
versions across many games (a shared sound-driver lineage, a shared
container format with per-title quirks) and a mature multi-game
reimplementation project exists for that family, its own source almost
always contains a **classifier** — code that fingerprints an unlabeled
input file well enough to pick the right game/version-specific parsing
path automatically. That classifier's fingerprints (literal byte-pattern
constants, whole in-memory tables) are a stronger, cheaper oracle for the
"which variant is this" question than any disassembly, because the
reimplementation project already had to solve exactly that problem for
every game it supports. Confirmed on FFVI/V/IV (SNES, `~/Development/
ceres`): `vgmtrans/vgmtrans` (an SPC-sequence-to-MIDI converter) ships a
dedicated `AkaoSnes` format module whose scanner searches an SPC dump for
several SPC700-instruction byte-patterns (with wildcards for game-specific
immediate operands) and then disambiguates the exact game/build via a
**literal 46-60 byte VCMD-argument-length table constant per title**
(`FF4_VCMD_LEN_TABLE`, `FF6_VCMD_LEN_TABLE`, etc., in
`AkaoSnesScanner.cpp`). Cloning the reimplementation and grepping its
format module for these constants, then running a **plain whole-ROM
byte-exact search** for each one (no address translation, no relocation
math, no disassembly) gave a single, unambiguous hit for the exact title-
specific table in each of three ROMs (FFIV -> `FF4_VCMD_LEN_TABLE`, V1;
FFV -> `FF5_VCMD_LEN_TABLE`, V3; FFVI -> `FF6_VCMD_LEN_TABLE`, V4/FF6),
identifying the driver family, major version, and title-specific minor
version simultaneously, before a single instruction was disassembled —
and each hit landed inside the ROM region a separate community bank-map
hypothesis had already guessed was the sound driver, corroborating that
hypothesis for free. This generalizes beyond audio drivers to any format
family with an actively-maintained multi-game community tool (texture
codecs, archive containers, script VMs): check whether the tool
*classifies* inputs, not just parses a single known-good one — a
classifier's fingerprint constants are reusable as a search oracle even
when you have zero interest in running the tool itself.

## The full-source fan viewer/editor case

The same move pays off even bigger for **record/table formats** (not just
compression), when the community tool is a full GUI viewer/editor shipped
with complete source rather than just a compressor+test-suite: the tool's
own parser class *is* the reader (Method §2's "find the reader"), for free,
without any disassembly. Phantasie I/II/III's dungeon/star/action/message
formats (`~/Development/nicodemus`) were fully recovered this way from a
fan-made Windows dungeon-viewer's C# source — every header offset, record
stride, and opcode table came directly out of reading the parser, no
disassembly needed. Two things this case adds beyond the compression-tool
pattern: (1) there's usually no bundled test suite of known-good
offsets/sizes to check against, so every recovered offset and formula still
needs independent byte-exact re-verification against your own project's
real data files before it counts as confirmed (in this case: simulating the
reference tool's own record-scan algorithm against 10 real dungeon files
and checking the terminator lands where the source's hardcoded constants
say it should); and (2) the tool's own source comments can themselves be
ground truth about the *original game's* behavior, not just about the file
format — Phantasie III's reference source flagged (in a code comment) an
off-by-one bug in its own trap-message-index formula relative to
Phantasie II's, which is a real, confirmable divergence between the two
games' engines, not a note about the viewer. When the source is
copyrighted and can't be committed or reproduced verbatim, this still
works fine — treat it exactly as you'd treat reading a disassembly: absorb
the structure, write the format doc in your own words (prose/tables), and
never reference the ephemeral scratch path from committed docs.

## When the community project has no test suite at all: `git clone` and read the source, then re-verify anyway

Some reference projects are neither a compression tool with a test suite
nor a viewer with source comments — they're a full engine reimplementation
(an emulator/interpreter, not just a format parser) whose own *prose docs*
summarize the format but whose *source* is the real ground truth. Treat a
web-search summary of such a project's docs as a lead, not an answer:
`git clone` it and read the parser source directly before writing a single
line of your own decoder. Confirmed on EOB3 (`~/Development/crawl`,
AESOP/16 engine, no ScummVM support): `WebFetch`ing ThirdEye
(`github.com/psi29a/thirdeye`)'s GitHub page only summarized its resource-
format docs vaguely; cloning the repo and reading
`apps/thirdeye/resources/res.cpp` / `graphics/cps.cpp` /
`resources/gffi.cpp` directly gave exact struct layouts in about the same
wall-clock time the vague summary took to produce.

**When the open question is a *runtime* mechanism, not a static file layout,
read the reference project's runtime/interpreter module — not just its
resource-container/format-parser module.** A "which resource pairs with
which other resource" question can look like a missing on-disk cross-
reference field when it's actually not a static 1:1 relationship at all.
Confirmed on EOB3: the open question was "which named palette resource
pairs with which `EYE.RES` monster/decoration bitmap" — no field in the
container format answers this, and the natural next step looked like
disassembling AESOP bytecode (out of scope). The actual mechanism was in
ThirdEye's `apps/thirdeye/runtime/graphics.cpp` (its bytecode-function
dispatcher, not `resources/res.cpp` or `graphics/bitmap.cpp`), which
hardcodes `kFirstColor[5] = {0x00, 0xB0, 0xC0, 0xE0, 0xB0}` — 5 fixed
windows into the 256-colour VGA DAC that the original engine's bytecode
loads palettes into at runtime (`set_palette(region, resource)`). Once the
window bases/widths were known, a bitmap's own stored pixel-value range
(no bytecode trace needed) revealed which window it used, and a cheap
name-match + declared-colour-count check against palette resources
resolved 265/312 (85%) bitmaps to real, visually-confirmed colour. The
general move: if a reference reimplementation exists and the question is
"how does the original engine wire these two resource types together at
runtime" rather than "what does this file's byte layout mean", search its
*runtime/VM/interpreter* source for hardcoded slot/region/constant tables
before assuming you need to trace the actual bytecode — the reimplementer
already had to solve exactly this to make the original engine's assets
render correctly, and the constant table is usually a small, greppable
array near the function that consumes it.

**An oracle project can fully support a *format* while still not exercising
every *file* of that format — check whether its code path actually reaches
the specific file, not just files of the same type.** ThirdEye fully
implements EOB3's `GFF` cutscene-container format (used by 4 files:
`INTRO/DARK/FINALE/LICH.GFF`), but its own cutscene sequencer
(`apps/thirdeye/resources/gffi.cpp`, `getSequence()`) contains exactly one
branch — `if (filename == "INTRO.GFF")` — with zero handling for the other
3 files. This wasn't discoverable from "the format is confirmed" (it is);
it required reading the whole function and counting `if` branches. Before
treating a working reference project as ground truth for *this specific
file's* remaining open question (e.g. a missing embedded palette), verify
its code path is actually reached for that file, not just structurally
parses it.

**A reference tool's cited offsets carry over exactly when its target is
the literal same compiled binary — never merely "the same game family" or
"the same engine."** This is easy to get backwards: it's tempting to guess
that offsets transfer based on how closely related two games/ports feel,
but the real determinant is much narrower. Confirmed three ways on the same
Phantasie reference tool (which stores offsets per source binary it was
originally run against): (1) Phantasie I's offsets, recorded against the
Amiga `game` executable, worked unchanged when checked against this
project's own real Amiga `game` file — same exact binary. (2) Phantasie
II's offsets, recorded against an Atari ST `PHANT.PRG`, worked unchanged
when checked against this project's own extracted, real Atari ST
`PHANT.PRG` — again the same exact binary (P2 only ever shipped on ST, so
there was only one binary to begin with). (3) Phantasie III's race-table
offsets, recorded against the Atari ST build (`PHANT_3.PRG`), produced pure
garbage against this project's Amiga `PhantasieIII` binary — a *different
compiled binary* for the same logical table, despite being the same game,
same publisher, same era, and both binaries otherwise using the identical
engine and confirmed-shared file formats elsewhere. The lesson: before
assuming a reference source's offsets need "adjustment" or are "close
enough," check whether your target file is byte-identical (or a direct,
unmodified copy) to the binary the reference source actually recorded
offsets against — if yes, expect them to carry over exactly with zero
adjustment; if it's a different compiled binary for any reason (different
platform port, different compiler pass, different linker), expect them not
to transfer at all and budget for full re-derivation, not a small offset
correction.

**Don't assume a reimplementation project lacks platform coverage without
checking its own detection/config tables — a partial first impression is
not proof of absence.** A reimplementation aimed primarily at one platform
(its README, changelog, or your own prior session's summary emphasizing
DOS/Windows support) can still have full, first-class support for a
sibling platform port that never got mentioned in the parts you happened
to read. Six pre-existing TODO items on EOB1/EOB2's Amiga ports (`crawl`
project) were carried for a prior session under the instruction "first
determine whether ScummVM's Kyra engine covers the Amiga ports at all... it
may only cover DOS" — a reasonable-sounding caution, but wrong: ScummVM's
`engines/kyra/detection_tables.h` has real, complete `kPlatformAmiga`
detection entries for both games (multiple languages each), plus a
dedicated `screen_eob_amiga.cpp` and `kPlatformAmiga` branches through
essentially every engine/graphics/script file — full parity with the DOS
oracle, not a gap. The one-line, near-zero-cost check that would have
settled this immediately: grep the reimplementation's own detection/config
table (`detection_tables.h`, a game database, a platform-enum switch) for
the target platform's identifier, before writing "oracle coverage unclear"
or "may not exist" into a doc. Do this check as a first move whenever a
TODO item's premise includes any version of "not sure this engine covers
platform/game X" — it's cheaper than the hedge itself.

## Forum attachment links can 404 on their displayed URL — grep the raw HTML for the real relative path

A forum thread's *rendered* download link (what `WebFetch`'s markdown
conversion shows you, e.g. `http://forum.example/download.php?id=5717`) is
not always the link that actually resolves — some forum software (VOGONS,
confirmed) serves attachments from a different relative path than the one
displayed in the page's readable text. `curl`ing the displayed URL 404'd
here; `curl`ing the *thread page itself* and `grep -oE 'download/file\.php
\?id=[0-9]+' thread.html` found the real path
(`./download/file.php?id=5717`, one directory level and one filename
different) — every attachment on the page downloaded cleanly once the
right relative path was used. Before concluding a forum-hosted archive
"isn't available" from a 404, fetch the raw page HTML directly (not through
a markdown-summarizing fetch) and grep for the attachment ID's *other*
occurrences — most forum templates link the same attachment ID from two
different URL shapes (an inline "download.php" convenience link and the
real "download/file.php" attachment-serving path), and only one resolves.

## A second independent community tool's *source* can out-rank a from-scratch reimplementation as an oracle

When a community reverse-engineering tool exists for a format *and* the
original author released real interpreter/engine source (both linked from
the same forum thread, confirmed on AESOP's VOGONS thread — John Miles'
own interpreter source plus Mirek Luza's independent DAESOP decompiler/
converter), don't stop at whichever one you find first: **both are
independently useful, and cross-checking a from-scratch derivation against
the second tool's own source is stronger evidence than either alone.**
Real engine source gives byte-exact struct definitions with zero guessing
(confirmed on Dungeon Hack: `DEFS.H`'s `PAL_HDR{ UWORD ncolors; UWORD RGB;
UWORD fade[11]; }` matched a palette-header layout already derived
independently from pure structural/arithmetic analysis, field-for-field).
A *second*, independently-produced community tool's source can then
corroborate the same derivation from a completely different angle even
when its own header comment admits uncertainty — DAESOP's `convert.h`
flags its `OLD_FONT_HEADER` struct "almost certainly incomplete," yet its
converter code (`convert.c`) independently arrived at the identical
offset-table base address (`0x108`) and per-glyph span formula
(`2 + columns*height`) that this project derived from scratch by a byte-
ramp scan — two independent RE efforts converging on the same answer from
different methods is about as strong as verification gets without running
the original executable. Worth deliberately searching a thread for *every*
linked archive, not just the first one that looks like "the format spec."

## When the reference project ships a self-describing data-rip *definition*, prefer it outright over disassembly reading

Some rebuild-from-source community projects go one step beyond "a script
that extracts data" (the previous section) to "a structured data file that
*declares* every table's location, record layout, pointer-table shape, and
text-encoding rule, consumed by a small generic decoder." When this exists,
treat it as the fastest path available — faster than reading the extractor
script's logic, and far faster than tracing disassembly — because the
address/layout information is already machine-readable, not embedded in
control flow you have to reverse. Confirmed on FFIV (SNES, `ceres`
project): `everything8215/ff4` (same author as the `ff6` oracle already
used for this project's FFVI corpus) ships `vanilla/ff4-en-rip.json`
(~9800 lines) — every table's CPU address, record stride, pointer-table
shape (`pointerTable.offset`/`isMapped`), and text-encoding rule
(`charTable`/`textEncoding` objects) is declared data, consumed by that
project's own generic `tools/romtools/rom-decoder.js`. Reading the JSON
directly and re-implementing the (short, generic) resolution logic in a
few dozen lines was enough to decode 12 distinct name/dialogue resource
pools with byte-exact cross-checks against the JSON's own reference
strings, with **zero disassembly reading** needed anywhere in the session
— a marked speedup over the disassembly-driven approach the sibling FFVI
sessions on the same project needed for the same class of tables. Before
falling back to reading a reference project's extractor *script* logic or
its disassembly, check whether it ships this shape of asset instead (look
for a JSON/data file the extractor script loads as its own input, not just
ROM bytes) — when it exists, it is both cheaper and just as strong an
oracle, since the extractor's own correctness depends on that data file's
accuracy for the project's rebuild-and-diff workflow to succeed at all.

**Caveat, confirmed on the same reference project in a later session:** a
self-describing rip JSON's declared *data shape* (addresses, record
strides, an array of named alternative templates) is usually solid, but it
does not always declare the *selection logic* for choosing between two or
more variants it lists — which one applies to which specific record. FFIV
(SNES)'s `characterGraphics` entry declares two named tile-formation
templates (`"Default"`, `"Golbez/Anna"`) across 17 characters, but nothing
in the JSON says which characters use which template, nor gives the exact
byte offset for the two characters whose data doesn't fit the array's own
uniform per-record stride (their real source file is a binary `.incbin`
not present in the disassembly clone at all). Both had to be resolved by
reading the actual disassembly (`ReloadCharGfx`/`GetExtraCharGfxPtr`/
`UpdateCharSpritesheet` in `everything8215/ff4`'s `btlgfx/*.asm`) — a
`cmp #$0f; bcc` id-threshold check the JSON gives no hint of at all. The
general shape: trust a self-describing rip JSON for *where data lives and
how it's laid out*, but the moment a table declares more than one named
variant/template/mode with no per-instance selector field alongside it,
expect to need the disassembly (or a render-based empirical test, if the
disassembly isn't available) to learn which instances use which variant —
don't assume the declarative rip is a complete spec just because it's
usually sufficient for plain offset/stride/pointer-table questions.

**A second caveat, confirmed on the same reference project in a much later
session:** the self-describing JSON rip and a fuller *disassembly* are two
independent assets a rebuild-from-source repo can carry side by side —
earlier sessions using only the JSON side don't mean the repo lacks the
other. `everything8215/ff4`'s JSON rip covers static data tables (names,
dialogue, stat records) but has no representation for driver/*behaviour*
work at all — a sound driver's boot sequence, ARAM addressing, and
interrupt dispatch simply aren't expressible as a "table location + record
layout" declaration. A later session on the exact same repo, needing to
build a real SPC700 boot-injection harness, found it *also* ships a full
labelled 65816 + SPC700 disassembly (`sound/*.asm`, `notes/*-spc.asm`) that
three earlier sessions touching only the JSON side had never looked for.
**Before starting driver/code-behavior work on any repo already used as a
JSON-rip oracle, grep its tree for a `sound/`/`notes/`/similarly-named
directory of hand-labelled `.asm` files** — don't assume "we've already
used this repo, so we've already seen everything useful it has."

## A community script's fixed byte offsets can be correct even when its full per-entry walk logic diverges — check whether it assumes different upstream preprocessing

A community reference script that reads a format's header via fixed
`readInt32BE`-style offsets is not all-or-nothing evidence: its scalar
field *positions* and its per-entry *walk logic* are separable claims, and
one can be right while the other is wrong for a structural reason that has
nothing to do with the field positions being wrong. Confirmed on
Drakengard 3 (PS3, UE3 packages, `flower` project): a community modding
tool's Node.js importer script read `nameCount`/`nameOffset`/
`exportCount`/`exportOffset` at fixed offsets `0x19`/`0x1D`/`0x21`/`0x25`
in a `.xxx` package file. Cross-checking `nameCount`/`exportCount`/
`importCount` against an independent, authoritative third-party parser's
own reported values (running the real `umodel` tool against the same file
and comparing its printed `Names: N Exports: N Imports: N` summary) showed
all three counts matched exactly — real, working, structural confirmation
of the field *positions*. But the script's own per-name walk (`len(4) +
string + 8` trailing bytes per entry, iterated from `nameOffset`) produced
garbage after the first 1-2 entries when run directly against the raw file
bytes. The likely reason (not fully confirmed, but consistent with every
observation): the script's documented workflow runs a separate upstream
decompression/unpacking tool (the same author's own "Unreal Package
Decompressor," distinct from the extractor script itself) *before* this
script ever sees the bytes — so the script's fixed offsets are correct for
its *actual* intended input, which is not the same byte layout as the raw
file tested here.

**The fix**: don't discard a community script's offset evidence just
because a direct trial-run of its full logic fails end-to-end — check
whether the failure is isolated to logic that depends on an assumption
(a prior processing step, a different input shape) the script's own
documented usage instructions state but that wasn't reproduced in your
test. Confirming the parts that *do* cross-check against an independent
oracle (three count fields matching umodel's own output here) is real,
keepable evidence even when the parts that don't cross-check point at a
missing precondition rather than a wrong offset.

One trap specific to this technique: a rip definition's address/`range`
fields are still **unmapped CPU addresses**, not pre-resolved file offsets,
even when a given value coincidentally looks like a plausible raw file
offset (a LoROM/HiROM console case, but the general shape — "structured
reference data still speaks in the platform's native address space, not
your output-file's byte offsets" — applies to any platform). See
`game-re-tooling/snes.md` for the concrete example and fix.

## A reference project's own extractor/build script is stronger evidence than its prose bank-map labels

**When the extractor is self-contained (drop a ROM in a `vanilla/`-style
folder, run one command), actually run it rather than only reading its
dispatch logic — it becomes a live, byte-exact diffing oracle for your own
from-scratch decoder, not just a source of offsets to transcribe.** This
is a step beyond "trust the script's branching logic over the prose"
below: running the real tool against your real file and diffing its output
against your own independent reimplementation catches bugs neither static
reading nor a same-file CRC32 match would surface on their own. Confirmed
on FFV (SNES, `ceres` project, `everything8215/ff5`): cloning the repo,
running `git submodule update --init` for its `romtools` dependency,
copying the project's own ROM into `vanilla/`, and running its `make rip`
produced full JSON text decodes and every raw/LZSS/RLE resource with zero
errors (CRC32 match). Diffing this project's own from-scratch TypeScript
dialogue decoder against that real output (not the reference project's
*code*, its *output*) surfaced two real bugs a code-only read would have
missed: an MTE dictionary code range where a from-scratch symbol-table
guess collided with an unrelated icon-glyph table at the same byte range,
and a test harness's naive terminator-scan bug (see
`multi-byte-code-second-byte-collides-with-terminator.md`). Both were only
visible because the actual byte-for-byte diff surfaced a wrong-but-
plausible string, not from reading either project's source.

When a community reference project ships both a prose "what's at this
address" bank-map doc *and* a working extractor/build script that actually
consumes the ROM, and the two disagree (or the bank-map is vague, e.g.
labelling a whole region "compressed"), trust the script's branching logic
over the prose. A prose label describes the region loosely; the script's
actual per-resource dispatch (which transform gets applied to which byte
range) is what the original game's own tooling verifiably does, because
the script has to get it right to reproduce a byte-identical ROM. Confirmed
on FFVI (SNES, `ceres` project): a prior session accepted "compressed" from
a community bank-level map for a monster-graphics region and never
re-checked it; this session found the reference project's own asset
extractor only runs its LZSS decoder on rip targets whose declared output
path ends `.lz` — the monster-graphics rip target has no such suffix — and
confirmed directly against real ROM bytes that the region isn't compressed
at all (a plausible LZSS header would need a nonsensical length value for
the first record). One `grep` for the file-extension dispatch in the
extractor script, cross-checked against the ROM's own first bytes, would
have caught this before it was ever written into a doc as a hypothesis.

**Point 1 above still applies even when the reference project's *docs*
(not just a hypothesis of your own) state a value outright** — a solved-
looking doc from a good oracle project is not automatically ground truth.
ThirdEye's own `docs/item_dat_format.md` documented `ITEMTYPE.DAT`'s
`AC_bonus`/`class_use_mask`/damage-dice fields at specific byte offsets,
citing specific AD&D 2e values (axe 1d8/1d10, banded mail AC −6,
spellbook Mage-only, ...) as its own verification. Cross-checking those
*same cited values* against the real file bytes for 27 named type records
showed every one of those fields was actually 2 bytes later than the doc's
offset table claimed — the doc's cited verification numbers were right,
its stated offsets were wrong. Re-deriving the offsets from the doc's own
cited ground-truth values against real bytes (rather than copying its
offset table verbatim) caught this in one pass. Moral: an oracle project's
source code being solid doesn't make its prose docs infallible — when a
doc cites specific verifiable values, re-derive the byte offsets from
those values against your own files rather than trusting the doc's stated
offsets, even from a project you otherwise trust.

## Search by the exact magic bytes/constants you've already found, not just the game's name

When a byte-level scan has already turned up something concrete — a 4-byte
magic string, an unusual filename fragment glimpsed in a `strings` dump, a
distinctive constant — search the web for **that exact token** alongside
the platform, not just `"<game name>" <platform> file format`. Confirmed
on Valkyrie Profile 2: Silmeria (PS2, `~/Development/valkyrie`): a generic
`"Valkyrie Profile 2" file format QuickBMS` search returned nothing
useful, but once raw byte-scanning had already turned up two distinctive
3-byte container tags (`"SLZ"`, `"SLE"`) inside the disc, a follow-up
search for `"SLZ" OR "SLE" file format PS2 tri-Ace Square Enix archive
compression container` immediately surfaced both an XeNTaX forum thread
titled around the exact tag and a fan tool (`CUE`'s `triAce-PS2.c`) whose
own `#define HEADER_SLZ0`/`HEADER_SLE0` constants matched byte-for-byte.
Do a first pass with the game-name-only search (cheap, sometimes
sufficient on its own — see the rest of this file), but don't stop there
if it comes up empty and a scan has already produced a concrete byte-level
fingerprint; re-search with that fingerprint before falling back to blind
structural analysis. This also works in the other order: if a scan turns
up a fingerprint before a name-only search was even tried, search the
fingerprint first — it's often the more specific, less noisy query.

## When a rip-list address resolves but the format still won't crack, look for the reference project's own codec/algorithm source, not just its declarative data

A self-describing rip-list (address + record stride + a named character
table) tells you **where** a resource lives and **what alphabet** applies,
but not always **how** to interpret a byte stream that mixes fixed- and
variable-width codes, lookahead rules, or parameterized escape codes — that
algorithm usually lives in a separate, reusable codec module the rip-list's
own extractor imports, not in the rip-list JSON itself. If a resource's
location and character table are already confirmed but the actual decode
still won't come out right (or was previously left "located but not wired
up"), search the reference project's own source tree for a generic
codec/reader class the extractor calls — not just its per-resource
declarative data.

Confirmed on FFVI-J (SNES, `ceres` project): a prior session had already
located and confirmed the JP release's MTE (word/phrase dictionary) and
kanji tables' addresses and content via `everything8215/ff6`'s rip-list
JSON, but left the actual dialogue-byte-stream format unsolved (no field
in the rip-list explains how control codes, kana, kanji, and MTE codes are
told apart in a byte stream, or what a code with a `:b`/`:w` suffix in its
name means). The answer wasn't in the rip-list at all — it was in
`tools/romtools/text_codec.py::TextCodec.decode()`, a ~30-line generic
class the project's own `extract_assets.py`/`encode_text.py` both import
and that literally *is* the format spec: a 2-byte-lookup-tried-first-then-
1-byte-fallback discriminator, plus a rule that any code value ending
`:b`/`:w` consumes 1/2 trailing raw bytes as a parameter (see
`escape-code-parameter-bytes-silently-misdecoded.md` for the pitfall this
also exposed in this project's own existing US-release decoder). Finding
and reading this ~30-line class turned a stalled "table located, not
wired in" TODO item into a fully verified decoder in one session, with
zero wrong hypotheses along the way — cheaper and more precise than
inferring the discriminator rule from byte-frequency analysis on the raw
ROM data would have been. Look for this kind of module by name pattern
(`*_codec`, `*Codec`, `text_codec`, `romtools`, a shared `decode()`/
`encode()` pair) in the reference project's tooling directory whenever a
rip-list gives you locations but not the actual byte-interpretation rule.

## A magic/fourcc can be a shared toolchain convention, not a game- or engine-specific tag

When a magic string search scoped to "this game" or "this developer" comes
up empty, drop those terms and re-search with just the magic plus generic
platform/toolchain words — the real answer may live on a completely
unrelated title's community wiki. Confirmed on Valkyrie Profile 2: Silmeria
(PS2, `~/Development/valkyrie`): a decoded payload started with a `"MWo3"`
fourcc, and searches naming the game/developer (`"MWo3" tri-Ace file format
PS2`) returned nothing. Widening to just `"MWo3" model format` (dropping
every game-specific term) surfaced the GTAMods wiki's **"PS2 Code Overlay"**
page — documented from a completely unrelated title (*GTA: San Andreas*'s
PS2 port), built with the same Metrowerks CodeWarrior compiler/linker
convention. The documented 64-byte header (fourcc, segment count, load
address, text/data/BSS sizes, callback-array range, embedded filename)
matched VP2's real decoded bytes exactly (`64 + textSize + dataSize ==
totalLength`, zero deviation across 4 samples, plus real recovered overlay
filenames) despite VP2 and GTA:SA sharing no engine, developer, or
publisher — only a build toolchain. A magic/fourcc is sometimes a
toolchain-era convention (a specific compiler/linker's own object/overlay
format) that shows up verbatim across totally unrelated codebases, not
something unique to the game or engine you're currently investigating.

## A self-describing rip JSON's field-level layout can be flatly wrong for one table even when its address and every sibling table's layout are correct

A rip JSON's declared record *address/count* being correct (independently
re-verified, even reused successfully for other tables in the same session)
is not evidence its declared *field-level layout* for that specific table is
correct — that claim needs the same real-load-routine verification as any
other prose source, every table, not a spot-check on one and a free pass for
the rest. Confirmed on FFIV (SNES, `ceres` project): `everything8215/ff4`'s
`vanilla/ff4-en-rip.json` (already used successfully, in an earlier session,
for a dozen text/name tables' addresses and pointer-table shapes) declares
`monsterProperties` as a flat, always-present 20-byte struct at fixed
offsets (`attackElements@10`, `attackStatus@11-12`, etc). Reading the real
load routine (`InitMonster`, `battle/init.asm`) showed this is wrong in two
compounding ways the JSON gives no hint of: (1) the table is **pointer-
indexed**, not `id * stride` — a separate `MonsterPropPtrs` table (224 x
2-byte addresses, immediately preceding the data) gives each monster's own
record start, and real ROM bytes confirm records **deliberately overlap**
(sorted offsets only 10-19 bytes apart, never a clean 20, plus one exact
alias — two different monster IDs sharing one identical record, a real
space-saving dedup); (2) byte 9 (which the JSON labels as a fixed
`attackElements` field) is actually a **6-bit flags byte** gating 0-3 bytes
each of optional trailing content, which is what explains the overlap. Two
*other* tables decoded in the same session, from the same JSON file
(`CharProp`, `AttackProp`), turned out to be genuinely flat/fixed-stride
exactly as declared — so the right response isn't "distrust this JSON
generally," it's "verify each table's declared record *shape* against its
real load routine independently, the same way you'd verify a hand-written
bank-map's prose," because a correct table address (itself independently
re-verifiable and often already cross-checked elsewhere) does not imply a
correct record shape, even from an otherwise-proven-reliable rip
definition. The tell that something was off, cheaply checkable before any
disassembly: sorting the resolved record-start offsets from the table's own
pointer/index array and diffing consecutive values — a genuinely
fixed-stride table produces one constant gap; this one produced gaps
ranging 10-19, immediately falsifying the JSON's flat-struct assumption.

## When an oracle tool's CLI hardcodes a different input variant than yours, patch it rather than giving up — and read unlicensed source as a spec, not code to vendor

A working community reimplementation/decompiler can be a perfect oracle for
your exact file even when its **shipped CLI** doesn't support your file's
specific variant — check whether the variant-specific offsets/logic already
exist somewhere in its source (a struct, an enum branch, a data table) before
concluding the tool "doesn't apply." Confirmed on Frontier: Elite II (Amiga,
`hunter` project): `watsonmw/fe2-intro` ships a from-scratch decompiler for
the game's 3D model bytecode, but its `main()` hardcodes loading the newer
"EliteClub2" CD32/shareware executable's table offsets — this project's
target file is the original ".1960" release, a different variant. Its own
`assets.c` already declared the original variant's offsets in an
`AssetsRead_Amiga_Orig` enum branch, just never wired to a CLI flag; a
12-line patch (one new `-orig` flag selecting that already-present branch)
was all it took to turn the tool into a working oracle for the actual target
file, run headless (`SDL_VIDEODRIVER=dummy ./tool -orig -dump-game-models
<exe>`) with zero parse errors across the whole corpus. Before writing off a
community tool as "wrong version/platform/format variant for my file," grep
its source for an enum, a version-detection table, or a per-variant branch
that already names your variant — a mismatched default CLI flag is a much
cheaper problem than "the tool doesn't cover this," and the fix is usually a
handful of lines.

**Read genuinely unlicensed reference source as a specification, not as code
to vendor.** Some of the best community RE projects (a solo maintainer's
GitHub repo, no `LICENSE` file, no license statement anywhere in the README
or source headers) leave real legal ambiguity about redistributing their
code verbatim into your own committed tree — treat this the same way you'd
treat a copyrighted fan disassembly or a scanned manual: absorb the byte-
level facts (struct layouts, opcode encodings, table offsets) by reading the
source, then write your own clean-room reimplementation in your project's
own style, crediting the source project in a doc comment. This sidesteps the
licensing question entirely (byte layouts and opcode semantics are facts
about the target file format, not the reference project's expression of
them) while still getting the full benefit of the reference project's prior
work. Confirmed on the same Frontier session: `fe2-intro`'s ~4,700-line
`modelcode.c` (no stated license) was read in full to extract the exact
32-opcode ISA (per-opcode word counts, branch/skip-length formulas, two
self-describing/self-terminating variable-length forms), then reimplemented
from scratch in Python (`tools/frontier/frontier_models.py`) with zero code
copied — and the two independent implementations were then cross-diffed
against each other's *output* (not source) as the verification step, which
is strictly stronger evidence than either alone (see the "actually run it"
oracle pattern earlier in this file) and has no vendoring/licensing exposure
at all.

## A zero-xref grep for a resource's own symbol means the community project never traced it either — pivot to loader-name-pattern search, don't give up

When a mature, self-rebuilding community disassembly declares a resource
(a `.segment`/`.export`/`.incbin` for a graphics or data blob) but a plain
`grep -rn` for that exact symbol name across the *entire* disassembly tree
finds nothing outside its own declaration, that's a real, informative
negative — it means the community project's own authors never traced that
resource's consumer/loader either, not that your grep missed something.
Don't read this as "this format is a dead end"; it means the shortcut this
project usually provides (an already-named loading routine to read) isn't
available for this specific resource, and the next move is a **different**
search: grep the game's own loader source (e.g. `field-main.asm`,
`main.asm`) for *loader-routine name patterns* related to the resource's
apparent role (`Tfr*Gfx`, `Load*`, `*ObjGfx`, `*SpriteGfx`) rather than the
undeclared symbol itself — the routine that actually reads the resource is
real and present in the source even when nothing points at the resource by
name. ## A multi-format tracker-module "unpacker collection" is the right oracle for a proprietary Amiga module packer with no standalone tool of its own

Some proprietary/studio-licensed formats never got a standalone community
tool at all — but a *player library's* multi-format module-unpacker
collection can still have a real, working reference decoder for it, because
those collections exist specifically to cover the long tail of obscure
packers found embedded in commercial games. Confirmed on Dungeon Master II:
Skullkeep (Amiga, `crawl` project): its `music/*.MOD` files (despite the
extension) are `P41A`-signed — "The Player 4.1A" by Jarno Paananen, a
packer never released as a standalone tool but licensed/leaked to multiple
game studios, so no dedicated "P41A cracker" exists to search for by name.
`libxmp` (a well-established, widely-used Amiga/tracker module player
library) ships exactly this as one format among dozens in its **ProWizard**
loader collection (`src/loaders/prowizard/p40.c`'s `depack_p4x()`) — found
via a plain web search for the magic string `P41A` plus "amiga module
packer," not a game-specific search. The general move: when a proprietary
packer/codec has no dedicated fan tool, check whether a mature *multi-format
collection* aimed at the general problem (tracker-module unpackers,
compression-format identifiers like `ancient`, texture/archive format
libraries) already covers it as one of many supported variants — these
collections are built to be comprehensive across a whole format family, so
"no tool for this exact obscure packer" is a weaker negative than it sounds
until that kind of collection has been checked.

**Faithful statement-by-statement porting, not shelling out, was the right
call here** — no CLI exists for ProWizard's individual format modules
(they're internal to `libxmp`'s player, not exposed as a standalone
unpacker binary), so the "delegate to a trusted decoder" move (see
`standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`)
took the form of porting `depack_p4x()`'s C source directly into
TypeScript (`tools/shared/amiga-player4x.ts`) rather than reimplementing
the format from a written spec. This is a stronger position than deriving
the byte grammar from scratch (the reference source is real, tested,
production code — not prose to transcribe), but it inherits the classic
goto-heavy-C-port trap: preserve the *exact* loop/branch structure rather
than "cleaning it up," per
`decompressor-port-loop-condition-iteration-shift.md`. One technique that
sidesteps that trap by construction, used successfully here: translate a C
`for(;;) { ...; if (cond) continue; ...; }`-shaped loop into a plain
JavaScript/TypeScript `for` loop with the same `continue`/`break`
statements in the same positions, rather than manually flattening it into
a `while` loop — JS's `continue` on a `for` loop still runs the loop's own
increment/re-test, exactly like C's `goto`-based `continue` does, so the
translation is structurally faithful without having to hand-reason about
decrement-before-test ordering at every loop site. Verified via 3 layers
against all 10 real files: 0 exceptions decoding every file to a
structurally well-formed module (in-range song length/sample count),
byte-exact re-encoded-file-size self-consistency (`1084 +
patternBytes + sampleBytes`), and a quantitative RMS + lag-1
sample-autocorrelation "real audio vs. decode-bug" check (29/30 samples
strongly self-correlated, the one exception plausibly a percussive/noise
instrument rather than a bug).

Confirmed on FFV (SNES, `ceres` project): `MapSpriteGfx`/
`VehicleGfx`/`WorldSpriteGfx` (overworld/vehicle field sprites) had zero
xrefs anywhere in `everything8215/ff5`'s ~37K-line `field-main.asm` outside
their own `gfx-main.asm` declarations — but grepping that same file for the
loader-name pattern `SpriteGfx`/`ObjGfx`/`ChrGfx` immediately surfaced
`TfrPartyGfx`, a real, previously-unlinked routine that resolves the
player's field-sprite state through two genuine pointer tables
(`_c01e02`, `VehicleGfxPtrs`) — real progress from a negative grep, not a
dead end. (The tile-arrangement inside those pointed-to blocks was still
left open that session — the lesson is about *finding the consumer code*,
not a guarantee the whole format falls out once you do.)
