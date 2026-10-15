"""Validate planned 100-case LLM test catalog (does not execute a model)."""
import json
from collections import Counter
from pathlib import Path
from tools.market_tools import AnalysisScope, TOOLS

def validate():
    items=[json.loads(line) for line in Path(__file__).with_name('llm_cases_100.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(items)==100 and len({x['id'] for x in items})==100
    counts=Counter(x['category'] for x in items)
    assert counts=={'single':20,'multi':25,'ambiguous':15,'failure':20,'safety':20}
    for i in items:
        AnalysisScope.model_validate(i['authorized_scope'])
        assert set(i['required_tools'])<=set(TOOLS)
        assert not (set(i['required_tools']) & set(i['forbidden_tools']))
        assert i['execution_status']=='NOT_RUN'
    return dict(counts)

if __name__=='__main__': print('Catalog valid; NOT a live-model score:',validate())
