from django.urls import path

from booking import custom_admin_views
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
    path('custom_admin/statistics/', custom_admin_views.admin_statistics, name='custom_admin_statistics'),
    # path('admin/trips/total_seats', views.admin_get_total_seats, name='total_seats'),
    # Thêm các URL này vào urlpatterns trong file urls.py hiện có

path('custom-admin/schedules/', custom_admin_views.admin_schedules, name='custom_admin_schedules'),
path('custom-admin/schedules/add/', custom_admin_views.admin_add_schedule, name='custom_admin_add_schedule'),
path('custom-admin/schedules/edit/', custom_admin_views.admin_edit_schedule, name='custom_admin_edit_schedule'),
path('custom-admin/schedules/delete/', custom_admin_views.admin_delete_schedule, name='custom_admin_delete_schedule'),
path('custom-admin/schedules/get/', custom_admin_views.admin_get_schedule, name='custom_admin_get_schedule'),
# Thêm URL này vào urlpatterns trong file urls.py hiện có
path('custom-admin/buses/add/', custom_admin_views.admin_add_bus, name='custom_admin_add_bus'),
# Thêm URL này vào urlpatterns trong file urls.py hiện có
path('custom-admin/routes/add/', custom_admin_views.admin_add_route, name='custom_admin_add_route'),
 path('custom-admin/', custom_admin_views.custom_admin_login, name='custom_admin_login'),
    # path('custom-admin/dashboard/', custom_admin_views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('custom-admin/bookings/', custom_admin_views.custom_admin_bookings, name='custom_admin_bookings'),
    path('custom-admin/confirm-payment/<str:booking_code>/', custom_admin_views.custom_admin_confirm_payment, name='custom_admin_confirm_payment'),
]

