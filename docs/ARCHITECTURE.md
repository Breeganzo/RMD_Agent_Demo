# RMD-Health System Architecture

## Overview

This document describes the architecture of the RMD-Health Screening Agent, a demonstration prototype for AI-powered clinical decision support in rheumatic and musculoskeletal disease (RMD) screening.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                           (Streamlit Web App)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  Patient Form   │  │   Results View  │  │      Disclaimer Banner      │ │
│  │  (Demographics, │  │  (Risk Level,   │  │  (Safety notices, not for   │ │
│  │   Symptoms)     │  │   Reasoning)    │  │   clinical use warnings)   │ │
│  └────────┬────────┘  └────────▲────────┘  └─────────────────────────────┘ │
│           │                    │                                            │
└───────────┼────────────────────┼────────────────────────────────────────────┘
            │                    │
            ▼                    │
┌───────────────────────────────────────────────────────────────────────────┐
│                          DATA MODELS LAYER                                 │
│                         (Pydantic + FHIR-inspired)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │ PatientScreening│  │     Symptom     │  │    RMDAssessment        │   │
│  │  - patient_id   │  │  - name         │  │  - risk_level           │   │
│  │  - age, sex     │  │  - present      │  │  - likely_conditions    │   │
│  │  - symptoms[]   │  │  - severity     │  │  - reasoning            │   │
│  │  - history      │  │  - duration     │  │  - next_step            │   │
│  └────────┬────────┘  └─────────────────┘  │  - confidence_score     │   │
│           │                                 └────────────▲────────────┘   │
└───────────┼──────────────────────────────────────────────┼────────────────┘
            │                                              │
            ▼                                              │
┌───────────────────────────────────────────────────────────────────────────┐
│                         AGENTIC AI LAYER                                   │
│                       (RMDScreeningAgent)                                  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Agent Workflow                                │  │
│  │                                                                      │  │
│  │  1. Receive Patient Data                                            │  │
│  │           │                                                          │  │
│  │           ▼                                                          │  │
│  │  2. Run Pattern Analysis Tools ──────────────────────────────┐      │  │
│  │     ┌─────────────────────────┐                              │      │  │
│  │     │ check_rmd_patterns()   │ ◄─────────────────────────────┤      │  │
│  │     │ - Polyarticular check  │                               │      │  │
│  │     │ - Morning stiffness    │                               │      │  │
│  │     │ - Red flags detection  │                               │      │  │
│  │     │ - Age-pattern analysis │                               │      │  │
│  │     └────────────┬───────────┘                               │      │  │
│  │                  │                                           │      │  │
│  │                  ▼                                           │      │  │
│  │  3. Build Enhanced Prompt (patient data + tool outputs)      │      │  │
│  │           │                                                  │      │  │
│  │           ▼                                                  │      │  │
│  │  4. Call LLM (Grok API) ─────────────────────────────────────┤      │  │
│  │           │                                                  │      │  │
│  │           ▼                                                  │      │  │
│  │  5. Parse JSON Response                                      │      │  │
│  │           │                                                  │      │  │
│  │           ▼                                                  │      │  │
│  │  6. Validate & Return RMDAssessment ─────────────────────────┘      │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      xAI Grok API                                   │  │
│  │                                                                      │  │
│  │  Endpoint: https://api.x.ai/v1/chat/completions                     │  │
│  │  Model: grok-beta / grok-2-latest                                   │  │
│  │                                                                      │  │
│  │  Request:                          Response:                        │  │
│  │  - System prompt (RMD knowledge)   - JSON structured assessment     │  │
│  │  - User prompt (patient data)      - Risk level, reasoning, etc.   │  │
│  │  - Temperature: 0.3                                                 │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. User Interface Layer (app.py)

**Responsibilities:**
- Render the patient screening form with all input fields
- Display assessment results with appropriate styling
- Show safety disclaimers prominently
- Handle user interactions and state management
- Provide demo mode for testing without API calls

**Key Features:**
- Responsive two-column layout
- Color-coded risk level display
- Expandable reasoning section
- Raw JSON data export

### 2. Data Models Layer (src/data_models.py)

**Responsibilities:**
- Define structured data schemas using Pydantic
- Validate input data types and ranges
- Provide FHIR-inspired resource mappings
- Generate clinical summary text for LLM processing

**Key Models:**
- `Symptom`: Individual clinical observation
- `PatientScreening`: Complete screening encounter
- `RMDAssessment`: AI-generated risk assessment

### 3. Agentic AI Layer (src/rmd_agent.py)

**Responsibilities:**
- Orchestrate the assessment workflow
- Execute pattern analysis tools
- Interface with the LLM API
- Parse and validate LLM responses
- Handle errors gracefully with fallbacks

**Key Components:**
- `RMDScreeningAgent`: Main agent class
- `check_rmd_patterns()`: Pattern analysis tool
- `demo_assessment()`: API-free demo mode

### 4. Prompt Engineering (src/prompts.py)

**Responsibilities:**
- Define system prompts with RMD clinical knowledge
- Build structured user prompts from patient data
- Enforce JSON output schema
- Include safety guardrails

### 5. Utilities (src/utils.py)

**Responsibilities:**
- API key management
- JSON extraction from LLM responses
- Response validation
- Fallback assessment generation

## Why Agentic AI?

The agentic design pattern is appropriate for this use case because:

1. **Tool Composition**: The agent can combine rule-based pattern analysis with LLM reasoning, getting the best of both approaches.

2. **Explainability**: Each tool provides structured outputs that can be inspected and understood, supporting clinical transparency.

3. **Modularity**: New tools (e.g., lab value analysis, imaging interpretation) can be added without rewriting the core logic.

4. **Reliability**: If the LLM fails, the agent can fall back to rule-based tools for a basic assessment.

5. **Auditability**: The separation of concerns makes it easier to audit and validate each component for regulatory compliance.

## Data Flow

1. **Input**: User enters patient data via Streamlit form
2. **Validation**: Pydantic validates and structures the data
3. **Tool Execution**: Agent runs pattern analysis tools
4. **Prompt Building**: System and user prompts are constructed
5. **LLM Inference**: Grok API generates clinical reasoning
6. **Response Parsing**: JSON response is extracted and validated
7. **Output**: Structured assessment is displayed to user

## Security Considerations

- API keys are loaded from environment variables, never hardcoded
- No real patient data is stored or transmitted
- All data processing happens in-memory during session
- Disclaimers clearly indicate prototype status

## Deployment Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐
│   User Browser  │◄────►│  Hugging Face    │◄────►│   xAI Grok     │
│                 │      │  Spaces          │      │   API          │
│                 │      │  (Streamlit)     │      │                │
└─────────────────┘      └──────────────────┘      └────────────────┘
```

The application is designed to be stateless and can be deployed on:
- Hugging Face Spaces (recommended)
- Streamlit Community Cloud
- Docker containers
- Any Python-compatible hosting

## Future Extensions

In a production system, this architecture could be extended with:

1. **NHS e-Referral Service Integration** (FHIR API)
2. **Electronic Health Record Connectivity** (HL7 FHIR)
3. **User Authentication** (NHS Login)
4. **Audit Logging** (for regulatory compliance)
5. **Multi-model Ensemble** (multiple LLMs for consensus)
6. **Active Learning** (clinician feedback loop)
