# Verification techniques — confirming a decode without full disassembly

`Read` this when Method §4's cheap oracles aren't available: the routines that
would confirm a struct are too expensive to disassemble, or you need to validate
a table/struct wholesale rather than spot-checking instances.

The verification *bar* itself stays in `game-re.md` §4 — this file is the
catalogue of techniques for meeting it.

When full disassembly of the routines that would confirm a struct is too
expensive (huge, mostly-undetected hunks — see the IRA caveat above), a raw
byte-pattern census across the *whole* binary can still independently
confirm a structural fact without needing correct code/data classification
anywhere: e.g. searching for a specific-size stack alloc/dealloc instruction
pair (`LEA -N(A7),A7` ... `LEA N(A7),A7`) found 10 unrelated sites across 5
different hunks all using the *same* N — independent confirmation of a
record's byte size, sidestepping a stalled field-offset trace entirely
(FE2's `0x11E`-byte object record).

A table of large 32-bit immediate constants in code (e.g. a chain of
`ADDA.L #imm32,An` computing sub-buffer offsets) can be verified wholesale,
with zero tracing of what consumes the table, by cross-referencing every
constant against a corpus's *already independently confirmed* per-file
sizes (a `_triage.json`-style manifest built in an earlier phase). Dozens of
constants all landing on real files' exact byte counts, with no false
matches, is strong confirmation on its own — this is how Jungle Strike
AGA's per-mission "which files this level needs" resource manifest inside
`JS` was confirmed (~50 constants, zero false matches, cross-referencing 9
missions' worth of already-known `worldNmap`/`worldNblks`/`objectsN`/
`spritesN`/`missionNstat` sizes). The same trick validates a *newly
inferred* struct's field offsets for free: read a fixed relative offset
from every entry an existing, unrelated scanner already found (e.g. a
self-pointer search built for palette-pairing) and check it lands on one
consistent value corpus-wide — 179/179 records across two ROMs reading the
same expected command-field value confirmed a Genesis resource-descriptor's
layout this way (Strike project), cheaper and more convincing than
spot-checking 1-2 hand-decoded instances.

For a candidate index/ID array (e.g. a suspected tile-index nametable), two
cheap mechanical checks catch a wrong candidate fast without waiting for a
future session: does its value range fit under *any* real corpus-confirmed
size ceiling (exceeding every known real object's count is disproof, not
just weak evidence), and does its unique-value distribution cluster
suspiciously regularly (e.g. every 256 apart) rather than scattering the
way real hand-placed indices would. Refuted a previously-flagged "concrete,
not yet cross-verified lead" this way in one pass instead of leaving it
open across sessions (Strike project, Jungle Strike Genesis).

**A decoded numeric table's own values can be the oracle**, with zero
disassembly, when they're round human-authored numbers in a domain-typical
shape: Wizardry 6 Amiga's `scenario.dbs` opens with 14 back-to-back tables
of 16 big-endian u32s, every value a round decimal (1000, 2000, 4000, 8000,
...) in a strictly increasing per-table sequence — the unmistakable shape of
a per-level XP-to-advance table — and the table *count* (14) was
independently checked against the game's real, externally-confirmed roster
of exactly 14 character classes, with the sequence breaking out of
round-number shape right at table index 14, confirming the exact boundary.
Round/human-typical values (prices, thresholds, percentages, counts) plus a
count that matches a known, checkable game fact (class/level/item counts
from a manual, wiki, or WebSearch) is a cheap, strong structural oracle —
reach for it on any small numeric table before assuming it needs
disassembly to identify.

**A non-round strictly-monotonic table can still be its own oracle, via a
recurrence check rather than roundness.** When values aren't human-typed
round numbers but the table is a plausible level/EXP/price-progression
curve, test whether consecutive entries satisfy `value[i+1] ≈
floor(value[i] * r)` for a small rational growth rate `r` (try ~1.05-1.15
first — real RPG level curves overwhelmingly land in that band), and allow
the rate to change once or twice across the table (a "regime shift" is
itself a normal design choice, e.g. slower growth after a level-cap
inflection point). Confirmed on Fire Emblem: Three Houses (`chimera`
project): a 98-entry `u16` EXP-to-next-level table (100, 110, 121, 133,
...) matched `floor(prev * 1.1)` **exactly** for the first 21 consecutive
values, then shifted to a visibly slower (~1.05x) regime for the remainder
— a shape that is effectively impossible to produce from 98 arbitrary
bytes by chance, and needed no external walkthrough or wiki lookup. Distinct
from the round-numbers case above: this test finds structure in a table
whose individual values look unremarkable, by checking the *relationship*
between neighbors instead of each value's own typicality.

**A localized/translated port's retained internal English strings can be a
Rosetta-stone oracle**, letting you locate *and* validate game-data tables
before you can read a word of the display language, and sometimes crack the
display-text encoding itself for free. Ports that share a source database
across regions often carry the original-language identifiers as
internal/debug strings even when the shipped game displays a different
language — check for this before assuming a translated release has nothing
readable. Wizardry 6's Japan-only SNES port displays Japanese but retains
plain-ASCII English class-rank titles (98 strings, 14 groups of 7) whose
group *count* and *order* matched — with zero deviation — a 14-class roster
already independently confirmed from the same game's Amiga port; the same
ROM's monster-name table paired each retained English name directly against
its localized-text counterpart (`[English name][translated name]` records
back to back), which both confirmed the table's existence *and* handed over
the transliteration/encoding scheme (half-width katakana, see
`game-re-tooling/snes.md`) for free — 102 pairs decoded clean, each one an
unambiguous, checkable transliteration of its English partner. Look for this
whenever a translated/localized release is otherwise opaque: grep for the
untranslated game's known terminology (class names, monster names, item
names) in the new release's raw strings, even though the game itself never
displays them.

**Finding undirected records in a maskless sprite bank via a padding-column
scan:** when a sprite format has no mask plane and instead keys transparency
on one backdrop colour index (common once you've confirmed it for one bank —
see `bitplane-layout-variants.md`'s family), new records elsewhere in the
same file can be found without any descriptor table by scanning a decoded
planar stream for a byte *column* that holds one constant value across every
row of *every* plane (implement with a per-plane cumulative-sum
sliding-window-all-true check, not nested Python loops — it's the difference
between seconds and hours over a multi-KB stream at a dozen candidate
widths). Run it two ways: strictly pinned to an already-confirmed backdrop
index first (near-zero false positives — this alone found 6 new UI records,
half a game's worth of previously-unclassified "BCSPEED" bytes, in Black
Crypt/crawl, 5 of them independently confirmed against a DOS port's *named*
catalog entries at 98.8-100% silhouette agreement and 2 against a live
screenshot); only fall back to a generalised "any single constant value per
plane" scan when the backdrop index isn't known in advance, and treat its
hits as leads, not confirmations — it also matched thousands of ordinary
detailed-image byte ranges in the same corpus and needs a stricter check or
an external oracle per hit before being trusted.

**Discriminating raw PCM audio from image or compressed data by profile
alone**, when a byte range's role is unknown and no marker/header points to
it: compare its Shannon entropy against the same file's already-confirmed
compressed streams (real 8-bit-signed PCM audio measured *higher* entropy,
6.9 bits/byte, than genuine RLE-compressed sprite data at 5.5 in the same
file — compressed image data is not always the densest thing in a
container), then check the signed-byte mean (near zero) and lag-1..10
autocorrelation: audio decays smoothly (0.49 down to 0.10 in one confirmed
case) the way a real waveform does, where compressed data reads near-zero at
every lag and bitplane image data has a different decay shape entirely. This
caught a second, previously mis-documented PCM sound bank in Black Crypt's
`bcdfa` (10 samples, confirmed byte-identical to a DOS port's sound archive
after an XOR 0x80 sign-convention flip) that an earlier pass had guessed was
a "raw movement/delta table" from eyeballing one short slice of it alone —
profile the *whole* candidate range before typing up what it is.

**A DMA/blitter transfer-size register the game's own code writes is a
free byte-exact oracle for a decompressor's output length**, on any
platform where graphics load via a hardware DMA engine (SNES, Genesis,
similar console-era hardware): once a resource's compressed-stream call
site is found (e.g. via the DMA-register byte-pattern census below), the
same code almost always writes the *decompressed* size into a transfer-
count register a few instructions after the decompression call and before
triggering the transfer — compare that register's literal/computed value
against your decoder's output length with zero disassembly of the
decompressor's internals required. Combine with "does the compressed
stream's end offset land exactly on an already-known boundary" (next
resource's start, or the decompressor routine's own entry point, packed
back-to-back with zero gap) for a second, independent byte-exact check from
the same trace. Cracked Urban Strike SNES's from-scratch tag-byte codec
this way, two ways per resource, with no other ground truth available (see
`game-re-corpora/strike.md`'s SNES section) — a **DMA-register byte-pattern
census** (search for the transfer-trigger opcode, e.g. absolute `STA
$420B`/MDMAEN on SNES, plus its accompanying size/source-address register
writes) is the cheap way to *find* these call sites across a whole ROM
without full disassembly in the first place. Remember a register can be
reached through more than one addressing mode (see
`narrow-opcode-form-census-false-negative.md`'s SNES addendum) — a census
restricted to one form will miss loaders that use another.

**Unprompted convergence between independently-dispatched parallel agents
is a cheap, strong corroboration signal in its own right.** When an
orchestrator dispatches multiple sub-agents on different TODO items in one
batch, each with a self-contained brief and no visibility into the others'
work, two agents landing on the *same* address/stride/slot-count while
chasing unrelated questions is evidence neither agent could have
manufactured by copying the other. Wizardry 6 Amiga: one agent tracing a
`.PIC` cel-list's runtime side tables and a second agent (independently)
tracing `scenario.dbs` section 8's file reader both arrived at the
identical `-0x3ae4(a4)`, 314-byte-stride, 64-slot resource cache from
opposite starting points — treated as strong confirmation of that
struct's shape without needing a third, separate oracle. Look for this
whenever a parallel-dispatch batch touches adjacent or overlapping parts
of the same binary; it costs nothing beyond noticing the address match
across the two reports, and it's a more reliable signal than either
agent's own self-reported confidence. **Second confirmed instance, same
project, later session:** one parallel-dispatched agent tracing
`pcfile.dbs`'s character-record fields independently flagged offsets
`+24/+26` and `+28/+30` as two current/max stat-bar pairs (rendered,
"HP/SP candidates, unconfirmed") purely from UI-display evidence (a bar
graph and a percentage widget); a second, concurrently-running
`re-codebreaker` escalation working the unrelated monster-catalog HP
question independently derived that the *same* two field pairs feed a
combat-participant struct's HP/stamina current-max fields (via a
disassembly cross-reference neither agent's brief mentioned to the
other) — upgrading both from rendered to confirmed with zero extra
tracing once the two reports were reconciled by the orchestrator. Worth
an explicit check at the end of any multi-agent batch: scan for cases
where one agent's "rendered, unconfirmed" candidate is exactly what
another agent's unrelated trace just confirmed by a different route.

**Cross-bit-depth pixel co-occurrence infers an unconfirmed palette from
an already-confirmed sibling.** When the exact same artwork ships at two
different bit depths (e.g. a 4bpp EGA screen with a confirmed
`PIC_PALETTE` and a 2bpp CGA sibling whose real hardware colors are
unknown), decode both at the same coordinate space and, for every
low-bit-depth index value, tally which high-bit-depth (already-known)
color co-occurs at the same pixel coordinates across the whole corpus (a
plain weighted mean or a mode/top-N tally both work). This gives an
empirical best fit before or alongside any disassembly, and is
particularly good at narrowing a small closed set of hardware-defined
candidates (confirmed a DOS CGA screen's palette family — cyan/magenta vs.
green/red/brown — by a wide quantitative margin this way) even when it
isn't fully decisive on a finer within-family distinction (e.g. low vs.
high intensity, where dithering/edge-pixel contamination narrows the
margin). Treat it as a fast corroborating cross-check alongside a harder
oracle (BIOS/driver disassembly — see `game-re-tooling/dos.md`'s CGA/EGA/
Tandy section) rather than a substitute for one when the finer
distinction matters.

**A decoded pointer/offset field can be its own oracle by matching where an
independent decode pass stopped.** When a format has a byte-offset field
pointing into a variable-length region you haven't traced the consumer of
(e.g. a per-record "script entry point" or "event pointer" offset) and a
*separate*, already-structurally-confirmed forward walk through the same
buffer (a fixed-shape header/table region) terminates at some byte offset
on its own bookkeeping, check whether any of the offset field's real values
equal that termination point exactly. If one does, that's strong,
zero-tracing confirmation both that the forward walk's own stop condition
is correct (nothing else would explain a real stored offset landing there)
and that the pointer field's semantic role is what you think it is (an
entry point into the region immediately following). Confirmed on EOB1's
`.INF` level-config format (`crawl` project): a decoded 30-entry
block-property-override table's `assignedObjects` field held the value
`719` for one record, and a completely independent byte-exact walk through
the earlier monster-spawn/decoration-list region of the same buffer (driven
by its own internal counts, no lookahead into the override table)
terminated at byte offset `719` — confirming in one step that the
"event script" bytecode region starts immediately after the decoration
list and that `assignedObjects` is a script-entry-point offset, without
tracing the bytecode VM at all. Cheap to check (compare a handful of
decoded field values against one already-known offset) and decisive when
it hits — look for this whenever a format has both an offset/pointer field
whose target region is unconfirmed and an independently-terminating
forward-walk boundary from unrelated bookkeeping in the same buffer.

**Content richness distinguishes "statically compiled" from "runtime-loaded
buffer" without tracing a single load instruction.** When a symbol table
(or offset-derivation method) hands you two same-shaped candidate tables in
an executable and it's unclear whether either is real static data or just
reserved space a loader fills in later, inspect the raw bytes at each
offset directly: a genuine runtime buffer sits zero-filled (or otherwise
uniformly patterned) in the executable itself, while statically-compiled
data is rich and varied at rest. Pair this with a cheap negative-oracle
check — byte-exact search for the candidate static table's own content
across every file that *would* have to contain it if the runtime-buffer
hypothesis were true (e.g. every per-level/per-episode save-shaped file the
game loads at runtime) — a clean zero-hit result across the whole set rules
the hypothesis out directly, rather than leaving it as an unconfirmed
assumption that gets repeated in docs across sessions. Confirmed on
Vengeance of Excalibur (middilgard project): a TODO item assumed terrain
factor/type tables were "likely also runtime EPISODE*.DAT buffers, like
entities/locations" by analogy — refuted in one pass by noting the
executable's own confirmed-runtime-buffer table (`_aForces`) reads as 5,208
zero bytes at rest, while the terrain tables at their own confirmed offsets
are rich, varied, domain-plausible values (movement-cost multiples of 5;
0x00-0x0e classification codes), and the terrain factor table's exact byte
sequence appears in none of the 7 save-shaped files it would have to be
loaded from if the runtime-buffer hypothesis were correct.

**An already-confirmed format's own reference/id fields can classify a
*different*, unrelated format's semantic role — not just validate the first
format's own id resolution.** When format A (already decoded) contains
fields that reference ids belonging to format B (still semantically
unclear, e.g. "what kind of sprite is this"), partitioning format B's whole
id space by "does format A reference this id" can be a free, code-backed
classifier for format B, even though nothing about format A's own spec
needed re-deriving to get it. Confirmed on Conan the Cimmerian (middilgard
project): `SCEN`'s `typeIndex 4/5` object entries (already fully traced from
disassembly in an earlier session) reference a 23-id subset of `ANIS32.RES`'s
101 `FRML` sprite-animation resources as in-scene decoration; cross-referencing
that already-decoded id list against the full `FRML` corpus split it cleanly
into "scene-placed decoration" (rendered inspection: 100% ambient fx like
torch flicker, zero overlap) vs. "not scene-placed" (combat/player sprites,
an entirely separate, still-untraced subsystem) — with no new tracing of
`SCEN` itself required. Look for this whenever a task asks "what kind of
thing is resource X" and a sibling, already-solved format in the same
project references a subset of the same id space.

**A per-resource "self-referential" geometric heuristic can propose a
labelled animation/state split when no code-level table is findable at
all** — useful as a last-resort, explicitly `hypothesis`-graded fallback,
not a substitute for a real trace. When a sprite-animation resource's frame
sequence visually splices multiple named states together (e.g. a walk loop
ending in a death collapse) but no engine code/data table assigning frame
ranges to states can be found (searched: direct resource-id immediate
loads, a data-table byte-value census, filename-string xrefs — all
inconclusive), compare each frame's own bounding-box dimensions against
*that same resource's own* max width/height (not a cross-resource
constant) rather than any absolute pixel threshold. A trailing frame run
that is both much shorter (e.g. ≤60% of the resource's own tallest frame)
and about as wide (e.g. ≥90% of the resource's own widest frame) as the
rest of the resource's frames is a computable proxy for "a standing figure
collapsed to lie on the ground." Confirmed on Conan the Cimmerian
(`ANIS32.RES` #56, #58, #87 all correctly flagged — visually a walk/attack
followed by a fall, with visible blood-red pixels in the flagged frames)
and correctly silent on two negative cases: a dissolve-into-particle-cloud
transformation that never goes short-and-wide (#63), and a degenerate 1×1
decode-artifact frame (#55). Known, honestly-recorded false negatives:
a slump that doesn't go fully flat (`ANIS32.RES` #89, just under the height
cutoff) and a colour/silhouette transformation with no bounding-box collapse
at all (`ANIM32.RES` #112) — a geometry-only rule can never catch the
latter class by construction. Grade every segment this produces
`confidence: 'hypothesis'`, never `'confirmed'` — it is a render-derived
proxy for an underlying mechanism (the game's own animation-state
selection) that was never actually located.

**A pointer-table format that resolves cleanly but under-counts against an
independently-known total is missing a second, same-format table nearby —
not evidence the format itself is wrong.** When a resource-pointer struct
(gfx/palette/index offsets packed into a fixed-size record) is confirmed
correct field-by-field (byte-exact against a handful of known instances)
but walking every record of the *one* table you found produces fewer
distinct resources than an independent oracle says should exist, look for
a second table using the identical record format adjacent in the address
space before doubting the struct layout itself — asset formats routinely
split "the same kind of pointer record" across two parallel tables for two
different actor classes (e.g. monsters vs. bosses/summons) that share one
graphics/palette pool. Confirmed on FFVI (SNES, `ceres` project): walking a
384-record `MonsterGfxProp` table (confirmed byte-exact on records 0-5)
found only 148 distinct graphics against a community manifest's
independently-known total of 176; a second, identically-shaped 32-record
table (`EsperGfxProp`) sitting immediately adjacent in ROM resolved the
other 28 (Espers, a separate battle-actor class sharing the same
graphics/palette/stencil storage) — walking both tables and deduplicating
landed on exactly 176, a byte-exact match. The tell that it's a
missing-table problem rather than a wrong-format problem: the resolved
records from the one table you have are all individually correct (their
pointers land on real, correctly-decoding data) — a wrong format would
produce garbage some fraction of the time, not a clean subset short of the
true total.

**Correlating an external name (from a string/asset scan) to an unnamed
data cluster: test "exclusively confined to," not "ever touches."** When
a literal name string exists in a corpus (a title-card texture, a credits
string, a level-select label) but the *event/UI* package it lives in isn't
the same package as the actual game-object cluster it names — so an
exact-package-string match fails — a same-broad-category heuristic (e.g.
"same chapter/level number") is the natural next idea but is usually
**too noisy to trust on its own**: ubiquitous clusters (a player
character, a constant companion, a shared prop/weapon pool) touch nearly
every category trivially, so "does this cluster ever appear under the
named entity's own chapter" returns dozens of false-candidate clusters.
The fix is to invert the test: does this cluster's **entire** membership
(every instance, not a sample) stay **exclusively confined** to that one
scope, with **zero** appearances anywhere else? A cluster that never
leaves one single scope is a structurally different, much rarer shape
than a shared/reused entity — and is exactly the shape a scope-specific
named entity's own dedicated data should have. Confirmed on Drakengard 3
(PS3, `flower` project, `docs/drakengard3/ps3/data-structure.md` §21):
of 7 boss names with a real title-card string but no exact-package match
to any of 124 character-identity clusters, checking every cluster's full
(untruncated) package membership against "confined entirely to this
boss's own chapter/sub-area token" cleanly separated 2 real hits (zero
cross-chapter appearances) from every rejected near-miss (which, without
exception, spanned 2-5 unrelated chapters — the generic-reused-entity
shape). Verify the *negative* side too, not just the positive: the
rejected candidates' actual cross-chapter spread is what proves this
technique discriminates rather than just being a looser version of the
already-rejected "same chapter" idea — if a "rejected" candidate turns
out to also be confined to one scope, the technique isn't actually
filtering anything.

**Cross-sample byte-divergence in fixed windows pins an unknown header/
struct boundary exactly, cheaper and more decisively than eyeballing render
quality.** Take 2-3 real samples of the same format that are the same total
length but carry genuinely different content (e.g. different characters'
portraits, not the same image twice), and compare them byte-for-byte in
small fixed windows (16 bytes is a convenient granularity) from offset 0.
Every window where all samples agree is template/header/constant data;
the first window where they diverge densely (not one stray differing byte,
but most of the window disagreeing) is where real per-sample content
starts — a hard, load-bearing boundary, not a fuzzy one. Confirmed twice in
one session on Valkyrie Profile 2 (PS2, `~/Development/valkyrie`): applied
independently to two structurally unrelated sample families of a "FIS"
texture format, both landed on exactly the same offset (256 bytes) — that
agreement across unrelated families is itself corroborating evidence the
boundary is a real structural fact of the format, not a coincidence of the
one sample pair tested. This discovers an *unknown* boundary from raw bytes
alone (no header field, no disassembly, no rendering needed yet) — stronger
than "decode looks clean at width W," which can't distinguish a genuinely
correct boundary from a wrong one that merely renders plausibly (see
`game-re-lessons/header-shape-ambiguous-pixel-encoding.md`).

**Two overlapping linear disassemblies of the same byte range that
reconverge byte-exactly downstream is real evidence for an intentional
alternate entry point, not proof one decode is simply wrong.** When a
confirmed JSR/BSR target doesn't land on an instruction boundary under
linear disassembly from the nearest known-good neighbor (see
`confirmed-call-target-off-instruction-boundary.md` — check the load base
first if this happens on 2+ targets in the same file), one real explanation
is a hand-optimized "two entry points share a tail" idiom: the main path
enters earlier and executes some setup, while the alternate path (the
suspicious target) enters mid-routine and skips that setup, consuming a
*different* number of bytes through the overlapping region before both
paths land on the identical next instruction. Test it directly: disassemble
fresh starting exactly at the anomalous target and compare against the
main path's own linear walk through the same byte range — if the two
decodes disagree on instruction boundaries through the overlap but agree
exactly (same address, same instruction) from some point onward, that
reconvergence is the signature of a real alternate entry point (the second
path is typically missing some register-initialization the first path did,
so the caller must pre-load those registers itself). Confirmed on Hunter
(Atari ST): a target flagged as "2 bytes into a 4-byte instruction" under
the main path's decode resolved as 2 clean `ORI.B` instructions (a
different byte count through the same 8-byte span) that reconverged
byte-exactly with the main path's own next instruction — versus a second,
superficially similar target in the same file where the fresh decode hit a
word that both radare2 and Capstone flagged as an outright illegal opcode
(no reconvergence via a valid alternate parse at all), which turned out to
be a completely different problem (a wrong load base, see the lesson file
above) rather than a real alternate entry point. The reconvergence test
cheaply distinguishes the two cases before spending effort on either.

**A candidate palette/CLUT can be confirmed non-visually by testing it
against the platform's own documented hardware convention, with a random-
baseline control.** If a GPU/hardware colour format has a known constraint
(e.g. the PS2 GS's alpha channel is documented as 0-0x80, with 0x80 meaning
fully opaque — not the PC-native 0-0xFF), count what fraction of a
candidate palette's alpha bytes violate that ceiling and compare against
what an arbitrary/wrong byte region would show. Confirmed on Valkyrie
Profile 2 (PS2): **0 of 25,664** real candidate-CLUT alpha bytes across the
whole corpus exceeded 0x80, while the same files' own pixel-index bytes
(a genuine near-uniform-random control drawn from the same files) exceeded
0x80 in 20.5% of cases, and an arbitrary byte stream would be expected
near 50% — a structural, quantified, non-visual confirmation this really is
a hardware CLUT using the documented alpha convention, obtained before any
image was rendered. The same "quantify, don't eyeball" approach also
settles competing unswizzle/permutation hypotheses for a palette-index
remap: score each candidate permutation by a cheap coherence metric (mean
absolute adjacent-pixel RGB delta, lower = smoother/more image-like) across
the whole corpus, not one sample. The documented-correct permutation (PS2
CSM1: swap palette-index bits 3 and 4) scored 26.5% better than stored
(unpermuted) order, while two plausible-looking alternative bit-swaps both
scored *worse* than doing nothing — proving the correct permutation is
uniquely so, not merely "a working guess" that happened to look fine on one
rendered example. **Independently re-confirmed on a second, unrelated PS2
title from a different developer** (Chaos Legion, Capcom, vs. Valkyrie
Profile 2's tri-Ace): a single-instance CLUT-only resource's alpha bytes
clustered at exactly {0, 0x80} (the same 0-0x80 GS convention), and the
standard PS2 CSM1 8-entry-block swizzle (a coarser block-level shuffle,
not the bit-3/4 swap above — PS2 CLUT storage has more than one documented
scrambling scheme depending on colour depth/mode) turned a choppy raw
palette render into clean, smooth per-row colour gradients — the same
"quantify/visualize before and after the documented unswizzle" pattern,
now confirmed across two unrelated codebases, evidence this is genuine
platform-wide GS convention rather than a coincidence of one game's tools.

**MPEG-PS concatenated-clip boundaries can be found from the container's
own embedded clock, with zero disassembly, when no explicit clip/count
table exists.** Every MPEG-2 `pack_header` (`00 00 01 BA`) carries a
33-bit System Clock Reference (SCR), a 90 kHz counter required to increase
monotonically *within one continuously-encoded stream*. A concatenation of
several independently-encoded clips (e.g. several FMV cutscenes packed
back-to-back into one raw region with no directory) shows the SCR **reset
to exactly 0** at each real clip boundary — a discrete, unambiguous signal
distinguishable from the much smaller (a few thousand ticks at most, never
revisiting exactly 0) non-monotonic jitter one continuous multiplexed
stream can show between its own interleaved audio/video packs. Confirmed
on Chaos Legion (PS2): decoding all 103,432 pack headers' SCR fields (with
all 4 required marker bits validated `1` on every one — 0 rejects, itself
confirming the bit-level parse is correct) and scanning for `SCR == 0`
resets found exactly 15 real boundaries (17 clips), with 5 additional
small-jitter negative deltas correctly *not* misread as boundaries since
none of them revisit exactly 0. Independent cross-check, not just the SCR
signal alone: every one of the 17 resulting clips starts its own fresh
MPEG `sequence_header_code` (`00 00 01 B3`) at the *identical* byte offset
(51) relative to its own first pack header — a coincidence a spurious
jitter-driven boundary would not reproduce 17/17 times. This generalizes
to any MPEG-PS (or similarly SCR-timestamped) concatenated-stream format
with no separate directory: check the embedded clock before assuming you
need a hand-built clip table or a full disassembly trace of the loader.

**A confirmed "facing B is facing A mirrored via hardware h-flip"
relationship self-verifies byte-exact, with no external oracle, by
comparing against a naive whole-image mirror.** When a sprite/animation
format has two directions/poses whose raw selector values are numerically
identical except for one flip-bit offset (e.g. `right_raw ==
left_raw + 0x40` for every step, confirmed directly from the selector
table's own values, not assumed), render both, independently mirror the
"unflipped" render pixel-by-pixel (reverse column order per row, a
one-line, decode-logic-free operation), and assert **zero** RGBA byte
differences against the "flipped" render. This is a strictly stronger
check than "looks like a mirror": it only passes if both (a) which tiles
the h-flip attribute applies to, and (b) the per-tile mirror math itself,
are simultaneously correct — a wrong tile-group split still produces a
plausible-*looking* image whenever the two groups happen to share the
same flip state on the tested sample, but fails this exact check the
moment a differently-grouped tile disagrees. Confirmed on FFVI (SNES,
`ceres` project): a right-facing standing sprite hit exactly 0/1536 RGBA
byte mismatches against a naive mirror of the left-facing render, across
all 15 tested objects — see
`game-re-lessons/tile-formation-table-not-raster-order.md`'s third
confirmed instance for how this also served as the deciding evidence
between two competing tile-group-split hypotheses.

**A shared reorder/formation template plus a per-instance declared byte
length shorter than the template's own max-index requirement predicts an
exact out-of-bounds read — confirm it by render instead of writing it off
as a bug.** When several same-family records share one tile-formation/
canvas reorder table (a fixed array of cell -> stored-tile-index mappings,
applied identically to every record) but one record's own declared content
is shorter than the highest index the shared table references, compute the
predicted overrun explicitly (`(maxIndex+1) * tileSize` vs. the record's
own declared byte length) *before* rendering, and check whether the
shortfall lands exactly on the start of the next record in address order —
if it does, the "overrun" is provably reading real, adjacent, structurally
sane data, not garbage, and the render should show a recognisable partial
blend of the current record's own content with the next record's colours/
shapes rather than noise. This turns an apparent edge-case anomaly into
positive, load-bearing evidence for both the addressing scheme and the
record boundary, rather than something to quietly work around. Confirmed
twice now, same general shape, two different games in the same corpus:
FFVI's Gestahl battle sprite (`tools/ffvi/battle-sprites.ts`, `ceres`
project) reads a shared 256-slot canvas table past its own 1,760-byte
blob into the next `MapSpriteGfx` object with no bounds check in the real
game code either; FFIV's Pig battle sprite (`tools/ffiv/battle-char-gfx.ts`,
same project, same session as the corroborating disassembly trace of
`ReloadCharGfx`) reads a shared 84-cell tile-formation table past its own
1,536-byte declared content, landing byte-exact on the very next
character's (Golbez's) declared start offset — and the rendered piglet
sprite visibly shows blue/gold Golbez-armour colour fragments blended into
its later action poses, exactly as predicted before the render was ever
generated. Treat this prediction-before-render step as free (it's just
arithmetic on already-known offsets/counts) and worth doing on *every*
shared-template format with variable per-instance content length, not just
as a post-hoc explanation once a render already looks visually "off."

**A narratively-explained blank/degenerate slot in an otherwise-dense
corpus is corroborating evidence for an index mapping, not noise to
explain away.** When a fully-decoded, verified corpus of per-index records
(a sprite atlas, a stat table, an item list) has exactly one entry that
renders empty/degenerate while every sibling entry is dense and legible,
check whether the specific index combination that's blank matches a real,
checkable fact about the game (a character who dies/leaves before a late-
game feature unlocks, an item that's cut content, a state that's
unreachable) before treating the gap as an extraction bug or coincidence.
If the domain fact and the blank slot line up, that's free, independent
confirmation of whatever index/id mapping produced the (row,column)
address of that slot — a wrong mapping would have no reason to make the
blank land exactly on the narratively-correct combination. Confirmed on
FFV (SNES, `ceres` project): a fully-rendered 110-sprite battle-character
atlas (5 characters x 22 jobs) has exactly one blank entry, and it's
`galuf` x `job20`; `job20` had already been mapped (via a separate code
citation) to the `JobName` table's "Mimic" entry, and Galuf is a real,
well-known FFV plot fact — he's permanently removed from the playable
party before the point in the story where the Mimic job becomes
available. The blank slot wasn't investigated as a decode failure (0
non-transparent pixels, structurally identical addressing to every other
slot) — it was recognised as the expected consequence of a correct
mapping, and documented as corroborating evidence for that mapping rather
than a caveat to explain away. Don't confuse this with
`reserved-slot-zero-shifts-extractor-index.md` (a *systematic* reserved
index across every record, causing an off-by-one) — this is a single,
domain-explained gap at one specific coordinate in an otherwise-populated
grid.

**A flat, unbranched byte-copy loop from ROM into a named WRAM struct
proves the struct's field offsets are identical to the ROM record's own
offsets — use the struct's real field-labelled consumers as offset
citations even when nothing ever indexes the ROM table by name directly.**
Many retro RPG loaders don't read a data-table field-by-field; they copy
the whole fixed-size record into a scratch/live struct in one pass (`lda
[ptr],Y / sta Struct,X`, incrementing both sides together, compared
against a literal byte count with no per-field branching), and only
*that* struct's fields get accessed by name elsewhere in the code. When
the copy loop is provably flat like this — no conditional field-skipping,
no reordering, same increment on both source and destination each
iteration — the destination struct's offset for field `F` **is** the
source ROM record's offset for `F`, by construction. This turns an
apparently-uncited ROM layout into a fully-cited one: find any real
instruction elsewhere that accesses the struct by its field label (e.g.
`lda MonsterStats::HP,X` or `lda RHWeapon::Properties,X`), and that's a
legitimate confirmation of the ROM record's own field offset, satisfying
the same "real lda/sta instruction, not prose" bar as a direct `lda
f:MonsterProp+8,X` would. Confirmed twice in the `ceres` project: FFVI's
`MagicProp` (an `mvn` block-move copies 14 bytes into a fixed WRAM
address before battle-effect code consumes fields there by offset) and
FFV's `MonsterProp`/`WeaponProp`/`ArmorProp` (three separate flat
byte-copy loops — `CopyMonsterStats`, `ApplyGear`'s `CopyOneItemData` —
each confirmed unbranched by reading the loop body itself, not assumed).
Before trusting this: actually read the copy loop's body end-to-end and
confirm there's no branch, mask, or reordering between source and
destination indices — a loop that skips/transforms even one field breaks
the offset-identity argument for every field after that point.

## Bind-pose inertness: proving a partially-resolved skin binding is harmless before animation exists

When exporting a skinned mesh (glTF `JOINTS_0`/`WEIGHTS_0`) whose per-vertex
bone-binding data only resolves for *some* vertices against the joint
palette you can build from the currently-decoded formats (a "partial
resolution rate" situation, `partial-resolution-rate-is-noise.md`'s
sibling case but for skin weights rather than an id field), and no baked
animation exists yet to actually pose the mesh, you don't have to treat the
unresolved fraction as an unverified gap. A skin's defining mathematical
property is that at the bind pose, `jointWorldMatrix_i * inverseBindMatrix_i
== identity` for **every joint `i` independently** — so *any* per-vertex
weighting across *any* subset of joints reproduces the exact authored
vertex position at rest, as long as each joint's own inverse-bind matrix and
its node's own bind-pose world transform are mutually consistent. This
means a vertex whose real bone binding didn't resolve (falls back to an
arbitrary/default joint) is provably harmless for a *static* render,
regardless of which joint it falls back to — the unresolved fraction only
becomes load-bearing once/if the mesh is actually posed away from bind.

Don't just assert this in prose — verify it directly with real matrix math,
the same rigor as any other ground-truth check: build a small unit test
that constructs two-plus synthetic (or real-sample) joints with non-trivial
rotation+translation, exercises both a resolved multi-bone-weighted vertex
and an unresolved/fallback-bound one, and checks
`jointWorldMatrix.multiply(inverseBindMatrix)` against the identity matrix
component-by-component (`toBeCloseTo`, not exact float equality). Confirmed
on Valkyrie Profile 2 (PS2): a `THREE.Matrix4`-based test proved this for
IDOM-bone-palette skinning where ~38% of per-vertex bone addresses didn't
resolve against any `IDOM` chunk carried by their own mesh record — the
proof meant the unresolved fraction did not need to block shipping a real,
visually-verified static-pose skinned export.

## A header's own count/table-start/table-end fields cross-checked arithmetically — before any semantic decode

When an unfamiliar container/bundle header has a plausible `count` field and
a plausible table-start-offset field, and a third field looks like it might
be a redundant "table end" or "next section" offset, check whether
`tableEnd == tableStart + count * assumedEntryWidth` holds *exactly* across
several real samples with different `count` values before trusting that
you've identified the right fields at the right widths/roles at all. This is
much cheaper than decoding what the table's entries actually point to, and
it's a strong disambiguator: a wrong entry width, a wrong table-start field,
or a miscounted header size almost never produces a coincidental exact match
across multiple different `count` values, so a clean pass across a handful
of samples is real confirmation, not just plausibility. Confirmed on NieR:
Automata (PC)'s in-house `DAT\0` resource-bundle container (`flower`
project): a 32-byte header (`magic`, `count` u32 LE, `headerSize` u32 LE,
`tableEnd` u32 LE, three more unidentified u32 fields) followed by a
`count`-entry table of `u32 LE` absolute offsets. `tableEnd == headerSize +
count*4` held with zero deviation across 12 real decoded samples spanning
`count = 1` to `count = 512` — strong enough evidence to treat the header
shape as confirmed and move straight to walking the offset table for real
sub-resource magics, without first tracing any loader code (none was
available for this title in this pass).

**The same invariant chains across more than one trailing header field.** A
follow-up pass on the same `DAT\0` container found its two remaining
unidentified header fields (`0x14`/`0x18`) were each *further*
`count`-length `u32[]` tables immediately following the ones already
confirmed — `nextFieldEnd == prevFieldEnd + count*4` held again, twice
more, with the same zero-deviation strength across a wider sweep (60
samples, `count` 1-666). Once one `tableEnd == tableStart + count*width`
invariant is confirmed, check whether the header's *next* unidentified
field is simply the end of another same-width parallel table before
assuming it's structurally different — repeating an already-confirmed
field-width guess against the next offset is nearly free to test and, when
it holds, decodes an entire additional table for the cost of one
arithmetic check. (One of the two candidate fields here turned out instead
to be the end of a variable-length name-string region — the invariant
correctly *failed* to hold there at the assumed fixed width, which was
itself the signal that field was a different kind of region, not a
counter-example to the technique.) A cheap secondary confirmation once a
table's role is still just a structural guess: if a nearby region turns
out to hold literal ASCII content, cross-check it against known strings
from other evidence — here, real per-entry resource *names* recovered from
that name-string region included `"dummy.wmb"`, matching a literal
fallback-mesh string already found in the executable by an unrelated
method (a strings scan) — an independent semantic confirmation stacked on
top of the arithmetic one.

## Two structurally-unrelated counts of the same population, derived by different methods, agreeing exactly

When a corpus has both (a) a low-level container-framing structure that can
be walked from raw bytes with **zero** knowledge of the higher-level
format (an outer compression codec's frame boundaries, a fixed-record
directory, a chunk-tag scan) and (b) a separately-decoded master index/
table-of-contents that *also* independently declares how many sub-units
belong to each group, comparing the two per-group tallies is an
unusually strong, free verification oracle — the two counts have no
shared derivation to produce a coincidental match, so exact agreement
across every group is close to byte-exact-strength confirmation of both
sides at once, without needing an emulator or a second reference
implementation. Confirmed on NieR Replicant ver.1.22474487139 (PC,
`flower` project): each `.arc` file's outer Zstandard-frame count (walked
from raw bytes via the public zstd frame-header spec, computed before any
knowledge of the in-house `tpArchiveFileParam` master index's contents)
exactly matched that same archive's `arc_index`-grouped file count from
the independently-decoded master index (`info.arc`) — `lang1.arc` 3 = 3,
`lang2.arc` 4 = 4, `param.arc` 250 = 250, `init.arc` 3,533 = 3,533,
`stream.arc` 3,593 = 3,593, and the sum (19,162) matched the index's own
declared total `file_count` field too. The one archive that *didn't*
match 1:1 (`common.arc`: 1 outer frame containing 11,779 index-declared
files) wasn't a failure — it was itself informative, since the index's
own `is_streamed=0` flag on that archive predicted exactly this shape
(whole-archive-decompressed-up-front, individual assets as flat
uncompressed slices within the one frame) before that flag's semantics
had been otherwise tested.

## A cross-region bijection: a predicate over region A selecting exactly the cells region B's record table addresses

When a file has both (a) a bulk array whose values you can classify with a
predicate derived from *code* (or from a value-decomposition rule), and (b) a
separate, smaller record table elsewhere in the same file whose records carry
coordinates into that array, the two can verify each other with no external
oracle at all. Select the cells the predicate marks special; collect the cells
the records point at; compare **as sets of coordinates**, not as counts.

An exact cell-for-cell match is unusually strong because a single test
confirms several independent unknowns simultaneously — the array's row stride,
its row order, the record's field order (which byte is column, which is row),
and the correctness of the predicate itself. Any one of those being wrong
scrambles the coordinates and destroys the match; there is no way to get a
perfect bijection out of a wrong layout.

Confirmed on Phantasie I (Amiga, `nicodemus` project): the predicate "the
engine's three dispatch paths that consult the point-of-interest table" (a
ones-digit test plus two whole-value compares, all read off the disassembly)
selects **99 cells** across 18 shipped 20×26 terrain grids, and the 18 record
tables hold **99 records landing on one** — matching at identical
`(column, row)`, with **zero** marked cells lacking a record and **zero**
records for a marked cell that isn't there. The two records that fell outside
the rule were traceable to stale slots. Note the negative half carries as much
weight as the positive: the engine's *other* events (a whole-value compare, a
class dispatch) are parameterless, and correctly have no records at all —
a predicate that over-selected would have shown up immediately as unmatched
cells.

## Settling an orientation/field-order ambiguity by rare-value enrichment, not by eye

When several readings of a coordinate pair (`(x,y)` vs `(y,x)`, row-major vs
column-major, width W vs width H) all produce in-range indices, "which render
looks right" is subjective and a wrong reading can look plausible. There is a
cheap objective discriminator whenever the coordinates are expected to point
at *special* cells: for each candidate reading, look up the value landed on
and score it by that value's **frequency in the corpus as a whole**. The
correct reading concentrates on rare values; wrong readings land on bulk
content at chance frequency.

Confirmed on the same corpus: reading a record's first two bytes as
`(col, row)` into a width-20 row-major grid landed on values with a mean
corpus frequency of **0.0023**, while `(row, col)` row-major, column-major and
row-major width-26 all scored **0.072** — i.e. exactly the background rate.
A **31× enrichment toward rare values** settled grid width, orientation and
record field order in one measurement, before any code had been disassembled.
This generalises to any "pointer into a bulk array" question — item drops into
a loot table, trigger cells into a map, entity ids into a name table — and it
is worth running *before* reaching for an emulator, since it costs one pass
over data already in hand.

## Corpus-wide content hashing discriminates "this instance's own resource" from "a shared/generic one"

When a container embeds several same-typed sub-resources (textures, sound
banks, palettes) per instance and it's unclear which slot is semantically
"this specific instance's own" versus a common/default one reused across
many unrelated instances, decode and content-hash that slot across the
*whole* corpus rather than guessing from slot position or size alone. A
slot whose decoded content is unique per instance is instance-owned; a slot
whose decoded content recurs byte-identical across many otherwise-unrelated
instances is a shared/generic resource, not that instance's own — no
disassembly of the loading code needed to make this call.

Confirmed on Chaos Legion (PS2, `flower` project): each of 40 decoded 3D
model packages embeds exactly 2 `TIM2` textures. MD5-hashing every
package's decoded RGBA content showed slot 0 (the first embedded texture)
is unique on every package sampled, while slot 1 recurs byte-identical
across many unrelated packages (e.g. one exact hash shared by 5 different
models with visibly different mesh shapes) — real, corpus-wide evidence
that slot 0 is the model's own per-part diffuse atlas (later bound as
`baseColorTexture`) and slot 1 is a shared secondary map, without needing
to trace the game's own material-binding code at all. This generalizes to
any "which of these N embedded resources is mine" question: dimension or
byte-size alone (see `recurring-exact-size-may-be-encoder-output-not-
shared-content.md`) is too weak a signal since same-size instances can be
completely unrelated content, but full-corpus *content* hashing turns
"shared vs. unique" into a cheap, decisive, code-free measurement.

## Reapply an already-validated technique to the new population before inventing a new statistic

When a format has an unresolved field (a flag bit, a sub-mode byte) *within
a format whose own spec already contains a decisive verification technique
for a structurally analogous question*, try that same technique against the
new field's two populations (flagged vs. unflagged, mode A vs. mode B)
before reaching for a new statistical test. Correlation-style approaches
(tag distribution, position-in-list, size distribution) tend to produce
real but merely suggestive signal — enough to write up a plausible
hypothesis, not enough to close it — because they measure *association*,
not the mechanism itself.

Confirmed on Drakengard 2's `CSFg` mesh format (`flower` project): a strip
header's bit 15 was known to require masking for correct parsing but its
meaning was unresolved after a full session of tag-correlation, list-
position, and vertex-set-overlap analysis (real signal, not decisive). The
same format's own spec already had a *decisive* winding-verification
technique from solving ordinary triangle-strip winding earlier (checking
face orientation against each triangle's own vertex normals, confirmed
100.00% agreement on thousands of real faces). Re-running that identical
face-vs-normal check, split by the flag bit instead of by nothing, was
immediately decisive: 14,362/14,368 flagged strips wound backwards, 0
forward — bit 15 is a reversed-winding flag, gated by a separate sub-block
`flags` bit that a prior pass had also left as "role unresolved" without
connecting the two fields at all. The fix cost one re-run of an existing
function against a new split, not a new investigation.

**A companion lesson on testing a "duplicate/two-sided geometry" hypothesis
specifically**: vertex-*index*-set overlap between two candidate
populations is a weak test — real, topologically distinct surfaces
routinely share a meaningful fraction of vertex indices at seams/borders,
so partial overlap is compatible with both "these are the same surface
duplicated" and "these are two different surfaces that happen to meet."
The decisive version operates one level up, on **triangles**, not vertices:
exact triangle duplication (same 3 indices, or same 3 resolved positions)
and shared-edge-topology counting (how many of population A's edges are
also population B's edges) between the two populations. Zero triangle
duplication and edges shared at roughly the rate you'd expect from one
continuous surface (not ~100%, which would mean two full copies) cleanly
refutes a duplicate-pass hypothesis in a way vertex-index overlap alone
cannot — confirmed in the same Drakengard 2 investigation above, where
0/104,348 flagged triangles duplicated an unflagged one and 31.8% of
flagged edges were shared unflagged-triangle edges (one continuous
membrane, not two stacked layers).

**Dual independent ports of a traced algorithm, diffed on intermediate
structured output — not just final renders.** When a disassembly trace of a
non-trivial algorithm (a view-walk, a dispatch cascade, a layout engine) is
being promoted into pipeline code, implement it twice from the trace
independently (e.g. a throwaway Python oracle and the committed TypeScript
port) and require **exact identity of the intermediate output list** (the
ordered resolved words/records/draw-calls, not the composed image) across
a spread of real inputs. This is stronger than Method §6's pixel-exact
final-render regression alone: renders tolerate classes of bugs that
structured-output identity does not. Confirmed on Wizardry 6 SNES's
dungeon-view walk — requiring word-identical output across 7 real poses
caught two bugs whose renders still looked plausible: a global-vs-grid-
local coordinate-space mix-up, and a parity term computed from local
instead of absolute map coordinates (wrong on levels whose grid origin is
odd). Any disagreement pinpoints the first diverging element, which names
the faulty stage directly.

## Legible in-game text as a free geometry oracle when no screenshot/emulator is available

When no ground-truth render (real screenshot, emulator framebuffer, sibling
port) can be obtained cheaply, rendering a *whole* tile/character ROM and
reading it for recognizable text is a strong, free structural oracle for
**tile geometry** — tile size, bitplane count, plane order, and intra-plane
bit order — even with zero palette work done. A wrong plane order, wrong
bit order (LSB- vs MSB-first), or wrong tile size produces visual noise;
it does not produce a legible alphabet strip or a legible sentence by
chance. Confirmed on Golden Axe (Sega System 16): rendering all 16,384
tiles from the "tiles" ROM region in plain greyscale (index value only, no
palette applied) reproduced a complete `A-Z` UI font strip, readable
English narration text ("...his brother was killed... Death Adder"), and
readable Japanese katakana — upgrading a plane-count/bit-order decode from
"reconstructed from a standard convention, unverified" to confirmed,
without installing an emulator or finding a real screenshot.

**Scope this claim carefully**: it confirms *geometry*, not *color*. See
`legible-text-render-weak-palette-oracle.md` — the same kind of legible
render is a **weak** oracle for whether a resolved *palette*/color-mapping
field is correct, because a wrong palette pointer can still land on data
that happens to render legible text. Keep the two claims (tile geometry vs.
palette/color) independently labeled; don't let a legible render upgrade
both at once.

## Sample-to-sample delta ("smoothness") discriminates signed vs. unsigned 8-bit PCM when byte-value statistics can't

A raw 8-bit sample ROM with no header/spec has two live hypotheses for how
to read a byte as an amplitude: two's-complement **signed** (silence at
byte `0x00`) or **unsigned with a bias** (silence at byte `0x80`). A naive
discriminator — the mean byte value across a region — does **not**
distinguish them: both readings of the *same* real bipolar waveform
average out to ~127.5 raw-byte-wise, regardless of which one is "true"
(an inherent property of the XOR-0x80 relationship between the two
readings, not a coincidence of any one game's data).

What does discriminate: **mean absolute sample-to-sample delta**
(`mean(abs(diff(samples)))`) computed under both candidate readings, on
several regions actually expected to hold real audio. Real audio is
low-frequency-dominant (smooth, low-derivative); reading it under the
*wrong* bit-interpretation introduces a spurious large jump every time a
raw byte crosses the 0x00/0x80 boundary that the two readings disagree
about, inflating the delta. Confirmed on Capcom QSound sample ROMs
(`kolbold`, ddsom + ddtod, CPS2): the signed-native reading scored 4-9x
*smaller* mean delta than the unsigned-biased reading, consistently
across 12 sampled 16 KB regions spread across two different games' 4MB
ROMs — agreeing with (and independently confirming, from raw bytes alone)
a reading also derivable directly from the emulator source's C++
arithmetic. This generalizes past QSound/CPS2 to any raw, header-less PCM
sample ROM on any platform where the signed-vs-unsigned convention isn't
otherwise documented.

**A stronger oracle, when available: check whether the format's reference
emulator is LLE, not HLE.** MAME's `qsound_device` is a *low-level
emulation* — it runs the real DL-1425 chip's own dumped internal DSP16A
microcode ROM, not a hand-tuned algorithmic approximation of "what the
chip probably does." An LLE device's low-level register-read/external-ROM
-read function bodies (here, `dsp_sample_r()`'s literal `u16(byte) << 8`)
are strong, literal ground truth for the *raw stored data format* — the
emulator has no slack to deviate from the real bit-level transform and
still sound right, unlike a from-scratch high-level model. Before trusting
an emulator device's source as literally as this, check which kind of
emulation it is (the device source's own header comments usually say, as
`qsound.cpp`'s does) — an HLE device's internal representation may not
correspond to the real stored byte format at all.

## Sizing an enum-driven jump table with no explicit count: use a second, already-suspected table's own start as the boundary

A `switch`-style PC-relative word-displacement jump table (the standard 68k
`move.w table(pc,Dn.w),Dn; jsr table(pc,Dn.w)` idiom, and its equivalents on
other CPUs) rarely stores its own entry count anywhere nearby — the count
lives only in whatever code computed the index (a `cmpi`/bounds-check
against the max valid type/state value), which may be far away or in a
different function entirely. If a *second* table is already suspected to
sit immediately after the first (e.g. two dispatch tables for the same
enum, one for "update" and one for "draw", back to back in the data
stream), walk the first table's entries sequentially, computing each one's
real target address, until one entry's computed target lands **exactly** on
the second table's own known first entry (byte-for-byte, not approximately)
— that coincidence pins the first table's true length decisively, with no
guessing and no need to find the bounds-check code at all. Confirmed on
PowerMonger (Amiga): walking a per-entity-type dispatch table entry-by-entry
found that entry 23's computed target address exactly equaled a second,
independently-suspected table's own entry 0 target — confirming the first
table holds exactly 23 entries (46 bytes), a clean, unambiguous boundary
with zero slack. Cheap (a few lines of address arithmetic, no disassembly
needed for the search itself) whenever two related tables are expected to
be adjacent, which is common for "one dispatch enum, several parallel
per-case tables" designs.

## Bidirectional back-reference: finding both writes in one code block is stronger than finding either alone

When two record types are hypothesized to hold reciprocal back-references
to each other (a child record pointing at its parent, and the parent
pointing back at the child — e.g. a unit referencing its owning
team/faction, and the team referencing its units), a single disassembled
write of *one* direction (`childRecord.ownerField = parentOffset`) is
already useful evidence, but it's still consistent with the other direction
not existing, or pointing somewhere unrelated. Finding **both** writes
inside the same short, unbranching code block — one instruction computing
`(childPtr − childArrayBase)` and storing it into the parent's field,
another instruction (a few lines away, same block) computing
`(parentPtr − parentArrayBase)` and storing it into the child's field — is
much stronger: it confirms the relationship is genuinely bidirectional and
intentional (an allocation/attachment routine wiring up both halves at
once), not a coincidental resemblance between two unrelated fields. This is
cheap to spot once you're already looking at the record-creation/attachment
code (no extra tracing needed beyond reading the rest of the block you're
already in) and much stronger than treating either write as sufficient on
its own. Confirmed on PowerMonger (Amiga): a single ~12-instruction block
computed both an entity's pool-relative offset (stored into its owning
team record's field) and the team record's own table-relative offset, +
a fixed bias (stored into the entity's own "owning team" field) — settling
both the entity→team and team→entity relationship in one read, rather than
needing two separate discoveries to independently agree.

## Self-verifying index-base alignment: derive a table's base by exhaustive search + 100% sentinel agreement, then falsify with a shift sweep

Two data structures index the same entity space but start at different
origins — a gamedata table numbered 100..470 and an executable-resident
resource array numbered 0..13132, say — and you need the constant that
joins them. The tempting move is to line up one landmark ("the table's
first record must be the model block's first entry") and hardcode the
resulting offset. That is exactly the move that fails silently: on FE
Warriors (Switch, `chimera`) the obvious landmark alignment put the
final-boss dragon at ID 131 while every other line of evidence said 132,
and an off-by-one hardcoded constant would have mislabelled all 350
records with a plausible, entirely wrong name each.

**Do this instead.** Find a *sentinel you already derived from the bytes
alone*, before and independently of the join — a property each record
carries that the other structure independently mirrors. Then search **every
candidate base** and keep the one where the two agree for *every* record.

FE Warriors' sentinel was a "reduced/placeholder record" flag found a pass
earlier by pure column census (`col1 == 0xffff` **and** `col2 == 0`
**and** `col5 == 0`), and the registry's mirror of it was the literal path
`nx/action/model/not_exists_file.bin.gz`. Exactly one base out of ~12,600
candidates made those agree on all 350 records (97 placeholder, 253 real),
0 false positives and 0 false negatives.

Three properties make this worth preferring over a landmark:

1. **It is its own verification.** Picking 97 specific slots out of 350 by
   coincidence is ~1 in 10⁹⁶; the search succeeding *is* the evidence. No
   separate confirmation step is needed, and the number it produces
   (350/350) is exactly the quantified figure Method §4 demands.
2. **It re-runs.** Ship the search in the extractor rather than the
   constant it found. Every pipeline run then re-derives and re-asserts the
   alignment against the real bytes; a different game build, a patched
   executable, or a wrong input fails loudly instead of emitting confident
   nonsense. Make the function **throw when zero or more than one base
   qualifies** — "ambiguous" must not silently pick the first hit.
3. **It refuses input that can't decide.** A table with no placeholders at
   all (FE Warriors' `ModelEvntParam.bin`) is satisfied by thousands of
   bases. Require a minimum count of *both* sentinel states before
   accepting a table as the aligner, and cross-check the siblings with the
   base the discriminating table produced.

**Then falsify it.** Uniqueness inside the search is good; showing the
score *peaks* at that base is better, because it proves the metric has
gradient rather than being satisfied by luck. Sweep the base ±N and print
the score at each offset:

```
shift  -6   -5   -4   -3   -2   -1   +0   +1   +2   +3
score  327  331  335  339  343  347  350  348  346  344   (of 350)
```

A clean unimodal peak at 0 is a much stronger statement than "350/350 at
the answer". Score a **second, structurally unrelated metric** the same way
if one is available — here, "does each `_V_Higher` costume variant's record
come out byte-identical to its own base character's record" (176/195 at the
correct base, 169 at −1, 44 at +1). Two independent metrics peaking at the
same offset is decisive.

**Best of all, add a third check that doesn't touch either structure.** FE
Warriors' data partition happens to contain 34 files named
`NNN_<ModelName>.bin.gz` — a number and a name in the same filename. For
all 32 members of the character block, `NNN − modelId == 99` exactly, 0
deviation, confirming the alignment from filenames alone with no dependence
on the executable or on any statistic above. Look for this shape wherever
an asset directory embeds ordinals in filenames; it is free ground truth
and it is the kind of thing a `ls` shows you in one second.

## Solving unknown per-type element sizes by least squares over a whole-corpus size invariant

**When it applies:** a record format has a `typeTag` field that selects an
element *type*, the tag is not the element size, the size is nowhere in the
file, and the corpus uses more tags than you want to bisect one at a time.

Guessing tag sizes one at a time is slow and ambiguous, because a record
usually mixes several tags at once, so any single record has many
consistent solutions. But every record gives you a linear equation:

```
sum over properties of  count[p] * size[tag[p]]  ==  valueSectionLength
```

Collect that equation from tens of thousands of real records (you can walk
the records without knowing the sizes at all — the record header carries its
own length, so block chaining is independent of value parsing) and solve the
whole system at once with `numpy.linalg.lstsq`. With enough records the
system is full rank and the solution comes out as exact small integers,
which is itself the tell that the model is right — a wrong model gives
fractional garbage.

Confirmed on FE Warriors: Three Hopes' `KOD` object database (`chimera`).
150,000 sampled records, 10 distinct tags, full rank, exact integer solution
`{0:1, 1:1, 2:2, 3:2, 4:4, 5:4, 8:4, 10:16, 12:8, 13:12}`. A first pass on
one file alone had produced `{1: 0.698, 2: 2.094, 4: 1.693, ...}` — rank 2
of 5, i.e. visibly under-determined, which correctly said "sample more
files" rather than "round these to integers".

**Then verify exhaustively, not statistically.** Re-run the model over the
whole corpus and require the value section to tile *exactly*: no slack, no
over-read, on every record. Three Hopes: **560,408 / 560,408 blocks with 0
slack**, and only those ten tags ever occur. That is a zero-deviation
structural invariant of the kind this document's opening argues for — a
wrong size for any tag would leave a residue somewhere in half a million
records.

Two practical notes. Rank deficiency is informative: tags that only ever
co-occur cannot be separated, so print the rank and add records until it is
full rather than trusting a plausible-looking fit. And a fitted value near
but not at an integer (`0.7`, `2.1`) means the equations are inconsistent —
usually because the walker is mis-parsing some record kind, not because the
size is unusual (here it was an unhandled sibling block magic; see
`block-chain-walk-stops-at-unknown-sibling-block-magic.md`).

## A published enum is three separate oracles: per-index labels, value gaps, and members' name suffixes

When a community template, header dump or wiki ships the game's own enums,
the usual use is weak — "every decoded value is in range". Real enums carry
far more structure than their value set, and all three signals below cost
nothing beyond parsing the enum you already have.

**1. An index→label enum is free ground truth for the whole table.** If an
enum has exactly as many members as the table has records, it names every
record by *position*, with no decoding at all. Cross-check it against a byte
field you decoded independently and you have two name spaces from unrelated
sources agreeing (or not) on semantics, per record. Confirmed on Fire Emblem:
Three Houses' `Scenario` table (`chimera`): the template's `ScenarioName`
enum has exactly 100 entries for 100 records, and names the auxiliary-battle
block by location (`AuxCanyon`, `AuxAlmyra`, `AuxGronder`, …). The
independently decoded map field at offset 0x13 resolved through a *different*
enum to `Zanado`, `FodlansThroat`, `GronderField`, … — **20/20 exact
agreement**, no deviation. Neither enum knows about the other; agreement on
20 consecutive records is decisive and took one script.

**2. Reproducing the enum's *gaps* is much stronger than staying in range.**
A sparse enum's skipped values are a free negative test: real data drawn from
that enum should skip them too. Same table: the `BGM` enum's low block is
even-valued but omits 22, and across four builds the real field takes
`{0,2,4,…,20,24,26,28}` and **never 22**. "Subset of the declared values
*including* the gaps" rules out the whole family of near-miss layouts (an
off-by-one field position, a neighbouring column) that "all values ≤ max"
happily accepts.

**3. Members' name suffixes pin slot order in a parallel array.** Where a
record holds N adjacent fields that are per-variant versions of one thing
(per route, per difficulty, per language, per region), value ranges alone
usually can't tell you which slot is which — every slot has the same range.
But if the enum's own member names carry the variant suffix, the *permutation*
does it for you. Same table, five adjacent condition bytes
`[casual, SilverSnow, AzureMoon, VerdantWind, CrimsonFlower]`: one record
stored `44, 71, 73, 74, 72`, and the enum independently declares
`FallMercieCaspar=44`, `…SS=71`, `…CF=72`, `…AM=73`, `…VW=74`. The stored
order is **not monotone** — `n, n+2, n+3, n+1` — yet each slot lands on the
member carrying that slot's variant suffix. A non-obvious permutation
matching independently-declared labels position-for-position cannot be
chance; a monotone run would have proved nothing. Prefer the records where
the values are *out* of numeric order as your evidence.

Caveat that applies to all three: the enum's *labels* are still fan-authored
and can be wrong even when the numbering is right — here five paralogue
labels named the wrong member of a character pair, which the record's own
decoded fields corrected. Treat the enum's structure as the oracle and its
prose as a hypothesis (`community-table-name-mismatches-semantic-content.md`).

## A synthesizer pitch table confirms itself from its own numbers — no emulator, no reference decoder

A candidate note/frequency lookup table for real sound-chip hardware (an
FM synth's block+F-number pair, a PSG's period-count table, any table
whose entries feed a musical pitch register) carries an extremely strong,
purely arithmetic self-check that needs no external oracle at all: real
equal-tempered chromatic music has a fixed, universal ratio of
**2^(1/12) ≈ 1.059463** between the numeric values of adjacent semitones,
and an octave/"block" field should increment by exactly 1 every 12
entries while the value's remaining bits cycle identically. Compute the
ratio between every pair of consecutive decoded entries (as a plain
`float`, no chip-specific math needed) and check it clusters tightly
around 1.0595 across the whole table; separately check the block/octave
field's own periodicity. Confirmed on Black Tiger's (arcade, `kolbold`)
YM2203 sound driver: a candidate table found purely by "this address is
read via a 16-bit table lookup right before two register writes at 0xA4/
0xA0 (the real YM2203 F-number/block registers)" showed a ~1.0595 ratio
between all 12 within-octave entries and the octave field advancing by
exactly 1 every 12 entries, across 6+ octaves with zero deviation — closed
the format with nothing but arithmetic on the raw bytes, before any
emulator or hand-rendered audio existed to check against.

This generalizes past pitch tables to any decoded field whose real-world
domain has a fixed, checkable numeric law independent of the specific
game or chip (evenly-tempered music is one instance of a broader class:
physical/mathematical constants baked into hardware behavior). A
**second, complementary check** for an adjacent instrument/voice-parameter
table in the same format family: if a decoded byte is masked to N bits
(e.g. `and 0x3f`, 6 bits) immediately before being written to a named
hardware register, and the target chip's real public register map
documents that exact register as an N-bit field (YM2203's algorithm+
feedback register, reg 0xB0, is documented as exactly 6 bits wide), the
width match itself is real corroborating evidence for the field's
identity — a coincidental bit-mask matching a real chip's exact
documented field width is unlikely, and this check costs nothing beyond
reading the chip's own register-map reference once (`ymfm_opn.h`, in this
case, already used elsewhere in the same project for the Timer A/B
register map).

## Two independently-decoded event/branch streams converging on the same byte address corroborates both

Any format where multiple independent instances read from a shared or
overlapping byte range via their own internal jump/loop/reference offsets
(a per-channel/per-voice event-byte stream with loop instructions, a
dialogue tree with shared branches, an animation state machine with
shared sub-sequences, a scene graph with instanced sub-trees) offers a
free, strong cross-check with no external oracle: decode two or more
instances independently, and check whether an instance's own internal
branch target lands on a byte address *inside another already-decoded
instance's own stream* — and, critically, whether the grammar continues
to decode as valid, coherent content from that shared point onward in
BOTH readings. This is stronger than "the offsets happen to overlap";
requiring both interpretations to remain well-formed and semantically
coherent past the convergence point is what makes it decisive (a
coincidental byte-range overlap with no semantic continuation would fail
this immediately). Confirmed on Black Tiger's (arcade, `kolbold`) FM
sound driver: decoding two of a track's six independent channel event
streams found one channel's own `LOOP_FOREVER` instruction targeting an
address that landed exactly on a `SET_INSTRUMENT` event in the middle of
a *different*, separately-decoded channel's stream — and both channels'
decodes continued to produce identical, grammatically valid musical
events past that point (a shared bassline/rhythm part referenced by two
voices). Confirms the event grammar, the loop-target field's width/
encoding, and the shared-content hypothesis all at once, from nothing but
the two decodes agreeing with each other.

## Within-group monotonicity resolves a row-grouping ambiguity a confirmed stride/count can't

A confirmed record stride and total row count can still satisfy more than
one factorization (`112 = 56×2` "one pair per roster entry" vs. `16×7`
"16 tiers × 7 growth stages"), and a whole-array autocorrelation scan
that already found the stride won't discriminate between them — it only
proves the stride, not the semantic grouping. The fix: for every
plausible group size, split the rows into that many consecutive groups
and test each numeric field for **strict monotonicity within each
group** (not across the whole array). A real tier/level/growth-curve
table shows near-total monotonicity — confirmed on Valkyrie Profile 2
(PS2)'s master gameplay data file: 6 of 10 candidate `u16`/`u8` fields
were strictly non-decreasing across *all* 16 groups of 7 with zero
exceptions, a result with combinatorial odds against chance on the
order of `(1/7!)^16` — decisively correcting a previously-documented
"56×2, unconfirmed coincidence" reading to "16×7, a per-tier stat
growth-curve table," which also happened to match the game's own
already-confirmed 16-valued (`0`-`15`) tier/grade field elsewhere in the
same file. Fields that don't show the pattern (2 of the 10 candidates,
in the same table) are real evidence they're a *different* kind of
field, not part of the growth sequence — the test discriminates within
one record's own field list, not just between grouping hypotheses.

## Touches-per-distinct-element ratio distinguishes overlapping independent variants from a spatial partition

A repeating-group structure where each group references a set of shared
elements (a facial morph-target group referencing mesh vertices, a level
layout referencing tile cells, any "many small records, each touching
some subset of a shared pool" shape) has two structurally different
readings that look similar at a glance: **spatial/logical partition**
(each group owns a disjoint slice of the pool — e.g. one group per mesh
region) vs. **independent overlapping variants** (many groups each
redundantly cover the *same* small pool with their own distinct values —
e.g. one group per blend-shape/animation-pose, all deforming the same
vertex set differently). Compute total `(group, element)` touches ÷
distinct elements touched: a partition keeps this near 1 (each element
belongs to ~1 group); an overlapping-variant system gives a ratio far
above 1. Confirmed on Valkyrie Profile 2 (PS2)'s `ECAF` facial
morph-delta groups: only 43-44 distinct vertices were touched by 30-48
groups each, a pooled ratio of `20.29` — decisive. A prior "spatial
clustering via group centroid distance" test on the identical data had
been inconclusive, because it silently assumed the partition premise
this ratio test directly refutes — always run the ratio test first, it's
cheaper and it tells you which of the two spatial tests (if either) even
applies. **Pair it with a redundancy check**: also confirm repeat visits
to the same element carry *different* values (98.8% did in the confirmed
case, checked at a `1e-6` threshold) — a high touch ratio with identical
repeated values would instead indicate duplicate/redundant encoding, not
real independent variants.

## Cross-file field-recurrence census locates a shared struct's layout when no single consumer reveals it, validated against already-known fields

When many small files/objects share one central manager/singleton/
service struct and no single consumer's own disassembly is complete
enough to reveal the whole struct, don't pick one file and trace it
deeper — census **every** direct field dereference off the shared
pointer across **all** files in the corpus that reference it at once,
then rank candidate field offsets by how many **distinct files**
reference them (not raw occurrence count within one file). A field a
compiler-generated struct genuinely has tends to recur across many
independent consumers; an offset that only shows up once, in one file,
is weaker evidence (could still be real, just not corroborated) —
occurrence count within a single file conflates "used many times in one
place" with "a real, corpus-wide struct member," which cross-file
recurrence doesn't.

**Validate the method before trusting new results**: if any of the
struct's fields are already independently confirmed (from prior,
unrelated disassembly work), check that the census's own top-ranked
entries reproduce them before trusting anything new it surfaces.
Confirmed on Valkyrie Profile 2 (PS2): censusing all 10 files in a
family of dungeon-mechanism scripts for their own dereferences of a
shared scene-manager singleton pointer found that the census's top 2
entries by cross-file recurrence (8/10 and 6/10 files) exactly
reproduced 2 already-independently-confirmed singleton fields (a
sub-manager pointer and a game-state pointer) — a real validation, not
a coincidence, since nothing in the census's own logic favored those
specific offsets over any other. With the method validated, its
top-ranked *new* offset (7/10 files, 35 total sites — more than either
already-known field) was then hand-traced to a decisive semantic
resolution: it's passed as the first argument to an already-confirmed
shared API function, explaining why it was the single most-referenced
field in the whole census (the operation it enables — firing a trigger/
completion event — is near-universal across the file family, unlike the
rarer once-per-entry-point accesses the other confirmed fields get).

This generalizes past this one project: any "many small files share one
opaque central struct, and no single file's code reveals the whole
layout" situation is a candidate for whole-corpus-census-by-cross-file-
recurrence instead of picking one file and tracing it deeper — the
struct's real field boundaries emerge from agreement across independent
consumers, the same way a format's real record boundaries emerge from
agreement across a container's redundant self-describing fields
(`content-addressed-manifest-merge-needs-source-precedence.md`'s sibling
principle for *containers*, applied here to *code-referenced structs*).
See `literal-argument-spilled-through-stack-slot-defeats-adjacency-scan.md`
for a scripting pitfall that hits this exact census shape — a scan
window too narrow to see past an intervening non-destructive instruction
will undercount or miss real fields before you ever get to rank them.

## An FSM's init routine, not just its dispatch table, decides animation frame play order

A confirmed 2-(or-more)-state animation ping-pong (a per-object state
field indexing a jump table, each target drawing one frame and toggling
to the next state) tells you *which* fields/frames exist and *how* they
alternate, but not *which one plays first* — the dispatch table's shape
is symmetric under state relabeling, so reading it alone can't settle
temporal order. The deciding evidence is one level up: the object's own
spawn/init routine, specifically the *initial* value it writes into the
same hold/countdown timer the steady-state dispatch resets on every
flip. If the initial value differs from (usually is shorter than) the
steady-state reset value, the state the FSM starts in fires its first
transition almost immediately — so the frame *that* transition draws is
the one shown first, not the state the FSM happens to begin in.

Confirmed on Knights of the Round (CPS1, `kolbold`): an enemy-portrait
object's 2-state ping-pong (`0x9d(a0)`, jump table at maincpu `0x52da`)
resets its hold timer (`0x9e(a0)`) to 3 on every steady-state flip
(confirmed at both dispatch targets, `0x52de`/`0x530a`). Tracing the
object's init routine (maincpu `0x547e`-`0x548d`, reached from a
blank-fill loop) found it sets the SAME timer's *initial* value to 1, not
3, alongside `state=0`. With hold=1, the very next per-frame call
decrements it to 0 and fires the first flip after just one frame — so
state 0's dispatch target (which draws record field `wordB`) is the
frame shown first, and the field the FSM only reaches after the initial
short hold (`wordA`) is the true "alternate"/second frame, settled on
permanently once a separate total-duration counter (also init'd in the
same routine) expires. Neither of these facts — which frame is first,
which frame is final — was recoverable from the dispatch table or the
per-flip bodies alone; both came from the init routine's own literal
immediate values.

**The general check:** whenever an animation/blink/ping-pong FSM's frame
identities are confirmed but play *order* isn't, find the object's own
init/spawn code (often reached via a "blank the destination first" loop,
or a dedicated one-shot entry distinct from the per-frame tick routine)
and read the literal immediate values it writes into the same state/
timer fields the tick routine reads. Compare the initial hold value
against the steady-state reset value — a shorter initial hold is strong,
decisive evidence for which state fires (and thus which frame draws)
first, without needing a live capture or emulator.

## A resolution chain's own arity can settle "could this ever vary per-X" cheaper than resolving an ambiguous field's meaning

When the question is "does some per-instance value (per-character, per-
object, per-entity) modulate a specific downstream output (a rendered
texture, a resolved id, a computed stat)," and a plausible-looking
candidate field has been found but its exact semantic role is still
ambiguous (no consumer traced, no lookup table found, sits in an
unrelated-looking section), don't spend the next block of effort trying to
fully pin down what the field does. Check the **arity of the actual
resolution chain** the output goes through instead: if every step from
"per-instance record" to "final output" is provably a scalar keyed only by
a *coarser* dimension (per-class, per-type, per-region — never per-
instance), then no per-instance field could modulate that output through
that chain, full stop, independent of what the ambiguous candidate field
turns out to mean. This is strictly cheaper than resolving the field's
role, and — unlike a hypothesis about the field's meaning — the verdict
survives even if that meaning later turns out to be something completely
unrelated.

Confirmed on Fire Emblem: Three Houses (`chimera`, Switch): asked whether
the game recolors a shared generic-class 3D body model per-character
(e.g. house colors) on top of an already-solved head-swap. A real
candidate mechanism was found and decoded — `PersonData`'s `PaletteID
CharColor` per-character enum field, domain-verified via house-leader
color-archetype matching (the three house leaders' values exactly matched
their real houses' colors) — but its exact consumer was never traced (no
RGB lookup table, no identified shader/mask channel; it sits in a
"weapon ranks/combat assets" section, not an appearance one). Rather than
chase that down further, checking the *actual* resolution chain the
picker's shared-class rendering uses (`ClassData.maleAssetId`/
`femaleAssetId` → an AssetID table → a DATA0 mesh-pack index) found it is
a **plain per-class-and-gender scalar with no per-character slot anywhere
in its type** — every character selecting a given class+gender gets the
exact same resolved mesh-pack index, by construction, regardless of what
`CharColor` means. Combined with a structural census of the mesh
container itself (each pack embeds exactly one fixed baked texture set,
never an array of palette variants, checked across 3 real packs), this
gave a confident, low-effort "not reachable via any decoded pathway"
verdict for the specific question asked, without ever resolving
`CharColor`'s real role.

**The move:** before spending a session budget on deciphering an
ambiguous candidate field, first ask whether the resolution chain its
output would have to flow through even *has* a slot at the granularity in
question. A chain with no such slot answers "could this vary" on its own;
a chain that *does* have the slot doesn't answer anything yet, but at
least tells you the ambiguous field is worth the further effort.

## UV-space unwrap texture baking: reconstruct a standalone atlas with zero packing math

When a mesh format stores raw texture-coordinate bytes (0-255, or any fixed
range) per vertex/primitive alongside a pointer into a shared source
texture/VRAM page, and the goal is a standalone per-model texture atlas
for a modern format (glTF, an atlas PNG) rather than re-deriving the
original engine's packing layout: draw each primitive as a filled polygon
into a blank canvas **at its own raw stored UV coordinates**, sampling the
*source* texture at that exact same (x, y) position for every filled
pixel. Because the canvas position equals the UV position by construction,
the result is a byte-exact standalone atlas directly addressable by
`(u/255, v/255)` (or the format's own UV normalization) — no atlas-packing,
rectangle-fitting, or seam math needed at all, since the "packing" is
whatever layout the UV coordinates already describe.

Confirmed on Parasite Eve (PSX)'s actor-model format: baking each
primitive's polygon at its own stored `(u,v)` byte coordinates into a
256x256 canvas, sampling the corresponding 4bpp/8bpp-indexed or 15bpp VRAM
region per pixel, reconstructed real character-body and clothing textures
pixel-exact against an independent reference decoder's render, across
136/136 models — with the resulting PNG usable directly as a glTF material
by feeding the same raw UV bytes (normalized to 0-1) as the mesh's
`TEXCOORD_0`. The technique only works when UV coordinates are genuinely
per-primitive/per-vertex (not shared/interpolated across the whole mesh)
and don't wrap/tile past the canvas bounds — both worth a quick sanity
check (do any stored UV values exceed the format's stated coordinate
range?) before relying on it.

A scanline polygon-fill implementation for this needs the same vertex
*winding* the mesh's own face-index array uses, not raw file order — see
`quad-uv-array-winding-differs-from-index-array-winding.md` for a real bug
this caused.

## Remainder-sweep: pinning a trailing section's stride when it absorbs alignment padding

**When it applies:** a container has several fixed-stride record sections
with known counts, and the last (physically final) section's stride won't
divide its size evenly for a majority of corpus files — even though every
earlier section's stride checks out fine via plain `size / count`.

The last section's declared span usually runs to the payload's real end,
which includes whatever trailing alignment padding the format pads the
whole file out to. That padding makes `size / count` non-integer (or
integer-but-wrong) for any file whose padding isn't a multiple of the
stride — so naive division is the wrong test specifically for the final
section, never mind how well it worked for every section before it.

The fix: don't divide, sweep. For each candidate stride `s`, compute
`remainder = size - count * s` for every file in the corpus and require (1)
no negative remainders anywhere (a stride too large to fit `count` records
is immediately disqualified) and (2) a small, tight set of remainder values
clustered near 0 (real alignment padding is bounded — a handful of bytes,
not an arbitrarily wide spread). The correct stride is the one where the
remainder distribution collapses to something like `{0, 4, 8, 12}` rather
than a wide scatter.

Confirmed twice on the same format family (`vanille`'s `FMBP`/`FMBS`
sprite-model container): first deriving PS2 `FMBP`'s `drawGroup` section
stride, then reconfirmed independently deriving Wii `FMBS`'s own
(different) `drawGroup` stride (16 bytes, vs. PS3 `FMBS`'s 20) after a
naive `size/count` came back non-integer for 382 of 621 real files. Both
times, the remainder sweep pinned the real stride from the corpus's own
bytes with no reference decoder or disassembly needed — see
`port-wide-byte-order-convention-not-uniform-across-formats.md`'s second
instance for the surrounding format-variant context this stride was
recovered under.

## Block-adjacency-derived stride: deriving a raster row width from decoded content alone, with zero layout hypothesis

**When it applies:** a fixed-size-block-compressed (or any tile/block-
structured) image-shaped resource decodes to visible garbage under every
tried header-derived width/height or swizzle-parameter guess, and each
individual guess still has to be tested by rendering and eyeballing it —
i.e. the investigation is stuck sweeping *parameters of a hypothesis*
rather than deriving the layout from the data itself.

Decode every block to its own small pixel patch (e.g. a 4×4 RGB tile for a
BC-family codec) with no assumption yet about how blocks are arranged in
2D. Then, for each block, search **all other blocks** for the one whose
left edge best continues its right edge (matching pixel columns), and
separately the one whose top edge best continues its bottom edge — scoring
by pixel-difference and requiring the best match to beat the runner-up by a
solid margin (e.g. 4×) so only confident, real-content blocks vote. Take
the modal "which other block index is my right/down neighbour, as a
delta from my own index" over all confident votes. A real raster layout
produces one overwhelmingly dominant delta for "right" (almost always `+1`
— adjacent memory) and one dominant delta for "down" (the true row stride
in blocks) — no header field, swizzle formula, or rendering-and-eyeballing
loop is needed; the layout falls straight out of the content's own spatial
continuity.

This also **discriminates competing hypotheses for free**: a genuinely
block-linear/Morton-swizzled surface's *real* memory-adjacency deltas are a
predictable, computable function of the known swizzle address formula (a
small, specific set of small deltas from the bit-interleave pattern) —
compare the empirically-found modal deltas against what the suspected
swizzle formula predicts. If they don't match the predicted set at all,
that's a decisive, corpus-independent refutation of the swizzle hypothesis
entirely, not just of one parameter choice.

Confirmed on Three Hopes' G1T still-art textures (`chimera` project,
2026-09-06, `re-codebreaker`): a "288×512 BC3 texture" that had resisted
four prior differently-shaped Tegra block-linear decode attempts (every
`blockHeightLog2`, several GOB-pitch values, a row-padded linear read, a
naive whole-image transpose) turned out to have no swizzle at all — it was
being read at transposed dimensions (really 512×288). The block-adjacency
search found modal deltas of **right = +1** and **down = +128 blocks**
directly from the block content, with no dimension hypothesis at all;
128 blocks × 72 blocks *is* a 512×288-pixel raster, settling the real
width in one measurement. The predicted-swizzle-delta check corroborated
the refutation: a genuine Tegra GOB layout at this surface's derived
parameters would produce right-deltas clustered on `{+2, +14}` and
down-deltas on `{+1, +3}` (computable directly from the address
function's bit-interleave pattern) — neither appeared anywhere in the
real data, ruling out the whole swizzle-scheme category the investigation
had spent a session inside. See `platform-port-swaps-adjacent-header-
fields.md`'s fifth confirmed case for the header-field bug this technique
uncovered.

## Colour-invariant index-map consistency — screenshot oracle for paletted renders under a runtime palette transform

When a real screenshot of the exact platform exists but the game applies a
runtime transform to the palette (day/night tint, fade, brightness ramp),
raw RGB pixel matching is the wrong test: Dune (DOS VGA, `wyrm`) scored
~0.002 exact-pixel agreement between a command-room screenshot and the
correct room render, because the screenshot's purple ramp carried a G
component (`0,0,16,32,48,64`) the bank's own palette lacks. What is
invariant under any per-index recolouring is the *index map*. Metric:
over the render's painted pixels, learn for each render colour the most
frequent screenshot colour at the same positions, and score the fraction
of pixels whose screenshot colour is that dominant partner. The right room
scored 0.68-0.87 (residual = runtime-placed characters + dither speckle);
every wrong room, and any positional offset, sits on a 0.3-0.5 floor set
by large flat areas — so always report the runner-up as the null. Then
recolour the render through the learned map and diff it against the
screenshot: the mismatch image isolates what is genuinely unexplained
(here: characters drawn from runtime state, and a dither LFSR whose rule
matched but whose sequence didn't) from what is just colour. Screenshots
from an abandonware gallery arrive via `WebFetch` on the raw image URL —
the tool saves the binary to a local path it quotes, which `Read` opens
as an image (see the §4 screenshot bullet in `game-re.md`).

## A masked/bounded argument's whole input domain can be exhaustively checked, not sampled

When a candidate closed-form formula feeds a function whose real argument is
masked or range-limited to a small, enumerable domain — `angle & 0xfff`
(4096 values), a byte (256), a 10-bit index (1024) — don't spot-check a
handful of values and call the formula confirmed. **Enumerate every possible
input and require the formula to match all of them.** This is categorically
stronger than a corpus sample (which only proves the formula holds for the
inputs the corpus happens to contain) and is usually cheap: a few thousand
iterations of table-lookup-plus-compare runs in milliseconds.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): the field engine's `rcos`
routine masks its argument `& 0xfff` and indexes a real on-disc `u16` sine
table through four quadrant branches. Reading the literal table bytes and
replaying the exact branch/quadrant logic for **all 4096** possible masked
inputs matched `Math.round(4096 * Math.cos(angle * 2*pi/4096))` with **zero
mismatches**, on both discs. Because this covers the function's *entire*
domain rather than a sample, it doesn't just corroborate the formula — it
proves the on-disc table holds nothing but a rounded sine curve, licensing
the port to drop the embedded table entirely and ship the closed form
instead (see `docs/valkyrieprofile/psx/dungeon-field-mechanics.md` § 21.2
and `tools/valkyrieprofile/verify-collision-response.ts`).

This is a distinct, complementary technique from
`aggregate-ratio-across-corpus-confirms-closed-form-constant.md`: that lesson
recovers a constant from many real corpus *records*, each contributing one
noisy data point, by averaging away per-record rounding error. This
technique instead recovers (or confirms) a *function*, by exhausting a
bounded synthetic *input space* the function itself defines — no corpus
records or real game content are involved at all, so there is no rounding
noise to average away in the first place, and a single mismatch anywhere in
the domain is decisive refutation rather than an outlier to explain away.
Whenever a formula's argument is provably bounded (a bitmask, a `sltiu`
range check, a fixed-size index), check whether exhausting it is cheaper
than it looks before reaching for a corpus sample.

## Generalize a single-value corpus census to the whole enum before writing it up as done

A corpus-wide census built to answer one narrow question ("does any script
call dispatch-table id 38?") is usually a few lines away from answering the
*same* question for every id in that table's whole range at once — group the
existing per-id/per-value loop's result by the value instead of filtering
for the one you started with. This is cheap (the expensive part, walking the
whole corpus, already has to happen once regardless of how many values
you're looking for) and routinely retires more than one open question in a
single pass, because "which real content invokes value X" is often an
*independent second signal* on top of whatever structural technique named X
in the first place — so the same census that finds a scripted caller for
every id can simultaneously arbitrate a separate structural ambiguity (two
or more candidates tied on byte content alone) by checking which candidate a
real caller actually lives in, and can serve as a positive control by
reproducing an already-published single-id result byte-exact in the same
run. Confirmed on Valkyrie Profile (PSX, `valkyrie`): a script census built
and published for exactly one dispatch-table id (`docs/valkyrieprofile/psx/
data-structure.md` § 9.6.31, "does any script call `TASK` 38") was
generalized, one round later, to all 58 ids of the same table at once
(`tools/valkyrieprofile/verify-task-id-scene-callsites.ts`) — it reproduced
the original id-38 finding byte-exact as a positive control, found a real
caller for 56/58 ids in the same run, and, as a completely free side effect,
settled 3 separate previously-unresolved structural ambiguities (each id had
2-7 candidate rooms tied on byte content; the id's real scripted caller's
own room broke every tie outright, with zero calls from any losing
candidate). None of this required a second pass over the disc — it was the
identical loop, grouped by value instead of filtered to one.

## Cursor-dispatch + save-value arithmetic + string-table join resolves a menu's real option order with no emulator

A common, otherwise-hard-to-settle-without-an-emulator question is "which
enum/index value (a difficulty setting, a game-mode toggle, a sound-test
track slot) corresponds to which real, named, on-screen choice" — i.e. the
menu's option *order*. When the UI draws distinguishing descriptive text per
option (a difficulty screen's flavour blurb, a mode-select screen's caption)
and the game's own string/label table is already cracked, this is resolvable
directly, with no statistical corroboration and no emulator, by chaining
three already-common pieces:

1. The screen's own drawer/dispatch function branches on a UI "current
   cursor" global — find the compare-and-branch (`beq`/`bne` against small
   literals) that selects which extra widget/list to draw for each cursor
   value.
2. A separate, already-known "commit" routine (often already cited in docs
   for an unrelated reason — the actual persisted-value writer) reads the
   *same* cursor global and transforms it into the saved setting via simple
   arithmetic (an offset subtract/shift). This pins the cursor-value-to-
   save-value mapping exactly, with no guessing.
3. Each cursor-gated widget/list has its own leading content record (a
   text/id field) — resolve that id through the game's already-cracked
   string table. If the resolved text is itself an unambiguous name for the
   option ("Recommended for beginners...", "...for a normal game...",
   "...as a challenge!"), the enum-to-name mapping is settled directly, not
   inferred.

This beats statistical/co-occurrence corroboration (see
`traced-enum-label-corroborated-by-carrier-name-set.md`) whenever it
applies, because the join is exact rather than probabilistic — there's no
"non-coherent set" failure mode to worry about, since the string itself
names the choice. Confirmed on Valkyrie Profile (PSX, `valkyrie`): the
title screen's New Game difficulty screen's join-level table had a
long-standing "not oracle-confirmed" hedge on which column meant Easy vs.
Normal vs. Hard. Tracing the screen's drawer (cursor `4`/`5`/`6` each draw
one extra list), joining to the already-cited difficulty-byte writer
(`cursor − 4` = the saved difficulty index), and resolving each list's
record-0 id through the title screen's own string table produced explicit,
unambiguous English naming each difficulty in exact index order — plus two
more ids in the same table independently corroborating the names as bare
words. 44/44 checks, both discs, zero disassembly beyond what a handful of
already-known addresses pointed at directly.

## A sibling field in the same record can explain what a separate field's own values mean

Distinct from "two independently-located tables agreeing on a number" and
from `traced-enum-label-corroborated-by-carrier-name-set.md`'s "join a
value's carrier records to an external name table" — this is narrower and
cheaper: when a record has **two already-independently-decoded fields**,
read one field's real content directly to explain the *other* field's own
enum/id partition, with no occurrence-counting or corroboration across
multiple records needed at all. It works whenever a record couples a raw
numeric/id field (an asset reference, a bucket index) with a human-readable
field (a name string, a category label) that the format's own reader has
already resolved for an unrelated reason.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a 23-scenario mission table
had two already-decoded fields per record — a location-name string id
(`+0x04`) and an "outcome CG" picture id (`+0x0E`) — with the CG ids long
documented as "5 extra ids beyond one-per-mission, role unclear." Joining
each record's own CG id directly against that *same record's* location
string (no lookup into any other table) showed the 5 ids aren't
per-mission art at all — they bucket all 23 missions by **terrain
category** (cave / open-plains / mountain-forest / water / fort), one CG
per bucket. Independently corroborated by an unrelated, code-blind session's
earlier pixel-content description of the same 5 images, which had reached
the identical 5-way split from raw crop content with no knowledge of the
scenario table at all.

The tell that this technique applies: a record format where one field has
long been "resolved" for a completely different reason (here, naming voice
lines) while a sibling field in the identical record sits nearby marked
"unclear"/"not oracle-confirmed" — the resolution is often sitting one field
over, not in a fresh table anyone has to go find.

## Re-rendering a decoder's output fresh, then viewing it with `Read`, turns a stale manual visual check into a repeatable one

A doc's only evidence for a visual/subjective claim ("this character's
illustration shows the class's own weapon/role") is sometimes just "checked
once, by eye" — a quantified tally (e.g. "24/25 match") with no committed
script behind it. That kind of spot-check degrades silently: nobody
re-derives it, and a later audit has only the prose to trust or distrust.
Two cheap changes turn it into a real, repeatable check instead of a second
leap of faith: (1) render the asset **fresh from the decoder under audit**
in a scratch script, not from whatever `public/assets/` cache the build
pipeline last wrote — a stale cached PNG can silently predate a decoder fix
(or a decoder regression) and would falsely corroborate the old claim
either way; (2) `Read` the freshly-written PNG directly (the tool renders
images inline) and judge it with fresh eyes rather than re-stating a prior
session's own verdict about what the picture shows.

Confirmed on Valkyrie Profile (PSX, `valkyrie`, round 205): a 2026-08-18
claim that 25 character illustrations each show a visual cue matching that
character's independently-decoded class string (Llewelyn/"Archer" holds a
bow, Lezard Valeth/"Sorcerer" wears spectacles, one bust-only pose is
correctly "neutral, no weapon visible") had never been re-checked since.
A throwaway script re-decoded the SLZ-compressed tile-sprite command
stream + paired TIM straight from the disc, wrote fresh PNGs to the
scratchpad, and `Read` them directly — independently reproducing every
cited match, plus the one deliberately neutral case, with no dependency on
the original session's prose. This is the image-domain sibling of
`test-fixture-encodes-same-wrong-model-as-implementation.md`'s "written
from the same understanding as the decoder" trap: an oracle that is only
"what a human once said the picture showed" is exactly as stale as a
hand-typed test fixture, and costs nothing to refresh once the decoder
itself is already committed and the container format already solved.
