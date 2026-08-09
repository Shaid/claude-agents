# A boot-time/quickload catalog's declared per-file byte range bounds what's loaded at that stage, not the resource's real semantic extent

**When it bites:** a disk/archive has a small, confirmed, byte-exact
catalog or directory (explicit terminal record, verified length/checksum,
zero ambiguity about where it says a file ends) that covers only *some*
of the container's total size — and a resource named in that catalog
turns out, on inspection, to hold recognizable content (readable text, a
repeating record shape) that is still forming/incomplete right at the
catalog's declared end.

The instinct is to trust a confirmed, verified directory boundary as the
resource's true content boundary — after all, the bytes checked out, the
terminal record parsed cleanly, nothing contradicts it structurally. But a
catalog built for a **staged loader** (a bootstrap-only "quickload" table
that just needs to know where to find the handful of files required to
get the title screen and first bit of gameplay running) has no obligation
to describe the whole disk, and in particular has no reason to describe a
resource's *logical* end if the game's own runtime code keeps reading
sequentially past it once the engine is up — the catalog only needed to
say "start here," not "this is everything."

Confirmed on Zeewolf (Amiga, `hunter` project): a byte-exact, code-free-
verified 4-file boot catalog declared one file (`TITLE.MOD`) ending at
logical block 363 and a second (`TITLE.DRV`) at block 368. A byte-exact
structural tag (a literal 3-byte marker preceding 94 of 95 real "Mission "
briefing-text occurrences disk-wide) showed the same mission-text database
actually starts *inside* `TITLE.MOD`'s own declared range (around block
333) and continues, with no header, marker, or transition of any kind at
the block-368 catalog boundary, into disk space the catalog does not
describe at all (through at least block 391). Nothing about the catalog's
own bytes was wrong or ambiguous — it simply wasn't claiming to bound the
resource's content, only the boot-time read.

**Takeaway:** treat a small/early directory's declared per-file range as
"proven correct for what it claims," not as "proven complete." Before
concluding a resource stops where its catalog entry says it does,
specifically check whether recognizable content (text, a repeating record
shape, anything with its own internal continuity) crosses that boundary
seamlessly — if it does, the catalog is a loading-stage bookmark, and the
resource's real extent is a separate, still-open question requiring its
own terminator/count/structural boundary to answer. This is the mirror
image of `unbounded-appended-data-boundary.md` (no declared bound at all):
here a bound exists, verified, and is simply the wrong kind of bound for
the question "where does this resource's content end."
