# A driver-code blob's ARAM<->file delta only covers that blob's own address range

**When it bites:** you've confirmed a sound-driver (or any boot-DMA'd) code
blob's ARAM<->file-offset mapping from one anchor inside it (e.g. a
byte-exact constant-table match), and are about to apply that same delta to
an ARAM address found via a *different* pattern search that turned out to
sit outside the code blob — a separately-uploaded data table referenced by
its own entry in the same boot upload table.

A boot loader that DMAs several independent blocks to different fixed ARAM
destinations (driver code, sample pointers, sample data, ADSR, tuning — the
classic AKAOSNES-family `InitTfrSrcTbl`/`InitTfrDestTbl` 6-entry shape) does
**not** store those blocks contiguously in ROM in destination-address order.
Each block has its own, independently-placed ROM source region (its own
2-byte length-prefixed header), so `fileOffset = codeBlobDelta + aramAddr`
is only valid for addresses that fall *inside the code blob's own declared
length* — applying it to an address belonging to a different uploaded block
silently returns a plausible-looking but wrong file offset (confirmed on
FFV/AKAOSNES V3: applying the driver-code delta to `addrTuningTable`/
`addrADSRTable` — ARAM addresses found via a *different* SPC700 signature
pattern than the one that anchored the delta — landed ~0xA2 bytes off; only
one other block, `SfxLoopStart`, coincidentally matched, purely because its
ROM bytes happened to sit link-adjacent to the code blob, not because the
delta genuinely applied).

**Fix:** treat "this address is a confirmed real address" as scoped to
*one* uploaded block. For every other ARAM address found (tuning, ADSR,
sample pointers, etc.), locate its **own** source-table entry in the boot
upload table (`InitTfrSrcTbl`-equivalent: 6×2-byte ROM-relative source
offsets, one per destination) and resolve `fileOffset = segStart + srcOffset
+ 2` (skipping that block's own length header) directly — don't reuse a
delta derived from a different block, even one that "looks" like it should
be nearby.

A cheap way to confirm you have the right per-block resolution, not just a
plausible one: find a **second, independent** anchor inside the *same*
block (a different pattern match, not the one used to size the block) and
check it lands byte-exact at the predicted position — e.g. AKAOSNES's own
note-duration table, found via a completely different SPC700 signature than
the opcode-length table used to anchor the delta, landing with zero
deviation confirms the whole mapping is right, not just self-consistent.
This is a stronger, cheaper oracle than "the address is in a plausible
range" and reusable for any AKAOSNES-family game (confirmed independently
for both FFV/V3 and FFIV/V1 this way).
