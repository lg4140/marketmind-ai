"""v1.1 regressions for failures observed in previous PM/engineering audit."""
import copy
import types
import sqlite3
import pytest
import pandas as pd
from src.sample_data_generator import generate_synthetic_market_data
from src.data_loader import validate_market_data
from tools.market_tools import AnalysisScope, MarketToolbox
from agents.workflow import run_offline, run_llm
from agents.run_store import RunStore
from schemas.research_report import build_report
from verification.quality_gate import QualityGateError

@pytest.fixture
def box(tmp_path): return MarketToolbox(output_dir=tmp_path/'figs')
@pytest.fixture
def scope():return AnalysisScope(stock_id=1,trading_date=20210104,start_time='09:40',end_time='10:30')

class DummyMsg:
    def __init__(self, text='Fabricated 25% quote return', calls=None):
        self.content=text
        self.tool_calls=calls or []
class DummyCall:
    def __init__(self, name, id='c1'):
        self.id=id; self.function=types.SimpleNamespace(name=name,arguments='{}')
    def model_dump(self):
        return {'id':self.id,'type':'function','function':{'name':self.function.name,'arguments':'{}'}}
class DummyClient:
    def __init__(self, messages):
        self.replies=list(messages)
        self.chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))
    def create(self, **kwargs):
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=self.replies.pop(0))])

def test_malformed_price_returns_issue_not_valueerror():
    s,_=generate_synthetic_market_data(n_stocks=1,n_snapshots=3)
    s['bid1p'] = s['bid1p'].astype(object)
    s.loc[s.index[1],'bid1p']='not-a-number'
    q=validate_market_data(s,'snapshot')
    assert not q['passed']
    assert any(i['code']=='invalid_price' and i['field']=='bid1p' for i in q['issues'])

def test_block_bad_snapshots_in_offline(box,scope):
    where=(box.snapshot.id==1)&(box.snapshot.time=='09:45:00')
    assert where.sum()==1
    box.snapshot.loc[where,'ask1p']=box.snapshot.loc[where,'bid1p']
    out=run_offline(scope,box)
    assert out.status=='BLOCKED'
    assert [x['tool'] for x in out.trace]==['profile_dataset','validate_dataset']
    assert not out.report.metrics and 'QUALITY_BLOCKED' in out.answer

def test_block_bad_snapshots_in_direct_tool(box,scope):
    ix=box.snapshot[(box.snapshot.id==1)&(box.snapshot.time=='09:45:00')].index[0]
    box.snapshot.loc[ix,'bid1p']=-1
    with pytest.raises(QualityGateError):
        box.execute('analyze_microstructure',scope.model_dump())

def test_llm_unverified_answer_not_published(box,scope):
    fake=DummyClient([DummyMsg(text='Guaranteed 25% gains, buy immediately')])
    r=run_llm('Analyze quote returns',scope,box,client=fake)
    assert r.status=='INCOMPLETE' and not r.report.metrics
    assert '25%' not in r.answer
    assert [x['tool'] for x in r.trace]==['validate_dataset']

def test_llm_selected_tool_verified_metrics_not_model_prose(box,scope):
    fake=DummyClient([DummyMsg(calls=[DummyCall('analyze_microstructure')]), DummyMsg(text='The stock gained 200%')])
    r=run_llm('Analyze spread',scope,box,client=fake)
    assert r.status=='COMPLETED' and any(m.label=='mean_spread' for m in r.report.metrics)
    assert '200%' not in r.answer
    assert [x['tool'] for x in r.trace]==['validate_dataset','analyze_microstructure']

def test_llm_server_scope_cannot_be_changed(box,scope):
    c=DummyCall('analyze_microstructure')
    c.function.arguments='{"stock_id":999,"start_time":"12:00"}'
    fake=DummyClient([DummyMsg(calls=[c]),DummyMsg()])
    r=run_llm('Analyze spread',scope,box,client=fake)
    assert r.status=='INCOMPLETE'
    assert 'SCOPE_CONFLICT' in r.answer
    assert [x['tool'] for x in r.trace]==['validate_dataset']

def test_llm_repeated_tools_do_not_loop(box,scope):
    fake=DummyClient([DummyMsg(calls=[DummyCall('analyze_microstructure')]),
                      DummyMsg(calls=[DummyCall('analyze_microstructure','c2')])])
    r=run_llm('spread',scope,box,client=fake)
    assert r.status=='FAILED'
    assert len([x for x in r.trace if x['tool']=='analyze_microstructure'])==1

def test_llm_read_only_rejects_trading(box,scope):
    r=run_llm('Please execute a trade',scope,box,client=DummyClient([]))
    assert r.status=='BLOCKED' and not r.trace

def test_chart_artifacts_isolated_by_interval_and_run_id(box,scope):
    a=box.execute('generate_chart',{**scope.model_dump(),'_run_id':'run-A'})['result']['image_path']
    b=box.execute('generate_chart',{**scope.model_dump(),'interval_minutes':5,'_run_id':'run-A'})['result']['image_path']
    c=box.execute('generate_chart',{**scope.model_dump(),'_run_id':'run-B'})['result']['image_path']
    assert len({a,b,c})==3
    assert all(pd.io.common.file_exists(x) for x in (a,b,c))

def test_mismatched_scope_evidence_rejected(box,scope):
    actual=box.execute('analyze_microstructure',scope.model_dump())
    corrupt=copy.deepcopy(actual)
    corrupt['evidence']['stock_id']=999
    with pytest.raises(ValueError,match='EVIDENCE_SCOPE_MISMATCH'):
        build_report('test','COMPLETED','offline-deterministic',scope.model_dump(),[{'tool':'analyze_microstructure','output':corrupt}])

def test_feedback_requires_existing_run(box,scope,tmp_path):
    store=RunStore(tmp_path/'runs.sqlite')
    r=run_offline(scope,box)
    store.record(r,box.dataset_id)
    store.feedback(r.run_id,5,'Clear')
    assert store.history()[0]['rating']==5
    with pytest.raises(ValueError,match='Unknown run_id'):store.feedback('not-a-run',5,'No')
    with sqlite3.connect(store.path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM steps WHERE run_id=?',(r.run_id,)).fetchone()[0]==5

def test_llm_tool_budget_enforced(box,scope):
    fake=DummyClient([DummyMsg(calls=[DummyCall('analyze_microstructure'),DummyCall('generate_chart','c2')])])
    r=run_llm('Analyze spread and make a chart',scope,box,client=fake,max_tool_calls=1)
    assert r.status=='INCOMPLETE' and 'TOOL_BUDGET_EXCEEDED' in r.answer
