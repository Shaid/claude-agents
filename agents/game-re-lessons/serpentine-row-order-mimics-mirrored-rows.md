# Serpentine (boustrophedon) row storage mimics mirrored rows and defeats bit-layout permutation sweeps

**When it bites:** a sprite/tile decode shows row-level mirror-like symmetry
(suggesting "stored with its mirror pair"), renders with vertical-stripe
artifacts, or an exhaustive bit-order / address-bit-permutation sweep over
the assumed record size returns "no improvement" — before concluding
mirror-pairs or an exotic bit layout, run the plain-vs-mirror row-equality
test below, and re-question the record size itself.

Software blitters that walk columns forward on even rows and backward on odd
rows (`cols 0,1,2,3` then `cols 3,2,1,0`, reading the source strictly
sequentially) store adjacent rows in alternating direction with the byte
content itself untransformed. At a glance that reads as palindrome symmetry
— "each row appears alongside its mirror" — which tempts a
sprite+mirror-pair or reflected-layout theory.

**The discriminating test is plain byte equality vs true pixel-mirror
equality between adjacent candidate rows.** True mirroring transforms the
bytes (pixel order reverses within each byte); serpentine storage does not.
On WIME CPC (`middilgard`), plain byte equality between adjacent 4-byte rows
scored 53–73% while genuine pixel-mirror equality scored 34–40% — plain
equality winning is the tell for boustrophedon order. A normalized
spatial-coherence sweep over base offset × row parity then peaked at exactly
the true base and parity (0.4990 serpentine vs 0.2775 row-major; vertical
neighbour-pixel agreement 77.5% vs 51.9%).

Two supporting generalisations from the same crack:

- **An exhaustive permutation search returning "no improvement" is a
  positive result.** Sweeping every 2/4bpp bit-assignment (2,520 variants)
  and every 7-bit address permutation over the assumed 128-byte record
  (covers row/column-major and every interleave) both failed to beat the
  baseline — which *ruled out* bit layout and interleave and pointed at the
  record size. The real records were 32 bytes (168 8×8 tiles), not 128
  (34 16×32 sprites).
- **A boot/fastloader's load-call argument list `(dest, firstTrack,
  lastTrack)` is the fastest route to the load base** every data offset
  depends on — and it's independently checkable for free by rendering a
  full-screen region at an address it predicts (a legible title screen
  confirms the whole map).

The final spec was read off the game's own blitter (sequential source reads,
`DEC E` column walk, `AND $AA`/`AND $55` per-pixel masking), not guessed.
See `middilgard/docs/wime/cpc/engine.md` § Sprite tiles.
