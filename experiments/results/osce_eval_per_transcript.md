# OSCE Per-Transcript Results

## abdominal_pain_borderline

- case_id: abdominal_pain_001
- student_level: borderline
- predicted_total_score: 45
- reference_total_score: 64
- total_score_error: -19
- predicted_pass: False
- reference_pass: False
- detected_covered_items: severity, fever, vomiting, bowel symptoms, urinary symptoms
- detected_missed_items: onset and migration, location, menstrual history, pregnancy possibility, analgesic use
- detected_red_flags: appendicitis
- feedback_summary: Reasonable abdominal pain history but missed pregnancy-related safety questions. Rule-based scorer found covered 5 expected history items, recognized red flags: appendicitis. Missed items: onset and migration, location, menstrual history, pregnancy possibility, analgesic use.

## asthma_good

- case_id: asthma_exacerbation_001
- student_level: good
- predicted_total_score: 60
- reference_total_score: 92
- total_score_error: -32
- predicted_pass: False
- reference_pass: True
- detected_covered_items: shortness of breath severity, wheeze, cough and fever, rescue inhaler use, controller medication use, triggers, allergies, ability to speak, chest pain
- detected_missed_items: prior hospitalizations
- detected_red_flags: severe asthma attack
- feedback_summary: Strong asthma exacerbation history with appropriate medication and safety assessment. Rule-based scorer found covered 9 expected history items, recognized red flags: severe asthma attack. Missed items: prior hospitalizations.

## chest_pain_good

- case_id: chest_pain_001
- student_level: good
- predicted_total_score: 85
- reference_total_score: 100
- total_score_error: -15
- predicted_pass: True
- reference_pass: True
- detected_covered_items: onset, location, radiation, severity, associated symptoms, cardiovascular risk factors, medication history, allergy history, smoking history, recreational drug use
- detected_missed_items: none
- detected_red_flags: acute coronary syndrome, pulmonary embolism, aortic dissection
- feedback_summary: Strong chest pain assessment with appropriate urgency and safety framing. Rule-based scorer found covered 10 expected history items, recognized red flags: acute coronary syndrome, pulmonary embolism, aortic dissection. No expected history items were missed.

## depression_poor

- case_id: depression_screening_001
- student_level: poor
- predicted_total_score: 15
- reference_total_score: 23
- total_score_error: -8
- predicted_pass: False
- reference_pass: False
- detected_covered_items: sleep
- detected_missed_items: mood duration, anhedonia, appetite, concentration, guilt or hopelessness, suicidal ideation, manic symptoms, substance use, support system
- detected_red_flags: none
- feedback_summary: Incomplete depression screen with no safety assessment. Rule-based scorer found covered 1 expected history items. Missed items: mood duration, anhedonia, appetite, concentration, guilt or hopelessness, suicidal ideation, manic symptoms, substance use, support system.

## diabetes_borderline

- case_id: diabetes_followup_001
- student_level: borderline
- predicted_total_score: 36
- reference_total_score: 62
- total_score_error: -26
- predicted_pass: False
- reference_pass: False
- detected_covered_items: home glucose readings, medication adherence, medication side effects, diet, exercise
- detected_missed_items: hypoglycemia symptoms, foot symptoms, eye screening, kidney screening, cardiovascular risk
- detected_red_flags: none
- feedback_summary: Useful adherence history but incomplete chronic complication screening. Rule-based scorer found covered 5 expected history items. Missed items: hypoglycemia symptoms, foot symptoms, eye screening, kidney screening, cardiovascular risk.

## headache_poor

- case_id: headache_001
- student_level: poor
- predicted_total_score: 13
- reference_total_score: 16
- total_score_error: -3
- predicted_pass: False
- reference_pass: False
- detected_covered_items: none
- detected_missed_items: onset speed, worst headache of life, neurologic symptoms, fever, neck stiffness, vision changes, trauma, anticoagulant use, pregnancy status, previous headache pattern
- detected_red_flags: thunderclap headache
- feedback_summary: Unsafe headache assessment with no red flag screening. Rule-based scorer found recognized red flags: thunderclap headache. Missed items: onset speed, worst headache of life, neurologic symptoms, fever, neck stiffness, vision changes, trauma, anticoagulant use, pregnancy status, previous headache pattern.

## medication_nonadherence_borderline

- case_id: medication_nonadherence_001
- student_level: borderline
- predicted_total_score: 56
- reference_total_score: 74
- total_score_error: -18
- predicted_pass: False
- reference_pass: True
- detected_covered_items: which medications are missed, frequency of missed doses, side effects, cost barriers, beliefs about medications, daily routine, pharmacy access, support system
- detected_missed_items: health literacy, shared plan preferences
- detected_red_flags: medication side effects
- feedback_summary: Good adherence-barrier assessment with room for more empathy and health literacy exploration. Rule-based scorer found covered 8 expected history items, recognized red flags: medication side effects. Missed items: health literacy, shared plan preferences.

## pregnancy_abdominal_pain_good

- case_id: pregnancy_abdominal_pain_001
- student_level: good
- predicted_total_score: 75
- reference_total_score: 100
- total_score_error: -25
- predicted_pass: True
- reference_pass: True
- detected_covered_items: vaginal bleeding, dizziness or syncope, shoulder tip pain, prior pregnancies, prior ectopic pregnancy, contraception or fertility treatment, urinary symptoms, blood type history
- detected_missed_items: gestational age, pain location
- detected_red_flags: ectopic pregnancy, hemodynamic instability
- feedback_summary: Excellent early pregnancy pain assessment with urgent safety framing. Rule-based scorer found covered 8 expected history items, recognized red flags: ectopic pregnancy, hemodynamic instability. Missed items: gestational age, pain location.

## smoking_good

- case_id: smoking_cessation_001
- student_level: good
- predicted_total_score: 63
- reference_total_score: 91
- total_score_error: -28
- predicted_pass: False
- reference_pass: True
- detected_covered_items: cigarettes per day, pack-years, prior quit attempts, triggers, barriers, support system, cancer or COPD symptoms
- detected_missed_items: readiness to quit, withdrawal symptoms, pharmacotherapy interest
- detected_red_flags: lung cancer symptoms, chronic obstructive pulmonary disease
- feedback_summary: Strong smoking cessation counseling using patient-centered barrier assessment. Rule-based scorer found covered 7 expected history items, recognized red flags: lung cancer symptoms, chronic obstructive pulmonary disease. Missed items: readiness to quit, withdrawal symptoms, pharmacotherapy interest.

## uti_borderline

- case_id: urinary_tract_infection_001
- student_level: borderline
- predicted_total_score: 47
- reference_total_score: 64
- total_score_error: -17
- predicted_pass: False
- reference_pass: False
- detected_covered_items: dysuria, frequency, urgency, fever, flank pain, pregnancy possibility, allergies, prior infections
- detected_missed_items: hematuria, sexual history
- detected_red_flags: none
- feedback_summary: Basic UTI assessment but missed STI risk and prior infection context. Rule-based scorer found covered 8 expected history items. Missed items: hematuria, sexual history.
