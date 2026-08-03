# A "0 matches, position-dependent" verdict on VM bytecode is usually a missed endian swap, not a real cross-platform barrier

**When it bites:** a known-content byte search for a data table's cross-platform
equivalent (Method §4's "known content as search oracle" /
`cross-platform-decode-oracles.md`) comes back with zero matches at every
chunk granularity you try, for a table you have strong independent reason to
believe exists on the target platform too — especially when the table in
question is VM bytecode, a scripted behavior table, or anything else
resembling compiled/linked code rather than a flat lookup table, and a
sibling doc's disassembly-derived description ("raw code-label addresses",
"embedded address operands") makes "structurally impossible across
platforms" sound like the correct conclusion.

Flat data tables (palettes, remap tables, terrain/type tables, item stat
blocks) are usually genuinely byte-identical across an Amiga (68k, big-endian,
32-bit flat addressing) and a DOS/x86 (little-endian, 16-bit segmented) build
of the same game, once any compression is stripped away — confirmed for
Vengeance of Excalibur's 20 remap tables and 2 terrain tables (0 mismatches
across 1,152 bytes) against DOS VGA's decompressed `game.exe`. A byte search
finding nothing for *this* kind of table is almost always a tooling problem
(wrong offset, still-compressed input) — see `renamed-magic-container.md` and
`cross-platform-decode-oracles.md`.

**A prior pass on this exact case (Vengeance's shared "FSME" entity-class
bytecode VM) concluded the format was genuinely unrecoverable this way — that
conclusion was wrong, and cost a full session to overturn.** The reasoning
at the time: Spirit's own `docs/spirit/amiga/bytecode-vm.md` documents the
class's 16-entry dispatch header as "IRA-generated local labels" (i.e. real
code addresses), and describes the `$64xx` "dispatch call" opcode as
recurring inline through the bytecode carrying "its own embedded address
operand" — so a byte search finding 0 matches at every granularity from 480
bytes down to 8 was read as proof the two platforms' builds literally cannot
share these bytes, the same way two independently-linked binaries never
share raw addresses. **The actual cause was much simpler and had nothing to
do with recompiled addresses**: the bytecode is a stream of **16-bit words**,
stored **big-endian on Amiga (native 68k) and little-endian on DOS VGA
(native x86)** — the exact same *sequence of word values* on both platforms,
just with each word's two bytes swapped. Re-running the identical
known-content search with every adjacent byte pair pre-swapped found **all
34 classes byte-exact and contiguous**, in the identical class order —
independently triple-confirmed by (1) the byte match itself, (2) a
`_prgm`-equivalent 34-entry far-pointer dispatch table on the DOS side
resolving to the same 34 offsets in the identical order as Amiga's own
`_prgm`, and (3) the existing opcode disassembler producing textually
identical output for both platforms' extractions.

The root mistake: a disassembler's own label-numbering scheme ("IRA-generated
local labels in the 0x64xx range") was read as proof the *stored on-disk
values* are absolute, per-build machine addresses. It wasn't checked directly
— the values just happened to visually resemble code-label-shaped numbers in
one disassembly. Whatever those `$64xx`-family values actually encode, they
are portable data, not addresses that differ per link.

**The fix: before accepting a "structurally cannot match" verdict for any
bytecode/word-stream format, try the search again with 16-bit words
byte-swapped** (a full per-word byte-pair swap across the whole candidate
region, then a fresh substring search for each already-confirmed source
block) — this is cheap (seconds) and must be exhausted before trusting a
disassembly-derived claim about "embedded addresses" as a reason cross-
platform matching is impossible. Only treat the "genuinely
position-dependent, needs a from-scratch interpreter trace" verdict as final
if the byte-swapped search *also* comes back empty, and even then, prefer
directly re-verifying the "raw address" claim against the suspect platform's
own bytes (e.g. checking whether the values form a strictly increasing or
otherwise position-correlated sequence) over accepting a sibling doc's
prose at face value — see `romhacking-community-tools-first.md`'s "don't
trust a reference project's prose without re-deriving it" principle, which
applies just as much to your own project's prior docs as to a third party's.
