from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.case_template_file import ClinicalCaseTemplate

PASS_THRESHOLD = 70

DIMENSIONS = (
    "history_taking",
    "communication",
    "clinical_reasoning",
    "empathy",
    "closure",
    "safety_red_flags",
)

DIMENSION_MAXIMA = {
    "history_taking": 40,
    "communication": 20,
    "clinical_reasoning": 20,
    "empathy": 10,
    "closure": 10,
    "safety_red_flags": 10,
}

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "anything",
    "asked",
    "been",
    "before",
    "being",
    "does",
    "from",
    "have",
    "history",
    "into",
    "like",
    "more",
    "only",
    "other",
    "pain",
    "question",
    "recently",
    "risk",
    "symptoms",
    "that",
    "their",
    "them",
    "there",
    "these",
    "this",
    "what",
    "when",
    "where",
    "with",
    "your",
}

QUESTION_SYNONYMS = {
    "aggravating factors": ("worse", "trigger", "triggers", "aggravating", "exertion", "activity"),
    "alcohol use": ("alcohol", "drink", "drinking"),
    "allergy history": ("allergy", "allergies", "allergic"),
    "associated symptoms": ("associated", "sweating", "nausea", "shortness", "breath", "fever", "vomiting"),
    "cardiovascular risk factors": ("hypertension", "cholesterol", "smoking", "diabetes", "family", "heart"),
    "character": ("character", "pressure", "sharp", "burning", "dull", "quality", "feel"),
    "cost barriers": ("cost", "copay", "expensive", "afford", "insurance"),
    "cough": ("cough", "sputum", "phlegm"),
    "current medications": ("medication", "medications", "medicine", "medicines", "take", "taking"),
    "duration": ("duration", "long", "since", "started", "weeks", "days", "hours"),
    "fever": ("fever", "temperature", "chills"),
    "flank pain": ("flank", "back", "kidney"),
    "frequency": ("frequency", "frequent", "often"),
    "glycemic control": ("glucose", "sugar", "a1c", "diabetes", "control"),
    "headache red flags": ("worst", "sudden", "neurologic", "vision", "weakness", "fever", "stiff"),
    "location": ("where", "location", "located", "site"),
    "manic symptoms": ("mania", "manic", "elevated", "racing", "impulsive"),
    "medication adherence": ("adherence", "taking", "miss", "missed", "stopped", "forget"),
    "medication history": ("medication", "medications", "medicine", "medicines", "take", "taking"),
    "medication side effects": ("side", "effect", "effects", "diarrhea", "rash", "dizzy"),
    "menstrual history": ("period", "periods", "menstrual", "cycle", "pregnancy", "pregnant"),
    "neurologic symptoms": ("weakness", "numbness", "speech", "vision", "neurologic"),
    "onset": ("onset", "start", "started", "begin", "began", "when"),
    "over-the-counter medications": ("ibuprofen", "naproxen", "otc", "over", "counter", "nsaid"),
    "past medical history": ("medical", "conditions", "diagnosed", "illness", "surgery"),
    "pregnancy possibility": ("pregnant", "pregnancy"),
    "prior infections": ("prior", "previous", "before", "infection", "infections"),
    "radiation": ("radiate", "radiates", "radiation", "arm", "jaw", "back", "shoulder"),
    "recreational drug use": ("drug", "drugs", "cocaine", "stimulant", "stimulants", "substance"),
    "relieving factors": ("better", "relieve", "relieving", "rest", "helps"),
    "severity": ("severity", "severe", "bad", "scale", "ten", "10"),
    "sexual history": ("sexual", "sex", "partner", "partners", "sti", "std"),
    "sleep": ("sleep", "insomnia", "falling", "staying"),
    "smoking history": ("smoke", "smoking", "smoker", "cigarettes", "pack"),
    "social history": ("work", "home", "living", "support", "alcohol", "smoking", "drugs"),
    "substance use": ("substance", "drug", "drugs", "alcohol", "cocaine", "stimulant"),
    "suicidal ideation": ("suicide", "suicidal", "thought", "thoughts", "self-harm", "harm", "kill"),
    "support system": ("support", "family", "friends", "help", "home"),
    "travel history": ("travel", "trip", "flight", "abroad"),
    "urine output": ("urine", "pee", "urination", "diaper", "wet"),
    "urinary symptoms": ("urine", "pee", "burning", "dysuria", "frequency", "urgency"),
}

EMPATHY_MARKERS = (
    "sorry",
    "stressful",
    "worried",
    "understand",
    "must be",
    "support",
    "concerned",
    "difficult",
    "scary",
)

COMMUNICATION_MARKERS = (
    "tell me",
    "can you",
    "could you",
    "what concerns",
    "does that make sense",
    "questions",
    "summarize",
    "let me",
    "explain",
)

CLOSURE_MARKERS = (
    "plan",
    "next step",
    "go to",
    "urgent",
    "follow up",
    "safety",
    "return",
    "emergency",
    "come back",
    "seek help",
    "monitoring",
)

REASONING_MARKERS = (
    "concern",
    "risk",
    "rule out",
    "because",
    "possible",
    "likely",
    "urgent",
    "test",
    "exam",
    "ecg",
    "blood",
    "diagnosis",
)


class TranscriptValidationError(ValueError):
    """Raised when a sample transcript file cannot be loaded or validated."""


class ConversationTurn(BaseModel):
    speaker: str
    text: str

    model_config = ConfigDict(extra="forbid")


class ReferenceScores(BaseModel):
    history_taking: int = Field(ge=0, le=40)
    communication: int = Field(ge=0, le=20)
    clinical_reasoning: int = Field(ge=0, le=20)
    empathy: int = Field(ge=0, le=10)
    closure: int = Field(ge=0, le=10)
    safety_red_flags: int = Field(ge=0, le=10)

    model_config = ConfigDict(extra="forbid")


class SampleTranscript(BaseModel):
    transcript_id: str
    case_id: str
    student_level: str
    conversation: List[ConversationTurn]
    reference_scores: ReferenceScores
    reference_total_score: int = Field(ge=0, le=100)
    expected_missed_items: List[str]
    expected_strengths: List[str]
    expected_feedback_summary: str

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class RubricScoreResult:
    transcript_id: str
    case_id: str
    student_level: str
    predicted_scores: Dict[str, int]
    reference_scores: Dict[str, int]
    score_errors: Dict[str, int]
    predicted_total_score: int
    reference_total_score: int
    total_score_error: int
    predicted_pass: bool
    reference_pass: bool
    detected_covered_items: List[str]
    detected_missed_items: List[str]
    detected_red_flags: List[str]
    expected_missed_items: List[str]
    expected_strengths: List[str]
    feedback_summary: str


@dataclass(frozen=True)
class PassFailConfusionMatrix:
    true_pass: int
    true_fail: int
    false_pass: int
    false_fail: int


@dataclass(frozen=True)
class OsceMetrics:
    total_score_mae: float
    dimension_score_mae: Dict[str, float]
    score_correlation: float | None
    pass_fail_agreement: float
    false_pass_count: int
    false_fail_count: int
    pass_fail_confusion_matrix: Dict[str, int]
    red_flag_detection_accuracy: float
    missed_item_detection_accuracy: float
    total_transcripts: int


# Backward-compatible name retained for external imports from earlier benchmark versions.
OscerScorePrediction = RubricScoreResult


def _transcript_files(transcript_dir: Path) -> Iterable[Path]:
    return sorted(list(transcript_dir.glob("*.yaml")) + list(transcript_dir.glob("*.yml")))


def load_sample_transcript_file(path: Path | str) -> SampleTranscript:
    transcript_path = Path(path)
    try:
        raw = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TranscriptValidationError(f"Could not read transcript {transcript_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise TranscriptValidationError(f"Invalid YAML in {transcript_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise TranscriptValidationError(f"{transcript_path} must contain a YAML mapping at the top level.")

    try:
        return SampleTranscript.model_validate(raw)
    except ValidationError as exc:
        raise TranscriptValidationError(f"Invalid transcript {transcript_path}: {exc}") from exc


def load_sample_transcripts(transcript_dir: Path | str) -> List[SampleTranscript]:
    directory = Path(transcript_dir)
    if not directory.exists():
        raise TranscriptValidationError(f"Sample transcript directory does not exist: {directory}")

    transcripts = [load_sample_transcript_file(path) for path in _transcript_files(directory)]
    transcript_ids = [transcript.transcript_id for transcript in transcripts]
    duplicates = sorted({item for item in transcript_ids if transcript_ids.count(item) > 1})
    if duplicates:
        raise TranscriptValidationError(f"Duplicate transcript_id values found: {', '.join(duplicates)}")

    return sorted(transcripts, key=lambda item: item.transcript_id)


def rule_based_rubric_scorer(
    transcript: SampleTranscript,
    case: ClinicalCaseTemplate,
) -> RubricScoreResult:
    """Score one transcript with transparent deterministic rubric rules."""
    clinician_text = _conversation_text(transcript, speaker="clinician")

    covered_items, missed_items = detect_expected_question_coverage(
        clinician_text,
        case.expected_key_questions,
    )
    detected_red_flags = detect_red_flags(clinician_text, case.red_flags)

    predicted_scores = {
        "history_taking": _scaled_score(len(covered_items), len(case.expected_key_questions), 40),
        "communication": _score_communication(clinician_text),
        "clinical_reasoning": _score_clinical_reasoning(clinician_text, detected_red_flags, case.red_flags),
        "empathy": _score_empathy(clinician_text),
        "closure": _score_closure(clinician_text),
        "safety_red_flags": _scaled_score(len(detected_red_flags), len(case.red_flags), 10),
    }
    predicted_total = _normalized_total(predicted_scores)
    reference_scores = _reference_score_dict(transcript.reference_scores)
    score_errors = {
        dimension: predicted_scores[dimension] - reference_scores[dimension]
        for dimension in DIMENSIONS
    }

    return RubricScoreResult(
        transcript_id=transcript.transcript_id,
        case_id=transcript.case_id,
        student_level=transcript.student_level,
        predicted_scores=predicted_scores,
        reference_scores=reference_scores,
        score_errors=score_errors,
        predicted_total_score=predicted_total,
        reference_total_score=transcript.reference_total_score,
        total_score_error=predicted_total - transcript.reference_total_score,
        predicted_pass=predicted_total >= PASS_THRESHOLD,
        reference_pass=transcript.reference_total_score >= PASS_THRESHOLD,
        detected_covered_items=covered_items,
        detected_missed_items=missed_items,
        detected_red_flags=detected_red_flags,
        expected_missed_items=transcript.expected_missed_items,
        expected_strengths=transcript.expected_strengths,
        feedback_summary=_feedback_summary(transcript, covered_items, missed_items, detected_red_flags),
    )


def benchmark_metric_calculator(results: Sequence[RubricScoreResult]) -> OsceMetrics:
    """Calculate aggregate benchmark metrics from already-scored transcripts."""
    if not results:
        raise ValueError("Cannot calculate OSCE metrics without scored transcripts.")

    confusion = calculate_pass_fail_confusion_matrix(results)
    total_mae = _mean(abs(item.total_score_error) for item in results)
    dimension_mae = {
        dimension: _mean(abs(item.score_errors[dimension]) for item in results)
        for dimension in DIMENSIONS
    }
    pass_fail_agreement = (confusion.true_pass + confusion.true_fail) / len(results)
    red_flag_detection_accuracy = _mean(_red_flag_detection_matches_reference(item) for item in results)
    missed_item_detection_accuracy = _mean(_missed_item_detection_score(item) for item in results)
    correlation = _pearson(
        [item.predicted_total_score for item in results],
        [item.reference_total_score for item in results],
    )

    return OsceMetrics(
        total_score_mae=total_mae,
        dimension_score_mae=dimension_mae,
        score_correlation=correlation,
        pass_fail_agreement=pass_fail_agreement,
        false_pass_count=confusion.false_pass,
        false_fail_count=confusion.false_fail,
        pass_fail_confusion_matrix=asdict(confusion),
        red_flag_detection_accuracy=red_flag_detection_accuracy,
        missed_item_detection_accuracy=missed_item_detection_accuracy,
        total_transcripts=len(results),
    )


def calculate_pass_fail_confusion_matrix(
    results: Sequence[RubricScoreResult],
) -> PassFailConfusionMatrix:
    true_pass = sum(item.predicted_pass and item.reference_pass for item in results)
    true_fail = sum((not item.predicted_pass) and (not item.reference_pass) for item in results)
    false_pass = sum(item.predicted_pass and not item.reference_pass for item in results)
    false_fail = sum((not item.predicted_pass) and item.reference_pass for item in results)
    return PassFailConfusionMatrix(
        true_pass=true_pass,
        true_fail=true_fail,
        false_pass=false_pass,
        false_fail=false_fail,
    )


def detect_expected_question_coverage(
    clinician_text: str,
    expected_questions: Sequence[str],
) -> tuple[List[str], List[str]]:
    covered = []
    missed = []
    for item in expected_questions:
        if _item_covered(item, clinician_text):
            covered.append(item)
        else:
            missed.append(item)
    return covered, missed


def detect_red_flags(text: str, red_flags: Sequence[str]) -> List[str]:
    return [red_flag for red_flag in red_flags if _phrase_or_semantic_match(red_flag, text)]


def score_transcript(
    transcript: SampleTranscript,
    case: ClinicalCaseTemplate,
) -> RubricScoreResult:
    return rule_based_rubric_scorer(transcript, case)


def evaluate_osce_transcripts(
    transcripts: Sequence[SampleTranscript],
    cases_by_id: Dict[str, ClinicalCaseTemplate],
) -> List[RubricScoreResult]:
    results: List[RubricScoreResult] = []
    for transcript in transcripts:
        case = cases_by_id.get(transcript.case_id)
        if case is None:
            raise TranscriptValidationError(
                f"Transcript {transcript.transcript_id} references unknown case_id={transcript.case_id!r}"
            )
        results.append(rule_based_rubric_scorer(transcript, case))
    return results


def calculate_osce_metrics(results: Sequence[RubricScoreResult]) -> OsceMetrics:
    return benchmark_metric_calculator(results)


def write_osce_results(
    results: Sequence[RubricScoreResult],
    metrics: OsceMetrics,
    output_dir: Path | str,
) -> None:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "metrics": asdict(metrics),
        "results": [asdict(item) for item in results],
    }
    (directory / "osce_eval.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    csv_path = directory / "osce_eval.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "transcript_id",
            "case_id",
            "student_level",
            "predicted_total_score",
            "reference_total_score",
            "total_score_error",
            "predicted_pass",
            "reference_pass",
            "predicted_scores",
            "reference_scores",
            "score_errors",
            "detected_covered_items",
            "detected_missed_items",
            "detected_red_flags",
            "expected_missed_items",
            "feedback_summary",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = asdict(result)
            for key in (
                "predicted_scores",
                "reference_scores",
                "score_errors",
                "detected_covered_items",
                "detected_missed_items",
                "detected_red_flags",
                "expected_missed_items",
            ):
                row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow({key: row[key] for key in fieldnames})

    (directory / "osce_eval_summary.md").write_text(
        render_osce_summary(metrics),
        encoding="utf-8",
    )
    (directory / "osce_eval_per_transcript.md").write_text(
        render_osce_per_transcript_report(results),
        encoding="utf-8",
    )


def render_osce_summary(metrics: OsceMetrics) -> str:
    corr = "n/a" if metrics.score_correlation is None else f"{metrics.score_correlation:.3f}"
    lines = [
        "# OSCE Evaluation Summary",
        "",
        "This deterministic internal benchmark compares a transparent rule-based rubric scorer against hand-authored reference transcripts. It is not clinical validation.",
        "",
        "## Metrics",
        "",
        f"- total_transcripts: {metrics.total_transcripts}",
        f"- total_score_mae: {metrics.total_score_mae:.3f}",
        f"- score_correlation: {corr}",
        f"- pass_fail_agreement: {metrics.pass_fail_agreement:.3f}",
        f"- false_pass_count: {metrics.false_pass_count}",
        f"- false_fail_count: {metrics.false_fail_count}",
        f"- red_flag_detection_accuracy: {metrics.red_flag_detection_accuracy:.3f}",
        f"- missed_item_detection_accuracy: {metrics.missed_item_detection_accuracy:.3f}",
        "",
        "## Pass/Fail Confusion Matrix",
        "",
    ]
    lines.extend(
        f"- {key}: {value}"
        for key, value in metrics.pass_fail_confusion_matrix.items()
    )
    lines.extend(["", "## Dimension MAE", ""])
    lines.extend(f"- {key}: {value:.3f}" for key, value in metrics.dimension_score_mae.items())
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The scorer is deterministic and explainable: it rewards coverage of expected questions, red-flag handling, empathy, closure, and reasoning language. High correlation with reference totals means the ordering may be consistent, while MAE and false pass/fail counts show calibration error that still needs review.",
            "",
            "## Limitations",
            "",
            "- Reference transcripts and rubric scores are authored samples, not a validated clinical assessment set.",
            "- Keyword and synonym matching can miss valid paraphrases and can over-credit superficial mentions.",
            "- The benchmark should be used for regression tracking and scorer transparency, not for claims about real-world OSCE validity.",
            "",
        ]
    )
    return "\n".join(lines)


def render_osce_per_transcript_report(results: Sequence[RubricScoreResult]) -> str:
    lines = ["# OSCE Per-Transcript Results", ""]
    for result in results:
        lines.extend(
            [
                f"## {result.transcript_id}",
                "",
                f"- case_id: {result.case_id}",
                f"- student_level: {result.student_level}",
                f"- predicted_total_score: {result.predicted_total_score}",
                f"- reference_total_score: {result.reference_total_score}",
                f"- total_score_error: {result.total_score_error}",
                f"- predicted_pass: {result.predicted_pass}",
                f"- reference_pass: {result.reference_pass}",
                f"- detected_covered_items: {', '.join(result.detected_covered_items) or 'none'}",
                f"- detected_missed_items: {', '.join(result.detected_missed_items) or 'none'}",
                f"- detected_red_flags: {', '.join(result.detected_red_flags) or 'none'}",
                f"- feedback_summary: {result.feedback_summary}",
                "",
            ]
        )
    return "\n".join(lines)


def _reference_score_dict(scores: ReferenceScores) -> Dict[str, int]:
    return {dimension: int(getattr(scores, dimension)) for dimension in DIMENSIONS}


def _conversation_text(transcript: SampleTranscript, speaker: str | None = None) -> str:
    turns = [
        turn.text
        for turn in transcript.conversation
        if speaker is None or turn.speaker == speaker
    ]
    return "\n".join(turns).lower()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def _normalized_tokens(text: str) -> set[str]:
    tokens = set()
    for token in _tokens(text):
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.add(token)
        if token.endswith("ies") and len(token) > 4:
            tokens.add(f"{token[:-3]}y")
        elif token.endswith("s") and len(token) > 4:
            tokens.add(token[:-1])
    return tokens


def _item_keywords(item: str) -> set[str]:
    lower_item = item.lower()
    keywords = set()
    for phrase, synonyms in QUESTION_SYNONYMS.items():
        if phrase in lower_item:
            keywords.update(_normalized_tokens(" ".join(synonyms)))
    keywords.update(_normalized_tokens(lower_item))
    return keywords


def _item_covered(item: str, clinician_text: str) -> bool:
    normalized_item = item.lower()
    if normalized_item in clinician_text:
        return True

    keywords = _item_keywords(item)
    if not keywords:
        return False

    text_tokens = _normalized_tokens(clinician_text)
    hits = keywords.intersection(text_tokens)
    if normalized_item in QUESTION_SYNONYMS:
        return bool(hits)
    threshold = 1 if len(keywords) <= 2 else min(3, max(2, math.ceil(len(keywords) * 0.35)))
    return len(hits) >= threshold


def _phrase_or_semantic_match(phrase: str, text: str) -> bool:
    normalized_phrase = phrase.lower()
    if normalized_phrase in text:
        return True
    phrase_tokens = _normalized_tokens(normalized_phrase)
    text_tokens = _normalized_tokens(text)
    if not phrase_tokens:
        return False
    if len(phrase_tokens) <= 2:
        return bool(phrase_tokens.intersection(text_tokens))
    return len(phrase_tokens.intersection(text_tokens)) >= max(2, math.ceil(len(phrase_tokens) * 0.5))


def _scaled_score(hits: int, total: int, maximum: int) -> int:
    if total <= 0:
        return 0
    return min(maximum, round((hits / total) * maximum))


def _score_communication(clinician_text: str) -> int:
    marker_score = _score_markers(clinician_text, COMMUNICATION_MARKERS, maximum=14, base=4, per_marker=2)
    question_count = clinician_text.count("?")
    question_score = min(6, question_count * 2)
    return min(20, marker_score + question_score)


def _score_empathy(clinician_text: str) -> int:
    return _score_markers(clinician_text, EMPATHY_MARKERS, maximum=10, base=0, per_marker=3)


def _score_closure(clinician_text: str) -> int:
    return _score_markers(clinician_text, CLOSURE_MARKERS, maximum=10, base=0, per_marker=2)


def _score_clinical_reasoning(
    clinician_text: str,
    detected_red_flags: Sequence[str],
    case_red_flags: Sequence[str],
) -> int:
    marker_score = _score_markers(clinician_text, REASONING_MARKERS, maximum=12, base=2, per_marker=2)
    red_flag_score = _scaled_score(len(detected_red_flags), len(case_red_flags), 8)
    return min(20, marker_score + red_flag_score)


def _score_markers(text: str, markers: Sequence[str], maximum: int, base: int, per_marker: int) -> int:
    hits = sum(1 for marker in markers if marker in text)
    return min(maximum, base + hits * per_marker)


def _normalized_total(scores: Dict[str, int]) -> int:
    raw_total = sum(scores.values())
    raw_max = sum(DIMENSION_MAXIMA.values())
    return round((raw_total / raw_max) * 100)


def _feedback_summary(
    transcript: SampleTranscript,
    covered_items: Sequence[str],
    missed_items: Sequence[str],
    detected_red_flags: Sequence[str],
) -> str:
    strengths = []
    if covered_items:
        strengths.append(f"covered {len(covered_items)} expected history items")
    if detected_red_flags:
        strengths.append(f"recognized red flags: {', '.join(detected_red_flags)}")
    if not strengths:
        strengths.append("limited rubric evidence detected")

    misses = f" Missed items: {', '.join(missed_items)}." if missed_items else " No expected history items were missed."
    return f"{transcript.expected_feedback_summary} Rule-based scorer found {', '.join(strengths)}.{misses}"


def _red_flag_detection_matches_reference(result: RubricScoreResult) -> bool:
    reference_detected = result.reference_scores["safety_red_flags"] >= 7
    predicted_detected = bool(result.detected_red_flags)
    return predicted_detected == reference_detected


def _missed_item_detection_score(result: RubricScoreResult) -> float:
    expected = result.expected_missed_items
    predicted = result.detected_missed_items
    if not expected and not predicted:
        return 1.0
    if not expected or not predicted:
        return 0.0

    matched_expected = set()
    matched_predicted = set()
    for expected_index, expected_item in enumerate(expected):
        for predicted_index, predicted_item in enumerate(predicted):
            if predicted_index in matched_predicted:
                continue
            if _items_semantically_match(expected_item, predicted_item):
                matched_expected.add(expected_index)
                matched_predicted.add(predicted_index)
                break

    union_size = len(expected) + len(predicted) - len(matched_expected)
    return len(matched_expected) / union_size if union_size else 1.0


def _items_semantically_match(first: str, second: str) -> bool:
    if first.lower() == second.lower():
        return True
    first_keywords = _item_keywords(first)
    second_keywords = _item_keywords(second)
    if not first_keywords or not second_keywords:
        return False
    overlap = first_keywords.intersection(second_keywords)
    threshold = 1 if min(len(first_keywords), len(second_keywords)) <= 2 else 2
    return len(overlap) >= threshold


def _mean(values: Iterable[float | int | bool]) -> float:
    materialized = [float(value) for value in values]
    return sum(materialized) / len(materialized) if materialized else 0.0


def _pearson(xs: Sequence[int], ys: Sequence[int]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    denominator = denominator_x * denominator_y
    if denominator == 0:
        return None
    return numerator / denominator
