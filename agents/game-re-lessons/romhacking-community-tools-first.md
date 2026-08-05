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
