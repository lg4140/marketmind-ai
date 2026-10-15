"""Regression tests for semantic completion, task scope, quality dependencies and output lineage."""
from __future__ import annotations
import types
import pytest
from agents.task_planner import plan_task
from agents.workflow import run_llm
from schemas.research_report import build_report
from tools.market_tools import MarketToolbox, AnalysisScope
from verification.quality_gate import classify_quality,require_acceptable,QualityGateError
from evaluation.select_cases import load_cases,balanced_select

@pytest.fixture(scope='module')
def box(tmp_path_factory):return MarketToolbox(output_dir=tmp_path_factory.mktemp('v12'))
@pytest.fixture
def scope():return AnalysisScope(stock_id=1,trading_date=20210104,start_time='09:40',end_time='10:30')

class Call:
    def __init__(self,name,args='{}',i='c1'):
        self.id=i;self.function=types.SimpleNamespace(name=name,arguments=args)
    def model_dump(self):return {'id':self.id,'type':'function','function':{'name':self.function.name,'arguments':self.function.arguments}}
class Response:
    def __init__(self,*calls):self.content='UNVERIFIED: 999%';self.tool_calls=list(calls)
class Client:
    def __init__(self,*responses):
        self.responses=list(responses)
        self.chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))
    def create(self,**kwargs):return types.SimpleNamespace(choices=[types.SimpleNamespace(message=self.responses.pop(0))])

def test_incomplete_missing_liquidity_tool(box,scope):
    r=run_llm('Count candidate newly visible price levels',scope,box,client=Client(Response(Call('analyze_microstructure')),Response()))
    assert r.status=='INCOMPLETE' and 'MISSING_TOOLS' in r.answer

def test_chart_is_not_obi_evidence(box,scope):
    r=run_llm('Compute OBI and show a chart',scope,box,client=Client(Response(Call('generate_chart')),Response()))
    assert r.status=='INCOMPLETE' and 'MISSING_TOOLS' in r.answer

def test_profile_only_completes(box,scope):
    r=run_llm('Show available stocks and dates',scope,box,client=Client(Response(Call('profile_dataset')),Response()))
    assert r.status=='COMPLETED' and r.report.profile['stocks_available']==[1,2,3]
    assert not r.report.metrics

def test_quality_only_completes(box,scope):
    r=run_llm('Check data quality for the selected stock',scope,box,client=Client(Response()))
    assert r.status=='COMPLETED' and [x['tool'] for x in r.trace]==['validate_dataset']

def test_tool_scope_mismatch_rejected(box,scope):
    r=run_llm('Analyze spread',scope,box,client=Client(Response(Call('analyze_microstructure','{"stock_id": 99}'))))
    assert r.status=='INCOMPLETE' and 'SCOPE_CONFLICT' in r.answer
    assert all(x['tool']!='analyze_microstructure' for x in r.trace)

@pytest.mark.parametrize('query,expected',[
    ('Stock 99: calculate spread','SCOPE_CONFLICT'),
    ('Analyze 2021-01-05 price quotes','SCOPE_CONFLICT'),
    ('Plot quotes from 09:00 to 10:00','SCOPE_CONFLICT'),
    ('Place a limit order','UNSUPPORTED_ACTION'),
    ('Buy 100 shares of Stock 1','UNSUPPORTED_ACTION'),
    ('Analyze the market.','NEEDS_CLARIFICATION'),
    ('How do I change my API key?','UNSUPPORTED_ACTION')])
def test_conservative_intent_decisions(scope,query,expected):
    assert plan_task(query,scope).decision==expected

def test_no_chart_negation(scope):
    c=plan_task('Analyze spread without a chart',scope)
    assert c.decision=='SUPPORTED' and 'generate_chart' not in c.required_tools

def test_quality_gate_dependent_on_trade():
    data={'snapshot_quality':{'issues':[]},'trade_quality':{'issues':[{'code':'no_trades_in_window'}]},'trade_match_rate':0.0}
    quote=classify_quality(data,require_trade=False)
    assert quote['status']=='WARN' and len(quote['warnings'])>=1
    assert classify_quality(data,require_trade=True)['status']=='BLOCK'
    with pytest.raises(QualityGateError):require_acceptable(data,require_trade=True)

def test_report_seed_lineage_when_no_tools(scope):
    r=build_report('runid','INCOMPLETE','llm-tool-calling',scope.model_dump(),[],dataset_id='synthetic-demo-seed-7')
    assert r.dataset_id=='synthetic-demo-seed-7'

def test_balanced_selector_all_categories():
    cases=load_cases();sample=balanced_select(cases,limit=20)
    assert len(cases)==100 and len(sample)==20
    assert {c['category'] for c in sample}=={'single','multi','ambiguous','failure','safety'}
    assert all(sum(c['category']==category for c in sample)==4 for category in ('single','multi','ambiguous','failure','safety'))

def test_no_cross_dataset_evidence(box,scope):
    out=box.execute('analyze_microstructure',scope.model_dump())
    with pytest.raises(ValueError,match='EVIDENCE_DATASET_MISMATCH'):
        build_report('r','COMPLETED','llm-tool-calling',scope.model_dump(),[{'tool':'analyze_microstructure','output':out}],dataset_id='different-dataset')

def test_claims_are_metric_bound(box,scope):
    out=box.execute('analyze_microstructure',scope.model_dump())
    report=build_report('r','COMPLETED','test',scope.model_dump(),[{'tool':'analyze_microstructure','output':out}],dataset_id=box.dataset_id)
    assert len(report.claims)==len(report.metrics)
    assert all(c['evidence_tool']=='analyze_microstructure' and c['type']=='DESCRIPTIVE' for c in report.claims)
