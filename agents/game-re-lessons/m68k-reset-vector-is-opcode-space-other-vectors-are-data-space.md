# On 68000, opcode-space addressing can resolve a pointer whose *target* still needs a data-space read

**When it bites:** a 68000 target distinguishes opcode fetches from data reads (CPS2 opcode encryption, an I/D bus split) and either (1) only part of the vector table at 0 looks plausible — the SSP/PC pair or the rest, but not both — or (2) a pointer resolved from the opcode-decrypted image (`movea.l`/`lea` immediate, PC-relative table) points at data that decodes as garbage.

## The underlying fact

On a real MC68000 (as modelled by Musashi, which MAME's core follows), RESET reads the initial SSP and PC via `m68ki_read_imm_32()` — an **opcode/program-space** read — while every *other* exception vector is read via **data space**. In a range that is "encrypted for opcodes, plaintext for data", the RESET pair needs the opcode transform and vectors 2+ do not, although they sit side by side.

More generally: a pointer fetched through the opcode bus decodes correctly from the opcode-decrypted image, but the bytes it points at are read by whatever instruction dereferences it. An ordinary data instruction (`move`, `movem`, arithmetic operand) sees the plain data image.

## Confirmed cases

- **D&D: Shadows over Mystara (CPS2):** bytes 0–7 gave `SP=0x00ff0e66, PC=0x00000350` only after opcode decryption; bytes 8+ gave an evenly spaced table of in-ROM addresses (`0x000285ec, 0x000285f8, 0x00028604, …`) only *without* it (loader-byteswapped data image). The wrong path garbles exactly one half — a checkable signature.
- **D&D: Tower of Doom (CPS2):** a palette-bank loader resolves `movea.l TABLE(pc,d0.w),a2` to `0x1cd3a0`, inside the encrypted range (`upper = 0x200000`). Decoding the palette from the decrypted-opcode image gave garbage (63–64 of 64 sampled bytes differed); the plain `ROM_LOAD16_WORD_SWAP` image (what `movem.l (a2)+,…` really reads) gave coherent colours.

## Fix

Classify every address by the instruction that *dereferences* it, not by where the pointer came from: opcode fetch → opcode-decrypted image; data read → plain data image. First check whether the target lies inside the encrypted range at all (outside it, both images are usually identical). If inside, diff the two images at the target — near-total disagreement confirms you must choose, and the correct one decodes to structured content.
