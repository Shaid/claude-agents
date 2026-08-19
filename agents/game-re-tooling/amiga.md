# Tooling — Amiga (68k, HUNK, ADF/HDF, amiberry)

`Read` this when working on an Amiga target. Covers static disassembly (IRA),
radare2's HUNK limitations, Ghidra's HUNK loader, disk-image tools, the
hardware-reference lookup, and amiberry's operational gotchas once access
has been granted.

## Ghidra

A working HUNK loader **is** installed — `ghidra-amiga` (author "Bartman/Abyss",
builds on lab313ru's `ghidra_amiga_ldr` plus WHDLoad support), at
`~/.config/ghidra/ghidra_12.1.2_PUBLIC/Extensions/ghidra-amiga/`. (That's the
real per-user extensions path this Ghidra build resolves to — not the legacy
`~/.ghidra/.ghidra_12.1.2_PUBLIC/` most other Ghidra documentation assumes;
see `game-re-tooling/ghidra-loaders.md` for why.) It ships Amiga NDK 3.9
datatypes for accurate struct typing and its own `ghidra_scripts/`
(`ApplyRegBase.java` for custom hardware register overlays, `CopperList.java`
for Copper-list analysis, `ExportFunctionsHeadless.java`). Confirmed working
via real prior sessions — a Black Crypt project exists at
`~/Development/ghidra-projects/blackcrypt`. Reach for it over IRA/radare2
when you specifically want a decompiler or the NDK's typed structs; IRA
remains better for the refine-and-repeat `.cnf` workflow below, and radare2
for quick interactive byte-pattern work. Own this tool's Amiga usage from
the `amiga-disasm` agent, not `ghidra-disasm` — the latter doesn't carry the
small-data/`A4`/hunk-offset context Ghidra's raw output needs interpreting
against.

## Static disassembly

- **`Skill: ira-disasm`** — static 68k disassembly: label-based search,
  annotated `.asm` navigation, reassembly verification. **Use IRA for Amiga
  HUNK executables** — radare2 does not parse HUNK natively (it shows 0xFF
  garbage); the `radare2-amiga` skill documents the workarounds when you do
  need r2 on Amiga code. IRA's `-preproc` auto-detect pass is unreliable in
  *both* directions depending on binary size/shape — check which failure
  mode you're in before trusting either its output or the fix below. **Large
  hand-optimized binary:** `-preproc` can classify almost none of it as code
  (one 645KB Frontier: Elite II executable: ~40 tiny islands total) — a
  linear capstone/`-preproc` scan finding zero callers for a known routine
  usually means this, not that the caller uses exotic dispatch. Fix:
  hand-add an explicit `CODE $start - $end` covering the whole containing
  hunk to the `.cnf` and re-run with `-config`; this alone turned an
  "unresolved caller" into a confirmed instruction-level call graph
  (confirmed a second time on a 351KB Wizardry 6 executable: ~1.5% ->
  99.47% declared-code coverage in one edit). A `.cnf` left at its raw,
  under-covering `-preproc` output doesn't error or look broken — it can
  sit committed and trusted as a search surface for multiple sessions
  before anyone checks its actual coverage; see
  `committed-ira-asm-silent-coverage-gap.md` for the diagnostic to run
  before trusting an existing `.asm`'s grep results. To
  target the range, derive each hunk's address delta (`IRA_addr =
  file_offset + (SECSTRT_n_addr - hunk_n_file_data_start)`, both sides read
  straight off the hunk header parse) and use it to predict where an
  already-known file offset should land — then confirm the clean
  disassembly's label sits exactly there. **Small single-CODE-hunk
  executable (a bootstrap/loader stub, tens of KB):** `-preproc` can
  overcorrect the *other* way, classifying almost the *whole* hunk as data
  (a 15KB Jungle Strike `JStrike` loader: `-preproc` found ~32 bytes of code
  total). Skip `-preproc` here — IRA's plain default pass (no flag) treats
  the whole hunk as code, falling back to `DC.W` only where a byte pattern
  genuinely fails to decode, which turned this same file into a usable
  multi-thousand-line disassembly. Rule of thumb: default pass first on
  anything single-hunk-sized; reach for `-preproc` on bigger, more
  heterogeneous binaries. **`LAB_XXXX` labels are not always addresses:**
  `-LABEL=0` (default) numbers labels by branch-target *discovery order*, not
  address — confirmed by finding label values that are impossible real 68k
  addresses (odd byte offsets). Only `-LABEL=1` emits real hex addresses.
  Before assuming a committed `.asm`'s labels are addresses (e.g. to
  cross-reference against a second disassembly of the same binary that *does*
  use real addresses, like a capstone dump), test one known function: if its
  label value doesn't match a real address you can independently confirm
  (a DATA-hunk offset it touches, a literal constant), it's index-mode.
  **Fix:** regenerate with the identical flags (same `.cnf`/no-`.cnf`,
  same `-COMPAT`, no `-CONFIG`/`-PREPROC` difference) plus `-LABEL=1` — this
  reproduces the *identical* instruction stream (confirmed line-for-line
  identical body content between the two runs), just with real addresses
  as labels, which then line up with a real-address-based disassembly from
  another tool. To translate any single address between the two committed
  files from there: take ~6-8 instructions from the address-labeled
  regenerate at the target address as a fingerprint (strip label/BASEREG-name
  text, which can legitimately differ between runs, but keep raw `-N(A4)`
  displacements) and grep the original index-labeled file for the same
  instruction text — the nearest preceding label is the answer. See
  `cross-disassembly-fingerprint-false-positive.md` before trusting a match.
- **A raw (`-binary`) flat image with runtime-populated dispatch tables
  defeats single-entry `-preproc` recursive descent even when the binary is
  neither hand-optimized-all-code nor a tiny bootstrap stub.** This is a
  third failure mode distinct from the two above: `-preproc` from just the
  program's real entry point (`-entry=0` on a decompressed/decrypted flat
  image) can find only a handful of small code islands (17 out of an
  eventual ~30 confirmed routines on a 358KB Carrier Command image) because
  several real call chains only exist as a runtime-constructed jump table
  (an entity-type dispatch table populated at load time, not stored as
  literal pointers in the file) — recursive descent has no static edge to
  follow across that gap, no matter how the binary is shaped. Don't try to
  fix `-preproc` itself here (whole-hunk `CODE` ranges would swallow the
  large amount of genuine non-code data — sprite/model tables, palettes —
  that this failure mode's binaries also tend to have, unlike the
  all-code-hunk case). Instead: **seed the `.cnf` with individual `CODE`
  ranges at every routine address already confirmed by other means across
  this and prior sessions** — live-capture register reads, spot `r2`
  disassembly, doc citations — even loosely-bounded ones (guess a generous
  end address; a range that runs a bit into trailing data just degrades to
  garbage instructions past the real end, it doesn't corrupt anything
  earlier). Re-run with `-config` (not `-preproc`, which would discard the
  hand additions and re-guess). This reliably decodes straight-line code the
  original single-entry pass never reached, including code *past* an
  already-confirmed routine's own end inside the same enclosing function —
  see `confirmed-subroutine-does-not-bound-its-caller.md` for what that
  found on Carrier Command (a full BSP-tree traversal, two sessions'
  disassembly windows away).
- **A fourth `-preproc` failure mode: one real function inside an
  otherwise-normal, large multi-hunk binary gets misclassified as `DC.L`
  data, with no `.cnf` even emitted to hand-fix.** Distinct from the three
  shapes above (whole-binary-as-data, whole-hunk-as-data, jump-table gap) —
  here the binary as a whole disassembles fine, just not this one function.
  Confirmed on a 240-hunk, 193KB Phantasie I (Amiga) executable: the
  function containing `GetStat`/`SetStat` (a plain, unremarkable
  range-check/arithmetic routine in raw hunk 99) came out as solid `DC.L`
  declarations under `-preproc`. Don't fight IRA's config syntax to fix one
  function in an otherwise-good disassembly — extract that hunk's raw CODE
  payload standalone (via the confirmed file-offset math, same as the
  overlay-executable technique below) and disassemble it with
  `r2 -a m68k -b 32 -q -n` instead. To keep the resolved symbol names IRA
  already worked out elsewhere in the binary, build an address→label
  lookup table from IRA's own already-resolved `DC.L LAB_xxxx`/
  `SECSTRT_xxxx` relocation comments in its `.asm` output, and substitute
  those into the r2 disassembly's absolute operands by hand — cheaper than
  re-deriving symbol names from scratch and keeps the two disassemblies
  cross-referenceable.
- **`Skill: radare2-amiga`** + the radare2 MCP tools (load via ToolSearch,
  `mcp__radare2__*`) — interactive disassembly, xrefs, hex dumps, byte-pattern
  search. radare2 is multi-architecture: it's the primary tool for DOS/x86 and
  other non-HUNK targets.
- **Overlay-linked executables** (`blink OVERLAY`-style: a resident root
  hunk set, then one or more additional `HUNK_HEADER`/`HUNK_CODE`/`HUNK_END`
  segments separated by `HUNK_BREAK`, each loaded on demand) defeat both
  the naive "skip RELOC32/SYMBOL/END" hand-rolled parser pattern above
  (which typically `break`s or throws at the first `HUNK_BREAK`, by design,
  not by bug — confirmed on Wings' (Cinemaware) main executable, 7 hunks
  across 5 physical load segments) **and** IRA itself (`ira -info`/
  `-preproc`/plain pass all fail outright on a second embedded
  `HUNK_HEADER`: `-info` partially recovers the root hunks but decodes the
  overlay table as garbage, full disassembly exits 1 with `Hunk...:0x3f3
  not supported`). Fix: use `amitools.binfmt.hunk.HunkReader` (Python;
  `reader.read_file(path)` then `reader.hunks`) to get every hunk's exact
  file offset/size including overlay segments — it handles
  `HUNK_OVERLAY`/`HUNK_BREAK` correctly where both the quick hand-rolled
  parser and IRA don't — then extract each CODE/DATA hunk's raw payload
  bytes standalone (via those confirmed offsets) and disassemble each with
  `ira -binary` instead of feeding IRA the original hunk-wrapped file.
  Don't burn time hand-constructing a synthetic single/multi-hunk
  `HUNK_HEADER` wrapper around an extracted payload to get IRA's small-data
  (`SECSTRT`/`A4`) symbolic labelling either — even a structurally-correct
  minimal header (byte-identical in shape to a real single-hunk file that
  disassembles fine) reliably triggers `ReadSymbol error (can not read
  size of symbol's name)` on `-info`/full disassembly; root cause not
  identified, not worth chasing. **This isn't limited to hand-constructed
  headers** — the identical error also fires on a byte-exact slice of a
  genuinely real, naturally-occurring single-hunk blob (e.g. a raw NDOS
  track-image region that happens to contain a well-formed `HUNK_HEADER`/
  `HUNK_CODE`/`HUNK_END` sequence, sliced verbatim with zero bytes altered —
  confirmed on Midwinter, Amiga). Don't treat a `ReadSymbol` failure as a
  signal your extraction is wrong; go straight to the same fix either way.
  Resolve `A4`-relative small-data
  displacements by formula instead (`A4 = DATA_hunk_start + 0x7FFE`,
  confirmed once per binary via a `HUNK_ABSRELOC32` entry whose
  pre-relocation stored value is exactly `0x7FFE`) and read the flat
  `-binary` disassembly's real addresses directly (`-label=1`).
- **Normalize decimal vs. hex `A4` displacements before concluding "new
  global".** IRA emits A4-relative displacements in **decimal**
  (`-18340(A4)`), while project docs and probe scripts routinely cite the
  same global in hex (`-0x47A4(a4)`). The two spellings never grep-match
  each other, so a global that a prior session fully identified can look
  brand-new (a Wizardry 6 session re-derived `-18340(A4)`'s role from
  scratch — it was the already-documented `-0x47A4` current-level global).
  Before investigating any `-N(A4)` reference, convert it to hex and grep
  the docs/scripts for both forms.

## Parsing HUNK yourself

If you write or reuse a hunk parser (to pull a DATA hunk out, or to read the
`HUNK_SYMBOL` block Method §2 tells you to look for first), it **must skip
`HUNK_SYMBOL` (`0x3F0`) and `HUNK_DEBUG` (`0x3F1`)** in the same
between-hunks loop that skips `HUNK_RELOC32` (`0x3EC`) and `HUNK_END`
(`0x3F2`). A parser that only knows RELOC32/END walks off the rails on the
first symbol block and then misreads everything after it — the symptom is a
misleading "DATA hunk not found" style failure on exactly the
symbol-bearing binaries you most want (a real bug found in middilgard's
shared `parseHunks()`, which threw on `ExcalII` and Spirit's `Excal`).

Layouts: `HUNK_SYMBOL` is a repeated `{ u32 nameLengthInLongwords; name
bytes (padded); u32 value }` terminated by a zero length. `HUNK_DEBUG` is a
`u32` length in longwords followed by that many longwords of opaque payload.

**Prefer `amitools.binfmt.hunk.HunkReader` (Python) over a fresh hand-rolled
parser** when you just need correct hunk boundaries and a `HUNK_SYMBOL`
table, not a from-scratch learning exercise — `reader.read_file(path)` then
`reader.hunks` (list of dicts with `type_name`/`data_file_offset`/`size`/
`symbols`) gets CODE/DATA/BSS file offsets and every symbol's `(name, hunk-
relative offset)` right on the first try. A quick hand-rolled parser is easy
to get subtly wrong on exactly the RELOC32/SYMBOL/END boundary this section
warns about — one such parser misread a `HUNK_SYMBOL` block as more
RELOC32 data, silently desyncing the whole rest of the stream while still
returning plausible-looking (wrong) hunk sizes for the first hunk, purely
by coincidence. `amitools` already handles every trap on this page.

> **But do NOT use `HunkReader` for a relocation-table census — its
> `reloc` field silently loses entries.** A `HUNK_ABSRELOC32` block is a
> *sequence* of `{count, targetHunk, count × offset}` groups, and nothing
> stops the same `targetHunk` appearing in many groups within one block.
> `HunkReader` flattens each block into a `{targetHunk: [offsets]}`
> **dict**, so every repeat of a target hunk **overwrites** the previous
> group's list. Confirmed on nicodemus/Phantasie I's `game` (240 hunks):
> hunk 77's single reloc block has 57 groups but only 19 distinct target
> hunks — target hunk 236 alone appears in **27** separate groups, of
> which `HunkReader` keeps one. Whole-file damage: **203 of 6,389
> relocation entries (3.2%), across 15 hunks, silently missing** — and
> the loss is invisible, since the surviving entries are all correct.
> This cost a full escalation: a whole-binary "who calls `_LoadRGB4`"
> scan returned **zero callers** for a program that obviously sets
> palettes, purely because the one `jsr _LoadRGB4` slot lived in a
> dropped group. Any question of the form "enumerate every caller of X"
> or "every reference into region Y" needs its own ~60-line raw walker
> that keeps relocs as a **flat list of `(offset, targetHunk)` pairs**;
> use `HunkReader` for hunk boundaries and `HUNK_SYMBOL` only. Cheap
> self-check either way: compare your total reloc count against a raw
> re-walk before trusting any negative result.

**Mask `& 0x3FFFFFFF` on BOTH the header's size-table longwords AND every
in-stream hunk-type tag longword**, not just one or the other. Some
linkers (Desert Strike Amiga's, confirmed) embed the `MEMF_CHIP`/
`MEMF_FAST` flag bits directly in the in-stream tag too (e.g. raw tag
`0x800003E9` = flags(CHIP) + `HUNK_CODE`), not only in the header's size
table — a parser that only masks one location works on single-hunk files
(where the distinction rarely surfaces) but throws "unhandled tag" on real
multi-hunk modules (CODE+DATA+BSS, 2-6 hunks). A minimal from-scratch
parser covering exactly this — locate CODE/DATA/BSS hunk boundaries and
file offsets, skip RELOC32/SYMBOL/DEBUG structurally without decoding their
contents, no relocation applied — is cheap to write when you just need to
find a chunk's DATA hunk to scan its bytes, not disassemble code:
`tools/shared/amiga-hunk.ts` in `~/Development/strike` is a committed,
reusable reference (parallel to middilgard's `parseHunks()` mentioned
above, which instead targets the symbol/debug-skip bug).

**Resolving a `JSR`/`PEA`/absolute-long operand's real target hunk, from
`HUNK_RELOC32` alone, without a runtime loader.** A raw disassembly of an
unrelocated multi-hunk binary shows every absolute-long operand (`JSR
$103A.L`, `PEA $166DF.L`, ...) as its **pre-relocation stored value** —
almost always the target's own **hunk-relative** offset, not a real
address — so two different call sites showing the same small number
(`0x0`, entry-point-of-some-hunk) tell you nothing about which hunk
either one actually targets. Fix: extend your hunk parser to record,
per CODE/DATA hunk, the full `HUNK_RELOC32` list as `(hunkRelativeOffset
→ targetHunkIndex)` pairs (the format is `repeat{ count n; targetHunk;
n × offset }`, terminated by `n==0`); then for any `JSR $XXXX.L`
instruction at file offset `F` inside hunk `H`, look up
`H.reloc[(F - H.dataStart) + 2]` (`+2` skips the 2-byte opcode to reach
the operand's own position) to get the real target hunk index, and add
that hunk's own `dataStart` to `XXXX` for the target's real file offset.
This is byte-exact and needs no emulator — confirmed resolving 7+ call
targets inside a single 5.8 KB function this way (nicodemus/Phantasie I,
`game`), definitively separating a genuine LCG-PRNG call site from an
unrelated call whose return value turned out to be dead (clobbered by
the very next instruction's own call before anything read it) — a cheap,
decisive way to rule out an ambiguous "candidate call site" without
fully reverse-engineering the callee: check liveness of its return value
first.

**Same technique, reversed: enumerate every caller of an already-known
function.** Given a target function's own file offset (already
disassembled/confirmed), scan **every** hunk's `HUNK_RELOC32` list for
entries whose target hunk matches the target's containing hunk *and*
whose pre-relocation stored value at that location equals the target's
hunk-relative offset — every hit is a real, byte-exact call site,
independent of which hunk it lives in. This turns "does anything call
`X`, and from where" from a guess into an exhaustive, decidable search
with no linear-disassembly xref-scan risk (see
`linear-disasm-desyncs-through-inline-data.md`). Confirmed on the same
`game` binary: a whole-binary scan for callers of `GetStat`/`SetStat`
(file offsets `0x116EA`/`0x11710`) found **exactly two** cross-hunk call
sites in the entire executable, both inside one unrelated utility
function — a decisive, exhaustive negative that settled "does the
character-sheet display routine call `GetStat`" (it doesn't) in one pass,
instead of an inconclusive linear-disassembly search that could only ever
report "found none in the code I looked at."

**Finding code xrefs to a data string when `HUNK_RELOC32` finds nothing
at all.** A position-independent, single-large-CODE-hunk binary (common
for a late-era, non-overlay-linked game) can reference nearby data via
**PC-relative** `PEA`/`LEA` addressing (`d16(PC)` mode, opcode `0x487A`
for `PEA d16(PC)`) instead of `HUNK_RELOC32`-patched absolute longs —
confirmed on a 3-hunk, 137 KB CODE-hunk Amiga binary (nicodemus/
Phantasie III) where a reloc-table lookup for 9 known string offsets
found **zero** matches. In that shape, brute-force the xref instead:
for every word-aligned position `p` in the CODE hunk, test whether
`p + s16(word_at(p)) == targetHunkRelativeOffset` (the PC-relative
encoding's own effective-address rule — displacement relative to the
extension word's own address); every real hit found this way had exactly
one match, with the 2 bytes just before `p` decoding as `0x487A` (`PEA
d16(PC)`) confirming it wasn't a coincidental match. Cheap (one pass over
the hunk, no disassembly needed for the search itself) and decisive where
the relocation-table approach is structurally blind.

**This isn't a contradiction of the `HUNK_RELOC32` technique above — it's
a different addressing shape, and checking which one applies first saves
the brute-force scan.** The "9 known string offsets, zero reloc32 matches"
result was for *direct* inline `PEA d16(PC)` references — individual code
sites embedding a string address themselves. A string reached instead
through an **indirection table** (an array of longword offsets that a
single generic "get string N" routine dereferences) is a different case:
the *table itself* lives in `DATA` and typically **is** `HUNK_RELOC32`-
patched even in a binary where individual call sites use PC-relative
addressing for everything else — because the table's own entries are
genuine cross-hunk absolute pointers, not PC-relative code operands.
Confirmed on the same 3-hunk Phantasie III binary this pattern was
originally found in: a still-undocumented race-name string block's
hunk-0-relative offset, searched for via the "reversed" `HUNK_RELOC32`
technique above (scan every hunk for a stored longword equal to the
string's known hunk-relative offset), found exactly one hit — inside the
`DATA` hunk, at what turned out to be one slot of an 18-entry pointer
array feeding a shared string-lookup table used for spell/race/class/
status text throughout the UI. Try the reloc32 reverse-lookup on the
target string's own offset first (cheap, one search); only fall back to
the PC-relative brute-force scan once that comes back empty, since an
empty reloc32 result only rules out "referenced via a relocated pointer
table," not "referenced at all."

## Disk images and hardware reference

- **`amitools`** (`xdftool`, `rdbtool`) — read/list/extract AmigaDOS floppy
  (ADF) and hard-disk (HDF) images without booting anything; the cheap first
  move for "is this a real filesystem" (Method §1) before assuming a raw
  blob. Only reads OFS/FFS (`DosType` `DOS\0`-`DOS\3`) — a PFS3/SFS HDF
  fails `xdftool open`/`list` with "Invalid Boot Block" even though it's a
  valid image; `rdbtool ... show` reveals the real per-partition `DosType`
  so you know upfront whether `xdftool` can help.
- **openground MCP, `amigadocs` library** — authoritative Amiga HRM/RKRM
  text: chipset registers (blitter, copper, DMA), LVOs, struct layouts, disk
  formats. `search_documents_tool` to find the section, `get_full_content_tool`
  to read it in full. A cheap lookup, not an emulator boot — check it before
  guessing at hardware semantics, and before reaching for amiberry to answer
  something a manual lookup would settle.

## Original game manuals — a naming oracle

`~/Development/amigadocs/game-manuals/` holds a large local archive of scanned
Amiga game manuals, named
`Title (Year)(Publisher)[tags][id].pdf` — with language markers where they
exist (`(DE)`, `(FR)`, `(US)`, `(M3)`/`(M4)` for multi-language editions) and
tags like `[budget]`, `[compilation ...]`, `[construction kit]`. Several games
have more than one entry (different releases, or a separate clue book).

**Why it matters:** a manual is often the only ground truth for *names* — items,
spells, monsters, characters, stats — that exist nowhere in the shipped data.
Black Crypt's monster names came from exactly this route (manual + clue book +
ending text), and `Black Crypt - Manual & Clue Book (en).pdf` is in here.
Check for the target's manual **before** concluding a name table doesn't exist,
and before inventing labels.

**Two practical traps:**

- **Most are image-only scans, not text.** Roughly two in five carry embedded
  text; the rest are pure JPEG page images. The cheap test is whether the file
  contains `/Font` — no `/Font` means nothing to grep, and a text search will
  return silence that looks like "the name isn't in the manual" when in fact
  nothing was ever searched.
- **No OCR tooling is installed** (no `pdftotext`, `tesseract` or `ocrmypdf`),
  so for scans, *read the PDF pages directly* — the `Read` tool takes a `pages`
  range and renders them, which is usually faster than setting up OCR for the
  two or three pages that actually carry the table you want. Manuals put
  item/spell/creature lists in appendices, so skim the contents page first
  rather than paging from the front.

The archive is grown periodically, so absence today is not proof; re-check if a
game was missing on an earlier pass.


## Static recompilation (native-port stretch goal)

See the "Recompilation landscape" table in `game-re.md` — `docs/amiga-recomp.md`
in `seer` is the platform's entry there.

## Hand-written 68k opcode byte-pattern censuses — verify the encoding first

A raw byte-pattern scan across a CODE hunk (no disassembler in the loop) is
a recurring, cheap technique for exhaustive write/read censuses of one
specific global (see `negative-from-addressing-root-not-shapes.md`'s
"does a hidden Nth case exist" worked example) — but a hand-recalled opcode
word is easy to get wrong in a way that produces a silent **false
negative** (zero hits, mistaken for "this instruction form doesn't occur")
rather than a crash. Confirmed wrong once: `clr.w $XXXX.l` (absolute-long
addressing) hand-recalled as `0x42B9` is **wrong** — the real encoding,
checked against actual PhantasieIII binary bytes, is `0x4279` (clr, size
bits for word, mode 111/register 001 = absolute long). Before trusting a
zero-hit result from a hand-written census, verify the opcode word against
one real, already-disassembled instance of that exact instruction+addressing-
mode combination in the target binary (or an authoritative 68k opcode
table) rather than recalling it from memory — the mistake is invisible
until a positive-control hit you expected to find doesn't show up.

## amiberry — operational detail (permission gate is in `game-re.md`)

Once granted, still keep
  usage narrow (one specific question, get in and out) — see the cost traps
  below and `amiberry-live-capture-workflow.md` in the pitfalls index for
  the operational gotchas once you do have permission. Two cost traps:
  WHDLoad quickstart boot (`--autoload`, `launch_whdload`) can SIGSEGV-loop
  in the JIT recompiler during Kickstart boot regardless of model/ROM/
  `cachesize=0` — the same crash signature (`comp_catchfault`, out-of-range
  fault addresses, after repeated `hdf_close_target` log lines) recurring
  across *unrelated* games/configs means it's an environment-level bug, not
  a per-game tuning problem: stop adjusting CPU/cachesize and boot manually
  via a prebuilt frontend HDF instead; and the IPC socket can silently
  attach to another concurrent amiberry session on the host — check
  `check_process_alive`'s PID after every launch.

## Offline `.uss` savestate analysis (no running emulator needed)

When a user supplies pre-made UAE-family (WinUAE/FS-UAE/Amiberry) `.uss`
savestates instead of granting live amiberry access, `@seer-project/amiga`'s
`uss.ts` (`loadSavestate`/`scanChunks`/`findChunk`/`inflateChunk`) parses the
chunk stream without launching anything — see its module docstring for the
format. Two things worth knowing beyond that doc:

- **Recovering a Zorro III fast-RAM chunk's real base address**: don't
  assume a conventional default. The savestate's `EXPB` (autoconfig board)
  chunks are `ConfigDev`-shaped — locate the board's ASCII name string
  (e.g. `"Z3Fast"`) inside the chunk payload and read the base/size
  longwords immediately preceding/following it; the size should match the
  chunk's own inflated length exactly, which is a free cross-check that
  you found the right board entry. Chip RAM (`CRAM`) is simpler — its base
  is always `$000000`, and its inflated length tells you the configured
  chip RAM size directly.
- **Recovering a hunk's live runtime load address from a savestate**: take
  a 32-64-byte window from a few different offsets across the executable's
  own raw hunk-payload bytes (avoiding windows that straddle a
  `HUNK_RELOC32`-patched longword, which will differ between file and
  memory) and search for it inside the inflated `CRAM`/`ZRAM` buffers — a
  match's buffer offset (plus the region's base address) is the hunk's
  runtime base. Confirmed cheap and decisive across 3 separate savestates
  from the same session (Wings) with 0 deviation outside relocation slots.
- **The `"CPU "` chunk (note the trailing space in the 4-byte tag — see
  `uss-chunk-name-trailing-space.md`) is not a simple flat 68k register
  struct on at least some Amiberry builds/CPU models.** One observed
  instance was 22,764 bytes — the region past a small header looked, under
  a cross-savestate diff, like a cycle-exact CPU core's internal
  prefetch/bus-cycle trace buffer (raw opcode-shaped bytes interleaved with
  addresses in a region unrelated to any loaded code hunk), not registers.
  A resync-by-plausibility scan (every word-aligned `u32` tested against
  known hunk address ranges) and a full-memory pointer census for a
  stack-like cluster of return addresses both came back empty for a live
  PC. No authoritative field layout was recovered this way — treat "read
  the live PC out of a `.uss` file's `CPU ` chunk" as an open problem, not
  a working technique, until a future session cracks the real layout
  (candidate approach: find and read actual WinUAE/Amiberry C++ savestate
  source rather than resync-by-plausibility alone).
