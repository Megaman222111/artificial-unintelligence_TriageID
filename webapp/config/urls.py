"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from nfc_users.views import nfc_scan as nfc_scan_view


def api_root(request):
    """API info at root. React frontend runs via Next.js and calls these endpoints."""
    return JsonResponse({
        "service": "medlink-api",
        "status": "running",
        "routes": [
            "/api/patients/",
            "/api/patients/<id>/",
            "/api/patients/by-nfc/<nfc_id>/",
            "/api/nfc/scan/",
            "/api/users/",
            "/admin/",
        ],
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("nfc_users.urls")),
    path("api/patients/", include("nfc_users.patient_urls")),
    path("api/nfc/scan/", nfc_scan_view),
    path("", api_root),
]
