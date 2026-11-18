# A reference project's debug dumper, tool helper or prose isn't its runtime code path

**When it bites:** you're porting a loop bound, a rule or a field label from a reference engine, a decomp or a sibling RE repo, and the code you copied sits in `debug.cpp`, a `dump*`/`list*` routine, a `tools/` script, a helper marked `fallback`/`approx`, or the repo's markdown. It is not in the path the game executes.

Reference projects carry several layers of different fidelity. The runtime path (draw, move, load, the ASM-cited decomp) is what the game does. Debug dumpers stop at the first empty entry because that is convenient for printing. Tool helpers simplify. Prose labels are the author's reading and can be wrong where the code they wrote is right. When your port and the reference prose agree, you have one source, not two.

**Check / fix:**
- For each borrowed rule, find its call site in the reference's game loop. If the only caller is a debug command, an exporter or a test tool, find the runtime equivalent and port that.
- Treat `break` on a 0/empty entry in a dumper as suspect. Compare it with the runtime lookup (`table + id*stride`, skip the empty entry) and count the full table up to its next structure, as well as the ids the game's scripts actually reference.
- For direction or bit labels, use the reference's code constants (`DIRMASK_N = 0xC0`), not its tables in prose. Cross-check the labels yourself, e.g. with a neighbour-symmetry test: each wall bit must pair with the facing bit of the neighbouring cell.
- In the doc, cite the reference's runtime function and line, not its README.

**Canonical example:** AGOS (Elvira 1, Elvira II, Waxworks, Amiga). The image-table walk "stops at the first entry whose width/height is 0", copied from ScummVM's debug-only `dumpVgaBitmaps`. The real `drawImage_init` looks up `vga2 + image*8` directly and returns on a 0×0 entry. 0×0 placeholders sit mid-table (189/198/1,061 of them). The full tables hold 1,654/3,273/4,381 valid images against 1,124/2,303/2,318, and "3/7/15 zones have empty animation tables" was false. The scripts' own draw calls land on valid entries beyond the early stop (612/1,625/2,067).

**Variants:**
- Might & Magic 2 (Amiga): the walker ported the reference repo's `mm2_map_move.py` (labelled `# Fallback`) instead of its ASM-cited `passabilityObstruction`. It blocked 41.2% of overland moves the game allows. The docs' N/E/S/W bit labels came from the same repo's prose, which its own decomp comment contradicts. Neighbour symmetry: the true W,S,E,N slot order pairs 6,996/7,005 faces (MM1) and 100% (MM2), while the documented order pairs about 30%.

Related: `reference-tool-parses-runtime-image-not-rom-blob.md`, `reader-side-may-still-be-export-target-math.md`, `fan-doc-algorithm-label-vs-attached-reference-script.md`, `early-stop-walk-truncates-table-check-consumer-references.md`, `walker-movement-rule-must-port-games-move-routine.md`.

**History:** 2 projects (AGOS, Might & Magic), 2026-11-13 audit.
