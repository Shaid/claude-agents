# Sprite frame bounding-box geometry can recover animation-segment boundaries even when the driving executable resists tracing — or can't name states even when it's fully traced

**When it bites:** you need a frame-index → named-animation map (idle, walk, attack, death) for a multi-frame sprite resource, and either the driving executable resists tracing, or the animation VM is fully decoded but selects behaviour by an opaque state/entry-point index nothing names. Also: comparing two ports/builds of a sprite whose frame counts differ.

A traceable interpreter tells you *how* frames are selected, not *which* selection means what (Vengeance of Excalibur's fully decoded FSME VM still left ~32 entry points per class unnamed). Segment *boundaries* can be recovered cheaply from data; segment *names* always need separate evidence.

**Check / fix — boundary signals, cheapest first:**
1. **Sustained bounding-box discontinuity:** width or height jumps by more than a ratio (e.g. 1.6×) over the preceding segment's median **and** stays in the new regime for several frames (e.g. ≥ 4). The plateau requirement rejects in-action motion — a 5-frame swing whose width changed every frame gave zero false boundaries.
2. **Exact frame-dimension prefix across resources:** if resource A's entire `(w,h)` sequence equals resource B's first N frames, B has an authored cut at N. Catches cuts signal 1 misses (a small stab within the idle width envelope). Run the full pairwise comparison — it is cheap.
3. **VM reachability walk (when decoded):** collect the literal frame indices each entry point's bytecode can draw (`vm-bytecode-embeds-platform-addresses.md`). Proves grouping, not naming; may disagree with 1/2 on the exact cut — report both.
4. **Read scripts in program order to name segments:** a backward `Goto` loop interleaved with move-toward-destination = walk; a forward ramp ending in a hold-frame-forever sentinel plus SFX and a conditional spawn = death; a 2-frame alternation reached from a shared status-check subroutine = idle/guard. Costly per class; budget for the classes that matter. Absence (no death in a class's script) can be a real finding: native code handles it.
5. **Prefer a code marker over a geometric tell** that fired for one instance. WIME FRML: the wizard's magic frames are wider *and* taller, but wraith and Balrog magic frames are width-only, indistinguishable from four races' footwork variants; the generalizing signal was a reserved opcode (`extra=0x80, code=16`) present in exactly the magic blocks.
6. **Different frame counts across builds → align by LCS** over `(w, h, composeX, composeY)` tuples, never positionally.

Names remain best-fit labels: at least one render check per distinct pose family, generalize by structural analogy, and grade confirmed / structural-but-unnamed / hypothesis (`published-walkthrough-numeric-oracle.md`, `partial-resolution-rate-is-noise.md`).

**Canonical example:** Warriors of Legend LMRF corpus (`middilgard`): a 16-frame resource with a clean ~2× width jump sustained for 8 frames matched a real idle→attack transition confirmed by rendering, with zero executable tracing; several pairs whose attack stayed inside the idle width envelope were caught only by the exact-dimension-prefix match across the 162-resource corpus.

**Variant:** WIME DOS-VGA vs Amiga `BSCENE.RES` "man": a positional diff called tail frames 17–19 new sit-down art; LCS showed they were frames 12–16 shifted by 3 frames genuinely inserted earlier as an alternate weapon swing (confirmed by bytecode references).

**History:** 6 recorded signals/instances (Warriors of Legend, Vengeance, WIME, Spirit of Excalibur — all `middilgard`) — full log in `_archive/sprite-frame-geometry-reveals-animation-segments.md`.
