# "A jump table ends at its lowest target" silently truncates tables whose first entry is a shared handler placed before them

**When it bites:** a recursive-descent tracer, disassembler script or static recompiler sizes a PC-relative word jump table as "up to the lowest target seen so far" (on the assumption that code starts where the table ends). Sub-state tables of state-machine objects often begin with entries pointing at a *shared* handler earlier in the routine (a negative offset). That entry is the lowest target, so the table is cut after one entry and every other sub-state is never traced or compiled.

The damage spreads: any random-state test generator that reads valid `(state, sub-state)` ranges from the same truncated tables samples a narrower space than "all states verified" claims. Per-routine oracle tests pass while whole handlers are missing.

**Check / fix:**
- Bound a table with the lowest **forward** target over all tables and labels after it, not with any target.
- Compile each extra candidate entry only if it decodes cleanly, uses supported instructions, and does not overlap an instruction decoded at another alignment. Process tables in address order, so a spurious backward pointer into the middle of another handler's instruction cannot beat the real handler.
- Make un-compiled targets **throw** at dispatch ("no label at …") instead of no-op, so a truncation shows up the first time it is reached.
- When a verification campaign takes its input ranges from the analysis it verifies, count the entries that analysis may have dropped. Run at least one end-to-end chained-frame scenario per subsystem: real game flow reaches states the generators cannot name.

**Canonical example:** kolbold `ddsom` (CPS2, 68000 → TypeScript recompiler). An end-to-end consecutive-frame run hit sub-state 2 of Goblin family 2 state 0 → "no label at 0x72ffc". Per-routine random-state oracle tests had passed for weeks because their state ranges came from the same truncated tables. The fix needed three parts together: `bra`-table sites, a speculative table pass in address order, and exact sizes for two tables.

**History:** 1 recorded instance (kolbold ddsom, 2026-11).
