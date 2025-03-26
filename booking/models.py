from django.db import models
from django.utils import timezone

class BusStation(models.Model):
    station_name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.station_name} - {self.city}"

class Bus(models.Model):
    BUS_TYPES = [
        ('Sitting', 'Sitting'),
        ('Sleeper', 'Sleeper'),
    ]
    
    license_plate = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=10, choices=BUS_TYPES)
    total_seats = models.IntegerField()
    amenities = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.license_plate} - {self.bus_type}"

class Route(models.Model):
    route_name = models.CharField(max_length=100)
    departure_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='departures')
    arrival_station = models.ForeignKey(BusStation, on_delete=models.CASCADE, related_name='arrivals')
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_duration_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return f"{self.schedule} on {self.trip_date}"

class Seat(models.Model):
    SEAT_TYPES = [
        ('Regular', 'Regular'),
        ('VIP', 'VIP'),
        ('Window', 'Window'),
        ('Aisle', 'Aisle'),
        ('UpperBerth', 'Upper Berth'),
        ('LowerBerth', 'Lower Berth'),
    ]
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPES)
    position_description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['bus', 'seat_number']

    def __str__(self):
        return f"{self.bus} - Seat {self.seat_number} ({self.seat_type})"

class Booking(models.Model):
    BOOKING_STATUS = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]
    
    PAYMENT_METHODS = [
        ('QR', 'QR'),
        ('AtStation', 'At Station'),
        ('Refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
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

class PriceList(models.Model):
    SEAT_TYPES = [
        ('Regular', 'Regular'),
        ('VIP', 'VIP'),
        ('Window', 'Window'),
        ('Aisle', 'Aisle'),
        ('UpperBerth', 'Upper Berth'),
        ('LowerBerth', 'Lower Berth'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['route', 'seat_type']

    def __str__(self):
        return f"{self.route} - {self.seat_type} Price"