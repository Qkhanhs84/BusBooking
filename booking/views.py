from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from .models import BusStation, Bus, Route, Schedule, Trip, Seat, Booking, CancellationRequest, SeatTrip
from django.db import models
from django.db.models import *
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
def home(request):

    popular_routes = (
    Route.objects
    .values('route_name')                          
    .annotate(
        route_count=Count('id'),                  
        min_base_price=Min('base_price'),          
        departure_station=Min('departure_station__province'),  # Lấy province
        arrival_station=Min('arrival_station__province'),
    )
    .order_by('-route_count')[:3]
                  # Sắp xếp theo count giảm dần, lấy 3 bản ghi
    )
    provinces = list(BusStation.PROVINCES)
    context = {
        'popular_routes': popular_routes,
        'provinces': provinces,
        'current_date': timezone.now().date(),
    }
    return render(request, 'booking/home.html', context)

def search(request):
    from_location = request.GET.get('from', 'Nghe An')
    to_location = request.GET.get('to', 'Quang Binh')
    departure_province = BusStation.get_province_name(from_location)
    arrival_province = BusStation.get_province_name(to_location)
    default_date = timezone.now().date().strftime('%Y-%m-%d')  
    date = request.GET.get('date')
    parsed_date = datetime.strptime(date, '%d-%m-%Y').date() if date else timezone.now().date()
    trips = Trip.objects.filter(
        schedule__route__departure_station__province=from_location,
        schedule__route__arrival_station__province=to_location,
        trip_date=parsed_date
    )
    
    provinces = list(BusStation.PROVINCES)
    
    
    
    context = {
        'from_location': from_location,
        'to_location': to_location,
        'departure_province': departure_province,
        'arrival_province': arrival_province,
        'date': parsed_date,
        'trips': trips,
        'provinces' : provinces,
        'current_date': timezone.now().date(),
    }
    return render(request, 'booking/search.html', context)

def booking(request):
    if request.method == 'GET':
        trip_id = request.GET.get('id',None)
        
        if(trip_id == None):
            return redirect('home')
        trip = Trip.objects.get(id=trip_id)
        context = {
            'trip': trip,
            'seats': SeatTrip.objects.filter(trip=trip),
            'bed_range': range(1, trip.schedule.bus.total_seats + 1),
            
            
        }
        return render(request, 'booking/booking.html', context)    
    else:
        selected_seats = request.POST.get('selected_seats', '').split(',')
        passenger_name = request.POST.get('passenger_name', None)
        passenger_phone = request.POST.get('passenger_phone', None)
        passenger_email = request.POST.get('passenger_email', None)
        trip_id = request.POST.get('trip_id', None)
        
        print(selected_seats)
        return redirect('home')
    
    

def about(request):
    return render(request, 'booking/about.html')

def contact(request):
    return render(request, 'booking/contact.html')

def services(request):
    routes = Route.objects.all()
    
    context = {
        'routes': routes,
    }
    return render(request, 'booking/services.html', context)
    

def news(request):
    return render(request, 'booking/news.html')
@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = random.randint(100000, 999999)

        # Gửi email OTP
        send_mail(
            "Mã xác thực email",
            f"Mã xác thực của bạn là: {otp}",
            "noreply@example.com",
            [email],
            fail_silently=False,
        )

        # Lưu OTP vào session (hết hạn sau 1 phút)
        request.session["otp"] = otp
        request.session.set_expiry(60)  

        return JsonResponse({"message": "OTP đã được gửi đến email."})

    return JsonResponse({"error": "Yêu cầu không hợp lệ"}, status=400)
@csrf_exempt
def verify_email(request):
    if request.method == "POST":
        passenger_email = request.POST.get("passenger_email")
        passenger_name = request.POST.get("passenger_name")
        passenger_phone = request.POST.get("passenger_phone")
        selected_seats = request.POST.get("selected_seats", "").split(",")
        trip_id = request.POST.get("trip_id")
        seats = SeatTrip.objects.filter(id__in=selected_seats)
        seats_number = ",".join([seat.seat.seat_number for seat in seats])
        print(seats_number)
        context = {
            "passenger_email": passenger_email,
            "passenger_name": passenger_name,
            "passenger_phone": passenger_phone,
            "selected_seats": selected_seats,
            "seats_number": seats_number,
            "trip_id": trip_id,
        }
        return render(request, "booking/verify.html", context)
def admin_trips(request):
    # Get date from query parameter or use today's date
    date_str = request.GET.get('date')
    current_time = timezone.now().time()
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Get all active schedules for adding new trips
            schedules = Schedule.objects.filter(is_active=True).select_related('route', 'bus')
        except ValueError:
            current_date = timezone.now().date()
            # Lọc các chuyến đi trong ngày và giờ khởi hành hợp lệ
            schedules = Schedule.objects.filter(
                is_active=True,
                trip__trip_date=current_date,
                departure_time__gte=current_time
            ).select_related('route', 'bus')

    else:
        current_date = timezone.now().date()
            # Lọc các chuyến đi trong ngày và giờ khởi hành hợp lệ
        schedules = Schedule.objects.filter(
            is_active=True,
            trip__trip_date=current_date,
            departure_time__gte=current_time
        ).select_related('route', 'bus')
    
    # Get trips for the selected date
    trips = Trip.objects.filter(trip_date=current_date).select_related('schedule__route', 'schedule__bus')
    
    context = {
        'active_page': 'trips',
        'trips': trips,
        'schedules': schedules,
        'current_date': current_date,
    }
    
    return render(request, 'admin/admin-trips.html', context)

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

def admin_cancellations(request):
    # Get all cancellation requests
    cancellation_requests = CancellationRequest.objects.all().select_related(
        'booking__trip__schedule__route',
        'booking__trip__schedule__bus'
    ).order_by('-request_time')
    
    # Calculate statistics
    total_requests = cancellation_requests.count()
    pending_requests = cancellation_requests.filter(status='Pending').count()
    
    # Get today's date
    today = timezone.now().date()
    processed_today = cancellation_requests.exclude(
        status='Pending'
    ).filter(
        request_time__date=today
    ).count()
    
    context = {
        'active_page': 'cancellations',
        'cancellation_requests': cancellation_requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'processed_today': processed_today,
    }
    
    return render(request, 'admin/admin-cancellations.html', context)

def admin_add_trip(request):
    if request.method == 'POST':
        # Process form data
        schedule_id = request.POST.get('schedule')
        trip_date = request.POST.get('trip_date')
        available_seats = int(request.POST.get('available_seats'))
        status = request.POST.get('status')
        
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            
            # Check if trip already exists
            if Trip.objects.filter(schedule=schedule, trip_date=trip_date).exists():
                messages.error(request, 'Chuyến xe này đã tồn tại cho ngày đã chọn!')
                return redirect('admin_trips')
            
            # Create new trip
            trip = Trip.objects.create(
                schedule=schedule,
                trip_date=trip_date,
                available_seats=available_seats,
                status=status
            )
            
            # Create seat-trip records
            seats = Seat.objects.filter(bus=schedule.bus)
            for seat in seats:
                SeatTrip.objects.create(
                    trip=trip,
                    seat=seat,
                    status='Available'
                )
            
            messages.success(request, 'Thêm chuyến xe thành công!')
        except Schedule.DoesNotExist:
            messages.error(request, 'Không tìm thấy lịch trình!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_trips')
    
    return redirect('admin_trips')

def admin_edit_trip(request):
    if request.method == 'POST':
        trip_id = request.POST.get('trip_id')
        
        try:
            trip = Trip.objects.get(id=trip_id)
            
            # Update trip data
            schedule_id = request.POST.get('schedule')
            trip.schedule = Schedule.objects.get(id=schedule_id)
            trip.trip_date = request.POST.get('trip_date')
            trip.available_seats = int(request.POST.get('available_seats'))
            trip.status = request.POST.get('status')
            
            trip.save()
            
            messages.success(request, 'Cập nhật chuyến xe thành công!')
        except Trip.DoesNotExist:
            messages.error(request, 'Không tìm thấy chuyến xe!')
        except Schedule.DoesNotExist:
            messages.error(request, 'Không tìm thấy lịch trình!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_trips')
    
    return redirect('admin_trips')

def admin_delete_trip(request):
    if request.method == 'POST':
        trip_id = request.POST.get('trip_id')
        
        try:
            trip = Trip.objects.get(id=trip_id)
            
            # Check if there are any bookings for this trip
            if Booking.objects.filter(trip=trip).exists():
                messages.error(request, 'Không thể xóa chuyến xe này vì đã có đặt vé!')
                return redirect('admin_trips')
            
            # Delete seat-trip records
            SeatTrip.objects.filter(trip=trip).delete()
            
            # Delete trip
            trip.delete()
            
            messages.success(request, 'Xóa chuyến xe thành công!')
        except Trip.DoesNotExist:
            messages.error(request, 'Không tìm thấy chuyến xe!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_trips')
    
    return redirect('admin_trips')

def admin_get_trip(request):
    trip_id = request.GET.get('id')
    
    try:
        trip = Trip.objects.select_related('schedule__route', 'schedule__bus').get(id=trip_id)
        
        data = {
            'id': trip.id,
            'schedule_id': trip.schedule.id,
            'route_name': trip.schedule.route.route_name,
            'trip_date': trip.trip_date.strftime('%Y-%m-%d'),
            'available_seats': trip.available_seats,
            'status': trip.status,
            'departure_time': trip.schedule.departure_time.strftime('%H:%M'),
            'arrival_time': trip.schedule.arrival_time.strftime('%H:%M'),
            'total_seats': trip.schedule.bus.total_seats,
            'price': trip.compute_price()
        }
        
        return JsonResponse(data)
    except Trip.DoesNotExist:
        return JsonResponse({'error': 'Trip not found'}, status=404)

def admin_get_booking(request):
    request_id = request.GET.get('id')
    
    try:
        cancellation_request = CancellationRequest.objects.select_related('booking').get(id=request_id)
        booking = cancellation_request.booking
        
        data = {
            'id': booking.id,
            'booking_code': booking.booking_code,
            'passenger_name': booking.passenger_name,
            'total_price': float(booking.total_price)
        }
        
        return JsonResponse(data)
    except CancellationRequest.DoesNotExist:
        return JsonResponse({'error': 'Cancellation request not found'}, status=404)

def admin_approve_cancellation(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        refund_amount = request.POST.get('refund_amount')
        refund_method = request.POST.get('refund_method')
        
        try:
            cancellation_request = CancellationRequest.objects.select_related('booking__trip').get(id=request_id)
            
            # Update cancellation request
            cancellation_request.status = 'Approved'
            cancellation_request.refund_amount = refund_amount
            cancellation_request.refund_method = refund_method
            cancellation_request.refund_status = 'Pending'
            cancellation_request.save()
            
            # Update booking status
            booking = cancellation_request.booking
            booking.booking_status = 'Cancelled'
            booking.payment_status = 'Refunded'
            booking.save()
            
            # Update trip available seats
            trip = booking.trip
            trip.available_seats += 1
            trip.save()
            
            # Update seat-trip status
            seat_trip = SeatTrip.objects.get(trip=trip, seat=booking.seat)
            seat_trip.status = 'Available'
            seat_trip.save()
            
            messages.success(request, 'Yêu cầu hủy vé đã được chấp nhận!')
        except CancellationRequest.DoesNotExist:
            messages.error(request, 'Không tìm thấy yêu cầu hủy vé!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_cancellations')
    
    return redirect('admin_cancellations')

def admin_reject_cancellation(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        reject_reason = request.POST.get('reject_reason')
        
        try:
            cancellation_request = CancellationRequest.objects.get(id=request_id)
            
            # Update cancellation request
            cancellation_request.status = 'Rejected'
            cancellation_request.notes = f"Từ chối: {reject_reason}"
            cancellation_request.save()
            
            messages.success(request, 'Yêu cầu hủy vé đã bị từ chối!')
        except CancellationRequest.DoesNotExist:
            messages.error(request, 'Không tìm thấy yêu cầu hủy vé!')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
        
        return redirect('admin_cancellations')
    
    return redirect('admin_cancellations')
def admin_get_total_seats(request):
    request_id = request.GET.get('id')
    
    try:
        schedule = Schedule.objects.get(id=request_id)
        
        data = {
            'total_seats': schedule.bus.total_seats
        }
        print(data)
        return JsonResponse(data)
    except CancellationRequest.DoesNotExist:
        return JsonResponse({'error': 'Schedule request not found'}, status=404)
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