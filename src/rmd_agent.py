"""
RMD-Health Screening Agent - LangChain Agentic AI
==================================================

This module implements a proper LangChain ReAct agent for RMD screening.
The LLM autonomously decides which tools to use based on the patient data,
following modern agent architecture patterns.

Key Features:
1. ReAct Agent Pattern - LLM reasons about which tools to use
2. Tool-based Architecture - Modular, extensible tool system
3. Free LLM Integration - Uses Groq (free tier) for inference
4. FHIR Compliance - Outputs proper FHIR resources

The agent workflow:
1. Receive patient data
2. LLM DECIDES which tools to call (not hardcoded!)
3. Execute selected tools
4. LLM synthesizes findings into assessment
5. Return structured FHIR-compliant results
"""

import os
import json
from datetime import datetime
from typing import Optional, Any
from dotenv import load_dotenv

# LangChain imports
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

from src.data_models import PatientScreening, RMDAssessment
from src.fhir_resources import (
    FHIRBundle, create_screening_bundle
)

# Load environment variables
load_dotenv()


# =============================================================================
# TOOL DEFINITIONS - The LLM will decide which tools to use!
# =============================================================================

@tool
def analyze_inflammatory_markers(patient_data: str) -> str:
    """
    Analyze inflammatory markers and signs in the patient data.
    Use this tool when you need to assess inflammatory indicators like
    joint swelling, redness, morning stiffness, and fever.
    
    Args:
        patient_data: JSON string of patient symptoms
    
    Returns:
        Analysis of inflammatory markers present
    """
    try:
        data = json.loads(patient_data) if isinstance(patient_data, str) else patient_data
    except:
        return "Error: Could not parse patient data"
    
    symptoms = data.get("symptoms", [])
    findings = []
    red_flags = []
    
    # Check inflammatory signs
    for symptom in symptoms:
        name = symptom.get("name", "")
        present = symptom.get("present", False)
        severity = symptom.get("severity")
        duration_minutes = symptom.get("duration_minutes")  # For morning stiffness
        
        if not present:
            continue
            
        if name == "joint_swelling":
            findings.append("🔴 Joint swelling present - indicates active inflammation")
            red_flags.append("Joint swelling")
            
        if name == "joint_redness":
            findings.append("🔴 Joint redness/warmth - suggests acute inflammatory process")
            red_flags.append("Joint redness")
            
        if name == "morning_stiffness":
            if duration_minutes and duration_minutes > 30:
                findings.append(f"⚠️ Morning stiffness for {duration_minutes} minutes - >30min suggests inflammatory arthritis")
                red_flags.append("Prolonged morning stiffness")
            elif severity and severity >= 5:
                findings.append(f"⚠️ Morning stiffness severity {severity}/10 - moderate to severe")
            else:
                findings.append("Morning stiffness present - mild")
                
        if name == "fever":
            findings.append("🔴 Fever present - systemic inflammatory response")
            red_flags.append("Fever with joint symptoms")
    
    if not findings:
        return "No significant inflammatory markers identified."
    
    result = "INFLAMMATORY MARKER ANALYSIS:\n" + "\n".join(findings)
    if red_flags:
        result += "\n\nRED FLAGS: " + ", ".join(red_flags)
    
    return result


@tool
def analyze_joint_pattern(patient_data: str) -> str:
    """
    Analyze the pattern of joint involvement to help identify likely conditions.
    Use this tool to assess polyarticular involvement, symmetry, and specific
    joint patterns that suggest particular RMD conditions.
    
    Args:
        patient_data: JSON string of patient symptoms and age
    
    Returns:
        Analysis of joint involvement pattern
    """
    try:
        data = json.loads(patient_data) if isinstance(patient_data, str) else patient_data
    except:
        return "Error: Could not parse patient data"
    
    symptoms = data.get("symptoms", [])
    age = data.get("age", 0)
    findings = []
    
    # Check for polyarticular involvement
    multiple_joints = False
    joint_pain = False
    
    for symptom in symptoms:
        name = symptom.get("name", "")
        present = symptom.get("present", False)
        
        if name == "multiple_joints_affected" and present:
            multiple_joints = True
        if name == "joint_pain" and present:
            joint_pain = True
    
    if multiple_joints:
        findings.append("🔴 POLYARTICULAR: Multiple joints (≥3) affected")
        findings.append("   → Consider: RA, PsA, viral arthritis, OA (generalized)")
    elif joint_pain:
        findings.append("MONOARTICULAR/OLIGOARTICULAR: Limited joint involvement")
        findings.append("   → Consider: Gout, septic arthritis, OA, trauma")
    
    # Age-related patterns
    if age < 40 and joint_pain:
        findings.append(f"YOUNG ADULT ({age}y): Consider inflammatory spondyloarthropathy, RA, reactive arthritis")
    elif age >= 50:
        findings.append(f"OLDER ADULT ({age}y): Consider late-onset RA, OA, PMR, crystal arthropathy")
    
    if not findings:
        return "Unable to determine joint pattern from available data."
    
    return "JOINT PATTERN ANALYSIS:\n" + "\n".join(findings)


@tool  
def analyze_systemic_symptoms(patient_data: str) -> str:
    """
    Analyze systemic symptoms that may indicate systemic inflammatory disease.
    Use this tool to assess fatigue, weight loss, fever, and skin involvement
    that suggests conditions like RA, SLE, or PMR.
    
    Args:
        patient_data: JSON string of patient symptoms
    
    Returns:
        Analysis of systemic symptoms
    """
    try:
        data = json.loads(patient_data) if isinstance(patient_data, str) else patient_data
    except:
        return "Error: Could not parse patient data"
    
    symptoms = data.get("symptoms", [])
    age = data.get("age", 0)
    findings = []
    systemic_count = 0
    
    for symptom in symptoms:
        name = symptom.get("name", "")
        present = symptom.get("present", False)
        severity = symptom.get("severity")
        
        if not present:
            continue
            
        if name == "fatigue":
            systemic_count += 1
            sev_text = f" (severity {severity}/10)" if severity else ""
            findings.append(f"⚡ Fatigue present{sev_text}")
            
        if name == "weight_loss":
            systemic_count += 1
            findings.append("📉 Unexplained weight loss - concerning for systemic disease")
            
        if name == "fever":
            systemic_count += 1
            findings.append("🌡️ Fever - systemic inflammatory response")
            
        if name == "skin_rash":
            systemic_count += 1
            findings.append("🔵 Skin rash - consider PsA, SLE, dermatomyositis")
    
    if systemic_count >= 2:
        findings.append(f"\n⚠️ MULTIPLE SYSTEMIC SYMPTOMS ({systemic_count}): High concern for systemic inflammatory disease")
        if age >= 50:
            findings.append("   → Strongly consider PMR in older adult with these symptoms")
    
    if not findings:
        return "No significant systemic symptoms identified."
    
    return "SYSTEMIC SYMPTOM ANALYSIS:\n" + "\n".join(findings)


@tool
def calculate_risk_score(patient_data: str) -> str:
    """
    Calculate a quantitative risk score based on all symptoms and findings.
    Use this tool to get a numerical assessment of RMD risk based on
    clinical criteria and red flags.
    
    Args:
        patient_data: JSON string of patient symptoms
    
    Returns:
        Risk score calculation and risk level
    """
    try:
        data = json.loads(patient_data) if isinstance(patient_data, str) else patient_data
    except:
        return "Error: Could not parse patient data"
    
    symptoms = data.get("symptoms", [])
    score = 0
    factors = []
    
    for symptom in symptoms:
        name = symptom.get("name", "")
        present = symptom.get("present", False)
        severity = symptom.get("severity")
        duration_minutes = symptom.get("duration_minutes")  # For morning stiffness
        
        if not present:
            continue
        
        if name == "joint_pain":
            score += 1
            if severity and severity >= 7:
                score += 1
                factors.append(f"Severe joint pain ({severity}/10): +2")
            else:
                factors.append("Joint pain: +1")
                
        if name == "multiple_joints_affected":
            score += 3
            factors.append("Polyarticular involvement: +3")
            
        if name == "morning_stiffness":
            if duration_minutes and duration_minutes > 60:
                score += 4
                factors.append(f"Prolonged morning stiffness ({duration_minutes} min): +4")
            elif duration_minutes and duration_minutes > 30:
                score += 2
                factors.append(f"Morning stiffness ({duration_minutes} min): +2")
            else:
                score += 1
                factors.append("Morning stiffness: +1")
                
        if name == "joint_swelling":
            score += 2
            factors.append("Joint swelling: +2")
            
        if name == "joint_redness":
            score += 2
            factors.append("Joint redness: +2")
            
        if name == "fever":
            score += 2
            factors.append("Fever: +2")
            
        if name == "weight_loss":
            score += 1
            factors.append("Weight loss: +1")
            
        if name == "fatigue":
            score += 1
            factors.append("Fatigue: +1")
            
        if name == "skin_rash":
            score += 2
            factors.append("Skin rash: +2")
    
    # Determine risk level
    if score >= 8:
        risk_level = "HIGH"
        interpretation = "Urgent rheumatology referral recommended"
    elif score >= 4:
        risk_level = "MODERATE"
        interpretation = "GP consultation recommended for further evaluation"
    else:
        risk_level = "LOW"
        interpretation = "Continue monitoring, reassess if symptoms persist"
    
    result = f"""RISK SCORE CALCULATION:
Score Factors:
{chr(10).join('  • ' + f for f in factors) if factors else '  No risk factors identified'}

TOTAL SCORE: {score}/20
RISK LEVEL: {risk_level}
INTERPRETATION: {interpretation}
"""
    
    return result


@tool
def get_differential_diagnosis(patient_data: str) -> str:
    """
    Generate a differential diagnosis list based on the symptom pattern.
    Use this tool to identify the most likely RMD conditions given
    the patient's presentation.
    
    Args:
        patient_data: JSON string of patient symptoms and demographics
    
    Returns:
        Ranked list of differential diagnoses with reasoning
    """
    try:
        data = json.loads(patient_data) if isinstance(patient_data, str) else patient_data
    except:
        return "Error: Could not parse patient data"
    
    symptoms = data.get("symptoms", [])
    age = data.get("age", 0)
    sex = data.get("sex", "Unknown")
    
    # Build symptom set
    symptom_set = set()
    for symptom in symptoms:
        if symptom.get("present", False):
            symptom_set.add(symptom.get("name", ""))
    
    differentials = []
    
    # Rheumatoid Arthritis
    ra_score = 0
    if "multiple_joints_affected" in symptom_set:
        ra_score += 3
    if "morning_stiffness" in symptom_set:
        ra_score += 2
    if "joint_swelling" in symptom_set:
        ra_score += 2
    if "fatigue" in symptom_set:
        ra_score += 1
    if sex == "Female":
        ra_score += 1
    if ra_score >= 4:
        differentials.append((ra_score, "Rheumatoid Arthritis", "Polyarticular, inflammatory pattern, morning stiffness"))
    
    # Osteoarthritis
    oa_score = 0
    if "joint_pain" in symptom_set and "multiple_joints_affected" not in symptom_set:
        oa_score += 2
    if age >= 50:
        oa_score += 2
    if "morning_stiffness" not in symptom_set:
        oa_score += 1
    if oa_score >= 3:
        differentials.append((oa_score, "Osteoarthritis", "Mechanical pain pattern, age-related"))
    
    # Psoriatic Arthritis
    psa_score = 0
    if "skin_rash" in symptom_set:
        psa_score += 4
    if "joint_swelling" in symptom_set:
        psa_score += 2
    if "joint_pain" in symptom_set:
        psa_score += 1
    if psa_score >= 4:
        differentials.append((psa_score, "Psoriatic Arthritis", "Skin involvement with joint symptoms"))
    
    # Polymyalgia Rheumatica
    pmr_score = 0
    if age >= 50:
        pmr_score += 3
    if "morning_stiffness" in symptom_set:
        pmr_score += 2
    if "fatigue" in symptom_set:
        pmr_score += 1
    if pmr_score >= 4:
        differentials.append((pmr_score, "Polymyalgia Rheumatica", "Older adult with stiffness and fatigue"))
    
    # Gout
    gout_score = 0
    if "joint_redness" in symptom_set:
        gout_score += 3
    if "joint_swelling" in symptom_set:
        gout_score += 2
    if sex == "Male":
        gout_score += 1
    if gout_score >= 4:
        differentials.append((gout_score, "Gout", "Acute inflammatory presentation"))
    
    # SLE
    sle_score = 0
    if "skin_rash" in symptom_set:
        sle_score += 2
    if "fatigue" in symptom_set:
        sle_score += 2
    if "joint_pain" in symptom_set:
        sle_score += 1
    if sex == "Female" and age < 50:
        sle_score += 2
    if sle_score >= 4:
        differentials.append((sle_score, "Systemic Lupus Erythematosus", "Multisystem involvement, typical demographics"))
    
    # Sort by score
    differentials.sort(reverse=True, key=lambda x: x[0])
    
    if not differentials:
        return "DIFFERENTIAL DIAGNOSIS: Insufficient symptoms to suggest specific RMD conditions. Consider non-inflammatory causes."
    
    result = "DIFFERENTIAL DIAGNOSIS (ranked by likelihood):\n"
    for i, (score, condition, rationale) in enumerate(differentials[:4], 1):
        result += f"\n{i}. {condition}\n   Rationale: {rationale}\n"
    
    return result


# =============================================================================
# AGENT CLASS
# =============================================================================

class RMDScreeningAgent:
    """
    LangChain-based Agentic AI for RMD risk screening.
    
    This agent uses the ReAct pattern where the LLM autonomously decides
    which tools to call based on the patient data, rather than following
    a fixed sequence.
    
    Features:
    - LLM-driven tool selection (true agent behavior!)
    - Free API via Groq
    - FHIR-compliant outputs
    - Explainable decision-making
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with API credentials."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Define available tools
        self.tools = [
            analyze_inflammatory_markers,
            analyze_joint_pattern,
            analyze_systemic_symptoms,
            calculate_risk_score,
            get_differential_diagnosis,
        ]
        
        # Initialize LLM if configured
        self.llm = None
        self.agent = None
        if self.is_configured():
            self._setup_agent()
    
    def _setup_agent(self):
        """Set up the LangGraph ReAct agent with tools."""
        self.llm = ChatGroq(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.3,
            max_tokens=2000,
        )
        
        # Create ReAct agent using langgraph - LLM decides which tools to use!
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )
    
    def _get_agent_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an AI clinical decision support agent specialized in early detection of Rheumatic and Musculoskeletal Diseases (RMDs).

## YOUR TASK
Analyze patient symptom data and provide a structured RMD risk assessment. You have access to specialized analysis tools - USE THEM to gather information before making your final assessment.

## AVAILABLE TOOLS
- analyze_inflammatory_markers: Check for inflammatory signs (swelling, redness, stiffness)
- analyze_joint_pattern: Assess joint involvement patterns
- analyze_systemic_symptoms: Evaluate systemic symptoms (fatigue, fever, weight loss)
- calculate_risk_score: Get quantitative risk scoring
- get_differential_diagnosis: Generate differential diagnosis list

## WORKFLOW
1. First, call the appropriate tools based on what symptoms are present
2. Use at least 2-3 tools to gather comprehensive analysis
3. Synthesize all tool outputs into your final assessment
4. Provide your response as a JSON object

## IMPORTANT
- You are a DEMONSTRATION PROTOTYPE - not for real clinical use
- Always err on the side of caution for patient safety
- Be thorough in your reasoning

## REQUIRED OUTPUT FORMAT
After using tools, provide your final answer as valid JSON:
```json
{
    "risk_level": "LOW" | "MODERATE" | "HIGH",
    "likely_conditions": ["condition1", "condition2"],
    "reasoning": "Your detailed clinical reasoning...",
    "recommended_next_step": "Specific recommendation...",
    "confidence_score": 0.0 to 1.0,
    "red_flags_identified": ["flag1", "flag2"],
    "tools_used": ["tool1", "tool2"]
}
```
"""
    
    def is_configured(self) -> bool:
        """Check if the agent is properly configured with API key."""
        return self.api_key is not None and len(self.api_key) > 10
    
    def _prepare_patient_json(self, patient: PatientScreening) -> str:
        """Convert patient data to JSON for tool input."""
        symptoms_data = []
        for symptom in patient.symptoms:
            symptoms_data.append({
                "name": symptom.name,
                "present": symptom.present,
                "severity": symptom.severity,
                "duration_days": symptom.duration_days,
                "duration_minutes": symptom.duration_minutes,
            })
        
        return json.dumps({
            "patient_id": patient.patient_id,
            "age": patient.age,
            "sex": patient.sex,
            "symptoms": symptoms_data,
            "medical_history": patient.medical_history,
        })
    
    def assess(self, patient: PatientScreening) -> RMDAssessment:
        """
        Perform RMD risk assessment using the LangGraph ReAct agent.
        
        The agent will autonomously decide which tools to use based on
        the patient's symptoms, following the ReAct pattern.
        
        Args:
            patient: PatientScreening object with symptoms
            
        Returns:
            RMDAssessment with risk level and recommendations
        """
        if not self.is_configured():
            return self._create_fallback_assessment(
                patient,
                "API key not configured. Please set GROQ_API_KEY in your .env file. "
                "Get a free API key at https://console.groq.com"
            )
        
        try:
            patient_json = self._prepare_patient_json(patient)
            
            # Create the agent input with system prompt
            system_prompt = self._get_agent_system_prompt()
            user_message = f"""Please analyze this patient and provide an RMD risk assessment.

PATIENT DATA:
{patient.to_clinical_summary()}

PATIENT DATA (JSON for tools):
{patient_json}

Use the available tools to analyze this patient, then provide your final assessment as JSON.
"""
            
            # Create messages for the agent
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            # Run the agent - it will decide which tools to use!
            result = self.agent.invoke({"messages": messages})
            
            # Extract the final output from the last message
            final_messages = result.get("messages", [])
            tools_used = []
            output = ""
            
            for msg in final_messages:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tools_used.extend([tc.get('name', '') for tc in msg.tool_calls])
                if hasattr(msg, 'content') and msg.content:
                    output = msg.content
            
            # Parse the JSON response
            assessment_dict = self._extract_json_from_response(output)
            
            if assessment_dict:
                assessment_dict["tools_used"] = list(set(tools_used))
                return self._create_assessment_from_dict(assessment_dict, patient)
            else:
                # Try to create assessment from the raw output
                return self._create_fallback_assessment(
                    patient,
                    f"Agent completed analysis. Tools used: {tools_used}. Output: {output[:500]}"
                )
                
        except Exception as e:
            return self._create_fallback_assessment(
                patient,
                f"Agent error: {str(e)}"
            )
    
    def _extract_json_from_response(self, text: str) -> Optional[dict]:
        """Extract JSON from the agent's response."""
        import re
        
        # Try to find JSON in code blocks
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except:
                    continue
        
        # Try direct parse
        try:
            return json.loads(text.strip())
        except:
            pass
        
        return None
    
    def _create_assessment_from_dict(
        self, 
        data: dict, 
        patient: PatientScreening
    ) -> RMDAssessment:
        """Create RMDAssessment from parsed dictionary."""
        # Validate and extract fields
        risk_level = data.get("risk_level", "MODERATE")
        if risk_level not in ["LOW", "MODERATE", "HIGH"]:
            risk_level = "MODERATE"
        
        confidence = data.get("confidence_score", 0.5)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            confidence = 0.5
        
        tools_used = data.get("tools_used", [])
        reasoning = data.get("reasoning", "")
        
        # Add tools used to reasoning
        if tools_used:
            reasoning += f"\n\n[Agent used tools: {', '.join(tools_used)}]"
        
        return RMDAssessment(
            risk_level=risk_level,
            likely_conditions=data.get("likely_conditions", []),
            reasoning=reasoning,
            recommended_next_step=data.get("recommended_next_step", "Consult healthcare professional"),
            confidence_score=float(confidence),
            red_flags_identified=data.get("red_flags_identified", []),
            assessment_timestamp=datetime.now()
        )
    
    def _create_fallback_assessment(
        self, 
        patient: PatientScreening, 
        error_msg: str
    ) -> RMDAssessment:
        """Create a fallback assessment using rule-based analysis."""
        from src.utils import calculate_basic_risk_score, check_rmd_patterns
        
        risk_level, confidence = calculate_basic_risk_score(patient)
        patterns = check_rmd_patterns(patient)
        
        # Determine likely conditions
        likely_conditions = []
        if patient.has_symptom("multiple_joints_affected"):
            likely_conditions.append("Rheumatoid Arthritis")
        if patient.has_symptom("skin_rash"):
            likely_conditions.append("Psoriatic Arthritis")
        if patient.age >= 50 and patient.has_symptom("morning_stiffness"):
            likely_conditions.append("Polymyalgia Rheumatica")
        if not likely_conditions:
            likely_conditions = ["Requires clinical evaluation"]
        
        # Next step based on risk
        if risk_level == "HIGH":
            next_step = "Urgent rheumatology referral recommended"
        elif risk_level == "MODERATE":
            next_step = "Schedule GP consultation"
        else:
            next_step = "Continue monitoring symptoms"
        
        return RMDAssessment(
            risk_level=risk_level,
            likely_conditions=likely_conditions,
            reasoning=f"FALLBACK ANALYSIS (Agent unavailable)\n\n{error_msg}\n\nRule-based analysis:\n{patterns}",
            recommended_next_step=next_step,
            confidence_score=confidence,
            red_flags_identified=["System used fallback - clinical review required"],
            assessment_timestamp=datetime.now()
        )
    
    def get_fhir_bundle(
        self, 
        patient: PatientScreening, 
        assessment: RMDAssessment
    ) -> FHIRBundle:
        """
        Generate a FHIR Bundle containing the complete screening encounter.
        
        Args:
            patient: PatientScreening data
            assessment: Generated RMDAssessment
            
        Returns:
            FHIRBundle with Patient, Observations, and RiskAssessment
        """
        # Convert symptoms to dict format
        symptoms_data = []
        for symptom in patient.symptoms:
            symptoms_data.append({
                "name": symptom.name,
                "present": symptom.present,
                "severity": symptom.severity,
                "duration_days": symptom.duration_days,
            })
        
        # Convert assessment to dict
        assessment_data = {
            "risk_level": assessment.risk_level,
            "likely_conditions": assessment.likely_conditions,
            "reasoning": assessment.reasoning,
            "recommended_next_step": assessment.recommended_next_step,
            "confidence_score": assessment.confidence_score,
            "red_flags_identified": assessment.red_flags_identified,
        }
        
        return create_screening_bundle(
            patient_id=patient.patient_id,
            age=patient.age,
            sex=patient.sex,
            symptoms=symptoms_data,
            assessment=assessment_data
        )


# =============================================================================
# DEMO MODE - For testing without API
# =============================================================================

def demo_assessment(patient: PatientScreening) -> RMDAssessment:
    """
    Generate a demo assessment without calling the LLM API.
    Uses rule-based analysis for offline testing.
    
    Args:
        patient: PatientScreening object
        
    Returns:
        RMDAssessment based on rule-based analysis
    """
    from src.utils import calculate_basic_risk_score, check_rmd_patterns
    
    # Run all tools locally to simulate agent behavior
    patient_json = json.dumps({
        "age": patient.age,
        "sex": patient.sex,
        "symptoms": [
            {"name": s.name, "present": s.present, "severity": s.severity, 
             "duration_days": s.duration_days, "duration_minutes": s.duration_minutes}
            for s in patient.symptoms
        ]
    })
    
    # Simulate tool calls
    inflammatory = analyze_inflammatory_markers.invoke(patient_json)
    joint_pattern = analyze_joint_pattern.invoke(patient_json)
    systemic = analyze_systemic_symptoms.invoke(patient_json)
    risk_calc = calculate_risk_score.invoke(patient_json)
    differentials = get_differential_diagnosis.invoke(patient_json)
    
    # Get risk level
    risk_level, confidence = calculate_basic_risk_score(patient)
    
    # Build reasoning
    reasoning = f"""DEMO MODE - Simulated Agent Analysis

The agent would use its tools to analyze the patient. Here's what each tool found:

--- INFLAMMATORY MARKERS ---
{inflammatory}

--- JOINT PATTERN ---
{joint_pattern}

--- SYSTEMIC SYMPTOMS ---
{systemic}

--- RISK CALCULATION ---
{risk_calc}

--- DIFFERENTIAL DIAGNOSIS ---
{differentials}

[Demo used tools: analyze_inflammatory_markers, analyze_joint_pattern, analyze_systemic_symptoms, calculate_risk_score, get_differential_diagnosis]
"""
    
    # Extract likely conditions from differential
    likely_conditions = []
    if patient.has_symptom("multiple_joints_affected"):
        likely_conditions.append("Rheumatoid Arthritis")
    if patient.has_symptom("morning_stiffness"):
        likely_conditions.append("Inflammatory Arthritis")
    if patient.has_symptom("skin_rash"):
        likely_conditions.append("Psoriatic Arthritis")
    if patient.age >= 50 and patient.has_symptom("fatigue"):
        likely_conditions.append("Polymyalgia Rheumatica")
    if not likely_conditions:
        likely_conditions = ["Osteoarthritis", "Mechanical Joint Pain"]
    
    # Determine next step
    if risk_level == "HIGH":
        next_step = "Urgent rheumatology referral recommended"
    elif risk_level == "MODERATE":
        next_step = "Schedule GP consultation for further evaluation"
    else:
        next_step = "Continue monitoring; consult GP if symptoms persist"
    
    # Extract red flags
    red_flags = []
    patterns = check_rmd_patterns(patient)
    for line in patterns.split("\n"):
        if "⚠️" in line:
            red_flags.append(line.replace("⚠️", "").strip())
    
    return RMDAssessment(
        risk_level=risk_level,
        likely_conditions=likely_conditions,
        reasoning=reasoning,
        recommended_next_step=next_step,
        confidence_score=confidence,
        red_flags_identified=red_flags,
        assessment_timestamp=datetime.now()
    )
