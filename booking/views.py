from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from .models import BusStation, Bus, Route, Schedule, Trip, Seat, Booking, CancellationRequest, SeatTrip,BookingSeat
from django.db import models
from django.db.models import *
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import qrcode
import os
import urllib.parse
import requests
import base64
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
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
    
    # Cập nhật available_seats cho tất cả chuyến đi
    for trip in trips:
        trip.update_available_seats()
    
    # Tính thời gian hiện tại
    current_datetime = timezone.now()
    
    # Đánh dấu các chuyến đã chạy (departure_time < current_time)
    trips_with_status = []
    for trip in trips:
        # Kết hợp ngày của chuyến và giờ khởi hành để tạo datetime đầy đủ
        departure_datetime = datetime.combine(
            trip.trip_date,
            trip.schedule.departure_time
        )
        # Chuyển về timezone-aware datetime nếu cần
        if timezone.is_naive(departure_datetime):
            departure_datetime = timezone.make_aware(departure_datetime)
        
        # Kiểm tra xem chuyến đã chạy chưa
        is_departed = current_datetime > departure_datetime
        
        trips_with_status.append({
            'trip': trip,
            'is_departed': is_departed
        })
    
    provinces = list(BusStation.PROVINCES)
    
    
    context = {
        'from_location': from_location,
        'to_location': to_location,
        'departure_province': departure_province,
        'arrival_province': arrival_province,
        'date': parsed_date,
        'trips_with_status': trips_with_status,
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
        payment_method = request.POST.get("payment_method")
        trip_id = request.POST.get("trip_id")
        
        # Lưu thông tin vào session
        request.session["payment_method"] = payment_method
        print("payment_method", payment_method)
        request.session["passenger_email"] = passenger_email
        request.session["passenger_name"] = passenger_name
        request.session["passenger_phone"] = passenger_phone
        request.session["selected_seats"] = selected_seats
        request.session["trip_id"] = trip_id
        
        seats = SeatTrip.objects.filter(id__in=selected_seats)
        seats_number = ",".join([seat.seat.seat_number for seat in seats])
        context = {
            "passenger_email": passenger_email,
            "passenger_name": passenger_name,
            "passenger_phone": passenger_phone,
            "selected_seats": selected_seats,
            "seats_number": seats_number,
            "trip_id": trip_id,
        }
        return render(request, "booking/verify.html", context)



    
    # Nếu không phải POST request, trả về lỗi
    return JsonResponse({"error": "Phương thức không được hỗ trợ"}, status=405)
@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        input_otp = request.POST.get("otp")
        session_otp = str(request.session.get("otp"))

        if input_otp == session_otp:
            # Xác thực thành công -> có thể xóa OTP khỏi session nếu muốn
            del request.session["otp"]
            # Chuyển hướng đến trang xác nhận thanh toán
            return JsonResponse({"message": "OTP hợp lệ", "redirect": "/payment_confirmation/"})
        else:
            return JsonResponse({"error": "OTP không đúng hoặc đã hết hạn"}, status=400)

    return JsonResponse({"error": "Yêu cầu không hợp lệ"}, status=400)

def payment_confirmation(request):
    # Lấy thông tin từ session
    passenger_name = request.session.get("passenger_name")
    passenger_email = request.session.get("passenger_email")
    passenger_phone = request.session.get("passenger_phone")
    selected_seats = request.session.get("selected_seats")
    payment_method = request.session.get("payment_method")
    
    # Debug: In ra payment_method để xác nhận
    print(f"DEBUG - Payment Method: {payment_method}")
    
    # Kiểm tra xem các dữ liệu cần thiết có tồn tại không
    if not selected_seats or not payment_method:
        # Nếu không có thông tin ghế đã chọn hoặc phương thức thanh toán, chuyển hướng về trang chủ
        return redirect('home')
    
    # Lấy thông tin về chuyến đi từ ID trong session
    trip_id = request.session.get("trip_id")
    if not trip_id:
        return redirect('home')
    
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return redirect('home')
    
    # Tính tổng giá tiền
    total_price = trip.compute_price() * len(selected_seats)
    
    # Lấy thông tin về số ghế
    seats = SeatTrip.objects.filter(id__in=selected_seats)
    if not seats.exists():
        return redirect('home')
        
    seats_number = ",".join([seat.seat.seat_number for seat in seats])
    
    context = {
        "trip": trip,
        "passenger_name": passenger_name,
        "passenger_phone": passenger_phone,
        "passenger_email": passenger_email,
        "selected_seats": selected_seats,
        "seats_number": seats_number,
        "payment_method": payment_method,
        "total_price": total_price,
    }    # Nếu thanh toán tại trạm, tạo mã đặt vé ngay
    if payment_method == "AtStation":
        booking_code = generate_booking_code()
        context["booking_code"] = booking_code
        
        # Tạo đối tượng Booking
        booking = create_booking(trip, seats, passenger_name, passenger_phone, 
                      passenger_email, payment_method, total_price, booking_code)
        
        # Xóa session để tránh create_booking được gọi lại
        if "selected_seats" in request.session:
            del request.session["selected_seats"]
        if "payment_method" in request.session:
            del request.session["payment_method"]
            
        # Gửi email xác nhận cho khách hàng
        try:
            # Lấy danh sách ghế để hiển thị trong email
            booking_seats = BookingSeat.objects.filter(booking=booking)
            seats_list = [bs.seat.seat_number for bs in booking_seats]
            seats_str = ", ".join(seats_list)
            
            # Format date và time cho email
            trip_date = trip.trip_date.strftime('%d/%m/%Y')
            departure_time = trip.schedule.departure_time.strftime('%H:%M')
            
            subject = 'Xác nhận đặt vé - BUSBOOKING'
            message = f'''Xin chào {passenger_name},

Cảm ơn bạn đã đặt vé trên hệ thống BUSBOOKING. Dưới đây là thông tin vé của bạn:

THÔNG TIN VÉ:
- Mã vé: {booking_code}
- Tuyến đường: {trip.schedule.route.route_name}
- Ngày khởi hành: {trip_date}
- Giờ khởi hành: {departure_time}
- Số ghế: {seats_str}
- Tổng tiền: {total_price}.000 VND
- Phương thức thanh toán: Thanh toán tại trạm

Vui lòng đến trạm xe trước giờ khởi hành ít nhất 15 phút và mang theo mã đặt vé của bạn.

Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.

BUSBOOKING
'''
            
            send_mail(
                subject,
                message,
                'noreply@busbooking.com',
                [passenger_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
      # Nếu thanh toán qua ngân hàng, tạo mã QR VietQR
    elif payment_method == "QR":
        # Tạo một mã tạm thời cho file QR
        temp_code = f"temp_{int(timezone.now().timestamp())}"
        
        # Thông tin ngân hàng theo chuẩn Napas
        # Danh sách mã ngân hàng: https://api.vietqr.io/v2/banks
        bank_id = "970422"  # MB Bank (Military Commercial Joint Stock Bank)
        account_number = "0764077235"  # Số tài khoản mẫu
        account_name = "VO TRAN QUOC KHANH"
        
        # Nội dung chuyển khoản
        description = f"BUS_{trip.schedule.route.route_name}_{passenger_name}"
        
        # Tạo mã QR
        qr_filename = generate_vietqr(bank_id, account_number, account_name, 
                                     int(total_price * 1000), description, temp_code)
        
        # Thêm thông tin vào context
        context["bank_name"] = "MB Bank"
        context["account_number"] = account_number
        context["account_name"] = account_name
        context["qr_filename"] = qr_filename
        context["description"] = description
    
    return render(request, "booking/payment_confirmation.html", context)

def complete_payment(request):
    # Xử lý khi người dùng đã thanh toán qua QR
    if request.method == "POST":
        # Lấy thông tin từ session
        passenger_name = request.session.get("passenger_name")
        passenger_email = request.session.get("passenger_email")
        passenger_phone = request.session.get("passenger_phone")
        selected_seats = request.session.get("selected_seats")
        payment_method = request.session.get("payment_method")
        trip_id = request.session.get("trip_id")
        
        # Debug: In ra payment_method để xác nhận
        print(f"DEBUG - Complete Payment Method: {payment_method}")
        
        # Chỉ xử lý nếu payment_method là QR:
        if payment_method == "QR":
            # Lấy thông tin về chuyến đi
            trip = Trip.objects.get(id=trip_id)
            
            # Tính tổng giá tiền
            total_price = trip.compute_price() * len(selected_seats)
            
            # Lấy thông tin về số ghế
            seats = SeatTrip.objects.filter(id__in=selected_seats)
            
            # Tạo mã đặt vé
            booking_code = generate_booking_code()
            
            # Tạo đối tượng Booking với trạng thái thanh toán là 'Pending'
            booking = create_booking(trip, seats, passenger_name, passenger_phone, 
                        passenger_email, payment_method, total_price, booking_code)
            
            # Xóa session để tránh create_booking được gọi lại
            if "selected_seats" in request.session:
                del request.session["selected_seats"]
            if "payment_method" in request.session:
                del request.session["payment_method"]
                
            # Thông báo cho admin về việc có booking mới cần xác nhận thanh toán
            try:
                # Gửi email đến admin
                admin_email = 'quockhanh08042004@gmail.com'  # Thay bằng email thực tế của admin
                send_mail(
                    'Booking mới cần xác nhận thanh toán',
                    f'Có một booking mới cần xác nhận thanh toán:\n\n'
                    f'Mã booking: {booking_code}\n'
                    f'Hành khách: {passenger_name}\n'
                    f'Email: {passenger_email}\n'
                    f'Số điện thoại: {passenger_phone}\n'
                    f'Tổng tiền: {total_price}.000 VND\n\n'
                    f'Vui lòng kiểm tra hệ thống quản trị để xác nhận thanh toán.',
                    'noreply@busbooking.com',
                    [admin_email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error sending admin notification: {e}")
                
            return JsonResponse({"success": True, "booking_code": booking_code})
        else:
            return JsonResponse({"error": "Phương thức thanh toán không hợp lệ"}, status=400)
    
    return JsonResponse({"error": "Yêu cầu không hợp lệ"}, status=400)

def generate_booking_code():
    # Tạo mã đặt vé ngẫu nhiên
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    code = ''.join(random.choice(letters + numbers) for _ in range(8))
    return code

def create_booking(trip, seats, passenger_name, passenger_phone, passenger_email, 
                  payment_method, total_price, booking_code):
    # Tạo đối tượng Booking
    booking = Booking(
        trip=trip,
        pickup_station=trip.schedule.route.departure_station,
        dropoff_station=trip.schedule.route.arrival_station,
        booking_code=booking_code,
        passenger_name=passenger_name,
        passenger_phone=passenger_phone,        passenger_email=passenger_email,
        booking_status="Pending",
        payment_method=payment_method,
        payment_status="Pending" if payment_method == "QR" else "Paid",
        total_price=total_price
    )
    booking.save()
    
    # Tạo các đối tượng BookingSeat để liên kết Booking với các ghế đã đặt
    
    
    for seat_trip in seats:
        # Tạo liên kết giữa booking và ghế
        BookingSeat.objects.create(
            booking=booking,
            seat=seat_trip.seat
        )
          # Cập nhật trạng thái ghế
        seat_trip.status = "Booked"
        seat_trip.save()
    
    # Cập nhật số ghế còn trống của chuyến
    trip.update_available_seats()
        
    return booking

def generate_vietqr(bank_id, account_number, account_name, amount, description, booking_id):
    
    
    
    client_id = os.environ.get('VIETQR_CLIENT_ID', 'daa03e38-9f24-44cf-9b71-062114de1d5c')
    api_key = os.environ.get('VIETQR_API_KEY', 'b6aa0bcb-52ef-4601-8b3f-c8c904c5a20d')
    
    # URL API
    api_url = "https://api.vietqr.io/v2/generate"
    
    # Chuẩn bị headers và payload
    headers = {
        'x-client-id': client_id,
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "accountNo": account_number,
        "accountName": account_name,
        "acqId": bank_id,           # Mã ngân hàng theo chuẩn Napas
        "addInfo": description,      # Nội dung chuyển khoản
        "amount": str(amount),       # Số tiền, chuyển sang string
        "template": "compact"        # Template cho QR
    }
    
    try:
        # Gọi API để tạo QR
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Kiểm tra kết quả
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == '00':
                # Lấy dữ liệu QR dạng base64
                qr_base64 = result.get('data', {}).get('qrDataURL', '')
                
                # Xử lý chuỗi base64 (bỏ phần header nếu có)
                if ',' in qr_base64:
                    qr_base64 = qr_base64.split(',')[1]
                
                # Lưu hình ảnh vào thư mục static/images
                static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
                os.makedirs(static_dir, exist_ok=True)
                
                # Tạo tên file duy nhất
                filename = f'vietqr_{booking_id}.png'
                file_path = os.path.join(static_dir, filename)
                
                # Giải mã base64 và lưu file
                with open(file_path, "wb") as file:
                    file.write(base64.b64decode(qr_base64))
                
                return filename
    except Exception as e:
        print(f"Error generating VietQR: {e}")
    
    # Nếu có lỗi hoặc không thành công, sử dụng phương pháp dự phòng
    # Tạo QR code bằng thư viện qrcode
    payment_info = f"Chuyển khoản: {amount} VND\nTK: {account_number}\nNgân hàng: {bank_id}\nNội dung: {description}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Thêm dữ liệu vào QR code
    qr.add_data(payment_info)
    qr.make(fit=True)
    
    # Tạo hình ảnh QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Lưu hình ảnh vào thư mục static/images
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
    os.makedirs(static_dir, exist_ok=True)
      # Tạo tên file duy nhất
    filename = f'vietqr_{booking_id}.png'
    file_path = os.path.join(static_dir, filename)    
    img.save(file_path)
    
    return filename

def ticket_lookup(request):
    """
    View for looking up a ticket by booking code
    """
    if request.method == 'POST':
        booking_code = request.POST.get('booking_code')
        try:
            booking = Booking.objects.get(booking_code=booking_code)
            return redirect('ticket_details', booking_code=booking_code)
        except Booking.DoesNotExist:
            return render(request, 'booking/ticket_lookup.html', {
                'error_message': 'Không tìm thấy vé với mã đặt vé này. Vui lòng kiểm tra lại.'
            })
    
    return render(request, 'booking/ticket_lookup.html')

def ticket_details(request, booking_code):
    """
    View for showing the details of a ticket
    """
    booking = get_object_or_404(Booking, booking_code=booking_code)
    booking_seats = BookingSeat.objects.filter(booking=booking)
    
    # Check if the trip has already departed
    current_datetime = timezone.now()
    departure_datetime = datetime.combine(
        booking.trip.trip_date,
        booking.trip.schedule.departure_time
    )
    
    # Convert to timezone-aware if needed
    if timezone.is_naive(departure_datetime):
        departure_datetime = timezone.make_aware(departure_datetime)
    
    is_departed = current_datetime > departure_datetime
    
    return render(request, 'booking/ticket_details.html', {
        'booking': booking,
        'booking_seats': booking_seats,
        'is_departed': is_departed
    })

def cancel_ticket(request, booking_code):
    """
    View for cancelling a ticket
    """
    booking = get_object_or_404(Booking, booking_code=booking_code)
    
    # Check if the trip has already departed
    current_datetime = timezone.now()
    departure_datetime = datetime.combine(
        booking.trip.trip_date,
        booking.trip.schedule.departure_time
    )
    
    # Convert to timezone-aware if needed
    if timezone.is_naive(departure_datetime):
        departure_datetime = timezone.make_aware(departure_datetime)
    
    # If the trip has already departed, don't allow cancellation
    if current_datetime > departure_datetime:
        messages.error(request, 'Không thể hủy vé cho chuyến xe đã khởi hành.')
        return redirect('ticket_details', booking_code=booking_code)
    
    # If the booking is already cancelled, don't allow cancellation again
    if booking.booking_status == 'Cancelled':
        messages.error(request, 'Vé này đã được hủy trước đó.')
        return redirect('ticket_details', booking_code=booking_code)
    
    # Create a cancellation request
    cancellation_request = CancellationRequest(
        booking=booking,
        status='Approved',  # Auto-approve the cancellation
        refund_amount=booking.total_price,
        refund_method='AtStation' if booking.payment_method == 'AtStation' else 'BankTransfer',
        refund_status='Completed' if booking.payment_method == 'AtStation' else 'Pending'
    )
    cancellation_request.save()
    
    # Update the booking status
    booking.booking_status = 'Cancelled'
    booking.save()
    
    # Free up the seats
    seat_trips = []
    for booking_seat in BookingSeat.objects.filter(booking=booking):
        seat_trip = SeatTrip.objects.get(
            trip=booking.trip,
            seat=booking_seat.seat
        )
        seat_trip.status = 'Available'
        seat_trips.append(seat_trip)
    
    # Bulk update the seat trips
    SeatTrip.objects.bulk_update(seat_trips, ['status'])
    
    # Update the available seats for the trip
    booking.trip.update_available_seats()
    
    # Send email notification based on payment method
    subject = 'Xác nhận hủy vé - BUSBOOKING'
    if booking.payment_method == 'AtStation':
        message = f'''Xin chào {booking.passenger_name},

Vé của bạn đã được hủy thành công.

THÔNG TIN VÉ ĐÃ HỦY:
- Mã đặt vé: {booking.booking_code}
- Tuyến đường: {booking.trip.schedule.route.route_name}
- Ngày khởi hành: {booking.trip.trip_date.strftime('%d/%m/%Y')}
- Giờ khởi hành: {booking.trip.schedule.departure_time.strftime('%H:%M')}

Cảm ơn bạn đã sử dụng dịch vụ của BUSBOOKING.
'''
        messages.success(request, 'Vé đã được hủy thành công.')
    else:  # QR payment
        message = f'''Xin chào {booking.passenger_name},

Vé của bạn đã được hủy thành công. Để nhận lại tiền hoàn trả, vui lòng đến trạm xe và cung cấp mã đặt vé để được hỗ trợ.

THÔNG TIN VÉ ĐÃ HỦY:
- Mã đặt vé: {booking.booking_code}
- Tuyến đường: {booking.trip.schedule.route.route_name}
- Ngày khởi hành: {booking.trip.trip_date.strftime('%d/%m/%Y')}
- Giờ khởi hành: {booking.trip.schedule.departure_time.strftime('%H:%M')}
- Số tiền hoàn trả: {booking.total_price}.000 VND

Thông tin chi tiết về việc hoàn tiền sẽ được xử lý tại văn phòng của chúng tôi. Vui lòng mang theo CMND/CCCD khi đến nhận tiền hoàn trả.

Cảm ơn bạn đã sử dụng dịch vụ của BUSBOOKING.
'''
        messages.success(request, 'Vé đã được hủy thành công. Vui lòng đến trạm xe để nhận lại tiền hoàn trả.')
    
    # Send the email
    try:
        send_mail(
            subject,
            message,
            'noreply@busbooking.com',
            [booking.passenger_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")
    
    return redirect('ticket_details', booking_code=booking_code)

