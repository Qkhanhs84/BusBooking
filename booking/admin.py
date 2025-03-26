from django.contrib import admin
from .models import  BusStation,Bus,Route,Schedule,Trip,Seat,Booking,CancellationRequest,PriceList


admin.site.register(BusStation)
admin.site.register(Bus)
admin.site.register(Route)
admin.site.register(Schedule)
admin.site.register(Trip)
admin.site.register(Seat)
admin.site.register(Booking)
admin.site.register(CancellationRequest)
admin.site.register(PriceList)



