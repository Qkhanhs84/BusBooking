from django.db import models
from django.utils import timezone

class BusStation(models.Model):
    PROVINCES = [
        ('DNANG', 'Đà Nẵng'),
        ('NAN', 'Nghệ An'),
        ('QNAM', 'Quảng Nam'),
        ('HNOI', 'Hà Nội'),
        ('HCMINH', 'Hồ Chí Minh'),
        ('TTTHUE', 'Thừa Thiên Huế'),
        ('QNGAI', 'Quảng Ngãi'),
        ('QTRI','Quảng Trị'),
        ('QBINH', 'Quảng Bình'),
        ('HTINH', 'Hà Tĩnh'),
        ('DLAT', 'Đà Lạt'),
        
        
    ]
    station_name = models.CharField(max_length=100)
    address = models.TextField()
    province = models.CharField(max_length=50,choices=PROVINCES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_province_code(cls,province_name):
        reversed_provinces = {v: k for k, v in cls.PROVINCES}
        return reversed_provinces.get(province_name, None)
    @classmethod
    def get_province_name(cls, province_code):
        return dict(cls.PROVINCES).get(province_code, None)
    
    def __str__(self):
        return f"{self.station_name} - {self.get_province_display()}"

class Bus(models.Model):
    BUS_TYPES = [
        ('Sitting', 'Ngồi'),
        ('Sleeper', 'Giường nằm'),
        ('SleeperVIP', 'Giường nằm VIP'),
    ]
    
    license_plate = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=10, choices=BUS_TYPES)
    total_seats = models.IntegerField()
    amenities = models.TextField(null=True, blank=True)
    surcharge = models.IntegerField(default=0,choices=[(0,0),(50,50),(100,100)]) # in VND
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.license_plate} - {self.bus_type}"

class Route(models.Model):
    route_name = models.CharField(max_length=100)
    departure_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='departures')
    arrival_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='arrivals')
    base_price = models.IntegerField(default=0) # in VND
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_duration_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def compute_time(self):
        return f'{self.estimated_duration_minutes // 60}h{(self.estimated_duration_minutes % 60) if self.estimated_duration_minutes %60 !=0 else '' }'
    
    def __str__(self):
        return f"{self.route_name} ({self.departure_station} to {self.arrival_station})"

class Schedule(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route} - {self.departure_time}"

class Trip(models.Model):
    TRIP_STATUS = [
        ('Scheduled', 'Scheduled'),
        ('Departed', 'Departed'),
        ('Arrived', 'Arrived'),
        ('Cancelled', 'Cancelled'),
    ]
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    trip_date = models.DateField()
    available_seats = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=TRIP_STATUS, default='Scheduled')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['schedule', 'trip_date']
        
    def compute_price(self):
        base_price = self.schedule.route.base_price
        surcharge = self.schedule.bus.surcharge
        return base_price + surcharge
        
    def get_available_seats(self):
        """Tính toán số ghế còn trống thực sự dựa trên số ghế đã đặt"""
        # Đếm số ghế đã đặt (có status là 'Booked')
        booked_seats_count = SeatTrip.objects.filter(
            trip=self, 
            status='Booked'
        ).count()
        
        # Tổng số ghế của xe
        total_seats = self.schedule.bus.total_seats
        
        # Số ghế còn trống
        return total_seats - booked_seats_count

    def update_available_seats(self):
        """Cập nhật trường available_seats dựa trên số ghế đã đặt"""
        booked_seats_count = SeatTrip.objects.filter(
            trip=self, 
            status='Booked'
        ).count()
        
        total_seats = self.schedule.bus.total_seats
        self.available_seats = total_seats - booked_seats_count
        self.save(update_fields=['available_seats'])
        
    def __str__(self):
        return f"{self.schedule} on {self.trip_date}"

class Seat(models.Model):
    
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    
    position_description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['bus', 'seat_number']

    def __str__(self):
        return f"{self.bus} - Seat {self.seat_number} "

class Booking(models.Model):
    BOOKING_STATUS = [
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]
    
    PAYMENT_METHODS = [
        ('QR', 'QR'),
        ('AtStation', 'At Station'),
        
    ]
    
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    pickup_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='pickups')
    dropoff_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='dropoffs')
    booking_code = models.CharField(max_length=20, unique=True)
    passenger_name = models.CharField(max_length=100)
    passenger_phone = models.CharField(max_length=20)
    passenger_email = models.EmailField()
    passenger_identity = models.CharField(max_length=20, null=True, blank=True)
    booking_status = models.CharField(max_length=10, choices=BOOKING_STATUS, default='Pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_time = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.booking_code} - {self.passenger_name}"

class CancellationRequest(models.Model):
    REQUEST_STATUS = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    REFUND_METHODS = [
        ('BankTransfer', 'Bank Transfer'),
        ('AtStation', 'At Station'),
    ]
    
    REFUND_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    request_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='Pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_method = models.CharField(max_length=12, choices=REFUND_METHODS, null=True, blank=True)
    refund_status = models.CharField(max_length=10, choices=REFUND_STATUS, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Cancellation for {self.booking.booking_code}"
class SeatTrip(models.Model):
    SEAT_STATUS = [
        ('Available', 'Còn trống'),
        ('Booked', 'Đã đặt'),
        ('InProgress', 'Đang tiến hành'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=SEAT_STATUS, default='Available')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['trip', 'seat']

    def __str__(self):
        return f"Trip {self.trip.id} - Seat {self.seat.seat_number} - {self.get_status_display()}"

class BookingSeat(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='booking_seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['booking', 'seat']
        
    def __str__(self):
        return f"{self.booking.booking_code} - Seat {self.seat.seat_number}"

