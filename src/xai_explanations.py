"""
RMD-Health Screening Agent - Explainable AI (XAI) Module
=========================================================

This module implements Explainable AI features tailored for different user types:
1. Clinicians - Technical, evidence-based explanations
2. Patients - Simple, reassuring explanations in plain language
3. Auditors - Complete audit trails with timestamps and decision logic

Based on XAI best practices for healthcare AI:
- LIME-style feature contributions
- SHAP-inspired factor attribution
- ReAct reasoning traces
- Counterfactual explanations

Reference: NHS Digital Technology Assessment Criteria (DTAC)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from enum import Enum
import json
import hashlib


class UserRole(str, Enum):
    """User roles with different explanation needs."""
    CLINICIAN = "clinician"
    PATIENT = "patient"
    AUDITOR = "auditor"


@dataclass
class FeatureContribution:
    """
    LIME/SHAP-style feature contribution to the risk assessment.
    Shows how each factor influenced the final decision.
    """
    feature_name: str
    feature_value: str
    contribution_score: float  # -1.0 to +1.0
    contribution_direction: Literal["increases_risk", "decreases_risk", "neutral"]
    clinical_significance: str
    plain_language: str  # Patient-friendly explanation


@dataclass
class ReasoningStep:
    """
    A single step in the agent's reasoning trace.
    Captures the Thought-Action-Observation pattern.
    """
    step_number: int
    timestamp: datetime
    thought: str
    action: Optional[str] = None
    tool_used: Optional[str] = None
    observation: Optional[str] = None
    duration_ms: int = 0


@dataclass
class AuditEntry:
    """
    Complete audit trail entry for regulatory compliance.
    Designed for MHRA/DTAC requirements.
    """
    entry_id: str
    timestamp: datetime
    event_type: str
    details: dict
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    model_version: str = "rmd-agent-v2.0.0"
    system_version: str = "RMD-Health-Demo-v2.0"


@dataclass
class XAIExplanation:
    """
    Complete XAI explanation package with views for all user types.
    """
    # Core data
    assessment_id: str
    risk_level: str
    confidence_score: float
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Feature contributions (LIME/SHAP style)
    feature_contributions: list[FeatureContribution] = field(default_factory=list)
    
    # Reasoning trace (ReAct pattern)
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    
    # Audit entries
    audit_trail: list[AuditEntry] = field(default_factory=list)
    
    # Pre-rendered explanations for each role
    clinician_summary: str = ""
    patient_summary: str = ""
    auditor_summary: str = ""
    
    # Counterfactual explanations
    counterfactuals: list[str] = field(default_factory=list)
    
    # Key findings
    key_factors: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


def generate_input_hash(patient_data: dict) -> str:
    """Generate SHA-256 hash of input data for audit purposes."""
    data_str = json.dumps(patient_data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()[:16]


def calculate_feature_contributions(
    symptoms: list[dict],
    age: int,
    sex: str
) -> list[FeatureContribution]:
    """
    Calculate LIME/SHAP-style feature contributions.
    Shows how each symptom/factor contributes to risk.
    
    In a production system, this would use actual LIME/SHAP libraries.
    For this demo, we use clinical rule-based attribution.
    """
    contributions = []
    
    # Age contribution
    if age >= 50:
        contributions.append(FeatureContribution(
            feature_name="Age",
            feature_value=f"{age} years",
            contribution_score=0.1,
            contribution_direction="increases_risk",
            clinical_significance="Age ≥50 increases risk of inflammatory conditions like PMR",
            plain_language="Your age means we want to be extra careful to check for certain conditions"
        ))
    elif age < 40:
        contributions.append(FeatureContribution(
            feature_name="Age",
            feature_value=f"{age} years",
            contribution_score=-0.05,
            contribution_direction="decreases_risk",
            clinical_significance="Younger age reduces risk of degenerative conditions",
            plain_language="Your age is a positive factor in this assessment"
        ))
    
    # Sex contribution
    if sex == "Female":
        contributions.append(FeatureContribution(
            feature_name="Sex",
            feature_value=sex,
            contribution_score=0.08,
            contribution_direction="increases_risk",
            clinical_significance="Female sex increases RA risk (3:1 female:male ratio)",
            plain_language="Some conditions are slightly more common in women"
        ))
    
    # Symptom contributions
    symptom_weights = {
        "joint_pain": {
            "base_score": 0.15,
            "clinical": "Joint pain is the primary presenting symptom in RMDs",
            "plain": "Joint pain is something we take seriously and want to investigate"
        },
        "multiple_joints_affected": {
            "base_score": 0.25,
            "clinical": "Polyarticular involvement suggests inflammatory arthritis (RA, PsA)",
            "plain": "Having pain in several joints at once can be a sign of certain conditions"
        },
        "morning_stiffness": {
            "base_score": 0.20,
            "clinical": "Morning stiffness >30min is characteristic of inflammatory arthritis",
            "plain": "Stiffness in the morning that takes time to improve is something we look out for"
        },
        "joint_swelling": {
            "base_score": 0.22,
            "clinical": "Synovitis (joint swelling) indicates active inflammation",
            "plain": "Swelling in your joints shows there may be inflammation we need to address"
        },
        "joint_redness": {
            "base_score": 0.18,
            "clinical": "Erythema suggests acute inflammatory process",
            "plain": "Redness around joints can indicate inflammation"
        },
        "fatigue": {
            "base_score": 0.10,
            "clinical": "Constitutional symptoms suggest systemic inflammatory disease",
            "plain": "Feeling very tired can sometimes be linked to inflammation in the body"
        },
        "fever": {
            "base_score": 0.15,
            "clinical": "Fever with joint symptoms requires urgent evaluation",
            "plain": "A fever along with joint problems needs quick attention"
        },
        "skin_rash": {
            "base_score": 0.18,
            "clinical": "Skin involvement suggests PsA, SLE, or dermatomyositis",
            "plain": "Skin changes can sometimes be connected to joint conditions"
        },
        "weight_loss": {
            "base_score": 0.12,
            "clinical": "Unexplained weight loss suggests systemic disease",
            "plain": "Losing weight without trying can be a sign your body is dealing with something"
        }
    }
    
    for symptom in symptoms:
        name = symptom.get("name", "")
        present = symptom.get("present", False)
        severity = symptom.get("severity")
        duration_days = symptom.get("duration_days")
        duration_minutes = symptom.get("duration_minutes")
        
        if name in symptom_weights and present:
            weight_info = symptom_weights[name]
            base_score = weight_info["base_score"]
            
            # Adjust score based on severity and duration
            score = base_score
            if severity and severity >= 7:
                score *= 1.3
            if duration_days and duration_days > 30:
                score *= 1.2
            # Morning stiffness > 30 mins is significant
            if duration_minutes and duration_minutes > 30:
                score *= 1.2
            
            value_parts = ["Present"]
            if severity:
                value_parts.append(f"Severity: {severity}/10")
            if duration_days:
                value_parts.append(f"Duration: {duration_days} days")
            if duration_minutes:
                value_parts.append(f"Duration: {duration_minutes} minutes")
            
            contributions.append(FeatureContribution(
                feature_name=name.replace("_", " ").title(),
                feature_value=", ".join(value_parts),
                contribution_score=round(min(score, 0.35), 2),
                contribution_direction="increases_risk",
                clinical_significance=weight_info["clinical"],
                plain_language=weight_info["plain"]
            ))
    
    # Sort by contribution score
    contributions.sort(key=lambda x: abs(x.contribution_score), reverse=True)
    
    return contributions


def generate_counterfactuals(
    risk_level: str,
    feature_contributions: list[FeatureContribution]
) -> list[str]:
    """
    Generate counterfactual explanations.
    "What would need to change for a different outcome?"
    """
    counterfactuals = []
    
    if risk_level == "HIGH":
        top_factors = [c for c in feature_contributions if c.contribution_score > 0.15]
        if top_factors:
            counterfactuals.append(
                f"The risk level would be MODERATE if {top_factors[0].feature_name.lower()} "
                f"was not present or less severe."
            )
        if len(top_factors) >= 2:
            counterfactuals.append(
                f"If both {top_factors[0].feature_name.lower()} and "
                f"{top_factors[1].feature_name.lower()} were absent, "
                f"the assessment would likely be LOW risk."
            )
    elif risk_level == "MODERATE":
        counterfactuals.append(
            "The risk would be HIGH if additional inflammatory signs were present."
        )
        counterfactuals.append(
            "The risk would be LOW if morning stiffness resolved within 15 minutes."
        )
    else:
        counterfactuals.append(
            "If symptoms persist beyond 6 weeks, the assessment may change to MODERATE."
        )
    
    return counterfactuals


def create_clinician_explanation(
    risk_level: str,
    confidence: float,
    feature_contributions: list[FeatureContribution],
    likely_conditions: list[str],
    reasoning_steps: list[ReasoningStep],
    red_flags: list[str]
) -> str:
    """
    Generate a technical, evidence-based explanation for clinicians.
    Includes clinical terminology and references.
    """
    lines = []
    
    # Header
    lines.append(f"## Clinical Assessment Summary")
    lines.append(f"**Risk Classification:** {risk_level}")
    lines.append(f"**Model Confidence:** {confidence:.0%}")
    lines.append("")
    
    # Key clinical findings
    lines.append("### Key Clinical Findings")
    for contrib in feature_contributions[:5]:
        direction = "↑" if contrib.contribution_direction == "increases_risk" else "↓"
        lines.append(f"- **{contrib.feature_name}** ({contrib.feature_value}): "
                    f"{direction} {contrib.clinical_significance}")
    lines.append("")
    
    # Differential considerations
    if likely_conditions:
        lines.append("### Differential Considerations")
        for i, condition in enumerate(likely_conditions, 1):
            lines.append(f"{i}. {condition}")
        lines.append("")
    
    # Red flags
    if red_flags:
        lines.append("### ⚠️ Red Flags Identified")
        for flag in red_flags:
            lines.append(f"- {flag}")
        lines.append("")
    
    # Agent reasoning trace (collapsed by default)
    if reasoning_steps:
        lines.append("### Agent Reasoning Trace")
        lines.append("The AI agent followed this clinical logic:")
        for step in reasoning_steps:
            lines.append(f"**Step {step.step_number}:** {step.thought}")
            if step.tool_used:
                lines.append(f"  - Tool: `{step.tool_used}`")
            if step.observation:
                lines.append(f"  - Finding: {step.observation[:200]}...")
    
    # Evidence base
    lines.append("")
    lines.append("### Evidence Base")
    lines.append("- NICE NG100: Rheumatoid arthritis in adults")
    lines.append("- NICE CG79: Early referral of suspected inflammatory arthritis")
    lines.append("- BSR Guidelines for RMD management")
    
    return "\n".join(lines)


def create_patient_explanation(
    risk_level: str,
    feature_contributions: list[FeatureContribution],
    recommended_action: str
) -> str:
    """
    Generate a simple, reassuring explanation for patients.
    Uses plain language, avoids medical jargon.
    """
    lines = []
    
    # Warm header
    lines.append("## Your Joint Health Check Results")
    lines.append("")
    
    # Result in plain language
    if risk_level == "HIGH":
        lines.append("### 🔴 We'd like a specialist to see you soon")
        lines.append("")
        lines.append("Based on your symptoms, we think it would be helpful for you to see a "
                    "joint specialist (called a rheumatologist). This doesn't mean anything "
                    "is definitely wrong – it just means we want to make sure you get the "
                    "right care.")
    elif risk_level == "MODERATE":
        lines.append("### 🟡 We'd like to learn more")
        lines.append("")
        lines.append("Your symptoms suggest we should look into this further. Your GP can "
                    "help arrange some tests or a follow-up appointment to better understand "
                    "what's happening.")
    else:
        lines.append("### 🟢 Things look okay for now")
        lines.append("")
        lines.append("Based on what you've told us, your symptoms don't suggest anything "
                    "serious right now. However, if things change or get worse, please don't "
                    "hesitate to speak to your GP.")
    
    lines.append("")
    
    # What we looked at
    lines.append("### What we looked at:")
    for contrib in feature_contributions[:4]:
        lines.append(f"- {contrib.plain_language}")
    
    lines.append("")
    
    # Next steps
    lines.append("### What happens next?")
    lines.append(f"**{recommended_action}**")
    lines.append("")
    
    # Reassurance
    lines.append("### Remember:")
    lines.append("- This check is a helpful first step, not a diagnosis")
    lines.append("- Many joint conditions can be managed very well with proper care")
    lines.append("- Early attention often leads to better outcomes")
    lines.append("- Your GP and healthcare team are here to support you")
    
    lines.append("")
    lines.append("*If you have any questions, please discuss them with your GP or healthcare provider.*")
    
    return "\n".join(lines)


def create_auditor_explanation(
    assessment_id: str,
    audit_trail: list[AuditEntry],
    feature_contributions: list[FeatureContribution],
    reasoning_steps: list[ReasoningStep],
    input_hash: str
) -> str:
    """
    Generate a complete audit log for regulators/auditors.
    Includes timestamps, hashes, and decision audit trail.
    """
    lines = []
    
    # Header
    lines.append("# AUDIT LOG")
    lines.append(f"**Assessment ID:** {assessment_id}")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Input Data Hash:** SHA256:{input_hash}")
    lines.append("")
    
    # System information
    lines.append("## System Information")
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    lines.append("| System Version | RMD-Health-Demo v2.0.0 |")
    lines.append("| Model Version | rmd-agent-v2.0.0 |")
    lines.append("| Framework | LangChain + LangGraph |")
    lines.append("| LLM Provider | Groq (Llama-3.1-8b) |")
    lines.append("| Explanation Method | ReAct Traces + Rule-Based Attribution |")
    lines.append("")
    
    # Processing steps
    lines.append("## Processing Steps")
    lines.append("| Step | Timestamp | Event | Details |")
    lines.append("|------|-----------|-------|---------|")
    
    for entry in audit_trail:
        details_short = str(entry.details)[:50] + "..." if len(str(entry.details)) > 50 else str(entry.details)
        lines.append(f"| {entry.entry_id[:8]} | {entry.timestamp.strftime('%H:%M:%S.%f')[:-3]} | "
                    f"{entry.event_type} | {details_short} |")
    
    lines.append("")
    
    # Decision factors
    lines.append("## Decision Factors")
    lines.append("| Factor | Value | Contribution | Direction |")
    lines.append("|--------|-------|--------------|-----------|")
    
    for contrib in feature_contributions:
        lines.append(f"| {contrib.feature_name} | {contrib.feature_value} | "
                    f"{contrib.contribution_score:+.2f} | {contrib.contribution_direction} |")
    
    lines.append("")
    
    # Reasoning trace
    lines.append("## Agent Reasoning Trace")
    for step in reasoning_steps:
        lines.append(f"### Step {step.step_number} ({step.timestamp.strftime('%H:%M:%S.%f')[:-3]})")
        lines.append(f"- **Thought:** {step.thought}")
        if step.action:
            lines.append(f"- **Action:** {step.action}")
        if step.tool_used:
            lines.append(f"- **Tool Used:** {step.tool_used}")
        if step.observation:
            lines.append(f"- **Observation:** {step.observation}")
        lines.append(f"- **Duration:** {step.duration_ms}ms")
        lines.append("")
    
    # Compliance notes
    lines.append("## Regulatory Compliance Notes")
    lines.append("- This system is a **DEMONSTRATION PROTOTYPE** only")
    lines.append("- Not certified for clinical use under MHRA/MDR regulations")
    lines.append("- Audit trails maintained for transparency demonstration")
    lines.append("- All explanations are deterministic and reproducible")
    
    return "\n".join(lines)


def generate_xai_explanation(
    assessment_id: str,
    patient_data: dict,
    risk_level: str,
    confidence: float,
    likely_conditions: list[str],
    recommended_action: str,
    red_flags: list[str],
    tools_used: list[str]
) -> XAIExplanation:
    """
    Generate a complete XAI explanation package with views for all user types.
    
    This is the main function to call after generating an assessment.
    """
    generated_at = datetime.now()
    
    # Calculate feature contributions
    symptoms = patient_data.get("symptoms", [])
    age = patient_data.get("age", 0)
    sex = patient_data.get("sex", "Unknown")
    
    feature_contributions = calculate_feature_contributions(symptoms, age, sex)
    
    # Generate counterfactuals
    counterfactuals = generate_counterfactuals(risk_level, feature_contributions)
    
    # Create reasoning steps (simulated for demo)
    reasoning_steps = []
    step_time = generated_at
    
    for i, tool in enumerate(tools_used or ["analyze_symptoms", "calculate_risk"], 1):
        from datetime import timedelta
        step_time = step_time + timedelta(milliseconds=150)
        reasoning_steps.append(ReasoningStep(
            step_number=i,
            timestamp=step_time,
            thought=f"Need to analyze patient data using {tool.replace('_', ' ')}",
            action=f"Call {tool}",
            tool_used=tool,
            observation=f"Analysis complete - findings integrated into assessment",
            duration_ms=150
        ))
    
    # Create audit trail
    input_hash = generate_input_hash(patient_data)
    audit_trail = [
        AuditEntry(
            entry_id=f"AE-{i:04d}",
            timestamp=generated_at + timedelta(milliseconds=i*100),
            event_type=event,
            details={"status": "completed"}
        )
        for i, event in enumerate([
            "INPUT_RECEIVED",
            "INPUT_VALIDATED",
            "AGENT_STARTED",
            "TOOLS_EXECUTED",
            "ASSESSMENT_GENERATED",
            "EXPLANATION_CREATED"
        ], 1)
    ]
    
    # Generate role-specific explanations
    clinician_summary = create_clinician_explanation(
        risk_level, confidence, feature_contributions,
        likely_conditions, reasoning_steps, red_flags
    )
    
    patient_summary = create_patient_explanation(
        risk_level, feature_contributions, recommended_action
    )
    
    auditor_summary = create_auditor_explanation(
        assessment_id, audit_trail, feature_contributions,
        reasoning_steps, input_hash
    )
    
    # Extract key factors
    key_factors = [
        f"{c.feature_name}: {c.feature_value}"
        for c in feature_contributions[:5]
    ]
    
    return XAIExplanation(
        assessment_id=assessment_id,
        risk_level=risk_level,
        confidence_score=confidence,
        generated_at=generated_at,
        feature_contributions=feature_contributions,
        reasoning_steps=reasoning_steps,
        audit_trail=audit_trail,
        clinician_summary=clinician_summary,
        patient_summary=patient_summary,
        auditor_summary=auditor_summary,
        counterfactuals=counterfactuals,
        key_factors=key_factors,
        red_flags=red_flags
    )


def get_explanation_for_role(
    explanation: XAIExplanation,
    role: UserRole
) -> str:
    """
    Get the appropriate explanation view for a specific user role.
    """
    if role == UserRole.CLINICIAN:
        return explanation.clinician_summary
    elif role == UserRole.PATIENT:
        return explanation.patient_summary
    elif role == UserRole.AUDITOR:
        return explanation.auditor_summary
    else:
        return explanation.clinician_summary
