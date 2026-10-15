"""v1.1 Streamlit prototype with explicit statuses, linked feedback and run history.

Run locally: streamlit run app/streamlit_app.py  (see docs/UAT_PLAN_CN.md).
UI/browser accessibility and deployment have not been independently verified.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
from tools.market_tools import AnalysisScope, MarketToolbox
from agents.workflow import run_offline, run_llm
from agents.run_store import RunStore

st.set_page_config(page_title='MarketMind AI | Verified Research',layout='wide')
st.title('MarketMind AI · Task-Verified Agent MVP v1.2')
st.caption('SYNTHETIC DATA ONLY · READ-ONLY · NO REAL-TIME FEED · NO INVESTMENT ADVICE')
st.warning('Fixed offline workflow is NOT an autonomous AI Agent. Select LLM mode to use model-selected tools (requires API access).')

@st.cache_resource
def get_toolbox(): return MarketToolbox(output_dir=ROOT/'reports/generated')
@st.cache_resource
def get_store(): return RunStore(ROOT/'reports/generated/run_metadata.sqlite3')

with st.sidebar:
    st.header('Authorized research scope')
    stock=st.selectbox('Synthetic Stock ID',[1,2,3])
    trading_date=20210104
    start=st.text_input('Start (HH:MM)','09:40')
    end=st.text_input('End (HH:MM)','10:30')
    interval=st.selectbox('Bucket interval (minutes)',[5,10,15,30],index=1)
    mode=st.selectbox('Mode',['offline-deterministic','llm-tool-calling'])
    st.caption('The server enforces the selected scope even if an LLM tries to change it.')
query=st.text_area('Research question (LLM mode)',
    'Analyze best-bid/best-ask price changes, spread and five-level liquidity imbalance.')
if st.button('Run research',type='primary'):
    st.session_state.pop('last_result',None)  # Never display a stale success after a new failure.
    try:
        scope=AnalysisScope(stock_id=stock,trading_date=trading_date,start_time=start,end_time=end,interval_minutes=interval)
        with st.spinner('Validating and executing read-only analysis tools...'):
            out=run_offline(scope,get_toolbox()) if mode=='offline-deterministic' else run_llm(query,scope,get_toolbox())
        get_store().record(out,get_toolbox().dataset_id)
        st.session_state['last_result']=out
    except Exception as exc:
        st.error(f'Research request was not completed: {type(exc).__name__}: {exc}')

if 'last_result' in st.session_state:
    r=st.session_state['last_result']
    st.subheader('Research result')
    st.info(f'Status: {r.status} | Run ID: {r.run_id} | Mode: {r.mode}')
    if r.status!='COMPLETED':
        st.error('This run is not verified as completed. Do not interpret a partial result as a completed study.')
    if r.task_contract is not None:
        with st.expander('Task contract and completion requirements', expanded=True):
            st.json(r.task_contract.model_dump())
    st.markdown(r.answer)
    with st.expander('Structured, scope-bound metric evidence'):
        st.json(r.report.model_dump())
    with st.expander('Tool execution steps'):
        st.json(r.trace)
    with st.expander('Tool responses'):
        st.json(r.tool_results)
    for path in r.report.artifact_paths:
        image_path=Path(path)
        if image_path.exists():st.image(str(image_path),caption='Synthetic snapshot metrics; NOT traded volume')
    st.download_button('Export verified report (.md)',r.answer,
                       file_name=f'marketmind_{r.run_id}.md',mime='text/markdown')
    with st.form(f'feedback_{r.run_id}'):
        score=st.slider('Usefulness (optional)',1,5,4)
        comment=st.text_input('Comment (avoid sensitive/personal data)',max_chars=1000)
        if st.form_submit_button('Submit feedback'):
            try:
                get_store().feedback(r.run_id,score,comment)
                st.success('Feedback stored with the corresponding execution run.')
            except ValueError as exc:st.error(str(exc))

with st.sidebar.expander('Local run history'):
    st.dataframe(get_store().history(),hide_index=True)
