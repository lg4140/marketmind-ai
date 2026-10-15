"""Server-side task completion verification; never trusts model narrative."""
from __future__ import annotations
from dataclasses import dataclass,field
from agents.task_planner import TaskContract

@dataclass
class TaskVerification:
    passed: bool
    missing_tools: list[str] = field(default_factory=list)
    missing_metrics: list[str] = field(default_factory=list)
    missing_artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def errors_list(self):
        return (['MISSING_TOOLS: '+','.join(self.missing_tools)] if self.missing_tools else []) + \
          (['MISSING_METRICS: '+','.join(self.missing_metrics)] if self.missing_metrics else []) + \
          (['MISSING_ARTIFACTS: '+','.join(self.missing_artifacts)] if self.missing_artifacts else []) + self.errors

def verify_task(contract:TaskContract,results:list[dict],report)->TaskVerification:
    if contract.decision!='SUPPORTED':
        return TaskVerification(False,errors=[f'NON_EXECUTABLE_TASK: {contract.decision}'])
    success={r['tool'] for r in results if r.get('output',{}).get('status')=='ok'}
    labels={m.label for m in report.metrics}
    # Validate existence and run-scoped path via report's evidenced artifacts; do not trust model text.
    missing_tools=[x for x in contract.required_tools if x not in success]
    missing_metrics=[x for x in contract.required_metrics if x not in labels]
    missing_artifacts=['chart'] if 'chart' in contract.required_artifacts and not report.artifact_paths else []
    return TaskVerification(not any([missing_tools,missing_metrics,missing_artifacts]),missing_tools,missing_metrics,missing_artifacts)
