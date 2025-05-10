from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('booking/', views.booking, name='booking'),
    path('booking/<int:schedule_id>/', views.booking, name='booking_with_id'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('news/', views.news, name='news'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify_email/', views.verify_email, name='verify_email'),
    path('research/', views.research, name='research'),
    # Thêm vào danh sách urlpatterns
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('cancel-booking/', views.cancel_booking, name='cancel_booking'),
]

