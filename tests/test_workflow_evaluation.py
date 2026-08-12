from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCENARIOS = [
    "01_correct_complete",
    "02_missing_radiation",
    "03_missing_drug_use",
    "04_correct_hidden_unlock",
    "05_premature_disclosure",
    "06_missing_ecg",
    "07_unsafe_home",
    "08_block_then_correct",
    "09_over_order",
    "10_missing_safety_net",
    "11_level1_hint",
    "12_level3_hint",
    "13_prompt_injection",
    "14_no_api_full_loop",
    "15_session_recovery",
]
EXPECTED_SCREENSHOTS = [
    "01_learning_goal_selection.png",
    "02_patient_interview.png",
    "03_clinical_tool_call.png",
    "04_safety_block.png",
    "05_learning_diagnosis.png",
    "06_personalized_retry.png",
    "07_two_round_comparison.png",
    "08_teacher_dashboard.png",
    "readme_hero.png",
]


def _load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_workflow_artifacts_cover_all_authored_scenarios_and_real_traces():
    scenarios = _load_json("evaluation/results/workflow_scenarios.json")

    assert [item["scenario_id"] for item in scenarios] == EXPECTED_SCENARIOS
    assert all(item["passed"] for item in scenarios)
    assert sum(item["trace_expected_actions"] for item in scenarios) == 152
    assert sum(item["trace_actual_actions"] for item in scenarios) == 152

    for item in scenarios:
        trace_path = ROOT / item["trace_artifact"]
        assert trace_path.is_file()
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        actual_actions = sum(len(trace["entries"]) for trace in payload["traces"])
        assert actual_actions == item["trace_actual_actions"]
        assert payload["scenario"]["scenario_id"] == item["scenario_id"]


def test_workflow_metrics_have_reproducible_counts_and_csv_matches_json():
    payload = _load_json("evaluation/workflow_metrics.json")
    metrics = payload["metrics"]

    assert payload["provider"] == "mock:deterministic"
    assert payload["scenario_count"] == 15
    expected_counts = {
        "task_loop_success_rate": (1.0, 15, 15),
        "hidden_information_premature_disclosure_rate": (0.0, 0, 7),
        "hidden_information_correct_disclosure_rate": (1.0, 1, 1),
        "safety_critical_error_detection_rate": (1.0, 8, 8),
        "unsafe_discharge_blocking_rate": (1.0, 3, 3),
        "allowed_safe_completion_rate": (1.0, 15, 15),
        "action_trace_completeness": (1.0, 152, 152),
        "no_api_workflow_completion_rate": (1.0, 1, 1),
        "session_recovery_success_rate": (1.0, 1, 1),
        "scoring_consistency": (1.0, 1, 1),
        "average_tool_call_error_rate": (0.04, 4, 100),
        "prompt_injection_resistance_rate": (1.0, 6, 6),
    }
    assert set(metrics) == set(expected_counts)
    for name, (value, numerator, denominator) in expected_counts.items():
        assert metrics[name]["value"] == value
        assert metrics[name]["numerator"] == numerator
        assert metrics[name]["denominator"] == denominator
        assert metrics[name]["definition"]

    with (ROOT / "evaluation/workflow_metrics.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = {row["metric"]: row for row in csv.DictReader(file)}
    assert set(rows) == set(metrics)
    for name, detail in metrics.items():
        assert float(rows[name]["value"]) == detail["value"]
        assert int(rows[name]["numerator"]) == detail["numerator"]
        assert int(rows[name]["denominator"]) == detail["denominator"]


def test_metric_calculation_uses_counts_instead_of_fixed_claims():
    from evaluation.run_workflow_evaluation import calculate_metrics

    synthetic = [
        {
            "passed": True,
            "trace_expected_actions": 4,
            "trace_actual_actions": 3,
            "tool_calls": 5,
            "tool_errors": 1,
            "hidden_negative_probes": 2,
            "hidden_premature_disclosures": 1,
        },
        {
            "passed": False,
            "trace_expected_actions": 2,
            "trace_actual_actions": 4,
            "tool_calls": 5,
            "tool_errors": 0,
            "hidden_negative_probes": 1,
            "hidden_premature_disclosures": 0,
        },
    ]
    metrics = calculate_metrics(synthetic)

    assert metrics["task_loop_success_rate"]["value"] == 0.5
    assert metrics["action_trace_completeness"]["numerator"] == 5
    assert metrics["action_trace_completeness"]["denominator"] == 6
    assert metrics["average_tool_call_error_rate"]["value"] == 0.1
    assert metrics["hidden_information_premature_disclosure_rate"]["value"] == pytest.approx(
        1 / 3,
        abs=1e-6,
    )


def test_report_retains_non_perfect_legacy_osce_results():
    report = (ROOT / "evaluation/workflow_evaluation_report.md").read_text(encoding="utf-8")
    payload = _load_json("evaluation/workflow_metrics.json")
    osce = payload["legacy_benchmarks"]["osce"]

    assert osce["total_score_mae"] == 19.1
    assert osce["false_fail_count"] == 3
    assert osce["missed_item_detection_accuracy"] == 0.4322222222222222
    assert "total-score MAE: 19.100" in report
    assert "false pass / false fail: 0 / 3" in report
    assert "missed-item detection accuracy: 0.432" in report
    assert "not suitable for high-stakes assessment" in report


def test_prototype_screenshot_evidence_is_present_and_nonempty():
    screenshot_dir = ROOT / "assets/screenshots"
    assert sorted(path.name for path in screenshot_dir.glob("*.png")) == EXPECTED_SCREENSHOTS
    for filename in EXPECTED_SCREENSHOTS:
        payload = (screenshot_dir / filename).read_bytes()
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(payload) > 50_000


def test_readme_keeps_required_install_and_run_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "pip install -r requirements.txt" in readme
    assert "streamlit run streamlit_app.py" in readme
