from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.mail import send_mail
from .models import Booking, Trip, BookingSeat

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
    
    return render(request, 'booking/custom_admin/login.html')

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
    
    return render(request, 'booking/custom_admin/bookings.html', context)

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

@login_required
@user_passes_test(is_admin)
def custom_admin_trips(request):
    """Xem và quản lý danh sách chuyến đi theo ngày"""
    # Lấy ngày cần xem, mặc định là ngày hiện tại
    date_str = request.GET.get('date', '')
    
    try:
        if date_str:
            # Format: yyyy-mm-dd
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = timezone.now().date()
    except ValueError:
        # Nếu ngày không đúng định dạng, sử dụng ngày hiện tại
        selected_date = timezone.now().date()
    
    # Lấy danh sách chuyến đi trong ngày đã chọn
    trips = Trip.objects.filter(trip_date=selected_date).order_by('schedule__departure_time')
    
    # Cập nhật số ghế trống cho mỗi chuyến
    for trip in trips:
        trip.update_available_seats()
    
    # Tạo danh sách các ngày trong tuần để hiển thị bộ chọn ngày
    today = timezone.now().date()
    week_dates = []
    for i in range(-3, 4):  # 3 ngày trước và 3 ngày sau ngày hiện tại
        date = today + timezone.timedelta(days=i)
        week_dates.append({
            'date': date,
            'is_today': date == today,
            'is_selected': date == selected_date
        })
    
    context = {
        'trips': trips,
        'selected_date': selected_date,
        'week_dates': week_dates,
        # Thêm tháng tiếp theo để hiển thị lịch
        'next_month': (selected_date.replace(day=1) + timezone.timedelta(days=32)).replace(day=1)
    }
    
    return render(request, 'booking/custom_admin/trips.html', context)
