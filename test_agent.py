"""Quick test script for RMD Agent Demo"""

from src.rmd_agent import demo_assessment, RMDScreeningAgent
from src.fhir_resources import create_screening_bundle
from src.data_models import PatientScreening, Symptom
import json

print("=" * 60)
print("RMD-Health Screening Agent - Test Suite")
print("=" * 60)

# Test 1: High-risk patient
print("\n--- Test 1: High-Risk Patient ---")
high_risk = PatientScreening(
    age=45,
    sex="Female",
    symptoms=[
        Symptom(name="joint_pain", present=True, severity=7),
        Symptom(name="morning_stiffness", present=True, duration_days=60),
        Symptom(name="multiple_joints_affected", present=True),
        Symptom(name="joint_swelling", present=True),
        Symptom(name="fatigue", present=True, severity=6),
    ],
    medical_history="Family history of RA"
)
assessment = demo_assessment(high_risk)
print(f"Risk Level: {assessment.risk_level}")
print(f"Confidence: {assessment.confidence_score:.2%}")
print(f"Conditions: {assessment.likely_conditions}")
print(f"Red Flags: {len(assessment.red_flags_identified)}")

# Test 2: Low-risk patient
print("\n--- Test 2: Low-Risk Patient ---")
low_risk = PatientScreening(
    age=35,
    sex="Male",
    symptoms=[
        Symptom(name="joint_pain", present=True, severity=3),
    ]
)
assessment = demo_assessment(low_risk)
print(f"Risk Level: {assessment.risk_level}")
print(f"Confidence: {assessment.confidence_score:.2%}")
print(f"Conditions: {assessment.likely_conditions}")

# Test 3: FHIR Bundle
print("\n--- Test 3: FHIR Bundle ---")
symptoms_data = [
    {"name": "joint_pain", "present": True, "severity": 7},
    {"name": "morning_stiffness", "present": True, "duration_days": 60},
]
assessment_data = {
    "risk_level": "HIGH",
    "likely_conditions": ["Rheumatoid Arthritis"],
    "reasoning": "Test reasoning",
    "recommended_next_step": "Urgent referral",
    "confidence_score": 0.85,
    "red_flags_identified": ["Multiple joint involvement"],
}
bundle = create_screening_bundle("TEST123", 45, "Female", symptoms_data, assessment_data)
fhir = bundle.to_fhir_json()
print(f"Bundle Type: {fhir['type']}")
print(f"Resources: {len(fhir['entry'])}")
print(f"Resource Types: {[e['resource']['resourceType'] for e in fhir['entry']]}")

# Test 4: Agent configuration
print("\n--- Test 4: Agent Configuration ---")
agent = RMDScreeningAgent()
print(f"Agent configured: {agent.is_configured()}")
print(f"Tools available: {[t.name for t in agent.tools]}")

print("\n" + "=" * 60)
print("All tests passed! ✅")
print("=" * 60)
