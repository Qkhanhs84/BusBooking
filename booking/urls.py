from django.urls import path
from . import views
from . import custom_admin_views


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
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('payment_confirmation/', views.payment_confirmation, name='payment_confirmation'),
    path('complete_payment/', views.complete_payment, name='complete_payment'),
    
    # Ticket lookup and cancellation
    path('research/', views.research, name='research'),
    path('ticket-details/<str:booking_code>/', views.ticket_details, name='ticket_details'),
    path('cancel-ticket/<str:booking_code>/', views.cancel_ticket, name='cancel_ticket'),
    
    # Trang admin riêng
    path('custom-admin/', custom_admin_views.custom_admin_login, name='custom_admin_login'),
    path('custom-admin/dashboard/', custom_admin_views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('custom-admin/bookings/', custom_admin_views.custom_admin_bookings, name='custom_admin_bookings'),
    path('custom-admin/trips/', custom_admin_views.custom_admin_trips, name='custom_admin_trips'),
    path('custom-admin/confirm-payment/<str:booking_code>/', custom_admin_views.custom_admin_confirm_payment, name='custom_admin_confirm_payment'),
]

