# A byte-pattern census of an indexed-addressing instruction cannot identify what it operates on

**When it bites:** a census of an instruction encoding (`BTST #n,(An,Dn)`, `MOVE.B (An,Dn),Dm`, `sw reg,0x570(base)`), a text grep for a literal field offset (`43(A0)`), or a bit-immediate scan near a known field access has returned hits, and you are about to count them as accesses to one specific table/struct field.

Instruction bytes encode an offset and register numbers, not which table the base register points at. Byte-identical instructions — or any `+43` displacement — can touch unrelated structures. Identity lives in the instruction that loads the base (`LEA`/`MOVEA`/`lui+lw`/prologue argument), independently corroborated by the index stride (the table's record size).

**Check / fix:**
- For **every** hit, resolve the base register to its defining instruction and confirm the table; check the index stride matches that table's record size. Two agreeing signals is the bar; an unresolvable base is *unclassified*, not a match.
- **Automated lookback heuristics fail under idiom repetition**: a function that reloads a global context pointer many times will out-compete a one-time prologue definition of the real base. Widen lookback to the function start, or hand-check several hits' true defining instruction before trusting a negative (same fix as `nearest-preceding-immediate-is-not-dataflow.md`, for operand identity).
- **For bit-immediate censuses** (`andi`/`ori` `0x40`/`0x80`/`0xc0` near a field access), check which register the masking instruction actually writes/reads and that it was loaded from the target offset. Proximity is a candidate filter, never evidence — sibling fields often share small bit values.
- **Exhaustive provenance is a closure method**: when the hit set is small, resolving *every* hit (all write forms that can address the offset, e.g. `MOVE.B`/`ADDI.B`/`CLR.B`) upgrades "N candidates, none traced" to "confirmed absent".

**Canonical example:** War in Middle Earth (Amiga, `middilgard`): four byte-identical `08 30 00 00 08 00` (`BTST #0,(A0,D0.L)`) were reported as four tests of one inventory bit. Bases and strides: `0x0B06E` and `0x0F726` — `LEA -16772(A4)` (location+0x08), ×10 → location `regionFlags`; `0x0F41C` — `LEA -25094(A4)` (entity+0x10), ×38 → the real item bit; `0x10436` — `LEA -11124(A4)`, ×2 → combat force-slot word array. Three false positives.

**Variants:**
- *Text grep of an offset* — Vengeance of Excalibur (`middilgard`): ~120 writes to `43(A0)/43(A1)` in named gameplay functions all hit an item-list struct, none the VM's PC field.
- *Exhaustive closure* — Black Crypt (`crawl`): 19 write sites to `byte +0x07` across the 166 KB image all resolved (via `MOVEQ #type,D3` type-filter arguments) to other record kinds → feature confirmed dead.
- *Lookback mislabel* — Valkyrie Profile PSX: `sw s1,0x570(s0)` was the right hit, but `s0` (prologue parameter, ~200 instructions back) was labelled the battle context because the function repeats `lui/lw ctx` 252 times; the clean "no actor-relative writer" negative was wrong.
- *Shared bit values* — Valkyrie Profile PSX: `ori $v1,$v1,0x80` next to an `obj+0xe8` load actually set bit 7 of `obj+0xc6` (the kind byte).

Related: false-negative faces in `narrow-opcode-form-census-false-negative.md` and `bitfield-spans-multiple-addressable-bytes.md`; general fix `negative-from-addressing-root-not-shapes.md`.

**History:** 5 recorded instances (middilgard ×2, crawl, valkyrie ×2) — full log in `_archive/indexed-operand-needs-base-provenance.md`.
