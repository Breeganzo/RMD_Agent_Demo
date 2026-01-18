"""
RMD-Health Database Module
==========================

SQLite database for storing users, assessments, and audit logs.
SQLite is free, file-based, and perfect for this demo.
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "rmd_health.db"


def get_connection():
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('patient', 'clinician', 'auditor')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Patient profiles (additional info for patients)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_profiles (
            user_id INTEGER PRIMARY KEY,
            age INTEGER,
            sex TEXT,
            medical_history TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Assessments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            assessment_number INTEGER NOT NULL,
            assessment_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symptoms_json TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            likely_conditions TEXT,
            red_flags TEXT,
            recommended_action TEXT,
            reasoning TEXT,
            xai_explanation_json TEXT,
            fhir_bundle_json TEXT,
            FOREIGN KEY (patient_id) REFERENCES users(id)
        )
    """)
    
    # Audit logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL,
            patient_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            details_json TEXT,
            entry_hash TEXT,
            FOREIGN KEY (patient_id) REFERENCES users(id),
            FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        )
    """)
    
    conn.commit()
    
    # Create default users if not exist
    create_default_users(conn)
    
    conn.close()


def hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_default_users(conn):
    """Create default demo users.
    
    NHS GDPR Note: All users are demo accounts with fictional data only.
    No real PII is stored in this demonstration system.
    """
    cursor = conn.cursor()
    
    default_users = [
        # Demo Auditor
        ("auditor@rmd-health.demo", "admin123", "Demo Auditor", "auditor"),
        # Demo Clinician
        ("clinician@rmd-health.demo", "clinician123", "Dr. Demo", "clinician"),
        # Demo Patients (fictional names)
        ("patient1@rmd-health.demo", "patient123", "Demo Patient 1", "patient"),
        ("patient2@rmd-health.demo", "patient123", "Demo Patient 2", "patient"),
    ]
    
    for email, password, name, user_type in default_users:
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, name, user_type) VALUES (?, ?, ?, ?)",
                (email, hash_password(password), name, user_type)
            )
            
            # Add patient profile if patient
            if user_type == "patient":
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO patient_profiles (user_id, age, sex) VALUES (?, ?, ?)",
                    (user_id, 45, "Female" if "Mary" in name else "Male")
                )
        except sqlite3.IntegrityError:
            pass  # User already exists
    
    conn.commit()


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user info."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, email, name, user_type FROM users WHERE email = ? AND password_hash = ?",
        (email, hash_password(password))
    )
    
    row = cursor.fetchone()
    
    if row:
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), row['id'])
        )
        conn.commit()
        
        user = {
            'id': row['id'],
            'email': row['email'],
            'name': row['name'],
            'user_type': row['user_type']
        }
        conn.close()
        return user
    
    conn.close()
    return None


def register_user(email: str, password: str, name: str, user_type: str = "patient") -> bool:
    """Register a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name, user_type) VALUES (?, ?, ?, ?)",
            (email, hash_password(password), name, user_type)
        )
        
        if user_type == "patient":
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO patient_profiles (user_id) VALUES (?)",
                (user_id,)
            )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_patient_profile(user_id: int) -> Optional[Dict]:
    """Get patient profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id, u.email, u.name, p.age, p.sex, p.medical_history
        FROM users u
        LEFT JOIN patient_profiles p ON u.id = p.user_id
        WHERE u.id = ? AND u.user_type = 'patient'
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_patient_profile(user_id: int, age: int, sex: str, medical_history: str = None):
    """Update patient profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE patient_profiles 
        SET age = ?, sex = ?, medical_history = ?
        WHERE user_id = ?
    """, (age, sex, medical_history, user_id))
    
    conn.commit()
    conn.close()


def save_assessment(
    patient_id: int,
    assessment_id: str,
    symptoms: List[Dict],
    risk_level: str,
    confidence_score: float,
    likely_conditions: List[str],
    red_flags: List[str],
    recommended_action: str,
    reasoning: str,
    xai_explanation: Dict,
    fhir_bundle: Dict
) -> int:
    """Save an assessment to database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get next assessment number for this patient
    cursor.execute(
        "SELECT COALESCE(MAX(assessment_number), 0) + 1 FROM assessments WHERE patient_id = ?",
        (patient_id,)
    )
    assessment_number = cursor.fetchone()[0]
    
    cursor.execute("""
        INSERT INTO assessments (
            patient_id, assessment_number, assessment_id, symptoms_json,
            risk_level, confidence_score, likely_conditions, red_flags,
            recommended_action, reasoning, xai_explanation_json, fhir_bundle_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        assessment_number,
        assessment_id,
        json.dumps(symptoms, default=str),
        risk_level,
        confidence_score,
        json.dumps(likely_conditions),
        json.dumps(red_flags),
        recommended_action,
        reasoning,
        json.dumps(xai_explanation, default=str),
        json.dumps(fhir_bundle, default=str)
    ))
    
    # Create audit log entry
    cursor.execute("""
        INSERT INTO audit_logs (assessment_id, patient_id, event_type, details_json, entry_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (
        assessment_id,
        patient_id,
        "ASSESSMENT_CREATED",
        json.dumps({
            "risk_level": risk_level,
            "confidence": confidence_score,
            "assessment_number": assessment_number
        }),
        hashlib.sha256(f"{assessment_id}{datetime.now()}".encode()).hexdigest()[:16]
    ))
    
    conn.commit()
    db_id = cursor.lastrowid
    conn.close()
    
    return db_id


def get_patient_assessments(patient_id: int) -> List[Dict]:
    """Get all assessments for a patient."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM assessments 
        WHERE patient_id = ? 
        ORDER BY created_at DESC
    """, (patient_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    assessments = []
    for row in rows:
        assessment = dict(row)
        assessment['symptoms'] = json.loads(assessment['symptoms_json'])
        assessment['likely_conditions'] = json.loads(assessment['likely_conditions'])
        assessment['red_flags'] = json.loads(assessment['red_flags'])
        if assessment['xai_explanation_json']:
            assessment['xai_explanation'] = json.loads(assessment['xai_explanation_json'])
        if assessment['fhir_bundle_json']:
            assessment['fhir_bundle'] = json.loads(assessment['fhir_bundle_json'])
        assessments.append(assessment)
    
    return assessments


def get_all_patients() -> List[Dict]:
    """Get all patients (for clinician view)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id, u.email, u.name, p.age, p.sex,
               (SELECT COUNT(*) FROM assessments WHERE patient_id = u.id) as assessment_count,
               (SELECT risk_level FROM assessments WHERE patient_id = u.id ORDER BY created_at DESC LIMIT 1) as last_risk_level
        FROM users u
        LEFT JOIN patient_profiles p ON u.id = p.user_id
        WHERE u.user_type = 'patient'
        ORDER BY u.name
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_audit_logs() -> List[Dict]:
    """Get all audit logs (for auditor view)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT al.*, u.name as patient_name, u.email as patient_email
        FROM audit_logs al
        JOIN users u ON al.patient_id = u.id
        ORDER BY al.timestamp DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        log = dict(row)
        if log['details_json']:
            log['details'] = json.loads(log['details_json'])
        logs.append(log)
    
    return logs


def get_patient_audit_logs(patient_id: int) -> List[Dict]:
    """Get audit logs for a specific patient."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE patient_id = ?
        ORDER BY timestamp DESC
    """, (patient_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        log = dict(row)
        if log['details_json']:
            log['details'] = json.loads(log['details_json'])
        logs.append(log)
    
    return logs


def get_assessment_by_id(assessment_id: str) -> Optional[Dict]:
    """Get a specific assessment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, u.name as patient_name, u.email as patient_email
        FROM assessments a
        JOIN users u ON a.patient_id = u.id
        WHERE a.assessment_id = ?
    """, (assessment_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        assessment = dict(row)
        assessment['symptoms'] = json.loads(assessment['symptoms_json'])
        assessment['likely_conditions'] = json.loads(assessment['likely_conditions'])
        assessment['red_flags'] = json.loads(assessment['red_flags'])
        if assessment['xai_explanation_json']:
            assessment['xai_explanation'] = json.loads(assessment['xai_explanation_json'])
        if assessment['fhir_bundle_json']:
            assessment['fhir_bundle'] = json.loads(assessment['fhir_bundle_json'])
        return assessment
    return None


def export_to_csv():
    """Export all data to CSV files for viewing."""
    import csv
    
    export_dir = DB_PATH.parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Export users
    cursor.execute("SELECT id, email, name, user_type, created_at, last_login FROM users")
    with open(export_dir / "users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Email", "Name", "User Type", "Created At", "Last Login"])
        writer.writerows(cursor.fetchall())
    
    # Export assessments
    cursor.execute("""
        SELECT a.id, a.patient_id, u.name, a.assessment_number, a.assessment_id,
               a.created_at, a.risk_level, a.confidence_score, a.likely_conditions,
               a.red_flags, a.recommended_action
        FROM assessments a
        JOIN users u ON a.patient_id = u.id
    """)
    with open(export_dir / "assessments.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Patient ID", "Patient Name", "Test #", "Assessment ID",
                        "Created At", "Risk Level", "Confidence", "Conditions", "Red Flags", "Action"])
        writer.writerows(cursor.fetchall())
    
    # Export audit logs
    cursor.execute("""
        SELECT al.id, al.assessment_id, al.patient_id, u.name, al.timestamp,
               al.event_type, al.details_json, al.entry_hash
        FROM audit_logs al
        JOIN users u ON al.patient_id = u.id
    """)
    with open(export_dir / "audit_logs.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Assessment ID", "Patient ID", "Patient Name", "Timestamp",
                        "Event Type", "Details", "Hash"])
        writer.writerows(cursor.fetchall())
    
    conn.close()
    return export_dir


# Initialize database when module is imported
init_database()
