"""Read-only scaffold verification, not an application evaluation."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['AGENTS.md', 'README.md', '.env.example', '.gitignore', 'Assignment.pdf',
            'docs/STATUS.md', 'docs/REQUIREMENTS.md', 'docs/ARCHITECTURE.md',
            'docs/WORKFLOW.md', 'docs/DECISIONS.md', 'docs/SUBMISSION.md',
            'evals/PLAN.md', 'evals/SCENARIOS.md', 'evals/RUN_TEMPLATE.md',
            'evals/ENVIRONMENT.md']
SKILLS = ['crisp-dm-step', 'evaluate-component', 'review-deliverable']

def main():
    errors = []
    if sys.version_info < (3, 11):
        errors.append('Python 3.11+ required')
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f'Missing: {name}')
    for name in SKILLS:
        path = ROOT / '.agents/skills' / name / 'SKILL.md'
        if not path.is_file():
            errors.append(f'Missing skill: {name}')
        elif not path.read_text(encoding='utf-8').startswith(f'---\nname: {name}\ndescription: '):
            errors.append(f'Invalid metadata: {name}')
    for path in ROOT.rglob('*.md'):
        if any(p in {'.git', '.venv', 'tmp'} for p in path.parts):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                if not (path.parent / target.split('#')[0]).exists():
                    errors.append(f'Broken link: {path.name}: {target}')
    env = ROOT / '.env.example'
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#') and ('=' not in line or line.split('=', 1)[1].strip()):
                errors.append('Nonempty or invalid env example')
    for error in errors:
        print(f'FAIL: {error}')
    if errors:
        return 1
    print('PASS: files, skill metadata, local Markdown links, empty env example')
    print('NOT TESTED: automatic discovery/routing, application, API, NLP quality')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
