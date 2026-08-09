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
