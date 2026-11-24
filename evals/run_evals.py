"""Run every test question through the agent and score the answers. Writes evals/report.md and evals/results.json.

Checks per case: the expected tool was called, required phrases are present (all / any), forbidden phrases are
absent, citations point to sections that were really retrieved, and policy answers carry at least one citation.

    python -m evals.run_evals
"""
import json
from pathlib import Path

from agent.agent import SupportAgent
from data.make_db import build

HERE = Path(__file__).parent


def score(case: dict, r: dict) -> list[str]:
    a = r['answer'].lower()
    fails = []
    called = [t['tool'] for t in r['trace']]
    if case.get('tool') and case['tool'] not in called:
        fails.append(f"did not call {case['tool']}")
    fails += [f"missing '{p}'" for p in case.get('all', []) if p.lower() not in a]
    if case.get('any') and not any(p.lower() in a for p in case['any']):
        fails.append(f"none of {case['any']}")
    fails += [f"contains '{p}'" for p in case.get('none', []) if p.lower() in a]
    if r['invalid_citations']:
        fails.append(f"invalid citations {r['invalid_citations']}")
    if case.get('cite') and not r['citations']:
        fails.append('no citation')
    return fails


def main() -> None:
    build()  # fresh orders + empty tickets table for every run
    agent = SupportAgent()
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
    results, lines = [], ['| # | Question | Tools called | Result |', '|---|---|---|---|']
    for i, case in enumerate(cases, 1):
        r = agent.ask(case['q'])
        fails = score(case, r)
        results.append({'q': case['q'], 'answer': r['answer'], 'tools': [t['tool'] for t in r['trace']],
                        'citations': r['citations'], 'fails': fails})
        status = 'PASS' if not fails else 'FAIL: ' + '; '.join(fails)
        lines.append(f"| {i} | {case['q'][:70]} | {', '.join(t['tool'] for t in r['trace']) or '-'} | {status} |")
        print(f'{i:2}. {status[:90]:90}  {case["q"][:50]}')
    passed = sum(1 for r in results if not r['fails'])
    head = [f'# Evaluation: {passed} of {len(results)} passed', '', 'Model: gpt-4o-mini, temperature 0.', '']
    (HERE / 'report.md').write_text('\n'.join(head + lines) + '\n', encoding='utf-8')
    (HERE / 'results.json').write_text(json.dumps(results, indent=1), encoding='utf-8')
    print(f'\n{passed} of {len(results)} passed. Report: evals/report.md')


if __name__ == '__main__':
    main()
