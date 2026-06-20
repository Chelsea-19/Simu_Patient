import json

import streamlit as st

from app.core.config import get_settings
from app.streamlit_services import (
    consultation_chat_logic,
    create_patient_from_case_logic,
    create_patient_logic,
    ensure_db_ready,
    evaluate_consultation_logic,
    list_case_templates_logic,
)


st.set_page_config(
    page_title="SimuPatient - AI Standardized Patient",
    page_icon="SP",
    layout="wide",
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
if "patient_profile" not in st.session_state:
    st.session_state.patient_profile = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "assessment" not in st.session_state:
    st.session_state.assessment = None

st.sidebar.title("System Status")
st.sidebar.success("Application ready")
st.sidebar.markdown(f"**Provider:** `{settings.selected_provider}`")
if settings.selected_provider == "gemini":
    st.sidebar.markdown(f"**Current model:** `{settings.GEMINI_MODEL}`")
elif settings.selected_provider == "ollama":
    st.sidebar.markdown(f"**Current model:** `{settings.OLLAMA_MODEL}`")
else:
    st.sidebar.markdown("**Current model:** `mock:deterministic`")
st.sidebar.markdown("---")
st.sidebar.info(
    "Data is saved automatically to the local SQLite database. On Streamlit Community Cloud, "
    "this database will reset when the app sleeps."
)

if st.sidebar.button("Reset Current Session", use_container_width=True):
    st.session_state.patient_id = None
    st.session_state.patient_profile = None
    st.session_state.chat_history = []
    st.session_state.assessment = None
    st.rerun()

st.title("SimuPatient: Medical SP Simulator")
st.markdown("A clinical standardized patient simulator with pluggable LLM providers.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Create Patient", "Consultation", "OSCE Assessment"])

with tab1:
    st.header("Generate Standardized Patient")
    patient_mode = st.radio(
        "Patient mode",
        ["Random patient", "Case template"],
        horizontal=True,
    )

    if patient_mode == "Random patient":
        seed_text = st.text_area(
            "Patient Description",
            placeholder="e.g. A 45-year-old male with sudden chest pain for 2 hours...",
            help="Input a brief clinical scenario to generate a full patient profile.",
        )

        if st.button("Generate Patient"):
            if not seed_text:
                st.error("Please enter a description.")
            else:
                with st.spinner(f"Generating clinical profile using {settings.selected_provider}..."):
                    try:
                        data = create_patient_logic(
                            seed_text=seed_text,
                            template_id=None,
                        )
                        st.session_state.patient_id = data["id"]
                        st.session_state.patient_profile = data["profile"]
                        st.session_state.chat_history = []
                        st.session_state.assessment = None
                        st.success(f"Patient generated. ID: {data['id']}")
                        st.json(data["profile"])
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
        if case_options:
            selected_label = st.selectbox("Case Template", list(case_options.keys()))
        else:
            st.info("No case templates are available.")

        if selected_label:
            selected_case = next(case for case in cases if case.case_id == case_options[selected_label])
            st.caption(
                f"{selected_case.specialty} | {selected_case.difficulty} | "
                f"{selected_case.demographics.age}-year-old {selected_case.demographics.gender}"
            )
            st.write(f"**Chief Complaint:** {selected_case.chief_complaint}")

        if st.button("Start Case Consultation", disabled=selected_label is None):
            with st.spinner("Initializing standardized case..."):
                try:
                    data = create_patient_from_case_logic(case_options[selected_label])
                    st.session_state.patient_id = data["id"]
                    st.session_state.patient_profile = data["profile"]
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": data["opening_statement"]}
                    ]
                    st.session_state.assessment = None
                    st.success(f"Case initialized. Patient ID: {data['id']}")
                    st.json(data["profile"])
                except Exception as e:
                    st.error(f"Case initialization failed: {e}")

with tab2:
    if not st.session_state.patient_id:
        st.warning("Please create a patient first in the first tab.")
    else:
        st.header(f"Chat with Patient: {st.session_state.patient_profile.get('name', 'Unknown')}")

        with st.expander("Patient Profile Summary"):
            patient = st.session_state.patient_profile
            st.write(f"**Age:** {patient.get('age')} | **Gender:** {patient.get('gender')}")
            st.write(f"**Chief Complaint:** {patient.get('chief_complaint')}")
            st.write(f"**History:** {patient.get('history', 'N/A')}")

        chat_container = st.container(height=400)
        for msg in st.session_state.chat_history:
            with chat_container.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask the patient something..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.write(prompt)

            with st.spinner("Patient is thinking..."):
                try:
                    reply = consultation_chat_logic(
                        patient_id=st.session_state.patient_id,
                        user_input=prompt,
                        history=st.session_state.chat_history[:-1],
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    with chat_container.chat_message("assistant"):
                        st.write(reply)
                except Exception as e:
                    st.error(f"Chat failed: {e}")

        st.markdown("---")
        if not st.session_state.chat_history:
            st.info("Start a conversation with the patient above to evaluate.")
        elif st.button("Finish Consultation and Evaluate"):
            with st.spinner("Analyzing consultation transcript..."):
                try:
                    result = evaluate_consultation_logic(
                        patient_id=st.session_state.patient_id,
                        history=st.session_state.chat_history,
                    )
                    st.session_state.assessment = result.model_dump()
                    st.success("Evaluation complete. Go to Tab 3.")
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

with tab3:
    if not st.session_state.assessment:
        st.warning("No assessment report yet. Finish the consultation in Tab 2.")
    else:
        result = st.session_state.assessment
        st.header("Final Assessment Report")

        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Score", f"{result.get('score', 0)}/100")
        col2.metric("Latency", f"{result.get('latency_ms', 0):.0f}ms")
        col3.metric("Model", result.get("model_used", "N/A"))

        st.subheader("Clinical Feedback")
        st.info(result.get("feedback", "No feedback provided."))

        st.subheader("Dimensions Breakdown")

        cols = st.columns(5)
        cols[0].metric("History Taking", f"{result.get('history_taking_score', 0)}/100")
        cols[1].metric("Communication", f"{result.get('communication_score', 0)}/100")
        cols[2].metric("Reasoning", f"{result.get('clinical_reasoning_score', 0)}/100")
        cols[3].metric("Empathy", f"{result.get('empathy_score', 0)}/100")
        cols[4].metric("Closure", f"{result.get('closure_score', 0)}/100")

        with st.expander("View Full JSON Report"):
            st.json(json.loads(json.dumps(result)))
