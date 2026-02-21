from django.contrib import admin
from .models import UserProfile, Patient, PatientOutcomeEvent


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user_id", "created_at")
    search_fields = ("user_id",)
    readonly_fields = ("user_id", "created_at", "updated_at")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "nfc_id", "status", "room")
    search_fields = ("id", "first_name", "last_name", "nfc_id")


@admin.register(PatientOutcomeEvent)
class PatientOutcomeEventAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "event_type", "event_time", "source", "created_at")
    search_fields = ("patient__id", "patient__nfc_id", "event_type", "source")
    list_filter = ("event_type", "source")
