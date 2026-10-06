#!/usr/bin/env python3
"""Validate the game-re knowledge base: size budgets, index sync, references.

Usage: python3 ~/.claude/skills/re-learn/check.py [--quiet]
Exit status 1 if any ERROR is found; WARNings never fail the run.
"""
import glob
import os
import re
import sys

ROOT = os.path.expanduser('~/.claude/agents')
AGENT = os.path.join(ROOT, 'game-re.md')
LESSONS = os.path.join(ROOT, 'game-re-lessons')
INDEX = os.path.join(LESSONS, 'INDEX.md')
CORPORA = os.path.join(ROOT, 'game-re-corpora')
METHOD = os.path.join(ROOT, 'game-re-method')
TOOLING = os.path.join(ROOT, 'game-re-tooling')
INBOX = os.path.join(ROOT, 'game-re-inbox')
SKILLS = [os.path.expanduser(f'~/.claude/skills/{s}/SKILL.md')
          for s in ('re-learn', 're-learn-curate', 're-codebreaker', 're-oracle')]
LOCK = os.path.join(ROOT, '.re-learn.lock')

AGENT_MAX = 30_000          # always-loaded system prompt (target ~25 KB)
LESSON_MAX = 8_000          # one lesson file
HOOK_MAX = 450              # one INDEX.md row's trigger text
CORPUS_MAX = 8_000          # mandatory first read per project
KEY_LESSONS_MAX = 10        # lesson filenames listed in a corpus summary
LOCK_STALE_MIN = 90         # matches skills/re-learn-curate/lock.sh
REFERENCE_WARN = 40_000     # on-demand method/tooling files
CATEGORIES = ['addressing', 'disassembly', 'containers', 'compression-crypto',
              'graphics', '3d-animation', 'audio', 'text', 'logic-scripts',
              'verification', 'tools', 'process']

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def size(path):
    return os.path.getsize(path)


def read(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def rel(path):
    return os.path.relpath(path, ROOT)


# --- game-re.md budget -------------------------------------------------------
if size(AGENT) > AGENT_MAX:
    err(f'game-re.md is {size(AGENT):,} B > {AGENT_MAX:,} B budget — move worked '
        'examples to game-re-method/ or game-re-tooling/, never grow the prompt')

# --- lessons -----------------------------------------------------------------
lesson_files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(LESSONS, '*.md'))
                      if os.path.basename(p) != 'INDEX.md')
for name in lesson_files:
    path = os.path.join(LESSONS, name)
    text = read(path)
    if not text.startswith('# '):
        err(f'lesson {name}: first line must be an H1 title')
    if '**When it bites:**' not in text:
        err(f'lesson {name}: missing "**When it bites:**" hook')
    if size(path) > LESSON_MAX:
        err(f'lesson {name}: {size(path):,} B > {LESSON_MAX:,} B — condense; move the '
            'instance log to _archive/ and keep one canonical example')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.md', name):
        err(f'lesson {name}: filename must be kebab-case')

# --- INDEX.md sync -----------------------------------------------------------
indexed = {}
if not os.path.exists(INDEX):
    err('game-re-lessons/INDEX.md is missing')
else:
    category = None
    for lineno, line in enumerate(read(INDEX).split('\n'), 1):
        m = re.match(r'^## (\S+)\s*$', line)
        if m:
            category = m.group(1)
            if category not in CATEGORIES:
                err(f'INDEX.md:{lineno}: unknown category "{category}" (allowed: {", ".join(CATEGORIES)})')
            continue
        m = re.match(r'^\| `([^`]+\.md)` \| (.*) \|\s*$', line)
        if not m:
            continue
        name, hook = m.group(1), m.group(2).strip()
        if category is None:
            err(f'INDEX.md:{lineno}: row for {name} is outside any category section')
        if name in indexed:
            err(f'INDEX.md:{lineno}: {name} indexed twice (also line {indexed[name]})')
        indexed[name] = lineno
        if not os.path.exists(os.path.join(LESSONS, name)):
            err(f'INDEX.md:{lineno}: row for nonexistent lesson {name}')
        if len(hook) > HOOK_MAX:
            err(f'INDEX.md:{lineno}: hook for {name} is {len(hook)} chars > {HOOK_MAX}')
        if not hook:
            err(f'INDEX.md:{lineno}: empty hook for {name}')
    for name in lesson_files:
        if name not in indexed:
            err(f'lesson {name} has no INDEX.md row')

# --- corpora -----------------------------------------------------------------
agent_text = read(AGENT)
corpus_rows = re.findall(r'^\| `(~?/[^`]+)`[^|]*\|.*\| `([a-z0-9-]+\.md)` \|\s*$', agent_text, re.M)
table_corpora = {name for _, name in corpus_rows}
for root, name in corpus_rows:
    if not os.path.isdir(os.path.expanduser(root)):
        warn(f'corpora row for {name}: project root {root} does not exist on this machine '
             '(moved, merged, or on an unmounted drive?)')
corpus_files = {os.path.basename(p) for p in glob.glob(os.path.join(CORPORA, '*.md'))}
for name in sorted(table_corpora - corpus_files):
    err(f'game-re.md corpora table names {name}, which does not exist in game-re-corpora/')
for name in sorted(corpus_files - table_corpora):
    err(f'game-re-corpora/{name} has no row in game-re.md\'s corpora table')
for name in sorted(corpus_files):
    path = os.path.join(CORPORA, name)
    if size(path) > CORPUS_MAX:
        err(f'corpus {name}: {size(path):,} B > {CORPUS_MAX:,} B — it is a mandatory first '
            'read; narrative goes to game-re-corpora/details/')
    lessons_cited = re.findall(r'(?<![\w/.-])([a-z0-9][a-z0-9-]*\.md)\b', read(path))
    lessons_cited = [n for n in dict.fromkeys(lessons_cited) if n in lesson_files]
    if len(lessons_cited) > KEY_LESSONS_MAX:
        err(f'corpus {name}: cites {len(lessons_cited)} lessons > {KEY_LESSONS_MAX} — keep the key '
            'ones; the full sourced list belongs in details/')
for path in glob.glob(os.path.join(CORPORA, 'details', '*.md')):
    if os.path.basename(path) not in corpus_files:
        warn(f'{rel(path)} has no matching summary in game-re-corpora/')

# --- tooling map: bare filenames in game-re.md's Tooling map must exist -----
m = re.search(r'^# Tooling map\n(.*?)^# ', agent_text, re.M | re.S)
if m:
    tooling_files = {os.path.basename(p) for p in glob.glob(os.path.join(TOOLING, '*'))}
    for name in set(re.findall(r'`([a-z0-9][a-z0-9-]*\.md)`', m.group(1))):
        if name not in tooling_files and name not in lesson_files:
            err(f'game-re.md Tooling map: {name} is not a file in game-re-tooling/')
else:
    err('game-re.md has no "# Tooling map" section')

# --- archive orphans ---------------------------------------------------------
for path in glob.glob(os.path.join(LESSONS, '_archive', '*.md')):
    if os.path.basename(path) not in lesson_files:
        warn(f'{rel(path)} has no live lesson of the same name (renamed or merged?)')

# --- reference files ---------------------------------------------------------
for path in sorted(glob.glob(os.path.join(METHOD, '*.md')) + glob.glob(os.path.join(TOOLING, '*.md'))):
    if size(path) > REFERENCE_WARN:
        warn(f'{rel(path)} is {size(path):,} B — on-demand, but consider splitting by topic')

# --- references --------------------------------------------------------------
# Live (non-archive) files whose cross-references must resolve.
live = [AGENT, INDEX] + SKILLS
live += [os.path.join(LESSONS, n) for n in lesson_files]
live += [os.path.join(CORPORA, n) for n in corpus_files]
live += glob.glob(os.path.join(METHOD, '*.md')) + glob.glob(os.path.join(TOOLING, '*.md'))
known = {
    'game-re-lessons': set(lesson_files) | {'INDEX.md'},
    'game-re-corpora': corpus_files,
    'game-re-method': {os.path.basename(p) for p in glob.glob(os.path.join(METHOD, '*'))},
    'game-re-tooling': {os.path.basename(p) for p in glob.glob(os.path.join(TOOLING, '*'))},
}
all_known = set().union(*known.values())
archived = {os.path.basename(p) for p in glob.glob(os.path.join(LESSONS, '_archive', '*.md'))}
for path in live:
    if not os.path.exists(path):
        continue
    text = read(path)
    # Explicitly directory-qualified references must resolve.
    for d, name in set(re.findall(r'(game-re-(?:lessons|corpora|method|tooling))/([A-Za-z0-9_.-]+\.md)', text)):
        if name not in known[d]:
            err(f'{rel(path)}: reference to missing {d}/{name}')
    for name in set(re.findall(r'_archive/([a-z0-9-]+\.md)', text)):
        if name not in archived:
            err(f'{rel(path)}: reference to missing _archive/{name}')
    for name in set(re.findall(r'(?<![\w/.-])details/([a-z0-9-]+\.md)', text)):
        if not os.path.exists(os.path.join(CORPORA, 'details', name)):
            err(f'{rel(path)}: reference to missing game-re-corpora/details/{name}')
    # Bare backticked lesson-shaped slugs (3+ hyphens) that resolve nowhere.
    for name in set(re.findall(r'`([a-z0-9]+(?:-[a-z0-9]+){3,}\.md)`', text)):
        if name not in all_known:
            warn(f'{rel(path)}: `{name}` does not match any lesson/corpus/method/tooling file')

# --- usage ledger ------------------------------------------------------------
USAGE = os.path.join(LESSONS, 'USAGE.tsv')
if os.path.exists(USAGE):
    archived_lessons = {os.path.basename(p) for p in glob.glob(os.path.join(LESSONS, '_archive', '*.md'))}
    usage_lines = read(USAGE).split('\n')
    if usage_lines[0] != 'date\tlesson\tproject\tnote':
        err('game-re-lessons/USAGE.tsv: first line must be the header "date<TAB>lesson<TAB>project<TAB>note"')
    for lineno, line in enumerate(usage_lines[1:], 2):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) != 4 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', parts[0]):
            err(f'USAGE.tsv:{lineno}: malformed row (need date<TAB>lesson<TAB>project<TAB>note)')
        elif parts[1] not in lesson_files and parts[1] not in archived_lessons:
            err(f'USAGE.tsv:{lineno}: credit for unknown lesson {parts[1]} — rewrite it to the '
                'lesson\'s new name when renaming or merging')
else:
    err('game-re-lessons/USAGE.tsv is missing')

# --- inbox and lock ----------------------------------------------------------
pending = [p for p in glob.glob(os.path.join(INBOX, '*.md'))]
if pending:
    warn(f'{len(pending)} candidate lesson(s) pending in game-re-inbox/ — run re-learn-curate')
credit_files = glob.glob(os.path.join(INBOX, 'credits-*.tsv'))
if credit_files:
    warn(f'{len(credit_files)} credit file(s) pending in game-re-inbox/ (ingested by the next curate)')
if os.path.isdir(LOCK):
    import time
    age_min = (time.time() - os.path.getmtime(LOCK)) / 60
    if age_min > LOCK_STALE_MIN:
        warn(f'curation lock is {age_min:.0f} min old (stale; lock.sh acquire will break it)')

# --- report ------------------------------------------------------------------
quiet = '--quiet' in sys.argv
for w in warnings if not quiet else []:
    print('WARN ', w)
for e in errors:
    print('ERROR', e)
print(f'game-re.md {size(AGENT):,} B / {AGENT_MAX:,} · {len(lesson_files)} lessons · '
      f'{len(indexed)} indexed · {len(corpus_files)} corpora · '
      f'{len(errors)} error(s), {len(warnings)} warning(s)')
sys.exit(1 if errors else 0)
