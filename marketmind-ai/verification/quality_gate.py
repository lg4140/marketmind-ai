"""Task-aware quality gates: quote-only research does not depend on trade prints."""
from __future__ import annotations
from typing import Any

BLOCK_CODES=frozenset({'duplicate_key','invalid_price','invalid_quantity','crossed_or_invalid_levels',
    'invalid_timestamp','non_monotonic_cumulative','empty_dataset','no_trades_in_window'})

class QualityGateError(ValueError):
    code='QUALITY_BLOCKED'
    def __init__(self,issues:list[dict[str,Any]]):
        self.issues=issues
        super().__init__('QUALITY_BLOCKED: '+', '.join(sorted({str(x.get('code')) for x in issues})))

def classify_quality(report:dict, require_trade:bool=False, min_trade_match_rate:float=0.8)->dict:
    entries=[]
    for source,key in [('snapshot','snapshot_quality'),('trade','trade_quality')]:
        for issue in report.get(key,{}).get('issues',[]):
            code=issue.get('code','unknown')
            severity='BLOCK' if code in BLOCK_CODES and (source=='snapshot' or require_trade) else 'WARN'
            entries.append({'source':source,**issue,'severity':severity})
    if 'trade_match_rate' in report:
        rate=report.get('trade_match_rate')
        if not isinstance(rate,(int,float)) or rate < min_trade_match_rate:
            entries.append({'source':'alignment','code':'low_trade_match_rate','observed':rate,
                'threshold':min_trade_match_rate,'severity':'BLOCK' if require_trade else 'WARN'})
    blockers=[x for x in entries if x['severity']=='BLOCK']
    warnings=[x for x in entries if x['severity']=='WARN']
    return {'status':'BLOCK' if blockers else ('WARN' if warnings else 'PASS'),
            'blockers':blockers,'warnings':warnings,'trade_required':require_trade}

def require_acceptable(report:dict, require_trade:bool=False,min_trade_match_rate:float=0.8)->dict:
    decision=classify_quality(report,require_trade=require_trade,min_trade_match_rate=min_trade_match_rate)
    if decision['blockers']:raise QualityGateError(decision['blockers'])
    return decision
