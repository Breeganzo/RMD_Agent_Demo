# 🛠️ RMD-Health Technology Stack

## Executive Summary

RMD-Health is built using modern, healthcare-appropriate technologies that prioritize **safety**, **explainability**, **interoperability**, and **auditability**. This document details every technology used, where it's applied, why it was chosen, and its relevance to the University of Reading Healthcare AI role.

---

## 1. Core Language & Framework

### Python 3.10+
**Where Used:** Entire codebase  
**Why Chosen:** 
- Industry standard for AI/ML applications
- Rich ecosystem for healthcare data processing
- Strong type hints support for safer code
- Extensive libraries for FHIR, data analysis, and web development

**Relevance to Role:**
- Primary language for healthcare AI development at most NHS/research institutions
- Required for working with clinical ML models and data pipelines

### Streamlit 1.35+
**Where Used:** [app.py](../app.py), [app_multiuser.py](../app_multiuser.py)  
**Why Chosen:**
- Rapid prototyping of clinical decision support tools
- Built-in security features (CSRF protection, secure cookies)
- Session state management for multi-user applications
- Easy deployment to healthcare-compliant cloud platforms

**Relevance to Role:**
- Quick iteration on clinical tool prototypes
- Ability to demonstrate AI capabilities to clinical stakeholders
- Low barrier to entry for clinician feedback cycles

---

## 2. Data & Storage

### SQLite
**Where Used:** [src/database.py](../src/database.py) → `data/rmd_health.db`  
**Why Chosen:**
- Zero-configuration embedded database (ACID compliant)
- File-based storage - easily auditable, backupable, portable
- No external dependencies - crucial for clinical environments with network restrictions
- SQL standard - easy migration to PostgreSQL/SQL Server for production

**Relevance to Role:**
- Understanding of database fundamentals for patient data management
- Data governance awareness (file-based = clear data boundaries)
- Scalability path to enterprise databases

### JSON (Serialization)
**Where Used:** FHIR bundles, XAI explanations, symptom data storage  
**Why Chosen:**
- FHIR R4 standard uses JSON
- Human-readable for audit purposes
- Schema validation possible with JSON Schema
- Native Python support

**Relevance to Role:**
- Healthcare data interchange standard
- API communication format
- Configuration and logging format

---

## 3. Healthcare Interoperability

### HL7 FHIR R4
**Where Used:** [src/fhir_resources.py](../src/fhir_resources.py)  
**Implementation Details:**
```
Resources Implemented:
├── Patient (demographics, NHS identifiers)
├── Condition (diagnoses, RMD conditions)
├── Observation (symptom severity, duration)
├── RiskAssessment (screening results)
└── Bundle (transaction bundles for atomic operations)
```

**Why Chosen:**
- NHS mandated standard (NHS England Digital)
- UK Core FHIR profiles compliance
- International interoperability (HL7 International)
- Strong validation libraries available

**Relevance to Role:**
- **Critical skill** - FHIR knowledge essential for NHS data integration
- GP Connect, NHS Spine, regional health records all use FHIR
- Understanding resource relationships for clinical workflows

### NHS Data Dictionary Alignment
**Where Used:** Patient identifiers, coding systems  
**Standards Referenced:**
- NHS Number (10-digit identifier with check digit)
- SNOMED CT (clinical terminology)
- ICD-10 (diagnosis coding)
- dm+d (medication coding - referenced in prompts)

**Relevance to Role:**
- Demonstrates understanding of NHS data standards
- Required for any NHS-integrated clinical system

---

## 4. Explainable AI (XAI)

### Custom XAI Framework
**Where Used:** [src/xai_explanation.py](../src/xai_explanation.py)  

**Components Implemented:**

| Component | Purpose | Medical Relevance |
|-----------|---------|-------------------|
| `FeatureContribution` | SHAP-like explanations | "Which symptoms increased your risk score?" |
| `DecisionPathStep` | Step-by-step reasoning | "How did the AI reach this conclusion?" |
| `ConfidenceBreakdown` | Uncertainty quantification | "How confident is the system?" |
| `Persona Explanations` | Role-appropriate language | Clinical vs Patient vs Auditor views |

**Why Chosen:**
- Regulatory requirement (EU AI Act, UK MHRA)
- Clinical trust - doctors need to understand AI recommendations
- Patient autonomy - informed consent requires explainability
- Audit compliance - regulators need decision traces

**Relevance to Role:**
- **High Priority** - XAI is a key focus area for the position
- Understanding of SHAP, LIME, attention mechanisms
- Ability to translate technical explanations for clinicians

---

## 5. Security & Authentication

### SHA-256 Password Hashing
**Where Used:** [src/database.py](../src/database.py) `hash_password()`  
**Why Chosen:**
- Cryptographically secure one-way hashing
- No password recovery possible (security by design)
- Industry standard for password storage

**Production Consideration:** Would use `bcrypt` or `argon2` with salting for production systems.

### Session-Based Authentication
**Where Used:** [app_multiuser.py](../app_multiuser.py)  
**Implementation:**
- Streamlit session state for user tracking
- Role-based access control (RBAC)
- Audit logging of all authentication events

**Relevance to Role:**
- NHS Data Security and Protection Toolkit (DSPT) compliance
- Understanding of access control models
- Audit trail requirements for clinical systems

---

## 6. Data Models & Validation

### Pydantic v2
**Where Used:** [src/data_models.py](../src/data_models.py)  
**Why Chosen:**
- Runtime data validation
- Automatic JSON schema generation
- Type-safe data structures
- Clear error messages for invalid data

**Example Models:**
```python
class Symptom(BaseModel):
    name: str
    present: bool
    severity: Optional[int] = Field(None, ge=0, le=10)
    duration_minutes: Optional[int] = Field(None, ge=0)

class PatientScreening(BaseModel):
    patient_id: str = Field(default_factory=lambda: f"PT-{uuid4().hex[:8].upper()}")
    age: int = Field(..., ge=18, le=120)
    sex: str
    symptoms: List[Symptom]
```

**Relevance to Role:**
- Data quality assurance in healthcare pipelines
- API contract enforcement
- Input validation for patient safety

### UUID Generation
**Where Used:** Patient IDs, Assessment IDs  
**Why Chosen:**
- Globally unique identifiers
- No sequential leaking (privacy)
- Collision-resistant

---

## 7. AI/ML Components

### LangChain Framework
**Where Used:** [src/rmd_agent.py](../src/rmd_agent.py)  
**Why Chosen:**
- Structured AI agent orchestration
- Tool-based reasoning (ReAct pattern)
- Prompt management
- Multi-model support (OpenAI, Anthropic, local models)

**Implementation Pattern:**
```
Agent Flow:
User Input → Symptom Parser → Risk Calculator → 
→ Condition Matcher → Red Flag Detector → 
→ Recommendation Engine → XAI Generator
```

**Relevance to Role:**
- Modern AI agent architectures
- Prompt engineering for clinical accuracy
- Tool integration for healthcare workflows

### OpenAI GPT-4 (via API)
**Where Used:** Clinical reasoning engine  
**Why Chosen:**
- State-of-the-art medical knowledge
- Reliable JSON output for structured responses
- Strong instruction following for clinical guidelines
- Temperature control for deterministic outputs

**Production Consideration:** Would evaluate NHS-approved AI services or local deployments for data residency.

---

## 8. Visualization & Reporting

### Matplotlib / Seaborn
**Where Used:** Risk visualizations, confidence charts  
**Why Chosen:**
- Publication-quality figures
- Extensive customization
- Static image generation for reports

### Streamlit Components
**Where Used:** Interactive dashboards  
**Components Used:**
- `st.metric()` - KPI displays
- `st.expander()` - Collapsible sections
- `st.tabs()` - Multi-view navigation
- `st.download_button()` - Report exports

---

## 9. Export & Interoperability

### CSV Export
**Where Used:** Audit logs, assessment data  
**Why Chosen:**
- Universal compatibility
- Excel/SPSS/R import support
- Human-readable for audits

### FHIR JSON Export
**Where Used:** Clinical data bundles  
**Format:** FHIR R4 Bundle (transaction type)

---

## 10. DevOps & Deployment

### Virtual Environment (venv)
**Where Used:** `rmd-env/`  
**Why Chosen:**
- Dependency isolation
- Reproducible environments
- No system Python conflicts

### Requirements Management
**Where Used:** [requirements.txt](../requirements.txt)  
**Key Dependencies:**
```
streamlit>=1.35.0      # Web framework
pydantic>=2.0.0        # Data validation
langchain>=0.1.0       # AI agent framework
openai>=1.0.0          # LLM API client
python-dotenv>=1.0.0   # Environment management
```

### Git Version Control
**Why Essential:**
- Change tracking for clinical software (MDR requirement)
- Collaboration with development teams
- Audit trail for regulatory compliance

---

## 11. Regulatory Technology Alignment

| Regulation | Technology Implementation |
|------------|--------------------------|
| **EU AI Act (High-Risk)** | XAI explanations, audit logs, risk classification |
| **UK MHRA SaMD** | Version control, documentation, clinical validation |
| **NHS DTAC** | Security controls, interoperability (FHIR), accessibility |
| **GDPR/UK GDPR** | Data minimization, consent tracking, audit logs |
| **Caldicott Principles** | Role-based access, purpose limitation |

---

## 12. Technology Decision Matrix

| Requirement | Technology Choice | Alternative Considered | Rationale |
|-------------|------------------|----------------------|-----------|
| Web Framework | Streamlit | Flask, Django, FastAPI | Rapid prototyping, built-in security |
| Database | SQLite | PostgreSQL, MongoDB | Zero-config, portable, ACID |
| AI Framework | LangChain | Direct API, Haystack | Agent orchestration, tool use |
| Data Validation | Pydantic | dataclasses, attrs | JSON schema, validation rules |
| Healthcare Standard | FHIR R4 | HL7v2, openEHR | NHS mandate, UK Core profiles |
| Authentication | Session + SHA256 | OAuth, SAML | Simplicity for demo, upgrade path |

---

## 13. Scalability Path

### Current (Demo/Research)
```
SQLite → Single Server → Local Storage
```

### Production (NHS Deployment)
```
PostgreSQL → Kubernetes → Azure UK South (NHS-approved)
+ NHS Login (OAuth2)
+ GP Connect Integration
+ Spine Connection
```

---

## 14. Skills Demonstrated

This technology stack demonstrates competency in:

1. **Healthcare AI Development** - LangChain, OpenAI, clinical prompts
2. **FHIR Interoperability** - Resource modeling, UK Core profiles
3. **Explainable AI** - Multi-persona explanations, feature contributions
4. **Data Security** - Authentication, RBAC, audit logging
5. **NHS Standards** - Data dictionary, coding systems
6. **Modern Python** - Type hints, Pydantic, async patterns
7. **Clinical Decision Support** - Risk stratification, red flag detection
8. **Regulatory Awareness** - MDR, EU AI Act, NHS DTAC

---

## Quick Reference Card

| Layer | Technology | File |
|-------|------------|------|
| Frontend | Streamlit | `app_multiuser.py` |
| Backend | Python | `src/*.py` |
| Database | SQLite | `src/database.py` |
| AI/ML | LangChain + OpenAI | `src/rmd_agent.py` |
| XAI | Custom Framework | `src/xai_explanation.py` |
| Healthcare | FHIR R4 | `src/fhir_resources.py` |
| Data Models | Pydantic | `src/data_models.py` |
| Security | SHA256 + Session | `src/database.py` |

---

## Contact

**Project:** RMD-Health Clinical Decision Support System  
**Purpose:** University of Reading Healthcare AI Role Demonstration  
**Author:** Anthony Breeganzo  
**Repository:** GitHub (for global access)

---

*This document was created to demonstrate comprehensive understanding of healthcare technology stacks and their application in clinical AI systems.*
