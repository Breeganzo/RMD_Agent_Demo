"""
RMD-Health Screening Agent - Professional Streamlit Application
================================================================

A clinical decision support prototype demonstrating:
- Explainable AI (XAI) for healthcare
- Role-based explanations (Clinicians, Patients, Auditors)
- FHIR R4 healthcare data standards
- LangChain ReAct Agentic AI

Built for University of Reading RMD-Health Project Interview Demonstration

IMPORTANT DISCLAIMER:
This is a DEMONSTRATION PROTOTYPE only. NOT for clinical use.

Run with: streamlit run app.py
"""

import streamlit as st
import json
from datetime import datetime
import os
from pathlib import Path
import uuid

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.data_models import PatientScreening, Symptom, RMDAssessment
from src.rmd_agent import RMDScreeningAgent, demo_assessment
from src.fhir_resources import create_screening_bundle, FHIRBundle
from src.xai_explanations import (
    UserRole, XAIExplanation, generate_xai_explanation, 
    get_explanation_for_role, FeatureContribution
)

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="RMD-Health | AI Screening Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        # RMD-Health Screening Agent
        
        An AI-powered clinical decision support prototype for early detection of 
        Rheumatic and Musculoskeletal Diseases (RMDs).
        
        Built for the University of Reading RMD-Health Project.
        
        **DISCLAIMER:** This is a demonstration prototype only.
        """
    }
)

# =============================================================================
# CUSTOM CSS - Professional Healthcare UI
# =============================================================================

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Role selection cards */
    .role-card {
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        height: 100%;
    }
    
    .role-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .role-clinician {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .role-patient {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .role-auditor {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
    }
    
    .role-icon {
        font-size: 48px;
        margin-bottom: 12px;
    }
    
    .role-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .role-desc {
        font-size: 14px;
        opacity: 0.9;
    }
    
    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(90deg, #fff3cd 0%, #ffeeba 100%);
        border-left: 5px solid #ffc107;
        border-radius: 0 8px 8px 0;
        padding: 16px 20px;
        margin-bottom: 24px;
    }
    
    .disclaimer-banner h4 {
        color: #856404;
        margin: 0 0 8px 0;
        font-size: 16px;
    }
    
    .disclaimer-banner p {
        color: #856404;
        margin: 0;
        font-size: 14px;
    }
    
    /* Risk level badges */
    .risk-badge {
        display: inline-block;
        padding: 8px 24px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .risk-high {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
    }
    
    .risk-moderate {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: #333;
    }
    
    .risk-low {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    /* Result cards */
    .result-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }
    
    /* Feature contribution bars */
    .contrib-bar {
        height: 24px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    
    .contrib-positive {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
    }
    
    .contrib-negative {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    }
    
    /* XAI Explanation tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
    }
    
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 24px;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .main-header p {
        color: #666;
        font-size: 1.1rem;
    }
    
    /* Info boxes */
    .info-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = True
    if 'assessment_complete' not in st.session_state:
        st.session_state.assessment_complete = False
    if 'current_assessment' not in st.session_state:
        st.session_state.current_assessment = None
    if 'current_patient' not in st.session_state:
        st.session_state.current_patient = None
    if 'xai_explanation' not in st.session_state:
        st.session_state.xai_explanation = None
    if 'sample_data' not in st.session_state:
        st.session_state.sample_data = None


# =============================================================================
# COMPONENT: DISCLAIMER BANNER
# =============================================================================

def show_disclaimer():
    """Display the important disclaimer banner."""
    st.markdown("""
    <div class="disclaimer-banner">
        <h4>⚠️ IMPORTANT DISCLAIMER - DEMONSTRATION PROTOTYPE</h4>
        <p>
            This is a <strong>demonstration prototype</strong> built for educational and interview purposes. 
            It is <strong>NOT</strong> intended for clinical use, real patient data, or medical decision-making. 
            All outputs are simulated and should NOT be considered medical advice. 
            Always consult qualified healthcare professionals.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# COMPONENT: ROLE SELECTION
# =============================================================================

def show_role_selection():
    """Display the role selection interface."""
    st.markdown("""
    <div class="main-header">
        <h1>🏥 RMD-Health Screening Agent</h1>
        <p>AI-Powered Clinical Decision Support with Explainable AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    show_disclaimer()
    
    st.markdown("### 👤 Select Your Role")
    st.markdown("Choose how you'd like to view the AI's explanations:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="role-card role-clinician">
            <div class="role-icon">👨‍⚕️</div>
            <div class="role-title">Healthcare Clinician</div>
            <div class="role-desc">
                Technical explanations with clinical terminology, 
                evidence references, and detailed reasoning traces
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Continue as Clinician", key="btn_clinician", use_container_width=True):
            st.session_state.user_role = UserRole.CLINICIAN
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="role-card role-patient">
            <div class="role-icon">🧑‍🤝‍🧑</div>
            <div class="role-title">Patient</div>
            <div class="role-desc">
                Simple, reassuring explanations in plain language
                with clear next steps and support information
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Continue as Patient", key="btn_patient", use_container_width=True):
            st.session_state.user_role = UserRole.PATIENT
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="role-card role-auditor">
            <div class="role-icon">📋</div>
            <div class="role-title">Regulator / Auditor</div>
            <div class="role-desc">
                Complete audit trails, decision logs, timestamps,
                and regulatory compliance documentation
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Continue as Auditor", key="btn_auditor", use_container_width=True):
            st.session_state.user_role = UserRole.AUDITOR
            st.rerun()
    
    # Demo info
    st.markdown("---")
    with st.expander("ℹ️ About This Demo", expanded=False):
        st.markdown("""
        ### What is this?
        
        This is a demonstration of **Explainable AI (XAI)** in healthcare, showing how AI systems can provide 
        different explanations to different audiences while maintaining transparency and trust.
        
        ### Key Features:
        
        - **🤖 Agentic AI**: Uses LangChain ReAct agents that autonomously decide which analysis tools to use
        - **🔍 Explainable AI**: Provides LIME/SHAP-style feature contributions and reasoning traces
        - **🏥 FHIR R4 Compliance**: Outputs proper HL7 FHIR healthcare data resources
        - **👥 Role-Based Views**: Tailored explanations for clinicians, patients, and auditors
        - **📊 Audit Trails**: Complete decision logging for regulatory compliance
        
        ### Technology Stack:
        
        - **LangChain + LangGraph**: Agentic AI framework
        - **Groq API**: Free LLM inference (Llama 3.1)
        - **Streamlit**: Interactive web interface
        - **FHIR R4**: Healthcare interoperability standard
        - **Pydantic**: Data validation
        """)


# =============================================================================
# COMPONENT: SIDEBAR
# =============================================================================

def create_sidebar():
    """Create the sidebar with settings and information."""
    with st.sidebar:
        # Logo and title
        st.markdown("### 🏥 RMD-Health Agent")
        
        # Current role display
        if st.session_state.user_role:
            role_info = {
                UserRole.CLINICIAN: ("👨‍⚕️", "Clinician View", "#667eea"),
                UserRole.PATIENT: ("🧑‍🤝‍🧑", "Patient View", "#11998e"),
                UserRole.AUDITOR: ("📋", "Auditor View", "#eb3349"),
            }
            icon, name, color = role_info[st.session_state.user_role]
            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 12px; 
                        border-radius: 8px; text-align: center; margin-bottom: 16px;">
                <span style="font-size: 24px;">{icon}</span><br>
                <strong>{name}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick role switch (preserves assessment)
            if st.session_state.assessment_complete:
                st.success("✅ Assessment complete!")
                st.markdown("**🔄 View same result as:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👨‍⚕️\nDoc", help="Clinician View", key="sw_clin", 
                                disabled=st.session_state.user_role == UserRole.CLINICIAN,
                                use_container_width=True):
                        st.session_state.user_role = UserRole.CLINICIAN
                        st.rerun()
                with col2:
                    if st.button("🧑‍🤝‍🧑\nPat", help="Patient View", key="sw_pat",
                                disabled=st.session_state.user_role == UserRole.PATIENT,
                                use_container_width=True):
                        st.session_state.user_role = UserRole.PATIENT
                        st.rerun()
                with col3:
                    if st.button("📋\nAudit", help="Auditor View", key="sw_aud",
                                disabled=st.session_state.user_role == UserRole.AUDITOR,
                                use_container_width=True):
                        st.session_state.user_role = UserRole.AUDITOR
                        st.rerun()
                st.caption("Same risk level, different explanations")
                st.markdown("---")
            
            if st.button("🔄 Start New Assessment", use_container_width=True):
                st.session_state.user_role = None
                st.session_state.assessment_complete = False
                st.session_state.current_assessment = None
                st.session_state.current_patient = None
                st.session_state.xai_explanation = None
                st.session_state.sample_data = None
                st.rerun()
        
        st.markdown("---")
        
        # API Configuration
        st.markdown("### ⚙️ Settings")
        
        agent = RMDScreeningAgent()
        api_configured = agent.is_configured()
        
        if api_configured:
            st.success("✅ Groq API Connected")
            demo_mode = st.toggle("Use Demo Mode", value=False, 
                                 help="Run without API calls using rule-based analysis")
        else:
            st.warning("⚠️ No API Key")
            st.info("Get FREE key at [console.groq.com](https://console.groq.com)")
            demo_mode = True
        
        st.session_state.demo_mode = demo_mode
        
        if demo_mode:
            st.info("📋 Demo Mode: Using rule-based analysis")
        
        st.markdown("---")
        
        # Quick load samples
        st.markdown("### 📋 Sample Data")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 High Risk", use_container_width=True, help="Load high-risk patient example"):
                load_sample_data("high_risk")
        with col2:
            if st.button("🟢 Low Risk", use_container_width=True, help="Load low-risk patient example"):
                load_sample_data("low_risk")
        
        st.markdown("---")
        
        # About section
        st.markdown("### ℹ️ About")
        st.markdown("""
        **RMD-Health Screening Agent**
        
        Built for the University of Reading 
        AI Software Engineer role interview.
        
        *Demonstrating:*
        - Agentic AI (LangChain)
        - Explainable AI (XAI)
        - FHIR R4 Standards
        - NHS Digital Compliance
        
        ---
        
        *This is a prototype demonstration only.*
        """)


# =============================================================================
# SAMPLE DATA LOADER
# =============================================================================

def load_sample_data(risk_type: str):
    """Load sample patient data."""
    sample_file = Path("sample_data/example_patient.json")
    
    if sample_file.exists():
        with open(sample_file, "r") as f:
            data = json.load(f)
        if risk_type in data:
            st.session_state.sample_data = data[risk_type]
    else:
        # Fallback sample data
        if risk_type == "high_risk":
            st.session_state.sample_data = {
                "age": 52,
                "sex": "Female",
                "joint_pain": True,
                "joint_pain_severity": 8,
                "multiple_joints": True,
                "morning_stiffness": True,
                "morning_stiffness_duration": 75,
                "joint_swelling": True,
                "joint_redness": True,
                "fatigue": True,
                "fatigue_severity": 7,
                "fever": False,
                "weight_loss": False,
                "skin_rash": False,
                "medical_history": "Family history of RA (mother and aunt). Hypothyroidism diagnosed 2020."
            }
        else:
            st.session_state.sample_data = {
                "age": 32,
                "sex": "Male",
                "joint_pain": True,
                "joint_pain_severity": 3,
                "multiple_joints": False,
                "morning_stiffness": False,
                "morning_stiffness_duration": 5,
                "joint_swelling": False,
                "joint_redness": False,
                "fatigue": False,
                "fatigue_severity": 2,
                "fever": False,
                "weight_loss": False,
                "skin_rash": False,
                "medical_history": "Occasional knee pain after running. Active lifestyle, plays football weekly."
            }
    
    # Update widget keys directly from sample data
    sample = st.session_state.sample_data
    st.session_state.input_age = sample.get("age", 45)
    st.session_state.input_sex = sample.get("sex", "Female")
    st.session_state.input_joint_pain = sample.get("joint_pain", False)
    st.session_state.input_joint_pain_severity = sample.get("joint_pain_severity", 5)
    st.session_state.input_multiple_joints = sample.get("multiple_joints", False)
    st.session_state.input_morning_stiffness = sample.get("morning_stiffness", False)
    st.session_state.input_stiffness_duration = sample.get("morning_stiffness_duration", 30)
    st.session_state.input_joint_swelling = sample.get("joint_swelling", False)
    st.session_state.input_joint_redness = sample.get("joint_redness", False)
    st.session_state.input_fatigue = sample.get("fatigue", False)
    st.session_state.input_fatigue_severity = sample.get("fatigue_severity", 5)
    st.session_state.input_fever = sample.get("fever", False)
    st.session_state.input_weight_loss = sample.get("weight_loss", False)
    st.session_state.input_skin_rash = sample.get("skin_rash", False)
    st.session_state.input_medical_history = sample.get("medical_history", "")
    
    st.rerun()


def get_default_value(key: str, default):
    """Get value from sample data or return default."""
    if st.session_state.sample_data:
        return st.session_state.sample_data.get(key, default)
    return default


# =============================================================================
# COMPONENT: PATIENT SCREENING FORM  
# =============================================================================

def init_form_state():
    """Initialize form state for dynamic slider enabling."""
    if 'form_joint_pain' not in st.session_state:
        st.session_state.form_joint_pain = get_default_value("joint_pain", False)
    if 'form_morning_stiffness' not in st.session_state:
        st.session_state.form_morning_stiffness = get_default_value("morning_stiffness", False)
    if 'form_fatigue' not in st.session_state:
        st.session_state.form_fatigue = get_default_value("fatigue", False)


def create_screening_form() -> PatientScreening | None:
    """Create the patient screening form with dynamic slider enabling."""
    
    init_form_state()
    
    # Form header based on role
    role = st.session_state.user_role
    if role == UserRole.CLINICIAN:
        st.markdown("### 📋 Patient Symptom Assessment")
        st.markdown("Enter clinical findings for RMD risk screening:")
    elif role == UserRole.PATIENT:
        st.markdown("### 📝 Tell Us About Your Symptoms")
        st.markdown("Please answer these questions about how you've been feeling:")
    else:
        st.markdown("### 📊 Patient Data Input")
        st.markdown("Enter screening parameters for assessment:")
    
    # =========================================================================
    # DEMOGRAPHICS SECTION (Outside form for proper interaction)
    # =========================================================================
    st.markdown("#### Basic Information")
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.slider(
            "Age" if role != UserRole.PATIENT else "Your Age",
            min_value=18, max_value=100,
            value=get_default_value("age", 45),
            help="Age in years",
            key="input_age"
        )
    
    with col2:
        sex_label = "Sex" if role != UserRole.PATIENT else "Your Sex"
        sex = st.selectbox(
            sex_label,
            options=["Male", "Female", "Other", "Prefer not to say"],
            index=["Male", "Female", "Other", "Prefer not to say"].index(
                get_default_value("sex", "Female")
            ),
            key="input_sex"
        )
    
    st.markdown("---")
    
    # =========================================================================
    # JOINT SYMPTOMS - Dynamic checkboxes and sliders
    # =========================================================================
    st.markdown("#### 🦴 Joint Symptoms")
    
    col1, col2 = st.columns(2)
    with col1:
        joint_pain_label = "Joint Pain" if role != UserRole.PATIENT else "Do you have joint pain?"
        joint_pain = st.checkbox(
            joint_pain_label,
            value=get_default_value("joint_pain", False),
            key="input_joint_pain"
        )
    with col2:
        jp_severity_label = "Pain Severity (0-10)" if role != UserRole.PATIENT else "How bad is the pain? (0=none, 10=worst)"
        joint_pain_severity = st.slider(
            jp_severity_label,
            0, 10,
            value=get_default_value("joint_pain_severity", 5),
            disabled=not joint_pain,
            key="input_joint_pain_severity",
            help="Enable by checking 'Joint Pain'" if not joint_pain else "Rate your pain level"
        )
    
    multi_label = "Multiple Joints Affected (≥3)" if role != UserRole.PATIENT else "Is the pain in more than 2 joints?"
    multiple_joints = st.checkbox(
        multi_label,
        value=get_default_value("multiple_joints", False),
        key="input_multiple_joints"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        ms_label = "Morning Stiffness" if role != UserRole.PATIENT else "Are your joints stiff in the morning?"
        morning_stiffness = st.checkbox(
            ms_label,
            value=get_default_value("morning_stiffness", False),
            key="input_morning_stiffness"
        )
    with col2:
        msd_label = "Duration (minutes)" if role != UserRole.PATIENT else "How long does the stiffness last?"
        stiffness_duration = st.slider(
            msd_label,
            0, 120,
            value=get_default_value("morning_stiffness_duration", 30),
            disabled=not morning_stiffness,
            key="input_stiffness_duration",
            help="Enable by checking 'Morning Stiffness'" if not morning_stiffness else "Duration in minutes"
        )
    
    st.markdown("---")
    
    # =========================================================================
    # INFLAMMATORY SIGNS
    # =========================================================================
    st.markdown("#### 🔴 Signs of Inflammation")
    
    col1, col2 = st.columns(2)
    with col1:
        swelling_label = "Joint Swelling" if role != UserRole.PATIENT else "Are any joints swollen?"
        joint_swelling = st.checkbox(
            swelling_label,
            value=get_default_value("joint_swelling", False),
            key="input_joint_swelling"
        )
    with col2:
        redness_label = "Joint Redness/Warmth" if role != UserRole.PATIENT else "Are any joints red or warm?"
        joint_redness = st.checkbox(
            redness_label,
            value=get_default_value("joint_redness", False),
            key="input_joint_redness"
        )
    
    st.markdown("---")
    
    # =========================================================================
    # SYSTEMIC SYMPTOMS
    # =========================================================================
    st.markdown("#### 🌡️ Other Symptoms")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fatigue_label = "Fatigue" if role != UserRole.PATIENT else "Unusual tiredness?"
        fatigue = st.checkbox(
            fatigue_label,
            value=get_default_value("fatigue", False),
            key="input_fatigue"
        )
        fatigue_severity = st.slider(
            "Fatigue Level" if role != UserRole.PATIENT else "How tired?",
            0, 10,
            value=get_default_value("fatigue_severity", 5),
            disabled=not fatigue,
            key="input_fatigue_severity",
            help="Enable by checking 'Fatigue'" if not fatigue else "Rate your fatigue level"
        )
    
    with col2:
        fever_label = "Fever" if role != UserRole.PATIENT else "Have you had a fever?"
        fever = st.checkbox(
            fever_label,
            value=get_default_value("fever", False),
            key="input_fever"
        )
    
    with col3:
        wl_label = "Unexplained Weight Loss" if role != UserRole.PATIENT else "Lost weight without trying?"
        weight_loss = st.checkbox(
            wl_label,
            value=get_default_value("weight_loss", False),
            key="input_weight_loss"
        )
    
    rash_label = "Skin Rash" if role != UserRole.PATIENT else "Any skin rashes?"
    skin_rash = st.checkbox(
        rash_label,
        value=get_default_value("skin_rash", False),
        key="input_skin_rash"
    )
    
    st.markdown("---")
    
    # =========================================================================
    # MEDICAL HISTORY
    # =========================================================================
    st.markdown("#### 📋 Additional Information")
    
    history_placeholder = (
        "Family history, medications, previous diagnoses..." if role != UserRole.PATIENT
        else "Tell us about any family history of joint problems, medicines you take, or other health conditions..."
    )
    
    medical_history = st.text_area(
        "Medical History" if role != UserRole.PATIENT else "Anything else we should know?",
        value=get_default_value("medical_history", ""),
        height=100,
        placeholder=history_placeholder,
        key="input_medical_history"
    )
    
    st.markdown("---")
    
    # =========================================================================
    # SUBMIT BUTTON
    # =========================================================================
    button_label = {
        UserRole.CLINICIAN: "🔬 Run Clinical Assessment",
        UserRole.PATIENT: "🔍 Check My Symptoms",
        UserRole.AUDITOR: "📊 Generate Assessment"
    }
    
    submitted = st.button(
        button_label.get(role, "🔍 Run Assessment"),
        use_container_width=True,
        type="primary",
        key="submit_assessment"
    )
    
    if submitted:
        # Clear sample data
        st.session_state.sample_data = None
        
        # Build symptoms list
        symptoms = [
            Symptom(name="joint_pain", present=joint_pain, 
                   severity=joint_pain_severity if joint_pain else None),
            Symptom(name="multiple_joints_affected", present=multiple_joints),
            Symptom(name="morning_stiffness", present=morning_stiffness,
                   duration_minutes=stiffness_duration if morning_stiffness else None),
            Symptom(name="joint_swelling", present=joint_swelling),
            Symptom(name="joint_redness", present=joint_redness),
            Symptom(name="fatigue", present=fatigue,
                   severity=fatigue_severity if fatigue else None),
            Symptom(name="fever", present=fever),
            Symptom(name="weight_loss", present=weight_loss),
            Symptom(name="skin_rash", present=skin_rash),
        ]
        
        return PatientScreening(
            age=age,
            sex=sex,
            symptoms=symptoms,
            medical_history=medical_history if medical_history else None
        )
    
    return None


# =============================================================================
# COMPONENT: RESULTS DISPLAY
# =============================================================================

def display_results(
    patient: PatientScreening,
    assessment: RMDAssessment,
    xai_explanation: XAIExplanation
):
    """Display the assessment results with XAI explanations."""
    
    role = st.session_state.user_role
    
    st.markdown("---")
    
    # ==========================================================================
    # HEADER WITH RISK LEVEL
    # ==========================================================================
    
    risk_class = f"risk-{assessment.risk_level.lower()}"
    risk_icons = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}
    
    st.markdown(f"""
    <div style="text-align: center; padding: 24px;">
        <span class="risk-badge {risk_class}">
            {risk_icons[assessment.risk_level]} {assessment.risk_level} RISK
        </span>
        <p style="margin-top: 16px; color: #666; font-size: 14px;">
            Confidence: {assessment.confidence_score:.0%}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # KEY METRICS
    # ==========================================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Risk Level", assessment.risk_level)
    with col2:
        st.metric("Confidence", f"{assessment.confidence_score:.0%}")
    with col3:
        st.metric("Conditions", len(assessment.likely_conditions))
    with col4:
        st.metric("Red Flags", len(assessment.red_flags_identified))
    
    st.markdown("---")
    
    # ==========================================================================
    # ROLE-SPECIFIC EXPLANATION
    # ==========================================================================
    
    st.markdown("## 🔍 AI Explanation")
    
    # Create tabs for different views
    if role == UserRole.CLINICIAN:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Clinical Summary", 
            "📊 Feature Contributions", 
            "🧠 Agent Reasoning",
            "🏥 FHIR Resources"
        ])
    elif role == UserRole.PATIENT:
        tab1, tab2, tab3 = st.tabs([
            "📋 Your Results", 
            "❓ What This Means",
            "📞 Next Steps"
        ])
    else:  # Auditor
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Audit Log", 
            "📊 Decision Factors", 
            "🔄 Processing Trace",
            "📥 Export Data"
        ])
    
    # ==========================================================================
    # CLINICIAN VIEW
    # ==========================================================================
    
    if role == UserRole.CLINICIAN:
        with tab1:
            st.markdown(xai_explanation.clinician_summary)
        
        with tab2:
            st.markdown("### Feature Contributions to Risk Assessment")
            st.markdown("*How each factor influenced the AI's decision (LIME/SHAP-style)*")
            
            for contrib in xai_explanation.feature_contributions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    direction_icon = "↑" if contrib.contribution_direction == "increases_risk" else "↓"
                    color = "#ff4b2b" if contrib.contribution_direction == "increases_risk" else "#38ef7d"
                    
                    st.markdown(f"""
                    **{contrib.feature_name}** ({contrib.feature_value})
                    
                    {contrib.clinical_significance}
                    """)
                    
                    # Visual bar
                    bar_width = abs(contrib.contribution_score) * 200
                    st.markdown(f"""
                    <div style="background: #eee; border-radius: 4px; height: 20px; width: 200px;">
                        <div style="background: {color}; height: 20px; width: {bar_width}px; 
                                    border-radius: 4px;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("Contribution", f"{contrib.contribution_score:+.2f}")
                
                st.markdown("---")
            
            # Counterfactuals
            st.markdown("### 🔄 Counterfactual Explanations")
            st.markdown("*What would change the outcome?*")
            for cf in xai_explanation.counterfactuals:
                st.info(cf)
        
        with tab3:
            st.markdown("### Agent Reasoning Trace")
            st.markdown("*The AI agent's step-by-step clinical reasoning (ReAct pattern)*")
            
            for step in xai_explanation.reasoning_steps:
                with st.expander(f"Step {step.step_number}: {step.tool_used or 'Analysis'}", expanded=True):
                    st.markdown(f"**Thought:** {step.thought}")
                    if step.action:
                        st.markdown(f"**Action:** {step.action}")
                    if step.tool_used:
                        st.code(f"Tool: {step.tool_used}", language=None)
                    if step.observation:
                        st.markdown(f"**Observation:** {step.observation}")
                    st.caption(f"⏱️ {step.duration_ms}ms | {step.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
        
        with tab4:
            display_fhir_bundle(patient, assessment)
    
    # ==========================================================================
    # PATIENT VIEW
    # ==========================================================================
    
    elif role == UserRole.PATIENT:
        with tab1:
            st.markdown(xai_explanation.patient_summary)
        
        with tab2:
            st.markdown("### What We Looked At")
            st.markdown("Here's what the check considered when looking at your symptoms:")
            
            for i, contrib in enumerate(xai_explanation.feature_contributions[:5], 1):
                icon = "✓" if contrib.contribution_direction == "increases_risk" else "○"
                st.markdown(f"""
                <div class="info-box">
                    <strong>{i}. {contrib.feature_name}</strong><br>
                    {contrib.plain_language}
                </div>
                """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("### What Happens Next?")
            
            if assessment.risk_level == "HIGH":
                st.error(f"**Recommended:** {assessment.recommended_next_step}")
                st.markdown("""
                Your GP will likely refer you to a **rheumatologist** - a doctor who specializes 
                in joint and muscle conditions. They'll do more detailed tests to understand 
                exactly what's happening.
                
                **Don't worry** - getting seen by a specialist is a good thing! It means you'll 
                get the right care from experts.
                """)
            elif assessment.risk_level == "MODERATE":
                st.warning(f"**Recommended:** {assessment.recommended_next_step}")
                st.markdown("""
                Your GP can help investigate your symptoms further. They might:
                - Order some blood tests
                - Examine your joints
                - Discuss your symptoms in more detail
                
                It's always better to check these things early.
                """)
            else:
                st.success(f"**Recommended:** {assessment.recommended_next_step}")
                st.markdown("""
                Your symptoms don't suggest anything requiring urgent attention right now.
                
                However, please do speak to your GP if:
                - Your symptoms get worse
                - You develop new symptoms
                - The symptoms don't improve over time
                
                Looking after your joint health is important!
                """)
            
            st.markdown("---")
            st.markdown("### 📞 Helpful Resources")
            st.markdown("""
            - **NHS 111**: Call 111 for non-emergency medical advice
            - **Your GP**: Book an appointment through your usual GP surgery
            - **Versus Arthritis**: [versusarthritis.org](https://www.versusarthritis.org) - Information and support
            - **NRAS**: [nras.org.uk](https://www.nras.org.uk) - National Rheumatoid Arthritis Society
            """)
    
    # ==========================================================================
    # AUDITOR VIEW
    # ==========================================================================
    
    else:
        with tab1:
            st.markdown(xai_explanation.auditor_summary)
        
        with tab2:
            st.markdown("### Decision Factor Analysis")
            
            # Create a table of all factors
            factor_data = []
            for contrib in xai_explanation.feature_contributions:
                factor_data.append({
                    "Factor": contrib.feature_name,
                    "Value": contrib.feature_value,
                    "Contribution": f"{contrib.contribution_score:+.2f}",
                    "Direction": contrib.contribution_direction,
                    "Clinical Basis": contrib.clinical_significance
                })
            
            st.dataframe(factor_data, use_container_width=True)
            
            st.markdown("### Risk Score Composition")
            total_positive = sum(c.contribution_score for c in xai_explanation.feature_contributions 
                               if c.contribution_score > 0)
            total_negative = sum(c.contribution_score for c in xai_explanation.feature_contributions 
                               if c.contribution_score < 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Factors", f"+{total_positive:.2f}")
            with col2:
                st.metric("Protective Factors", f"{total_negative:.2f}")
            with col3:
                st.metric("Net Score", f"{total_positive + total_negative:.2f}")
        
        with tab3:
            st.markdown("### Processing Trace")
            
            for entry in xai_explanation.audit_trail:
                st.markdown(f"""
                `{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]}` | **{entry.event_type}** | 
                ID: `{entry.entry_id}` | Status: {entry.details.get('status', 'N/A')}
                """)
            
            st.markdown("---")
            
            st.markdown("### Reasoning Steps Detail")
            for step in xai_explanation.reasoning_steps:
                st.markdown(f"""
                **Step {step.step_number}** | `{step.timestamp.strftime('%H:%M:%S.%f')[:-3]}` | 
                Duration: {step.duration_ms}ms
                
                - Thought: {step.thought}
                - Tool: `{step.tool_used}`
                - Observation: {step.observation}
                """)
                st.markdown("---")
        
        with tab4:
            st.markdown("### Export Assessment Data")
            
            # Prepare export data
            export_data = {
                "assessment_id": xai_explanation.assessment_id,
                "generated_at": xai_explanation.generated_at.isoformat(),
                "risk_level": assessment.risk_level,
                "confidence_score": assessment.confidence_score,
                "likely_conditions": assessment.likely_conditions,
                "red_flags": assessment.red_flags_identified,
                "feature_contributions": [
                    {
                        "feature": c.feature_name,
                        "value": c.feature_value,
                        "contribution": c.contribution_score,
                        "direction": c.contribution_direction
                    }
                    for c in xai_explanation.feature_contributions
                ],
                "reasoning": assessment.reasoning,
                "audit_trail": [
                    {
                        "entry_id": e.entry_id,
                        "timestamp": e.timestamp.isoformat(),
                        "event_type": e.event_type
                    }
                    for e in xai_explanation.audit_trail
                ]
            }
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download Audit Log (JSON)",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"rmd_audit_{xai_explanation.assessment_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                st.download_button(
                    "📥 Download Audit Report (MD)",
                    data=xai_explanation.auditor_summary,
                    file_name=f"rmd_audit_report_{xai_explanation.assessment_id}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Display FHIR bundle for auditors too
            st.markdown("---")
            st.markdown("### FHIR R4 Bundle")
            display_fhir_bundle(patient, assessment)


# =============================================================================
# COMPONENT: FHIR BUNDLE DISPLAY
# =============================================================================

def display_fhir_bundle(patient: PatientScreening, assessment: RMDAssessment):
    """Display FHIR R4 bundle information."""
    
    # Create FHIR bundle
    symptoms_data = [
        {"name": s.name, "present": s.present, "severity": s.severity, 
         "duration_days": s.duration_days, "duration_minutes": s.duration_minutes}
        for s in patient.symptoms
    ]
    assessment_data = {
        "risk_level": assessment.risk_level,
        "likely_conditions": assessment.likely_conditions,
        "reasoning": assessment.reasoning,
        "recommended_next_step": assessment.recommended_next_step,
        "confidence_score": assessment.confidence_score,
        "red_flags_identified": assessment.red_flags_identified,
    }
    
    fhir_bundle = create_screening_bundle(
        patient_id=patient.patient_id,
        age=patient.age,
        sex=patient.sex,
        symptoms=symptoms_data,
        assessment=assessment_data
    )
    
    fhir_json = fhir_bundle.to_fhir_json()
    
    st.markdown("### 🏥 FHIR R4 Healthcare Data Bundle")
    st.markdown("*Standards-compliant healthcare interoperability format*")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bundle Type", fhir_json.get("type", "collection").title())
    with col2:
        st.metric("Resources", len(fhir_json.get("entry", [])))
    with col3:
        st.metric("Standard", "FHIR R4")
    
    for entry in fhir_json.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "Unknown")
        resource_id = resource.get("id", "")[:8]
        
        icons = {"Patient": "👤", "Observation": "🔬", "RiskAssessment": "⚠️"}
        
        with st.expander(f"{icons.get(resource_type, '📄')} {resource_type} ({resource_id}...)"):
            st.json(resource)
    
    st.download_button(
        "📥 Download FHIR Bundle (JSON)",
        data=json.dumps(fhir_json, indent=2, default=str),
        file_name="rmd_fhir_bundle.json",
        mime="application/fhir+json",
        use_container_width=True
    )


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    
    init_session_state()
    
    # If no role selected, show role selection
    if not st.session_state.user_role:
        show_role_selection()
        return
    
    # Create sidebar
    create_sidebar()
    
    # Main header
    role_titles = {
        UserRole.CLINICIAN: "Clinical Assessment Interface",
        UserRole.PATIENT: "Joint Health Checker",
        UserRole.AUDITOR: "Assessment Audit System"
    }
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 RMD-Health</h1>
        <p>{role_titles[st.session_state.user_role]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    show_disclaimer()
    
    # Check if we have a saved assessment (from role switch)
    if st.session_state.assessment_complete and st.session_state.current_assessment:
        st.info("📋 Viewing previous assessment result. Use sidebar to switch views or start a new assessment.")
        display_results(
            st.session_state.current_patient,
            st.session_state.current_assessment,
            st.session_state.xai_explanation
        )
        
        st.markdown("---")
        st.markdown("### 📝 Run New Assessment")
    
    # Show screening form
    patient = create_screening_form()
    
    # Process assessment if form submitted
    if patient is not None:
        with st.spinner("🔍 AI Agent analyzing symptoms..."):
            # Run assessment
            demo_mode = st.session_state.get('demo_mode', True)
            
            if demo_mode:
                assessment = demo_assessment(patient)
            else:
                agent = RMDScreeningAgent()
                assessment = agent.assess(patient)
            
            # Generate XAI explanation
            patient_data = {
                "age": patient.age,
                "sex": patient.sex,
                "symptoms": [
                    {"name": s.name, "present": s.present, "severity": s.severity, 
                     "duration_days": s.duration_days, "duration_minutes": s.duration_minutes}
                    for s in patient.symptoms
                ],
                "medical_history": patient.medical_history
            }
            
            # Extract tools used from reasoning
            tools_used = []
            if "[Agent used tools:" in assessment.reasoning:
                import re
                match = re.search(r'\[Agent used tools: ([^\]]+)\]', assessment.reasoning)
                if match:
                    tools_used = [t.strip() for t in match.group(1).split(',')]
            
            xai_explanation = generate_xai_explanation(
                assessment_id=f"RMD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}",
                patient_data=patient_data,
                risk_level=assessment.risk_level,
                confidence=assessment.confidence_score,
                likely_conditions=assessment.likely_conditions,
                recommended_action=assessment.recommended_next_step,
                red_flags=assessment.red_flags_identified,
                tools_used=tools_used
            )
            
            # Store in session state
            st.session_state.current_patient = patient
            st.session_state.current_assessment = assessment
            st.session_state.xai_explanation = xai_explanation
            st.session_state.assessment_complete = True
        
        # Display results
        display_results(patient, assessment, xai_explanation)


if __name__ == "__main__":
    main()
