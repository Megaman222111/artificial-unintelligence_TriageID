from django.contrib import admin
from .models import UserProfile, Patient


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user_id", "created_at")
    search_fields = ("user_id",)
    readonly_fields = ("user_id", "created_at", "updated_at")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "nfc_id", "status", "room")
    search_fields = ("id", "first_name", "last_name", "nfc_id")
