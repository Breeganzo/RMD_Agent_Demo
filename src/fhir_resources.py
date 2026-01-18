"""
RMD-Health Screening Agent - FHIR R4 Resources
================================================

This module implements HL7 FHIR R4 compliant resource structures for
healthcare interoperability. These models follow the official FHIR
specification for Patient, Observation, and RiskAssessment resources.

FHIR (Fast Healthcare Interoperability Resources) is the NHS standard
for exchanging healthcare information electronically.

Resources Implemented:
- FHIRPatient: Demographics and identification (FHIR Patient)
- FHIRObservation: Clinical symptoms as observations (FHIR Observation)
- FHIRRiskAssessment: AI-generated risk assessment (FHIR RiskAssessment)
- FHIRBundle: Collection of resources (FHIR Bundle)

References:
- https://www.hl7.org/fhir/R4/
- https://digital.nhs.uk/services/fhir-apis
"""

from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
import uuid


# SNOMED CT Codes for RMD symptoms (for demonstration)
SNOMED_CODES = {
    "joint_pain": {"code": "57676002", "display": "Joint pain"},
    "multiple_joints_affected": {"code": "202322003", "display": "Polyarthralgia"},
    "morning_stiffness": {"code": "271706000", "display": "Morning stiffness"},
    "joint_swelling": {"code": "298158008", "display": "Joint swelling"},
    "joint_redness": {"code": "248491001", "display": "Redness of joint"},
    "fatigue": {"code": "84229001", "display": "Fatigue"},
    "reduced_mobility": {"code": "8510008", "display": "Reduced mobility"},
    "fever": {"code": "386661006", "display": "Fever"},
    "weight_loss": {"code": "89362005", "display": "Weight loss"},
    "skin_rash": {"code": "271807003", "display": "Skin rash"},
}

# RMD Condition SNOMED codes
RMD_CONDITIONS = {
    "Rheumatoid Arthritis": {"code": "69896004", "display": "Rheumatoid arthritis"},
    "Osteoarthritis": {"code": "396275006", "display": "Osteoarthritis"},
    "Psoriatic Arthritis": {"code": "33339001", "display": "Psoriatic arthritis"},
    "Ankylosing Spondylitis": {"code": "9631008", "display": "Ankylosing spondylitis"},
    "Gout": {"code": "90560007", "display": "Gout"},
    "Systemic Lupus Erythematosus": {"code": "55464009", "display": "Systemic lupus erythematosus"},
    "Fibromyalgia": {"code": "203082005", "display": "Fibromyalgia"},
    "Polymyalgia Rheumatica": {"code": "65323003", "display": "Polymyalgia rheumatica"},
}


class FHIRCoding(BaseModel):
    """FHIR Coding element - represents a code from a code system."""
    system: str = Field(..., description="Identity of the terminology system")
    code: str = Field(..., description="Symbol in syntax defined by the system")
    display: Optional[str] = Field(None, description="Representation defined by the system")


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept - represents a coded concept with text."""
    coding: list[FHIRCoding] = Field(default_factory=list)
    text: Optional[str] = Field(None, description="Plain text representation")


class FHIRReference(BaseModel):
    """FHIR Reference - a reference to another resource."""
    reference: str = Field(..., description="Relative or absolute URL reference")
    display: Optional[str] = Field(None, description="Text alternative for the resource")


class FHIRIdentifier(BaseModel):
    """FHIR Identifier - a business identifier."""
    system: Optional[str] = Field(None, description="The namespace for the identifier")
    value: str = Field(..., description="The value that is unique")


class FHIRHumanName(BaseModel):
    """FHIR HumanName - a name of a human."""
    use: Optional[str] = Field("official", description="usual | official | temp | nickname")
    family: Optional[str] = Field(None, description="Family name (surname)")
    given: list[str] = Field(default_factory=list, description="Given names")


class FHIRPatient(BaseModel):
    """
    FHIR R4 Patient Resource.
    
    This represents a patient in the healthcare system.
    Reference: https://www.hl7.org/fhir/R4/patient.html
    """
    resourceType: Literal["Patient"] = "Patient"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    name: list[FHIRHumanName] = Field(default_factory=list)
    gender: Optional[Literal["male", "female", "other", "unknown"]] = None
    birthDate: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    
    # Extension for age (since we use age directly in demo)
    extension: list[dict] = Field(default_factory=list)
    
    # Meta for NHS UK Core FHIR profile compliance
    meta: dict = Field(default_factory=lambda: {
        "profile": ["https://fhir.hl7.org.uk/StructureDefinition/UKCore-Patient"]
    })
    
    @classmethod
    def from_screening_data(cls, patient_id: str, age: int, sex: str) -> "FHIRPatient":
        """Create a FHIR Patient from screening data.
        
        NHS GDPR Compliance Notes:
        - Patient ID is pseudonymized (not real NHS Number)
        - Name is intentionally NOT included to minimize PII
        - Only age and sex stored for clinical relevance
        - Full PII available only through authorized audit trail
        """
        gender_map = {
            "Male": "male",
            "Female": "female", 
            "Other": "other",
            "Prefer not to say": "unknown"
        }
        
        # Generate pseudonymized NHS-style identifier (10-digit format)
        import hashlib
        pseudo_id = hashlib.sha256(f"NHS-{patient_id}".encode()).hexdigest()[:10].upper()
        
        return cls(
            id=patient_id,
            identifier=[
                # Pseudonymized identifier (NOT real NHS Number)
                FHIRIdentifier(
                    system="https://fhir.nhs.uk/Id/nhs-number",  # NHS Number system
                    value=f"DEMO-{pseudo_id}"  # Clearly marked as demo/pseudonymized
                ),
                # RMD-Health internal reference
                FHIRIdentifier(
                    system="urn:rmd-health:patient-ref",
                    value=patient_id
                )
            ],
            # GDPR: No name included - pseudonymized patient
            name=[],
            gender=gender_map.get(sex, "unknown"),
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                    "valueInteger": age
                }
            ],
            meta={
                "profile": ["https://fhir.hl7.org.uk/StructureDefinition/UKCore-Patient"],
                "security": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                        "code": "R",
                        "display": "Restricted"
                    }
                ],
                "tag": [
                    {
                        "system": "urn:rmd-health:data-classification",
                        "code": "PSEUDONYMIZED",
                        "display": "Pseudonymized Patient Data"
                    }
                ]
            }
        )
    
    def to_fhir_json(self) -> dict:
        """Convert to FHIR-compliant JSON."""
        return self.model_dump(exclude_none=True)


class FHIRQuantity(BaseModel):
    """FHIR Quantity element."""
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = "http://unitsofmeasure.org"
    code: Optional[str] = None


class FHIRObservation(BaseModel):
    """
    FHIR R4 Observation Resource.
    
    This represents a clinical observation (symptom) in the healthcare system.
    Reference: https://www.hl7.org/fhir/R4/observation.html
    """
    resourceType: Literal["Observation"] = "Observation"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["registered", "preliminary", "final", "amended"] = "final"
    category: list[FHIRCodeableConcept] = Field(default_factory=list)
    code: FHIRCodeableConcept
    subject: Optional[FHIRReference] = None
    effectiveDateTime: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueQuantity: Optional[FHIRQuantity] = None
    valueString: Optional[str] = None
    component: list[dict] = Field(default_factory=list)
    note: list[dict] = Field(default_factory=list)
    
    @classmethod
    def from_symptom(
        cls,
        symptom_name: str,
        present: bool,
        severity: Optional[int] = None,
        duration_days: Optional[int] = None,
        patient_ref: Optional[str] = None
    ) -> "FHIRObservation":
        """Create a FHIR Observation from a symptom."""
        snomed = SNOMED_CODES.get(symptom_name, {
            "code": "unknown",
            "display": symptom_name.replace("_", " ").title()
        })
        
        obs = cls(
            id=str(uuid.uuid4()),
            status="final",
            category=[
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="exam",
                            display="Exam"
                        )
                    ],
                    text="Clinical Examination"
                )
            ],
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system="http://snomed.info/sct",
                        code=snomed["code"],
                        display=snomed["display"]
                    )
                ],
                text=snomed["display"]
            ),
            valueBoolean=present,
            effectiveDateTime=datetime.now().isoformat()
        )
        
        if patient_ref:
            obs.subject = FHIRReference(reference=f"Patient/{patient_ref}")
        
        # Add severity as component
        if severity is not None:
            obs.component.append({
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "246112005",
                        "display": "Severity"
                    }]
                },
                "valueInteger": severity
            })
        
        # Add duration as component
        if duration_days is not None:
            obs.component.append({
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "103335007",
                        "display": "Duration"
                    }]
                },
                "valueQuantity": {
                    "value": duration_days,
                    "unit": "days",
                    "system": "http://unitsofmeasure.org",
                    "code": "d"
                }
            })
        
        return obs
    
    def to_fhir_json(self) -> dict:
        """Convert to FHIR-compliant JSON."""
        return self.model_dump(exclude_none=True)


class FHIRRiskAssessmentPrediction(BaseModel):
    """FHIR RiskAssessment Prediction component."""
    outcome: Optional[FHIRCodeableConcept] = None
    qualitativeRisk: Optional[FHIRCodeableConcept] = None
    probabilityDecimal: Optional[float] = Field(None, ge=0, le=1)
    rationale: Optional[str] = None


class FHIRRiskAssessment(BaseModel):
    """
    FHIR R4 RiskAssessment Resource.
    
    This represents an AI-generated risk assessment.
    Reference: https://www.hl7.org/fhir/R4/riskassessment.html
    """
    resourceType: Literal["RiskAssessment"] = "RiskAssessment"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["registered", "preliminary", "final", "amended"] = "final"
    subject: Optional[FHIRReference] = None
    occurrenceDateTime: Optional[str] = None
    condition: Optional[FHIRReference] = None
    performer: Optional[FHIRReference] = None
    basis: list[FHIRReference] = Field(default_factory=list)
    prediction: list[FHIRRiskAssessmentPrediction] = Field(default_factory=list)
    mitigation: Optional[str] = None
    note: list[dict] = Field(default_factory=list)
    
    # Extension for our custom fields
    extension: list[dict] = Field(default_factory=list)
    
    @classmethod
    def from_assessment(
        cls,
        risk_level: str,
        likely_conditions: list[str],
        reasoning: str,
        recommended_next_step: str,
        confidence_score: float,
        red_flags: list[str],
        patient_ref: Optional[str] = None,
        observation_refs: Optional[list[str]] = None
    ) -> "FHIRRiskAssessment":
        """Create a FHIR RiskAssessment from our assessment."""
        
        risk_coding = {
            "HIGH": FHIRCodeableConcept(
                coding=[FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/risk-probability",
                    code="high",
                    display="High likelihood"
                )],
                text="High Risk"
            ),
            "MODERATE": FHIRCodeableConcept(
                coding=[FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/risk-probability",
                    code="moderate",
                    display="Moderate likelihood"
                )],
                text="Moderate Risk"
            ),
            "LOW": FHIRCodeableConcept(
                coding=[FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/risk-probability",
                    code="low",
                    display="Low likelihood"
                )],
                text="Low Risk"
            )
        }
        
        # Create predictions for each likely condition
        predictions = []
        for condition in likely_conditions:
            snomed = RMD_CONDITIONS.get(condition, {
                "code": "unknown",
                "display": condition
            })
            
            pred = FHIRRiskAssessmentPrediction(
                outcome=FHIRCodeableConcept(
                    coding=[FHIRCoding(
                        system="http://snomed.info/sct",
                        code=snomed.get("code", "unknown"),
                        display=snomed.get("display", condition)
                    )],
                    text=condition
                ),
                qualitativeRisk=risk_coding.get(risk_level),
                probabilityDecimal=confidence_score,
                rationale=reasoning[:200] if len(reasoning) > 200 else reasoning
            )
            predictions.append(pred)
        
        ra = cls(
            id=str(uuid.uuid4()),
            status="final",
            occurrenceDateTime=datetime.now().isoformat(),
            prediction=predictions,
            mitigation=recommended_next_step,
            note=[
                {"text": reasoning},
            ]
        )
        
        if patient_ref:
            ra.subject = FHIRReference(reference=f"Patient/{patient_ref}")
        
        # Add observation references as basis
        if observation_refs:
            ra.basis = [
                FHIRReference(reference=f"Observation/{ref}")
                for ref in observation_refs
            ]
        
        # Add red flags as extension
        if red_flags:
            ra.extension.append({
                "url": "http://rmd-health.demo/fhir/StructureDefinition/red-flags",
                "valueString": "; ".join(red_flags)
            })
        
        # Add performer (AI system)
        ra.performer = FHIRReference(
            reference="Device/rmd-health-ai-agent",
            display="RMD-Health AI Screening Agent"
        )
        
        return ra
    
    def to_fhir_json(self) -> dict:
        """Convert to FHIR-compliant JSON."""
        return self.model_dump(exclude_none=True)


class FHIRBundleEntry(BaseModel):
    """FHIR Bundle Entry."""
    fullUrl: Optional[str] = None
    resource: dict = Field(...)


class FHIRBundle(BaseModel):
    """
    FHIR R4 Bundle Resource.
    
    A container for a collection of resources.
    Reference: https://www.hl7.org/fhir/R4/bundle.html
    """
    resourceType: Literal["Bundle"] = "Bundle"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["document", "message", "transaction", "collection", "searchset"] = "collection"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    entry: list[FHIRBundleEntry] = Field(default_factory=list)
    
    def add_resource(self, resource: BaseModel):
        """Add a resource to the bundle."""
        resource_dict = resource.model_dump(exclude_none=True)
        resource_type = resource_dict.get("resourceType", "Unknown")
        resource_id = resource_dict.get("id", str(uuid.uuid4()))
        
        self.entry.append(FHIRBundleEntry(
            fullUrl=f"urn:uuid:{resource_id}",
            resource=resource_dict
        ))
    
    def to_fhir_json(self) -> dict:
        """Convert to FHIR-compliant JSON."""
        return self.model_dump(exclude_none=True)


def create_screening_bundle(
    patient_id: str,
    age: int,
    sex: str,
    symptoms: list[dict],
    assessment: Optional[dict] = None
) -> FHIRBundle:
    """
    Create a FHIR Bundle containing the complete screening encounter.
    
    Args:
        patient_id: Patient identifier
        age: Patient age
        sex: Patient sex
        symptoms: List of symptom dicts with name, present, severity, duration_days
        assessment: Optional assessment dict with risk_level, conditions, etc.
        
    Returns:
        FHIRBundle containing Patient, Observations, and optionally RiskAssessment
    """
    bundle = FHIRBundle()
    
    # Create Patient
    patient = FHIRPatient.from_screening_data(patient_id, age, sex)
    bundle.add_resource(patient)
    
    # Create Observations for each symptom
    observation_ids = []
    for symptom in symptoms:
        obs = FHIRObservation.from_symptom(
            symptom_name=symptom.get("name", "unknown"),
            present=symptom.get("present", False),
            severity=symptom.get("severity"),
            duration_days=symptom.get("duration_days"),
            patient_ref=patient_id
        )
        bundle.add_resource(obs)
        observation_ids.append(obs.id)
    
    # Create RiskAssessment if provided
    if assessment:
        risk_assessment = FHIRRiskAssessment.from_assessment(
            risk_level=assessment.get("risk_level", "MODERATE"),
            likely_conditions=assessment.get("likely_conditions", []),
            reasoning=assessment.get("reasoning", ""),
            recommended_next_step=assessment.get("recommended_next_step", ""),
            confidence_score=assessment.get("confidence_score", 0.5),
            red_flags=assessment.get("red_flags_identified", []),
            patient_ref=patient_id,
            observation_refs=observation_ids
        )
        bundle.add_resource(risk_assessment)
    
    return bundle
