from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.evaluation.osce_metrics import (
    calculate_osce_metrics,
    evaluate_osce_transcripts,
    load_sample_transcripts,
    write_osce_results,
)
from app.services.case_loader import load_case_templates


def main() -> int:
    cases = load_case_templates(ROOT / "case_templates")
    cases_by_id = {case.case_id: case for case in cases}
    transcripts = load_sample_transcripts(ROOT / "experiments" / "sample_transcripts")
    predictions = evaluate_osce_transcripts(transcripts, cases_by_id)
    metrics = calculate_osce_metrics(predictions)
    output_dir = ROOT / "experiments" / "results"
    write_osce_results(predictions, metrics, output_dir)

    print(f"OSCE evaluation complete: {len(predictions)} transcripts")
    print(f"Results written to: {output_dir}")
    print(f"total_score_mae={metrics.total_score_mae:.3f}")
    print(f"pass_fail_agreement={metrics.pass_fail_agreement:.3f}")
    print(f"false_pass_count={metrics.false_pass_count}")
    print(f"false_fail_count={metrics.false_fail_count}")
    print(f"red_flag_detection_accuracy={metrics.red_flag_detection_accuracy:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
