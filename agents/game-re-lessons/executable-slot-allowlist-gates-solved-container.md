# A hardcoded slot-index allowlist in the executable can gate which parts of an already-solved container the engine actually reads

**When it bites:** A self-describing container format is already fully
solved (directory/slot-count + per-slot size/pointer, byte-exact) and a new
file placed into one of its unused/reserved slots (a content-injection mod,
a hand-built test file, a fuzzing probe) either crashes the game or is
silently ignored — before assuming the container spec itself is incomplete
or the new content is malformed, trace the real caller loop that walks the
container for a small, literal integer table in `.rodata`.

## What went wrong

Fire Emblem: Three Houses (Switch, `chimera`): the PACK container format
(`{u32 slotCount, (u32 ptr, u32 size)[slotCount]}`) was already solved
byte-exact. A modded character pack placed real G1M model data in slot 18 —
structurally valid, well-formed, no violation of the container spec — and
the game crashed. The container format alone gave no reason to expect a
problem: nothing in its own bytes says "slot 18 is special."

The real mechanism was in the *consumer*, not the container: FE3H's model
loader walks a hardcoded, undocumented 16-entry slot-index table in
`.rodata` (`main+0xcd89c4`: `0,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18`) —
an allowlist of which numbered slots the engine actually opens as G1M
blocks. Every slot not on that list (1,2,3,19,20,21 in this game) is either
handled by separate, differently-typed code (slot 1 = `GT1G`, slot 3 =
`BGIR`/`RIGB`) or never read at all. Across the base game's entire corpus
(569 packs), the allowlisted-but-unused slots (14-18) are always empty —
safe only by authoring convention, never enforced or documented anywhere in
the container itself. A file that puts non-G1M data in one of those
"reserved" slots is invisible to a structural/byte-level container audit and
only shows up by tracing the real slot-walking loop's literal table.

## The fix

For any already-solved variable-slot/section container, treat "which slots
does the container format support" and "which slots does the engine actually
consume" as two separate questions. The second can only be answered by
finding the real consumer loop and its bound (a literal trip count, an
immediate compared against an index) and, where the loop indexes through an
indirection table rather than 0..N-1 directly, dumping that table's raw
bytes. A container-level census (sizes, magics, chained offsets) proves the
data is *well-formed*; it cannot prove the data is *reachable*.
