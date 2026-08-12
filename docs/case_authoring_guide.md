# SimuPatient Case Authoring Guide

## Scope

SimuPatient cases are structured teaching simulations, not real-patient protocols. Authors should
create one reviewed YAML file per case and keep facts, deterministic workflow rules, and language
generation separate.

- YAML defines case truth, hidden facts, authored tool results, and safety vocabulary.
- Python defines unlocking, stages, Trace, scoring baselines, and blocking combinations.
- The LLM expresses patient language and bounded qualitative feedback; it must not invent facts.

For the competition Demo, use `chest_pain_001` as the safety-critical reference. The existing
`hypertension_followup_001` illustrates a non-acute case that remains compatible without hard-block
safety rules. Do not mass-generate unreviewed cases.

## Recommended workflow

1. Copy the structurally closest reviewed YAML case.
2. Assign a unique, stable `case_id` such as `specialty_topic_001`.
3. Write the learner-visible opening first: demographics, specialty/setting, chief complaint, and
   opening statement.
4. Author all case facts. Avoid contradictions between present illness, histories, tools, and hidden
   information.
5. Add hidden facts only when they serve a teaching objective. Write a direct, testable
   `reveal_condition`.
6. Add expected questions and red flags for instructor review; these never enter learner payloads.
7. Add authored vital signs, examinations, and investigations only when the case needs them.
8. For a safety-critical case, add `safety_supervision` vocabulary and learner-safe reflection text.
9. Start the app with `APP_ROLE=instructor`, open **YAML Case Template Validator**, select the case,
   and run validation.
10. Review the learner-visible preview before conducting a MockProvider walkthrough.
11. Run the full tests and both offline evaluation scripts before merging.

## Minimal authoring skeleton

```yaml
case_id: example_case_001
title: Example reviewed teaching case
specialty: primary_care
difficulty: beginner
chief_complaint: A short learner-visible complaint
demographics:
  age: 45
  gender: female
  occupation: teacher
present_illness:
  onset: gradual
  duration: 3 days
  location: example location
  character: example character
  severity: mild
  radiation: none
  associated_symptoms: []
  aggravating_factors: []
  relieving_factors: []
past_medical_history: []
medication_history: []
allergy_history:
  - no known drug allergies
family_history: []
social_history:
  smoking: never
  alcohol: none
  drug_use: denies
hidden_information:
  - item: a teaching-relevant hidden fact
    reveal_condition: only reveal if asked directly about the relevant topic
    clinical_relevance: why this changes reasoning
red_flags: []
expected_key_questions:
  - onset
scoring_rubric:
  history_taking: 40
  communication: 20
  clinical_reasoning: 20
  empathy: 10
  closure: 10
patient_personality:
  anxiety: low
  cooperativeness: high
  health_literacy: medium
opening_statement: "A first-person patient opening statement."
```

Tool and safety sections are optional. If they are absent, the case remains valid but the validator
warns that the corresponding structured or hard-block behavior is not configured.

## Authoring deterministic tools

Every result must be fully authored. Do not ask the LLM to generate an ECG, biomarker value, vital
sign, or imaging result during the encounter.

```yaml
vital_signs:
  kind: vital_signs
  unlock_condition: history_taking_or_later
  time_cost: 2
  result:
    blood_pressure: "128/76 mmHg"

physical_examination:
  cardiovascular:
    kind: physical_exam
    unlock_condition: history_taking_or_later
    time_cost: 4
    result:
      heart_sounds: "Normal S1 and S2"

investigations:
  ecg:
    kind: ecg
    unlock_condition: examination_or_later
    time_cost: 5
    result:
      rhythm: "Sinus rhythm"
      impression: "No acute abnormality"
```

Supported unlock values are `available`, `history_taking_or_later`, `examination_or_later`, and
`investigation_or_later`. Unknown values fail closed.

## Hidden-information rules

A good hidden-information item has one precise fact, one observable gate, and one teaching reason.

Good:

```yaml
hidden_information:
  - item: takes ibuprofen daily for knee pain
    reveal_condition: only reveal if asked about over-the-counter medicines or pain medication
    clinical_relevance: NSAID use can worsen blood pressure control
```

Avoid:

- putting the hidden fact in `chief_complaint` or `opening_statement`;
- vague gates such as “reveal when appropriate”;
- combining multiple unrelated secrets in one item;
- using trust alone without a topic-specific learner question;
- embedding the correct diagnosis or rubric in patient-visible text.

## Safety-critical cases

Use `safety_supervision` only after clinician/instructor review. At minimum, configure critical
tests, unsafe disposition language, urgent escalation language, safety-net language, reflective
feedback, and reflection questions. The critical test must also exist under `investigations`.

Never put the ground-truth diagnosis in learner feedback. Prefer:

> Current management has not adequately excluded a potentially life-threatening cause. Recheck
> danger signs, necessary investigations, and the appropriate care setting.

Schema validity does not prove clinical correctness. A reviewer must confirm all facts and rules.

## Validation and release checklist

- [ ] `case_id` is unique and stable.
- [ ] All required fields are present.
- [ ] Learner opening contains no hidden fact, rubric, red flag answer, or diagnosis.
- [ ] Hidden reveal conditions are direct and testable.
- [ ] Tool values are internally consistent and authored in YAML.
- [ ] Critical tests named by safety rules exist under `investigations`.
- [ ] Blocking feedback is reflective and does not reveal the answer.
- [ ] Learner-visible preview contains only allowed fields.
- [ ] MockProvider can complete the intended path without network access.
- [ ] Existing cases and disclosure evaluation still pass.
- [ ] Medical content has instructor/clinician approval.
