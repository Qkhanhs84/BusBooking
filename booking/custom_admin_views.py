from datetime import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.mail import send_mail
from .models import Booking, Bus, BusStation, Route, Schedule, Seat, Trip, BookingSeat
from django.contrib import messages
from django.utils import timezone
# Custom Admin Views
def is_admin(user):
    """Kiểm tra xem người dùng có quyền admin không"""
    return user.is_superuser or user.is_staff

def custom_admin_login(request):
    """Đăng nhập cho trang admin riêng"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and is_admin(user):
            login(request, user)
            return redirect('custom_admin_dashboard')
        else:
            return render(request, 'booking/custom_admin/login.html', {'error_message': 'Invalid credentials or insufficient permissions'})
    
    return render(request, 'admin/login.html')

@login_required
@user_passes_test(is_admin)
def custom_admin_dashboard(request):
    """Dashboard trang admin"""
    # Lấy thông tin tổng quan
    total_bookings = Booking.objects.count()
    pending_payments = Booking.objects.filter(payment_method='QR', payment_status='Pending').count()
    today = timezone.now().date()
    total_trips_today = Trip.objects.filter(trip_date=today).count()
    
    # Lấy các đơn đặt vé gần đây
    recent_bookings = Booking.objects.all().order_by('-booking_time')[:10]
    
    context = {
        'total_bookings': total_bookings,
        'pending_payments': pending_payments,
        'total_trips_today': total_trips_today,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'booking/custom_admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def custom_admin_bookings(request):
    """Quản lý tất cả đơn đặt vé"""
    # Lọc theo các tham số
    payment_status = request.GET.get('payment_status', '')
    booking_status = request.GET.get('booking_status', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Bắt đầu với tất cả bookings
    bookings = Booking.objects.all().order_by('-booking_time')
    
    # Áp dụng các bộ lọc nếu có
    if payment_status:
        bookings = bookings.filter(payment_status=payment_status)
    
    if booking_status:
        bookings = bookings.filter(booking_status=booking_status)
    
    if payment_method:
        bookings = bookings.filter(payment_method=payment_method)
    
    # Phân trang
    paginator = Paginator(bookings, 10)  # 10 bookings mỗi trang
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookings': page_obj,
        'payment_status': payment_status,
        'booking_status': booking_status,
        'payment_method': payment_method
    }
    
    return render(request, 'admin/admin-bookings.html', context)

@login_required
@user_passes_test(is_admin)
def custom_admin_confirm_payment(request, booking_code):
    """Xác nhận thanh toán cho một đơn đặt vé"""
    booking = get_object_or_404(Booking, booking_code=booking_code)
    
    # Kiểm tra xem booking có phải QR và đang ở trạng thái Pending không
    if booking.payment_method == 'QR' and booking.payment_status == 'Pending':
        # Cập nhật trạng thái thanh toán
        booking.payment_status = 'Paid'
        booking.booking_status = 'Completed'
        booking.save()
        
        # Lấy danh sách ghế để hiển thị trong email
        booking_seats = BookingSeat.objects.filter(booking=booking)
        seats_list = [bs.seat.seat_number for bs in booking_seats]
        seats_str = ", ".join(seats_list)
        
        # Format date và time cho email
        trip_date = booking.trip.trip_date.strftime('%d/%m/%Y')
        departure_time = booking.trip.schedule.departure_time.strftime('%H:%M')
        
        # Gửi email thông báo cho khách hàng
        try:
            subject = 'Xác nhận thanh toán - BUSBOOKING'
            message = f'''Xin chào {booking.passenger_name},

Thanh toán cho đơn hàng của bạn với mã {booking.booking_code} đã được xác nhận.

THÔNG TIN VÉ:
- Tuyến đường: {booking.trip.schedule.route.route_name}
- Ngày khởi hành: {trip_date} 
- Giờ khởi hành: {departure_time}
- Số ghế: {seats_str}

Vui lòng đến trạm xe trước giờ khởi hành ít nhất 15 phút và mang theo mã đặt vé của bạn.

Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.

BUSBOOKING
'''
            
            send_mail(
                subject,
                message,
                'noreply@busbooking.com',
                [booking.passenger_email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
      # Chuyển hướng trở lại trang bookings
    return redirect('custom_admin_bookings')
def admin_statistics(request):
    # Get date from query parameter or use today's date
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()
    
    # Get trips for the selected date
    trips = Trip.objects.filter(trip_date=current_date).select_related('schedule__route', 'schedule__bus')
    
    # Calculate statistics
    total_trips = trips.count()
    total_seats = sum(trip.schedule.bus.total_seats for trip in trips)
    total_available_seats = sum(trip.available_seats for trip in trips)
    total_booked_seats = total_seats - total_available_seats
    full_booked_trips = trips.filter(available_seats=0).count()
    
    # Calculate occupancy rate for each trip
    trip_stats = []
    for trip in trips:
        total_seats = trip.schedule.bus.total_seats
        booked_seats = total_seats - trip.available_seats
        occupancy_rate = int((booked_seats / total_seats) * 100) if total_seats > 0 else 0
        
        trip_stats.append({
            'schedule': trip.schedule,
            'booked_seats': booked_seats,
            'available_seats': trip.available_seats,
            'occupancy_rate': occupancy_rate,
        })
    
    context = {
        'active_page': 'statistics',
        'current_date': current_date,
        'total_trips': total_trips,
        'total_booked_seats': total_booked_seats,
        'total_available_seats': total_available_seats,
        'full_booked_trips': full_booked_trips,
        'trips': trip_stats,
    }
    
    return render(request, 'admin/admin-statistics.html', context)


# Thêm các hàm này vào file views.py hiện có

def admin_schedules(request):
    # Get all schedules
    schedules = Schedule.objects.all().select_related('route__departure_station', 'route__arrival_station', 'bus')
    
    # Get all routes for the forms
    routes = Route.objects.all().select_related('departure_station', 'arrival_station')
    
    # Get all stations for adding new routes
    stations = BusStation.objects.all()
    
    # Get buses that are not already assigned to active schedules
    # First, get all buses used in active schedules
    used_bus_ids = Schedule.objects.filter(is_active=True).values_list('bus_id', flat=True)
    
    # Then, get all buses that are not in the used_bus_ids list
    available_buses = Bus.objects.exclude(id__in=used_bus_ids)
    
    # Get all buses for editing (we need all buses for editing existing schedules)
    all_buses = Bus.objects.all()
    
    # Get bus types for filtering
    bus_types = Bus.BUS_TYPES
    
    context = {
        'active_page': 'schedules',
        'schedules': schedules,
        'routes': routes,
        'stations': stations,
        'available_buses': available_buses,
        'all_buses': all_buses,
        'bus_types': bus_types,
    }
    
    return render(request, 'admin/admin-schedules.html', context)
# Thêm hàm để tạo xe mới
def admin_add_bus(request):
    if request.method == 'POST':
        # Process form data
        license_plate = request.POST.get('license_plate')
        bus_type = request.POST.get('bus_type')
        total_seats = request.POST.get('total_seats')
        amenities = request.POST.get('amenities')
        surcharge = request.POST.get('surcharge')
        
        try:
            # Check if license plate already exists
            if Bus.objects.filter(license_plate=license_plate).exists():
                messages.error(request, 'Biển số xe này đã tồn tại!')
                return redirect('admin_schedules')
            
            # Create new bus
            bus = Bus.objects.create(
                license_plate=license_plate,
                bus_type=bus_type,
                total_seats=total_seats,
                amenities=amenities,
                surcharge=surcharge
            )
            
            # Create seats for the new bus
            for i in range(1, int(total_seats) + 1):
                seat_number = str(i)
                position_description = f"Ghế {i}"
                
                Seat.objects.create(
                    bus=bus,
                    seat_number=seat_number,
                    position_description=position_description
                )
            
            messages.success(request, 'Thêm xe mới thành công!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_schedules')
    
    return redirect('admin_schedules')

def admin_add_schedule(request):
    if request.method == 'POST':
        # Process form data
        route_id = request.POST.get('route')
        bus_id = request.POST.get('bus')
        departure_time = request.POST.get('departure_time')
        arrival_time = request.POST.get('arrival_time')
        is_active = 'is_active' in request.POST
        
        try:
            route = Route.objects.get(id=route_id)
            bus = Bus.objects.get(id=bus_id)
            
            # Create new schedule
            schedule = Schedule.objects.create(
                route=route,
                bus=bus,
                departure_time=departure_time,
                arrival_time=arrival_time,
                is_active=is_active
            )
            
            messages.success(request, 'Thêm lịch trình thành công!')
        except Route.DoesNotExist:
            messages.error(request, 'Không tìm thấy tuyến đường!')
        except Bus.DoesNotExist:
            messages.error(request, 'Không tìm thấy xe!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_schedules')
    
    return redirect('admin_schedules')

def admin_edit_schedule(request):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            
            # Update schedule data
            route_id = request.POST.get('route')
            bus_id = request.POST.get('bus')
            
            schedule.route = Route.objects.get(id=route_id)
            schedule.bus = Bus.objects.get(id=bus_id)
            schedule.departure_time = request.POST.get('departure_time')
            schedule.arrival_time = request.POST.get('arrival_time')
            schedule.is_active = 'is_active' in request.POST
            
            schedule.save()
            
            messages.success(request, 'Cập nhật lịch trình thành công!')
        except Schedule.DoesNotExist:
            messages.error(request, 'Không tìm thấy lịch trình!')
        except Route.DoesNotExist:
            messages.error(request, 'Không tìm thấy tuyến đường!')
        except Bus.DoesNotExist:
            messages.error(request, 'Không tìm thấy xe!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_schedules')
    
    return redirect('admin_schedules')

def admin_delete_schedule(request):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            
            # Check if there are any trips for this schedule
            if Trip.objects.filter(schedule=schedule).exists():
                messages.error(request, 'Không thể xóa lịch trình này vì đã có chuyến xe được tạo từ lịch trình này!')
                return redirect('admin_schedules')
            
            # Delete schedule
            schedule.delete()
            
            messages.success(request, 'Xóa lịch trình thành công!')
        except Schedule.DoesNotExist:
            messages.error(request, 'Không tìm thấy lịch trình!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_schedules')
    
    return redirect('admin_schedules')

def admin_add_route(request):
    if request.method == 'POST':
        # Process form data
        route_name = request.POST.get('route_name')
        departure_station_id = request.POST.get('departure_station')
        arrival_station_id = request.POST.get('arrival_station')
        base_price = request.POST.get('base_price')
        distance_km = request.POST.get('distance_km')
        estimated_duration_minutes = request.POST.get('estimated_duration_minutes')
        
        try:
            # Get stations
            departure_station = BusStation.objects.get(id=departure_station_id)
            arrival_station = BusStation.objects.get(id=arrival_station_id)
            
            # Create new route
            route = Route.objects.create(
                route_name=route_name,
                departure_station=departure_station,
                arrival_station=arrival_station,
                base_price=base_price,
                distance_km=distance_km,
                estimated_duration_minutes=estimated_duration_minutes
            )
            
            messages.success(request, 'Thêm tuyến đường thành công!')
        except BusStation.DoesNotExist:
            messages.error(request, 'Không tìm thấy trạm xe!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_schedules')
    
    return redirect('admin_schedules')

def admin_get_schedule(request):
    schedule_id = request.GET.get('id')
    
    try:
        schedule = Schedule.objects.select_related('route', 'bus').get(id=schedule_id)
        
        # Get buses that are not already assigned to active schedules (excluding current schedule)
        used_bus_ids = Schedule.objects.filter(is_active=True).exclude(id=schedule_id).values_list('bus_id', flat=True)
        
        # Get available buses (current bus + unused buses)
        available_buses = []
        current_bus = {
            'id': schedule.bus.id,
            'license_plate': schedule.bus.license_plate,
            'bus_type': schedule.bus.get_bus_type_display(),
            'total_seats': schedule.bus.total_seats,
            'is_current': True
        }
        available_buses.append(current_bus)
        
        for bus in Bus.objects.exclude(id__in=used_bus_ids).exclude(id=schedule.bus.id):
            available_buses.append({
                'id': bus.id,
                'license_plate': bus.license_plate,
                'bus_type': bus.get_bus_type_display(),
                'total_seats': bus.total_seats,
                'is_current': False
            })
        
        data = {
            'id': schedule.id,
            'route_id': schedule.route.id,
            'route_name': schedule.route.route_name,
            'bus_id': schedule.bus.id,
            'bus_name': f"{schedule.bus.license_plate} ({schedule.bus.get_bus_type_display()})",
            'departure_time': schedule.departure_time.strftime('%H:%M'),
            'arrival_time': schedule.arrival_time.strftime('%H:%M'),
            'is_active': schedule.is_active,
            'available_buses': available_buses
        }
        
        return JsonResponse(data)
    except Schedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)

