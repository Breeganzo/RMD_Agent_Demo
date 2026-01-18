# 🏥 RMD-Health Screening Agent

<div align="center">

![RMD-Health Banner](https://img.shields.io/badge/RMD--Health-AI%20Screening%20Agent-667eea?style=for-the-badge&logo=heart&logoColor=white)

**An AI-powered Clinical Decision Support prototype demonstrating Explainable AI (XAI) for early detection of Rheumatic and Musculoskeletal Diseases**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-Agent-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com/)
[![FHIR R4](https://img.shields.io/badge/FHIR-R4-FF6B35?style=flat-square&logo=databricks&logoColor=white)](https://www.hl7.org/fhir/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [XAI Approach](#-explainable-ai-approach) • [Demo](#-running-the-demo)

</div>

---

## ⚠️ IMPORTANT DISCLAIMER

> **🚨 DEMONSTRATION PROTOTYPE ONLY**
> 
> This application is a **proof-of-concept demonstration** built for educational and interview purposes.
> It is **NOT intended for clinical use**, real patient data, or actual medical decision-making.
> 
> **Do NOT use this for real medical assessments.** Always consult qualified healthcare professionals.

---

## 🎯 Purpose

This project was built as a demonstration for the **AI Software Engineer** role interview at the **University of Reading** for the **RMD-Health project** (NIHR206473).

It showcases how modern AI technologies can be applied to healthcare while maintaining:
- **Transparency** through Explainable AI
- **Compliance** with healthcare data standards (FHIR R4)
- **Trust** through role-appropriate explanations
- **Auditability** for regulatory requirements

---

## ✨ Features

### 🤖 Agentic AI Architecture
- **LangChain ReAct Agent** - The AI autonomously decides which analysis tools to use
- **Tool-based Architecture** - Modular, extensible clinical analysis tools
- **Free LLM Integration** - Uses Groq's free tier (Llama 3.1)
- **Fallback Mode** - Works offline with rule-based analysis

### 🔍 Explainable AI (XAI)
- **Role-Based Explanations** - Different views for clinicians, patients, and auditors
- **LIME/SHAP-style Contributions** - Visual feature importance with contribution scores
- **Reasoning Traces** - Step-by-step agent decision-making (ReAct pattern)
- **Counterfactual Explanations** - "What would change the outcome?"
- **Audit Trails** - Complete decision logging for compliance

### 🏥 Healthcare Standards
- **FHIR R4 Compliance** - Proper HL7 FHIR resources (Patient, Observation, RiskAssessment)
- **SNOMED CT Ready** - Structured for clinical coding integration
- **NHS-Aligned** - Follows UK healthcare terminology and guidelines

### 👥 Multi-Stakeholder Design

| User Role | Explanation Style | Key Features |
|-----------|------------------|--------------|
| **👨‍⚕️ Clinician** | Technical, evidence-based | Clinical terminology, guideline references, reasoning traces |
| **🧑‍🤝‍🧑 Patient** | Simple, reassuring | Plain language, clear next steps, support resources |
| **📋 Auditor** | Complete audit trail | Timestamps, hashes, decision factors, export capabilities |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT WEB INTERFACE                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │  Clinician  │  │   Patient   │  │   Auditor   │  ← Role Selection       │
│  │    View     │  │    View     │  │    View     │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    XAI EXPLANATION ENGINE                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ Feature          │  │ Reasoning        │  │ Counterfactual   │          │
│  │ Contributions    │  │ Traces           │  │ Analysis         │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LANGCHAIN ReAct AGENT                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LLM (Groq - Llama 3.1)  →  AUTONOMOUSLY DECIDES which tools to use │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                             │                                               │
│           ┌─────────────────┼─────────────────────────────┐                │
│           ▼                 ▼                             ▼                │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ analyze_inflam-  │ │ analyze_joint_   │ │ calculate_risk_  │           │
│  │ matory_markers   │ │ pattern          │ │ score            │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│           ▼                 ▼                                              │
│  ┌──────────────────┐ ┌──────────────────┐                                │
│  │ analyze_systemic │ │ get_differential │                                │
│  │ _symptoms        │ │ _diagnosis       │                                │
│  └──────────────────┘ └──────────────────┘                                │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FHIR R4 OUTPUT BUNDLE                                     │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────┐             │
│  │   Patient    │  │   Observation   │  │   RiskAssessment   │             │
│  │   Resource   │  │   Resources     │  │   Resource         │             │
│  └──────────────┘  └─────────────────┘  └────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Explainable AI Approach

This demo implements multiple XAI techniques aligned with healthcare regulatory requirements:

### 1. Feature Contributions (LIME/SHAP-style)
Shows how each symptom/factor contributes to the risk assessment:

```
┌─────────────────────────────────────────────────────────────────┐
│ Feature Contribution Analysis                                    │
├─────────────────────────────────────────────────────────────────┤
│ Multiple Joints Affected  ████████████████████  +0.25           │
│ Morning Stiffness        ████████████████      +0.20           │
│ Joint Swelling           ██████████████        +0.18           │
│ Age (52 years)           ████                  +0.10           │
└─────────────────────────────────────────────────────────────────┘
```

### 2. ReAct Reasoning Traces
Captures the agent's step-by-step clinical reasoning:

```
Step 1: THOUGHT
"I need to analyze inflammatory markers because the patient has joint pain."

Step 2: ACTION → analyze_inflammatory_markers
OBSERVATION: "Joint swelling present - indicates active inflammation"

Step 3: THOUGHT  
"Inflammatory signs confirmed. Let me check the joint pattern..."
```

### 3. Role-Appropriate Explanations

**For Clinicians:**
> "Elevated inflammatory markers (joint swelling, prolonged morning stiffness >30min) 
> combined with symmetric polyarticular involvement strongly suggests inflammatory 
> arthritis, most likely RA. Recommend referral per NICE NG100 guidelines."

**For Patients:**
> "Your symptoms suggest we should have a specialist take a closer look. This doesn't 
> mean anything is definitely wrong – it means we want to make sure you get the right 
> care. Your GP will arrange a referral to a rheumatologist."

### 4. Counterfactual Explanations
```
"The risk level would be MODERATE if morning stiffness lasted less than 30 minutes."
"If joint swelling was not present, the assessment would likely be LOW risk."
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone or navigate to the project
cd RMD_Agent_Demo

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up API key for full AI mode
cp .env.example .env
# Edit .env and add your FREE Groq API key
```

### Get Your FREE API Key (Optional)

The app works in **Demo Mode** without any API key. For full AI-powered assessment:

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up with Google or GitHub (completely FREE!)
3. Create a new API key
4. Add it to your `.env` file:
   ```
   GROQ_API_KEY=gsk_your_actual_api_key_here
   ```

---

## ▶️ Running the Demo

```bash
# Start the application
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Demo Walkthrough

1. **Select Your Role** - Choose Clinician, Patient, or Auditor
2. **Enter Symptoms** - Use the form or load sample data (High/Low Risk)
3. **Run Assessment** - Click the assessment button
4. **Explore XAI** - Navigate through role-specific explanation tabs

### Sample Scenarios

**High Risk Example:**
- 52-year-old female
- Multiple joints affected with swelling
- Morning stiffness lasting 75+ minutes
- Family history of RA

**Low Risk Example:**
- 32-year-old male
- Occasional knee pain after exercise
- No inflammatory signs
- Active lifestyle

---

## 📁 Project Structure

```
RMD_Agent_Demo/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
├── README.md                  # This file
│
├── src/
│   ├── __init__.py            # Package initialization
│   ├── data_models.py         # Pydantic data models (FHIR-inspired)
│   ├── fhir_resources.py      # FHIR R4 resource generation
│   ├── prompts.py             # LLM system & user prompts
│   ├── rmd_agent.py           # LangChain ReAct agent implementation
│   ├── utils.py               # Utility functions
│   └── xai_explanations.py    # Explainable AI module ⭐ NEW
│
├── sample_data/
│   └── example_patient.json   # Sample patient data
│
└── docs/
    ├── ARCHITECTURE.md        # System architecture details
    ├── FHIR_MAPPING.md        # FHIR resource mapping guide
    └── ...
```

---

## 🔧 Technology Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.10+** | Core language | Type hints, modern syntax |
| **Streamlit** | Web interface | Rapid prototyping, healthcare-friendly |
| **LangChain** | Agent framework | ReAct pattern, tool orchestration |
| **LangGraph** | Agent execution | Stateful, observable agent runs |
| **Groq** | LLM inference | FREE tier, fast inference |
| **Pydantic** | Data validation | Type safety, FHIR alignment |
| **FHIR R4** | Healthcare standard | NHS interoperability |

---

## 📊 Key Concepts Demonstrated

### For Interview Discussion

1. **Agentic AI**
   - ReAct pattern (Reasoning + Acting)
   - Tool-based architecture
   - LLM-driven decision making

2. **Explainable AI (XAI)**
   - LIME/SHAP concepts
   - Reasoning traces
   - Multi-stakeholder explanations

3. **Healthcare AI Compliance**
   - FHIR R4 data standards
   - Audit trail requirements
   - Regulatory considerations (MHRA, DTAC)

4. **Software Engineering**
   - Clean architecture
   - Type safety with Pydantic
   - Modular design

---

## 🔒 Regulatory Considerations

This demo demonstrates awareness of healthcare AI requirements:

| Requirement | Implementation |
|-------------|----------------|
| **Transparency** | Full reasoning traces, feature contributions |
| **Auditability** | Timestamped logs, input/output hashing |
| **Explainability** | Role-appropriate explanations |
| **Data Standards** | FHIR R4 compliance |
| **User Understanding** | Tested explanation formats |

**Note:** A production system would require full MHRA/MDR certification, clinical validation, and extensive testing.

---

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [FHIR Mapping Guide](docs/FHIR_MAPPING.md)
- [Interview Q&A](docs/INTERVIEW_QA.md)
- [Speaking Guide](docs/SPEAKING_GUIDE.md)

---

## 🙏 Acknowledgments

Built for the University of Reading RMD-Health Project interview demonstration.

- **RMD-Health Project** - NIHR206473
- **LangChain** - Agent framework
- **Groq** - Free LLM API
- **Streamlit** - UI framework

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for Healthcare AI**

*This is a demonstration prototype. Not for clinical use.*

</div>
