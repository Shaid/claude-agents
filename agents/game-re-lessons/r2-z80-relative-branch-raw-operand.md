# radare2's z80 disassembler shows a `jr`/`djnz`'s raw displacement byte as the operand text, not the resolved branch target

**When it bites:** disassembling a Z80 binary with `radare2 -a z80`
(arcade sound CPUs are the most common target — MAME-format ROM sets
routinely bundle a Z80 `audiocpu` region alongside the main CPU) and
reading a `jr`/`jr cc`/`djnz` instruction's mnemonic text at face value to
figure out where control flow goes next, even after running `aa`
(analysis) first.

radare2 6.1.9's z80 plugin prints these instructions' operand as the raw
signed-displacement byte from the opcode bytes, formatted as if it were an
absolute address (`jr 0x7e`, `jr nz, 0xca`, `djnz 0xf8`) — it is not. The
real target is `pc_after_instruction + signed_displacement`, computed the
normal Z80 way; the displayed hex text is just the unsigned rendering of
that one signed byte. This is easy to miss because the output *looks*
exactly like a resolved target the way r2 shows one for absolute jumps
(`jp nn`, `call nn`) — nothing in the mnemonic text flags it as
unresolved, and running `aa` first (which does correctly build the
function's flow-graph arrows internally) doesn't fix the *displayed text*.

Concrete example (Capcom CPS2 `ddsom` Z80 sound driver, `audiocpu` region,
address `0xb`): opcode bytes `18 7e` disassembles as `jr 0x7e`. Read
literally, that looks like a jump to address `0x7e`. The real target,
computed from the actual signed displacement (`0x7e` = +126, PC after the
2-byte instruction = `0xd`): `0xd + 126 = 0x8b` — a full 13 bytes past the
address the raw text suggests. In this case address `0x7e` happened to
also contain valid-looking code (an embedded ASCII version string mid-ROM
resynchronizing into real code a few bytes later), which made the
misread nearly invisible: linear disassembly from the wrong address
`0x7e` still eventually reached the real target `0x8b` by coincidence of
instruction-length alignment, hiding the bug until the target was
independently recomputed and checked byte-for-byte.

**Fix:** never trust a `jr`/`jr cc`/`djnz` instruction's displayed operand
as an address. Recompute the real target yourself from the two raw opcode
bytes (`target = address_after_instruction + signed(displacement_byte)`;
Python: `disp = disp_byte - 256 if disp_byte >= 128 else disp_byte`), and
verify it by checking that the bytes at the computed target actually
decode as the expected code (not garbage/mid-instruction). r2's internal
flow-graph arrows in `pd`'s box-drawing gutter (`┌─<`/`└─>`) *are* computed
from the real resolved target and can be trusted as a secondary check —
it's specifically the inline mnemonic text that's misleading. Absolute
`jp`/`call nn` operands are unaffected (they're genuinely absolute
addresses already).