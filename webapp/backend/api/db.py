import json
import os
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "medlink.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL,
                blood_type TEXT NOT NULL,
                nfc_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                room TEXT NOT NULL,
                admission_date TEXT NOT NULL,
                allergies_json TEXT NOT NULL,
                primary_diagnosis TEXT NOT NULL,
                insurance_provider TEXT NOT NULL,
                insurance_id TEXT NOT NULL,
                emergency_contact_json TEXT NOT NULL,
                medications_json TEXT NOT NULL,
                vital_signs_json TEXT NOT NULL,
                medical_history_json TEXT NOT NULL,
                notes_json TEXT NOT NULL
            )
            """
        )

        existing_count = connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        prod_row = _prod_user_row()
        existing_prod_row = connection.execute(
            "SELECT * FROM patients WHERE id = ?", (prod_row["id"],)
        ).fetchone()

        if existing_count == 0:
            connection.execute(_insert_sql(), prod_row)
            return

        if existing_prod_row is None:
            return

        # One-time repair path for old placeholder bootstrap rows.
        if _is_placeholder_row(existing_prod_row):
            connection.execute(_update_sql(), prod_row)


def list_patients() -> list[dict]:
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM patients ORDER BY id").fetchall()
    return [_from_db_row(row) for row in rows]


def get_patient_by_id(patient_id: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return _from_db_row(row) if row else None


def get_patient_by_nfc(nfc_id: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute("SELECT * FROM patients WHERE nfc_id = ?", (nfc_id,)).fetchone()
    return _from_db_row(row) if row else None


def patient_count() -> int:
    with _connect() as connection:
        return connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]


def _prod_user_row() -> dict:
    prod_user_id = os.getenv("PROD_USER_ID", "PROD-USER-001")
    return {
        "id": prod_user_id,
        "first_name": "Avery",
        "last_name": "Brooks",
        "date_of_birth": "1992-04-14",
        "gender": "Female",
        "blood_type": "O+",
        "nfc_id": f"NFC-{prod_user_id}",
        "status": "active",
        "room": "ICU-204",
        "admission_date": "2026-02-10",
        "allergies_json": json.dumps(["Penicillin"]),
        "primary_diagnosis": "Acute Myocardial Infarction",
        "insurance_provider": "BlueCross BlueShield",
        "insurance_id": "BCB-449281",
        "emergency_contact_json": json.dumps(
            {"name": "Jordan Brooks", "relationship": "Spouse", "phone": "(555) 123-4567"}
        ),
        "medications_json": json.dumps(
            [
                {"name": "Aspirin", "dosage": "81mg", "frequency": "Daily"},
                {"name": "Metoprolol", "dosage": "50mg", "frequency": "Twice daily"},
            ]
        ),
        "vital_signs_json": json.dumps(
            {
                "heartRate": 78,
                "bloodPressure": "128/82",
                "temperature": 98.6,
                "oxygenSaturation": 97,
            }
        ),
        "medical_history_json": json.dumps(
            ["Hypertension (diagnosed 2018)", "Type 2 Diabetes (diagnosed 2020)"]
        ),
        "notes_json": json.dumps(["Production bootstrap user"]),
    }


def _insert_sql() -> str:
    return """
        INSERT INTO patients (
            id, first_name, last_name, date_of_birth, gender, blood_type, nfc_id,
            status, room, admission_date, allergies_json, primary_diagnosis,
            insurance_provider, insurance_id, emergency_contact_json,
            medications_json, vital_signs_json, medical_history_json, notes_json
        ) VALUES (
            :id, :first_name, :last_name, :date_of_birth, :gender, :blood_type, :nfc_id,
            :status, :room, :admission_date, :allergies_json, :primary_diagnosis,
            :insurance_provider, :insurance_id, :emergency_contact_json,
            :medications_json, :vital_signs_json, :medical_history_json, :notes_json
        )
    """


def _update_sql() -> str:
    return """
        UPDATE patients SET
            first_name = :first_name,
            last_name = :last_name,
            date_of_birth = :date_of_birth,
            gender = :gender,
            blood_type = :blood_type,
            nfc_id = :nfc_id,
            status = :status,
            room = :room,
            admission_date = :admission_date,
            allergies_json = :allergies_json,
            primary_diagnosis = :primary_diagnosis,
            insurance_provider = :insurance_provider,
            insurance_id = :insurance_id,
            emergency_contact_json = :emergency_contact_json,
            medications_json = :medications_json,
            vital_signs_json = :vital_signs_json,
            medical_history_json = :medical_history_json,
            notes_json = :notes_json
        WHERE id = :id
    """


def _is_placeholder_row(row: sqlite3.Row) -> bool:
    return row["primary_diagnosis"] in {"N/A", ""} or row["blood_type"] == "Unknown"


def _from_db_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "firstName": row["first_name"],
        "lastName": row["last_name"],
        "dateOfBirth": row["date_of_birth"],
        "gender": row["gender"],
        "bloodType": row["blood_type"],
        "nfcId": row["nfc_id"],
        "status": row["status"],
        "room": row["room"],
        "admissionDate": row["admission_date"],
        "allergies": json.loads(row["allergies_json"]),
        "primaryDiagnosis": row["primary_diagnosis"],
        "insuranceProvider": row["insurance_provider"],
        "insuranceId": row["insurance_id"],
        "emergencyContact": json.loads(row["emergency_contact_json"]),
        "medications": json.loads(row["medications_json"]),
        "vitalSigns": json.loads(row["vital_signs_json"]),
        "medicalHistory": json.loads(row["medical_history_json"]),
        "notes": json.loads(row["notes_json"]),
    }
