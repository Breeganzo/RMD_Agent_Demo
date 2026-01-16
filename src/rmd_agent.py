"""
RMD-Health Screening Agent - Agentic AI Logic
==============================================

This module implements the core agentic AI functionality for RMD screening.
It uses xAI's Grok API for LLM inference and implements a tool-using
agent pattern for structured clinical decision support.

Key Components:
1. RMDScreeningAgent - Main agent class
2. Tool definitions for pattern analysis
3. API integration with Grok
4. Robust error handling and fallbacks

The agent follows an agentic workflow:
1. Receive patient data
2. Run pattern analysis tools
3. Generate LLM assessment with tool outputs
4. Parse and validate structured response
5. Return RMDAssessment object
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Callable

from dotenv import load_dotenv

from src.data_models import PatientScreening, RMDAssessment
from src.prompts import SYSTEM_PROMPT, build_assessment_prompt, build_tool_analysis_prompt
from src.utils import (
    load_api_key,
    get_model_name,
    get_api_base_url,
    extract_json_from_response,
    validate_assessment_dict,
    check_rmd_patterns,
    create_fallback_assessment
)

# Load environment variables
load_dotenv()


class RMDScreeningAgent:
    """
    Agentic AI for RMD risk screening and assessment.
    
    This agent:
    1. Takes structured patient screening data
    2. Applies domain-specific pattern analysis tools
    3. Uses an LLM (Grok) for clinical reasoning
    4. Returns structured, validated assessments
    
    The agent pattern allows for:
    - Modular tool composition
    - Explainable decision-making
    - Robust error handling
    - Easy extension with new capabilities
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the RMD Screening Agent.
        
        Args:
            api_key: Optional xAI API key. If not provided, loaded from environment.
        """
        self.api_key = api_key or self._load_api_key_safe()
        self.model = get_model_name()
        self.base_url = get_api_base_url()
        
        # Register available tools
        self.tools: dict[str, Callable] = {
            "check_rmd_patterns": check_rmd_patterns
        }
    
    def _load_api_key_safe(self) -> Optional[str]:
        """Load API key without raising exception if not found."""
        try:
            return load_api_key()
        except ValueError:
            return None
    
    def is_configured(self) -> bool:
        """Check if the agent is properly configured with an API key."""
        return self.api_key is not None and self.api_key != "your_xai_api_key_here"
    
    def _call_grok_api(self, messages: list[dict]) -> str:
        """
        Make a chat completion request to the Grok API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            The assistant's response content
            
        Raises:
            requests.RequestException: If the API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for more consistent medical reasoning
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def run_tools(self, patient: PatientScreening) -> str:
        """
        Run all registered tools on the patient data.
        
        This implements the "tool-using" aspect of the agentic AI,
        where the agent can call specialized functions to gather
        structured analysis before making its final assessment.
        
        Args:
            patient: PatientScreening object
            
        Returns:
            Combined output from all tools
        """
        outputs = []
        
        for tool_name, tool_func in self.tools.items():
            try:
                output = tool_func(patient)
                outputs.append(f"[{tool_name}]\n{output}")
            except Exception as e:
                outputs.append(f"[{tool_name}] Error: {str(e)}")
        
        return "\n\n".join(outputs)
    
    def assess(self, patient: PatientScreening) -> RMDAssessment:
        """
        Perform a complete RMD risk assessment on the patient.
        
        This is the main entry point for the agent. It:
        1. Runs pattern analysis tools
        2. Builds the assessment prompt
        3. Calls the LLM for reasoning
        4. Parses and validates the response
        5. Returns a structured RMDAssessment
        
        Args:
            patient: PatientScreening object with all patient data
            
        Returns:
            RMDAssessment object with risk level, reasoning, etc.
        """
        # Check configuration
        if not self.is_configured():
            return create_fallback_assessment(
                patient,
                "API key not configured. Please set XAI_API_KEY in your .env file."
            )
        
        try:
            # Step 1: Run tools for pattern analysis
            tool_output = self.run_tools(patient)
            
            # Step 2: Build the enhanced prompt with tool outputs
            user_prompt = build_tool_analysis_prompt(patient, tool_output)
            
            # Step 3: Prepare messages for the LLM
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            # Step 4: Call the LLM
            response = self._call_grok_api(messages)
            
            # Step 5: Parse the JSON response
            assessment_dict = extract_json_from_response(response)
            
            if assessment_dict is None:
                return create_fallback_assessment(
                    patient,
                    f"Failed to parse LLM response as JSON. Raw response: {response[:200]}..."
                )
            
            # Step 6: Validate the response structure
            is_valid, errors = validate_assessment_dict(assessment_dict)
            
            if not is_valid:
                return create_fallback_assessment(
                    patient,
                    f"Invalid assessment structure: {'; '.join(errors)}"
                )
            
            # Step 7: Create and return the RMDAssessment object
            return RMDAssessment(
                risk_level=assessment_dict["risk_level"],
                likely_conditions=assessment_dict.get("likely_conditions", []),
                reasoning=assessment_dict["reasoning"],
                recommended_next_step=assessment_dict["recommended_next_step"],
                confidence_score=float(assessment_dict["confidence_score"]),
                red_flags_identified=assessment_dict.get("red_flags_identified", []),
                assessment_timestamp=datetime.now()
            )
            
        except requests.exceptions.Timeout:
            return create_fallback_assessment(
                patient,
                "API request timed out. Please try again."
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"API request failed: {str(e)}"
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
                except:
                    pass
            return create_fallback_assessment(patient, error_msg)
        except requests.exceptions.RequestException as e:
            return create_fallback_assessment(
                patient,
                f"Network error: {str(e)}"
            )
        except Exception as e:
            return create_fallback_assessment(
                patient,
                f"Unexpected error: {str(e)}"
            )


# Convenience function for quick assessments
def assess_patient(patient: PatientScreening, api_key: Optional[str] = None) -> RMDAssessment:
    """
    Convenience function to assess a patient without explicitly creating an agent.
    
    Args:
        patient: PatientScreening object
        api_key: Optional API key (uses environment if not provided)
        
    Returns:
        RMDAssessment object
    """
    agent = RMDScreeningAgent(api_key=api_key)
    return agent.assess(patient)


# Demo mode for testing without API key
def demo_assessment(patient: PatientScreening) -> RMDAssessment:
    """
    Generate a demo assessment without calling the LLM.
    
    This is useful for testing the UI without using API credits.
    It uses the rule-based pattern analysis only.
    
    Args:
        patient: PatientScreening object
        
    Returns:
        RMDAssessment based on rule-based analysis
    """
    from src.utils import calculate_basic_risk_score
    
    # Run pattern analysis
    patterns = check_rmd_patterns(patient)
    risk_level, confidence = calculate_basic_risk_score(patient)
    
    # Determine likely conditions based on patterns
    likely_conditions = []
    if patient.has_symptom("multiple_joints_affected"):
        likely_conditions.append("Rheumatoid Arthritis")
    if patient.has_symptom("morning_stiffness"):
        likely_conditions.append("Inflammatory Arthritis (general)")
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
        next_step = "Continue monitoring symptoms; consult GP if symptoms persist or worsen"
    
    # Build reasoning
    reasoning = f"""DEMO MODE - Rule-based analysis only (no LLM called)

Pattern Analysis Results:
{patterns}

This is a demonstration of the assessment logic. In production, the AI would provide
more nuanced clinical reasoning based on the full symptom picture and medical history.

Risk Level: {risk_level}
This assessment is based on the number and severity of symptoms present, with particular
attention to inflammatory markers (morning stiffness, joint swelling, systemic symptoms)
and polyarticular involvement.
"""
    
    # Extract red flags from patterns
    red_flags = []
    if "RED FLAGS" in patterns:
        # Simple extraction of red flags from the pattern output
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
