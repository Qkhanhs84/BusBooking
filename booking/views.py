from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

def home(request):
    popular_routes = [
        {'from': 'Nghe An', 'to': 'Quang Binh', 'price': '200,000 VND'},
        {'from': 'Nghe An', 'to': 'Ha Noi', 'price': '250,000 VND'},
        {'from': 'Nghe An', 'to': 'Ho Chi Minh', 'price': '500,000 VND'},
    ]
    
    context = {
        'popular_routes': popular_routes,
    }
    return render(request, 'booking/home.html', context)

def search(request):
    from_location = request.GET.get('from', 'Nghe An')
    to_location = request.GET.get('to', 'Quang Binh')
    date = request.GET.get('date', '01-03-2025')
    
    # Mock data for bus schedules
    bus_schedules = [
        {
            'id': 1,
            'company': 'Hải Hoàng Gia',
            'departure_time': '06:00',
            'arrival_time': '12:00',
            'type': 'Giường nằm',
            'price': '200,000 VND',
            'available_seats': 12,
        },
        {
            'id': 2,
            'company': 'Hải Hoàng Gia',
            'departure_time': '08:30',
            'arrival_time': '14:30',
            'type': 'Giường nằm cao cấp',
            'price': '250,000 VND',
            'available_seats': 8,
        },
        {
            'id': 3,
            'company': 'Hải Hoàng Gia',
            'departure_time': '13:00',
            'arrival_time': '19:00',
            'type': 'Giường nằm',
            'price': '200,000 VND',
            'available_seats': 15,
        },
        {
            'id': 4,
            'company': 'Hải Hoàng Gia',
            'departure_time': '19:30',
            'arrival_time': '01:30',
            'type': 'Giường nằm cao cấp',
            'price': '250,000 VND',
            'available_seats': 10,
        },
    ]
    
    context = {
        'from_location': from_location,
        'to_location': to_location,
        'date': date,
        'bus_schedules': bus_schedules,
    }
    return render(request, 'booking/search.html', context)

def booking(request, schedule_id=None):
    if schedule_id is None:
        schedule_id = request.GET.get('id', '1')
    
    from_location = request.GET.get('from', 'Nghe An')
    to_location = request.GET.get('to', 'Quang Binh')
    date = request.GET.get('date', '01-03-2025')
    
    # Mock data for the selected bus
    bus_details = {
        'id': int(schedule_id),
        'company': 'Hải Hoàng Gia',
        'departure_time': '06:00',
        'arrival_time': '12:00',
        'type': 'Giường nằm',
        'price': '200,000 VND',
        'available_seats': 12,
        'departure_location': 'Bến xe Vinh, Nghệ An',
        'arrival_location': 'Bến xe Đồng Hới, Quảng Bình',
    }
    
    context = {
        'bus_details': bus_details,
        'from_location': from_location,
        'to_location': to_location,
        'date': date,
    }
    return render(request, 'booking/booking.html', context)

def about(request):
    return render(request, 'booking/about.html')

def contact(request):
    return render(request, 'booking/contact.html')

def services(request):
    return render(request, 'booking/services.html')

def news(request):
    return render(request, 'booking/news.html')

