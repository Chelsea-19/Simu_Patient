# YAML Case Schema Reference

## Validation model

Every file in `case_templates/` is parsed as YAML and validated by
`app.schemas.case_template_file.ClinicalCaseTemplate`. Pydantic uses `extra="forbid"`, so unknown
fields fail validation instead of being silently ignored.

## Required top-level fields

| Field | Type | Purpose |
|---|---|---|
| `case_id` | string | Stable unique identifier |
| `title` | string | Instructor-facing title |
| `specialty` | string | Encounter setting/category |
| `difficulty` | string | Author-assigned difficulty |
| `chief_complaint` | string | Learner-visible complaint |
| `demographics` | object | Age, gender, occupation |
| `present_illness` | object | Structured history facts |
| `past_medical_history` | string list | Authored history |
| `medication_history` | string list | Authored medications |
| `allergy_history` | string list | Authored allergies |
| `family_history` | string list | Authored family history |
| `social_history` | object | Authored social history |
| `hidden_information` | object list | Gated teaching facts |
| `red_flags` | string list | Instructor-only risk targets |
| `expected_key_questions` | string list | Instructor/scoring reference |
| `scoring_rubric` | object | Five legacy rubric weights |
| `patient_personality` | object | Anxiety, cooperation, literacy |
| `opening_statement` | string | Learner-visible first-person opening |

## Nested required objects

### `demographics`

```yaml
demographics:
  age: 58          # integer
  gender: male     # string
  occupation: taxi driver
```

### `hidden_information[]`

```yaml
- item: recent cocaine use
  reveal_condition: only reveal if asked directly about recreational drug or stimulant use
  clinical_relevance: increases concern for a coronary mechanism
```

All three values are required. The deterministic disclosure controller decides whether the learner's
question meets the authored gate.

### `scoring_rubric`

```yaml
scoring_rubric:
  history_taking: 40
  communication: 20
  clinical_reasoning: 20
  empathy: 10
  closure: 10
```

Each value is an integer from 0 to 100. These are formative configuration values, not validated exam
weights.

### `patient_personality`

```yaml
patient_personality:
  anxiety: high
  cooperativeness: medium
  health_literacy: low
```

## Optional structured evidence

`vital_signs`, each `physical_examination` entry, and each `investigations` entry use
`ConfiguredClinicalEvidence`:

| Field | Type | Default | Notes |
|---|---|---|---|
| `result` | object | required | Complete authored result |
| `unlock_condition` | string | `available` | Deterministic stage gate |
| `time_cost` | integer ≥ 0 | `1` | Simulated minutes |
| `kind` | string | `other` | Routes labs/exams/ECG |

Example:

```yaml
investigations:
  troponin:
    kind: lab
    unlock_condition: examination_or_later
    time_cost: 10
    result:
      value: "78 ng/L"
      reference_range: "less than 14 ng/L"
      interpretation: "Elevated"
```

## Optional `safety_supervision`

| Field | Type | Purpose |
|---|---|---|
| `risk_level` | string | Case risk label; default `high` |
| `history_topic_keywords` | map of string lists | Deterministic topic evidence |
| `life_threatening_diagnosis_keywords` | string list | Differential-risk evidence |
| `critical_tests` | string list | Tests that must be configured |
| `unsafe_disposition_keywords` | string list | Low-acuity plan detection |
| `escalation_keywords` | string list | Urgent care/referral evidence |
| `safety_net_keywords` | string list | Deterioration advice evidence |
| `block_feedback` | string | Learner-safe reflective feedback |
| `reflection_questions` | string list | Remediation prompts |

The chest-pain implementation blocks only a configured high-risk home disposition combined with a
missing critical ECG or missing urgent escalation. Single history omissions remain formative flags.

## Learner-visible projection

The validator preview and learner API contain only:

- `patient_id` (zero in a template preview);
- `case_id`;
- age;
- gender;
- encounter setting;
- chief complaint;
- opening statement;
- legitimately unlocked evidence.

Forbidden learner fields include hidden information, red flags, expected questions, scoring rubric,
ground-truth diagnosis, and unreleased investigation results. Removing a field from the UI is not
enough; the learner projection is a strict server-side Schema.

## Validator outcomes

- `error`: template cannot be safely released; `valid=false`.
- `warning`: Schema remains valid but an educational capability or authoring quality check needs
  review, such as missing case-specific safety rules.
- `info`: non-blocking explanatory result.

The validator checks raw required fields before Schema parsing, so authors receive explicit missing
field names. It then checks hidden-fact leakage, reveal-condition clarity, critical-test references,
and required safety-rule components.
