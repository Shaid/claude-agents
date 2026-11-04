# A masked container header makes a code image invisible to every byte-shape search — find it from the outgoing module's exit path

**When it bites:** a whole mode image is *known* to exist — an ELF `PT_LOAD`
reservation with zero `filesz`, a slot-table row, a documented size — yet
after several passes nothing on the disc matches it by container magic, by
decoded-size match against the archive's own lengths, by overlay-header
shape, or by a keystream/zero-plaintext detector. The search keeps widening
the *scan*. Also bites when a read of two adjacent archive entries into one
sector-rounded buffer was dismissed as audio/SFX/voice because its indices
"weren't in the known population".

## The trap

Any publisher who obfuscates at all eventually masks **the header itself**:
a short LCG or XOR pass over the first N bytes of the pack/overlay header, a
key-table XOR over just the magic word, a per-pack seed byte — with a
*chained* (plaintext-feedback) cipher on the payload behind it. Each of your
detectors then fails for an independent reason:

- no container magic exists anywhere in the file, so a magic scan is blind;
- the declared decoded size is not readable, so a size match against known
  lengths cannot fire;
- the cipher is not an XOR stream, so a word-LCG keystream detector sees
  nothing;
- the first words are not a header shape, so an overlay-header classifier
  never triggers.

Every scan returns a clean, confident **zero — by construction, not because
the thing is absent.** And unlike compressed members in an indexed archive
(`compressed-container-members-invisible-to-magic-scan.md`, where the remedy
is "walk the directory instead"), there *is* no directory to walk: the
top-level header is the masked thing. Scanning harder in the same medium
cannot work, however many escalations you spend on it.

## Check / fix

Stop scanning bytes and attack it from the loader side.

1. **Enumerate the archive reads the mode-transition code issues** — the
   field/world engine's "enter battle" sequencer, the title loop's "start
   game", the minigame launcher. A read whose size is
   `roundup(entrySize(i) + entrySize(i+1), sector)` and whose buffer is then
   handed to the generic container/overlay decoder *with a slot address* is a
   code image, whatever its first bytes look like.
2. **Look on the exit path of the module being replaced, not in the resident
   loader.** This is the counter-intuitive half. A mode image that loads over
   the current module's own slot must be unmasked by the current module *as
   it leaves* — the decrypt loop sits in the main loop's exit branch a few
   dozen instructions before the `decode(buf, SLOT_ADDR)` call. A "who loads
   slot X" search of the resident executable finds nothing, because nothing
   resident does.
3. **Once one layer is off, the next layer's key table is usually in an
   already-decoded data file.** Compute `word0 ^ expectedMagic` (and
   `~(word0 ^ expectedMagic)`) for the suspect entry and `bytes.find` that
   across every blob you have already decoded — master/config data, the
   bootstrap module's own data section. A hit names the table *and* the
   index; then trace the pointer global (`RefsTo`) back to whatever fills it.
4. **Treat prior-pass labels on such reads as hypotheses.** "Sealstone SFX
   pair", "voice line" and friends attached to a read that was never traced
   to a sound API are the first thing to re-examine — the misfiled read is
   often already in your own notes.

## Canonical example

Valkyrie Profile 2 (PS2, `valkyrie`). Five escalations (three
`ghidra-disasm`, one `re-codebreaker`, one `re-oracle`) built root-based
negatives for the damage formula across every extracted module, plus
whole-disc scans for every known container/overlay magic and a size match of
the ELF's two zero-`filesz` reservations against every decoded archive
length — **all zero**. The answer was a two-layer mask, visible only from
code:

- the field engine's battle-entry sequencer read two adjacent TOC entries
  together into one sector-rounded buffer — a read already found in an
  earlier pass and written up as an SFX pair;
- its main loop's **exit branch** XORs the first entry's leading ~1.4 KB with
  a u16 LCG and decodes it over its own slot: that is the battle bootstrap,
  the only entry on the disc that unmasks to a valid container record, with
  header fields matching the smaller ELF reservation byte-exact;
- the bootstrap then XORs the second entry's first 14 bytes with a key in its
  own data, unlocks the pack magic via a 39-pair key table located by
  searching the already-decoded master data for `~(word0 ^ magic)`, and runs
  a chained word cipher seeded from a header byte. Member 0 decodes to the
  1.7 MB combat engine, matching the larger reservation with bss — and 40 of
  its functions write the current-HP field that no resident module wrote.

Written up in `docs/valkyrieprofile2/ps2/battle-logic.md` § 16, verified by
`tools/valkyrieprofile2/verify-battle-image-location.ts` (all checks pass,
6 null controls).

**Related:** `negative-from-addressing-root-not-shapes.md` is the general
rule this is the loader-side instance of — here the correct root for the
negative is "every archive read issued at a mode transition", not any byte
shape. `compressed-container-members-invisible-to-magic-scan.md` is the
sibling where a directory walk *is* the remedy.

**History:** 1 confirmed instance (valkyrie, VP2 PS2).
