from django.contrib import admin
from .models import Profile, Customer, Owner, Inventory, Booking, Event

# Register your models here.
admin.site.register(Profile)
admin.site.register(Customer)
admin.site.register(Owner)
admin.site.register(Inventory)
admin.site.register(Booking)
admin.site.register(Event)
