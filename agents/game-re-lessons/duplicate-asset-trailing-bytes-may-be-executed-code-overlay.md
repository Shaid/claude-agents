# "Leftover code" trailing a duplicate/reused data-file asset may be a real, deliberately-executed overlay

**When it bites:** a data-file asset (an animation, image, or other
resource format with a confirmed codec) turns out to be byte-identical to
a sibling asset for its whole declared payload, plus some extra trailing
bytes that disassemble as plausible machine code — and that asset is
*not* reachable from the subsystem's own already-traced consumer table
(e.g. it sits one slot past the last valid index, or its index is
otherwise excluded). The natural, cheap conclusion is "authoring residue"
or "a leftover fragment from a build step" — check for a second, separate
consumer before writing it off.

Confirmed on Reunion (Amiga AGA, `methanoid`): `spwar/SPANIM22.ANM` (an
`EFT!ANIM` animation) is byte-identical to `SPANIM14.ANM` for its whole
19,612-byte declared payload, then carries 1,692 extra bytes previously
documented as "unrelated leftover 68k code — authoring residue." It's
also the one file in its family not reachable from the already-traced
21-entry animation-selection table (its asset-table index sits exactly
one slot past the table's valid range, structurally unreachable via the
normal random-pick call). Both facts made "residue" look decisively
correct. A grep for the file's own literal asset-table index as an
immediate operand ANYWHERE else in the disassembly — a five-minute check
— found a real second load site: `MOVE.W #<index>,D0` / generic-loader
call, followed immediately by `JSR <payloadLength>(A0)` — a jump directly
into the just-loaded buffer at the exact byte offset where the "residue"
begins. Disassembling that offset (with a real disassembler, not just
eyeballing hex) showed genuine, valid machine code (`OpenLibrary`/`Open`
calls implementing a save-file routine), not garbage.

**Why this is a good hiding spot, and why it's easy to miss.** The
resource is genuinely a real animation (or texture, or sound) for the
bulk of its content, so every ordinary content-driven check (does it
decode? does it look right rendered/played?) passes cleanly. The "extra
bytes past the declared payload" pattern reads exactly like a dozen
mundane explanations (build artifact, unused draft frame, padding) that
are individually far more common than "hidden code overlay," so it's
easy to stop investigating once ANY plausible-sounding explanation
presents itself — especially when, as here, the asset is *also*
excluded from the normal consumer table, which looks like independent
corroborating evidence for "unused" when it's really just evidence that
this resource has a *different* consumer than the one already traced.

**The check, generalized:** before calling trailing bytes in a
duplicate/reused/oddly-excluded asset "residue," (1) grep the whole
disassembly for a literal immediate load of that exact asset-table
index/resource ID outside the already-traced normal consumer, and (2) if
found, check whether the call site does anything with the loaded buffer
beyond the ordinary decode-and-display path — specifically a direct
`JSR`/`CALL`/computed-jump into the buffer at or past the known real
payload's length. A generic asset loader used as a "load this blob into
RAM" primitive followed by a jump into it is a strong, cheap-to-spot
signal of a deliberately hidden native subroutine, independent of
whether the surrounding bytes "look like" residue.

Sibling lesson: `proven-residue-does-not-bound-region-start.md` (a
different failure shape — genuine residue found at one offset doesn't
bound how much *structured* data precedes it in the same region). This
lesson is about "residue" being not residue at all, but a second,
separately-triggered live consumer.
