---
name: radare2-amiga
description: Use when radare2 is the right tool for the job — interactive 68k disassembly, data xrefs, hex dumps, byte-pattern search. Covers AmigaOS hunk format and SAS/C small-data addressing conventions that radare2 needs to interpret Amiga executables correctly. Use ONLY when Radare2 is required for step-through analysis, cross-references, or raw memory inspection that IRA cannot provide.
---

# Radare2 on Amiga Binaries

## The Problem

Radare2 does not natively understand the AmigaOS `loadseg()` hunk executable
format. When opened as-is, radare2 either misidentifies the file type or
reads garbage at offsets where valid code exists. The MCP radare2 tools
have additional issues where the hexdump returns all `FFFF` bytes even when
the file contains valid data.

## Workaround: Extract Hunks First

The reliable approach is to **extract each hunk to a separate raw binary file**
before opening in radare2. Check whether the current project already has a
hunk parser before writing your own — e.g. middilgard's `parseHunks()` in
`src/assets/formats/exe-data.ts` — and adapt the import below to wherever
it actually lives; if the project has none yet, write one against the
AmigaOS Hunk Format Reference just below and add it to the project's shared
decode library (see the `game-re` agent's Output-conventions section) rather
than as a one-off inline script:

```typescript
import { parseHunks } from './src/assets/formats/exe-data.ts'; // adapt path
import { readFileSync, writeFileSync } from 'fs';

const exe = new Uint8Array(readFileSync('path/to/executable'));
const { code, data } = parseHunks(exe);

writeFileSync('/tmp/code-hunk.bin', code);
writeFileSync('/tmp/data-hunk.bin', data);
```

The CODE hunk is the primary target for disassembly. The DATA hunk contains
tables, pointer chains, and small-data trampolines.

## Loading the Extracted Hunk

```bash
# Load the extracted CODE hunk as raw m68k binary
r2 -a m68k -b 32 -q -n -c 'pd 20 @ 0x0' /tmp/code-hunk.bin

# Key flags:
#   -a m68k    Set architecture to Motorola 68000
#   -b 32      Set address width to 32-bit
#   -n         Skip binary header parsing (critical for raw hunk data)
#   -q         Quiet mode (cleaner output for scripting)
```

The `-n` flag is **essential**. Without it, radare2 tries to parse the raw
bytes as ELF/PE headers and produces garbage.

**Do NOT use the MCP radare2 tools for initial analysis.** The MCP server
appears to have issues reading Amiga binaries correctly (returns `FFFF` at
all offsets). Use the CLI directly instead.

## AmigaOS Hunk Format Reference

All multi-byte fields are **big-endian** (Amiga 68000 byte order).

```
Header:  magic 0x3F3 (u32)
         string table size (u32)
         string table entries (u32 × size)
         number of hunks (u32)
         first hunk index (u32)
         last hunk index (u32)
         hunk sizes (u32 × num_hunks, masked with 0x3FFFFFFF, ×4 for bytes)

Per hunk:  hunk type (u32)
           0x3E9 = CODE
           0x3EA = DATA
           0x3EB = BSS
           0x3EC = RELOC32
           0x3F2 = HUNK_END
           For CODE/DATA: word count (u32), then data bytes
```

## SAS/C Small Data Model

Applies **if** the target was compiled with SAS/C using the small data
model — common for Amiga games of this era (e.g. Melbourne House titles),
but confirm it for your target rather than assuming it; a `JSR offset(A4)`
pattern in the disassembly is the tell. Key addressing conventions when it
applies:

- **A4** = base register for the small data section (DATA hunk end)
- Data accesses use `offset(A4)` with signed 16-bit displacements
- Function calls use `JSR offset(A4)` which jumps through **trampolines**
  (JMP instructions) stored in the DATA hunk's small-data area
- The IRA disassembler labels these as `SECSTRT_0-offset(A4)` where
  `SECSTRT_0` is the small-data section label

### Computing A4-relative addresses

```
A4 = DATA_hunk_start + 0x7FFE   (SAS/C convention)

To find what a disassembly label references:
  label = SECSTRT_0 - N
  A4-relative offset = A4 - N = (DATA_start + 0x7FFE) - N
  DATA hunk offset = 0x7FFE - N

Example: SECSTRT_0-32172(A4)
  DATA offset = 0x7FFE - 0x7DAC = 0x0252
```

### Trampoline indirection

Function calls via `JSR offset(A4)` don't jump directly to code. They
jump to a location in the DATA hunk that contains a `JMP.L <addr>`
instruction (opcode `4E F9`). To find the actual function:

1. Compute the DATA hunk offset from the A4 displacement
2. Read the 6-byte `JMP.L` instruction at that offset: `4E F9 xx xx xx xx`
3. The target address is the 4-byte absolute address following `4E F9`
4. If the target is in the CODE hunk's virtual address space, subtract the
   CODE base to get the file offset for disassembly

```javascript
// Find actual function address from trampoline
const trampolineOffset = 0x7ffe - displacement; // DATA hunk offset
const opcode = data.getUint16(trampolineOffset);
if (opcode === 0x4ef9) {
  const targetAddr = data.getUint32(trampolineOffset + 2);
  // targetAddr is a virtual address; map to CODE hunk offset
  // using the load address from the hunk header
}
```

## m68k Instruction Quick Reference

| Pattern | Meaning |
|---------|---------|
| `4E 55 xx xx` | `LINK.W A5, #imm16` — function prologue |
| `4E 5D` | `UNLK A5` — function epilogue |
| `4E 75` | `RTS` — return |
| `4E F9 xx xx xx xx` | `JMP.L <addr>` — absolute long jump (trampoline) |
| `4E AC xx xx` | `JSR (d16, A4)` — small-data function call |
| `2F xx` | `MOVE.L Rn, -(A7)` — push parameter |
| `48 78 xx xx` | `PEA.L #imm.w` — push immediate |
| `4F EF xx xx` | `LEA.L (d16, A7), A7` — clean up stack |
| `06 40 xx xx` | `ADD.W #imm, D0` — add immediate to D0 |

**Reading `MULU`/`MULS` as record-size disclosure:** a `MULU #imm,Dn`
immediately before an indexed address computation (feeding a `LEA`/`ADD.L
Dn,An`) is very commonly `index × record_size` for a struct-array lookup —
the immediate operand *is* the record size, letting you infer a struct's
byte length without ever finding its definition. Cross-check against the
struct fields you can already identify from other reads/writes at that
base address.

### Searching for functions

Since radare2 can't auto-detect functions in raw hunk data, search for
known instruction patterns:

```bash
# Find LINK.W A5, #-8 (function prologue with 8-byte frame)
r2 -a m68k -b 32 -q -n -c '/x 4e55fff8' /tmp/code-hunk.bin

# Find all RTS instructions
r2 -a m68k -b 32 -q -n -c '/x 4e75' /tmp/code-hunk.bin

# Find JMP.L instructions (trampolines / far calls)
r2 -a m68k -b 32 -q -n -c '/x 4ef9' /tmp/code-hunk.bin
```

### Cross-referencing with the IRA disassembly

Check the current project's `docs/` for existing annotated IRA `.asm`
output before disassembling from scratch (see the `ira-disasm` skill for how
these are produced and kept current). Example from middilgard:
`docs/WarInMiddleEarth.asm` (WIME, primary), `vengeance.asm`,
`conan-game.asm`, `conan-loader.asm` — your project's file(s) will have
different names.

Use the IRA labels (e.g., `LAB_0A11`) to find functions, then locate them
in the CODE hunk by searching for their instruction byte patterns.

### Mapping IRA line numbers to CODE offsets

IRA disassembly does not directly map line numbers to CODE hunk offsets.
To find a function's CODE offset:

1. Read 2-3 unique instructions from the IRA disassembly at the target label
2. Convert to byte pattern (e.g., `LINK.W A5,#-8` = `4E 55 FF F8`)
3. Search the extracted CODE hunk for that pattern
4. The match offset is the function's position in the CODE hunk

```python
# Python example: find function by instruction pattern
import struct
code = open('/tmp/code-hunk.bin', 'rb').read()
# LINK.W A5, #-8 followed by CLR.B -5(A5)
pattern = bytes([0x4E, 0x55, 0xFF, 0xF8, 0x42, 0x2D, 0xFF, 0xFB])
offset = code.find(pattern)
print(f'Function at CODE+0x{offset:x}')
```

## DATA Hunk Analysis

The DATA hunk contains tables accessed via A4-relative addressing.
To analyze it:

```javascript
// Extract and analyze DATA hunk
const { data } = parseHunks(exeData);
const dv = new DataView(data.buffer);

// Read A4-relative values
// A4 points to data + 0x7FFE
const A4 = 0x7ffe;
function readA4(offset) { return dv.getUint16(A4 - offset); }
function readA4L(offset) { return dv.getUint32(A4 - offset); }
function readA4B(offset) { return data[A4 - offset]; }

// Find pointer chains (scene descriptors, etc.)
function followPointerChain(baseOffset, maxEntries = 20) {
  const ptr = dv.getUint32(baseOffset);
  const offsets = [];
  for (let j = 0; j < maxEntries; j++) {
    const entry = dv.getUint32(ptr + j * 4);
    if (entry === 0) break;
    offsets.push(entry);
  }
  return offsets;
}
```

## Troubleshooting

### "All FFFF in hexdump"

The MCP radare2 tools may not read Amiga binaries correctly. Always use the
CLI with extracted hunk files instead:

```bash
r2 -a m68k -b 32 -q -n -c 'px 16 @ 0x0' /tmp/code-hunk.bin
```

### "No functions found"

Expected for raw hunk data. Functions must be located manually via byte
pattern search (see above). Use `af+` to define functions once found:

```bash
r2 -a m68k -b 32 -q -n -c 'af+ 0x101f2 LAB_0A11; pdf @ LAB_0A11' /tmp/code-hunk.bin
```

### Wrong disassembly

If radare2 shows incorrect instructions, verify you're loading the correct
hunk at the right offset. The CODE hunk typically starts at file offset
`0x20`-`0x30` (after hunk headers). Use the `parseHunks()` function to
get exact offsets.
