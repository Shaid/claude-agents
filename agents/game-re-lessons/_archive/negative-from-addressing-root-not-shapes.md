# "I searched and found nothing" is a weak negative; "I enumerated every access root" is a strong one

**When it bites:** you're about to write up "no code reads this field / no
consumer exists / this item has no effect", and the evidence is that one or more
searches returned zero hits. **Also fires in the opposite direction, for a
POSITIVE identity claim rather than a negative:** two doc citations (or a doc
citation and a fresh disassembly) name the identical literal RAM address from
two different code regions, on an architecture where many separately-compiled
units (per-level overlays, TOC-slot-loaded modules, bank-switched code) share
one fixed load address — the shared hex value alone is shape-based evidence
("looks like the same thing") and needs the same root check ("which unit was
actually resident, and which function actually computed this pointer") before
it can be trusted as identity rather than address reuse.

There are two fundamentally different ways to build a negative, and they have
very different reliability:

- **Shape-based:** enumerate instruction/operand patterns that *would* access
  the thing, search for each, find none. This is only ever as complete as your
  enumeration of shapes. Every encoding you didn't think of is a silent hole,
  and you cannot tell from the result whether the hole exists. It fails
  *quietly* and produces confident wrong answers.
- **Root-based:** enumerate every way an address for the thing can be *formed*
  in the first place, then follow each root forward to a finite, classified set
  of accesses. This is countable. If the roots are complete, the access set is
  complete, and a negative over it is real.

**First establish how many roots the binary actually has — one compiler
convention does not mean one addressing mode.** The chain below is written
for a pure SAS/C small-data binary where A4 is the only base, but real
binaries mix. Phantasie III (Amiga, `nicodemus`) reaches its library bases
through A4 (`GfxBase` at `-0x56D2(A4)`, so `A4 = DATA + 0x7FFE`) while
reaching its *own* globals by absolute-long-plus-relocation (`lea $2BCE.l`)
in the same functions. Either census alone leaves a silent hole:
A4-relative accesses carry **no relocation entry**, so a reloc-table walk
is structurally blind to them, and an A4-displacement scan says nothing
about relocated absolute operands. A load-bearing "written but never read"
verdict there — two runtime palette slots with exactly one reference each
in the whole executable, their own store — only became decidable after
running *both*: a flat-list walk of all 6,838 relocation entries, **and** a
separate word-scan of the CODE hunk for each slot's own A4 displacement
(`addr - 0x7FFE`), which returned zero at any alignment. Cheap tell that
you're in a mixed binary: disassemble any one function and look for both
`(d16,A4)` operands and reloc-patched absolute longs in the same body.

For SAS/C small-data 68k the root chain is:

1. No absolute relocations point into the table (check the hunk's reloc block) —
   so nothing reaches it by absolute address.
2. Enumerate every `(d16,A4)` displacement that resolves into the table's byte
   range — a complete, finite root set, because A4 is the only base.
3. Pointer-escape analysis: show the derived pointers never leave their stack
   frame (no store to a global, no pass to a function that retains it).
4. What remains is a finite, individually classified set of access instructions.

Worked contrast, both from War in Middle Earth (`middilgard` project):

- **Strong.** "Are there character-death game-end conditions?" A raw scan of the
  entire CODE hunk for the two ending-stub displacements returned **exactly two
  hits each** — so the binary has exactly four game-end trigger sites, all four
  decoded, none reading a character death. The conclusion doesn't rest on a
  pattern search at all: a death ending cannot exist because there is nowhere
  for it to dispatch to. That negative is airtight by construction.
- **Weak, and it broke.** "Does the Elven cloak do anything?" A census
  enumerating operand shapes around the item field returned nothing, and was
  written up as "confirmed inert". It was wrong — the real test used an operand
  shape the census never covered (see
  `bitfield-spans-multiple-addressable-bytes.md`). The sibling coil-of-rope
  negative, reached the same way, then had to be re-argued from the addressing
  root before it could be trusted — and this time it held.
- **Weak by construction, not just by omission.** Carrier Command (Amiga): a
  literal-address `BSR`/`JSR $TARGET` byte-pattern scan is inherently
  shape-based — it can only ever match a *direct* call encoding. A candidate
  routine (`$CB5C`) had 12 confirmed direct callers, none of them the one call
  site in question (`$B742`'s model loader) — read as disqualifying evidence
  and the routine was "ruled out" as that call's target. But `$B742` calls its
  target via `JSR (A2)`, a **register-indirect** call with `A2` loaded from
  data at runtime (`MOVEA.L (A0)+,A2` immediately before the `JSR`). No literal
  target address exists in that instruction at all — a scan for `BSR`/`JSR
  $CB5C` is *structurally incapable* of ever matching it, no matter how
  exhaustive. The 12-caller census was true and complete for direct calls, and
  said nothing whatsoever about the one indirect call that mattered; "ruled
  out" had to be walked back to "undecided." The root-based fix here is to
  enumerate where the *register* (`A2`) gets its value — trace every write to
  it, including ones sourced from data/memory, not just literal-immediate
  `LEA`/`MOVEA.L #imm`. A pure byte-pattern scan for `JSR $addr` forms cannot
  do this; it needs either a data-flow trace back from the `JSR (An)` site, or
  a live capture of the register at the call.

**The same shape recurs at architecture scale, not just one call site — and
when tracing the register forward is impractical, trace the target address
backward instead.** Knights of the Round (CPS1, `kolbold` project): a
fully-traced, real game-(re)initialization routine (`$f4a`) had zero direct
`bsr`/`bra`/`jsr`/`jmp` callers anywhere across a full 1MB program ROM —
every encoding checked, a genuinely exhaustive shape-based scan, correctly
returning nothing (same as Carrier Command's 12-caller census above: true
and complete for direct calls, silent on the one indirect call that
mattered). Tracing a specific register's writes forward wasn't practical
here — the eventual `jmp (a1)` sits inside one generic, reusable dispatcher
shared by every task in the game, not a one-off call site with a nearby
`MOVEA.L`. The fix went the other direction instead: a literal 32-bit scan
for the routine's own address as *data* (not as an instruction operand)
found it written at exactly 2 sites, both a recognizable 3-instruction
"register this function as callback N" idiom. Searching for every OTHER call
to that same registration syscall then enumerated the full mechanism (a
16-slot cooperative task scheduler with a `TRAP`-vectored register-task
syscall, RAM-resident Task Control Blocks, and a shared `jmp (a1)` dispatcher
reading each task's function pointer fresh from its own TCB) in one pass —
77 real registrations found project-wide from that one pivot. See
`engine-implements-cooperative-task-kernel.md` for the full technique and
what to look for (TRAP-as-syscall convention, a fixed-stride RAM array with
a function-pointer field, a per-slot private-stack-pointer table). **General
shape:** when tracing an indirect register's writes forward is impractical
(the call site is generic/shared, not specific to your target), try tracing
the target *address* backward instead — search for it as a data value, not
an instruction shape, and use whatever idiom writes it there to find every
sibling instance of the same mechanism at once.

**An enumerated inventory used to build a negative ("these N callers don't
match any of the M known pools/functions/slots, so this must be something
else") is itself a root-based census, and inherits the same completeness
requirement — validate the inventory's own completeness before trusting it
as a filter.** D&D: Tower of Doom (CPS2, `kolbold`): a prior pass found 8
real call sites to what turned out to be the correct shared monster
HP-init routine, checked each against a previously-built object-pool
inventory (5 pools, found via a byte-exact loop-signature match), saw none
of the 8 callers fell inside any of those 5 pools' routine-address ranges,
and used that absence to *dismiss* the lead as "a different, not-yet-
identified pool" — a plausible-sounding negative that was actually wrong.
The inventory was incomplete: the byte-exact signature silently rejected 4
of the game's real 9 pools (their loop bodies had a few extra bookkeeping
instructions the strict pattern didn't allow for), and the pool holding
the dismissed lead's true target was one of the 4 missing ones. The
generalizable fix is a structural **closure/chain check**, not more
scanning: object pools of this shape sit contiguously in work RAM, so a
`base + slots*stride == nextPool.base` chain across the whole claimed
inventory is a cheap, strong completeness oracle — run over the (wrong)
5-pool inventory it would have shown an unexplained gap immediately
(`0x25c8`..`0x43c8`, exactly where the missing character pool lived),
rather than silently accepting 5 pools as "the pools." This generalizes
past object pools specifically: any "list of N things" used as a filter
(a function-table population, a directory-entry count, a symbol-table
size) needs its own independent completeness check — a chain, a checksum,
a cross-count from an unrelated source — before it's trustworthy enough to
rule something *out*. This is a different failure from every other example
in this file (which are about search *shape* completeness); here the
search technique itself (a signature-based enumeration) was sound for what
it matched, the miss was that its match criterion was too strict and
nobody checked whether the resulting count was actually complete.

**The single cheapest way to test any zero-hit negative: run the identical
search against a POSITIVE CONTROL you already know is live.** If the control
also returns zero, the search has no discriminating power and the negative is
worthless — you learn this in one command, before writing anything up. Epic
(Ocean, Amiga, `hunter` project): a filename pool was written up across two
sessions as "possibly dead content," on the strength of three structurally
distinct zero-hit scans (LEA/PEA; then every addressing mode plus branch
targets; then the whole `HUNK_ABSRELOC32` table). Re-running all five scan
shapes against a control pool of **nine `*_MAP` filenames of files that
definitely ship and definitely load** returned the *identical* zero result,
invalidating three sessions of negatives at once. The real cause was that the
executable holds two separately-linked images and the referencing pointers live
in the other one's address space (`hunk − 0xCAB6`) — see
`two-linked-images-one-hunk-module-relative-addresses.md`. Pick a control that
is live for the *same reason* the target would be (here: another filename read
by the same loader), and pick a negative control too where you can — a third
pool that genuinely *is* reached by PC-relative `LEA` scored 4 hits, proving
the scan worked when the reference was in the address space it searched.

**Related: "this name is never referenced" is a weak signal in any corpus where
most assets are loaded by computed or table-driven names.** In the same binary,
94 of the game's shipped data files — every `PAUL*.IGD`, `SPACE3/5/7/8`,
`threedee.bin`, every `.ANI`/`.LBM` — have no literal filename anywhere in the
executable at all. Before treating "no literal reference to this filename"
as evidence about a *file*, measure what fraction of the corpus's known-live
files have a literal name in the binary; if it's low, the test is measuring the
engine's naming convention, not the file's liveness.

**Fix:** when a negative is load-bearing — it closes a question, contradicts
prior documentation, or lets you stop looking — do not ship it shape-based.
Convert it to root-based, or state plainly in the docs that it is a search that
came up empty rather than a proof of absence. Those are different claims and
should never be written as the same one. And whichever you ship, run a positive
control first: it is one command and it is the difference between "I searched
and found nothing" and "a search that finds known-live instances found nothing
here."

**A root-based census can still be incomplete if it only greps the array's
*unindexed* base constant, missing every literal-index access compiled to a
different constant.** War in Middle Earth (`middilgard`): a shared,
FRML-id-indexed pointer array lives at base `SECSTRT_0-10674(A4)`, written
once per id as `arr[id] := handle` (`base + 4×id`). A census concluded "only
one routine in the whole binary references this array" by grepping for the
literal string `10674` — genuinely root-based in spirit (searching for the
array's own address, not an instruction shape), but incomplete, because
every *other* consumer that indexes the array with a **literal** id has that
arithmetic folded by the assembler into its own distinct constant
(`-10674 + 4×id`, e.g. `-10650` for id 6, `-10642` for id 8) with no
occurrence of `10674` anywhere in the instruction. The true second consumer
(four such accesses, for four different literal ids) was invisible to the
one-string grep and the negative was wrong. **Fix:** once a base and stride
are known, the addressing-root enumeration is not complete until you also
compute and search for `base ± stride×n` for every plausible index `n` in
the domain (here, the small set of known valid ids) — not just the bare base
string. This is the same "enumerate every root" discipline as the `(d16,A4)`
displacement method above, just applied one level deeper: the "root" for an
array is not one constant, it's a *family* of constants parameterized by
index, and a grep for only the family's zero-offset member is shape-based
in disguise.

The **mirror** of that hole bites when you search for one *entry's* address
instead of the array's: an entry reached only by a runtime index off the
array base (`lea $BASE.l,a0; move.l (a0,d0.l),d1`) has its own address appear
nowhere in any instruction, so a whole-binary search for that 4-byte value
finds zero hits even though the entry is live. Confirmed on Phantasie III
(Amiga, `nicodemus` project): two filename-template strings were about to be
written up as "dead strings, unreferenced in this build" on exactly that
evidence — the search would have caught any `movea.l $slot.l,a0`, and
correctly found none, because the real consumer indexes a contiguous
filename-pointer array from its base with a runtime resource-type id. Rule of
thumb covering both directions: **a pointer/data table has exactly one
address guaranteed to appear literally in code — its base.** Zero hits on an
individual entry is the *expected* result for an indexed table, not evidence
of anything; resolve the base first, then work out the index domain.

**A negative can also be an artifact of the search *tool*, not just its
shape — re-run a load-bearing zero-hit result with an independent, simpler
method before trusting it.** Hunter (Amiga, `hunter` project): a prior
session documented "no code in `game_decrypted.bin` reads back the OB-format
header's `+0xc` longword" as a confirmed negative, evidenced by `r2 /x`
byte-pattern searches for the field's cached scratch-memory displacement
finding nothing beyond the one known write. A later session re-ran the
identical question with a plain Python `bytes.find()` over the raw file and
found a real second hit immediately — a genuine consumer routine
(`move.l 0x157c(a5),d6 ; beq ; bsr`) that the disassembler's own search
feature had somehow missed, root cause not identified (search-scope option,
an indexing gap, or an operator error in the invocation — moot; the
disassembler's search is not infallible). The fix isn't "root-based vs.
shape-based" here — the search *was* root-based (searching for the one
displacement value at the addressing root, not enumerable instruction
shapes) — it's that even a well-designed search is only as trustworthy as
the tool executing it. Before writing up a load-bearing "confirmed inert,
zero consumers" from a single tool's zero-hit result, re-run the identical
byte-level question with a second, independent, dumber method (a raw
`bytes.find()`/`grep -a` over the file beats trusting one disassembler's
search implementation) — it's minutes of work and it overturned a
"confirmed" verdict a prior session had closed with a full closure
argument.

**The same root-vs-shape distinction settles "does a hidden Nth case exist"
questions about a value's whole domain, not just "does a consumer exist" —
census every *write* to the controlling variable, not just its reads.**
Phantasie III (Amiga, `nicodemus` project): a domain expert recalled "three,
maybe four" non-overworld maps (three were already found and decoded —
two castle interiors plus a Netherworld) and asked whether a fourth was
real or a fuzzy memory. The map-switch routine's own dispatch logic
(`and.w #3,d0` on the active-map-id global) would *structurally* also
accept map ids the game was never observed to use (3, 5, 6, 7 — anything
sharing the same low 2 bits as the known ids), so tracing the dispatch arms
alone could only ever answer "what does the code do *if* asked for id N",
not "is the game ever asked for id N". The decisive check was root-based on
the *write* side instead: a raw byte-pattern census of every
`move.w #imm,ABS.L`/`clr.w ABS.L` instruction writing to that one global
across the whole CODE hunk, enumerating **every value the binary ever
assigns to it, anywhere** — not inferring the domain from what one dispatch
path happens to test for. The census found writes at seven distinct call
sites and confirmed the assigned-value set was exactly `{0, 1, 2, 4}`, never
3 or anything else — a complete, mechanically verifiable negative on "does
a fourth map id ever get requested," settling a question no amount of
dispatch-arm tracing could close by itself. General shape: when the
question is "what is the whole domain of values X ever takes" rather than
"does anything read X," the addressing root to enumerate is every
**write** site to X's storage location, not every read/branch/consumer —
reads only tell you what the code *could* do with a value, writes tell you
what values actually occur.

**The same "structurally cannot exist" root cause applies to *content*
searches, not just consumer searches — and a noted-but-unexplained anomaly
can be the resolving fact, not a distraction from it.** Phantasie III
(Amiga, `nicodemus` project): two local attempts to find the file location
of several `HUNK_RELOC32`-resolved lookup-table addresses both failed
(a literal base-offset guess, and a brute-force monotonic-value scan) —
both were, without realizing it, searching for file bytes that don't
exist, because the target hunk's `HUNK_DATA` block stored fewer bytes than
its `HUNK_HEADER`-declared allocation (a SAS/C merged `data+bss` hunk; see
`hunk-data-shorter-than-declared-is-merged-bss.md`). The escalation brief
that finally cracked it had flagged the size mismatch as a peripheral
"worth double-checking" anomaly alongside the real question ("what base do
I add") — the fix was recognizing the anomaly *was* the answer (no base
exists; the references are runtime BSS variables, not stored content), not
a side detail to verify away before returning to the main search.

**A root-based census can be exhaustive and still wrong, because the root
itself is the wrong one — the fix is switching to a different,
independently-discoverable anchor, not enumerating harder.** Valkyrie
Profile (PSX, `valkyrie` project): six direct passes hunting for the
consumer of a 2D sprite-animation sub-record's per-part fields all rooted
the search at one specific object field, `obj+0xc8` — the field the game's
own animation-state setters (`SetAnimation`/`SetFrame`) write a "current
sub-record" pointer into. Every one of those passes was root-based in the
correct sense: stride-based access-pattern scans, offset-signature scans,
and finally a full taint census of *every* `lw *, 0xc8(rX)` site in the
overlay (24 of them, all non-stack). All six came back negative, and the
last one was airtight by the file's own standard — a complete, mechanically
enumerated set of every access to that exact address. The root was simply
wrong: the renderer never reads `obj+0xc8` at all. The object's per-frame
update copies that pointer into a *separate* per-frame draw-list entry, and
the renderer reads it from there instead — one hop removed from every root
the six passes anchored on. The fix that worked was not enumerating more
shapes at the same root, but abandoning it for a different, independently
verifiable anchor with much lower fan-out: the record-block's own registry
pointer (`obj+0xcc`, only 7 xrefs overlay-wide) combined with a
content-agnostic instruction-pair signature for the format's own
self-length chain-advance (`lhu rX,0(rB); addu rB,rB,rX`, 6 xrefs). That
combination led directly to the engine's real `SetAnimation`/`SetFrame`
implementations and, from there, to the actual renderer. **General shape:
when a root-based census is complete and still negative, and the item is
known to exist (a format is confirmed, a mechanism is known to run), treat
"the root is wrong" as a live hypothesis before concluding the search
technique failed — look for a second, independently-discoverable anchor
(a registry/table pointer with a small literal xref count, an allocation
size, a format-defining instruction pattern that doesn't depend on which
field holds the pointer) and re-root the search there.** This is a
distinct failure mode from every other example in this file: those show
incomplete root enumeration or an untrustworthy tool; this one shows a
*correctly and completely enumerated* root that was nonetheless the wrong
starting point.

**A load-bearing byte value can be structurally absent from every
instruction because the code computes it via a runtime table lookup one
hop away from where the search was aimed — the fix is tracing the id's own
consumer, not widening the constant search.** Chaos Legion (PS2, `flower`
project): "find the audio region's track LBAs" first tried searching
`SLUS_206.95`'s EE text for the LBAs as absolute `u32` constants, as
relative sector offsets, and as `lui`-built immediates — all root-based in
spirit (searching for the value itself, not an instruction shape) but all
came back empty, because the driver never materializes an LBA as an
immediate anywhere: `SdrXagStandby(tbl_idx)` only enqueues an index: the
real resolution happens one function later, in the IOP driver's own
`XagCdRead` → `CdFileOpen(fno)`, which uses `fno` as a direct index into a
*second, previously unknown* 8-byte-stride `(size, LBA)` table at a
completely different data address. No amount of searching for the LBA
*value* could find this, because the LBA is data at a computed address,
not a literal operand in any instruction — the addressing root here is
"trace the id-taking call's own body to find what table it indexes",
not "search for the resulting value". General shape: when a resource-load
call takes only a small integer id and a value search for what that id
*should* resolve to comes back empty, suspect a hidden runtime table
lookup inside the id's consumer before concluding the value isn't derivable
from static analysis at all.

**"N independently-shaped techniques all agree" is not independent evidence
if the techniques share an underlying implementation primitive — and this
applies even to a `re-oracle`/`re-codebreaker` escalation's own follow-up
techniques, not just a base session's.** Valkyrie Profile (PSX, `valkyrie`
project): a producer search for `obj+0xe8` bit 10 was escalated after 3
differently-named static techniques (a literal census, a biased-base
census, a regionType-18/22 native-module scan) all returned zero; the
escalation ran 4 MORE differently-named techniques (a biased-STORE census,
a combined/any-mask SET census, a branch-following forward trace, full
store provenance) and all 4 *also* returned zero, closing it as a settled
negative "confirmed by technique-diverse agreement." The negative was
wrong: a real producer existed, sitting in the delay slot of an
unconditional `j` (`mips-delay-slot-instruction-always-executes.md`) — and
every one of those 7 techniques across both sessions, despite having
different names and surface shapes, shared the identical underlying
forward-scan primitive that stops advancing the instant it sees a
`j`/`jr`/`jal` opcode, one instruction before the delay slot that always
executes. A technique built by *adapting* an existing scan (extending it to
stores, widening its mask logic, following its branches) inherits every
control-flow assumption baked into the original — it is a variation on one
method, not a second method, no matter how different the resulting hit list
looks. The tell that finally cracked it: re-checking the doc's OWN
already-published prose for the affected function (found via
`doc-self-cross-reference-before-fresh-disassembly.md`) named the real
producer directly, with no census involved at all — an orthogonal
discovery *route*, not a sharper scan. **Fix:** before crediting a
multi-technique negative as "hardened," ask what each technique's actual
scanning primitive is, not just what its name or stated scope is — if two
or more share a common helper function, a common "stop at the first
branch/call" rule, or a common bias-tracking core, they are one technique
wearing several names, and the true independent-technique count is lower
than it looks. The cheapest real diversifier is a technique with a
*structurally different failure mode* — direct disassembly of the region a
census claims is clean, or (as here) a plain prose/doc search that never
touches code at all.

**A VM's own opcode family can have a computed-address addressing mode
where the target never appears as a literal in any instruction word at
all — six genuinely different shape-based censuses are structurally
incapable of finding it, and the fix is shape-matching the *consuming
routine*, not enumerating more instruction encodings.** Valkyrie Profile
(PSX, `valkyrie` project): a story flag's setter resisted a literal-
immediate MIPS census (compiled code), a `jal SetFlag`-argument census, a
`STOREBIT`/`LOADBIT` scene-script operand census, a direct byte-poke
census, a room-module scan, and an engine-capability check — six
differently-shaped searches, each exhaustive over its own population, all
correctly returning zero. The write was a scene-script bytecode opcode
(`STI` in bit width) whose **address field was entirely zero**: that mode
computes the target bit address from the VM's accumulator register at
run time (`bitBlock + (ACC>>3)`, bit `ACC&7`), and `ACC` was built a few
instructions earlier from a `PUSHI`-pushed argument, never appearing as a
literal anywhere near the store. No word-value scan, byte-poke scan, or
operand-shape scan — however many variations — could ever find this,
because the thing being searched for (the flag id, as a literal at the
store site) genuinely does not exist in the instruction stream. The fix
that worked (via `re-oracle`) was root-based in a different sense than
usual: instead of enumerating addressing roots for the *value*, it
shape-matched the **consuming library routine itself** (a fixed ~40-word
bytecode sequence: `ENTER` → test-bit-0 → conditional test-bit-1 →
set-bit-1 → clear-bit-0 → `RET`, recognizable by control shape alone,
independent of which flag id it's called with) and then found every
`PUSHI K; CALL <that routine>` site corpus-wide — which named the flag
*and* found the other 29 flags the same routine sets, in one pass.
**General shape:** when a value you're hunting is provably absent from
every literal-word search (confirm this — don't just widen the search
further), suspect a computed/indirect addressing mode in whatever VM or
custom ALU is doing the store, and pivot from "search for the value" to
"shape-match the routine that would consume the value as a runtime
argument, then enumerate its callers" — the argument is a literal at the
*call site* even when the store it feeds into never contains one.

**The same discipline applied to a POSITIVE claim, not a negative one: two
overlays sharing one fixed load address can make an address match look like
proof of shared identity, when it's really coincidental reuse.** Valkyrie
Profile (PSX, `valkyrie` project): while cross-referencing a scene-script
opcode's `*(0x8007f1e4)` companion-record array against the project's own
docs (the standard `doc-self-cross-reference-before-fresh-disassembly.md`
technique), a battle-overlay doc comment surfaced reading `charTable =
lookupResource(...) = *(0x8007f1e4)` — the identical literal address, which
briefly looked like strong evidence that the field-overlay's 25-slot
companion array *was* the party's `charTable`. This would have been a major,
wrong, cross-subsystem claim. The shape (matching hex value) was
shape-based; the root wasn't checked yet. Checking the root — which function
actually computed each address, and which TOC-slot overlay is resident when
that function runs — refuted it immediately: `charTable` is independently
confirmed elsewhere (`save-system.md`) to be `*(0x8004B87C)`, resolved by
`loadActorStats` inside a completely different overlay (TOC slot 1491) than
the field overlay (TOC slot 2292) where the companion array's own opcodes
run. `0x8007f1e4` is simply reused RAM across two overlays that are never
resident at the same time, addressing two unrelated structures. **Fix:**
before trusting an address match between two doc citations (or a citation
and a fresh disassembly) as evidence of shared identity, identify which
overlay/module each citation's own code belongs to and confirm they're
either the same overlay or genuinely simultaneously resident — a bare hex
match across two different resident-code contexts is exactly as unreliable
as a shape-based zero-hit negative, and for the identical reason: it never
checked how the address was actually formed.

**A root-based census is only as complete as its own FILE scope — a sibling
overlay/module sharing the same runtime address space can hold a root your
single-file scan never sees.** Follow-up round on the same Valkyrie Profile
companion array above: an earlier pass had built a real root-based census
(every literal `lui/lw` construction of the array's base, forward-tainted
through register chains) and found no writer for one field — but that
census only ever disassembled the ONE overlay file (TOC slot 2292) the
investigation started in. The field's true "no writer exists" verdict only
became trustworthy after widening the identical root-search to **every**
cached code artifact the project had (73 files: every top-level overlay,
every menu screen's own native sub-module, several dungeon-room modules) —
which turned up exactly one more root, in a second file ("the field
overlay's paired module," a separate TOC slot sharing the field overlay's
nominal base address) that the single-file census had structurally never
looked at. That second root turned out not to be a writer either, but
finding and ruling it out is what converted "no writer found in this
overlay" into a real, corpus-wide negative — the two are not the same
claim, and only the second one is safe to write up as closed. **Fix:**
before writing up a root-based negative for a global/struct accessed via a
literal base address, enumerate every file/overlay that could plausibly
share that runtime address space (paired modules, per-room native
sub-blocks, sibling overlays at the same nominal base) and re-run the exact
same root search across all of them — not just the one file the
investigation happened to start disassembling. A stronger, free variant of
the same check: search for the address-construction idiom at the *address-
space* level (any `lui reg,0xHIWORD` at all touching the global's hi-word,
not just the one 16-bit low-offset you care about) across a whole
candidate-subsystem's worth of overlays (e.g. "does the entire equip/menu
screen family ever construct ANY address in this hi-word range") — a clean
zero there rules out every field that subsystem could touch, not just the
one you started with.

**File-scope widening also has to reach INSIDE an already-cataloged
container's own nested/chained compressed sub-blocks, not just add more
sibling files.** Valkyrie Profile (PSX, `valkyrie`), round 192: a "no
caller found" negative for a specific function address had been built from
a literal `jal <target>` scan over "every cached file" — but those files
were each decoded only at their OWN top-level compressed-block header;
several of the project's own containers bundle additional code/data as
*nested* compressed sub-blocks reachable only by scanning for the
container's magic bytes again past offset 0 (the same shape
`compressed-container-members-invisible-to-magic-scan.md` warns about for
asset-coverage claims, here biting a call-target search instead). Widening
to a magic-byte walk of every nested sub-block inside every cataloged
container (not just adding more whole files to the file list), combined
with the two already-known indirect-target roots this file documents above
(the Knights-of-the-Round "search for the target address as literal DATA"
technique, and the immediately-preceding "search for the `lui`+`addiu`/`ori`
address-construction idiom") turned a 109-file, one-mechanism negative into
one spanning the entire decompressible disc under three call/reference
mechanisms — a materially stronger (though still not closing) negative,
found by combining lessons this file already taught rather than by
discovering a new one. **Fix:** when widening a root-based census's file
scope, also ask whether any already-cataloged file is itself a container
with more compressed content past its own top-level header — a
directory/chain walk or a plain magic-byte re-scan of each file's raw
bytes past offset 0 is what actually completes the corpus, not just a
longer file list.
