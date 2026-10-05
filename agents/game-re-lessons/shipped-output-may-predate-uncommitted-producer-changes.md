# Shipped build output can predate uncommitted working-tree changes — check `git diff HEAD` of the producer before blaming your own change

**When it bites:** you regenerate an asset corpus and diff it against the
previously-shipped one, and some elements have appeared or (worse)
disappeared that your change does not explain. Especially in a repo where
build output is gitignored, other agents work concurrently, or the working
tree has been dirty for a while.

## What went wrong

A fix to a shared mesh exporter was regression-checked by diffing the
rebuilt GLB corpus against the shipped one. Three games came back cleanly
except for **63 FE Warriors primitives that had vanished**, clustered
suspiciously in one family of packs (`O_Soldier_*`, always submeshes 3-5).
Time went into tracing those submeshes through the exporter's skip
conditions looking for a newly-thrown exception.

There wasn't one. The submeshes were LOD1/LOD2, and the exporter had a
"export only LOD0" deduplication guard that correctly excluded them — a
guard added by a **different, concurrent session, uncommitted, already
present in the working tree before this task started**. The shipped GLBs had
been built before that edit, so the diff was measuring someone else's change,
not this one.

## The check, and why it is one command

```
git show HEAD:<producer file> | grep -c '<the code you suspect>'
```

Returning `0` while the working copy has it proves the behaviour is
working-tree-only and therefore absent from any previously-shipped output.
More generally, before trusting *any* regenerated-vs-shipped diff:

1. `git status --short` — is the producing code modified at all?
2. `git diff HEAD -- <producer paths>` — read it. Every behavioural change in
   there is already baked into your "after" and absent from your "before",
   and will be silently attributed to you.
3. Prefer diffing **your change alone**: stash or revert only your own edits,
   rebuild a small sample, and compare that against the full rebuild. If
   that is too expensive, at least enumerate the pre-existing working-tree
   changes so you can classify each unexplained delta against them.

Also note the inverse failure: a rebuild that *adds* elements (this corpus
went 181 -> 183 GLBs) is just as likely to be a sibling's change, and reads
as a win if you are not looking for it. Related:
`concurrent-sibling-live-edit-collision-on-shared-source.md`,
`concurrent-sibling-agent-edits-shared-repo-decoder-live.md`,
`semantic-output-diff-with-unchanged-parts-as-reference-frame.md`.
