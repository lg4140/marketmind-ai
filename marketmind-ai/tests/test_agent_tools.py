import os
import pytest
from pydantic import ValidationError
from tools.market_tools import AnalysisScope,MarketToolbox,TOOLS,function_schemas
from agents.workflow import run_offline,run_llm
from agents.feedback import save_feedback

@pytest.fixture(scope="module")
def toolbox(tmp_path_factory): return MarketToolbox(output_dir=tmp_path_factory.mktemp("charts"))
@pytest.fixture
def scope(): return AnalysisScope(stock_id=1,trading_date=20210104,start_time="09:40",end_time="10:30")

def test_tool_catalog_matches_llm_schema():
    assert set(TOOLS)=={t["function"]["name"] for t in function_schemas()}

def test_tool_rejects_unknown(toolbox,scope):
    with pytest.raises(ValueError,match="not allowed"):
        toolbox.execute("execute_shell",scope.model_dump())

@pytest.mark.parametrize("bad",[
    {"stock_id":0}, {"trading_date":20211501},{"start_time":"25:99"},{"start_time":"10:30","end_time":"09:40"},{"interval_minutes":0},{"interval_minutes":61}
])
def test_scope_validation(scope,bad):
    with pytest.raises(ValidationError):AnalysisScope.model_validate({**scope.model_dump(),**bad})

def test_invalid_stock(toolbox,scope):
    with pytest.raises(ValueError,match="No records"):
        toolbox.execute("profile_dataset",{**scope.model_dump(),"stock_id":99})

@pytest.mark.parametrize("name",TOOLS)
def test_all_tools(toolbox,scope,name):
    r=toolbox.execute(name,scope.model_dump())
    assert r["status"]=="ok"
    assert r["evidence"]["data_kind"]=="synthetic"
    assert r["evidence"]["tool"]==name

def test_report_trace(toolbox,scope,tmp_path):
    output=run_offline(scope,toolbox,report_path=tmp_path/"report.md")
    assert len(output.trace)==len(TOOLS)
    assert all(t["status"]=="ok" for t in output.trace)
    assert "no LLM used" in output.answer
    assert "not confirmed" not in output.answer.lower() or "NOT observed" in output.answer
    assert (tmp_path/"report.md").exists()

def test_llm_mode_needs_key(toolbox,scope,monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    with pytest.raises(RuntimeError,match="OPENAI_API_KEY"):
        run_llm("analyze price",scope,toolbox)

def test_feedback(tmp_path, toolbox, scope):
    from agents.run_store import RunStore
    store=RunStore(tmp_path/'feedback.sqlite')
    r=run_offline(scope, toolbox)
    store.record(r, toolbox.dataset_id)
    save_feedback(store.path, r.run_id, 5, 'Useful')
    assert store.history()[0]['rating']==5
    with pytest.raises(ValueError, match='Unknown run_id'):
        save_feedback(store.path,'fake-run',5)
    with pytest.raises(ValueError):
        save_feedback(store.path,r.run_id,6)
