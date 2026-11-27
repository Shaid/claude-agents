# Low handler coverage in an emulation census: suspect the harness before the game's gates

**When it bites:** you run many game handlers/scripts/overlay routines under an emulator for a behaviour or coverage census, a sizeable share of instructions is never reached, and the working explanation is "gated by story flags / passwords / items".

A run that hits an unstubbed draw or sound routine, a timing busy-wait, or a wait-for-key loop errors out or times out, and every instruction after that point counts as "unreached". In a coverage report that is indistinguishable from a real gate, and the gate story is plausible, so nobody checks.

**Check / fix:**
1. Log **why each run ended** — normal return, error (which address/routine), timeout (where the PC was spinning) — and tabulate it before interpreting coverage.
2. Stub graphics/sound leaves, shorten busy-wait delays (exploration runs only), and script returns for key-wait loops; re-measure.
3. Only the residue is a candidate real gate. Solve each one by setting the byte the first unreached compare reads, not by guessing story state.
4. Exploration runs must not record key scripts or inputs that solve protection/password gates into committed output (`generated-artefacts-from-game-code-carry-retail-text.md`).

Related: a frozen/blank run is often an unmodelled hardware wait (`harness-blank-output-is-unmodelled-hardware-wait.md`); a behaviour sweep can also miss per-entity main-loop calls (`sweep-harness-must-replay-main-loop-per-entity-calls.md`).

**Canonical example:** crawl MM1 (DOS, Unicorn 8086, `docs/mm1/dosega/game-rules.md` §5.2 correction 2026-11-26): ~14% of overlay event-handler code was labelled "gated"; most were harness stub bugs (graphics leaves, busy-wait delays, key-wait tails). Fixing them raised coverage 85.8% -> 94.6% and fully covered screens believed to be password-gated.

**History:** 1 recorded instance (crawl MM1, 2026-11).
