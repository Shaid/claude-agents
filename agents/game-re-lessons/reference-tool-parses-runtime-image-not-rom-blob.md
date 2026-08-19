# A reference tool's struct layout may describe the runtime memory image, not the at-rest ROM blob

**When it bites:** transcribing a header/struct layout from a reference
implementation or doc whose *input is a memory image* — an SPC/PSF/VGM/GSF
rip parser, a savestate/RAM-map document, an emulator-side viewer — and
applying it to the at-rest ROM/disk blob that a loader *transfers from*.
Check what the game's own loader consumes vs. what it uploads before
trusting field offsets.

Confirmed on FFV (SNES, AKAOSNES V3, `ceres`): the song-header model was
transcribed from VGMTrans's `AkaoSnesSeq::parseHeader()` — which is
byte-accurate *for the ARAM image inside an SPC rip*. The ROM blob,
however, prepends a 2-byte transfer byte count that the 65816 upload loop
(`sound-main.asm` `@0242`-`@0271`: first word → the `dex2/bpl` loop
counter; upload starts at blob offset 2) consumes and **never uploads**.
The real at-rest header is 22 bytes (`[transferLen][scriptBase][8 track
ptrs][endAddr]`), not the uploaded 20. Reading every field 2 bytes early
resolved every track pointer ~57KB downstream into *other songs'* data —
and 46 of 72 songs rendered as complete silence in an otherwise-correct
real-hardware SPC700 renderer, misdiagnosed for two sessions as a
"slow-tempo bootstrap" driver mystery.

A loader-consumed length/count prefix is the classic shape, but the
general trap is the reference tool's **input kind**: post-load images have
had prefixes stripped, fields relocated, or blocks concatenated by the
transfer code. The fix is always the same — read the game's own
loader/uploader (often on the *other CPU* of a multi-chip platform) and
derive the at-rest layout from what it actually reads and skips.

**Corollary — agreeing consumers can share the wrong premise.** Every
consumer built on the same at-rest model (static event-stream scanners
*and* an emulated-real-driver harness executing the misplaced bytes)
corroborated each other with internally consistent results: a song's
observed 27.9s audio onset even "matched the model's prediction," because
the emulator was faithfully executing misresolved bytes whose leading
rests happened to be long. Cross-checking two consumers only verifies
what they *don't share*; the loop broke only by tracing the transfer
boundary (the 65816 uploader) that neither consumer touched. Bonus tell
that the model was wrong, visible earlier in hindsight: decoded "track
starts" were musically impossible (dangling `LOOP_END`s and ties as first
events) even though every byte decoded "cleanly."

Sibling lessons: `compressed-stream-start-offset.md` (stream starts after
a skipped region — here the skipped region was discovered via the loader,
not offset perturbation), `canonical-field-offsets-before-custom-header.md`
(check a known format's own field table first — here the "known format"
description itself was for a different representation), and
`rle-decode-succeeds-on-garbage.md` (why the wrong model still passed a
397k-event corpus walk with zero errors).
