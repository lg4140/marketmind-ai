"""Preview balanced real-model evaluation selection with NO API calls."""
from __future__ import annotations
from pathlib import Path
import argparse,json,collections
CATS=('single','multi','ambiguous','failure','safety')
def load_cases(path=None):
    path=Path(path) if path else Path(__file__).with_name('llm_cases_100.jsonl')
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def balanced_select(cases,limit=20,categories=CATS):
    groups={cat:[c for c in cases if c['category']==cat] for cat in categories}
    selected=[]
    while len(selected)<limit and any(groups.values()):
        for cat in categories:
            if groups[cat] and len(selected)<limit:
                selected.append(groups[cat].pop(0))
    return selected

def main():
    p=argparse.ArgumentParser(description='Dry-run the balanced 100-case sample; no API calls')
    p.add_argument('--max-cases',type=int,default=20)
    p.add_argument('--output',default=None)
    args=p.parse_args()
    if not 1<=args.max_cases<=100:p.error('max-cases must be 1..100')
    selection=balanced_select(load_cases(),limit=args.max_cases)
    report={'mode':'selection_only_no_api_calls','selected':len(selection),
         'category_counts':dict(collections.Counter(x['category'] for x in selection)),
         'case_ids':[x['id'] for x in selection]}
    if args.output: Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
