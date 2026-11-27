# Generated artefacts from executing game code carry retail text (and protection content)

**When it bites:** before committing or pushing any machine-generated output of a harness that ran real game handlers — event tables, UI/print call logs, trace vectors, string dumps — in a repo that is or may become public, especially when the output is gzipped or minified JSON.

The harness logs the strings each handler printed or passed to a stubbed UI call: dialogue, riddle prompts, copy-protection screens and hints. gzip hides them from `git grep`, from diff review and from any text scan of the tree. Commit messages describing the run can carry the same words.

**Check / fix:**
1. Store pointers/ids, never strings. Resolve text at build time from the user's own gitignored retail data, and skip cleanly when it is absent.
2. Before every push: decompress every added `.gz`/blob and grep for prompt/marker text; grep commit messages too.
3. If it already landed in **unpushed** history: fold the fix into the original commit (backup branch first, then check the final tree is identical apart from the intended change), and re-scan. Pushed history needs the user's decision.
4. Exploration runs must not record the inputs that solve protection/password gates.

**Canonical example:** crawl MM1 rules pass 4: a 74 KB gzipped overlay event table held verbatim riddle prompts, a gate hint and protection-screen text. Rewritten to text pointers before push; re-scan found 0 hits.

**History:** 1 recorded instance (crawl MM1, 2026-11).
