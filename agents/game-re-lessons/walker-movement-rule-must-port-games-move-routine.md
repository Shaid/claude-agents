# A walker's movement rule must come from the game's move routine, not its render evaluator

**When it bites:** you're writing a walker's `canStep`/collision rule, picking its start position, or deciding what happens at the map edge. Or a user says the walker "feels very inaccurate" while the renders look right.

Render code answers "what is drawn on this face". It folds in decorative features, doors and stairs art, fog and pits. Move code answers "can the party cross this edge", and it usually reads **raw** wall codes and different bits. Reusing the render evaluator for movement makes every drawn door, doorway, stairs and feature a wall. Porting a reference project's convenience helper instead of its ASM-cited game routine gives the same result. Typical errors: doorways and closed doors become impassable (the game opens a closed door on a forward step), the destination cell's back wall gets checked as well (the game checks only the current cell, and one-way doors exist), and terrain rules come from a "fallback" heuristic. Start poses and map edges get guessed in the same way: "first fully open cell", clamping at the edge where the game wraps or links sectors, solid walls where the game treats off-map as open sky.

**Check / fix:**
- Locate the move handler: the forward/turn key dispatch, the routine that plays the bump sound or shows "you can't go that way", or the one that writes the party X/Y. Port it with its exact inputs: which plane, which bits, current vs destination cell, facing-dependent cases.
- Quantify with a flood-fill census over every level. Count edges the walker blocks but the game allows, and the reverse. Count one-way edges, and the largest reachable area per level, under both rules. Thousands of edges or a 2× area difference means the rule is wrong.
- Take start cells and facings from the game's own data or code (a start table, an `entry_coord` field, the new-game routine). Take map-edge behaviour from the off-map branch of the neighbour lookup (wrap, link to the adjacent sector, or open).
- Wire level transitions (stairs, teleporters, exits) from their real handlers. "Matching stairs by absolute position across levels" usually fails.
- Write down "walker movement rule: from routine X" in the walker doc, so it isn't mistaken for verified.

**Canonical example:** Wizardry 6 (Amiga). `canStepDir` allowed a step only when the render evaluator `evalCellFace(...)` returned 0. The game's TryMove (`LAB_07C0` → `LAB_0792`) reads only the raw wall planes: codes 0 (open) and 1 (doorway) pass, code 3 (closed door) passes when moving forward (door sound + redraw, then the step), and stairs cells are walkable. Over all 14 levels the walker blocked 1,267 edges the game allows (754 doorways, 309 closed doors, 204 feature-gated edges) and made 410 edges one-way. On level 9 the largest walkable area was 56 cells in the walker against 132 in the game. The "298,744-pose sweep, 0 exceptions" only showed the code didn't crash.

**Variants:**
- Might & Magic 2 overland: the walker used a helper rule labelled `# Fallback` in the reference repo's tools script, not its ASM-cited `passabilityObstruction` (`0x9424`, a 32-entry terrain-class table plus party skills). It blocked 9,490 of 23,040 moves (41.2%) the game allows. MM1 and MM2 indoor maps also checked the destination cell's back wall, which blocked about 1% of moves, mostly at one-way or locked doors.
- Might & Magic 1: edges clamped, but every indoor map wraps onto itself and the 20 overland sectors form a reciprocal 5×4 grid (62/62 links). Start cells came from a first-open-cell heuristic; ScummVM's `loadTown` gives the real cells and facings.
- Wizardry 6 levels 10/12: the evaluator's off-map path returns open (sky/ground), but the walker drew walls along the edge.

Related: `reference-debug-dumper-or-tool-helper-is-not-runtime-path.md`, `topdown-grid-orientation-check-via-planted-cell.md` (axes and facings), `check-that-cannot-fail-is-not-evidence.md` (crash-free sweeps).

**History:** 3 projects (Wizardry 6, Might & Magic 1/2, Ishar), 2026-11-13 audit.
