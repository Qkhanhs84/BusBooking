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
    path('admin/trips/', views.admin_trips, name='admin_trips'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),
    path('admin/cancellations/', views.admin_cancellations, name='admin_cancellations'),
    path('admin/trips/add/', views.admin_add_trip, name='admin_add_trip'),
    path('admin/trips/edit/', views.admin_edit_trip, name='admin_edit_trip'),
    path('admin/trips/delete/', views.admin_delete_trip, name='admin_delete_trip'),
    path('admin/trips/get/', views.admin_get_trip, name='admin_get_trip'),
    path('admin/bookings/get/', views.admin_get_booking, name='admin_get_booking'),
    path('admin/cancellations/approve/', views.admin_approve_cancellation, name='admin_approve_cancellation'),
    path('admin/cancellations/reject/', views.admin_reject_cancellation, name='admin_reject_cancellation'),
    path('admin/trips/total_seats', views.admin_get_total_seats, name='total_seats'),
    # Thêm các URL này vào urlpatterns trong file urls.py hiện có

path('admin/schedules/', views.admin_schedules, name='admin_schedules'),
path('admin/schedules/add/', views.admin_add_schedule, name='admin_add_schedule'),
path('admin/schedules/edit/', views.admin_edit_schedule, name='admin_edit_schedule'),
path('admin/schedules/delete/', views.admin_delete_schedule, name='admin_delete_schedule'),
path('admin/schedules/get/', views.admin_get_schedule, name='admin_get_schedule'),
# Thêm URL này vào urlpatterns trong file urls.py hiện có
path('admin/buses/add/', views.admin_add_bus, name='admin_add_bus'),
# Thêm URL này vào urlpatterns trong file urls.py hiện có
path('admin/routes/add/', views.admin_add_route, name='admin_add_route'),
]

