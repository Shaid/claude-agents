# On 68000, opcode-space addressing can resolve a pointer whose *target* still needs a data-space read

**When it bites:** decoding a 68000 target with a hardware/emulator-level
distinction between "opcode fetch" and "data read" (self-modifying-code
protection, an opcode-only encryption/decryption layer, an instruction
cache vs. data-bus split) — two situations: (1) the exception-vector table
at address 0 partially makes sense (some entries look like plausible
in-range addresses) and partially doesn't (specifically the very first two
entries: the initial supervisor stack pointer and initial PC), or vice
versa; (2) more generally, code resolves a literal ROM pointer via
opcode-space addressing (a `movea.l`/`lea.l` immediate, or a PC-relative
extension word — both fetched through the *opcode* bus and therefore
already correctly decrypted in an opcode-decrypted image) and then reads
*through* that pointer with an ordinary data instruction (`movem.l
(a2)+,...`, `move.w (a1),...`) — decoding that read's bytes from the same
opcode-decrypted image produces garbage specifically when the resolved
target address falls *inside* the opcode-encrypted range, even though the
pointer itself decoded fine.

## What went wrong / the underlying fact

On real MC68000 hardware, exception-vector-table *reads* are not all the
same kind of bus cycle. Per the Musashi 68000 core (the reference many
emulators, including MAME's own, model their 68000 core's behavior on):
the CPU's RESET sequence reads the initial SSP and initial PC via
`m68ki_read_imm_32()` — an **opcode/program-space** read, the same kind
used for ordinary instruction fetches — while every *other* exception
vector (bus error, address error, illegal instruction, autovectors, trap
vectors, ...) is read via the **data-space** read path instead.

This matters wherever a system distinguishes opcode-space and data-space
memory (CPS2's 68000 opcode encryption is the concrete case this was found
in, but any 68000 target with an instruction/data split needs the same
care): a byte range that is "encrypted for opcodes only, plaintext for
data" will have its RESET vector (SP/PC) subject to the opcode-space
transform, while the rest of its vector table is not — even though every
entry lives in the same small address range and looks superficially
uniform.

Confirmed on D&D: Shadows over Mystara (ddsom, CPS2): the first 8 bytes
(SP, PC) only produced a plausible address (`SP=0x00ff0e66,
PC=0x00000350`) after applying the opcode-space decrypt; bytes 8 onward
(vectors 2+) only produced a plausible, evenly-incrementing table of
in-ROM addresses (`0x000285ec, 0x000285f8, 0x00028604, ...`, +0xE bytes
apart) *without* decryption, read straight from the (loader-byteswapped,
undecrypted) data-space region. Applying the wrong path to either half
produced garbage for that half specifically, while the other half stayed
plausible — a strong, checkable signature of exactly this split.

Confirmed a second, more general form on the sibling D&D: Tower of Doom
(ddtod, CPS2): a real, confirmed-reachable palette-bank-load function
resolves a source pointer via `movea.l TABLE(pc,d0.w),a2` (opcode-space,
correctly decrypted) to ROM data-space address `0x1cd3a0` — which sits
*inside* ddtod's own encrypted range (`upper = 0x200000`). Decoding the
16-color palette bank at that address from the same decrypted-opcode image
produced high-entropy garbage (63-64 of 64 sampled bytes differed from the
plain, undecrypted data image at the same offset); re-decoding from the
plain `ROM_LOAD16_WORD_SWAP` data image (what the real `movem.l
(a2)+,...` data-bus read actually sees) produced coherent, plausible,
varied palette colors. The pointer's own resolution was never in question
— only the *bytes at the address it pointed to* needed the other image.

## The fix / the generalizable lesson

Don't treat "resolved via opcode-space addressing" as proof the *target*
bytes are opcode-space too. When a platform distinguishes opcode/program-
space from data-space memory, every literal address a decrypted opcode
stream hands you (vector table entry, PC-relative pointer-table entry,
`lea`/`movea` immediate) still needs its *own* read-path classification
based on what kind of instruction dereferences it — an opcode fetch there
needs the opcode-decrypted image, an ordinary data read (`move`, `movem`,
arithmetic operand) needs the plain, undecrypted data image, regardless of
which image the *pointer itself* came from or which side of any "upper
boundary" the pointer's own address falls on. Check whether the target
address is inside the encrypted range at all first (outside it, opcode and
data images are typically identical passthrough and the distinction is
moot); if it is inside, verify by diffing the two images' bytes at that
target address — a large, near-total byte disagreement there confirms
you're looking at the wrong one, and the correctly-classified image should
decode to plausible, structured content instead of garbage.
