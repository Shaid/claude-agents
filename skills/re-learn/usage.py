#!/usr/bin/env python3
"""Lesson usage: credits (a lesson changed what an agent did) vs reads.

Usage:
  python3 ~/.claude/skills/re-learn/usage.py                 # report
  python3 ~/.claude/skills/re-learn/usage.py --summary       # one line
  python3 ~/.claude/skills/re-learn/usage.py --ingest --token <T>
      Merge game-re-inbox/credits-*.tsv into game-re-lessons/USAGE.tsv.
      Only the curator may run this, holding the curation lock (<T> from
      skills/re-learn-curate/lock.sh acquire).

Credits are self-reported in game-re's "Lessons applied" report section and
written as `date<TAB>lesson.md<TAB>project<TAB>note` rows. Reads are counted
from Read tool calls in ~/.claude/projects transcripts, so they include reads
that changed nothing — a read is opportunity, a credit is value.
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser('~/.claude')
LESSONS = os.path.join(HOME, 'agents', 'game-re-lessons')
USAGE = os.path.join(LESSONS, 'USAGE.tsv')
INBOX = os.path.join(HOME, 'agents', 'game-re-inbox')
LOCK_OWNER = os.path.join(HOME, 'agents', '.re-learn.lock', 'owner')
TRANSCRIPTS = os.path.join(HOME, 'projects')
HEADER = 'date\tlesson\tproject\tnote'
STALE_DAYS = 60


def lesson_names():
    return {os.path.basename(p) for p in glob.glob(os.path.join(LESSONS, '*.md'))} - {'INDEX.md'}


def archived_names():
    return {os.path.basename(p) for p in glob.glob(os.path.join(LESSONS, '_archive', '*.md'))}


def parse_row(line):
    """Return (date, lesson, project, note) or raise ValueError."""
    parts = line.rstrip('\n').split('\t')
    if len(parts) != 4:
        raise ValueError(f'expected 4 tab-separated fields, got {len(parts)}')
    date, lesson, project, note = (p.strip() for p in parts)
    datetime.date.fromisoformat(date)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.md', lesson):
        raise ValueError(f'bad lesson filename {lesson!r}')
    if not project or not note:
        raise ValueError('empty project or note')
    return date, lesson, project, note


def read_usage():
    if not os.path.exists(USAGE):
        return []
    with open(USAGE, encoding='utf-8') as f:
        lines = f.read().split('\n')
    return [parse_row(l) for l in lines[1:] if l.strip()]


def ingest(token):
    try:
        with open(LOCK_OWNER, encoding='utf-8') as f:
            owner = f.read().strip()
    except OSError:
        sys.exit('refusing to ingest: curation lock is not held')
    if owner != token:
        sys.exit(f'refusing to ingest: lock is owned by {owner!r}, not the given token')
    live, archived = lesson_names(), archived_names()
    accepted, rejected = [], []
    files = sorted(glob.glob(os.path.join(INBOX, 'credits-*.tsv')))
    for path in files:
        with open(path, encoding='utf-8') as f:
            for line in f:
                if not line.strip() or line.startswith('date\t'):
                    continue
                try:
                    row = parse_row(line)
                    if row[1] not in live and row[1] not in archived:
                        raise ValueError(f'no such lesson {row[1]}')
                    accepted.append(row)
                except ValueError as e:
                    rejected.append(f'{os.path.basename(path)}: {e}: {line.rstrip()}')
    if accepted:
        new = not os.path.exists(USAGE)
        with open(USAGE, 'a', encoding='utf-8') as f:
            if new:
                f.write(HEADER + '\n')
            for row in accepted:
                f.write('\t'.join(row) + '\n')
    if rejected:
        os.makedirs(os.path.join(INBOX, 'rejected'), exist_ok=True)
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        with open(os.path.join(INBOX, 'rejected', f'credits-{stamp}.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(rejected) + '\n')
    for path in files:
        os.remove(path)
    print(f'ingested {len(accepted)} credit(s) from {len(files)} file(s); rejected {len(rejected)}')


def count_reads():
    """Read tool calls on live lesson files, from session transcripts."""
    reads, last = {}, {}
    pat = re.compile(r'game-re-lessons/([a-z0-9][a-z0-9-]*\.md)$')
    for path in glob.glob(os.path.join(TRANSCRIPTS, '**', '*.jsonl'), recursive=True):
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                for line in f:
                    if 'game-re-lessons/' not in line or '"Read"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    content = d.get('message', {}).get('content')
                    if not isinstance(content, list):
                        continue
                    for b in content:
                        if b.get('type') != 'tool_use' or b.get('name') != 'Read':
                            continue
                        m = pat.search(str(b.get('input', {}).get('file_path', '')))
                        if m:
                            n = m.group(1)
                            reads[n] = reads.get(n, 0) + 1
                            ts = d.get('timestamp', '')[:10]
                            if ts > last.get(n, ''):
                                last[n] = ts
        except OSError:
            continue
    return reads, last


def added_dates():
    """First-commit date per lesson (untracked lessons count as today)."""
    out = subprocess.run(
        ['git', '-C', HOME, 'log', '--diff-filter=A', '--format=@%ad', '--date=short',
         '--name-only', '--', 'agents/game-re-lessons/'],
        capture_output=True, text=True).stdout
    dates, cur = {}, None
    for line in out.splitlines():
        if line.startswith('@'):
            cur = line[1:]
        elif line.strip():
            dates[os.path.basename(line.strip())] = cur  # log is newest-first; keep oldest
    return dates


def report(summary_only):
    live = lesson_names()
    credits = {}
    for _, lesson, project, _ in read_usage():
        credits.setdefault(lesson, set()).add(project)
    ncred = {n: 0 for n in live}
    for _, lesson, _, _ in read_usage():
        if lesson in ncred:
            ncred[lesson] += 1
    reads, last = count_reads()
    credited = [n for n in live if ncred[n]]
    never_read = [n for n in live if not reads.get(n)]
    if summary_only:
        print(f'{len(live)} lessons · {len(credited)} credited ({sum(ncred.values())} credits) · '
              f'{len(live) - len(never_read)} ever read · {len(never_read)} never read')
        return
    today = datetime.date.today()
    added = added_dates()

    def age(n):
        d = added.get(n)
        return (today - datetime.date.fromisoformat(d)).days if d else 0

    print('## Most credited (changed what an agent did)')
    for n in sorted(credited, key=lambda n: -ncred[n])[:15]:
        print(f'{ncred[n]:4}  {n}  [{", ".join(sorted(credits[n]))}]')
    if not credited:
        print('  (no credits recorded yet)')
    print('\n## Read often, never credited (trigger fires but the lesson may not pay off)')
    for n in sorted((n for n in live if reads.get(n, 0) >= 5 and not ncred[n]), key=lambda n: -reads[n])[:15]:
        print(f'{reads[n]:4} reads, last {last.get(n, "?")}  {n}')
    stale = sorted((n for n in never_read if age(n) >= STALE_DAYS and not ncred[n]), key=age, reverse=True)
    print(f'\n## Never read, never credited, older than {STALE_DAYS} days — rewrite the hook or archive ({len(stale)})')
    for n in stale[:40]:
        print(f'{age(n):4}d  {n}')
    if len(stale) > 40:
        print(f'  … and {len(stale) - 40} more')
    print()
    report(True)


if __name__ == '__main__':
    if '--ingest' in sys.argv:
        i = sys.argv.index('--token') if '--token' in sys.argv else -1
        if i < 0 or i + 1 >= len(sys.argv):
            sys.exit('usage: usage.py --ingest --token <lock token>')
        ingest(sys.argv[i + 1])
    else:
        report('--summary' in sys.argv)
