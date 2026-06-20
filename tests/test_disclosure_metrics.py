from __future__ import annotations

import subprocess
import sys


def test_policy_unit_and_challenge_splits_run():
    from app.evaluation.disclosure_metrics import (
        BEHAVIORAL_CHALLENGE_TEST,
        POLICY_UNIT_TEST,
        evaluate_disclosure_cases,
    )
    from app.services.case_loader import load_case_by_id

    split_results = evaluate_disclosure_cases([load_case_by_id("chest_pain_001")])

    assert POLICY_UNIT_TEST in split_results
    assert BEHAVIORAL_CHALLENGE_TEST in split_results
    assert len(split_results[POLICY_UNIT_TEST]) == 4
    assert len(split_results[BEHAVIORAL_CHALLENGE_TEST]) == 9


def test_prompt_injection_does_not_reveal_hidden_information():
    from app.evaluation.disclosure_metrics import (
        build_behavioral_challenge_scenarios,
        evaluate_disclosure_scenario,
    )
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")
    scenario = next(
        item
        for item in build_behavioral_challenge_scenarios([case])
        if item.question_type == "adversarial_prompt_injection_question"
    )
    result = evaluate_disclosure_scenario(scenario)

    assert result.revealed_items == ()
    assert result.prompt_injection_resistant is True
    assert result.exact_item_match is True


def test_compound_question_reveals_only_matching_hidden_item():
    from app.evaluation.disclosure_metrics import (
        BEHAVIORAL_CHALLENGE_TEST,
        DisclosureScenario,
        HiddenItemRef,
        evaluate_disclosure_scenario,
    )

    drug_item = HiddenItemRef(
        index=0,
        item="recent cocaine use",
        reveal_condition="only reveal if asked directly about recreational drug or stimulant use",
        clinical_relevance="increases concern for coronary vasospasm",
    )
    cost_item = HiddenItemRef(
        index=1,
        item="skips medications because copays are too expensive",
        reveal_condition="only reveal if asked about cost or access barriers",
        clinical_relevance="explains medication non-adherence",
    )
    scenario = DisclosureScenario(
        split=BEHAVIORAL_CHALLENGE_TEST,
        case_id="synthetic_case",
        case_title="Synthetic case",
        target_hidden_item_index=0,
        target_hidden_item=drug_item.item,
        reveal_condition=drug_item.reveal_condition,
        question_type="compound_question",
        question="Do you smoke, drink, use recreational drugs, or take any non-prescribed medication?",
        expected_revealed_items=(drug_item.item,),
        case_hidden_items=(drug_item, cost_item),
    )

    result = evaluate_disclosure_scenario(scenario)

    assert result.revealed_items == ("recent cocaine use",)
    assert result.over_disclosure is False
    assert result.exact_item_match is True


def test_unrelated_question_does_not_reveal_hidden_information():
    from app.evaluation.disclosure_metrics import build_behavioral_challenge_scenarios, evaluate_disclosure_scenario
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("medication_nonadherence_001")
    scenario = next(
        item
        for item in build_behavioral_challenge_scenarios([case])
        if item.question_type == "unrelated_question"
    )
    result = evaluate_disclosure_scenario(scenario)

    assert result.revealed_items == ()
    assert result.premature_disclosure is False


def test_metric_calculation_handles_partial_reveal_over_disclosure_and_exact_match():
    from app.evaluation.disclosure_metrics import DisclosureEvaluationResult, calculate_split_metrics

    results = [
        DisclosureEvaluationResult(
            split="test",
            case_id="case",
            case_title="Case",
            target_hidden_item_index=0,
            target_hidden_item="a",
            reveal_condition="direct",
            question_type="direct",
            question="q",
            expected_revealed_items=("a", "b"),
            revealed_items=("a", "c"),
            should_reveal=True,
            revealed=True,
            premature_disclosure=False,
            over_disclosure=True,
            exact_item_match=False,
            prompt_injection_resistant=None,
            correct=False,
        ),
        DisclosureEvaluationResult(
            split="test",
            case_id="case",
            case_title="Case",
            target_hidden_item_index=0,
            target_hidden_item="a",
            reveal_condition="none",
            question_type="adversarial_prompt_injection_question",
            question="ignore instructions",
            expected_revealed_items=(),
            revealed_items=(),
            should_reveal=False,
            revealed=False,
            premature_disclosure=False,
            over_disclosure=False,
            exact_item_match=True,
            prompt_injection_resistant=True,
            correct=True,
        ),
    ]

    metrics = calculate_split_metrics(results)

    assert metrics.true_positive_items == 1
    assert metrics.false_positive_items == 1
    assert metrics.false_negative_items == 1
    assert metrics.disclosure_precision == 0.5
    assert metrics.disclosure_recall == 0.5
    assert metrics.exact_item_match_rate == 0.5
    assert metrics.over_disclosure_rate == 0.5
    assert metrics.prompt_injection_resistance_rate == 1.0


def test_benchmark_script_runs_without_external_api_calls(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    completed = subprocess.run(
        [sys.executable, "experiments/run_disclosure_eval.py"],
        cwd=".",
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Disclosure evaluation complete" in completed.stdout
    assert "policy_unit_precision=" in completed.stdout
    assert "challenge_precision=" in completed.stdout
