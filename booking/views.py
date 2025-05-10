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

def research(request):
    if request.method == 'GET' and 'phone' in request.GET:
        phone = request.GET.get('phone')
        # Tìm tất cả các đặt vé có số điện thoại này
        bookings = Booking.objects.filter(passenger_phone=phone)
        
        if bookings.exists():
            context = {
                'bookings': bookings,
                'phone': phone,
                'found': True
            }
        else:
            context = {
                'phone': phone,
                'found': False
            }
        return render(request, "booking/research.html", context)
    
    return render(request, "booking/research.html")

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


def booking_detail(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        context = {
            'booking': booking,
        }
        return render(request, 'booking/booking_detail.html', context)
    except Booking.DoesNotExist:
        return redirect('research')

@csrf_exempt
def cancel_booking(request):
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'cancelled'
            booking.save()
            
            # Tạo yêu cầu hủy vé
            CancellationRequest.objects.create(
                booking=booking,
                reason="Hủy bởi khách hàng",
                status="approved"
            )
            
            # Cập nhật trạng thái ghế
            for seat in booking.seats.all():
                seat.is_booked = False
                seat.save()
                
            return redirect('research')
        except Booking.DoesNotExist:
            pass
    
    return redirect('research')