# A CPU register stored in an `Int32Array` reads negative for addresses >= 0x80000000, and every downstream unsigned check silently misfires

**When it bites:** writing (or extending) a scoped CPU interpreter that
keeps registers in a `Int32Array`/`Int32`-typed field for speed, on any ISA
whose real addresses can carry the sign bit (PSX/PS2 MIPS `0x8000_0000`+
kernel-segment addresses, 68000 addresses above `0x8000_0000`, any 32-bit
address space at all really) — a register value read straight out of that
array and used as a `pc`/memory address produces a *negative* JS number,
and every later `addr >= base && addr < base + len`-style unsigned range
check on it fails, even though the value is a perfectly valid, in-range
address.

Confirmed on Valkyrie Profile (PSX): a scoped MIPS R3000A interpreter
(`tools/valkyrieprofile/mips-interp.ts`) stored `regs` in an `Int32Array`.
After a `jr $ra`-simulating assignment `this.pc = this.regs[31]`, every
subsequent memory access threw `unmapped address 0x800387dc` — a real,
in-range overlay address — because `regs[31]` had been read back as
`-2145616420`, not `0x800387dc`. Worse, the thrown address wasn't even the
one that actually faulted first: JS's console/template-literal hex
formatting of a negative number produces a *different*, wrong-but-plausible
hex string, so the error pointed at a PC several instructions past the real
fault, actively misleading the first debugging pass.

**The fix, once, at the boundary — not at every call site.** Don't sprinkle
`>>> 0` at each place a register is read; normalize inside the single
function that turns an address into a memory access (`MemMap.find()`/
equivalent), and also on every direct `this.pc = <register>`-style
assignment:

```ts
private find(addrIn: number): { region: MemRegion; addr: number } {
  const addr = addrIn >>> 0;               // <-- the whole fix
  for (const r of this.regions) {
    if (addr >= r.base && addr < r.base + r.bytes.length) return { region: r, addr };
  }
  throw new Error(`unmapped address 0x${addr.toString(16)}`);
}
```

and `this.pc = target >>> 0;` at every place `pc`/`ra` gets assigned from a
register. This generalizes past MIPS: any hand-rolled interpreter/emulator
core in JS/TS that stores registers as signed 32-bit integers (for
performance, or because `Int32Array` was the obvious typed-array choice)
needs the identical fix wherever a register value crosses from "CPU value"
to "memory address" — including PC, base+offset effective-address
computation, and any table-lookup keyed by a register value.
