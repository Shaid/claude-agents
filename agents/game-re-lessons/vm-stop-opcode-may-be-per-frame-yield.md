# A VM "stop" opcode may be a per-frame yield — a CFG walk that ends paths there hides live code

**When it bites:** a reachability walk over script bytecode says some resource/state is never touched ("no palette load ever reaches slot 8"), and the walker's successor model ends every path at a `stop`/`halt`/`end`/`sleep`/`wait`-named opcode.

Game script VMs commonly run each script for one frame until it yields; the "stop" opcode just clears a running flag, and the per-frame loop resumes the script at the saved pc on the next tick. Everything after it is ordinary straight-line code (init on tick 1, palette/state setup on tick 2, then an animation loop). A walker that treats the opcode as terminal never reaches it, and every negative built on that walk is void. (The opposite failure — a linear scan finding unreachable hits — is `false-positive-bytecode-hit-without-cfg-reachability.md`.)

**Check / fix:**
1. Read the reference/original interpreter's handler for each terminal-looking opcode: does it destroy the task, or merely clear `running` and keep `pc`?
2. For yields, continue the CFG to `pc+len` (a single-frame interpreter may still stop there).
3. Cheap cross-check: a linear decode sweep from just past every terminal opcode, filtered to the opcodes in question; confirm each hit by decoding a chain that lands on it.

**Canonical example:** crawl, Ishar 1 (Silmarils ALIS). `cstop` (`maestun/alis` `opcodes.c`) only does `script->running = 0`; `alis_loop()` resumes at `pc`. An audit concluded the backdrop's world palette was never loaded; a sweep past the backdrop script's `cstop` found `cselpalet(0); cpalette(8)` on tick 2 — the same pattern in all 7 backdrop scripts of 3 games, plus a "flash red, yield, restore palette" sequence elsewhere. The shipped palette was right; the negative came from the walker.

**History:** 1 instance (crawl/Ishar, 2026-11-13).
