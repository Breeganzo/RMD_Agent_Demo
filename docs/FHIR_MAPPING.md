# FHIR Resource Mapping

## Overview

This document explains how the RMD-Health Screening Agent's data models align with **FHIR (Fast Healthcare Interoperability Resources)** standards. FHIR is the NHS's preferred standard for healthcare data exchange, and understanding these mappings is essential for future NHS integration.

## What is FHIR?

FHIR (Fast Healthcare Interoperability Resources) is a standard for exchanging healthcare information electronically. It defines a set of "resources" that represent different types of healthcare data (patients, observations, conditions, etc.) and standardized ways to create, read, update, and delete them via RESTful APIs.

**Key FHIR Concepts:**
- **Resources**: Building blocks of FHIR (Patient, Observation, Condition, etc.)
- **References**: Links between resources (e.g., Observation → Patient)
- **Code Systems**: Standardized terminologies (SNOMED CT, ICD-10, LOINC)
- **Bundles**: Collections of related resources

## Our Data Models → FHIR Mapping

### 1. PatientScreening → FHIR Patient + Encounter + Bundle

Our `PatientScreening` model represents a complete screening session and maps to multiple FHIR resources:

```
PatientScreening
├── patient_id     → FHIR Patient.identifier
├── age            → FHIR Patient.birthDate (calculated)
├── sex            → FHIR Patient.gender
├── symptoms[]     → FHIR Bundle containing Observation resources
├── medical_history → FHIR DocumentReference or Condition resources
└── screening_date  → FHIR Encounter.period
```

**FHIR Patient Resource Example:**
```json
{
  "resourceType": "Patient",
  "identifier": [{
    "system": "https://rmd-health.nhs.uk/patient-id",
    "value": "ABC12345"
  }],
  "gender": "female",
  "birthDate": "1979-06-15"
}
```

**NHS Context:**
- In production, `patient_id` would be the **NHS Number** (10-digit identifier)
- Patient demographics would come from the **Personal Demographics Service (PDS)**
- The encounter would link to the **NHS e-Referral Service (e-RS)**

### 2. Symptom → FHIR Observation

Each `Symptom` in our model corresponds to a FHIR Observation resource:

```
Symptom
├── name           → Observation.code (SNOMED CT concept)
├── present        → Observation.valueBoolean
├── severity       → Observation.component[severity]
├── duration_days  → Observation.component[duration]
└── notes          → Observation.note
```

**FHIR Observation Resource Example:**
```json
{
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "57676002",
      "display": "Joint pain"
    }]
  },
  "subject": {
    "reference": "Patient/ABC12345"
  },
  "valueBoolean": true,
  "component": [{
    "code": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "246112005",
        "display": "Severity"
      }]
    },
    "valueInteger": 7
  }]
}
```

**Symptom → SNOMED CT Mapping:**

| Our Symptom Name | SNOMED CT Code | SNOMED CT Display |
|------------------|----------------|-------------------|
| joint_pain | 57676002 | Joint pain |
| multiple_joints_affected | 202292004 | Polyarthritis |
| morning_stiffness | 271706000 | Morning joint stiffness |
| joint_swelling | 298158008 | Joint swelling |
| joint_redness | 297954000 | Joint redness |
| fatigue | 84229001 | Fatigue |
| fever | 386661006 | Fever |
| weight_loss | 89362005 | Weight loss |
| skin_rash | 271807003 | Skin rash |

### 3. RMDAssessment → FHIR RiskAssessment

Our `RMDAssessment` model maps directly to the FHIR RiskAssessment resource:

```
RMDAssessment
├── risk_level              → RiskAssessment.prediction[].qualitativeRisk
├── likely_conditions       → RiskAssessment.prediction[].outcome
├── reasoning               → RiskAssessment.note
├── recommended_next_step   → RiskAssessment.mitigation
├── confidence_score        → RiskAssessment.prediction[].probabilityDecimal
├── red_flags_identified    → RiskAssessment.note (additional)
└── assessment_timestamp    → RiskAssessment.occurrenceDateTime
```

**FHIR RiskAssessment Resource Example:**
```json
{
  "resourceType": "RiskAssessment",
  "status": "final",
  "subject": {
    "reference": "Patient/ABC12345"
  },
  "occurrenceDateTime": "2025-01-16T10:30:00Z",
  "condition": {
    "display": "Rheumatic Disease Risk"
  },
  "prediction": [{
    "outcome": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "69896004",
        "display": "Rheumatoid arthritis"
      }]
    },
    "qualitativeRisk": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
        "code": "high",
        "display": "High likelihood"
      }]
    },
    "probabilityDecimal": 0.85
  }],
  "mitigation": "Urgent referral to rheumatology recommended",
  "note": [{
    "text": "Patient presents with polyarticular involvement, morning stiffness >60 minutes, and bilateral joint swelling. Pattern strongly suggests inflammatory arthritis."
  }]
}
```

## NHS Integration Considerations

### NHS Spine & FHIR APIs

In a production NHS environment, this system would integrate with:

1. **Personal Demographics Service (PDS)** - Patient lookup via NHS Number
2. **e-Referral Service (e-RS)** - Creating and tracking referrals
3. **GP Connect** - Accessing GP records
4. **Summary Care Record (SCR)** - Viewing key patient information

### FHIR UK Core

The UK has defined [UK Core FHIR Profiles](https://simplifier.net/hl7fhirukcorer4) that add NHS-specific requirements to base FHIR resources:

- **UKCore-Patient**: Adds NHS Number, ethnic category, communication preferences
- **UKCore-Observation**: Adds UK-specific code system bindings
- **UKCore-RiskAssessment**: NHS-specific risk assessment extensions

### Interoperability Standards

The RMD-Health system, in production, would comply with:

| Standard | Purpose |
|----------|---------|
| **FHIR R4** | Data exchange format |
| **SNOMED CT** | Clinical terminology |
| **ICD-10** | Diagnosis coding |
| **NHS Data Dictionary** | NHS-specific data standards |
| **DTAC** | Digital Technology Assessment Criteria |
| **ISO 13485** | Medical device quality management |

## Example: Complete FHIR Bundle

Here's how a complete screening would look as a FHIR Bundle:

```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "patient-001",
        "identifier": [{
          "system": "https://fhir.nhs.uk/Id/nhs-number",
          "value": "9000000009"
        }],
        "gender": "female",
        "birthDate": "1980-01-15"
      }
    },
    {
      "resource": {
        "resourceType": "Encounter",
        "id": "encounter-001",
        "status": "finished",
        "class": {
          "code": "AMB",
          "display": "ambulatory"
        },
        "subject": {
          "reference": "Patient/patient-001"
        },
        "period": {
          "start": "2025-01-16T09:00:00Z",
          "end": "2025-01-16T09:30:00Z"
        }
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "id": "obs-joint-pain",
        "status": "final",
        "code": {
          "coding": [{
            "system": "http://snomed.info/sct",
            "code": "57676002",
            "display": "Joint pain"
          }]
        },
        "subject": {
          "reference": "Patient/patient-001"
        },
        "encounter": {
          "reference": "Encounter/encounter-001"
        },
        "valueBoolean": true
      }
    },
    {
      "resource": {
        "resourceType": "RiskAssessment",
        "id": "risk-001",
        "status": "final",
        "subject": {
          "reference": "Patient/patient-001"
        },
        "encounter": {
          "reference": "Encounter/encounter-001"
        },
        "occurrenceDateTime": "2025-01-16T09:30:00Z",
        "prediction": [{
          "qualitativeRisk": {
            "coding": [{
              "code": "high"
            }]
          },
          "probabilityDecimal": 0.85
        }],
        "mitigation": "Urgent rheumatology referral recommended"
      }
    }
  ]
}
```

## Benefits of FHIR Alignment

1. **NHS Interoperability**: Easy integration with NHS systems
2. **Standardized Data**: Consistent data representation across healthcare settings
3. **Semantic Richness**: SNOMED CT provides precise clinical meaning
4. **Future-Proof**: FHIR is the NHS's strategic direction for APIs
5. **Regulatory Compliance**: Supports DTAC and other NHS requirements

## Limitations of This Demo

This demonstration prototype simplifies FHIR concepts:

- ❌ Does not generate actual FHIR resources
- ❌ Does not connect to NHS systems
- ❌ Uses simplified symptom names instead of SNOMED codes
- ❌ No patient consent management
- ❌ No audit trail (required for NHS)

In a production system, these would all be implemented according to NHS Digital guidance.

## Further Reading

- [HL7 FHIR R4 Specification](https://www.hl7.org/fhir/)
- [NHS Digital FHIR API Standards](https://digital.nhs.uk/developer/api-catalogue)
- [UK Core FHIR Profiles](https://simplifier.net/hl7fhirukcorer4)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)
