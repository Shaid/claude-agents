# The game's own executable may carry a resource-path registry that names every asset ID — extract the code partition, not just the data partition

**When it bites:** an ID-indexed gamedata table's records are anonymous
numbers and you're about to conclude (or have already concluded, in a
paths-tried table) that **no ID→name oracle exists** for this game because
WebSearch found no 010-template / cheat table / save-editor list and the
data files themselves carry no names. Also bites earlier: whenever a
console/PC target's extraction pipeline only unpacks the *data* partition
(Switch RomFS, PS3 `USRDIR`, a disc's ISO tree) and never the *executable*
one.

## What happened

Fire Emblem Warriors (Switch, `chimera`). Four separate passes tried to
name `ModelChrParam.bin`'s 350 records: WebSearch for community templates
and cheat tables (0 hits, twice), a raw byte-scan of every gamedata table
for embedded `C_<Name>` model-filename strings (0 hits), an
alphabetical-model-order correlation (refuted), and a statistical
cross-table outlier argument that got exactly *one* record circumstantially
identified. The docs recorded "no external ID→name oracle exists for this
game" as a settled fact.

Every one of those passes searched the RomFS and the web. Nobody had
extracted the **ExeFS**. One `hactool --exefsdir` run plus an NSO0/LZ4
decompress, and `strings` on the resulting image immediately showed
`nx/action/model/C_Marth.bin.gz` and every sibling path — laid out as one
ordered pool. Behind it sat a flat 13,133-entry array of
`{const char* path, void* handleSlot, u32 flags}`, i.e. **a complete
resource-ID → filename table for the whole game**, one entry per loadable
file. All 350 records named in an afternoon, and `id=132 = C_Evildragon`
went from "hypothesis, strongly corroborated" to byte-exact confirmed.

## Why this is a class of thing, not a one-off

A game engine that loads assets by numeric ID has to turn that ID into
*something* the filesystem understands. Where it does that is decided by the
container design, and this is predictive:

- **Loose files in the data partition** → the executable must hold literal
  paths (a path table, or a `sprintf` template plus a name table). This is
  the case that hands you a free, complete, authoritative oracle.
- **Assets inside an indexed archive** (a LINKDATA/`DATA0`/BigFile with a
  numeric TOC) → the executable needs no path table; expect only
  `"%s.bin"`-style templates. Confirmed on Three Houses.
- **Assets addressed by a content hash** (an ID that is a hash, not an
  index) → the executable holds a *hash*-substituting template and no path
  array. Confirmed on Three Hopes: its `main` carries `"%s0x%08x.fdata"`,
  `"KtidFilePath"`, `"root.rdb"` — every resource is reached by a 32-bit
  KTID through a resource directory, and a `strings` pass over the whole
  39 MB decompressed image finds no asset-path array anywhere. **This does
  not mean there is no oracle** — see the second correction below; the
  oracle for this case lives in the executable's *code*, not its data.

> **Correction.** This lesson previously said Three Houses *and Three Hopes*
> "ship indexed archives and have no registry at all in their `main`",
> presented as confirmed. The Three Hopes half was not confirmed — that
> title had **no ExeFS extracted at all** at the time, so its `main` was
> never on disk to check. The conclusion survives, but the reasoning was
> wrong: Three Hopes is hash-addressed, not index-addressed, which is a
> third case the two-way taxonomy above couldn't express. **Before writing
> any claim about what an executable does or doesn't contain, confirm the
> executable is actually extracted for that title** — a claim of this shape
> is cheap to make and expensive to un-believe, because later passes cite it
> instead of re-checking.

> **Second correction — the hash-addressed case is not a dead end.** The
> bullet above used to end "there is genuinely no oracle to find and the
> search can be closed with confidence". A later `re-codebreaker` pass on
> the same title disproved that. A hash-addressed engine still has an
> oracle; it is just in the **code** rather than the data. The engine's
> property/descriptor **registration routines** pair each plaintext name
> with its precomputed hash constant in adjacent instructions, because both
> halves are needed at build/edit time. On Three Hopes a 4-instruction
> jump-table idiom in `main` yielded 8,037 literal `(name, hash)` cells →
> 2,756 distinct anchors → the algorithm itself,
> `ktid(s) = Σ s[i]·31^(i+1)`, code-confirmed at `main+0x75D574`. That named
> 21 real resources, resolved **3,187 / 3,354 (95.0%)** of the object
> database's property names, and exposed a 188-edge resource dependency
> graph.
>
> The true limit is narrower and must be *measured*, not assumed: a hash
> names only strings that survived somewhere. Three Hopes' model and
> animation names are 16–36 characters long (measured from the ID set
> itself, with no plaintext) and appear in no shipped string, so they stay
> unrecoverable — yet thousands of property and object names were fully
> recoverable in the same binary. Recover the algorithm first, then measure
> its reach. Full chain: `game-re-method/name-hash-recovery.md`.

So before spending a pass hunting a name oracle, ask which of those three
the target is — and note that all three have *something* to give: a path
array, a filename template, or a recoverable hash. FE Warriors' own docs had
*already* recorded "this game has no LINKDATA archive at all" — the clue that
a path table must exist was sitting in the project's own corpus notes,
unconnected.

## What to do

1. Extract the executable partition as a matter of course, not as a last
   resort. It is small (a few MB next to a 14 GB RomFS) and cheap. Make the
   extraction tool do it unconditionally so no future pass has to think of
   it. (Switch: `hactool -x --exefsdir=<out> <Program NCA>`, then decompress
   the NSO's LZ4 segments — see `game-re-tooling/switch.md`.)

   **"Unconditionally" is not enough on its own if the step is idempotency-
   guarded.** Chimera's `extract-romfs.ts` does extract ExeFS — but only
   when `p0-exefs/main` is missing, and it never re-runs for an already-
   extracted title. Three Hopes had been extracted before that step existed,
   so it silently never got one, for months, while the tool's source read as
   if every title had it. Whenever a pipeline gains a new per-title output,
   check the titles extracted *before* it landed; a "skip if already done"
   guard keyed on the whole extraction, not on the individual artifact, will
   never backfill them.
2. `strings` the decompressed image for a known asset's filename. If the
   paths are there, find the pointer array that indexes them: locate the
   8-byte (or 4-byte) little-endian address of one known string, then
   measure the stride between two entries whose relative order you know.
3. Registry entries are usually `{pathPtr, runtimeHandleSlot, flags}` with
   the handle slot advancing by a fixed amount per entry — that progression
   is a much better locator signature than any string (see
   `pointer-array-stride-signature-needs-content-plausibility.md` for the
   guard it needs).
4. Then pin the base: the table's ID space is normally the array index plus
   a per-class constant, which you should *derive and verify*, never assume
   — see `verification-techniques.md`'s self-verifying-base-alignment entry.

## The meta-lesson

"No oracle exists" is a claim about where you looked, not about the game.
Four honest negative passes over the same search space are not four pieces
of evidence — they're one, repeated. When a negative keeps recurring, change
the *shape* of the search (a different partition, a different artifact
class), not the effort. Same failure mode as
`negative-from-addressing-root-not-shapes.md`, in a different medium.
