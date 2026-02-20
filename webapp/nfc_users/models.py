"""
User profile keyed by NFC user_id. Sensitive fields stored encrypted in SQLite.
"""
from django.db import models


class UserProfile(models.Model):
    """
    User record keyed by the ID written on their NFC tag (user_id, max 15 chars).
    Sensitive info is encrypted at rest; user_id is not encrypted for lookup.
    """
    user_id = models.CharField(max_length=15, unique=True, db_index=True)
    # Encrypted at rest (stored as base64 ciphertext in DB)
    _first_name = models.TextField(blank=True, default="")
    _last_name = models.TextField(blank=True, default="")
    _email = models.TextField(blank=True, default="")
    _phone = models.TextField(blank=True, default="")
    _notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]
        verbose_name = "User (NFC)"
        verbose_name_plural = "Users (NFC)"

    def __str__(self):
        return self.user_id

    @property
    def first_name(self):
        from .encryption import decrypt_value
        return decrypt_value(self._first_name) if self._first_name else ""

    @first_name.setter
    def first_name(self, value):
        from .encryption import encrypt_value
        self._first_name = encrypt_value((value or "").strip())

    @property
    def last_name(self):
        from .encryption import decrypt_value
        return decrypt_value(self._last_name) if self._last_name else ""

    @last_name.setter
    def last_name(self, value):
        from .encryption import encrypt_value
        self._last_name = encrypt_value((value or "").strip())

    @property
    def email(self):
        from .encryption import decrypt_value
        return decrypt_value(self._email) if self._email else ""

    @email.setter
    def email(self, value):
        from .encryption import encrypt_value
        self._email = encrypt_value((value or "").strip())

    @property
    def phone(self):
        from .encryption import decrypt_value
        return decrypt_value(self._phone) if self._phone else ""

    @phone.setter
    def phone(self, value):
        from .encryption import encrypt_value
        self._phone = encrypt_value((value or "").strip())

    @property
    def notes(self):
        from .encryption import decrypt_value
        return decrypt_value(self._notes) if self._notes else ""

    @notes.setter
    def notes(self, value):
        from .encryption import encrypt_value
        self._notes = encrypt_value((value or "").strip())

    def set_plain_fields(self, first_name="", last_name="", email="", phone="", notes=""):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.notes = notes

    def to_api_dict(self):
        return {
            "userId": self.user_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "notes": self.notes,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Patient(models.Model):
    """
    Patient record for MedLink dashboard. Matches the React Patient interface.
    nfc_id is the value stored on the NFC tag (max 15 chars from PN532).
    """
    id = models.CharField(max_length=64, primary_key=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    date_of_birth = models.CharField(max_length=32)
    gender = models.CharField(max_length=32)
    blood_type = models.CharField(max_length=16)
    nfc_id = models.CharField(max_length=15, unique=True, db_index=True)
    status = models.CharField(max_length=32)  # active | discharged | critical
    room = models.CharField(max_length=64)
    admission_date = models.CharField(max_length=32)
    allergies = models.JSONField(default=list)  # ["Penicillin"]
    primary_diagnosis = models.CharField(max_length=256)
    insurance_provider = models.CharField(max_length=128)
    insurance_id = models.CharField(max_length=128)
    emergency_contact = models.JSONField(default=dict)  # {name, relationship, phone}
    medications = models.JSONField(default=list)  # [{name, dosage, frequency}]
    vital_signs = models.JSONField(default=dict)  # {heartRate, bloodPressure, temperature, oxygenSaturation}
    medical_history = models.JSONField(default=list)
    notes = models.JSONField(default=list)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.nfc_id})"

    def to_api_dict(self):
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "dateOfBirth": self.date_of_birth,
            "gender": self.gender,
            "bloodType": self.blood_type,
            "nfcId": self.nfc_id,
            "status": self.status,
            "room": self.room,
            "admissionDate": self.admission_date,
            "allergies": self.allergies or [],
            "primaryDiagnosis": self.primary_diagnosis,
            "insuranceProvider": self.insurance_provider,
            "insuranceId": self.insurance_id,
            "emergencyContact": self.emergency_contact or {},
            "medications": self.medications or [],
            "vitalSigns": self.vital_signs or {},
            "medicalHistory": self.medical_history or [],
            "notes": self.notes or [],
        }
