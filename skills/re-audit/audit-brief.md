# Codebreaker gap-audit brief (report-only)

TASK: gap-audit what the project *believes it knows about the data* for the title(s) named in
your prompt. First read the project's AGENTS.md / README / docs/architecture-overview.md, the
titles' format docs and TODO.md, and any shared format docs your prompt names. Retail data is
gitignored under data/<game>/<platform>/.

## Method
Treat every claim marked solved, confirmed or verified as a hypothesis. Re-check the
load-bearing ones against the retail bytes with your own fresh code, independent of the repo
decoders where you can. Checks that have caught real errors:
- container tiling and exact sizes (every byte accounted for, entries end where the next begins);
- decompressor **exact consumption** (input pointer ends at the declared end, output equals the
  declared size) — "output length == w*h" is a tautology when the decoder allocated w*h;
- record counts and strides over the **whole** corpus, not a sample;
- cross-platform / cross-version / cross-region consistency — byte identity where ports share
  data is a free oracle (hash-join every file against the other port before decoding);
- the executable's own tables and loader code (what the game actually reads, and how far);
- **null controls** — shuffled input, wrong offset, swapped fields, ±1 shift — that a real check
  must FAIL. A check that passes on garbage is not evidence.
Also ask whether the corpus itself is trustworthy: fan-patched or translated dumps, damaged or
truncated rips, modded files, a different region than the docs assume.

## Look for
(a) claims that are wrong or overstated, especially circular or tautological "verification"
    (tests that can't fail, sampled-subset checks standing in for the whole corpus, visual
    plausibility used as proof, renders called "confirmed");
(b) contradictions between docs, TODO and code;
(c) cross-platform / cross-title inconsistencies and unused oracles;
(d) important unknowns that no TODO row tracks — including unread regions (containers whose
    later directories/sections are never parsed, over-read "trailers", slack that is really
    another buffer's residue) and data dirs with no docs;
(e) cheap, high-value next steps.

## Constraints
- REPORT-ONLY: do not edit, create, stage or commit anything in the repo. Leave all
  uncommitted user work alone (your prompt lists it or gives a path to the list).
- Scratch scripts only under the scratch folder your prompt gives, with absolute output paths.
- No emulators. No network requests to game services (public reference sources such as
  open-source tools and wikis are fine).
- Never write into data/.
- Do not decrypt anything and record no key material (keys, IVs, decrypt command lines) in any
  output; work only from data already on disk in decrypted form.
- No lesson or credit files (do not write to ~/.claude/agents/game-re-inbox).

## Output (your final message)
A ranked findings list. For each finding: the claim and where it is stated (file:line); what
you checked and how; the evidence (numbers, offsets, controls); a verdict (WRONG / OVERSTATED /
UNVERIFIED / CONFIRMED-solid); the recommended doc/TODO/code change. Then: live in-game checks
the user could run herself (she runs emulators manually), cheap next steps, a short list of
confirmed-solid claims, and anything you were blocked from checking (say so plainly).
