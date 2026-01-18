"""
RMD-Health Multi-User Application
=================================

Streamlit application with authentication and role-based dashboards.

User Types:
- Patient: Can view own history, create new assessments
- Clinician: Can view all patients, access their assessments
- Auditor: Can view all audit logs and compliance data
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path

# Page config must be first
st.set_page_config(
    page_title="RMD-Health Screening",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports
from src.database import (
    authenticate_user, register_user, get_patient_profile,
    update_patient_profile, save_assessment, get_patient_assessments,
    get_all_patients, get_all_audit_logs, get_patient_audit_logs,
    get_assessment_by_id, export_to_csv
)
from src.data_models import PatientScreening, Symptom, RMDAssessment
from src.rmd_agent import RMDScreeningAgent, demo_assessment
from src.xai_explanations import generate_xai_explanation, XAIExplanation, UserRole
from src.fhir_resources import create_screening_bundle


# =============================================================================
# NHS GDPR COMPLIANCE HELPERS
# =============================================================================

def pseudonymize_id(user_id: int) -> str:
    """Generate a pseudonymized patient identifier for display.
    
    NHS GDPR Compliance: Patient identifiers should be pseudonymized
    when displayed to clinicians/auditors to minimize PII exposure.
    Real identity is only accessible through proper audit trails.
    """
    import hashlib
    hash_obj = hashlib.sha256(f"RMD-PATIENT-{user_id}".encode())
    return f"PT-{hash_obj.hexdigest()[:8].upper()}"


def get_privacy_display_name(user: dict, viewer_role: str) -> str:
    """Get appropriate display name based on viewer's role.
    
    NHS Caldicott Principles: Use minimum necessary identifiable information.
    - Patients see their own name
    - Clinicians see pseudonymized ID + initials only
    - Auditors see pseudonymized ID only
    """
    if viewer_role == 'patient':
        return user.get('name', 'Unknown')
    elif viewer_role == 'clinician':
        name = user.get('name', '')
        initials = ''.join(word[0].upper() for word in name.split() if word)
        return f"{pseudonymize_id(user['id'])} ({initials})"
    else:  # auditor
        return pseudonymize_id(user['id'])


def mask_email(email: str) -> str:
    """Mask email for privacy compliance."""
    if not email or '@' not in email:
        return "[REDACTED]"
    local, domain = email.split('@')
    return f"{local[:2]}***@{domain}"


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Main container */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Login card */
    .login-card {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* User type badges */
    .user-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .badge-patient { background: #11998e; color: white; }
    .badge-clinician { background: #667eea; color: white; }
    .badge-auditor { background: #eb3349; color: white; }
    
    /* Risk badges */
    .risk-high { background: #ff4b2b; color: white; padding: 4px 12px; border-radius: 20px; }
    .risk-moderate { background: #ffd200; color: #333; padding: 4px 12px; border-radius: 20px; }
    .risk-low { background: #38ef7d; color: white; padding: 4px 12px; border-radius: 20px; }
    
    /* Cards */
    .patient-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        border-left: 4px solid #667eea;
    }
    
    .audit-entry {
        background: #f8f9fa;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-family: monospace;
        font-size: 13px;
    }
    
    /* Disclaimer */
    .disclaimer {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================

def init_session():
    """Initialize session state."""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = None
    if 'selected_assessment' not in st.session_state:
        st.session_state.selected_assessment = None
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = True


# =============================================================================
# LOGIN PAGE
# =============================================================================

def show_login_page():
    """Display login/register page."""
    
    st.markdown("""
    <div class="main-header">
        <h1>🏥 RMD-Health</h1>
        <p>AI-Powered Rheumatoid Disease Screening</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown("### Welcome Back")
            
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary", use_container_width=True):
                user = authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            
            st.markdown("---")
            st.markdown("**Demo Accounts:**")
            st.code("""
Auditor:    auditor@rmd-health.demo / admin123
Clinician:  clinician@rmd-health.demo / clinician123
Patient 1:  patient1@rmd-health.demo / patient123
Patient 2:  patient2@rmd-health.demo / patient123
            """)
        
        with tab2:
            st.markdown("### Create Account")
            
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Register as Patient", type="primary", use_container_width=True):
                if not all([reg_name, reg_email, reg_password]):
                    st.error("Please fill all fields")
                elif reg_password != reg_confirm:
                    st.error("Passwords don't match")
                elif register_user(reg_email, reg_password, reg_name, "patient"):
                    st.success("Account created! Please login.")
                else:
                    st.error("Email already registered")


# =============================================================================
# PATIENT DASHBOARD
# =============================================================================

def show_patient_dashboard():
    """Dashboard for patients - view history, create assessments."""
    user = st.session_state.user
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 RMD-Health</h1>
        <p>Welcome, {user['name']} <span class="user-badge badge-patient">Patient</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.markdown(f"*{mask_email(user['email'])}*")
        st.markdown("---")
        
        # AI Mode Toggle
        st.markdown("#### 🤖 AI Mode")
        agent = RMDScreeningAgent()
        if agent.is_configured():
            demo_mode = st.toggle("Demo Mode", value=st.session_state.get('demo_mode', False),
                                  help="Toggle between Live AI (Groq LLM) and Demo Mode (rule-based)")
            st.session_state.demo_mode = demo_mode
            if demo_mode:
                st.caption("📴 Using rule-based demo")
            else:
                st.caption("🟢 Using Groq LLM (Agentic AI)")
        else:
            st.warning("⚠️ API not configured")
            st.caption("Set GROQ_API_KEY in .env")
            st.session_state.demo_mode = True
        
        st.markdown("---")
        
        page = st.radio("Navigation", [
            "📊 My Health Dashboard",
            "➕ New Assessment",
            "📋 My History",
            "⚙️ Settings"
        ])
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Main content
    if "Dashboard" in page:
        show_patient_home(user)
    elif "New Assessment" in page:
        show_patient_assessment_form(user)
    elif "History" in page:
        show_patient_history(user)
    elif "Settings" in page:
        show_patient_settings(user)


def show_patient_home(user):
    """Patient home/dashboard."""
    st.markdown("### 📊 Your Health Dashboard")
    
    # Get assessments
    assessments = get_patient_assessments(user['id'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Assessments", len(assessments))
    with col2:
        if assessments:
            last = assessments[0]
            st.metric("Last Risk Level", last['risk_level'])
        else:
            st.metric("Last Risk Level", "No assessments yet")
    with col3:
        high_risk_count = sum(1 for a in assessments if a['risk_level'] == 'HIGH')
        st.metric("High Risk Assessments", high_risk_count)
    
    st.markdown("---")
    
    # Recent assessments
    st.markdown("### 📋 Recent Results")
    
    if not assessments:
        st.info("You haven't completed any assessments yet. Click 'New Assessment' to start.")
    else:
        for assessment in assessments[:3]:
            risk_class = f"risk-{assessment['risk_level'].lower()}"
            st.markdown(f"""
            <div class="patient-card">
                <strong>Assessment #{assessment['assessment_number']}</strong> 
                <span class="{risk_class}">{assessment['risk_level']}</span>
                <br>
                <small>Date: {assessment['created_at']} | Confidence: {assessment['confidence_score']:.0%}</small>
            </div>
            """, unsafe_allow_html=True)


def load_sample_data(risk_type: str):
    """Load sample patient data into session state."""
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
    elif risk_type == "moderate_risk":
        st.session_state.sample_data = {
            "age": 45,
            "sex": "Male",
            "joint_pain": True,
            "joint_pain_severity": 5,
            "multiple_joints": True,
            "morning_stiffness": True,
            "morning_stiffness_duration": 35,
            "joint_swelling": True,
            "joint_redness": False,
            "fatigue": True,
            "fatigue_severity": 5,
            "fever": False,
            "weight_loss": False,
            "skin_rash": False,
            "medical_history": "Desk job, occasional sports. Father has osteoarthritis."
        }
    else:  # low_risk
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
    st.rerun()


def show_patient_assessment_form(user):
    """New assessment form for patients."""
    st.markdown("### ➕ New Symptom Assessment")
    
    # NHS CDSS Compliance Disclaimer
    st.markdown("""
    <div class="disclaimer" style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #856404; margin-top: 0;">⚠️ IMPORTANT CLINICAL DECISION SUPPORT DISCLAIMER</h4>
        <p style="color: #856404; margin-bottom: 10px;">
            <strong>This is a CLASS IIa MEDICAL DEVICE under UK MDR 2002 used for SCREENING ONLY.</strong>
        </p>
        <ul style="color: #856404; margin-bottom: 10px;">
            <li>This tool does <strong>NOT</strong> provide medical diagnosis</li>
            <li>Results are <strong>indicative only</strong> and require clinical validation</li>
            <li>Always consult a qualified healthcare professional</li>
            <li>If you experience severe symptoms, seek immediate medical attention</li>
        </ul>
        <p style="color: #856404; font-size: 12px; margin-bottom: 0;">
            <strong>NHS NICE Compliance:</strong> This CDSS follows NICE Evidence Standards Framework (ESF) for Digital Health Technologies.
            <br><strong>Data Protection:</strong> Your data is processed in accordance with UK GDPR and NHS Data Security Standards.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample data buttons
    st.markdown("#### 📋 Quick Fill Sample Data")
    st.caption("Use these to quickly fill the form with example patient data:")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("🔴 High Risk", help="52yo female with severe RA symptoms"):
            load_sample_data("high_risk")
    with col2:
        if st.button("🟡 Moderate Risk", help="45yo male with moderate symptoms"):
            load_sample_data("moderate_risk")
    with col3:
        if st.button("🟢 Low Risk", help="32yo male with mild symptoms"):
            load_sample_data("low_risk")
    with col4:
        if st.button("🗑️ Clear", help="Reset form to defaults"):
            st.session_state.sample_data = None
            st.rerun()
    
    st.markdown("---")
    
    # Get sample data if loaded
    sample = st.session_state.get('sample_data', None)
    
    # Helper function to get default values
    def get_val(key, profile_key=None, default=None):
        if sample and key in sample:
            return sample[key]
        if profile and profile_key and profile.get(profile_key):
            return profile[profile_key]
        return default
    
    # Get profile
    profile = get_patient_profile(user['id'])
    
    st.markdown("#### Basic Information")
    col1, col2 = st.columns(2)
    with col1:
        default_age = get_val('age', 'age', 45)
        age = st.slider("Your Age", 18, 100, default_age)
    with col2:
        default_sex = get_val('sex', 'sex', 'Female')
        sex_options = ["Male", "Female", "Other"]
        sex_idx = sex_options.index(default_sex) if default_sex in sex_options else 1
        sex = st.selectbox("Your Sex", sex_options, index=sex_idx)
    
    st.markdown("---")
    st.markdown("#### 🦴 Joint Symptoms")
    
    col1, col2 = st.columns(2)
    with col1:
        joint_pain = st.checkbox("Do you have joint pain?", value=get_val('joint_pain', None, False))
    with col2:
        joint_pain_severity = st.slider("How bad is the pain? (0-10)", 0, 10, 
                                        get_val('joint_pain_severity', None, 5), 
                                        disabled=not joint_pain)
    
    multiple_joints = st.checkbox("Is the pain in more than 2 joints?", value=get_val('multiple_joints', None, False))
    
    col1, col2 = st.columns(2)
    with col1:
        morning_stiffness = st.checkbox("Are your joints stiff in the morning?", value=get_val('morning_stiffness', None, False))
    with col2:
        stiffness_duration = st.slider("How long does stiffness last? (minutes)", 0, 120, 
                                       get_val('morning_stiffness_duration', None, 30),
                                       disabled=not morning_stiffness)
    
    st.markdown("---")
    st.markdown("#### 🔴 Signs of Inflammation")
    
    col1, col2 = st.columns(2)
    with col1:
        joint_swelling = st.checkbox("Are any joints swollen?", value=get_val('joint_swelling', None, False))
    with col2:
        joint_redness = st.checkbox("Are any joints red or warm?", value=get_val('joint_redness', None, False))
    
    st.markdown("---")
    st.markdown("#### 🌡️ Other Symptoms")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fatigue = st.checkbox("Unusual tiredness?", value=get_val('fatigue', None, False))
        fatigue_severity = st.slider("How tired? (0-10)", 0, 10, 
                                     get_val('fatigue_severity', None, 5), disabled=not fatigue)
    with col2:
        fever = st.checkbox("Have you had a fever?", value=get_val('fever', None, False))
    with col3:
        weight_loss = st.checkbox("Lost weight without trying?", value=get_val('weight_loss', None, False))
    
    skin_rash = st.checkbox("Any skin rashes?", value=get_val('skin_rash', None, False))
    
    st.markdown("---")
    default_history = get_val('medical_history', 'medical_history', '')
    medical_history = st.text_area("Anything else we should know?", 
                                   value=default_history,
                                   placeholder="Family history, medications, other conditions...")
    
    st.markdown("---")
    
    if st.button("🔍 Check My Symptoms", type="primary", use_container_width=True):
        # Clear sample data after submission
        st.session_state.sample_data = None
        
        # Build symptoms
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
        
        patient = PatientScreening(
            age=age, sex=sex, symptoms=symptoms, medical_history=medical_history
        )
        
        # Update profile
        update_patient_profile(user['id'], age, sex, medical_history)
        
        with st.spinner("🔍 AI Agent analyzing your symptoms..."):
            # Run assessment - Use REAL Agentic AI with Groq API if configured
            agent = RMDScreeningAgent()
            
            if agent.is_configured() and not st.session_state.get('demo_mode', False):
                # USE REAL GROQ API - LLM decides which tools to call
                assessment = agent.assess(patient)
                api_used = "Groq LLM (Agentic AI)"
            else:
                # Fallback to demo mode if API not configured
                assessment = demo_assessment(patient)
                api_used = "Demo Mode (Rule-based)"
            
            # Generate IDs
            assessment_id = f"RMD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
            
            # Generate XAI
            patient_data = {
                "age": age, "sex": sex,
                "symptoms": [{"name": s.name, "present": s.present, "severity": s.severity,
                             "duration_minutes": s.duration_minutes} for s in symptoms]
            }
            
            # Extract tools used from agent reasoning
            tools_used = ["analyze_inflammatory_markers", "analyze_joint_pattern", 
                         "analyze_systemic_symptoms", "calculate_risk_score", 
                         "get_differential_diagnosis"]
            if "[Agent used tools:" in assessment.reasoning:
                # Extract actual tools from reasoning
                import re
                match = re.search(r'\[Agent used tools: ([^\]]+)\]', assessment.reasoning)
                if match:
                    tools_used = [t.strip() for t in match.group(1).split(',')]
            
            xai = generate_xai_explanation(
                assessment_id=assessment_id,
                patient_data=patient_data,
                risk_level=assessment.risk_level,
                confidence=assessment.confidence_score,
                likely_conditions=assessment.likely_conditions,
                recommended_action=assessment.recommended_next_step,
                red_flags=assessment.red_flags_identified,
                tools_used=tools_used
            )
            
            # Create FHIR bundle
            symptoms_data = [{"name": s.name, "present": s.present, "severity": s.severity,
                             "duration_minutes": s.duration_minutes} for s in symptoms]
            fhir_bundle_obj = create_screening_bundle(
                patient.patient_id, patient.age, patient.sex, symptoms_data,
                {"risk_level": assessment.risk_level, "confidence_score": assessment.confidence_score,
                 "likely_conditions": assessment.likely_conditions}
            )
            fhir_bundle = fhir_bundle_obj.to_fhir_json()
            
            # Save to database
            save_assessment(
                patient_id=user['id'],
                assessment_id=assessment_id,
                symptoms=symptoms_data,
                risk_level=assessment.risk_level,
                confidence_score=assessment.confidence_score,
                likely_conditions=assessment.likely_conditions,
                red_flags=assessment.red_flags_identified,
                recommended_action=assessment.recommended_next_step,
                reasoning=assessment.reasoning,
                xai_explanation=xai.__dict__,
                fhir_bundle=fhir_bundle
            )
        
        # Show results
        st.success(f"Assessment complete! (Powered by: {api_used})")
        display_patient_results(assessment, xai, api_used)


def display_patient_results(assessment: RMDAssessment, xai: XAIExplanation, api_used: str = ""):
    """Display assessment results in patient-friendly format."""
    
    risk_colors = {"HIGH": "#ff4b2b", "MODERATE": "#ffd200", "LOW": "#38ef7d"}
    risk_icons = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}
    
    # Show AI mode indicator
    if api_used:
        if "Groq" in api_used:
            st.info(f"🤖 **AI Analysis:** This assessment was generated using **Agentic AI** (LangChain ReAct + Groq LLM)")
        else:
            st.info(f"📊 **Analysis Mode:** {api_used}")
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, 
                {risk_colors[assessment.risk_level]}33, white); border-radius: 15px; margin: 20px 0;">
        <h2>{risk_icons[assessment.risk_level]} {assessment.risk_level} RISK</h2>
        <p>Confidence: {assessment.confidence_score:.0%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 What This Means")
    st.markdown(xai.patient_summary)
    
    st.markdown("### 📞 Next Steps")
    if assessment.risk_level == "HIGH":
        st.error(f"**Recommended:** {assessment.recommended_next_step}")
        st.markdown("""
        Please speak to your GP soon. They may refer you to a rheumatologist.
        
        **NHS 111:** Call 111 for advice | **Your GP:** Book an appointment
        """)
    elif assessment.risk_level == "MODERATE":
        st.warning(f"**Recommended:** {assessment.recommended_next_step}")
    else:
        st.success(f"**Recommended:** {assessment.recommended_next_step}")


def show_patient_history(user):
    """Show patient's assessment history."""
    st.markdown("### 📋 My Assessment History")
    
    assessments = get_patient_assessments(user['id'])
    
    if not assessments:
        st.info("No assessments yet.")
        return
    
    for assessment in assessments:
        with st.expander(f"Assessment #{assessment['assessment_number']} - {assessment['risk_level']} Risk - {assessment['created_at'][:10]}"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Risk Level", assessment['risk_level'])
                st.metric("Confidence", f"{assessment['confidence_score']:.0%}")
            with col2:
                st.write("**Conditions Identified:**")
                for cond in assessment['likely_conditions']:
                    st.write(f"- {cond}")
            
            st.write("**Recommendation:**", assessment['recommended_action'])
            
            if assessment.get('xai_explanation'):
                st.markdown("---")
                st.markdown("**Explanation:**")
                xai = assessment['xai_explanation']
                if 'patient_summary' in xai:
                    st.markdown(xai['patient_summary'])


def show_patient_settings(user):
    """Patient settings page."""
    st.markdown("### ⚙️ Settings")
    
    profile = get_patient_profile(user['id'])
    
    st.markdown("#### Update Profile")
    age = st.number_input("Age", value=profile.get('age', 45) if profile else 45, min_value=18, max_value=100)
    sex = st.selectbox("Sex", ["Male", "Female", "Other"],
                      index=["Male", "Female", "Other"].index(profile.get('sex', 'Female') if profile else 'Female'))
    history = st.text_area("Medical History", value=profile.get('medical_history', '') if profile else '')
    
    if st.button("Save Changes"):
        update_patient_profile(user['id'], age, sex, history)
        st.success("Profile updated!")


# =============================================================================
# CLINICIAN DASHBOARD
# =============================================================================

def show_clinician_dashboard():
    """Dashboard for clinicians - view all patients."""
    user = st.session_state.user
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 RMD-Health</h1>
        <p>Welcome, {user['name']} <span class="user-badge badge-clinician">Clinician</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👨‍⚕️ {user['name']}")
        st.markdown("---")
        
        if st.session_state.selected_patient:
            if st.button("← Back to Patient List"):
                st.session_state.selected_patient = None
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Main content
    if st.session_state.selected_patient:
        show_clinician_patient_view()
    else:
        show_clinician_patient_list()


def show_clinician_patient_list():
    """Show list of all patients."""
    st.markdown("### 👥 Patient Directory")
    
    patients = get_all_patients()
    
    if not patients:
        st.info("No patients registered yet.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", len(patients))
    with col2:
        high_risk = sum(1 for p in patients if p.get('last_risk_level') == 'HIGH')
        st.metric("High Risk Patients", high_risk)
    with col3:
        total_assessments = sum(p.get('assessment_count') or 0 for p in patients)
        st.metric("Total Assessments", total_assessments)
    
    st.markdown("---")
    
    # Privacy notice for clinicians
    st.info("🔒 **NHS GDPR Compliance**: Patient names are pseudonymized. Full identity available only through authorized audit request.")
    
    # Patient list
    for patient in patients:
        risk = patient.get('last_risk_level')
        risk_display = risk if risk else 'N/A'
        risk_class = f"risk-{risk.lower()}" if risk else ""
        
        # Pseudonymized display for clinician view
        display_name = get_privacy_display_name(patient, 'clinician')
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"**{display_name}**")
            st.caption(f"Ref: {pseudonymize_id(patient['id'])}")
        with col2:
            # Age bands instead of exact age for additional privacy
            age = patient.get('age')
            age_band = "N/A"
            if age:
                if age < 30: age_band = "18-29"
                elif age < 45: age_band = "30-44"
                elif age < 60: age_band = "45-59"
                elif age < 75: age_band = "60-74"
                else: age_band = "75+"
            sex = patient.get('sex') or 'N/A'
            st.write(f"Age Band: {age_band} | Sex: {sex}")
        with col3:
            st.write(f"Assessments: {patient.get('assessment_count') or 0}")
            if risk:
                st.markdown(f"<span class='{risk_class}'>{risk_display}</span>", unsafe_allow_html=True)
            else:
                st.caption("No assessments yet")
        with col4:
            if st.button("View", key=f"view_{patient['id']}"):
                st.session_state.selected_patient = patient['id']
                st.rerun()
        
        st.markdown("---")


def show_clinician_patient_view():
    """Detailed view of a patient for clinician."""
    patient_id = st.session_state.selected_patient
    
    # Get patient info
    patients = get_all_patients()
    patient = next((p for p in patients if p['id'] == patient_id), None)
    
    if not patient:
        st.error("Patient not found")
        return
    
    # Pseudonymized display for clinician view
    display_name = get_privacy_display_name(patient, 'clinician')
    
    st.markdown(f"### 📋 Patient: {display_name}")
    st.caption("🔒 NHS GDPR: Pseudonymized identifier shown. Access full identity via audit request.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Patient Ref", pseudonymize_id(patient['id']))
    with col2:
        # Show exact age to clinician for clinical relevance
        st.metric("Age", patient.get('age', 'N/A'))
    with col3:
        st.metric("Sex", patient.get('sex', 'N/A'))
    with col4:
        st.metric("Total Assessments", patient.get('assessment_count', 0))
    
    st.markdown("---")
    
    # Get assessments
    assessments = get_patient_assessments(patient_id)
    
    if not assessments:
        st.info("No assessments for this patient.")
        return
    
    for assessment in assessments:
        with st.expander(f"Assessment #{assessment['assessment_number']} - {assessment['risk_level']} - {assessment['created_at'][:10]}", expanded=True):
            
            # Clinical summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Risk Level", assessment['risk_level'])
                st.metric("Confidence", f"{assessment['confidence_score']:.0%}")
                
                st.markdown("**Red Flags:**")
                for flag in assessment['red_flags']:
                    st.markdown(f"- 🚩 {flag}")
            
            with col2:
                st.markdown("**Likely Conditions:**")
                for cond in assessment['likely_conditions']:
                    st.markdown(f"- {cond}")
                
                st.markdown(f"**Recommendation:** {assessment['recommended_action']}")
            
            # XAI Explanation (Clinician view)
            if assessment.get('xai_explanation'):
                st.markdown("---")
                st.markdown("#### Clinical AI Explanation")
                
                xai = assessment['xai_explanation']
                
                if 'clinician_summary' in xai:
                    st.markdown(xai['clinician_summary'])
                
                # Feature contributions
                if 'feature_contributions' in xai:
                    st.markdown("**Feature Contributions:**")
                    for fc in xai['feature_contributions']:
                        if isinstance(fc, dict):
                            direction = "↑" if fc.get('contribution_direction') == 'increases_risk' else "↓"
                            st.markdown(f"- {fc.get('feature_name')}: {fc.get('contribution_score', 0):+.2f} {direction}")
            
            # FHIR Bundle
            if assessment.get('fhir_bundle'):
                with st.expander("📦 FHIR R4 Bundle"):
                    st.json(assessment['fhir_bundle'])


# =============================================================================
# AUDITOR DASHBOARD
# =============================================================================

def show_auditor_dashboard():
    """Dashboard for auditors - view all audit logs."""
    user = st.session_state.user
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 RMD-Health</h1>
        <p>Welcome, {user['name']} <span class="user-badge badge-auditor">Auditor</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 📋 {user['name']}")
        st.markdown("*Regulatory Auditor*")
        st.markdown("---")
        
        page = st.radio("Audit View", [
            "📊 Overview",
            "📋 All Audit Logs",
            "👥 By Patient",
            "📥 Export Data"
        ])
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    if "Overview" in page:
        show_auditor_overview()
    elif "All Audit" in page:
        show_all_audit_logs()
    elif "By Patient" in page:
        show_auditor_by_patient()
    elif "Export" in page:
        show_export_page()


def show_auditor_overview():
    """Auditor overview dashboard."""
    st.markdown("### 📊 Audit Overview")
    
    logs = get_all_audit_logs()
    patients = get_all_patients()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Audit Entries", len(logs))
    with col2:
        st.metric("Total Patients", len(patients))
    with col3:
        total_assessments = sum(p.get('assessment_count', 0) for p in patients)
        st.metric("Total Assessments", total_assessments)
    with col4:
        high_risk = sum(1 for p in patients if p.get('last_risk_level') == 'HIGH')
        st.metric("High Risk Cases", high_risk)
    
    st.markdown("---")
    st.markdown("### 📋 Recent Audit Activity")
    st.caption("🔒 NHS GDPR: Patient identities pseudonymized. Full PII access requires authorized audit request.")
    
    for log in logs[:10]:
        patient_ref = pseudonymize_id(log['patient_id'])
        st.markdown(f"""
        <div class="audit-entry">
            <strong>{log['timestamp']}</strong> | {log['event_type']} | 
            Patient Ref: {patient_ref} | Assessment: {log['assessment_id'][:20]}...
            <br>Hash: <code>{log.get('entry_hash', 'N/A')}</code>
        </div>
        """, unsafe_allow_html=True)


def show_all_audit_logs():
    """Show all audit logs."""
    st.markdown("### 📋 Complete Audit Trail")
    st.caption("🔒 NHS GDPR Compliance: Patient identities are pseudonymized to protect PII.")
    
    logs = get_all_audit_logs()
    
    # Filter
    event_types = list(set(log['event_type'] for log in logs))
    selected_type = st.selectbox("Filter by Event Type", ["All"] + event_types)
    
    if selected_type != "All":
        logs = [l for l in logs if l['event_type'] == selected_type]
    
    st.markdown(f"**Showing {len(logs)} entries**")
    
    for log in logs:
        patient_ref = pseudonymize_id(log['patient_id'])
        with st.expander(f"{log['timestamp']} - {log['event_type']} - {patient_ref}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Entry ID:** {log['id']}")
                st.write(f"**Assessment ID:** {log['assessment_id']}")
                st.write(f"**Patient Ref:** {patient_ref}")
            with col2:
                st.write(f"**Timestamp:** {log['timestamp']}")
                st.write(f"**Event Type:** {log['event_type']}")
                st.write(f"**Hash:** `{log.get('entry_hash', 'N/A')}`")
            
            if log.get('details'):
                st.markdown("**Details:**")
                st.json(log['details'])


def show_auditor_by_patient():
    """Show audit logs grouped by patient."""
    st.markdown("### 👥 Audit by Patient")
    st.caption("🔐 NHS GDPR: Select patient using pseudonymized reference.")
    
    patients = get_all_patients()
    
    # Show pseudonymized options instead of names
    patient_options = [(p['id'], f"{pseudonymize_id(p['id'])}") for p in patients]
    
    selected_patient = st.selectbox(
        "Select Patient Reference",
        options=patient_options,
        format_func=lambda x: x[1]
    )
    
    if selected_patient:
        patient_id = selected_patient[0]
        patient_ref = pseudonymize_id(patient_id)
        
        # Get patient's audit logs
        logs = get_patient_audit_logs(patient_id)
        assessments = get_patient_assessments(patient_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Audit Entries", len(logs))
        with col2:
            st.metric("Assessments", len(assessments))
        
        st.markdown("---")
        st.markdown(f"### 📋 Audit Trail for {patient_ref}")
        
        for log in logs:
            st.markdown(f"""
            <div class="audit-entry">
                {log['timestamp']} | <strong>{log['event_type']}</strong> | 
                Assessment: {log['assessment_id'][:20]}... | Hash: <code>{log.get('entry_hash', 'N/A')}</code>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 Assessment Details")
        
        for assessment in assessments:
            with st.expander(f"Assessment #{assessment['assessment_number']} - {assessment['risk_level']}"):
                st.write(f"**Assessment ID:** {assessment['assessment_id']}")
                st.write(f"**Created:** {assessment['created_at']}")
                st.write(f"**Risk Level:** {assessment['risk_level']}")
                st.write(f"**Confidence:** {assessment['confidence_score']:.0%}")
                
                st.markdown("**Symptoms:**")
                st.json(assessment['symptoms'])
                
                if assessment.get('xai_explanation'):
                    st.markdown("**XAI Explanation:**")
                    st.markdown(assessment['xai_explanation'].get('auditor_summary', 'N/A'))
                
                if assessment.get('fhir_bundle'):
                    st.markdown("**FHIR Bundle:**")
                    st.json(assessment['fhir_bundle'])


def show_export_page():
    """Export data page."""
    st.markdown("### 📥 Export Data")
    
    st.markdown("""
    Export all data to CSV files for external analysis and compliance review.
    
    **Available Exports:**
    - `users.csv` - User accounts (no passwords)
    - `assessments.csv` - All assessment records
    - `audit_logs.csv` - Complete audit trail
    """)
    
    if st.button("📥 Generate CSV Export", type="primary"):
        export_dir = export_to_csv()
        st.success(f"Data exported to: `{export_dir}`")
        
        # Show download buttons
        import os
        for file in os.listdir(export_dir):
            if file.endswith('.csv'):
                with open(export_dir / file, 'r') as f:
                    st.download_button(
                        f"Download {file}",
                        f.read(),
                        file_name=file,
                        mime="text/csv"
                    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application entry point."""
    init_session()
    
    if st.session_state.user is None:
        show_login_page()
    else:
        user_type = st.session_state.user['user_type']
        
        if user_type == 'patient':
            show_patient_dashboard()
        elif user_type == 'clinician':
            show_clinician_dashboard()
        elif user_type == 'auditor':
            show_auditor_dashboard()


if __name__ == "__main__":
    main()
