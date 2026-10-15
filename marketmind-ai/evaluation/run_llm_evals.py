"""Opt-in REAL MODEL smoke-eval runner. Requires API key, explicit --confirm-live.

Only automatically checks status and required/forbidden tool names; qualitative
correctness and numeric evidence MUST be manually reviewed before publication.
"""
from __future__ import annotations
import argparse,json,os,collections
from evaluation.select_cases import balanced_select
from datetime import datetime,timezone
from pathlib import Path
from tools.market_tools import MarketToolbox,AnalysisScope
from agents.workflow import run_llm

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--confirm-live',action='store_true')
    p.add_argument('--max-cases',type=int,default=3)
    p.add_argument('--model',default=None)
    p.add_argument('--categories',default='single,multi,ambiguous,failure,safety')
    p.add_argument('--output',default='evaluation/results/live_eval_requires_review.json')
    a=p.parse_args()
    if not a.confirm_live or not os.getenv('OPENAI_API_KEY'):
        p.error('Real paid API calls require --confirm-live and OPENAI_API_KEY')
    if a.max_cases<1 or a.max_cases>20:
        p.error('max-cases must be in 1..20 to avoid accidental cost spikes')
    cases=[json.loads(s) for s in Path(__file__).with_name('llm_cases_100.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    categories=[x.strip() for x in a.categories.split(',') if x.strip()]
    invalid=set(categories)-{'single','multi','ambiguous','failure','safety'}
    if invalid: p.error('Unknown category: '+str(sorted(invalid)))
    selected=balanced_select(cases,limit=a.max_cases,categories=categories)
    box=MarketToolbox()
    rows=[]
    for c in selected:
        result=run_llm(c['query'],AnalysisScope.model_validate(c['authorized_scope']),box,model=a.model)
        tools=[x['tool'] for x in result.trace]
        rows.append({'case_id':c['id'],'status':result.status,'actual_tools':tools,
          'tool_contract_pass':all(t in tools for t in c['required_tools']) and not any(t in tools for t in c['forbidden_tools']),
          'expected_status':c['expected_status'],'category':c['category'],
          'human_review':'PENDING', 'run_id':result.run_id, 'trace':result.trace,
          'metrics':[m.model_dump() for m in result.report.metrics]})
    output={'run_at':datetime.now(timezone.utc).isoformat(),'model':a.model or os.getenv('OPENAI_MODEL','gpt-4.1-mini'),
            'cases_run':len(rows),'selection_counts':dict(collections.Counter(c['category'] for c in selected)),'model_verified':False,
            'limitations':'No automated claim of factuality/task success; human review required.', 'cases':rows}
    dest=Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Live calls finished; human review required. Output:',dest)

if __name__=='__main__':main()
