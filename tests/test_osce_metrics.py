from __future__ import annotations

import subprocess
import sys

import pytest


def _result(
    transcript_id: str,
    predicted_total: int,
    reference_total: int,
    predicted_flags: list[str],
    reference_safety_score: int,
    detected_missed: list[str],
    expected_missed: list[str],
):
    from app.evaluation.osce_metrics import RubricScoreResult

    predicted_scores = {
        "history_taking": 30,
        "communication": 15,
        "clinical_reasoning": 15,
        "empathy": 8,
        "closure": 7,
        "safety_red_flags": 8,
    }
    reference_scores = {
        "history_taking": 32,
        "communication": 14,
        "clinical_reasoning": 13,
        "empathy": 7,
        "closure": 6,
        "safety_red_flags": reference_safety_score,
    }

    return RubricScoreResult(
        transcript_id=transcript_id,
        case_id="case_001",
        student_level="good",
        predicted_scores=predicted_scores,
        reference_scores=reference_scores,
        score_errors={
            key: predicted_scores[key] - reference_scores[key]
            for key in predicted_scores
        },
        predicted_total_score=predicted_total,
        reference_total_score=reference_total,
        total_score_error=predicted_total - reference_total,
        predicted_pass=predicted_total >= 70,
        reference_pass=reference_total >= 70,
        detected_covered_items=["onset"],
        detected_missed_items=detected_missed,
        detected_red_flags=predicted_flags,
        expected_missed_items=expected_missed,
        expected_strengths=[],
        feedback_summary="summary",
    )


def _transcript(clinician_turns: list[str]):
    from app.evaluation.osce_metrics import ConversationTurn, ReferenceScores, SampleTranscript

    conversation = [ConversationTurn(speaker="patient", text="I have chest pressure.")]
    conversation.extend(
        ConversationTurn(speaker="clinician", text=text)
        for text in clinician_turns
    )
    return SampleTranscript(
        transcript_id="test_transcript",
        case_id="chest_pain_001",
        student_level="borderline",
        conversation=conversation,
        reference_scores=ReferenceScores(
            history_taking=20,
            communication=10,
            clinical_reasoning=10,
            empathy=2,
            closure=2,
            safety_red_flags=0,
        ),
        reference_total_score=40,
        expected_missed_items=[],
        expected_strengths=[],
        expected_feedback_summary="Test transcript.",
    )


def test_osce_metric_calculation():
    from app.evaluation.osce_metrics import benchmark_metric_calculator

    results = [
        _result("t1", 80, 75, ["acute coronary syndrome"], 8, ["onset"], ["onset"]),
        _result("t2", 50, 60, [], 0, ["suicidal ideation"], ["suicidal thoughts"]),
    ]

    metrics = benchmark_metric_calculator(results)

    assert metrics.total_score_mae == 7.5
    assert metrics.dimension_score_mae["history_taking"] == 2.0
    assert metrics.pass_fail_agreement == 1.0
    assert metrics.false_pass_count == 0
    assert metrics.false_fail_count == 0
    assert metrics.red_flag_detection_accuracy == 1.0
    assert metrics.missed_item_detection_accuracy == 1.0
    assert metrics.score_correlation is not None


def test_pass_fail_confusion_matrix_is_correct():
    from app.evaluation.osce_metrics import calculate_pass_fail_confusion_matrix

    results = [
        _result("true_pass", 80, 75, [], 0, [], []),
        _result("true_fail", 50, 60, [], 0, [], []),
        _result("false_pass", 80, 60, [], 0, [], []),
        _result("false_fail", 50, 75, [], 0, [], []),
    ]

    matrix = calculate_pass_fail_confusion_matrix(results)

    assert matrix.true_pass == 1
    assert matrix.true_fail == 1
    assert matrix.false_pass == 1
    assert matrix.false_fail == 1


def test_red_flag_detection_metric():
    from app.evaluation.osce_metrics import benchmark_metric_calculator

    results = [
        _result("t1", 80, 75, ["ectopic pregnancy"], 8, [], []),
        _result("t2", 50, 60, [], 8, [], []),
    ]

    metrics = benchmark_metric_calculator(results)

    assert metrics.red_flag_detection_accuracy == 0.5


def test_rubric_scorer_detects_covered_expected_questions():
    from app.evaluation.osce_metrics import rule_based_rubric_scorer
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")
    transcript = _transcript(
        [
            "When did it start, where is it located, and how severe is it on a scale of ten?",
            "Does it radiate to your arm or jaw, and do you feel sweating, nausea, or shortness of breath?",
            "Do you smoke, have high cholesterol, diabetes, hypertension, allergies, or take medications?",
        ]
    )

    result = rule_based_rubric_scorer(transcript, case)

    assert "onset" in result.detected_covered_items
    assert "location" in result.detected_covered_items
    assert "severity" in result.detected_covered_items
    assert "radiation" in result.detected_covered_items
    assert "associated symptoms" in result.detected_covered_items
    assert result.predicted_scores["history_taking"] > 20


def test_rubric_scorer_detects_missed_expected_questions():
    from app.evaluation.osce_metrics import rule_based_rubric_scorer
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")
    transcript = _transcript(["How long has this been happening?"])

    result = rule_based_rubric_scorer(transcript, case)

    assert "recreational drug use" in result.detected_missed_items
    assert "allergy history" in result.detected_missed_items
    assert result.predicted_scores["history_taking"] < 20


def test_empathy_statements_increase_empathy_score():
    from app.evaluation.osce_metrics import rule_based_rubric_scorer
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")
    neutral = rule_based_rubric_scorer(_transcript(["When did it start?"]), case)
    empathic = rule_based_rubric_scorer(
        _transcript(["I am sorry this is scary and I understand you are worried. When did it start?"]),
        case,
    )

    assert empathic.predicted_scores["empathy"] > neutral.predicted_scores["empathy"]


def test_closure_statements_increase_closure_score():
    from app.evaluation.osce_metrics import rule_based_rubric_scorer
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")
    no_closure = rule_based_rubric_scorer(_transcript(["When did it start?"]), case)
    closure = rule_based_rubric_scorer(
        _transcript(["When did it start? The next step is an urgent plan with emergency follow up."]),
        case,
    )

    assert closure.predicted_scores["closure"] > no_closure.predicted_scores["closure"]


def test_sample_transcript_schema_validation(tmp_path):
    from app.evaluation.osce_metrics import TranscriptValidationError, load_sample_transcript_file

    invalid = tmp_path / "invalid_transcript.yaml"
    invalid.write_text(
        """
transcript_id: invalid
case_id: chest_pain_001
student_level: good
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(TranscriptValidationError, match="conversation"):
        load_sample_transcript_file(invalid)


def test_sample_transcripts_load_successfully():
    from app.evaluation.osce_metrics import load_sample_transcripts

    transcripts = load_sample_transcripts("experiments/sample_transcripts")

    assert len(transcripts) >= 10
    assert {item.student_level for item in transcripts}.issuperset({"poor", "borderline", "good"})


def test_osce_benchmark_script_runs_with_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    completed = subprocess.run(
        [sys.executable, "experiments/run_osce_eval.py"],
        cwd=".",
        capture_output=True,
        text=True,
        check=True,
    )

    assert "OSCE evaluation complete" in completed.stdout
    assert "total_score_mae=" in completed.stdout
    assert "false_pass_count=" in completed.stdout
