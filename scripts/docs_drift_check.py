#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.github', '__pycache__'}
FORBIDDEN = [
    '/api/approval-requests',
    '/api/pending-approvals',
    '/api/bot/pending-approvals?agent_id=',
]


def iter_md_files(root: Path):
    for path in root.rglob('*.md'):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def main():
    findings = []
    for file in iter_md_files(ROOT):
        text = file.read_text(encoding='utf-8')
        for pattern in FORBIDDEN:
            if pattern in text:
                findings.append(f'{file.relative_to(ROOT)} contains legacy pattern: {pattern}')

    if findings:
        print('docs drift check failed:')
        for finding in findings:
            print(f'- {finding}')
        sys.exit(1)

    print('docs drift check passed.')


if __name__ == '__main__':
    main()
