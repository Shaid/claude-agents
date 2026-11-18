# A decoder's "output length == declared size" check can't fail; assert exact input consumption

**When it bites:** a codec is "confirmed" because every record decodes to its declared size, an image test asserts `pixels.length === w*h`, or a fill metric ("≥95% filled") is high. Look at how the decoder sizes its output first: if it allocates the declared size, loops until the output is full, or stops at the declared length, the check passes for any input.

Most hand-written decoders take the target size as a parameter. They allocate it, stop when it is reached, and often return 0 for reads past the end of the input. Then "output == declared" and "output is full" hold whether the grammar is right or wrong. The input side is where a wrong grammar shows: it stops early (most of the stream never read), overruns into the next record, or leaves a fixed residue.

**Check / fix:**
- Make the decoder return `{data, outPos, consumed}`. Assert **both** `consumed == storedSize` (allowing only a documented 0-1 byte bit-buffer look-ahead or alignment pad) **and** `outPos == declaredSize`, ideally with the end marker landing on the last byte. Report the count as "N/N exact in and out".
- Run a null control the check can actually fail: payload shifted +1, wrong codec, a corrupted byte. A sound check gives about 0/N.
- Make sure reads past the end of the input fail or are counted, not silently 0. A 0-returning reader turns "filled to w*h" into a constant.
- A **constant leftover** across many records (the same 32-33 nibbles, the same 4 bytes) is a fixed trailer or the next structure's header, not noise. Model it, then re-check.
- When two codecs could apply (PackBits vs LZSS), "hits the declared length" can't separate them, because a stop-at-length decoder reaches it either way. Full-input consumption can.

**Canonical example:** Warriors of Legend (DOS) `XFSD` sound, "PackBits, 32/32 decoded". `packBitsDecompress(payload, declared)` stopped at the declared size after consuming 167 of 2,233 payload bytes (#103), 287/6,094, 1,012/7,511. Decoding the full input gave a different length for 32/32. The "shared leading sample `0xb9`" was a bit-transformed Creative VOC header ("reative Voice File"). The tests ("matches declared size", "starts with 0xb9", "autocorrelation in range") could not fail.

**Variants:**
- Dungeon Master 2 `IMG4` "98.9% decode to ≥95% filled": the reader returned 0 past the end, so almost every item filled. Exact consumption: 5/2,263 under the shipped grammar. A constant 32-33-nibble leftover revealed a 16-byte trailer, and with it 1,533 + 727 items tiled exactly. DM1 `IMG1` "683/683": the test asserted only `pixels.length === w*h`; consumption found one non-image and 5 excluded full screens.
- Valkyrie Profile 2 SL/ZLS: `decodeSlz*` returned `new Uint8Array(outSize)` and the pipeline compared it with `outSize`. The consumption re-check (125/125 in and out, null 0/124) is the real evidence.
- Powermonger Amiga LZ "variant A": emitted all 85,400 declared bytes after consuming 32 of 36,608 stream bytes. The output was a periodic texture ("sensible repeating structure"). A correct bit-refill rule consumed every chunk exactly.
- Dune `balcon` frame 6: the decoder zero-filled to 64 KB and shipped a 320×327 noise PNG. The frame's own length word and an exact 30,400-byte output would have rejected it.

Related: `check-that-cannot-fail-is-not-evidence.md` (the general audit question), `rle-decode-succeeds-on-garbage.md` (a walk that never errors), `container-entry-end-overread-becomes-fake-trailer.md` (when the constant leftover is the next header).

**History:** 7 recorded instances (Warriors of Legend, DM1, DM2, VP2, Powermonger, Dune, Urban Strike), 2026-11 audit sweep.
