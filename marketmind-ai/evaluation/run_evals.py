"""Offline fixture evaluation of schema, control flow, error *cause* and tool order.

Does NOT test autonomous model choice or the quality of LLM-generated prose.
"""
from __future__ import annotations
from pathlib import Path
import json
from pydantic import ValidationError
from tools.market_tools import MarketToolbox, AnalysisScope, TOOLS
from agents.workflow import run_offline

CASE_FILE=Path(__file__).with_name('test_cases.jsonl')

def run():
    cases=[json.loads(line) for line in CASE_FILE.read_text(encoding='utf-8').splitlines() if line.strip()]
    box=MarketToolbox(output_dir=Path('reports/generated'))
    scored=[]
    for c in cases:
        try:
            scope=AnalysisScope.model_validate(c['scope'])
        except ValidationError:
            actual={'status':'error','error_code':'INVALID_SCOPE','tools':[]}
        else:
            try:
                r=run_offline(scope,box)
                if r.status=='COMPLETED':
                    actual={'status':'success','error_code':None,'tools':[t['tool'] for t in r.trace]}
                else:
                    last=r.tool_results[-1]['output'] if r.tool_results else {}
                    code=last.get('error_code') or ('QUALITY_BLOCKED' if r.status=='BLOCKED' else 'UNEXPECTED_ERROR')
                    if code=='ValueError' and 'No records' in last.get('error',''):code='NO_RECORDS'
                    actual={'status':'error','error_code':code,'tools':[t['tool'] for t in r.trace]}
            except Exception as exc:
                # An unrelated crash is NEVER counted as an expected user-input error.
                actual={'status':'error','error_code':'UNEXPECTED_ERROR','tools':[], 'exception':type(exc).__name__}
        passed=(actual['status']==c['expected'] and
                actual['error_code']==c.get('expected_error_code') and
                actual['tools']==c['expected_tools'])
        scored.append({'id':c['id'],'expected':c['expected'], 'actual':actual,
                       'expected_error_code':c.get('expected_error_code'),
                       'expected_tools':c['expected_tools'],'passed':passed})
    report={'evaluation_type':'deterministic offline fixture and runtime contract only',
            'dataset':'synthetic-demo-seed-42','total':len(scored),
            'passed':sum(x['passed'] for x in scored),
            'pass_rate':round(sum(x['passed'] for x in scored)/len(scored),4),
            'cases':scored,
            'limitations':'This does not evaluate LLM interpretation, live API stability, latency, user research or production readiness.'}
    out=Path('evaluation/results/offline_eval_results_v1_2.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    return report

if __name__=='__main__':run()
