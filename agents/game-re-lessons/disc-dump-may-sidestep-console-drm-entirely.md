# A disc dump can make PKG/NPDRM decryption work moot for base-game assets

**When it bites:** starting console-PKG (PS3/PSVita/PS4/Xbox-Live-style
digital release) decryption work for a title that also ever shipped on
physical disc, before checking whether an unpacked disc dump is available
or obtainable.

Digital storefront packages (PS3 PSN `.pkg`, and the equivalent on other
platforms) carry an extra encryption layer purely to protect the download
itself — the PKG container's AES-CTR wrapper, and often a further per-file
NPDRM/DRM layer (PS3's `.EDAT`) on top of that. **None of this exists on a
physical disc release of the same game**: disc media doesn't need
download-piracy protection, so disc dumps frequently ship the exact same
asset files as **plaintext**, readable with nothing more than the game's
own in-house compression/container formats (already the actual reverse-
engineering target either way).

Confirmed on Drakengard 3 (PS3): substantial, correct, fully-verified PKG
container decryption (custom AES-128-CTR implementation, since the classic
retail-PS3 PKG header differs from Vita's and the obvious first tool
`pkg2zip` doesn't support it — see `game-re-tooling/ps3.md`) plus NPDRM
`.EDAT` decryption (RAP-file-based klicensee derivation, RPCS3-sourced
algorithm) were both built and confirmed working against the PSN digital
`.pkg` release — genuinely useful work, but it turned out an unpacked disc
dump of the same game (supplied by the user mid-session, not initially
mentioned) contained the **entire base-game asset set as plaintext**, no
PKG or NPDRM layer at all, confirmed by magic-byte inspection of sample
files (`9E 2A 83 C1` UE3 package tag directly at offset 0, no encryption).
The PKG/NPDRM work wasn't wasted — DLC for this title only exists as PSN
pkgs, no disc equivalent — but it was not on the critical path for the
~8,700 base-game files that mattered most, and would have been correctly
deprioritized from the start had a disc dump been checked for first.

**Fix**: before investing in a console digital-storefront package's crypto
layer, explicitly ask (or check the supplied data directory for) whether a
disc dump / physical release rip of the same title is also available — for
a multi-source game this is a first-order question, not an afterthought,
since it can make an entire layer of otherwise-necessary crypto work
irrelevant for the bulk of the content. If both exist, the disc dump is
very likely the cheaper path to assets; the PKG route remains necessary
only for anything disc-only titles don't include (DLC, day-one patches
shipped exclusively via PSN, etc.).
