# A pooled-instance spawner's own literal handler-install address is a stronger prologue oracle than back-scanning from a call site

**When it bites:** a function's start address rests only on back-scanning to something prologue-shaped, or to the nearest `jr $ra`/`rts`, especially on a fixed-width ISA. Also: bucketing many census hits by "nearest preceding prologue". Also: a handler/task function has 0 direct callers, or a corpus census for its address returns 0, and you're about to call it unreachable.

On MIPS and other fixed-width ISAs, two candidate starts a few instructions apart both disassemble cleanly, so "does it disassemble cleanly" tells you nothing. Every back-scanned landmark can lie. A plausible mid-function instruction looks like a routine start. A real `addiu $sp,$sp,-N` can still be late, because compilers hoist frame-independent loads (a `lui`/`lw` gate) above the stack adjust. A real `jr $ra` can be the *same* function's early return. A single prologue at the top of a long function can "contain" addresses that actually belong to the next function.

**Check / fix:**
- **Use the literal install as ground truth.** In pooled-instance / vtable engines (VP1, Parasite Eve actor packages, others), the spawner builds the handler address with `lui`/`addiu` immediately before `sw <addr>,0(inst)`. That literal names the entry exactly. Treat any back-scanned start as a hypothesis until a literal install/reference confirms it, or an unconditional transfer/return sits directly before it.
- **0 callers or 0 census hits:** run the literal `lui`/`addiu`-construction census for the exact 32-bit address *first*, not as a fallback. Then check whether the hit falls inside an **already-documented** function's bounded `[start,end)` before you go looking for a dedicated spawner.
- **A zero-hit census for an address is evidence the address is wrong** (off by a few, hoisted prologue, wrong base or segment) before it is evidence of unreachability. Real engine code is referenced somewhere.
- **Grep the project's `docs/` for every derived entry address** before you analyse it or write it up, even when you derived it correctly. Getting the address right doesn't mean you found it first.
- **Bucketing many addresses into functions:** forward-walk from the prologue to its real `jr $ra` (or cross-check a length already cited in the docs), and confirm every grouped address falls inside that span.
- **Back-scanning to `jr $ra` with no anchor:** use an iterative convergence resolver. From the nearest preceding `jr $ra`, forward-walk from its delay slot to that candidate's own end. If the target falls outside `[start,end)`, that `jr $ra` was an early return, so back up to the next-earlier one and repeat. The procedure verifies itself.

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`), the "First Aid" heal-over-time chain. A back-scan stopped at `0x800705dc` (`lbu`, branches, a jump). It disassembled cleanly and was read as "a caller-side helper". The spawner `fcn.80070790` installs the handler with a literal `lui/addiu` + `sw <addr>,0(instance)` naming `0x800705a4`, 14 instructions (0x38 bytes) earlier, where an ordinary `addiu sp,sp,-80; sw s2,…; addu s2,a0,zero` prologue sits. Starting from there changed the reading to "a per-instance tick handler taking the instance as `a0`".

**Variants (all `valkyrie`):**
- Hoisted load: a back-scan to `addiu $sp,$sp,-0x70` gave `0x8005ee04`, but the real entry is `0x8005edfc`, 8 bytes earlier (`lui $v0,0x8008; lw $v0,-0xda0($v0)`). The 0-hit census and its absence from the task table nearly led to an "unreachable" write-up. `dungeon-field-mechanics.md` § 20.5 already documented it as the chest task installed by opcode 204. A later round re-derived it correctly and still announced it as "never before cited".
- Prologue bucketing: 10 flag-test sites were attributed to one invented "party propagation" function. A forward walk to `jr $ra` matched a documented length, and only 6 of the 10 were inside it.
- Convergence resolver: it bounded 19 sites across 11 new functions. A second implementation matched with 0 deviations.
- Sibling installer: `0x8006623c` had 0 `jal` callers. The literal census found 2 hits, both inside the already-traced 1747-instruction `0x8005edfc`.

**History:** 6 recorded instances (`valkyrie`): full log in `_archive/spawner-install-literal-outranks-backscan-prologue.md`.
