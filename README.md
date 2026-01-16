# 🩺 RMD-Health Screening Agent

An AI-powered clinical decision support prototype for early detection of **Rheumatic and Musculoskeletal Diseases (RMDs)**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚠️ IMPORTANT DISCLAIMER

> **This is a DEMONSTRATION PROTOTYPE only.**  
> It is NOT intended for clinical use, real patient data, or actual medical decision-making.  
> This application was created for educational and interview demonstration purposes.  
> Any outputs should NOT be considered medical advice.  
> Always consult qualified healthcare professionals for medical concerns.

---

## 🎯 Purpose

This project demonstrates an AI-enabled clinical decision support system for the early detection and referral of patients with suspected rheumatic and musculoskeletal diseases (RMDs). It was built as a demonstration for the **AI Software Engineer** role interview at the **University of Reading** for the **RMD-Health project** (NIHR206473).

## ✨ Features

- **🤖 Agentic AI**: Uses LLM + tools pattern for robust clinical reasoning
- **📊 FHIR-Inspired Data Models**: Structured data aligned with healthcare standards
- **🔍 Explainable AI**: Transparent reasoning with red flag identification
- **🎨 Clean Web Interface**: User-friendly Streamlit application
- **⚡ Demo Mode**: Works without API key using rule-based analysis
- **🚀 Easy Deployment**: Ready for Hugging Face Spaces

## 🖼️ Screenshot

```
┌─────────────────────────────────────────────────────────────────┐
│  🩺 RMD-Health Screening Agent                                  │
├─────────────────────────────────────────────────────────────────┤
│  ⚠️ IMPORTANT DISCLAIMER                                        │
│  This is a DEMONSTRATION PROTOTYPE only...                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Patient Screening Form                                      │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Age: [45]       │  │ Sex: [Female ▼] │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                 │
│  🦴 Joint Symptoms                                              │
│  [✓] Joint Pain         Severity: [7/10]                       │
│  [✓] Multiple Joints    [✓] Morning Stiffness (60 min)        │
│                                                                 │
│  🔴 Inflammatory Signs                                          │
│  [✓] Joint Swelling     [✓] Joint Redness                      │
│                                                                 │
│  [🔍 Run RMD Screening Assessment]                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  📊 Assessment Results                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔴 Risk Level: HIGH                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│  Confidence: 85%  |  Conditions: 3  |  Red Flags: 4            │
│                                                                 │
│  🏥 Possible Conditions: Rheumatoid Arthritis, Inflammatory... │
│  ⚠️ Red Flags: Polyarticular involvement, Morning stiffness... │
│  📋 Next Step: Urgent rheumatology referral recommended        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rmd-health-agent.git
cd rmd-health-agent

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your xAI API key (optional - demo mode works without it)
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 🔑 API Key Setup (Optional)

The application works in **Demo Mode** without an API key, using rule-based analysis.

For full AI-powered assessment, get a free xAI API key:

1. Go to [https://console.x.ai/](https://console.x.ai/)
2. Sign up with your X (Twitter) account
3. Create a new API key
4. Add it to your `.env` file:
   ```
   XAI_API_KEY=your_api_key_here
   ```

## 📁 Project Structure

```
rmd-health-agent/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── src/
│   ├── __init__.py           # Package initialization
│   ├── data_models.py        # Pydantic data models (FHIR-inspired)
│   ├── prompts.py            # LLM system & user prompts
│   ├── rmd_agent.py          # Agentic AI logic
│   └── utils.py              # Utility functions
├── sample_data/
│   └── example_patient.json  # Sample patient data for testing
└── docs/
    ├── ARCHITECTURE.md       # System architecture documentation
    ├── FHIR_MAPPING.md       # FHIR resource mapping guide
    ├── ABOUT_RMD.md          # RMD disease background
    ├── HOW_TO_RUN.md         # Detailed running guide
    ├── WHAT_IS_DONE.md       # Project summary
    └── INTERVIEW_QA.md       # Interview Q&A preparation
```

## 🏗️ Architecture

```
User Browser → Streamlit UI → Agentic AI Layer → Grok LLM API
                    ↑               ↑
              Pydantic Models   Pattern Analysis Tools
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🏥 Healthcare Standards

This prototype aligns with FHIR (Fast Healthcare Interoperability Resources):

- **PatientScreening** → FHIR Patient + Encounter + Bundle
- **Symptom** → FHIR Observation
- **RMDAssessment** → FHIR RiskAssessment

See [docs/FHIR_MAPPING.md](docs/FHIR_MAPPING.md) for detailed mappings.

## 🌐 Deploying to Hugging Face Spaces

### Step 1: Create a Space

1. Go to [huggingface.co](https://huggingface.co/)
2. Click New → Space
3. Choose Streamlit SDK
4. Name it `rmd-health-agent`

### Step 2: Add Space Configuration

The repository already includes proper configuration. Just ensure your README has:

```yaml
---
title: RMD-Health Screening Agent
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
---
```

### Step 3: Add API Key Secret

1. Go to Space → Settings → Repository Secrets
2. Add `XAI_API_KEY` with your API key

### Step 4: Push Code

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/rmd-health-agent
# Copy all files to the cloned directory
git add .
git commit -m "Initial commit"
git push
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and component overview |
| [FHIR_MAPPING.md](docs/FHIR_MAPPING.md) | Healthcare data standard alignment |
| [ABOUT_RMD.md](docs/ABOUT_RMD.md) | RMD disease background and approach |
| [HOW_TO_RUN.md](docs/HOW_TO_RUN.md) | Detailed setup and improvement guide |
| [WHAT_IS_DONE.md](docs/WHAT_IS_DONE.md) | Project summary |
| [INTERVIEW_QA.md](docs/INTERVIEW_QA.md) | Interview preparation Q&A |

## 🛠️ Technologies Used

- **Python 3.10+** - Core language
- **Streamlit** - Web interface
- **Pydantic v2** - Data validation
- **xAI Grok API** - LLM inference
- **Requests** - HTTP client
- **python-dotenv** - Environment management

## 🤝 Relevance to RMD-Health Project

This demo addresses key job requirements:

| Requirement | Implementation |
|-------------|----------------|
| AI/ML integration | Agentic AI with LLM reasoning |
| FHIR interoperability | FHIR-inspired data models |
| Software engineering | Clean architecture, modular code |
| Explainable AI | Transparent reasoning, red flags |
| NHS context | SNOMED mappings, referral pathways |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Created for the AI Software Engineer role interview at University of Reading, RMD-Health Project (NIHR206473).

---

<p align="center">
  <strong>⚠️ DEMONSTRATION PROTOTYPE - NOT FOR CLINICAL USE ⚠️</strong>
</p>
