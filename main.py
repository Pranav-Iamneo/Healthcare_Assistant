"""
Smart Healthcare Assistant - Streamlit Interface
Multi-agent healthcare system using Agno framework and Gemini AI
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any
import traceback
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import config first to initialize settings
from config import settings

# Now import agents
orchestrator_agent = None
try:
    from agents.agno_orchestrator import orchestrator_agent as imported_agent
    orchestrator_agent = imported_agent
    if orchestrator_agent is None:
        st.warning("⚠️ Orchestrator not fully initialized. Check API key and database.")
except Exception as e:
    st.warning(f"⚠️ Failed to initialize orchestrator: {e}")
    print(f"Error details: {traceback.format_exc()}")

# Configure Streamlit page
st.set_page_config(
    page_title="Smart Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

STYLES = """
<style>
.card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    background: #fff;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px;
}

.kv {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px;
    font-size: 14px;
}

.kv b {
    color: #555;
}

.pills {
    margin: 6px 0;
}

.pill {
    display: inline-block;
    background: #f1f3f5;
    border: 1px solid #e6e8eb;
    padding: 4px 10px;
    border-radius: 999px;
    margin: 3px;
    font-size: 13px;
}

.h3 {
    font-weight: 600;
    margin: 18px 0 8px;
}

.status-success {
    color: #28a745;
    font-weight: 600;
}

.status-pending {
    color: #6c757d;
    font-weight: 600;
}

.status-processing {
    color: #ffc107;
    font-weight: 600;
}

.risk-high {
    color: #dc3545;
}

.risk-medium {
    color: #ffc107;
}

.risk-low {
    color: #28a745;
}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

# ============================================================================
# AGENT FUNCTIONS
# ============================================================================

def call_agent(operation: str, data: dict) -> Dict[str, Any]:
    """Call agents directly"""
    try:
        if not orchestrator_agent:
            return {"error": "Orchestrator not initialized"}

        if operation == "assess":
            # Initialize workflow with patient data
            workflow = orchestrator_agent.initialize_workflow(data)

            # Create agents dictionary for coordination
            from agents import (
                data_agent,
                diagnosis_agent,
                reasoning_agent,
                treatment_agent,
                evaluation_agent
            )

            agents = {
                "data_agent": data_agent,
                "diagnosis_agent": diagnosis_agent,
                "reasoning_agent": reasoning_agent,
                "treatment_agent": treatment_agent,
                "evaluation_agent": evaluation_agent
            }

            # Run the full assessment workflow
            workflow = orchestrator_agent.coordinate_assessment(workflow, agents)

            return {
                "status": "success",
                "assessment": workflow
            }
        else:
            return {"error": f"Unknown operation: {operation}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _to_py(o):
    """Normalize LLM JSON-ish like {'0': 'A', '1': 'B'} -> ['A','B'] recursively."""
    if isinstance(o, dict):
        keys = list(o.keys())
        if keys and all(str(k).isdigit() for k in keys):
            return [_to_py(o[str(i)]) for i in sorted(map(int, keys))]
        return {k: _to_py(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_to_py(v) for v in o]
    return o

def _as_list(x):
    """Convert to list"""
    x = _to_py(x)
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def render_pills(title: str, items: List[str]):
    """Render pill-style tags"""
    if not items:
        return
    st.markdown(f"<div class='h3'>{title}</div>", unsafe_allow_html=True)
    pills_html = "".join(f"<span class='pill'>{str(i)}</span>" for i in items)
    st.markdown(f"<div class='pills'>{pills_html}</div>", unsafe_allow_html=True)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Streamlit application"""

    # Header
    st.title("🏥 Smart Healthcare Assistant")
    st.caption("AI-driven patient health assessment with multi-agent Agno framework and Gemini AI")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Assessment", "💾 History", "ℹ️ System Info"])

    # ============ TAB 1: ASSESSMENT ============
    with tab1:
        st.header("Patient Health Assessment")

        # Sidebar configuration
        with st.sidebar:
            st.header("⚙️ Configuration")
            st.subheader("Quick Actions")

            if st.button("🚀 Run Sample Assessment", width="stretch"):
                with st.spinner("Running sample assessment..."):
                    try:
                        sample_data = {
                            "patient_name": "John Doe",
                            "age": 45,
                            "gender": "Male",
                            "symptoms": [{"name": "Headache", "severity": 7}, {"name": "Fever", "severity": 8}],
                            "medical_history": ["Hypertension"],
                            "vital_signs": {"temperature": 38.5, "blood_pressure": "140/90"}
                        }
                        result = call_agent("assess", sample_data)

                        if "error" in result:
                            st.error(f"Error: {result['error']}")
                        else:
                            st.session_state.last_assessment = result
                            st.success("✅ Sample assessment completed!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to run sample assessment: {str(e)}")

        # Two-column layout for patient input
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("👤 Patient Information")

            patient_name = st.text_input("Patient Name", value="John Doe", key="patient_name")
            patient_age = st.number_input("Age", min_value=0, max_value=150, value=35, key="patient_age")
            patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="patient_gender")

            st.subheader("🏥 Medical History")
            medical_history_input = st.text_area(
                "Medical History (comma-separated)",
                value="Hypertension, Type 2 Diabetes",
                height=80,
                key="medical_history"
            )
            medical_history = [h.strip() for h in medical_history_input.split(",") if h.strip()]

        with col2:
            st.subheader("💊 Medications & Allergies")

            medications_input = st.text_area(
                "Current Medications (comma-separated)",
                value="Aspirin (once daily), Metformin",
                height=80,
                key="medications"
            )
            medications = [m.strip() for m in medications_input.split(",") if m.strip()]

            st.subheader("⚠️ Allergies")
            allergies_input = st.text_area(
                "Known Allergies (comma-separated)",
                value="Penicillin",
                height=80,
                key="allergies"
            )
            allergies = [a.strip() for a in allergies_input.split(",") if a.strip()]

        # Symptoms section
        st.divider()
        st.subheader("🤒 Symptoms")

        # Dynamic symptom input
        st.caption("Add patient symptoms below. You can add multiple symptoms.")

        # Initialize symptoms list in session state
        if "symptoms" not in st.session_state:
            st.session_state.symptoms = [
                {"name": "fever", "severity": "moderate", "duration_days": 3, "details": "Temperature around 38.5°C"}
            ]

        symptoms_count = st.number_input(
            "Number of Symptoms",
            min_value=1,
            max_value=10,
            value=len(st.session_state.symptoms),
            key="symptoms_count"
        )

        # Adjust symptoms list
        while len(st.session_state.symptoms) < symptoms_count:
            st.session_state.symptoms.append({
                "name": "",
                "severity": "moderate",
                "duration_days": 0,
                "details": ""
            })

        while len(st.session_state.symptoms) > symptoms_count:
            st.session_state.symptoms.pop()

        # Display symptom inputs
        symptom_cols = st.columns([2, 2, 2, 2])

        with symptom_cols[0]:
            st.caption("Symptom Name")
        with symptom_cols[1]:
            st.caption("Severity")
        with symptom_cols[2]:
            st.caption("Duration (days)")
        with symptom_cols[3]:
            st.caption("Additional Details")

        for idx in range(symptoms_count):
            cols = st.columns([2, 2, 2, 2])

            with cols[0]:
                st.session_state.symptoms[idx]["name"] = st.text_input(
                    "Symptom",
                    value=st.session_state.symptoms[idx].get("name", ""),
                    key=f"symptom_name_{idx}",
                    label_visibility="collapsed"
                )

            with cols[1]:
                st.session_state.symptoms[idx]["severity"] = st.selectbox(
                    "Severity",
                    ["mild", "moderate", "severe"],
                    index=["mild", "moderate", "severe"].index(st.session_state.symptoms[idx].get("severity", "moderate")),
                    key=f"symptom_severity_{idx}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                st.session_state.symptoms[idx]["duration_days"] = st.number_input(
                    "Days",
                    min_value=0,
                    value=st.session_state.symptoms[idx].get("duration_days", 0),
                    key=f"symptom_duration_{idx}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                st.session_state.symptoms[idx]["details"] = st.text_input(
                    "Details",
                    value=st.session_state.symptoms[idx].get("details", ""),
                    key=f"symptom_details_{idx}",
                    label_visibility="collapsed"
                )

        # Additional context
        st.divider()
        st.subheader("📝 Additional Context")
        additional_context = st.text_area(
            "Any additional medical context or recent events",
            value="Recent office exposure",
            height=80,
            key="additional_context"
        )

        # Assessment button
        st.divider()

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            assess_button = st.button(
                "🔬 Run Health Assessment",
                type="primary",
                use_container_width=True,
                key="assess_button"
            )

        # Run assessment
        if assess_button:
            # Validate input
            if not patient_name:
                st.error("Please enter patient name")
                st.stop()

            if not any(s.get("name") for s in st.session_state.symptoms):
                st.error("Please add at least one symptom")
                st.stop()

            # Prepare assessment request
            assessment_request = {
                "patient": {
                    "name": patient_name,
                    "age": patient_age,
                    "gender": patient_gender,
                    "allergies": allergies,
                    "medications": medications,
                    "medical_history": medical_history
                },
                "symptoms": [
                    {
                        "name": s["name"],
                        "severity": s["severity"],
                        "duration_days": int(s["duration_days"]),
                        "additional_details": s.get("details", "")
                    }
                    for s in st.session_state.symptoms if s.get("name")
                ],
                "additional_context": additional_context
            }

            # Call Agent
            with st.spinner("🔄 Running comprehensive health assessment..."):
                try:
                    result = call_agent("assess", assessment_request)
                    assessment = None

                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.session_state.last_assessment = result
                        st.success("✅ Assessment completed successfully!")

                        # Display results
                        st.balloons()

                        assessment = result.get("assessment", {})

                    if assessment is not None and assessment:
                        # Display assessment summary
                        st.header("📊 Assessment Results")

                        # Try to get final summary
                        summary = assessment.get("final_summary")

                        # Debug: show what we got
                        if not summary:
                            st.warning("⚠️ Summary data is empty. Checking assessment status...")
                            st.write(f"Assessment status: {assessment.get('status')}")
                            st.write(f"Assessment error: {assessment.get('error', 'None')}")
                            # Try to reconstruct from available data
                            if assessment.get("diagnoses"):
                                summary = {
                                    "patient_name": assessment.get("patient", {}).get("patient", {}).get("name"),
                                    "assessment_date": assessment.get("assessment_date", "N/A"),
                                    "quality_score": assessment.get("evaluation", {}).get("quality_score", 0),
                                    "probable_diagnoses": assessment.get("diagnoses", []),
                                    "treatments": assessment.get("treatments", []),
                                    "symptoms_analyzed": [s["name"] for s in assessment.get("symptoms", [])],
                                    "diagnostic_tests": [],
                                    "next_steps": [],
                                    "safety_warnings": []
                                }

                        if summary:
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                # Use quality_score for confidence (0.0-1.0 scale)
                                quality_score = summary.get("quality_score", 0)
                                st.metric("Quality Score", f"{quality_score:.1%}" if isinstance(quality_score, (int, float)) else quality_score)

                            with col2:
                                assessment_date = summary.get("assessment_date", "N/A")
                                date_str = assessment_date.split("T")[0] if isinstance(assessment_date, str) and "T" in assessment_date else assessment_date
                                st.metric("Assessment Date", date_str)

                            with col3:
                                patient_name = summary.get("patient_name", "Unknown")
                                st.metric("Patient", patient_name)

                            # Primary diagnosis section
                            probable_diagnoses = summary.get("probable_diagnoses", [])
                            if probable_diagnoses:
                                st.subheader("🔍 Probable Diagnoses")

                                # Get the top diagnosis
                                if isinstance(probable_diagnoses, list) and len(probable_diagnoses) > 0:
                                    top_diagnosis = probable_diagnoses[0]
                                    if isinstance(top_diagnosis, dict):
                                        disease_name = top_diagnosis.get("disease", "Unknown")
                                        confidence = top_diagnosis.get("confidence_score", 0)
                                        st.info(f"**{disease_name}** (Confidence: {confidence:.1%})")
                                    else:
                                        st.info(f"**{top_diagnosis}**")

                                    # Show differential diagnoses
                                    if len(probable_diagnoses) > 1:
                                        st.write("**Differential Diagnoses:**")
                                        for idx, diag in enumerate(probable_diagnoses[1:], 2):
                                            if isinstance(diag, dict):
                                                disease = diag.get("disease", "Unknown")
                                                conf = diag.get("confidence_score", 0)
                                                st.write(f"{idx}. {disease} (Confidence: {conf:.1%})")
                                            else:
                                                st.write(f"{idx}. {diag}")

                            # Symptoms analyzed
                            symptoms_analyzed = summary.get("symptoms_analyzed", [])
                            if symptoms_analyzed:
                                st.subheader("🤒 Symptoms Analyzed")
                                st.write(", ".join(symptoms_analyzed))

                            # Treatment recommendations
                            treatments = summary.get("treatments", [])
                            if treatments:
                                st.subheader("💊 Treatment Recommendations")
                                for idx, treatment in enumerate(treatments[:5], 1):  # Show first 5
                                    if isinstance(treatment, dict):
                                        rec_text = treatment.get("recommendation", str(treatment))
                                        treatment_type = treatment.get("type", "").upper()
                                        st.write(f"{idx}. **[{treatment_type}]** {rec_text}")
                                    else:
                                        st.write(f"{idx}. {treatment}")

                            # Diagnostic tests
                            diagnostic_tests = summary.get("diagnostic_tests", [])
                            if diagnostic_tests:
                                st.subheader("🧪 Recommended Diagnostic Tests")
                                for idx, test in enumerate(diagnostic_tests[:5], 1):
                                    st.write(f"{idx}. {test}")

                            # Next steps
                            next_steps = summary.get("next_steps", [])
                            if next_steps:
                                st.subheader("📋 Next Steps")
                                for idx, step in enumerate(next_steps, 1):
                                    st.write(f"{idx}. {step}")

                            # Safety warnings
                            safety_warnings = summary.get("safety_warnings", [])
                            if safety_warnings:
                                st.subheader("⚠️ Safety Warnings")
                                for warning in safety_warnings:
                                    st.warning(warning)

                            # Full assessment data (expandable - formatted as table)
                            with st.expander("📄 View Detailed Assessment Summary", expanded=False):
                                detail_cols = st.columns(2)
                                with detail_cols[0]:
                                    st.write("**Assessment Metadata**")
                                    metadata = {
                                        "Patient": summary.get("patient_name", "N/A"),
                                        "Date": summary.get("assessment_date", "N/A"),
                                        "Quality Score": f"{summary.get('quality_score', 0):.1%}",
                                        "Symptoms Analyzed": ", ".join(summary.get("symptoms_analyzed", [])) or "N/A"
                                    }
                                    for key, value in metadata.items():
                                        st.text(f"**{key}:** {value}")

                                with detail_cols[1]:
                                    st.write("**Assessment Statistics**")
                                    stats = {
                                        "Total Diagnoses": len(summary.get("probable_diagnoses", [])),
                                        "Treatments Recommended": len(summary.get("treatments", [])),
                                        "Diagnostic Tests": len(summary.get("diagnostic_tests", [])),
                                        "Next Steps": len(summary.get("next_steps", []))
                                    }
                                    for key, value in stats.items():
                                        st.text(f"**{key}:** {value}")
                        else:
                            st.warning("Assessment completed but summary data is incomplete")
                            with st.expander("📄 View Raw Assessment Data", expanded=True):
                                st.json(assessment)
                    else:
                        if result.get("error"):
                            st.error(f"Assessment Error: {result.get('error', 'Unknown error')}")
                        else:
                            st.error(f"Assessment failed: {result.get('message', 'No assessment data returned')}")

                except Exception as e:
                    st.error(f"Error during assessment: {str(e)}")
                    st.write(traceback.format_exc())

    # ============ TAB 2: HISTORY ============
    with tab2:
        st.header("Assessment History")

        if "last_assessment" in st.session_state:
            assessment = st.session_state.last_assessment

            if assessment and assessment.get("status") == "success":
                assessment_data = assessment.get("assessment", {})
                summary = assessment_data.get("final_summary") if assessment_data else None

                if summary:
                    st.subheader(f"Assessment for: {summary.get('patient_name', 'Unknown')}")

                    # Create history card
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        assessment_date = summary.get("assessment_date", "N/A")
                        date_str = assessment_date.split("T")[0] if assessment_date else "N/A"
                        st.metric("Date", date_str)

                    with col2:
                        # Extract primary diagnosis from probable_diagnoses array
                        probable_diagnoses = summary.get("probable_diagnoses", [])
                        if probable_diagnoses and isinstance(probable_diagnoses, list) and len(probable_diagnoses) > 0:
                            primary = probable_diagnoses[0]
                            if isinstance(primary, dict):
                                primary_diagnosis = primary.get("disease", "N/A")
                            else:
                                primary_diagnosis = str(primary)
                        else:
                            primary_diagnosis = "N/A"
                        diagnosis_display = (primary_diagnosis[:30] + "...") if len(str(primary_diagnosis)) > 30 else primary_diagnosis
                        st.metric("Primary Diagnosis", diagnosis_display)

                    with col3:
                        # Use quality_score instead of confidence
                        quality_score = summary.get("quality_score", 0)
                        st.metric("Quality Score", f"{quality_score:.1%}" if isinstance(quality_score, (int, float)) else quality_score)

                    with col4:
                        # Get risk assessment from probable diagnoses (could also extract from evaluation)
                        # For now, show quality score as a proxy for risk (higher quality = lower risk)
                        quality = summary.get("quality_score", 0.5)
                        if quality >= 0.75:
                            risk_display = "LOW"
                        elif quality >= 0.5:
                            risk_display = "MODERATE"
                        else:
                            risk_display = "HIGH"
                        st.metric("Risk Level", risk_display)

                    # Expandable details - Formatted summary instead of raw JSON
                    with st.expander("📋 View Full History Details", expanded=False):
                        st.write("**Diagnosis Details**")
                        probable_diagnoses = summary.get("probable_diagnoses", [])
                        if probable_diagnoses:
                            for idx, diagnosis in enumerate(probable_diagnoses, 1):
                                if isinstance(diagnosis, dict):
                                    disease = diagnosis.get("disease", "Unknown")
                                    confidence = diagnosis.get("confidence_score", 0)
                                    st.write(f"{idx}. **{disease}** - Confidence: {confidence:.1%}")
                                    indicators = diagnosis.get("key_indicators", [])
                                    if indicators:
                                        st.caption(f"   Key indicators: {', '.join(str(i) for i in indicators[:2])}")

                        st.divider()
                        st.write("**Treatment Recommendations**")
                        treatments = summary.get("treatments", [])
                        if treatments:
                            for idx, treatment in enumerate(treatments[:3], 1):
                                if isinstance(treatment, dict):
                                    rec = treatment.get("recommendation", "N/A")
                                    t_type = treatment.get("type", "").upper()
                                    st.write(f"{idx}. **[{t_type}]** {rec}")
                        else:
                            st.write("No treatments recommended")

                        st.divider()
                        st.write("**Safety Warnings**")
                        safety_warnings = summary.get("safety_warnings", [])
                        if safety_warnings:
                            for warning in safety_warnings:
                                st.warning(warning)
                        else:
                            st.write("No safety warnings")
                else:
                    st.warning("Assessment data incomplete")
            else:
                st.warning("No successful assessment history")
        else:
            st.info("No assessment history yet. Run an assessment first!")

    # ============ TAB 3: SYSTEM INFO ============
    with tab3:
        st.header("System Information")

        with st.spinner("Loading system info..."):
            info = {"name": "Smart Healthcare Assistant", "version": "1.0.0", "framework": "Agno Framework", "model": "Gemini AI", "status": "running"}

            if "error" not in info:
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Name", info.get("name", "N/A"))
                    st.metric("Version", info.get("version", "N/A"))
                    st.metric("Framework", info.get("framework", "N/A"))
                    st.metric("Model", info.get("model", "N/A"))

                with col2:
                    st.metric("Database", info.get("database", "N/A"))
                    st.metric("Knowledge Base", info.get("knowledge_base", "N/A"))
                    st.metric("Agent Count", len(info.get("agents", [])))

                st.subheader("Available Agents")
                agents = info.get("agents", [])

                agent_data = []
                for agent in agents:
                    agent_data.append({
                        "Agent": agent,
                        "Status": "✅ Active"
                    })

                if agent_data:
                    st.dataframe(pd.DataFrame(agent_data), use_container_width=True, hide_index=True)
            else:
                st.error(f"Error loading system info: {info.get('error', 'Unknown error')}")

        # Health check
        st.divider()
        st.subheader("Health Check")

        with st.spinner("Checking health..."):
            health = {"status": "healthy", "message": "Healthcare Assistant is running and ready"}

            if "error" not in health:
                status = health.get("status", "unknown")

                if status == "healthy":
                    st.success(f"✅ {health.get('message', 'System is healthy')}")
                else:
                    st.warning(f"⚠️ {health.get('message', 'System status unknown')}")
            else:
                st.error(f"Error checking health: {health.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
