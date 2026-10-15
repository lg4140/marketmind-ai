"""CLI: execute read-only demo and save run-scoped artifacts/metadata."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from tools.market_tools import MarketToolbox,AnalysisScope
from agents.workflow import run_offline,run_llm
from agents.run_store import RunStore

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['offline','llm'],default='offline')
    p.add_argument('--stock-id',type=int,default=1)
    p.add_argument('--date',type=int,default=20210104)
    p.add_argument('--start',default='09:40')
    p.add_argument('--end',default='10:30')
    p.add_argument('--interval',type=int,default=10)
    p.add_argument('--question',default='Analyze quote returns, spread and five-level imbalance.')
    p.add_argument('--model',default=None)
    args=p.parse_args()
    scope=AnalysisScope(stock_id=args.stock_id,trading_date=args.date,
                        start_time=args.start,end_time=args.end,interval_minutes=args.interval)
    directory=Path('reports/generated');directory.mkdir(parents=True,exist_ok=True)
    box=MarketToolbox(output_dir=directory)
    result=run_offline(scope,box) if args.mode=='offline' else run_llm(args.question,scope,box,model=args.model)
    RunStore(directory/'run_metadata.sqlite3').record(result,box.dataset_id)
    (directory/f'{result.run_id}_report.md').write_text(result.answer,encoding='utf-8')
    (directory/f'{result.run_id}_trace.json').write_text(json.dumps({
        'run_id':result.run_id,'status':result.status,'mode':result.mode,'scope':result.scope,
        'trace':result.trace,'report':result.report.model_dump()},ensure_ascii=False,indent=2),encoding='utf-8')
    print(result.answer)
    print(f'Status: {result.status}; run ID: {result.run_id}; artifacts saved under {directory}')
    if result.status!='COMPLETED':raise SystemExit(2)

if __name__=='__main__':main()
