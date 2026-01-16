"""
RMD-Health Screening Agent - Streamlit Application
===================================================

This is the main Streamlit web application for the RMD-Health Screening Agent.
It provides a user-friendly interface for:
- Entering patient screening data
- Running AI-powered RMD risk assessment
- Displaying results with explanations

IMPORTANT DISCLAIMER:
This is a DEMONSTRATION PROTOTYPE only. It is NOT intended for clinical use
or real patient data. Do not use for actual medical decision-making.

Run with: streamlit run app.py
"""

import streamlit as st
import json
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.data_models import PatientScreening, Symptom, RMDAssessment
from src.rmd_agent import RMDScreeningAgent, demo_assessment

# Page configuration
st.set_page_config(
    page_title="RMD-Health Screening Agent",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .disclaimer-banner {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .disclaimer-banner h4 {
        color: #856404;
        margin: 0 0 8px 0;
    }
    .disclaimer-banner p {
        color: #856404;
        margin: 0;
        font-size: 14px;
    }
    .risk-high {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 16px;
    }
    .risk-moderate {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 16px;
    }
    .risk-low {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 16px;
    }
    .stMetric > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def show_disclaimer():
    """Display the important disclaimer banner."""
    st.markdown("""
    <div class="disclaimer-banner">
        <h4>⚠️ IMPORTANT DISCLAIMER</h4>
        <p>
            This is a <strong>DEMONSTRATION PROTOTYPE ONLY</strong>. It is NOT intended for clinical use, 
            real patient data, or actual medical decision-making. This application was created for 
            educational and interview demonstration purposes. Any outputs should NOT be considered 
            medical advice. Always consult qualified healthcare professionals for medical concerns.
        </p>
    </div>
    """, unsafe_allow_html=True)


def create_sidebar():
    """Create the sidebar with information and settings."""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/stethoscope.png", width=80)
        st.title("RMD-Health")
        st.markdown("### AI Screening Agent")
        
        st.markdown("---")
        
        st.markdown("""
        **About this Demo**
        
        This prototype demonstrates:
        - 🤖 Agentic AI with LLM reasoning
        - 📊 FHIR-inspired data models
        - 🔍 Explainable AI outputs
        - 🏥 Clinical decision support concepts
        
        Built for the AI Software Engineer role interview at University of Reading.
        """)
        
        st.markdown("---")
        
        # Mode selection
        st.markdown("### Settings")
        
        # Check if API key is configured
        agent = RMDScreeningAgent()
        api_configured = agent.is_configured()
        
        if api_configured:
            st.success("✅ API Key Configured")
            demo_mode = st.checkbox("Use Demo Mode (no API calls)", value=False)
        else:
            st.warning("⚠️ No API Key Found")
            st.info("Using Demo Mode (rule-based only)")
            demo_mode = True
        
        st.session_state['demo_mode'] = demo_mode
        
        st.markdown("---")
        
        # Load sample data option
        st.markdown("### Quick Load")
        if st.button("📋 Load High-Risk Example"):
            load_sample_data("high_risk")
        if st.button("📋 Load Low-Risk Example"):
            load_sample_data("low_risk")
        
        st.markdown("---")
        
        st.markdown("""
        **Technology Stack**
        - Python 3.10+
        - Streamlit
        - Pydantic
        - xAI Grok API
        
        [View on GitHub](#) | [Documentation](#)
        """)


def load_sample_data(risk_type: str):
    """Load sample patient data into the session state."""
    sample_file = Path("sample_data/example_patient.json")
    
    if sample_file.exists():
        with open(sample_file, "r") as f:
            data = json.load(f)
        
        if risk_type in data:
            patient_data = data[risk_type]
            st.session_state['sample_data'] = patient_data
            st.rerun()
    else:
        # Hardcoded fallback if file doesn't exist
        if risk_type == "high_risk":
            st.session_state['sample_data'] = {
                "age": 45,
                "sex": "Female",
                "joint_pain": True,
                "joint_pain_severity": 7,
                "multiple_joints": True,
                "morning_stiffness": True,
                "morning_stiffness_duration": 60,
                "joint_swelling": True,
                "joint_redness": True,
                "fatigue": True,
                "fatigue_severity": 6,
                "fever": False,
                "weight_loss": False,
                "skin_rash": False,
                "medical_history": "Family history of rheumatoid arthritis (mother). No current medications."
            }
        else:
            st.session_state['sample_data'] = {
                "age": 35,
                "sex": "Male",
                "joint_pain": True,
                "joint_pain_severity": 3,
                "multiple_joints": False,
                "morning_stiffness": False,
                "morning_stiffness_duration": 10,
                "joint_swelling": False,
                "joint_redness": False,
                "fatigue": False,
                "fatigue_severity": 2,
                "fever": False,
                "weight_loss": False,
                "skin_rash": False,
                "medical_history": "Occasional knee pain after exercise. No family history of arthritis."
            }
        st.rerun()


def get_default_value(key: str, default):
    """Get value from sample data or return default."""
    if 'sample_data' in st.session_state:
        return st.session_state['sample_data'].get(key, default)
    return default


def create_patient_form() -> PatientScreening | None:
    """Create the patient data input form and return PatientScreening if submitted."""
    
    st.markdown("### 📝 Patient Screening Form")
    st.markdown("Enter the patient's symptoms and information below:")
    
    with st.form("screening_form"):
        # Demographics
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider(
                "Age (years)",
                min_value=18,
                max_value=100,
                value=get_default_value("age", 45),
                help="Patient's current age"
            )
        
        with col2:
            sex = st.selectbox(
                "Sex",
                options=["Male", "Female", "Other", "Prefer not to say"],
                index=["Male", "Female", "Other", "Prefer not to say"].index(
                    get_default_value("sex", "Female")
                ),
                help="Patient's biological sex"
            )
        
        st.markdown("---")
        st.markdown("#### 🦴 Joint Symptoms")
        
        # Joint pain
        col1, col2 = st.columns(2)
        with col1:
            joint_pain = st.checkbox(
                "Joint Pain",
                value=get_default_value("joint_pain", False),
                help="Patient reports joint pain"
            )
        with col2:
            joint_pain_severity = st.slider(
                "Pain Severity (0-10)",
                min_value=0,
                max_value=10,
                value=get_default_value("joint_pain_severity", 5),
                disabled=not joint_pain
            )
        
        # Multiple joints
        multiple_joints = st.checkbox(
            "Multiple Joints Affected",
            value=get_default_value("multiple_joints", False),
            help="Pain/symptoms in 3 or more joints"
        )
        
        # Morning stiffness
        col1, col2 = st.columns(2)
        with col1:
            morning_stiffness = st.checkbox(
                "Morning Stiffness",
                value=get_default_value("morning_stiffness", False),
                help="Joint stiffness upon waking"
            )
        with col2:
            stiffness_duration = st.slider(
                "Duration (minutes)",
                min_value=0,
                max_value=120,
                value=get_default_value("morning_stiffness_duration", 30),
                disabled=not morning_stiffness,
                help="How long does morning stiffness last?"
            )
        
        st.markdown("---")
        st.markdown("#### 🔴 Inflammatory Signs")
        
        col1, col2 = st.columns(2)
        with col1:
            joint_swelling = st.checkbox(
                "Joint Swelling",
                value=get_default_value("joint_swelling", False),
                help="Visible swelling of joints"
            )
        with col2:
            joint_redness = st.checkbox(
                "Joint Redness/Warmth",
                value=get_default_value("joint_redness", False),
                help="Redness or warmth over joints"
            )
        
        st.markdown("---")
        st.markdown("#### 🌡️ Systemic Symptoms")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fatigue = st.checkbox(
                "Fatigue",
                value=get_default_value("fatigue", False),
                help="Unusual tiredness or fatigue"
            )
            fatigue_severity = st.slider(
                "Fatigue Severity",
                0, 10,
                value=get_default_value("fatigue_severity", 5),
                disabled=not fatigue
            )
        
        with col2:
            fever = st.checkbox(
                "Fever",
                value=get_default_value("fever", False),
                help="Elevated temperature"
            )
        
        with col3:
            weight_loss = st.checkbox(
                "Unexplained Weight Loss",
                value=get_default_value("weight_loss", False)
            )
        
        skin_rash = st.checkbox(
            "Skin Rash",
            value=get_default_value("skin_rash", False),
            help="Any skin rashes or lesions"
        )
        
        st.markdown("---")
        st.markdown("#### 📋 Medical History")
        
        medical_history = st.text_area(
            "Relevant Medical History",
            value=get_default_value("medical_history", ""),
            height=100,
            placeholder="Enter any relevant medical history, family history, current medications, or additional notes...",
            help="Include family history, current medications, previous diagnoses"
        )
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🔍 Run RMD Screening Assessment",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Clear sample data after submission
            if 'sample_data' in st.session_state:
                del st.session_state['sample_data']
            
            # Build symptoms list
            symptoms = []
            
            symptoms.append(Symptom(
                name="joint_pain",
                present=joint_pain,
                severity=joint_pain_severity if joint_pain else None
            ))
            
            symptoms.append(Symptom(
                name="multiple_joints_affected",
                present=multiple_joints
            ))
            
            symptoms.append(Symptom(
                name="morning_stiffness",
                present=morning_stiffness,
                duration_days=stiffness_duration if morning_stiffness else None
            ))
            
            symptoms.append(Symptom(
                name="joint_swelling",
                present=joint_swelling
            ))
            
            symptoms.append(Symptom(
                name="joint_redness",
                present=joint_redness
            ))
            
            symptoms.append(Symptom(
                name="fatigue",
                present=fatigue,
                severity=fatigue_severity if fatigue else None
            ))
            
            symptoms.append(Symptom(
                name="fever",
                present=fever
            ))
            
            symptoms.append(Symptom(
                name="weight_loss",
                present=weight_loss
            ))
            
            symptoms.append(Symptom(
                name="skin_rash",
                present=skin_rash
            ))
            
            # Create PatientScreening object
            patient = PatientScreening(
                age=age,
                sex=sex,
                symptoms=symptoms,
                medical_history=medical_history if medical_history else None
            )
            
            return patient
    
    return None


def display_assessment(assessment: RMDAssessment):
    """Display the assessment results in a clear, structured format."""
    
    st.markdown("---")
    st.markdown("## 📊 Assessment Results")
    
    # Risk level banner
    risk_colors = {
        "HIGH": ("🔴", "risk-high", "#dc3545"),
        "MODERATE": ("🟡", "risk-moderate", "#ffc107"),
        "LOW": ("🟢", "risk-low", "#28a745")
    }
    
    icon, css_class, color = risk_colors[assessment.risk_level]
    
    st.markdown(f"""
    <div class="{css_class}">
        <h2 style="margin:0; color: {color};">{icon} Risk Level: {assessment.risk_level}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Confidence Score",
            value=f"{assessment.confidence_score:.0%}",
            help="Model's confidence in this assessment"
        )
    
    with col2:
        st.metric(
            label="Conditions Identified",
            value=len(assessment.likely_conditions),
            help="Number of possible conditions to consider"
        )
    
    with col3:
        st.metric(
            label="Red Flags",
            value=len(assessment.red_flags_identified),
            help="Clinical red flags identified"
        )
    
    st.markdown("---")
    
    # Likely conditions
    st.markdown("### 🏥 Possible Conditions to Consider")
    if assessment.likely_conditions:
        for condition in assessment.likely_conditions:
            st.markdown(f"- {condition}")
    else:
        st.info("No specific conditions identified")
    
    # Red flags
    if assessment.red_flags_identified:
        st.markdown("### ⚠️ Red Flags Identified")
        for flag in assessment.red_flags_identified:
            st.warning(f"🚨 {flag}")
    
    # Recommended next step
    st.markdown("### 📋 Recommended Next Step")
    if assessment.risk_level == "HIGH":
        st.error(f"**{assessment.recommended_next_step}**")
    elif assessment.risk_level == "MODERATE":
        st.warning(f"**{assessment.recommended_next_step}**")
    else:
        st.success(f"**{assessment.recommended_next_step}**")
    
    # Reasoning
    st.markdown("### 🧠 Clinical Reasoning")
    with st.expander("View Detailed Reasoning", expanded=True):
        st.markdown(assessment.reasoning)
    
    # Metadata
    st.markdown("---")
    st.caption(f"Assessment generated at: {assessment.assessment_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Repeat disclaimer
    show_disclaimer()


def main():
    """Main application entry point."""
    
    # Header
    st.title("🩺 RMD-Health Screening Agent")
    st.markdown("""
    An AI-powered clinical decision support prototype for early detection of 
    **Rheumatic and Musculoskeletal Diseases (RMDs)**.
    """)
    
    # Show disclaimer
    show_disclaimer()
    
    # Create sidebar
    create_sidebar()
    
    # Main content
    patient = create_patient_form()
    
    if patient is not None:
        # Show spinner while processing
        with st.spinner("🔍 Analyzing patient data..."):
            # Check mode
            demo_mode = st.session_state.get('demo_mode', True)
            
            if demo_mode:
                assessment = demo_assessment(patient)
            else:
                agent = RMDScreeningAgent()
                assessment = agent.assess(patient)
        
        # Display results
        display_assessment(assessment)
        
        # Show raw data in expander
        with st.expander("📄 View Raw Data (JSON)"):
            st.markdown("#### Patient Screening Data")
            st.json(json.loads(patient.model_dump_json()))
            
            st.markdown("#### Assessment Result")
            st.json(json.loads(assessment.model_dump_json()))


if __name__ == "__main__":
    main()
