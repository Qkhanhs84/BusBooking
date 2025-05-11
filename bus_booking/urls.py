"""
URL configuration for bus_booking project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('booking.urls')),
]

