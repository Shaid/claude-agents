
## 2026-11-22 — lucina, Fire Emblem Fates GameData.bin (unlabelled tables off header slots)
Evidence: lucina docs/fe-fates/exe.md §7-8, docs/3ds-formats.md §15.5; commits 271006d, 67ea0bd.
In a labelled table container, the move-cost matrix, weapon types/kinds, rank and triangle tables had no labels; they hang off data-header slots +0x30..+0x4c. Move-cost matrix at slot +0x4c: u32 count 16, then 16x16 bytes, ending exactly at slot +0x50's target. Matches 169/170 cells of the published terrain table (shifted rows 129/170, transposed 48/170). A sibling agent had first searched code.bin and found nothing.
Check/fix proposed: enumerate every pointer slot in the data header, resolve targets in ascending order; gap to next target = exact table size; join each candidate to a published table with shifted-row and transposed nulls.
