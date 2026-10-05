# A third-party format doc's prose can describe a converted/internal value, not the raw on-disc bytes its own tool reads

**When it bites:** a community reverse-engineering project's doc states a
header/record field's *unit* in prose (e.g. "a byte length, always a
multiple of 0x800") and you're about to trust that unit for a field you
haven't independently decoded from real bytes yet — especially when the
project's own extractor tool demonstrably works correctly (ships real,
correct output), which can feel like license to trust its documentation
too.

A tool being correct does not mean its doc's prose describes the *raw
stored representation* rather than a value the tool computes/converts
internally (sectors→bytes, or vice versa) before or after reading it. The
doc can describe the converted concept the author was thinking in while the
raw field on disk is in a different, smaller unit — and nothing about the
tool working correctly would ever surface this, since the tool's own
internal conversion papers over the discrepancy every time.

Confirmed on Parasite Eve II's `STAGE0.CDF` chunk container
(`~/Development/parasite`). The community decompilation project
`GabeRealB/parasite-eve-2-decomp`'s `ASSET_FORMATS.md` states a 16-byte
chunk header's `chunk_size` field is "Total on-disc size in **bytes**
(multiple of `0x800`)". Reading the real first two chunk headers in
`STAGE0.CDF` gives `chunk_size = 0x1c` and `0xaf` — nowhere near
sector-aligned as byte counts (28 and 175 *bytes* would collide with the
header itself). Reading the same raw values as **sector counts** instead
checks out exactly: `28 + 175 = 203` sectors, which is byte-for-byte the
project's own independently-derived file-table boundary for that file, and
the *next* chunk header was found empirically at exactly sector 28
(`0xe000` bytes in) with a real, plausible `load_addr` matching the doc's
own separately-cited example value. The doc's stated unit was simply wrong
for the raw field; the underlying tool's actual behavior (whatever it is
internally) is self-consistent with sector-based storage.

**Fix:** treat a third-party doc's stated *unit* for a numeric field as a
hypothesis, not a given — even when the same doc's *structural* claims
(field existence, offset, width) have already checked out byte-exact on
other fields. Verify a field's unit the same way you'd verify anything
else: derive an independent boundary (a sibling table's own cumulative
offset, a file size, a directory's declared count) and check whether the
raw value satisfies it under each candidate unit, rather than assuming the
doc's prose already did that check for you. This is a sibling to
`reference-tool-field-never-consumed-by-its-own-importer.md` (a field's
*formula* can be unvalidated even when the tool works) and
`self-consistent-chain-wrong-unit.md` (your *own* derived chain can still
have the wrong unit) — here the twist is that the mismatch lives in
someone else's *prose*, not in either project's code.
