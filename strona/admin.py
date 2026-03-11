from django.contrib import admin
from .models import *

# Rejestracja słowników
admin.site.register([
    Brand, CarCategory, FuelType, RentalStatus,
    PaymentMethod, City, Role, InspectionItem, AddonType
])

# Rejestracja ważnych tabel

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('model','price_per_day','is_available')
    list_filter = ('is_available',)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'pickup_date', 'return_date', 'status')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('street', 'building_number', 'phone_number')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role' ,'phone_number')

# Rejestracja reszty modeli
admin.site.register([
    CarModel, Street, Transfer,Payment, Invoice, Addon,RentalAddon, DamageReport, Maintenance
])