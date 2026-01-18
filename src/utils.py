"""
RMD-Health Screening Agent - Utility Functions
===============================================

This module provides utility functions for:
- API communication with Groq (LLM provider)
- JSON parsing and validation
- Pattern analysis tools for the agent
- Error handling helpers
"""

import json
import re
import os
from typing import Optional, Any
from datetime import datetime

from src.data_models import PatientScreening, RMDAssessment, Symptom


def load_api_key() -> str:
    """
    Load the Groq API key from environment variables or Streamlit secrets.
    
    Supports both:
    - Local: .env file with GROQ_API_KEY
    - Streamlit Cloud: secrets.toml with GROQ_API_KEY
    
    Returns:
        The API key string
        
    Raises:
        ValueError: If the API key is not set
    """
    api_key = None
    
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    
    # Fall back to environment variable (for local development)
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "For local: add to .env file. "
            "For Streamlit Cloud: add to secrets in dashboard."
        )
    return api_key


def get_model_name() -> str:
    """Get the configured model name from GROQ_MODEL environment variable."""
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def get_api_base_url() -> str:
    """Get the API base URL, defaulting to Groq's endpoint."""
    return os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def extract_json_from_response(text: str) -> Optional[dict]:
    """
    Extract JSON from LLM response text, handling various formats.
    
    The LLM might return:
    - Pure JSON
    - JSON wrapped in ```json``` code blocks
    - JSON with surrounding text
    
    Args:
        text: Raw response text from the LLM
        
    Returns:
        Parsed JSON as dict, or None if parsing fails
    """
    # Try direct JSON parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                   # Raw JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Clean up the match
                cleaned = match.strip()
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue
    
    return None


def validate_assessment_dict(data: dict) -> tuple[bool, list[str]]:
    """
    Validate that a dictionary has all required fields for RMDAssessment.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = {
        "risk_level": str,
        "likely_conditions": list,
        "reasoning": str,
        "recommended_next_step": str,
        "confidence_score": (int, float)
    }
    
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Invalid type for {field}: expected {expected_type}, got {type(data[field])}")
    
    # Validate risk_level values
    if "risk_level" in data and data["risk_level"] not in ["LOW", "MODERATE", "HIGH"]:
        errors.append(f"Invalid risk_level: {data['risk_level']}. Must be LOW, MODERATE, or HIGH")
    
    # Validate confidence score range
    if "confidence_score" in data:
        score = data["confidence_score"]
        if isinstance(score, (int, float)) and not (0 <= score <= 1):
            errors.append(f"confidence_score must be between 0 and 1, got {score}")
    
    return len(errors) == 0, errors


def check_rmd_patterns(patient: PatientScreening) -> str:
    """
    Analyze patient data for RMD-specific patterns.
    
    This is a TOOL function that the agent can use to get structured
    pattern analysis before making its final assessment.
    
    Args:
        patient: PatientScreening object
        
    Returns:
        String summary of identified patterns
    """
    patterns = []
    red_flags = []
    
    # Check for polyarticular involvement
    multiple_joints = patient.get_symptom("multiple_joints_affected")
    if multiple_joints and multiple_joints.present:
        patterns.append("POLYARTICULAR: Multiple joints affected - concerning for inflammatory arthritis")
        red_flags.append("Multiple joint involvement")
    
    # Check morning stiffness
    morning_stiffness = patient.get_symptom("morning_stiffness")
    if morning_stiffness and morning_stiffness.present:
        if morning_stiffness.duration_days and morning_stiffness.duration_days > 30:
            patterns.append(f"MORNING STIFFNESS: Present for {morning_stiffness.duration_days} minutes - significant (>30 min suggests inflammatory)")
            red_flags.append("Prolonged morning stiffness")
        elif morning_stiffness.severity and morning_stiffness.severity >= 5:
            patterns.append(f"MORNING STIFFNESS: Severity {morning_stiffness.severity}/10 - moderate to severe")
    
    # Check for inflammatory signs
    swelling = patient.get_symptom("joint_swelling")
    redness = patient.get_symptom("joint_redness")
    if swelling and swelling.present:
        if redness and redness.present:
            patterns.append("INFLAMMATORY SIGNS: Both swelling and redness present - active inflammation likely")
            red_flags.append("Joint swelling with redness")
        else:
            patterns.append("JOINT SWELLING: Present - possible inflammatory component")
    
    # Check for systemic symptoms
    fever = patient.get_symptom("fever")
    weight_loss = patient.get_symptom("weight_loss")
    fatigue = patient.get_symptom("fatigue")
    
    systemic_count = sum([
        1 for s in [fever, weight_loss, fatigue]
        if s and s.present
    ])
    
    if systemic_count >= 2:
        patterns.append(f"SYSTEMIC: {systemic_count} systemic symptoms present - concerning for systemic inflammatory disease")
        red_flags.append("Multiple systemic symptoms")
    elif fever and fever.present:
        patterns.append("FEVER: Present - consider infectious or inflammatory cause")
        red_flags.append("Fever with joint symptoms")
    
    # Age-related patterns
    if patient.age < 40:
        joint_pain = patient.get_symptom("joint_pain")
        if joint_pain and joint_pain.present:
            patterns.append(f"YOUNG ADULT ({patient.age}y): Consider inflammatory spondyloarthropathy, RA, or reactive arthritis")
    elif patient.age >= 50:
        if fatigue and fatigue.present and (swelling or (morning_stiffness and morning_stiffness.present)):
            patterns.append(f"OLDER ADULT ({patient.age}y): Consider PMR, late-onset RA, or OA with inflammatory overlay")
    
    # Skin involvement
    rash = patient.get_symptom("skin_rash")
    if rash and rash.present:
        patterns.append("SKIN INVOLVEMENT: Rash present - consider psoriatic arthritis, SLE, or reactive arthritis")
        red_flags.append("Skin rash with joint symptoms")
    
    # Build summary
    if not patterns:
        return "No specific RMD patterns identified. Symptoms appear non-specific or mechanical in nature."
    
    summary_lines = ["PATTERN ANALYSIS RESULTS:", "=" * 40]
    summary_lines.extend(patterns)
    
    if red_flags:
        summary_lines.append("")
        summary_lines.append("RED FLAGS IDENTIFIED:")
        for flag in red_flags:
            summary_lines.append(f"  ⚠️ {flag}")
    
    return "\n".join(summary_lines)


def calculate_basic_risk_score(patient: PatientScreening) -> tuple[str, float]:
    """
    Calculate a basic rule-based risk score as a fallback.
    
    This provides a simple heuristic assessment if the LLM fails.
    Confidence is calculated based on:
    - Number of symptoms reported (more data = higher confidence)
    - Severity information availability
    - Duration information availability
    - Medical history provided
    
    Args:
        patient: PatientScreening object
        
    Returns:
        Tuple of (risk_level, confidence_score)
    """
    risk_score = 0
    confidence_factors = 0
    max_confidence_factors = 0
    
    # Joint pain is baseline
    joint_pain = patient.get_symptom("joint_pain")
    if joint_pain:
        max_confidence_factors += 2  # presence + severity
        if joint_pain.present:
            risk_score += 1
            confidence_factors += 1
            if joint_pain.severity is not None:
                confidence_factors += 1
                # Higher severity increases risk
                if joint_pain.severity >= 7:
                    risk_score += 1
    
    # Multiple joints is concerning
    multiple_joints = patient.get_symptom("multiple_joints_affected")
    if multiple_joints:
        max_confidence_factors += 1
        if multiple_joints.present:
            risk_score += 2
            confidence_factors += 1
    
    # Morning stiffness
    morning_stiffness = patient.get_symptom("morning_stiffness")
    if morning_stiffness:
        max_confidence_factors += 2  # presence + duration
        if morning_stiffness.present:
            risk_score += 2
            confidence_factors += 1
            if morning_stiffness.duration_days is not None:
                confidence_factors += 1
                if morning_stiffness.duration_days > 30:
                    risk_score += 2
                elif morning_stiffness.duration_days > 60:
                    risk_score += 3
    
    # Inflammatory signs
    swelling = patient.get_symptom("joint_swelling")
    if swelling:
        max_confidence_factors += 1
        if swelling.present:
            risk_score += 2
            confidence_factors += 1
    
    redness = patient.get_symptom("joint_redness")
    if redness:
        max_confidence_factors += 1
        if redness.present:
            risk_score += 1
            confidence_factors += 1
    
    # Systemic symptoms
    fever = patient.get_symptom("fever")
    if fever:
        max_confidence_factors += 1
        if fever.present:
            risk_score += 2
            confidence_factors += 1
    
    weight_loss = patient.get_symptom("weight_loss")
    if weight_loss:
        max_confidence_factors += 1
        if weight_loss.present:
            risk_score += 1
            confidence_factors += 1
    
    fatigue = patient.get_symptom("fatigue")
    if fatigue:
        max_confidence_factors += 2  # presence + severity
        if fatigue.present:
            risk_score += 1
            confidence_factors += 1
            if fatigue.severity is not None:
                confidence_factors += 1
                if fatigue.severity >= 7:
                    risk_score += 1
    
    skin_rash = patient.get_symptom("skin_rash")
    if skin_rash:
        max_confidence_factors += 1
        if skin_rash.present:
            risk_score += 2
            confidence_factors += 1
    
    # Medical history adds to confidence
    max_confidence_factors += 1
    if patient.medical_history and len(patient.medical_history.strip()) > 10:
        confidence_factors += 1
    
    # Calculate confidence score based on data completeness
    # Base confidence starts at 0.4, can go up to 0.95 based on data quality
    if max_confidence_factors > 0:
        data_completeness = confidence_factors / max_confidence_factors
        # Scale from 0.4 to 0.95 based on completeness
        confidence = 0.40 + (data_completeness * 0.55)
    else:
        confidence = 0.40
    
    # Adjust confidence based on symptom count (more symptoms = clearer picture)
    symptom_count = sum(1 for s in patient.symptoms if s.present)
    if symptom_count >= 5:
        confidence = min(0.95, confidence + 0.10)
    elif symptom_count >= 3:
        confidence = min(0.90, confidence + 0.05)
    elif symptom_count == 0:
        confidence = max(0.30, confidence - 0.15)
    
    # Round to 2 decimal places
    confidence = round(confidence, 2)
    
    # Determine risk level
    if risk_score >= 8:
        return "HIGH", confidence
    elif risk_score >= 4:
        return "MODERATE", confidence
    else:
        return "LOW", confidence


def create_fallback_assessment(patient: PatientScreening, error_msg: str) -> RMDAssessment:
    """
    Create a fallback assessment when the LLM fails.
    
    This ensures the user always gets some output, even if the AI
    component fails. The fallback is conservative to ensure safety.
    
    Args:
        patient: PatientScreening object
        error_msg: Error message from the failed LLM call
        
    Returns:
        Conservative RMDAssessment
    """
    risk_level, confidence = calculate_basic_risk_score(patient)
    
    return RMDAssessment(
        risk_level=risk_level,
        likely_conditions=["Unable to determine - requires clinical review"],
        reasoning=f"Automated analysis encountered an issue: {error_msg}. "
                  f"A basic rule-based assessment was performed. "
                  f"This patient should be reviewed by a healthcare professional.",
        recommended_next_step="Schedule GP consultation for proper clinical evaluation",
        confidence_score=confidence,
        red_flags_identified=["System unable to perform full analysis - clinical review required"],
        assessment_timestamp=datetime.now()
    )


def format_duration(minutes: int) -> str:
    """Format duration in minutes to a readable string."""
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes == 60:
        return "1 hour"
    else:
        hours = minutes / 60
        return f"{hours:.1f} hours"
