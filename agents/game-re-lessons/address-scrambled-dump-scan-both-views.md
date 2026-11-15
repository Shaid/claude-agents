# Address-scrambled dumps hold two layers in two byte orders: scan both views

**When it bites:** a ROM is address-line scrambled (MAME `rom[i] = raw[bitswap(i, …)]`) and you run `strings`, entropy or printable-run scans on only the descrambled image (or only the raw file), then call the incoherent fragments "filler" or noise.

The board wiring applies the address scramble to the bytes the game actually uses. Unused EPROM space often keeps whatever the EPROM programmer's buffer held, written in **physical** order. So the dump holds two layers: program data that is coherent only after descrambling, and leftover content that is coherent only in the raw file. Each view shows the other layer as short broken fragments (runs of 2^k bytes matching the low address bits the swap leaves alone), which look like garbage.

**Check / fix:**
- Count printable runs of 16 bytes or more, and find the longest run, in **both** views. A multi-KB run in either view is real content.
- Leftover listings (`LOC OBJ LINE SOURCE` columns, commented source, `Assembly Complete`, Intel-HEX `:10…` records) name routines, RAM and shared-RAM fields, and handshake protocols: a strong **semantic** oracle.
- Before using a listing's object bytes as a **byte** oracle, search for them in the descrambled image (re-applying any opcode substitution table). The listing may come from a different build than the shipped program.

**Canonical example:** kolbold `ga2` (Sega System 32), V25 protection ROM `epr-14468-02.u3`. The raw file has 35,720 printable bytes in runs ≥ 16 (longest 6,367 B at `file+0xC400`): a `uPD70320 Assembler V3.10 … 01 Sep 92` listing with procedures such as `RW22` ("V25 read/write check") and `WRITE_EVENT3`. The game's handshake string `wake up! GOLDEN AXE The Revenge of Death-Adder!` is coherent only after MAME's `bitswap<16>(i,14,11,15,12,13,4,3,7,5,10,2,8,9,6,1,0)`. The listing's object bytes (re-encrypted through `ga2_opcode_table`) had 0 matches in the descrambled image: use it for names, not bytes.

**Related:** `file-named-dummy-may-hold-real-leftover-content.md` (the same "leftover is real" idea for named padding files on discs, with no byte-order twist).

**History:** 1 recorded instance (kolbold ga2, 2026-11).
