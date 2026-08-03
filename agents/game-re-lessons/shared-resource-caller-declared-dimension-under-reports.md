# A shared variable-dimension resource can be under-declared by some of its callers — trust the resource's own byte count over any one caller's declared size

**When it bites:** a resource (tilemap, tile grid, any 2D or record-count
blob whose dimensions live in a separate calling/header record rather than
the resource itself) is referenced by multiple different callers, and a
`declaredWidth * declaredHeight === decompressedLength` (or equivalent)
assertion fails for a minority of them — especially if the failures
cluster on resources that are referenced by more than one caller.

A resource with genuinely no in-band dimension header (dimensions must
come from whatever record points at it) is not guaranteed to have exactly
one *correct* caller-declared size when it's shared by several callers.
The loader code that actually consumes it may process a **fixed** amount
of data per row/column regardless of what a given caller declares — e.g.
always copying a full physical buffer's worth of rows, or reading
sequentially until a fixed hardware-buffer boundary — and simply never
routing the *extra* rows/columns into the visible or interactive region
when a particular caller declares a smaller size than the resource
actually contains. That makes under-declaring **harmless at runtime** (the
excess is silently unused) but means several callers can legitimately
declare *different*, and sometimes *wrong* (too small), sizes for the
exact same physical bytes.

Confirmed on FFVI (SNES, `ceres` project): `SubTilemap` resources (LZSS-
compressed per-layer tile-ID grids for field maps) have no stored
width/height — both come from the owning map-header record's own
width/height class fields. Asserting `decompressedLength ===
declaredWidth*declaredHeight` against the *referencing* record's own
class fields failed for 24 of 350 resources — e.g. one resource is shared
by 5 different interior-room records that all declare a `64x16` height
class for it, while its true decompressed size is `64x64`. The game's own
row-copy loop (`CopyMapTiles`, `src/field/map.asm`) always processes a
row count driven only by the *width* class (64 rows for any width <=64,
128 rows for width=128) — it never reads a caller-declared *height* class
at all during the copy itself; height only clips the *visible/scrollable*
region afterward. A caller declaring a smaller height than the resource's
real content loses nothing observable in-game.

**Fix:** for a resource shared across callers with no in-band dimension
header, don't trust any single caller's declared size as the resource's
true size. Instead, identify which dimension the loader treats as the
*hard* row/column stride (usually the one that determines memory
addressing/wraparound, confirmable from the loader's copy-loop code) and
trust that one from the caller; derive the *other*, tolerant dimension by
dividing the resource's own decompressed/raw byte count by the trusted
one — it must divide evenly, and doing so across the *whole* corpus (not
just the failing cases) is itself a strong structural invariant to check
before promoting the fix.
