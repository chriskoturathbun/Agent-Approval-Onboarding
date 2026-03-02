#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.github', '__pycache__'}

REPLACEMENTS = [
    ('/api/bot/pending-approvals?agent_id=kotubot', '/api/bot/pending-approvals'),
    ('/api/bot/pending-approvals?agent_id=$AGENT_ID', '/api/bot/pending-approvals'),
    ('/api/pending-approvals', '/api/bot/pending-approvals'),
    ('/api/approval-requests', '/api/bot/approval-requests'),
]


def iter_md_files(root: Path):
    for path in root.rglob('*.md'):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def main():
    changed = 0
    for file in iter_md_files(ROOT):
        before = file.read_text(encoding='utf-8')
        after = before
        for old, new in REPLACEMENTS:
            after = after.replace(old, new)
        if after != before:
            file.write_text(after, encoding='utf-8')
            changed += 1
            print(f'updated: {file.relative_to(ROOT)}')
    print(f'docs drift fix complete. files changed: {changed}')


if __name__ == '__main__':
    main()
