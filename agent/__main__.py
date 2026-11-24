"""python -m agent "Can I return an opened candle?" """
import json
import sys

from .agent import SupportAgent


def main() -> None:
    question = ' '.join(sys.argv[1:]) or input('Question: ')
    result = SupportAgent().ask(question)
    for step in result['trace']:
        print(f"  tool {step['tool']}({json.dumps(step['args'])})")
    print('\n' + result['answer'])
    print(f"\n[verified: {result['verified']}; citations: {', '.join(result['citations']) or 'none'}]")


if __name__ == '__main__':
    main()
