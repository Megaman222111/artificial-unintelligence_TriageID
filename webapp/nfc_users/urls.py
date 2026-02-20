from django.urls import path
from . import views

urlpatterns = [
    # User (simple NFC) API
    path("", views.user_list),
    path("create/", views.user_create),
    path("<str:user_id>/", views.user_by_id),
]
