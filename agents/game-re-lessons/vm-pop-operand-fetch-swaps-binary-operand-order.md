# In an accumulator VM, a stack-pop operand fetch can swap a binary operator's operand order

**When it bites:** a reimplemented script VM's `acc OP operand` steps behave inverted only when the operand is a stack pop (`opile`/`pop`/`pull`) — edge clamps that never fire, a bound that runs to the region edge — and the symptom has been rationalised as genuine engine behaviour ("source-confirmed quirk").

In two-register evaluators (accumulator D7, scratch D6) each binary operator typically does `D6 = D7; fetch operand into D7; D7 = D6 OP D7`. If the pop operand's own fetch is `D7 = D6; D6 = *sp++`, then `acc OP[pop]` computes `popped OP acc`, not `acc OP popped`. Commutative ops (`+`, `*`, `&`, `|`, `==`) hide it; `>`/`<`/`-`/`/`/`%` invert.

**Check / fix:**
1. For each operand kind, read the operand-fetch routine, not just the operator body, and track where it leaves the old accumulator.
2. Census which non-commutative operators actually take a pop operand in the corpus — usually a handful of sites, so the bug hides behind a mostly-correct interpreter.
3. Test them against an invariant the game must satisfy (e.g. a view scan must be symmetric about the viewer).

**Canonical example:** crawl, Silmarils ALIS (Ishar 1-3, Crystals of Arborea; reference `maestun/alis` `opernames.c` `opile`: `D7 = D6; D6 = *acc++`). The only non-commutative pop uses were four `osup[opile]` view-edge clamps per location script; implemented as `acc > popped` they ran backwards, one lateral scan bound stuck at the region edge (183 cells read instead of a 48-cell symmetric wedge). A prior session had documented it as a residual engine quirk. Fixed in all 13 location scripts of 4 games.

**History:** 1 instance (crawl/Ishar, 2026-11-13).
