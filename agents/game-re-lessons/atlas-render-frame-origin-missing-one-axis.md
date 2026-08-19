# Atlas render dropping the frame origin on one axis silently overlaps frames

**When it bites:** Writing a texture-atlas / sprite-sheet / minimap-grid
renderer where each item's pixel coordinates are computed as (frame origin +
item-local offset), and one axis of the frame origin is missing — frames in
every atlas row/column after the first silently overwrite earlier frames.
Especially dangerous when the reviewer model can't view images, so the broken
render "looks fine" (row 0 is correct, and overlapped small-scale frames are
plausible).

**The bug:** `drawCell` received the cell's X already premultiplied by the
frame's horizontal origin (`ox / SCALE + x` → `dx = ox + x*SCALE`) but
recomputed Y from the cell's own row only (north-up flip), never adding the
frame's vertical origin `oy`. Every minimap in atlas rows 1–4 was drawn over
row 0. The atlas was 352×160 and "rendered" — only a pixel-exact check
caught it: an independently recomputed colour rule diffed against the PNG
flagged 49,995/56,320 mismatches; after the fix the count collapsed to
exactly 3,090 — the number of intentional event-dot overlay pixels (one red
dot per event cell).

**The fix / the verification technique:** (1) apply the frame origin on
every axis — never mix "frame-relative X, absolute Y" coordinate spaces in
one per-item draw call; pass both origins in, or compute both from the same
frame descriptor. (2) Verify rendered atlases pixel-by-pixel against an
independently recomputed colour/layout rule rather than eyeballing —
especially when image review is unavailable. (3) A mismatch count that
equals a known intentional-overlay count (event dots, highlight pixels) is
the signature of an otherwise-correct render: the remaining pixels all
match, and the diff is exactly the overlays.

Confirmed on the MM1 (DOS) maze-minimap atlas in the crawl project
(`tools/mm1/export-maps.ts`): 56,320 pixels checked, 53,230/53,230 plain
pixels exact + 3,090/3,090 event-dot pixels exact after the fix.
