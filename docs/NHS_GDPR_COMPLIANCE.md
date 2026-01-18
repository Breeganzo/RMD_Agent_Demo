# 🔒 NHS GDPR & CDSS Compliance Documentation

## Executive Summary

RMD-Health is designed with **privacy-by-design** principles following NHS GDPR requirements and Clinical Decision Support System (CDSS) regulations. This document outlines the compliance measures implemented.

---

## 1. UK GDPR Compliance

### 1.1 Data Minimization (Article 5(1)(c))

| Data Element | Stored | Reason |
|-------------|--------|--------|
| Patient Name | ✅ (for login only) | Required for authentication |
| Email | ✅ (hashed display) | Authentication identifier |
| Age | ✅ | Clinically relevant for RMD screening |
| Sex | ✅ | Clinically relevant for RMD screening |
| Symptoms | ✅ | Core screening function |
| NHS Number | ❌ | Not required for demo - would need proper NHS Spine connection |
| Date of Birth | ❌ | Age sufficient for screening |
| Address | ❌ | Not clinically relevant |
| Phone | ❌ | Not required |

### 1.2 Pseudonymization (Article 4(5))

**Implementation:**
```python
def pseudonymize_id(user_id: int) -> str:
    """Generate a pseudonymized patient identifier."""
    hash_obj = hashlib.sha256(f"RMD-PATIENT-{user_id}".encode())
    return f"PT-{hash_obj.hexdigest()[:8].upper()}"
```

**Display Rules:**
| Viewer Role | Sees |
|-------------|------|
| Patient | Own full name |
| Clinician | Pseudonymized ID + initials (e.g., "PT-A1B2C3D4 (JS)") |
| Auditor | Pseudonymized ID only (e.g., "PT-A1B2C3D4") |

### 1.3 Purpose Limitation (Article 5(1)(b))

Data is used ONLY for:
1. RMD symptom screening
2. Clinical decision support
3. Audit trail for regulatory compliance

**NOT used for:**
- Marketing
- Research (without explicit consent)
- Third-party sharing

### 1.4 Storage Limitation (Article 5(1)(e))

- SQLite database with clear data boundaries
- Data deletion capability via patient request (Right to Erasure)
- Audit logs retained for regulatory period

### 1.5 Security (Article 32)

| Measure | Implementation |
|---------|----------------|
| Password Hashing | SHA-256 (production: use bcrypt/argon2) |
| Session Management | Streamlit secure cookies |
| Access Control | Role-based (RBAC) |
| Audit Logging | All access logged with hash verification |

---

## 2. Caldicott Principles Compliance

### Principle 1: Justify the Purpose
✅ Clear clinical purpose: RMD screening assistance

### Principle 2: Don't Use PII Unless Absolutely Necessary
✅ Pseudonymized IDs for clinician/auditor views

### Principle 3: Use Minimum Necessary PII
✅ Only age, sex, and symptoms stored

### Principle 4: Access on Need-to-Know Basis
✅ Patients see only own data, clinicians see clinical data, auditors see logs

### Principle 5: Everyone with Access Understands Responsibilities
✅ Disclaimers shown on login and assessment pages

### Principle 6: Comply with the Law
✅ UK GDPR compliant architecture

### Principle 7: Duty to Share for Individual Care
✅ FHIR R4 export enables safe clinical data sharing

### Principle 8: Inform Patients About Use
✅ Clear disclaimers and purpose statements

---

## 3. FHIR R4 Compliance

### 3.1 UK Core Profile Alignment

```json
{
  "resourceType": "Patient",
  "meta": {
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
}
```

### 3.2 Resources Implemented

| FHIR Resource | Purpose | Compliance |
|---------------|---------|------------|
| Patient | Demographics | UKCore-Patient profile |
| Observation | Symptoms | SNOMED CT coding |
| RiskAssessment | Screening result | Standard resource |
| Bundle | Transaction | Atomic operations |

### 3.3 NHS Identifier Handling

```python
identifier=[
    FHIRIdentifier(
        system="https://fhir.nhs.uk/Id/nhs-number",
        value=f"DEMO-{pseudo_id}"  # Clearly marked as demo
    )
]
```

**Note:** Real NHS Numbers would require NHS Spine connection and proper verification.

---

## 4. Clinical Decision Support System (CDSS) Compliance

### 4.1 UK MDR 2002 Classification

**Proposed Classification:** Class IIa Medical Device
- Software providing clinical decision support
- Results require clinical validation
- Not standalone diagnostic

### 4.2 Required Disclaimers (Implemented)

```
⚠️ IMPORTANT CLINICAL DECISION SUPPORT DISCLAIMER

This is a CLASS IIa MEDICAL DEVICE under UK MDR 2002 used for SCREENING ONLY.

• This tool does NOT provide medical diagnosis
• Results are indicative only and require clinical validation
• Always consult a qualified healthcare professional
• If you experience severe symptoms, seek immediate medical attention

NHS NICE Compliance: This CDSS follows NICE Evidence Standards Framework
Data Protection: Your data is processed in accordance with UK GDPR
```

### 4.3 NICE Evidence Standards Framework (ESF)

| Standard | Implementation |
|----------|----------------|
| Describe condition | RMD overview in prompts |
| Describe intervention | AI-assisted screening |
| Show how it works | XAI explanations |
| Demonstrate accuracy | Confidence scores |
| Identify risks | Red flags + limitations |

---

## 5. Explainable AI (XAI) Compliance

### 5.1 EU AI Act Requirements (High-Risk AI)

| Requirement | Implementation |
|-------------|----------------|
| Transparency | Multi-persona explanations |
| Human Oversight | Clinician review required |
| Accuracy | Confidence scoring |
| Robustness | Input validation |
| Data Governance | Audit trails |

### 5.2 Explanation Levels

**Patient View:**
- Plain language explanation
- Risk level in simple terms
- Clear next steps

**Clinician View:**
- Technical feature contributions
- SHAP-style importance
- Clinical reasoning chain

**Auditor View:**
- Complete decision trace
- Hash-verified audit trail
- Algorithm version tracking

---

## 6. Audit Trail Compliance

### 6.1 Logged Events

| Event | Data Captured |
|-------|---------------|
| User Login | User ID, timestamp, IP (if enabled) |
| Assessment Created | Patient ref, assessment ID, risk level |
| Data Accessed | Accessor role, pseudonymized patient |
| Export Generated | Auditor ID, timestamp, data scope |

### 6.2 Hash Verification

Each audit entry includes a SHA-256 hash for tamper detection:

```python
entry_hash = hashlib.sha256(
    f"{assessment_id}{timestamp}{event_type}".encode()
).hexdigest()
```

---

## 7. Production Deployment Checklist

Before deploying to production, implement:

| Item | Status | Notes |
|------|--------|-------|
| NHS Login (OAuth2) | ⬜ | Replace demo auth |
| bcrypt/argon2 passwords | ⬜ | Upgrade from SHA-256 |
| PostgreSQL | ⬜ | Replace SQLite |
| Azure UK South hosting | ⬜ | NHS-approved cloud |
| Penetration testing | ⬜ | Required for NHS DSPT |
| Clinical validation | ⬜ | Required for MDR |
| Information Governance review | ⬜ | Required for NHS |

---

## 8. References

- [UK GDPR](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)
- [NHS Data Security Standards](https://www.dsptoolkit.nhs.uk/)
- [NICE Evidence Standards](https://www.nice.org.uk/about/what-we-do/our-programmes/evidence-standards-framework-for-digital-health-technologies)
- [UK MDR 2002](https://www.gov.uk/guidance/regulating-medical-devices-in-the-uk)
- [HL7 UK Core FHIR](https://simplifier.net/hl7fhirukcorer4)
- [Caldicott Principles](https://www.gov.uk/government/publications/the-caldicott-principles)

---

*Document Version: 1.0*  
*Last Updated: January 2026*  
*Author: Anthony Breeganzo*
