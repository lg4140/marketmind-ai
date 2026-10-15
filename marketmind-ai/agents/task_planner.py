"""Conservative, auditable intent-to-contract baseline. Not an LLM semantic classifier.

Unknown/underspecified tasks abstain. The contract is authoritative for completion,
not for permissions: the server-provided AnalysisScope is always authoritative.
"""
from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, Field
from tools.market_tools import AnalysisScope

ToolName = Literal['profile_dataset','validate_dataset','analyze_microstructure','analyze_liquidity_events','generate_chart']

class TaskContract(BaseModel):
    decision: Literal['SUPPORTED','NEEDS_CLARIFICATION','UNSUPPORTED_ACTION','SCOPE_CONFLICT']
    intent: str
    scope: dict
    required_tools: list[ToolName] = Field(default_factory=list)
    required_metrics: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    query: str
    planner_version: str = 'deterministic-contract-v1.2'

TRADE_ACTION = re.compile(r'\b(?:place|submit|execute|send)\s+(?:(?:a|an|the)\s+)?(?:market\s+|limit\s+)?(?:order|trade)\b|\b(?:buy|sell|purchase|short)\s+(?:\w+\s+){0,3}(?:shares|stocks|stock|contracts)\b|\bguarantee\s+(?:a\s+)?(?:profit|return|gain)|(?:下单|买入|卖出|代我交易|执行交易|保证盈利|保证收益|帮我交易)',re.I)
OTHER_UNSUPPORTED = re.compile(r'(?i)(?:api\s*key|secret\s*key|environment\s*variable|delete\s+(?:logs|traces)|publish\s+(?:raw|proprietary)|live\s+(?:price|market)|today.s\s+live|realtime\s+(?:price|feed)|real.world\s+price|未经授权|删除日志|泄露密钥|实时股价|实时行情|公布原始数据|真实股价)')
NEG_CHART = re.compile(r'(?i)(?:no\s+(?:chart|plot|graph)|without\s+(?:a\s+)?(?:chart|plot|graph)|不(?:要|需要)(?:画图|图表)|无需(?:画图|图表))')


def plan_task(query: str, scope: AnalysisScope) -> TaskContract:
    q=query.strip()
    s=scope.model_dump()
    base=dict(query=q,scope=s)
    def c(decision, intent, tools=(), metrics=(), artifacts=(), notes=()):
        return TaskContract(decision=decision,intent=intent,required_tools=list(dict.fromkeys(tools)),
            required_metrics=list(dict.fromkeys(metrics)),required_artifacts=list(artifacts),notes=list(notes),**base)
    if not q: return c('NEEDS_CLARIFICATION','empty_request',notes=['Please specify a research question.'])
    if TRADE_ACTION.search(q) or OTHER_UNSUPPORTED.search(q):
        return c('UNSUPPORTED_ACTION','out_of_scope',notes=['This is synthetic, read-only analysis. No trading, secrets, unlicensed data, or live quotes.'])
    # Reject explicit changes to authorization; do not silently substitute server scope.
    for m in re.finditer(r'(?i)\b(?:stock|symbol|股票|证券)\s*#?\s*(\d+)\b',q):
        if int(m.group(1))!=scope.stock_id: return c('SCOPE_CONFLICT','scope_mismatch',notes=['Requested stock differs from authorized scope.'])
    for m in re.finditer(r'\b20\d{6}\b|\b20\d{2}-\d{2}-\d{2}\b',q):
        dt=m.group(0).replace('-','')
        if dt!=str(scope.trading_date): return c('SCOPE_CONFLICT','scope_mismatch',notes=['Requested date differs from authorized scope.'])
    times=re.findall(r'(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)',q)
    if len(times)>=2:
        normalize=lambda t: f'{int(t.split(":")[0]):02d}:{t.split(":")[1]}'
        if normalize(times[0])!=scope.start_time or normalize(times[1])!=scope.end_time:
            return c('SCOPE_CONFLICT','scope_mismatch',notes=['Requested time range differs from authorized scope.'])
    mm=re.search(r'(?i)(?:bucket|interval|sampling|采样间隔|时间桶|桶长)\s*(?:size)?\s*(?:of|=|:)?\s*(-?\d+)\s*(?:min|分钟)',q)
    if mm and int(mm.group(1))!=scope.interval_minutes:
        return c('SCOPE_CONFLICT','scope_mismatch',notes=['Requested time-bucket size differs from authorized scope.'])
    lowered=q.lower()
    if re.search(r'(?i)\b(?:analy[sz]e|calculate|study)\s+price\b',q):
        q=q+' quote'  # Interpret explicit request to analyze price as quote-based descriptive metrics.
    profile = bool(re.search(r'(?i)\b(?:available|coverage|inventory|dataset|list\s+stocks|which\s+stocks|timestamps)\b|可用|有哪些股票|数据概览|覆盖范围|数据集',q))
    quality = bool(re.search(r'(?i)\b(?:quality|validat|duplicates?|missing|alignment|integrity)\b|数据质量|校验|缺失|重复|对齐',q))
    micro = bool(re.search(r'(?i)\b(?:spread|imbalance|obi\d*|depth|quote|return|market microstructure|bid|ask|price chang|price movement|price trend|price return|microstructure|bps|volatility)\b|价差|盘口|买卖盘|不平衡|深度|收益|价格|波动|报价',q))
    liquidity = bool(re.search(r'(?i)\b(?:candidate|liquidity event|new(?:ly)? visible|free.hole|price.level addition|event candidates|liquidity shift|liquidity event|liquidity)\b|新增流动性|新增档位|空档|候选档位|流动性事件|新可见',q))
    chart = bool(re.search(r'(?i)\b(?:plot|chart|graph|visualiz|figure|draw)\b|画图|图表|可视化|绘图',q)) and not NEG_CHART.search(q)
    # An underspecified generic task must not be incorrectly stamped complete.
    generic = bool(re.fullmatch(r'(?i)(?:analy[sz]e|research|study|分析)(?:\s+the\s+market)?\.?',q))
    if generic or not any((profile,quality,micro,liquidity,chart)):
        return c('NEEDS_CLARIFICATION','underspecified',notes=['Specify one of data coverage, data quality, spread/OBI, liquidity events or charts.'])
    tools=[];metrics=[];art=[]
    if profile: tools.append('profile_dataset')
    if quality: tools.append('validate_dataset')
    if micro:
        tools.append('analyze_microstructure')
        keys={
            'spread':['mean_spread','mean_relative_spread_bps'],
            'imbalance':['mean_best_level_imbalance','mean_obi5'],
            'obi':['mean_obi5'],
            'depth':['mean_bid_depth_5','mean_ask_depth_5'],
            'quote':['bid_quote_return_pct','ask_quote_return_pct'],
            'return':['bid_quote_return_pct','ask_quote_return_pct'],
            'bps':['mean_relative_spread_bps'],
        }
        for k,fields in keys.items():
            if k in lowered: metrics.extend(fields)
        if '价差' in q: metrics.append('mean_spread')
        if '不平衡' in q: metrics.append('mean_obi5')
        if '收益' in q or '报价' in q:metrics.extend(['bid_quote_return_pct','ask_quote_return_pct'])
        if not metrics: metrics.append('mean_spread')
    if liquidity:
        tools.append('analyze_liquidity_events');metrics.append('candidate_new_visible_levels')
    if chart:
        tools.append('generate_chart'); art.append('chart')
    notes=[]
    if re.search(r'(?i)(?:caus|because|why|导致|原因|因果)',q):
        notes.append('Descriptive synthetic quotes cannot establish a causal explanation.')
    return c('SUPPORTED','research',tools,metrics,art,notes)
