# How to Run This Code

## 📋 Prerequisites

Before running this application, ensure you have:

- **Python 3.10+** installed
- **pip** (Python package manager)
- **Git** (for version control)
- A **xAI API Key** (free tier available at https://console.x.ai/)

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone/Download the Repository

```bash
# If you have the folder locally, navigate to it
cd rmd-health-agent

# Or clone from GitHub
git clone https://github.com/YOUR_USERNAME/rmd-health-agent.git
cd rmd-health-agent
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your xAI API key
# On Windows, use notepad:
notepad .env

# On macOS/Linux, use any editor:
nano .env
```

Your `.env` file should look like:
```
XAI_API_KEY=xai-your-actual-api-key-here
XAI_MODEL=grok-beta
XAI_BASE_URL=https://api.x.ai/v1
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 🔑 Getting a Free xAI API Key

1. Go to [https://console.x.ai/](https://console.x.ai/)
2. Sign up or log in with your X (Twitter) account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

**Note**: The free tier has rate limits but is sufficient for demo purposes.

## 🎮 Using the Application

### Demo Mode (No API Key Required)

If you don't have an API key, the application automatically runs in **Demo Mode**:
- Uses rule-based pattern analysis only
- No LLM calls are made
- Results are less sophisticated but functional

### Full Mode (With API Key)

With a valid API key:
1. Fill in the patient screening form
2. Click "Run RMD Screening Assessment"
3. Wait for the AI to analyze (takes 5-10 seconds)
4. View the detailed assessment results

### Quick Load Sample Patients

Use the sidebar buttons to quickly load sample patient data:
- **High-Risk Example**: Inflammatory arthritis pattern
- **Low-Risk Example**: Mechanical joint pain pattern

## 🐛 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'streamlit'"
```bash
# Make sure you activated the virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. "XAI_API_KEY environment variable is not set"
- Ensure you created the `.env` file (not `.env.example`)
- Check that the API key is correctly formatted
- Restart the Streamlit server after changing `.env`

#### 3. "API request failed: 401 Unauthorized"
- Your API key may be invalid or expired
- Generate a new key at https://console.x.ai/

#### 4. "API request timed out"
- Check your internet connection
- The Grok API may be experiencing high load
- Try again in a few minutes

#### 5. Port 8501 already in use
```bash
# Run on a different port
streamlit run app.py --server.port 8502
```

## 🌐 Deploying to Hugging Face Spaces

### Step 1: Create a Hugging Face Account
Go to [huggingface.co](https://huggingface.co/) and sign up.

### Step 2: Create a New Space
1. Click on your profile → New Space
2. Choose a name (e.g., `rmd-health-agent`)
3. Select **Streamlit** as the SDK
4. Choose **Public** or **Private**

### Step 3: Configure the Space

Create a `README.md` file (or update existing) with Space metadata at the top:

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

### Step 4: Add Your API Key as a Secret

1. Go to your Space → Settings → Repository secrets
2. Add a new secret: `XAI_API_KEY` with your API key value

### Step 5: Upload Files

You can either:
- **Git**: Clone the Space repo and push your files
- **Web UI**: Upload files directly through the browser

```bash
# Using Git
git clone https://huggingface.co/spaces/YOUR_USERNAME/rmd-health-agent
cp -r your-local-files/* rmd-health-agent/
cd rmd-health-agent
git add .
git commit -m "Initial commit"
git push
```

### Step 6: Wait for Build

Hugging Face will automatically build and deploy your app. This takes 2-5 minutes.

## 📈 How to Make This Better

### Short-Term Improvements

#### 1. Add Unit Tests
```python
# tests/test_data_models.py
import pytest
from src.data_models import PatientScreening, Symptom

def test_patient_screening_creation():
    patient = PatientScreening(age=45, sex="Female", symptoms=[])
    assert patient.age == 45
    assert patient.patient_id is not None

def test_symptom_validation():
    symptom = Symptom(name="joint_pain", present=True, severity=7)
    assert symptom.severity == 7
```

#### 2. Add Input Validation
- Age range validation with meaningful errors
- Required field indicators
- Form completion progress indicator

#### 3. Improve Error Messages
- User-friendly error displays
- Specific guidance on how to resolve issues
- Contact/support information

#### 4. Add Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting assessment for patient %s", patient.patient_id)
```

### Medium-Term Improvements

#### 1. Multiple LLM Support
```python
# src/llm_providers.py
class LLMProvider:
    def chat(self, messages: list) -> str:
        raise NotImplementedError

class GrokProvider(LLMProvider):
    def chat(self, messages: list) -> str:
        # Grok implementation
        pass

class OpenAIProvider(LLMProvider):
    def chat(self, messages: list) -> str:
        # OpenAI implementation
        pass
```

#### 2. Session History
- Track assessments within a session
- Allow comparison between patients
- Export assessment history

#### 3. Enhanced Visualizations
- Symptom severity radar charts
- Risk trend over time
- Condition probability distributions

#### 4. Caching
```python
import streamlit as st

@st.cache_data(ttl=3600)
def get_cached_assessment(patient_hash: str) -> RMDAssessment:
    # Cache expensive LLM calls
    pass
```

### Long-Term / Production Improvements

#### 1. NHS Integration
- Connect to NHS Spine for patient lookup
- Integrate with e-Referral Service
- Use NHS Login for authentication

#### 2. FHIR API
- Generate actual FHIR resources
- Implement FHIR R4 endpoints
- Support Bulk FHIR exports

#### 3. Regulatory Compliance
- Implement audit logging (ISO 13485)
- Add data retention policies
- Document clinical safety (DCB0129)
- Prepare for UKCA marking

#### 4. Machine Learning Enhancements
- Add traditional ML models alongside LLM
- Ensemble predictions for robustness
- Uncertainty quantification
- Active learning from clinician feedback

#### 5. Performance Optimization
- Async API calls
- Background processing
- Database for session persistence
- Container orchestration (Kubernetes)

## 🧪 Running Tests

If you add tests:

```bash
# Install pytest
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📊 Performance Profiling

```bash
# Install profiler
pip install streamlit-profiler

# Run with profiling
streamlit run app.py --server.runOnSave true
```

## 🔒 Security Checklist

Before deploying to production:

- [ ] API keys stored as environment secrets (never in code)
- [ ] No real patient data in the repository
- [ ] Input sanitization for all form fields
- [ ] Rate limiting implemented
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Dependencies audited for vulnerabilities (`pip-audit`)

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes with tests
4. Run linting (`black .`, `flake8 .`)
5. Commit with meaningful messages
6. Push and create a Pull Request

## 🆘 Getting Help

- Open an issue on GitHub
- Check Streamlit documentation: https://docs.streamlit.io/
- xAI API documentation: https://docs.x.ai/
- FHIR specification: https://www.hl7.org/fhir/
