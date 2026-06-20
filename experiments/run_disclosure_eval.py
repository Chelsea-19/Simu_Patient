from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.evaluation.disclosure_metrics import (
    BEHAVIORAL_CHALLENGE_TEST,
    POLICY_UNIT_TEST,
    calculate_disclosure_benchmark_metrics,
    evaluate_disclosure_cases,
    write_disclosure_results,
)
from app.services.case_loader import load_case_templates


def main() -> int:
    cases = load_case_templates(ROOT / "case_templates")
    cases_with_hidden_info = [case for case in cases if case.hidden_information]
    split_results = evaluate_disclosure_cases(cases_with_hidden_info)
    policy_unit_results = split_results[POLICY_UNIT_TEST]
    challenge_results = split_results[BEHAVIORAL_CHALLENGE_TEST]
    metrics = calculate_disclosure_benchmark_metrics(policy_unit_results, challenge_results)
    output_dir = ROOT / "experiments" / "results"
    write_disclosure_results(policy_unit_results, challenge_results, metrics, output_dir)

    print("Disclosure evaluation complete")
    print(f"Results written to: {output_dir}")
    print(f"policy_unit_scenarios={metrics.policy_unit.total_scenarios}")
    print(f"policy_unit_precision={metrics.policy_unit_precision:.3f}")
    print(f"policy_unit_recall={metrics.policy_unit_recall:.3f}")
    print(f"policy_unit_premature_disclosure_rate={metrics.policy_unit_premature_disclosure_rate:.3f}")
    print(f"challenge_scenarios={metrics.behavioral_challenge.total_scenarios}")
    print(f"challenge_precision={metrics.challenge_precision:.3f}")
    print(f"challenge_recall={metrics.challenge_recall:.3f}")
    print(f"challenge_premature_disclosure_rate={metrics.challenge_premature_disclosure_rate:.3f}")
    print(f"challenge_exact_item_match_rate={metrics.challenge_exact_item_match_rate:.3f}")
    print(f"over_disclosure_rate={metrics.over_disclosure_rate:.3f}")
    if metrics.prompt_injection_resistance_rate is not None:
        print(f"prompt_injection_resistance_rate={metrics.prompt_injection_resistance_rate:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
