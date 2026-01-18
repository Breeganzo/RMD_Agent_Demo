# 🗺️ Technology Map - Where Each Concept is Used

This document maps each technology/concept to its exact location in the codebase.

---

## 🤖 1. AGENTIC AI (LangChain + LangGraph ReAct)

**What it is:** AI that autonomously decides which tools to use based on the situation.

| File | Lines | What It Does |
|------|-------|--------------|
| `src/rmd_agent.py` | 450-530 | `RMDScreeningAgent` class with LangGraph ReAct agent |
| `src/rmd_agent.py` | 40-320 | **5 Agent Tools**: `analyze_inflammatory_markers`, `analyze_joint_pattern`, `analyze_systemic_symptoms`, `calculate_risk_score`, `get_differential_diagnosis` |
| `src/rmd_agent.py` | 380-445 | System prompt with ReAct instructions |
| `app.py` | 1260-1265 | Agent invocation: `agent.assess(patient)` |

**Interview Point:** "The agent uses the ReAct pattern - it Reasons about which tool to use, Acts by calling that tool, then Observes the result before deciding the next step."

---

## 🔍 2. EXPLAINABLE AI (XAI)

**What it is:** Making AI decisions transparent and understandable.

| File | Lines | Technique |
|------|-------|-----------|
| `src/xai_explanations.py` | 105-240 | **LIME/SHAP-style Feature Contributions** - calculates how each symptom contributes to risk |
| `src/xai_explanations.py` | 243-310 | **Counterfactual Explanations** - "what would change the outcome" |
| `src/xai_explanations.py` | 313-380 | **Reasoning Traces** - step-by-step agent thought process |
| `src/xai_explanations.py` | 383-500 | **Role-based Summaries** - different explanations for Clinician/Patient/Auditor |
| `app.py` | 870-945 | **Clinician View** - technical feature bars, contribution scores |
| `app.py` | 960-1020 | **Patient View** - plain language, "what this means" |
| `app.py` | 1025-1100 | **Auditor View** - decision factors table, audit trail |

**Interview Point:** "We implement LIME/SHAP-style attribution to show which factors contributed most to the risk score, plus counterfactual explanations showing what would change the outcome."

---

## 🏥 3. FHIR R4 (Healthcare Interoperability)

**What it is:** HL7 standard for healthcare data exchange used by NHS.

| File | Lines | Resource Type |
|------|-------|---------------|
| `src/fhir_resources.py` | 1-50 | FHIR Bundle structure |
| `src/fhir_resources.py` | 52-120 | **Patient Resource** - demographics |
| `src/fhir_resources.py` | 122-200 | **Observation Resources** - symptoms with SNOMED codes |
| `src/fhir_resources.py` | 202-280 | **RiskAssessment Resource** - AI output |
| `app.py` | 1145-1200 | FHIR bundle display in Clinician view |

**Interview Point:** "The output follows FHIR R4 with proper Patient, Observation, and RiskAssessment resources that could integrate with NHS Spine or GP systems."

---

## 📋 4. NHS DATA GOVERNANCE & AUDIT

**What it is:** Compliance with NHS data protection and traceability requirements.

| File | Lines | Feature |
|------|-------|---------|
| `src/xai_explanations.py` | 53-68 | **AuditEntry dataclass** - timestamps, event types, hashes |
| `src/xai_explanations.py` | 96-102 | **Input hashing** - SHA-256 for data integrity |
| `src/xai_explanations.py` | 440-500 | **Audit trail generation** - processing events |
| `app.py` | 1065-1095 | **Auditor View** - Processing trace display |
| `app.py` | 1100-1140 | **Export functionality** - JSON audit data |
| `app.py` | 270-300 | **Disclaimer banner** - non-clinical use warning |

**Interview Point:** "Every decision is timestamped and logged, with input hashes for data integrity - essential for MHRA compliance and NHS IG Toolkit."

---

## ✅ 5. DATA VALIDATION (Pydantic)

**What it is:** Type-safe data models with automatic validation.

| File | Lines | Model |
|------|-------|-------|
| `src/data_models.py` | 24-65 | **Symptom** - validated symptom with severity 0-10 |
| `src/data_models.py` | 67-110 | **PatientScreening** - validated patient input |
| `src/data_models.py` | 112-170 | **RMDAssessment** - validated AI output |

**Interview Point:** "Pydantic ensures data integrity - if severity is outside 0-10 range, it's rejected before processing. Critical for healthcare where bad data = bad decisions."

---

## 🎨 6. STREAMLIT (Web Interface)

**What it is:** Python framework for interactive web applications.

| File | Lines | Feature |
|------|-------|---------|
| `app.py` | 35-250 | CSS styling and layout |
| `app.py` | 290-380 | **Role selection screen** |
| `app.py` | 385-500 | **Sidebar** with role switching |
| `app.py` | 555-780 | **Screening form** - dynamic checkboxes/sliders |
| `app.py` | 820-1140 | **Results display** - tabs, metrics, charts |

---

## 📊 Summary: What Happens Where

```
User Input (Streamlit Form)
    ↓
Data Validation (Pydantic)
    ↓
┌─────────────────────────────────────┐
│      AGENTIC AI (LangGraph)         │
│  ┌─────────────────────────────┐    │
│  │ Tool 1: Inflammatory Analysis│    │
│  │ Tool 2: Joint Pattern        │    │
│  │ Tool 3: Systemic Symptoms    │    │
│  │ Tool 4: Risk Calculator      │    │
│  │ Tool 5: Differential Dx      │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
    ↓
XAI Explanation Generator
    ↓
┌─────────────────────────────────────┐
│         OUTPUT FORMATS              │
│  • FHIR R4 Bundle (Interop)        │
│  • Clinician Summary (Technical)    │
│  • Patient Summary (Plain)          │
│  • Auditor Log (Compliance)         │
└─────────────────────────────────────┘
```

---

## 🎯 Quick Reference for Interview

| When They Ask About... | Point to... |
|------------------------|-------------|
| "How does the AI decide?" | `src/rmd_agent.py` - ReAct agent with 5 tools |
| "How is it explainable?" | `src/xai_explanations.py` - LIME/SHAP + counterfactuals |
| "NHS integration?" | `src/fhir_resources.py` - FHIR R4 bundle |
| "Regulatory compliance?" | Auditor view - audit trails, timestamps |
| "Data safety?" | `src/data_models.py` - Pydantic validation |
| "Different users?" | Role selection - 3 tailored XAI views |
