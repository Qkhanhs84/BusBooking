# booking/management/commands/create_trips.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from booking.models import Schedule, Trip, Seat, SeatTrip
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create trips and seat associations for the next 7 days'
    
    def handle(self, *args, **options):
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=7)
        
        for schedule in Schedule.objects.filter(is_active=True):
            current_date = start_date
            
            while current_date <= end_date:
                # Tạo Trip nếu chưa tồn tại
                trip, created = Trip.objects.get_or_create(
                    schedule=schedule,
                    trip_date=current_date,
                    defaults={'available_seats': schedule.bus.total_seats}
                )
                
                # Chỉ xử lý nếu Trip mới được tạo
                if created:
                    # Lấy tất cả ghế thuộc xe của Schedule
                    seats = Seat.objects.filter(bus=schedule.bus)
                    
                    # Tạo SeatTrip cho từng ghế
                    seat_trips = [
                        SeatTrip(seat=seat, trip=trip)
                        for seat in seats
                    ]
                    
                    # Bulk create để tối ưu hiệu suất
                    SeatTrip.objects.bulk_create(seat_trips)
                    
                    self.stdout.write(f"Created {len(seats)} seat trips for {trip}")
                
                current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS('Successfully created trips and seat associations'))