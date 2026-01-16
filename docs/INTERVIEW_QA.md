# Interview Questions & Answers

## About This Document

This document contains potential interview questions and suggested answers for the **AI Software Engineer** role on the **RMD-Health project** at the University of Reading. The questions cover technical skills, domain knowledge, and the demonstration project.

---

## 🎯 Project-Specific Questions

### Q1: Can you walk me through the architecture of your RMD-Health demo?

**Answer:**
"The RMD-Health Screening Agent follows a layered architecture with clear separation of concerns:

1. **User Interface Layer** (Streamlit): Handles all user interactions through a web-based form. It collects patient symptoms, validates inputs, and displays assessment results with appropriate visual styling.

2. **Data Models Layer** (Pydantic): Defines structured schemas that are inspired by FHIR healthcare standards. The main models are PatientScreening (representing the screening encounter), Symptom (individual observations), and RMDAssessment (the AI output).

3. **Agentic AI Layer**: This is where the intelligence lives. The RMDScreeningAgent class orchestrates the assessment workflow:
   - First, it runs pattern analysis tools to identify clinical red flags
   - Then it constructs a prompt combining patient data with tool outputs
   - It calls the LLM (Grok API) for clinical reasoning
   - Finally, it parses and validates the JSON response

4. **External Services**: We integrate with xAI's Grok API for LLM inference. The architecture is designed to be provider-agnostic, making it easy to swap in other LLMs.

The key design decision was the **agentic pattern** - rather than just sending data to an LLM, we pre-process it with specialized tools and post-process the response with validation. This gives us better explainability and reliability."

---

### Q2: Why did you choose an agentic AI approach rather than a simpler LLM call?

**Answer:**
"I chose the agentic approach for several important reasons:

1. **Explainability**: In healthcare, clinicians need to understand *why* a recommendation was made. By separating the pattern analysis tools from the LLM reasoning, we can show exactly which patterns were detected and how they influenced the assessment.

2. **Reliability**: Pure LLM calls can be unpredictable. By having structured tools that run deterministically, we have a fallback if the LLM fails. The pattern analysis tool gives us a basic assessment even without the LLM.

3. **Modularity**: As the RMD-Health project evolves, we'll need to add new capabilities - perhaps lab value analysis, imaging integration, or different referral pathways. The agentic pattern lets us add these as new tools without rewriting the core logic.

4. **Compliance**: For medical device software, we need to demonstrate control over the system's behavior. Having explicit tools with defined inputs and outputs makes it easier to document and validate for regulatory purposes.

5. **Domain Knowledge Injection**: The tools encode specific clinical knowledge (like 'morning stiffness > 30 minutes suggests inflammatory arthritis') that might not be reliably present in a general-purpose LLM."

---

### Q3: How do your data models align with FHIR?

**Answer:**
"While this is a prototype that doesn't generate actual FHIR resources, the data models are designed with FHIR alignment in mind:

**PatientScreening** maps to multiple FHIR resources:
- The demographic data (age, sex) maps to a **FHIR Patient** resource
- The screening session maps to a **FHIR Encounter**
- The collection of symptoms would be a **FHIR Bundle** of Observations

**Symptom** maps to a **FHIR Observation**:
- The `name` field would use SNOMED CT codes in production (e.g., joint_pain → 57676002)
- `present` maps to `valueBoolean`
- `severity` and `duration_days` would be `Observation.component` elements

**RMDAssessment** maps to **FHIR RiskAssessment**:
- `risk_level` maps to `prediction.qualitativeRisk`
- `likely_conditions` maps to `prediction.outcome`
- `confidence_score` maps to `prediction.probabilityDecimal`
- `reasoning` maps to the `note` element
- `recommended_next_step` maps to `mitigation`

In a production NHS integration, we'd generate actual FHIR resources using UK Core profiles and submit them to the e-Referral Service via their FHIR API."

---

### Q4: How would you ensure this system is safe for clinical use?

**Answer:**
"For clinical safety, I would implement multiple layers of protection:

1. **Clear Disclaimers**: The system is explicit that it supports, not replaces, clinical judgment. All outputs include warnings.

2. **Conservative Defaults**: When in doubt, the system errs on the side of caution - recommending referral rather than dismissal.

3. **Fallback Mechanisms**: If the AI fails, we have rule-based fallbacks that still provide a basic assessment.

4. **Structured Outputs**: By forcing JSON schema validation, we prevent malformed or unexpected outputs from reaching users.

5. **Audit Trail**: In production, every assessment would be logged with full inputs, outputs, and timestamps for clinical governance.

6. **Clinical Validation**: Before deployment, the system would need prospective validation against clinician decisions and patient outcomes.

7. **Regulatory Compliance**: As a clinical decision support system, it would be classified as a medical device and need UKCA marking. This requires following standards like ISO 13485 for quality management and DCB0129 for clinical safety.

8. **Human-in-the-Loop**: The design always places a clinician between the AI output and any patient action."

---

## 🔧 Technical Skills Questions

### Q5: How do you handle errors and edge cases in your LLM integration?

**Answer:**
"Error handling is critical for healthcare applications. My approach includes:

1. **Try-Except Blocks**: All API calls are wrapped with specific exception handling for timeouts, HTTP errors, and network issues.

2. **JSON Parsing Robustness**: The `extract_json_from_response()` function handles multiple response formats - pure JSON, markdown code blocks, or JSON embedded in text.

3. **Schema Validation**: Before creating the RMDAssessment object, I validate that all required fields exist and have correct types.

4. **Graceful Degradation**: If the LLM fails, `create_fallback_assessment()` generates a conservative assessment using rule-based logic. The patient still gets an output.

5. **User Feedback**: Errors are displayed to users in a friendly way with guidance on next steps, not raw stack traces.

6. **Retry Logic**: For transient errors (like timeouts), we could add automatic retries with exponential backoff - I didn't implement this in the demo but would in production."

---

### Q6: Explain how you'd integrate with NHS e-Referral Service APIs.

**Answer:**
"NHS e-Referral Service (e-RS) integration would involve several components:

1. **Authentication**: e-RS uses OAuth 2.0 with NHS Identity. We'd need to implement the authorization code flow and securely store tokens.

2. **FHIR Resources**: e-RS accepts FHIR R4 resources. Our RMDAssessment would be converted to a ServiceRequest resource with the RiskAssessment as a supporting document.

3. **Endpoints**:
   - `POST /ServiceRequest` to create a new referral
   - `GET /ServiceRequest/{id}` to check status
   - `POST /DocumentReference` to attach clinical documents

4. **Validation**: Before submission, we'd validate against NHS Digital's FHIR validation service to ensure compliance with UK Core profiles.

5. **Error Handling**: e-RS returns detailed OperationOutcome resources on errors. We'd need to parse these and present meaningful feedback.

6. **Audit**: All API interactions would be logged with timestamps, user IDs, and patient identifiers for governance.

The job spec mentions experience with NHS national e-referral services API - this would be directly relevant to that requirement."

---

### Q7: What's your experience with FHIR and HL7 standards?

**Answer:**
"I have experience with healthcare interoperability standards:

**FHIR (Fast Healthcare Interoperability Resources)**:
- I understand the resource model - Patient, Observation, Condition, etc.
- I've worked with FHIR bundles for transactional data exchange
- I'm familiar with UK Core profiles that add NHS-specific requirements
- I've used FHIR search parameters and the RESTful API pattern

**HL7 v2**:
- I understand the segment-based message format (MSH, PID, OBR, OBX)
- I know it's still widely used in NHS trusts for lab and radiology messaging

**SNOMED CT and ICD-10**:
- I can map clinical concepts to standardized codes
- I understand the importance of consistent terminology for interoperability

In this demo, I designed the data models to be easily mappable to FHIR, with comments explaining the correspondence. This would make the transition to actual FHIR integration straightforward."

---

### Q8: How would you approach implementing explainable AI features?

**Answer:**
"Explainability is crucial for clinical AI. My approach involves:

1. **Transparent Reasoning**: The LLM is instructed to provide detailed reasoning in natural language. This is exposed directly to users rather than hidden.

2. **Red Flag Identification**: The system explicitly lists which clinical red flags were detected, so clinicians can verify the AI's observations.

3. **Confidence Scoring**: Every assessment includes a confidence score, helping users understand the AI's certainty level.

4. **Tool Outputs**: Because we use an agentic approach, the pattern analysis tool outputs are available for inspection - showing exactly what rules triggered.

5. **Feature Attribution**: In a more sophisticated version, we could implement techniques like SHAP or LIME to show which input features most influenced the output.

6. **Audit Logs**: Complete input-output pairs are preserved, allowing post-hoc review of any decision.

7. **Contrastive Explanations**: Explaining why a HIGH risk was assigned vs. MODERATE - 'Because morning stiffness exceeded 60 minutes and multiple joints were affected...'

The goal is that a clinician should be able to read the AI's reasoning and agree or disagree based on their clinical judgment."

---

## 🏥 Domain Knowledge Questions

### Q9: What clinical red flags indicate a patient needs urgent rheumatology referral?

**Answer:**
"Based on NICE guidelines and clinical best practices, key red flags for urgent referral include:

1. **Morning Stiffness > 30-60 minutes**: Prolonged morning stiffness that improves with activity suggests inflammatory arthritis rather than mechanical causes.

2. **Polyarticular Involvement**: Three or more joints affected, especially if symmetric, suggests systemic inflammatory disease.

3. **Joint Swelling with Warmth/Redness**: Objective signs of inflammation rather than just pain.

4. **Rapid Onset with Systemic Symptoms**: Fever, weight loss, or fatigue alongside joint symptoms may indicate serious conditions like septic arthritis or vasculitis.

5. **Small Joint Involvement**: Inflammation in hands and feet, particularly MCP and PIP joints, is classic for RA.

6. **Skin/Nail Changes with Arthritis**: Suggests psoriatic arthritis.

7. **Symptoms in Young Adults + Back Pain**: Inflammatory back pain in under-40s could indicate ankylosing spondylitis.

8. **Elderly with Sudden Shoulder/Hip Symptoms**: Consider polymyalgia rheumatica and the associated risk of giant cell arteritis.

The key message is that early referral for inflammatory arthritis (within 12 weeks) significantly improves outcomes by allowing treatment before irreversible joint damage occurs."

---

### Q10: What's the 'window of opportunity' in rheumatoid arthritis?

**Answer:**
"The 'window of opportunity' refers to the critical period in early rheumatoid arthritis - typically the first 12 weeks from symptom onset - where aggressive treatment can significantly alter the disease course.

During this window:
- Joint damage hasn't become irreversible
- The disease is most responsive to disease-modifying drugs (DMARDs)
- Patients have the best chance of achieving remission

Research shows that patients treated within this window have:
- Higher rates of drug-free remission
- Less radiographic progression
- Better functional outcomes
- Lower healthcare costs long-term

This is exactly why early detection tools like RMD-Health are so valuable - they help identify patients who need urgent referral before this window closes. Current NHS pathways often take 6-12 months from symptom onset to rheumatology appointment, by which time significant joint damage may have occurred.

The AI system I've built specifically prioritizes identifying patients who need urgent referral to catch them within this window."

---

## 👥 Team & Collaboration Questions

### Q11: How would you work with clinicians and patient representatives on this project?

**Answer:**
"Effective collaboration with clinical partners is essential:

1. **Regular Stakeholder Meetings**: I'd participate in cross-disciplinary meetings with clinicians from RBFT and OUH to understand their workflows and requirements.

2. **Clinical Validation Sessions**: Present system outputs to clinicians, gather feedback on clinical accuracy, and iterate on the prompts and logic.

3. **User Research**: Work with PPI (Patient and Public Involvement) representatives to ensure the system is accessible and addresses real patient needs.

4. **Pilot Testing**: Deploy in a controlled clinical setting, collect feedback, and refine based on real-world usage.

5. **Documentation**: Create clear technical documentation that clinical collaborators can understand, and ensure clinical requirements are captured in technical specifications.

6. **Humble Approach**: I'm a software engineer, not a clinician. I'd always defer to clinical expertise on medical questions and ensure the system supports rather than overrides clinical judgment.

The job description emphasizes multi-disciplinary teamwork - I see this as one of the most important aspects of the role."

---

### Q12: How do you stay current with AI developments relevant to healthcare?

**Answer:**
"I maintain currency through multiple channels:

1. **Research Papers**: I follow arXiv.org for preprints, particularly the cs.AI, cs.CL, and cs.LG categories. For healthcare AI, I track journals like Nature Medicine and npj Digital Medicine.

2. **Industry Updates**: I follow developments from NHS Digital, NHSX, and the MHRA on healthcare AI regulation.

3. **Conferences**: I follow NeurIPS, ICML, and specialized conferences like CHIL (Conference on Health, Inference, and Learning).

4. **LLM Developments**: I track new model releases and capabilities from OpenAI, Anthropic, Google, and xAI, evaluating how they might improve clinical AI applications.

5. **Regulatory Landscape**: I stay informed about evolving AI regulations including the EU AI Act, UK AI strategy, and MHRA guidance on AI as a Medical Device.

6. **Communities**: I participate in relevant communities like HL7 FHIR forums, NHS Digital developer communities, and healthcare AI working groups.

The field moves quickly, especially with LLMs. What was state-of-the-art six months ago may be outdated today. Continuous learning is essential."

---

## 💻 Coding & Technical Deep-Dive

### Q13: Show me how you'd add a new symptom to the screening system.

**Answer:**
"Adding a new symptom is straightforward due to the modular design:

1. **Add to Standard Symptoms List** (data_models.py):
```python
STANDARD_SYMPTOMS = [
    ...
    'new_symptom_name',
]
```

2. **Add to Form** (app.py):
```python
new_symptom = st.checkbox(
    'New Symptom Description',
    value=get_default_value('new_symptom', False)
)

symptoms.append(Symptom(
    name='new_symptom_name',
    present=new_symptom
))
```

3. **Add Pattern Analysis** (utils.py):
```python
def check_rmd_patterns(patient):
    ...
    new_symptom = patient.get_symptom('new_symptom_name')
    if new_symptom and new_symptom.present:
        patterns.append('NEW SYMPTOM: Present - clinical significance...')
```

4. **Update System Prompt** (prompts.py):
```python
SYSTEM_PROMPT = '''
...
New red flag: new_symptom_name indicates...
'''
```

5. **Add Sample Data** (example_patient.json):
```json
{
    'new_symptom': true
}
```

The key is that each component has a single responsibility, so changes are localized."

---

### Q14: How would you implement authentication for this application?

**Answer:**
"For NHS deployment, I would implement authentication using NHS Login:

1. **OAuth 2.0 / OpenID Connect**: NHS Login uses standard protocols. We'd register our application as an OIDC client.

2. **Streamlit Authentication**:
```python
import streamlit as st
from streamlit_oauth import OAuth2Component

oauth = OAuth2Component(
    client_id=os.getenv('NHS_CLIENT_ID'),
    client_secret=os.getenv('NHS_CLIENT_SECRET'),
    authorize_url='https://auth.login.nhs.uk/authorize',
    token_url='https://auth.login.nhs.uk/token'
)

if 'token' not in st.session_state:
    result = oauth.authorize_button('Login with NHS')
    if result:
        st.session_state['token'] = result['token']
        st.experimental_rerun()
else:
    # User is authenticated
    user_info = get_user_info(st.session_state['token'])
```

3. **Role-Based Access**: NHS Login provides identity vectors that indicate the user's role (clinician, admin, etc.). We'd use these for authorization.

4. **Session Management**: Implement secure session handling with appropriate timeouts.

5. **Audit Logging**: All authenticated actions would be logged with user identity for governance."

---

### Q15: What testing strategy would you use for this application?

**Answer:**
"I would implement a comprehensive testing pyramid:

1. **Unit Tests** (~70%):
```python
# test_data_models.py
def test_symptom_validation():
    with pytest.raises(ValueError):
        Symptom(name='pain', present=True, severity=11)  # >10

def test_patient_clinical_summary():
    patient = PatientScreening(age=45, sex='Female', symptoms=[])
    summary = patient.to_clinical_summary()
    assert 'Age: 45' in summary
```

2. **Integration Tests** (~20%):
```python
# test_agent.py
def test_agent_assessment_high_risk():
    patient = create_high_risk_patient()
    agent = RMDScreeningAgent()
    assessment = agent.assess(patient)
    assert assessment.risk_level == 'HIGH'
```

3. **End-to-End Tests** (~10%):
```python
# test_e2e.py
def test_full_workflow(page):
    page.goto('http://localhost:8501')
    page.fill('[data-testid=age-slider]', '45')
    page.click('[data-testid=submit-button]')
    assert page.locator('[data-testid=risk-level]').is_visible()
```

4. **Clinical Validation Tests**:
- Test against a set of 'gold standard' cases reviewed by clinicians
- Measure sensitivity and specificity
- Track false negatives (missing high-risk patients) as the most critical metric

5. **Continuous Integration**:
- Run tests on every commit
- Require passing tests before merge
- Generate coverage reports"

---

## ⚖️ Regulatory & Ethics Questions

### Q16: What regulatory considerations apply to AI medical device software?

**Answer:**
"AI clinical decision support software is regulated as a medical device in the UK:

1. **Classification**: Under UK MDR 2002 (as amended), clinical decision support software is typically Class IIa or IIb, depending on the risk level.

2. **UKCA Marking**: Required for placing the device on the UK market. This requires:
   - Quality Management System (ISO 13485)
   - Technical documentation
   - Conformity assessment by a UK Approved Body

3. **DTAC (Digital Technology Assessment Criteria)**: NHS-specific requirements for digital tools, covering:
   - Clinical safety
   - Data protection
   - Technical security
   - Interoperability
   - Usability

4. **DCB0129 (Clinical Risk Management)**: Standard for clinical safety of health IT systems, requiring:
   - Hazard identification
   - Risk assessment
   - Safety case report
   - Clinical safety officer

5. **GDPR/UK GDPR**: Data protection requirements for processing patient data, including:
   - Lawful basis for processing
   - Data minimization
   - Rights of data subjects
   - Data Protection Impact Assessment

6. **NHS Information Governance**: Additional NHS-specific requirements for handling patient data.

For the RMD-Health project specifically, the job description mentions ISO 13485 and DTAC compliance, so I understand these are key requirements."

---

### Q17: How would you handle bias in the AI system?

**Answer:**
"AI bias is a critical concern in healthcare:

1. **Training Data Bias**: The LLM may have been trained on data that underrepresents certain demographics. We mitigate this by:
   - Using explicit clinical criteria in prompts rather than relying solely on learned patterns
   - Testing across demographic groups during validation

2. **Prompt Engineering**: The system prompts avoid stereotypes and ensure equal consideration regardless of patient demographics:
```python
# Good: 'Analyze based on clinical symptoms and patterns'
# Bad: 'Consider typical presentations in middle-aged women'
```

3. **Fairness Testing**: During validation, we'd test the system's performance across:
   - Age groups
   - Sex/gender
   - Ethnicity
   - Socioeconomic indicators

4. **Transparent Reasoning**: By making the AI's reasoning visible, clinicians can identify if biased assumptions are being made.

5. **Diverse Stakeholder Input**: Working with PPI representatives from diverse backgrounds to identify potential biases we might miss.

6. **Continuous Monitoring**: Post-deployment monitoring for outcome disparities across groups.

7. **Documentation**: Clear documentation of known limitations and potential biases for clinician awareness."

---

## 🎤 Closing Questions

### Q18: Why are you interested in this specific role?

**Answer:**
"Several aspects of this role strongly appeal to me:

1. **Impact**: RMD-Health has the potential to improve outcomes for thousands of patients by enabling earlier diagnosis. That's meaningful work.

2. **Technical Challenge**: Integrating agentic AI with NHS systems, ensuring FHIR compliance, and meeting regulatory requirements is a complex and interesting engineering problem.

3. **Multi-disciplinary Environment**: I thrive in teams that combine technical and domain expertise. Working with clinicians, patients, and NHS IT specialists would be professionally enriching.

4. **Research Context**: Being based at Henley Business School's Informatics Research Centre offers opportunities to contribute to academic publications and advance the field.

5. **Full Lifecycle**: The role covers design, implementation, testing, and deployment - I'd be involved in the complete product journey.

6. **Emerging Technology**: LLM-powered clinical decision support is at the frontier of healthcare AI. This is where I want to build my expertise.

The demonstration project I've built shows my genuine interest and initiative in this space."

---

### Q19: What questions do you have for us?

**Suggested Questions to Ask:**

1. "Can you tell me more about the current state of the RMD-Health prototype and what the immediate technical priorities are?"

2. "How does the team currently approach clinical validation - what does the feedback loop with clinicians look like?"

3. "What's the timeline for regulatory submission, and how involved would I be in the DTAC and CE marking process?"

4. "What LLM providers or frameworks is the project currently using or evaluating?"

5. "How does the team collaborate with NHS IT specialists at RBFT and OUH? What integration points exist today?"

6. "What does success look like for this role after 6 months? After 22 months?"

7. "Are there opportunities to contribute to publications or present at conferences?"

---

## 📚 Additional Resources

### Key Documents to Review Before Interview
- NICE NG100: Rheumatoid Arthritis in Adults
- NHS Digital FHIR API documentation
- MHRA Guidance on AI as a Medical Device
- DTAC Assessment Framework
- ISO 13485:2016 summary
- The original job description and person specification

### Practice Points
- Run through the demo application and be ready to screen-share it
- Be prepared to discuss code and make live changes if asked
- Have the architecture diagram ready to explain
- Practice explaining technical concepts to non-technical audiences
