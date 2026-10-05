# Catalog/index adjacency is not proof of content grouping — verify each entry by content, not by position

**When it bites:** a directory/TOC/catalog has several consecutive entries
that *look* like they should belong together (same rough size class, same
content-type bucket from a classifier), and the plan is to treat "N
consecutive entries" as one logical unit (one character's expression set,
one animation's frames, one object's LOD chain) without checking each
entry's actual content individually.

Confirmed on Valkyrie Profile (PSX): a 42-image "sprite" TIM bucket was
assumed to fall into "11 consecutive TOC-slot groups of 3-4 images, each one
character's head at a different facial expression" — two groups (the first
two checked) really were exactly that, which made the pattern look solid.
Actually cropping and viewing the next group (`4812-4815`) found **4
completely different individuals**, not one character's expressions — the
true boundaries were irregular, several single slots were monster/NPC art
or non-facial content (armour fragments) with no relation to their TOC
neighbours at all, and the correct unit of comparison was the single entry,
not the chunk. Switching to per-entry matching against the known-character
reference set went from 3 confirmed identities to 11.

Rule: a directory/catalog's storage order groups entries by *when they were
authored or packed*, not necessarily by what they depict. A couple of early
confirming examples are not enough to lock in a chunk size — check a middle
or late chunk before writing up the grouping as a premise, and when in
doubt, verify every individual entry against the reference set rather than
one representative per assumed group.

Siblings: `shared-prefixes-at-guessed-stride-fake-animation-frames.md` (the
byte-level version of the same mistake — shared prefixes at a guessed record
stride, within one blob, read as animation frames).
