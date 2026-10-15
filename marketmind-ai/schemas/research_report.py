"""A report can only contain registered metrics derived from a successful tool output.

LLM prose is never accepted as a source for numerical metrics in v1.1.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from typing import Any

class EvidenceMetric(BaseModel):
    label: str
    value: float | int
    unit: str = ''
    evidence_tool: str
    dataset_id: str
    scope: dict

class ResearchReport(BaseModel):
    run_id: str
    status: Literal['COMPLETED', 'PARTIAL', 'FAILED', 'BLOCKED', 'INCOMPLETE']
    mode: str
    dataset_id: str
    scope: dict
    metrics: list[EvidenceMetric] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_paths: list[str] = Field(default_factory=list)
    task_contract: dict | None = None
    claims: list[dict[str,Any]] = Field(default_factory=list)
    profile: dict[str,Any] | None = None

_METRICS = {
    'analyze_microstructure': {
        'bid_quote_return_pct': '%', 'ask_quote_return_pct': '%',
        'mean_spread': 'price units', 'mean_relative_spread_bps': 'bps',
        'mean_best_level_imbalance': 'ratio', 'mean_obi5': 'ratio',
        'mean_bid_depth_5': 'shares', 'mean_ask_depth_5': 'shares',
    },
    'analyze_liquidity_events': {'candidate_new_visible_levels': 'candidate levels'},
}

def build_report(run_id: str, status: str, mode: str, scope: dict, results: list[dict], warnings=None,
                 dataset_id=None, task_contract=None) -> ResearchReport:
    metrics=[]; paths=[]
    dataset=dataset_id or 'unknown-dataset'
    profile=None
    for entry in results:
        payload=entry.get('output', {})
        if payload.get('status') != 'ok':
            continue
        evidence=payload.get('evidence', {})
        # Only trust exact server-supplied scope and dataset metadata.
        if not isinstance(evidence, dict) or any(evidence.get(k) != scope.get(k) for k in scope):
            raise ValueError('EVIDENCE_SCOPE_MISMATCH')
        incoming_dataset=str(evidence['dataset'])
        if dataset_id is not None and incoming_dataset!=dataset_id:
            raise ValueError('EVIDENCE_DATASET_MISMATCH')
        dataset=incoming_dataset
        tool=entry['tool']
        for name, unit in _METRICS.get(tool, {}).items():
            value=payload.get('result', {}).get(name)
            if type(value) in (int, float):
                metrics.append(EvidenceMetric(label=name, value=value, unit=unit,
                                              evidence_tool=tool, dataset_id=dataset, scope=scope))
        if tool=='profile_dataset': profile=payload.get('result',{})
        if tool=='generate_chart':
            path=payload.get('result', {}).get('image_path')
            if path: paths.append(str(path))
    claims=[]
    for metric in metrics:
        claims.append({'type':'DESCRIPTIVE','statement':metric.label,'value':metric.value,
                       'evidence_tool':metric.evidence_tool,'scope':metric.scope,
                       'limitation':'Synthetic descriptive data; no causal inference.'})
    return ResearchReport(run_id=run_id, status=status, mode=mode, dataset_id=dataset,
        scope=scope, metrics=metrics, artifact_paths=paths, warnings=warnings or [],
        task_contract=task_contract.model_dump() if task_contract is not None else None,claims=claims,profile=profile,
        limitations=[
          'All observations are seeded synthetic data, not live or historical market facts.',
          'Bid/ask quote changes are not trading returns or causal evidence.',
          'Candidate visible price levels do not establish order placement or queue position.',
        ])


def render_report(report: ResearchReport) -> str:
    header=['# MarketMind AI | Verified Synthetic Research',
       f'**Run ID:** `{report.run_id}`',
       f'**Status:** {report.status}; **Mode:** {report.mode}',
       f'**Data:** {report.dataset_id}',
       f'**Authorized scope:** {report.scope}', '',
       '## Task contract']
    if report.task_contract:
        header.append(f'- **Intent:** {report.task_contract.get("intent")} · **Required tools:** {report.task_contract.get("required_tools")}')
    else: header.append('- Offline fixed baseline (no user-intent planning)')
    if report.profile: header.append(f'- **Available data:** {report.profile}')
    header+=['', '## Tool-derived metrics']
    if report.metrics:
        for m in report.metrics:
            header.append(f'- **{m.label}:** {m.value} {m.unit}  — evidence: `{m.evidence_tool}` / `{m.dataset_id}`')
    else:
        header.append('- No verified numeric metrics are available for this run.')
    header += ['', '## Warnings'] + [f'- {w}' for w in (report.warnings or ['None'])]
    header += ['', '## Limitations'] + [f'- {x}' for x in report.limitations]
    if report.artifact_paths:
        header+=['','## Generated artifacts']+[f'- `{x}`' for x in report.artifact_paths]
    header+=['','All numeric metrics above are copied from validated, scope-matched Python tool outputs. Model free text is not used as a numeric source.']
    return '\n'.join(header)+'\n'
