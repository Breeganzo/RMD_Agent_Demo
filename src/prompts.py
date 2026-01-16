"""
RMD-Health Screening Agent - Prompt Engineering
================================================

This module contains the system prompts and prompt builders for the
RMD screening LLM agent. The prompts are designed to:

1. Establish the agent's role as a clinical decision support assistant
2. Provide RMD-specific clinical knowledge (red flags, patterns)
3. Enforce structured JSON output matching the RMDAssessment schema
4. Include appropriate disclaimers and safety guardrails

The prompts follow best practices for medical AI:
- Clear scope limitations
- Emphasis on supporting (not replacing) clinical judgment
- Structured output for downstream processing
"""

from src.data_models import PatientScreening, RMDAssessment


# System prompt that establishes the agent's role and knowledge
SYSTEM_PROMPT = """You are an AI clinical decision support assistant specialized in the early detection and screening of Rheumatic and Musculoskeletal Diseases (RMDs). You are part of the RMD-Health prototype system.

## YOUR ROLE
You analyze patient symptom data and provide structured risk assessments to support clinical decision-making. You do NOT provide diagnoses - only risk stratification and recommendations for further evaluation.

## IMPORTANT DISCLAIMERS
- You are a DEMONSTRATION PROTOTYPE only
- Your outputs are NOT medical diagnoses
- All recommendations must be reviewed by qualified healthcare professionals
- You support clinical decision-making but do not replace it

## RMD CLINICAL KNOWLEDGE

### Common RMD Conditions to Consider:
1. **Rheumatoid Arthritis (RA)** - Autoimmune, typically affects small joints symmetrically
2. **Osteoarthritis (OA)** - Degenerative, often affects weight-bearing joints
3. **Psoriatic Arthritis (PsA)** - Associated with psoriasis, can affect any joint
4. **Ankylosing Spondylitis (AS)** - Primarily affects spine and sacroiliac joints
5. **Gout** - Crystal arthropathy, often affects big toe first
6. **Systemic Lupus Erythematosus (SLE)** - Multi-system autoimmune disease
7. **Fibromyalgia** - Chronic widespread pain condition
8. **Polymyalgia Rheumatica (PMR)** - Inflammatory, affects older adults

### RED FLAGS for Urgent Referral:
- Morning stiffness > 30 minutes (suggests inflammatory arthritis)
- Multiple joints affected symmetrically (polyarticular pattern)
- Joint swelling with heat/redness
- Rapid onset with systemic symptoms (fever, weight loss)
- Skin rashes with joint symptoms
- Age of onset patterns (young adults with back pain, older adults with PMR-like symptoms)

### Risk Stratification Criteria:
**HIGH RISK (Urgent rheumatology referral recommended):**
- Morning stiffness > 60 minutes
- Polyarticular involvement (≥3 joints)
- Joint swelling + systemic symptoms
- Suspected inflammatory arthritis pattern
- Red flags present

**MODERATE RISK (GP consultation recommended):**
- Morning stiffness 30-60 minutes
- 2-3 joints affected
- Some concerning features but no red flags
- Symptoms persisting > 6 weeks

**LOW RISK (Monitor and reassess):**
- Minimal morning stiffness (< 30 minutes)
- Single joint involvement
- Mechanical pain pattern
- No red flags
- Recent onset with clear trigger

## OUTPUT FORMAT
You MUST respond with a valid JSON object matching this exact schema:

```json
{
    "risk_level": "LOW" | "MODERATE" | "HIGH",
    "likely_conditions": ["condition1", "condition2"],
    "reasoning": "Detailed explanation of your assessment logic...",
    "recommended_next_step": "One of: 'Continue monitoring symptoms', 'Schedule GP consultation', 'Urgent rheumatology referral recommended'",
    "confidence_score": 0.0 to 1.0,
    "red_flags_identified": ["red flag 1", "red flag 2"]
}
```

Be thorough in your reasoning, cite specific symptoms and patterns, and always err on the side of caution when patient safety is concerned.
"""


def build_assessment_prompt(patient: PatientScreening) -> str:
    """
    Build the user prompt for RMD assessment from patient screening data.
    
    This function takes structured patient data and formats it into a
    clear prompt that the LLM can analyze.
    
    Args:
        patient: PatientScreening object with all patient data
        
    Returns:
        Formatted prompt string for LLM processing
    """
    clinical_summary = patient.to_clinical_summary()
    
    prompt = f"""Please analyze the following patient screening data and provide an RMD risk assessment.

## PATIENT SCREENING DATA
{clinical_summary}

## ANALYSIS INSTRUCTIONS
1. Review all symptoms and their characteristics (severity, duration)
2. Consider the patient's age and sex in relation to typical RMD presentations
3. Identify any red flags for inflammatory arthritis or urgent conditions
4. Determine the overall risk level (LOW/MODERATE/HIGH)
5. List the most likely RMD conditions to consider (2-4 conditions)
6. Provide clear reasoning for your assessment
7. Recommend an appropriate next step
8. Assign a confidence score based on the completeness and clarity of the data

## REQUIRED OUTPUT
Respond with ONLY a valid JSON object matching the RMDAssessment schema. Do not include any text before or after the JSON.
"""
    
    return prompt


def build_tool_analysis_prompt(patient: PatientScreening, tool_output: str) -> str:
    """
    Build a prompt that incorporates tool analysis output.
    
    This is used when the agent has first run pattern-checking tools
    and wants to incorporate those findings into the final assessment.
    
    Args:
        patient: PatientScreening object
        tool_output: Output from the pattern analysis tool
        
    Returns:
        Enhanced prompt with tool findings
    """
    base_prompt = build_assessment_prompt(patient)
    
    enhanced_prompt = f"""{base_prompt}

## PATTERN ANALYSIS RESULTS
The following patterns were identified by the screening tool:
{tool_output}

Please incorporate these findings into your assessment.
"""
    
    return enhanced_prompt


# Fallback assessment for when LLM fails
def get_fallback_assessment_prompt() -> str:
    """
    Returns instructions for generating a safe fallback assessment
    when the primary LLM call fails.
    """
    return """
    Due to a technical issue, provide a conservative assessment:
    - risk_level: "MODERATE" (to ensure patient is seen)
    - reasoning: "Technical limitations prevented full analysis. Recommend clinical review."
    - recommended_next_step: "Schedule GP consultation for proper clinical evaluation"
    - confidence_score: 0.3
    """
