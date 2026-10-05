# A traced-but-unnamed type/enum value can be corroborated by the *set of named places its carrier records occur in*

**When it bites:** an enum, type byte, flag or opcode has had its handler
fully traced — you know exactly which fields it writes and which flags it
sets — but the plain-English *label* is still a guess ("a drag volume? water?
a conveyor?"), and there is no external oracle, no in-game string, and
nothing in the code that names it. Especially for per-level/per-room data,
where the value is authored content rather than engine plumbing.

**Variant — naming a whole screen/feature, not an enum value:** when the
open item is "what is this screen/mode" (an anonymous thumbnail grid, a
menu), the carrier is the screen's own draw list. UI-widget list records
(a type byte + a string-table id + x/y, drawn by a shared widget renderer)
resolve through the project's already-decoded string bank to the game's own
labels for the screen, its rows and its per-item prompts — cheaper and more
authoritative than inferring the feature from its data. Valkyrie Profile
(PSX, `valkyrie`): the lists drawn for a 7×5 grid of character thumbnails
resolved to "Sound Mode" → "Voice Collection" → "Open voice", naming the
title screen's voice-collection artwork viewer from its own text, and the
grid's per-character table order then matched the game's roster with 22/22
agreement against an earlier pass's independent by-eye identifications.

**Variant — naming a whole ASSET (a video/audio/picture clip with no
on-disk title at all) via its own direct trigger, not a corroborative
occurrence set:** when the "carrier" isn't an ambiguous enum value spread
across many records but a single asset instance, and there is a confirmed
*direct* trigger relationship (a scene-script instruction that names this
exact clip's own resource id) rather than a loose semantic association,
the join can be **confirmed**, not merely corroborated — because it isn't
inferring meaning from thematic coherence, it's reading off which specific
room's script plays this specific clip. Valkyrie Profile (PSX, `valkyrie`):
61 STR/FMV video clips per disc have no title string anywhere on disc
(confirmed even at the code level — a debug menu that could have printed
one instead renders a bare `sprintf("%d", elem)` integer). But every
dungeon-range clip is played by a specific room's scene script (a direct
opcode naming the clip's own TOC slot, or an opcode loading its
`slot - 1` companion resource), and that room already has a real in-game
name from an unrelated, already-decoded table — joining "which room(s)
trigger this clip" to "that room's own name" named 87/92 clips across both
discs with a real location, reusing exactly the same room-name tables an
earlier pass had used to name a totally different asset class (battle-arena
backgrounds, via their own binding room). One clip's trigger set
**disagreed** across its two mechanisms (a direct call from one room, a
companion-load from an unrelated other room) — correctly left unresolved
rather than forced to one answer, the same "hold the label" discipline as
the enum-value case below, just decided by literal disagreement rather than
thematic incoherence.

## The technique

Join each enum value's **carrier records** against a name table the project
has already extracted (room names, area names, stage names, map labels), and
look at the resulting occurrence set. A rare value that appears in only a
handful of *thematically coherent* named places has effectively named itself,
and the query costs one pass over data you already parse.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), the room collision-primitive
type byte. Nine values, `0..8`; the engine special-cases exactly four, and
each special handler was traced to the actor flag it sets. Two of the four
were already self-evident from the flag alone (type 4 sets the documented
"on a ladder" bit, type 6 the documented "holding a ledge" bit). The other
two only had mechanism, not meaning — type 8 halves horizontal velocity and
clamps the actor inside its own X span, which could be a dozen things.
Joining its 11 carrier rooms to the game's own room-name bank gave **three**
locations: *Nethov Swamp*, *Dark Tower of Xervah (the stomach)* and *Former
Salerno Test Facility*. One of them is literally a swamp, and all three are
hazard/terrain-themed — "wade slowly through, can't leave the strip" stops
being a guess.

Two things make this stronger than it first looks:

- **It pairs with a geometry census as a second, independent signal.** Median
  bounding boxes over the same corpus gave type 4 as 32 × 242 px and type 6 as
  240 × 5 px — tall-and-thin and wide-and-flat, exactly a ladder and a ledge
  lip. The disassembly, the geometry and the occurrence set are three unrelated
  derivations; nothing makes them agree unless the reading is right.
- **The negative case is as informative as the positive one.** Type 5's three
  locations were *Sunken Shrine*, *Eroded Caves of Thackus* and *Karakuri
  (Clockwork) Mansion* — two water dungeons and one machine dungeon. That is
  consistent with a drag/current volume but does **not** discriminate water
  from conveyor, so the label stayed an explicit hypothesis in the write-up
  while the mechanism stayed confirmed. A non-coherent occurrence set is a
  signal to *hold* the label, not to force one.

## Where it applies, and the confidence it earns

Any value space whose instances live in per-level data and whose levels have
names: collision/terrain types, trigger-volume kinds, spawn-table classes,
tile attributes, audio-zone ids. The prerequisite is usually already met —
projects that have got this far have normally already decoded a name/label
bank for the UI or the map screen, so this is reuse, not new work.

Report the result as **corroborated**, not confirmed, for the enum/screen
cases: the mechanism is confirmed by disassembly, the English noun is
inferred from thematic coherence across several occurrences. That
distinction matters downstream — a reimplementation must copy the traced
behaviour exactly and is free to disagree about what to call it. The
direct-trigger asset variant is the exception: when every triggering
instance names the exact same target unanimously, that IS a confirmed join
(not an inference), and disagreement across triggers is the signal to
report "unresolved" rather than downgrade to "corroborated." Related:
`domain-archetype-plausibility-oracle.md` (same "does this match the
content's own world" move, for licensed stat blocks),
`cross-table-outlier-corroboration-without-external-oracle.md` (same
no-external-oracle situation, for a single ID rather than an enum),
`plausible-render-not-semantic-label.md` (the failure this guards against —
writing a confident noun off a plausible-looking output).
