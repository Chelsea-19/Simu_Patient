import json

import streamlit as st

from app.core.config import get_settings
from app.streamlit_services import (
    consultation_chat_logic,
    compare_learning_progress_logic,
    create_patient_from_case_logic,
    create_patient_logic,
    ensure_db_ready,
    evaluate_consultation_logic,
    export_case_validation_logic,
    export_learner_case_logic,
    export_teacher_dashboard_logic,
    finish_encounter_logic,
    get_action_trace_logic,
    get_available_tools_logic,
    get_consultation_history_logic,
    get_encounter_state_logic,
    get_instructor_case_view_logic,
    get_learning_diagnosis_logic,
    get_learner_case_logic,
    get_teacher_dashboard_logic,
    list_case_templates_for_validation_logic,
    list_case_templates_logic,
    order_ecg_logic,
    order_lab_test_logic,
    perform_physical_exam_logic,
    request_hint_logic,
    request_vital_signs_logic,
    start_encounter_logic,
    start_focused_retry_logic,
    submit_differential_diagnosis_logic,
    submit_management_plan_logic,
    validate_case_template_logic,
)


st.set_page_config(
    page_title="SimuPatient - AI Standardized Patient",
    layout="wide",
    initial_sidebar_state="collapsed",
)

settings = get_settings()

if settings.selected_provider == "gemini" and not settings.resolved_gemini_api_key:
    st.error("Configuration error: GEMINI_API_KEY is not set in Streamlit secrets or the environment.")
    st.stop()

if settings.selected_provider == "gemini" and not settings.GEMINI_MODEL:
    st.error("Configuration error: GEMINI_MODEL is not configured.")
    st.stop()

try:
    ensure_db_ready()
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    st.stop()

if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "learner_case" not in st.session_state:
    st.session_state.learner_case = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "assessment" not in st.session_state:
    st.session_state.assessment = None
if "encounter_session_id" not in st.session_state:
    st.session_state.encounter_session_id = None
if "encounter_state" not in st.session_state:
    st.session_state.encounter_state = None
if "last_tool_result" not in st.session_state:
    st.session_state.last_tool_result = None
if "progress_report" not in st.session_state:
    st.session_state.progress_report = None
if "confirm_session_reset" not in st.session_state:
    st.session_state.confirm_session_reset = False
if settings.is_instructor and "case_validation_result" not in st.session_state:
    st.session_state.case_validation_result = None


def reset_current_session() -> None:
    """Clear only the active learner session after explicit confirmation."""
    st.session_state.patient_id = None
    st.session_state.learner_case = None
    st.session_state.chat_history = []
    st.session_state.assessment = None
    st.session_state.encounter_session_id = None
    st.session_state.encounter_state = None
    st.session_state.last_tool_result = None
    st.session_state.progress_report = None
    st.session_state.confirm_session_reset = False
    if settings.is_instructor:
        st.session_state.case_validation_result = None


def provider_model_label() -> str:
    if settings.selected_provider == "gemini":
        return settings.GEMINI_MODEL
    if settings.selected_provider == "ollama":
        return settings.OLLAMA_MODEL
    return "mock:deterministic"


st.sidebar.title("Session")
st.sidebar.success("Ready for training")

active_state = st.session_state.encounter_state
if active_state:
    st.sidebar.metric("Current stage", active_state["current_stage"].replace("_", " ").title())
    st.sidebar.caption(f"Elapsed time: {active_state['elapsed_time']} min")
elif st.session_state.patient_id:
    st.sidebar.info("Patient ready. Continue in Clinical Encounter.")
else:
    st.sidebar.caption("Choose a case to begin a new training session.")

with st.sidebar.expander("Resume a saved encounter"):
    resume_session_id = st.text_input("Session ID", key="resume_session_id")
    st.caption("Paste the encounter session ID shown during training.")
    if st.button(
        "Resume encounter",
        disabled=not resume_session_id.strip(),
        use_container_width=True,
    ):
        try:
            restored = get_encounter_state_logic(resume_session_id.strip())
            learner_case = get_learner_case_logic(restored["patient_id"])
            st.session_state.patient_id = restored["patient_id"]
            st.session_state.learner_case = learner_case.model_dump(mode="json")
            st.session_state.chat_history = get_consultation_history_logic(restored["patient_id"])
            try:
                learning = get_learning_diagnosis_logic(restored["session_id"])
                st.session_state.assessment = {
                    "score": learning["profile"]["overall_score"],
                    "latency_ms": 0,
                    "model_used": "persisted learning profile",
                    "feedback": "Restored session-level formative learning diagnosis.",
                    "learning_profile": learning["profile"],
                    "remediation_plan": learning["remediation_plan"],
                }
            except KeyError:
                st.session_state.assessment = None
            st.session_state.encounter_session_id = restored["session_id"]
            st.session_state.encounter_state = restored
            st.session_state.last_tool_result = None
            if restored.get("retry_of_session_id") and st.session_state.assessment:
                st.session_state.progress_report = compare_learning_progress_logic(
                    restored["retry_of_session_id"],
                    restored["session_id"],
                )
            else:
                st.session_state.progress_report = None
            st.rerun()
        except Exception as e:
            st.error(f"Could not resume encounter: {e}")

with st.sidebar.expander("System and data details"):
    st.markdown(f"**Provider:** `{settings.selected_provider}`")
    st.markdown(f"**Model:** `{provider_model_label()}`")
    st.markdown(f"**Role:** `{settings.APP_ROLE}`")
    st.caption(
        "Session data is saved to local SQLite. On Streamlit Community Cloud, "
        "it resets when the app sleeps."
    )

st.sidebar.divider()
if st.sidebar.button("Reset session data", use_container_width=True):
    st.session_state.confirm_session_reset = True

if st.session_state.confirm_session_reset:
    st.sidebar.warning("This clears the active patient, encounter, chat, and feedback from this view.")
    reset_col, cancel_col = st.sidebar.columns(2)
    if reset_col.button("Confirm reset", type="primary", use_container_width=True):
        reset_current_session()
        st.rerun()
    if cancel_col.button("Cancel", use_container_width=True):
        st.session_state.confirm_session_reset = False
        st.rerun()

st.title("SimuPatient")
st.caption("CLINICAL REASONING | STRUCTURED EVIDENCE | FORMATIVE FEEDBACK")
st.write(
    "Adaptive clinical reasoning and OSCE practice with structured evidence, safety supervision, "
    "and personalized formative feedback."
)

with st.container(border=True):
    st.caption("TRAINING WORKFLOW")
    setup_col, encounter_col, feedback_col = st.columns(3)
    setup_col.markdown("**1  Choose training**")
    setup_col.caption("Ready" if not st.session_state.patient_id else "Case selected")
    encounter_col.markdown("**2  Clinical encounter**")
    encounter_col.caption(
        active_state["current_stage"].replace("_", " ").title()
        if active_state
        else ("Ready to begin" if st.session_state.patient_id else "Waiting for a case")
    )
    feedback_col.markdown("**3  Formative feedback**")
    feedback_col.caption("Available" if st.session_state.assessment else "Pending completion")

tab_names = ["Setup", "Encounter", "Feedback"]
if settings.is_instructor:
    tab_names.append("Instructor")
tabs = st.tabs(tab_names)
tab1, tab2, tab3 = tabs[:3]
instructor_tab = tabs[3] if settings.is_instructor else None


def render_learner_case(case: dict) -> None:
    """Render only fields allowed by LearnerVisibleCase."""
    st.write(f"**Age:** {case.get('age')} | **Gender:** {case.get('gender')}")
    st.write(f"**Encounter setting:** {case.get('encounter_setting')}")
    st.write(f"**Chief complaint:** {case.get('chief_complaint')}")
    st.write(f"**Opening statement:** {case.get('opening_statement')}")


def render_key_value_result(result: dict) -> None:
    """Render structured clinical evidence as readable rows, never as raw learner JSON."""
    rows = []
    for key, value in result.items():
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                rows.append(
                    {
                        "Finding": (
                            f"{key.replace('_', ' ').title()} / "
                            f"{child_key.replace('_', ' ').title()}"
                        ),
                        "Result": str(child_value),
                    }
                )
        elif isinstance(value, list):
            rows.append(
                {"Finding": key.replace("_", " ").title(), "Result": ", ".join(map(str, value))}
            )
        else:
            rows.append({"Finding": key.replace("_", " ").title(), "Result": str(value)})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)


def render_feedback_items(label: str, items: list[str], empty_text: str) -> None:
    st.markdown(f"**{label}**")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty_text)


def refresh_encounter_state() -> dict | None:
    session_id = st.session_state.encounter_session_id
    if not session_id:
        return None
    state = get_encounter_state_logic(session_id)
    st.session_state.encounter_state = state
    return state


def handle_tool_result(result: dict) -> None:
    st.session_state.last_tool_result = result
    refresh_encounter_state()
    if result["status"] == "success":
        st.success(result["learner_message"])
    elif result["status"] == "duplicate":
        st.info(result["learner_message"])
    else:
        st.warning(result["learner_message"])

with tab1:
    st.header("Choose a Training Case")
    st.caption("Start with a structured case for the complete evidence, safety, and feedback workflow.")
    if st.session_state.patient_id:
        st.success("Patient ready. Open Encounter to begin or continue the consultation.")
        with st.expander("Current learner-visible case summary"):
            render_learner_case(st.session_state.learner_case)
            if st.session_state.encounter_session_id:
                st.caption(f"Encounter session: {st.session_state.encounter_session_id}")

    patient_mode = st.radio(
        "Training mode",
        ["Case template", "Random patient"],
        horizontal=True,
    )

    if patient_mode == "Random patient":
        st.info("Random patients support conversational practice only. Use a case template for clinical tools and trace-grounded feedback.")
        with st.container(border=True):
            st.subheader("Describe the patient")
            seed_text = st.text_area(
                "Clinical scenario",
                placeholder="Example: A 45-year-old man with sudden chest pain for two hours.",
                help="Enter a short, synthetic scenario. Do not include real patient information.",
            )

        if st.button("Generate random patient", type="primary", use_container_width=True):
            if not seed_text:
                st.error("Enter a clinical scenario before generating the patient.")
            else:
                with st.spinner(f"Generating clinical profile using {settings.selected_provider}..."):
                    try:
                        data = create_patient_logic(
                            seed_text=seed_text,
                            template_id=None,
                        )
                        st.session_state.patient_id = data["id"]
                        st.session_state.learner_case = data["case"]
                        st.session_state.chat_history = [
                            {"role": "assistant", "content": data["opening_statement"]}
                        ]
                        st.session_state.assessment = None
                        st.session_state.encounter_session_id = None
                        st.session_state.encounter_state = None
                        st.session_state.last_tool_result = None
                        st.session_state.progress_report = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Patient generation failed: {e}")
    else:
        try:
            cases = list_case_templates_logic()
        except Exception as e:
            cases = []
            st.error(f"Could not load case templates: {e}")

        case_options = {f"{case.title} ({case.case_id})": case.case_id for case in cases}
        selected_label = None
        selected_case = None
        learner_id = "demo_learner"
        training_goal = "Focused history, evidence gathering, clinical reasoning, and safe management"
        with st.container(border=True):
            st.subheader("Case and learning objective")
            if case_options:
                selected_label = st.selectbox("Case template", list(case_options.keys()))
                selected_case = next(
                    case for case in cases if case.case_id == case_options[selected_label]
                )
                case_col, learner_col = st.columns(2)
                with case_col:
                    st.markdown("**Learner-visible case preview**")
                    st.write(selected_case.chief_complaint)
                    st.caption(
                        f"{selected_case.specialty.replace('_', ' ').title()} | "
                        f"{selected_case.demographics.age}-year-old "
                        f"{selected_case.demographics.gender} | {selected_case.difficulty}"
                    )
                with learner_col:
                    learner_id = st.text_input(
                        "Learner ID",
                        value="demo_learner",
                        help="Used to group local formative progress records.",
                    )
                    training_goal = st.text_area(
                        "Training goal",
                        value=training_goal,
                        height=100,
                    )
            else:
                st.info("No case templates are available.")

        if st.button(
            "Start structured encounter",
            type="primary",
            disabled=selected_case is None,
            use_container_width=True,
        ):
            with st.spinner("Initializing standardized case..."):
                try:
                    data = create_patient_from_case_logic(case_options[selected_label])
                    st.session_state.patient_id = data["id"]
                    st.session_state.learner_case = data["case"]
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": data["opening_statement"]}
                    ]
                    st.session_state.assessment = None
                    encounter = start_encounter_logic(
                        patient_id=data["id"],
                        learner_id=learner_id.strip() or "demo_learner",
                        case_id=selected_case.case_id,
                        training_goal=training_goal.strip() or "Clinical reasoning practice",
                        difficulty=selected_case.difficulty,
                    )
                    st.session_state.encounter_session_id = encounter["session_id"]
                    st.session_state.encounter_state = encounter
                    st.session_state.last_tool_result = None
                    st.session_state.progress_report = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Case initialization failed: {e}")

with tab2:
    if not st.session_state.patient_id:
        st.header("Clinical Encounter")
        st.info("Choose a training case in Setup to unlock the encounter workspace.")
    else:
        state = refresh_encounter_state()
        st.header("Clinical Encounter")
        st.caption("Interview the patient, gather evidence, document your reasoning, and make a safe plan.")

        if state:
            with st.container(border=True):
                stage_col, time_col = st.columns(2)
                stage_col.metric(
                    "Current stage",
                    state["current_stage"].replace("_", " ").title(),
                )
                time_col.metric("Elapsed time", f"{state['elapsed_time']} min")
                st.caption(f"Session ID: `{state['session_id']}`")
            if state.get("assessment_status") == "blocked_by_safety":
                st.error(
                    "Safety review blocked completion. Reassess the unresolved risk, essential "
                    "investigations, disposition, and escalation plan before trying again."
                )
            if state.get("focused_retry"):
                st.info(
                    "Focused Retry: practice "
                    + ", ".join(skill.replace("_", " ") for skill in state["focus_skills"])
                )
                st.caption(
                    f"Focused history turns: {len(state['questions_asked'])}/"
                    f"{state['history_turn_limit']}"
                )
        else:
            st.info("Random-patient mode supports chat only. Use a YAML case for structured clinical tools.")

        with st.expander("Learner-visible case summary"):
            render_learner_case(st.session_state.learner_case)
            evidence = state["evidence_unlocked"] if state else []
            if evidence:
                st.write("**Unlocked evidence:**")
                for item in evidence:
                    st.markdown(f"**{item.get('label')}**")
                    st.write(item.get("value"))
            else:
                st.caption("No evidence has been unlocked yet.")

            safe_export = export_learner_case_logic(st.session_state.patient_id)
            st.download_button(
                "Download learner case summary",
                data=safe_export,
                file_name=f"learner_case_{st.session_state.patient_id}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.subheader("Patient interview")
        chat_container = st.container(height=400)
        for msg in st.session_state.chat_history:
            with chat_container.chat_message(msg["role"]):
                st.write(msg["content"])

        history_limit_reached = bool(
            state
            and state.get("focused_retry")
            and state.get("history_turn_limit")
            and len(state["questions_asked"]) >= state["history_turn_limit"]
        )
        if history_limit_reached:
            st.info("Focused history limit reached. Continue with examination and investigations.")
        if prompt := st.chat_input(
            "Ask one focused question at a time",
            disabled=history_limit_reached,
        ):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.write(prompt)

            with st.spinner("Patient is thinking..."):
                try:
                    reply = consultation_chat_logic(
                        patient_id=st.session_state.patient_id,
                        user_input=prompt,
                        history=st.session_state.chat_history[:-1],
                        encounter_session_id=st.session_state.encounter_session_id,
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    if st.session_state.encounter_session_id:
                        state = refresh_encounter_state()
                    with chat_container.chat_message("assistant"):
                        st.write(reply)
                except Exception as e:
                    st.error(f"Chat failed: {e}")

        if state:
            st.divider()
            st.subheader("Clinical actions")
            st.caption("Available actions update as the encounter advances. Disabled controls are not yet available.")
            tools = get_available_tools_logic(state["session_id"])
            observe_col, investigate_col = st.columns(2)

            with observe_col:
                with st.container(border=True):
                    st.markdown("**Observe and examine**")
                    if st.button(
                        "Request vital signs",
                        disabled=not tools["vital_signs"],
                        use_container_width=True,
                    ):
                        handle_tool_result(request_vital_signs_logic(state["session_id"]))

                    exam_options = tools["physical_examinations"]
                    selected_exam = st.selectbox(
                        "Physical examination",
                        exam_options,
                        disabled=not exam_options,
                    )
                    if st.button(
                        "Perform selected examination",
                        disabled=not exam_options,
                        use_container_width=True,
                    ):
                        handle_tool_result(
                            perform_physical_exam_logic(state["session_id"], selected_exam)
                        )

            with investigate_col:
                with st.container(border=True):
                    st.markdown("**Order investigations**")
                    if st.button(
                        "Order ECG",
                        disabled=not tools["ecg"],
                        use_container_width=True,
                    ):
                        handle_tool_result(order_ecg_logic(state["session_id"]))

                    lab_options = tools["lab_tests"]
                    selected_lab = st.selectbox(
                        "Laboratory test",
                        lab_options,
                        disabled=not lab_options,
                    )
                    if st.button(
                        "Order selected laboratory test",
                        disabled=not lab_options,
                        use_container_width=True,
                    ):
                        handle_tool_result(order_lab_test_logic(state["session_id"], selected_lab))

            if st.session_state.last_tool_result:
                last_result = st.session_state.last_tool_result
                with st.expander("Latest clinical tool result", expanded=True):
                    st.write(f"**Status:** {last_result['status']}")
                    st.write(f"**Time cost:** {last_result['time_cost']} min")
                    safety_review = last_result.get("result", {}).get("safety_review")
                    if safety_review:
                        if safety_review["decision"] == "block_completion":
                            st.error(safety_review["learner_feedback"])
                        else:
                            st.info(safety_review["learner_feedback"])
                        render_feedback_items(
                            "Safety review actions",
                            safety_review["missing_critical_actions"],
                            "No safety-critical action gap was identified.",
                        )
                    elif last_result["result"]:
                        render_key_value_result(last_result["result"])
                    if safety_review and safety_review["recommended_reflection_questions"]:
                        st.write("**Reflection before retrying**")
                        for question in safety_review["recommended_reflection_questions"]:
                            st.markdown(f"- {question}")

            st.subheader("Clinical reasoning and plan")
            reasoning_col, management_col = st.columns(2)
            with reasoning_col:
                with st.container(border=True):
                    st.markdown("**Differential diagnosis**")
                    differential_text = st.text_area(
                        "Diagnoses",
                        key="differential_input",
                        placeholder="Enter one diagnosis per line, in priority order.",
                        help="You may also separate diagnoses with commas.",
                    )
                    if st.button("Submit differential", use_container_width=True):
                        diagnoses = [
                            value.strip()
                            for line in differential_text.splitlines()
                            for value in line.split(",")
                            if value.strip()
                        ]
                        handle_tool_result(
                            submit_differential_diagnosis_logic(state["session_id"], diagnoses)
                        )

            with management_col:
                with st.container(border=True):
                    st.markdown("**Management plan**")
                    disposition = st.text_input(
                        "Disposition",
                        key="management_disposition",
                        placeholder="Example: monitored admission",
                    )
                    initial_management = st.text_area(
                        "Initial management",
                        key="management_initial",
                        placeholder="Immediate treatment and escalation steps",
                    )
                    safety_net = st.text_area(
                        "Safety-net advice",
                        key="management_safety_net",
                        placeholder="Red flags, follow-up, and when to seek urgent care",
                    )
                    if st.button("Submit management plan", use_container_width=True):
                        handle_tool_result(
                            submit_management_plan_logic(
                                state["session_id"],
                                {
                                    "disposition": disposition,
                                    "initial_management": initial_management,
                                    "safety_net": safety_net,
                                },
                            )
                        )

            hint_col, finish_col = st.columns(2)
            with hint_col:
                with st.container(border=True):
                    st.markdown("**Need support?**")
                    hint_level = st.select_slider("Hint level", options=[1, 2, 3], value=1)
                    if st.button("Request hint", use_container_width=True):
                        handle_tool_result(request_hint_logic(state["session_id"], hint_level))

            with finish_col:
                with st.container(border=True):
                    st.markdown("**Ready for feedback?**")
                    st.caption("Finish after submitting both your differential and management plan.")
                if st.button(
                    "Finish encounter and evaluate",
                    type="primary",
                    use_container_width=True,
                ):
                    finished = finish_encounter_logic(state["session_id"])
                    handle_tool_result(finished)
                    if finished["status"] == "success":
                        with st.spinner("Analyzing consultation transcript..."):
                            try:
                                result = evaluate_consultation_logic(
                                    patient_id=st.session_state.patient_id,
                                    history=st.session_state.chat_history,
                                    encounter_session_id=state["session_id"],
                                )
                                st.session_state.assessment = result.model_dump()
                                completed_state = refresh_encounter_state()
                                if completed_state and completed_state.get("retry_of_session_id"):
                                    st.session_state.progress_report = compare_learning_progress_logic(
                                        completed_state["retry_of_session_id"],
                                        completed_state["session_id"],
                                    )
                                st.success("Evaluation complete. Open Formative Feedback.")
                            except Exception as e:
                                st.error(f"Evaluation failed: {e}")

            trace = get_action_trace_logic(state["session_id"])
            with st.expander("Action trace", expanded=False):
                trace_rows = [
                    {
                        "timestamp": entry["timestamp"],
                        "stage": entry["stage"],
                        "tool": entry["tool_name"],
                        "input": entry["natural_language_input"],
                        "status": entry["result_summary"].get("status"),
                        "evidence": ", ".join(
                            item["label"] for item in entry["evidence_unlocked"]
                        ),
                        "time_cost": entry["time_cost"],
                        "hint_level": entry["hint_level"],
                        "safety_event": "; ".join(entry["safety_event"]),
                    }
                    for entry in trace
                ]
                st.dataframe(trace_rows, use_container_width=True, hide_index=True)

        elif st.button(
            "Finish consultation and evaluate",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Analyzing consultation transcript..."):
                try:
                    result = evaluate_consultation_logic(
                        patient_id=st.session_state.patient_id,
                        history=st.session_state.chat_history,
                    )
                    st.session_state.assessment = result.model_dump()
                    st.success("Evaluation complete. Open Formative Feedback.")
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

with tab3:
    if not st.session_state.assessment:
        st.header("Formative Feedback")
        st.info("Finish the clinical encounter to generate a trace-grounded learning report.")
    else:
        result = st.session_state.assessment
        learning_profile = result.get("learning_profile")
        remediation_plan = result.get("remediation_plan")
        st.header("Formative Feedback")
        st.caption("Use this report to identify the next specific skill to practice. It is not a clinical credential.")

        score_col, feedback_col = st.columns([1, 2])
        with score_col:
            with st.container(border=True):
                st.metric("Overall formative score", f"{result.get('score', 0)}/100")
        with feedback_col:
            st.info(result.get("feedback", "No feedback provided."))

        with st.expander("Assessment details"):
            detail_col1, detail_col2 = st.columns(2)
            detail_col1.write(f"**Model:** {result.get('model_used', 'N/A')}")
            detail_col2.write(f"**Latency:** {result.get('latency_ms', 0):.0f} ms")

        st.subheader("Performance by dimension")
        dimension_metrics = [
            ("History taking", result.get("history_taking_score", 0)),
            ("Communication", result.get("communication_score", 0)),
            ("Clinical reasoning", result.get("clinical_reasoning_score", 0)),
            ("Empathy", result.get("empathy_score", 0)),
            ("Closure", result.get("closure_score", 0)),
        ]
        first_metric_row = st.columns(3)
        second_metric_row = st.columns(2)
        for metric_col, (label, score) in zip(first_metric_row, dimension_metrics[:3]):
            metric_col.metric(label, f"{score}/100")
        for metric_col, (label, score) in zip(second_metric_row, dimension_metrics[3:]):
            metric_col.metric(label, f"{score}/100")

        if learning_profile:
            st.subheader("Trace-grounded learning profile")
            dimension_rows = [
                {
                    "dimension": name.replace("_", " ").title(),
                    "score": detail["score"],
                    "deterministic_base": detail["deterministic_score"],
                    "qualitative_adjustment": detail["qualitative_adjustment"],
                    "omissions": "; ".join(detail["omissions"]),
                    "risks": "; ".join(detail["risks"]),
                }
                for name, detail in learning_profile["dimensions"].items()
            ]
            st.dataframe(dimension_rows, use_container_width=True, hide_index=True)

            with st.expander("Scoring evidence and targeted practice", expanded=False):
                for name, detail in learning_profile["dimensions"].items():
                    st.markdown(f"**{name.replace('_', ' ').title()} - {detail['score']}/100**")
                    render_feedback_items(
                        "Evidence", detail["scoring_evidence"], "No scoring evidence recorded."
                    )
                    render_feedback_items(
                        "Strengths", detail["strengths"], "No confirmed strength yet."
                    )
                    render_feedback_items(
                        "Omissions", detail["omissions"], "No deterministic omission."
                    )
                    render_feedback_items(
                        "Risks", detail["risks"], "No dimension-specific risk."
                    )
                    render_feedback_items(
                        "Practice", detail["recommended_practice"], "No practice task generated."
                    )

        if remediation_plan:
            st.subheader("Personalized remediation plan")
            with st.container(border=True):
                st.write(f"**Learning objective:** {remediation_plan['learning_objective']}")
                st.write(
                    "**Priority skills:** "
                    + ", ".join(
                        skill.replace("_", " ") for skill in remediation_plan["priority_skills"]
                    )
                )
                render_feedback_items(
                    "Actions to practice",
                    remediation_plan["specific_actions_to_practice"],
                    "No focused action generated.",
                )
                st.write(f"**Hint policy:** {remediation_plan['hint_policy']}")
                render_feedback_items(
                    "Success criteria",
                    remediation_plan["success_criteria"],
                    "No criteria generated.",
                )

            current_state = st.session_state.encounter_state
            can_start_retry = bool(
                current_state
                and current_state["current_stage"] == "COMPLETED"
                and not current_state.get("retry_of_session_id")
            )
            if st.button(
                "Start focused retry",
                type="primary",
                disabled=not can_start_retry,
                use_container_width=True,
            ):
                try:
                    retry = start_focused_retry_logic(current_state["session_id"])
                    patient = retry["patient"]
                    encounter = retry["encounter"]
                    st.session_state.patient_id = patient["id"]
                    st.session_state.learner_case = patient["case"]
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": patient["opening_statement"]}
                    ]
                    st.session_state.assessment = None
                    st.session_state.encounter_session_id = encounter["session_id"]
                    st.session_state.encounter_state = encounter
                    st.session_state.last_tool_result = None
                    st.session_state.progress_report = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not start focused retry: {e}")

        if st.session_state.progress_report:
            progress = st.session_state.progress_report
            st.subheader("Focused retry progress")
            score_col1, score_col2 = st.columns(2)
            score_col1.metric("First round", progress["first_total_score"])
            score_col2.metric(
                "Second round",
                progress["second_total_score"],
                delta=progress["second_total_score"] - progress["first_total_score"],
            )
            st.dataframe(
                [
                    {"dimension": name.replace("_", " ").title(), "change": change}
                    for name, change in progress["dimension_changes"].items()
                ],
                use_container_width=True,
                hide_index=True,
            )
            safety_change = progress["safety_critical_omissions_change"]
            st.markdown(
                "**Resolved safety omissions:** "
                + (", ".join(safety_change["resolved"]) or "None")
            )
            st.markdown(
                "**Remaining safety omissions:** "
                + (", ".join(safety_change["second_round"]) or "None")
            )
            st.write(
                f"**Hints:** {progress['first_hints_used']} -> {progress['second_hints_used']} | "
                f"**Time:** {progress['first_completion_time']} -> "
                f"{progress['second_completion_time']} min"
            )
            st.markdown(
                "**Still needs improvement:** "
                + (
                    ", ".join(
                        item.replace("_", " ") for item in progress["still_needs_improvement"]
                    )
                    or "No dimension below the current threshold"
                )
            )
            st.caption(progress["interpretation"])

        st.download_button(
            "Download learner formative report",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"formative_report_{st.session_state.encounter_session_id or 'consultation'}.json",
            mime="application/json",
            use_container_width=True,
        )


if instructor_tab is not None:
    with instructor_tab:
        st.header("Instructor Workspace")
        st.warning("This view contains hidden case facts and must not be shown to learners.")
        st.subheader("Learner progress")

        try:
            all_dashboard = get_teacher_dashboard_logic()
            learner_options = ["All local learners"] + all_dashboard["available_learners"]
            selected_learner = st.selectbox("Learner record filter", learner_options)
            learner_filter = None if selected_learner == "All local learners" else selected_learner
            dashboard = (
                all_dashboard
                if learner_filter is None
                else get_teacher_dashboard_logic(learner_filter)
            )
            records = dashboard["records"]
            st.caption(
                f"{len(records)} structured session(s) | formative teaching support only"
            )
            if records:
                st.dataframe(
                    [
                        {
                            "session_id": record["session_id"],
                            "learner_id": record["learner_id"],
                            "case": record["case_id"],
                            "stage": record["current_stage"],
                            "score": record["overall_score"],
                            "hints": len(record["hints_used"]),
                            "safety_events": len(record["safety_events"]),
                            "retry_of": record["retry_of_session_id"],
                        }
                        for record in records
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                selected_session = st.selectbox(
                    "Training session",
                    [record["session_id"] for record in records],
                )
                selected_record = next(
                    record for record in records if record["session_id"] == selected_session
                )
                score_col, hint_col, time_col = st.columns(3)
                score_col.metric(
                    "Formative score",
                    selected_record["overall_score"]
                    if selected_record["overall_score"] is not None
                    else "Not assessed",
                )
                hint_col.metric("Hints used", len(selected_record["hints_used"]))
                time_col.metric("Simulated time", f"{selected_record['elapsed_time']} min")
                st.markdown(
                    "**Safety events:** "
                    + (", ".join(selected_record["safety_events"]) or "None")
                )
                if selected_record["dimension_scores"]:
                    st.dataframe(
                        [
                            {"dimension": name.replace("_", " ").title(), "score": score}
                            for name, score in selected_record["dimension_scores"].items()
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                with st.expander("Complete Action Trace", expanded=False):
                    st.dataframe(
                        [
                            {
                                "timestamp": entry["timestamp"],
                                "stage": entry["stage"],
                                "tool": entry["tool_name"],
                                "input": entry["natural_language_input"],
                                "status": entry["result_summary"].get("status"),
                                "hint": entry["hint_level"],
                                "safety": "; ".join(entry["safety_event"]),
                                "score_event": entry["score_event"],
                            }
                            for entry in selected_record["action_trace"]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                if selected_record["progress_report"]:
                    progress = selected_record["progress_report"]
                    st.subheader("First vs Second Attempt")
                    st.write(
                        f"**Total:** {progress['first_total_score']} -> "
                        f"{progress['second_total_score']}"
                    )
                    st.dataframe(
                        [
                            {"dimension": name.replace("_", " ").title(), "change": change}
                            for name, change in progress["dimension_changes"].items()
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.write(
                        "**Resolved safety omissions:**",
                        progress["safety_critical_omissions_change"]["resolved"] or ["None"],
                    )
                    st.caption(progress["interpretation"])
            else:
                st.info("No structured training records are available for this learner filter.")

            export_col1, export_col2 = st.columns(2)
            export_col1.download_button(
                "Download Teacher Report (Markdown)",
                data=export_teacher_dashboard_logic(learner_filter, format="markdown"),
                file_name=f"teacher_report_{learner_filter or 'all'}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            export_col2.download_button(
                "Download Teacher Report (JSON)",
                data=export_teacher_dashboard_logic(learner_filter, format="json"),
                file_name=f"teacher_report_{learner_filter or 'all'}.json",
                mime="application/json",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Teacher dashboard failed: {e}")

        st.divider()
        st.subheader("YAML case template validator")
        try:
            validation_templates = list_case_templates_for_validation_logic()
            template_labels = {
                f"{item['title']} ({item['case_id']})": item["case_id"]
                for item in validation_templates
            }
            validation_label = st.selectbox("YAML template", list(template_labels))
            if st.button("Validate YAML Template", use_container_width=True):
                st.session_state.case_validation_result = validate_case_template_logic(
                    template_labels[validation_label]
                )
            validation = st.session_state.case_validation_result
            if validation:
                if validation["valid"]:
                    st.success("Schema and blocking validation checks passed.")
                else:
                    st.error("Template validation failed. Review error-level findings.")
                st.write("**Metadata:**", validation["metadata"])
                issues = [
                    {**issue, "category": category}
                    for category, category_issues in (
                        ("schema", validation["schema_issues"]),
                        ("hidden", validation["hidden_rule_issues"]),
                        ("safety", validation["safety_rule_issues"]),
                    )
                    for issue in category_issues
                ]
                st.dataframe(issues, use_container_width=True, hide_index=True)
                st.subheader("Learner-visible preview")
                st.dataframe([validation["learner_preview"]], use_container_width=True, hide_index=True)
                validation_col1, validation_col2 = st.columns(2)
                validation_col1.download_button(
                    "Download Validation (Markdown)",
                    data=export_case_validation_logic(validation, format="markdown"),
                    file_name=f"validation_{validation['case_id']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
                validation_col2.download_button(
                    "Download Validation (JSON)",
                    data=export_case_validation_logic(validation, format="json"),
                    file_name=f"validation_{validation['case_id']}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        except Exception as e:
            st.error(f"Case template validation failed: {e}")

        st.divider()
        st.subheader("Instructor-only current case review")
        if not st.session_state.patient_id:
            st.info("Initialize a case to review its instructor-only state.")
        else:
            try:
                instructor_view = get_instructor_case_view_logic(st.session_state.patient_id)
                with st.expander("Full case blueprint"):
                    st.json(instructor_view.full_case.model_dump(mode="json"))
                with st.expander("Rubric"):
                    st.json(instructor_view.rubric)
                with st.expander("Learner action trace"):
                    st.json(instructor_view.learner_action_trace)
                with st.expander("Unlock history"):
                    st.json(instructor_view.unlock_history)
                with st.expander("Scoring evidence"):
                    st.json(instructor_view.scoring_evidence)
            except Exception as e:
                st.error(f"Instructor view failed: {e}")
