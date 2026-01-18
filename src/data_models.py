"""
RMD-Health Screening Agent - Data Models
=========================================

FHIR-Inspired Pydantic Models for Patient Screening and Risk Assessment

This module defines structured data models that align with FHIR (Fast Healthcare
Interoperability Resources) concepts while remaining simple and practical for
this demonstration prototype.

FHIR Mapping Overview:
- PatientScreening ~ FHIR Patient + Observation Bundle
- Symptom ~ FHIR Observation (component)
- RMDAssessment ~ FHIR RiskAssessment

For detailed FHIR mappings, see docs/FHIR_MAPPING.md
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


class Symptom(BaseModel):
    """
    Represents a clinical symptom observation.
    
    FHIR Mapping: This corresponds to a FHIR Observation resource with:
    - code: Symptom name (would map to SNOMED CT/ICD codes in production)
    - valueBoolean: present field
    - component[severity]: Severity score
    - component[duration]: Duration in days
    
    In a real NHS integration, this would use proper SNOMED CT codes:
    - Joint pain: 57676002
    - Morning stiffness: 271706000
    - Joint swelling: 298158008
    """
    
    name: str = Field(
        ...,
        description="Name of the symptom (e.g., 'joint_pain', 'morning_stiffness')"
    )
    present: bool = Field(
        default=False,
        description="Whether the symptom is currently present"
    )
    severity: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Severity score from 0-10, where 10 is most severe"
    )
    duration_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duration of the symptom in days"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duration in minutes (used for morning stiffness)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about the symptom"
    )


class PatientScreening(BaseModel):
    """
    Represents a patient screening encounter for RMD assessment.
    
    FHIR Mapping: This is a composite that would translate to:
    - FHIR Patient resource (demographics: age, sex)
    - FHIR Encounter resource (the screening session)
    - FHIR Bundle containing Observation resources (symptoms)
    - FHIR DocumentReference for medical history
    
    In NHS context, patient_id would typically be the NHS Number,
    and the encounter would be linked to the national e-Referral Service (e-RS).
    """
    
    patient_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8].upper(),
        description="Unique patient identifier (demo only - not real NHS number)"
    )
    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Patient age in years"
    )
    sex: Literal["Male", "Female", "Other", "Prefer not to say"] = Field(
        ...,
        description="Patient sex/gender"
    )
    symptoms: list[Symptom] = Field(
        default_factory=list,
        description="List of observed symptoms"
    )
    medical_history: Optional[str] = Field(
        default=None,
        description="Free-text medical history and relevant conditions"
    )
    screening_date: datetime = Field(
        default_factory=datetime.now,
        description="Date and time of the screening"
    )
    
    def get_symptom(self, name: str) -> Optional[Symptom]:
        """Helper to retrieve a specific symptom by name."""
        for symptom in self.symptoms:
            if symptom.name.lower() == name.lower():
                return symptom
        return None
    
    def has_symptom(self, name: str) -> bool:
        """Check if a symptom is present."""
        symptom = self.get_symptom(name)
        return symptom is not None and symptom.present
    
    def to_clinical_summary(self) -> str:
        """Generate a clinical summary string for LLM processing."""
        lines = [
            f"Patient ID: {self.patient_id}",
            f"Age: {self.age} years",
            f"Sex: {self.sex}",
            f"Screening Date: {self.screening_date.strftime('%Y-%m-%d %H:%M')}",
            "",
            "SYMPTOMS:"
        ]
        
        for symptom in self.symptoms:
            if symptom.present:
                severity_str = f" (severity: {symptom.severity}/10)" if symptom.severity else ""
                duration_str = f" for {symptom.duration_days} days" if symptom.duration_days else ""
                lines.append(f"  - {symptom.name}: Present{severity_str}{duration_str}")
            else:
                lines.append(f"  - {symptom.name}: Not present")
        
        if self.medical_history:
            lines.extend(["", "MEDICAL HISTORY:", f"  {self.medical_history}"])
        
        return "\n".join(lines)


class RMDAssessment(BaseModel):
    """
    Represents the AI-generated risk assessment for RMD conditions.
    
    FHIR Mapping: This corresponds to a FHIR RiskAssessment resource with:
    - subject: Reference to Patient
    - prediction[].outcome: Likely conditions
    - prediction[].qualitativeRisk: Risk level (LOW/MODERATE/HIGH)
    - prediction[].probabilityDecimal: Confidence score
    - note: Reasoning text
    - mitigation: Recommended next step
    
    In NHS context, this would be formatted for the e-Referral Service
    and potentially integrate with SNOMED CT condition codes.
    """
    
    risk_level: Literal["LOW", "MODERATE", "HIGH"] = Field(
        ...,
        description="Overall risk level for possible RMD conditions"
    )
    likely_conditions: list[str] = Field(
        default_factory=list,
        description="List of possible RMD conditions to consider (indicative only)"
    )
    reasoning: str = Field(
        ...,
        description="Natural language explanation of the assessment logic"
    )
    recommended_next_step: str = Field(
        ...,
        description="Suggested action: 'monitor', 'GP consultation', 'rheumatology referral'"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the assessment (0-1)"
    )
    red_flags_identified: list[str] = Field(
        default_factory=list,
        description="Clinical red flags that triggered higher risk assessment"
    )
    assessment_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the assessment was generated"
    )
    
    def get_risk_color(self) -> str:
        """Get a display color for the risk level."""
        colors = {
            "LOW": "green",
            "MODERATE": "orange", 
            "HIGH": "red"
        }
        return colors.get(self.risk_level, "gray")
    
    def get_confidence_label(self) -> str:
        """Get a human-readable confidence label."""
        if self.confidence_score >= 0.8:
            return "High Confidence"
        elif self.confidence_score >= 0.5:
            return "Moderate Confidence"
        else:
            return "Low Confidence"


# Standard symptom names used in the screening
STANDARD_SYMPTOMS = [
    "joint_pain",
    "multiple_joints_affected",
    "morning_stiffness",
    "joint_swelling",
    "joint_redness",
    "fatigue",
    "reduced_mobility",
    "fever",
    "weight_loss",
    "skin_rash"
]


def create_default_symptoms() -> list[Symptom]:
    """Create a list of standard symptoms with default (not present) values."""
    return [
        Symptom(name="joint_pain", present=False, severity=None, duration_days=None),
        Symptom(name="multiple_joints_affected", present=False),
        Symptom(name="morning_stiffness", present=False, severity=None, duration_days=None),
        Symptom(name="joint_swelling", present=False),
        Symptom(name="joint_redness", present=False),
        Symptom(name="fatigue", present=False, severity=None),
        Symptom(name="reduced_mobility", present=False),
        Symptom(name="fever", present=False),
        Symptom(name="weight_loss", present=False),
        Symptom(name="skin_rash", present=False)
    ]
