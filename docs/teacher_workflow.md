# Teacher Workflow

## Start in instructor mode

Set the role before launching Streamlit:

```powershell
$env:APP_ROLE='instructor'
$env:LLM_PROVIDER='mock'
streamlit run streamlit_app.py
```

Instructor mode is a lightweight local Demo role, not an authentication system. Use a non-sensitive
local `learner_id`. Do not deploy it as an internet-facing teacher account without real identity,
authorization, and privacy controls.

## Review learner training records

Open **Instructor Case View → Teacher Dashboard**.

1. Select **All local learners** or a specific `learner_id`.
2. Review the session table for case, stage, score, hints, safety-event count, and retry linkage.
3. Select a session.
4. Review the nine dimension scores.
5. Open **Complete Action Trace** to inspect inputs, tools, rejected actions, hints, safety events,
   and assessment score evidence.
6. If the session is a Focused Retry, review the first/second score, dimension changes, resolved
   safety omissions, hints, time, and the non-causal interpretation.

Scores are formative. They support feedback conversations and case refinement; they do not replace
an OSCE examiner or certify clinical competence.

## Download reports

The Dashboard provides:

- Markdown for human-readable teaching review;
- JSON for structured local analysis or future integrations.

Both exports respect the selected learner filter and include session metadata, dimensions, Trace,
safety events, hints, and retry comparison. Store downloads according to your institution's learner
privacy policy.

## Review the current full case

The lower **Instructor-only Current Case Review** retains the server-side full blueprint, rubric,
Action Trace, unlock history, and scoring evidence for the currently active patient. These fields
must never be shown in a learner screen share.

Learner mode remains the default. Direct calls to Dashboard, validation, and full-case services raise
`PermissionError` unless `APP_ROLE=instructor`.

## Validate a YAML template

Open **YAML Case Template Validator**.

1. Select an existing YAML case.
2. Click **Validate YAML Template**.
3. Confirm metadata and PASS/FAIL status.
4. Review Schema findings for missing or invalid fields.
5. Review hidden-information findings for ambiguous gates or visible leaks.
6. Review safety findings for missing configuration, unknown critical tests, or empty rule parts.
7. Inspect the learner-visible preview.
8. Download the Markdown or JSON validation report.

Warnings do not invalidate a Schema. For example, `hypertension_followup_001` is a compatible
non-acute case and receives a warning that no case-specific hard-block safety rule is configured.
Errors set `valid=false` and must be resolved before release.

## Suggested preparation workflow

Before a teaching session:

1. Select the learning objective and reviewed YAML case.
2. Validate the template and preview the learner opening.
3. Run one MockProvider walkthrough of the intended path.
4. Confirm critical tool results and Safety Supervisor behavior.
5. Decide which hint level the instructor will permit.
6. Provide learners only the learner-mode app.

After training:

1. Filter the Dashboard by learner ID.
2. Review safety-critical omissions before the total score.
3. Use evidence and Trace to discuss one to three priority skills.
4. Start or review a Focused Retry.
5. Compare both attempts without claiming causal improvement.
6. Export a report only when local handling is appropriate.

## Interpreting progress responsibly

Use this phrasing:

> 当前 Demo 中的个体训练表现对比。

Do not claim that a higher second score proves teaching effectiveness. The same case, greater
familiarity, hints, and repeated exposure can all affect the result. Review dimension evidence,
safety omissions, hints, and time together.

## Operational boundaries

- SQLite and local learner IDs are appropriate for the competition Demo, not multi-institution
  deployment.
- Instructor mode contains hidden case facts and learner traces.
- Reports may contain learner inputs and legitimately unlocked sensitive simulation facts.
- YAML validation checks structure and configured rules; it does not clinically approve a case.
- All clinical content needs instructor/clinician review.
- The system is for education and formative feedback, not real diagnosis or treatment.
