from django.urls import path

from booking import custom_admin_views
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
    path('ticket-lookup/', views.ticket_lookup, name='ticket_lookup'),
    path('ticket-details/<str:booking_code>/', views.ticket_details, name='ticket_details'),
    path('cancel-ticket/<str:booking_code>/', views.cancel_ticket, name='cancel_ticket'),
    
    # Trang admin riêng
    path('custom-admin/', custom_admin_views.custom_admin_login, name='custom_admin_login'),   
    path('custom-admin/bookings/', custom_admin_views.custom_admin_bookings, name='custom_admin_bookings'),
    path('custom-admin/confirm-payment/<str:booking_code>/', custom_admin_views.custom_admin_confirm_payment, name='custom_admin_confirm_payment'),
    path('custom_admin/statistics/', custom_admin_views.admin_statistics, name='custom_admin_statistics'),
    path('custom-admin/schedules/', custom_admin_views.admin_schedules, name='custom_admin_schedules'),
    path('custom-admin/schedules/add/', custom_admin_views.admin_add_schedule, name='custom_admin_add_schedule'),
    path('custom-admin/schedules/edit/', custom_admin_views.admin_edit_schedule, name='custom_admin_edit_schedule'),
    path('custom-admin/schedules/delete/', custom_admin_views.admin_delete_schedule, name='custom_admin_delete_schedule'),
    path('custom-admin/schedules/get/', custom_admin_views.admin_get_schedule, name='custom_admin_get_schedule'),
    path('custom-admin/buses/add/', custom_admin_views.admin_add_bus, name='custom_admin_add_bus'),
    path('custom-admin/routes/add/', custom_admin_views.admin_add_route, name='custom_admin_add_route'),
    path('custom-admin/', custom_admin_views.custom_admin_login, name='custom_admin_login'),
    path('custom-admin/bookings/', custom_admin_views.custom_admin_bookings, name='custom_admin_bookings'),
    path('custom-admin/confirm-payment/<str:booking_code>/', custom_admin_views.custom_admin_confirm_payment, name='custom_admin_confirm_payment'),
]

