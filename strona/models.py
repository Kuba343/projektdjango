from django.contrib.auth.models import User
from django.db import models

# Create your models here.

# TABELE SŁOWNIKOWE:
class Brand(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class CarCategory(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class FuelType(models.Model):
    FUEL_CHOICES=[
        ('Benzyna', 'Benzyna'),
        ('Diesel', 'Diesel'),
        ('Benzyna + Gaz', 'Benzyna + Gaz'),
        ('Elektryczny', 'Elektryczny'),
        ('Hybryda', 'Hybryda'),
    ]
    name=models.CharField(max_length=20,choices=FUEL_CHOICES)
    def __str__(self):
        return self.name

class RentalStatus(models.Model):
    STATUS_CHOICES=[
        ('Oczekująca','Oczekująca'),#Czeka na platnosc
        ('Potwierdzona', 'Potwierdzona'),#Zaplacone
        ('W trakcie', 'W trakcie'),#Samochod  u klienta
        ('Zwrócona', 'Zwrócona'),#Samochód wrocil
        ('Anulowana','Anulowana'),#Anulowane
    ]
    status=models.CharField(max_length=20,choices=STATUS_CHOICES)
    def __str__(self):
        return self.status

class PaymentMethod(models.Model):
    PAYMENT_CHOICES=[
        ('Blik','Blik'),
        ('Karta', 'Karta'),
        ('Przelew', 'Przelew'),
        ('Gotówka', 'Gotówka'),#przy odbiorze gotówka
    ]
    name=models.CharField(max_length=20,choices=PAYMENT_CHOICES)
    def __str__(self):
        return self.name

class City(models.Model):
    name=models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)  # np. 00-001
    def __str__(self):
        return f"{self.zip_code} {self.name}"

class Role(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class InspectionItem(models.Model):
    name=models.CharField(max_length=50)# np. Stan opon, Hamulce
    def __str__(self):
        return self.name

class AddonType(models.Model):
    name=models.CharField(max_length=50)#np. Akcesoria, Ubezpieczenie
    def __str__(self):
        return self.name
# TABELE GŁÓWNE:
#FLOTA
class CarModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Street(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Branch(models.Model):
    street = models.ForeignKey(Street, on_delete=models.CASCADE)
    building_number = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.street} {self.building_number} {self.phone_number}"

class Car(models.Model):
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    category = models.ForeignKey(CarCategory, on_delete=models.SET_NULL,null=True)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.SET_NULL,null=True)
    current_branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    horsepower = models.IntegerField()
    price_per_day=models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.model} {self.category}"


class Transfer(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    from_branch = models.ForeignKey(Branch, related_name='transfers_from', on_delete=models.CASCADE)
    to_branch = models.ForeignKey(Branch, related_name='transfers_to', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
#REZERWACJE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=40)
    phone_number = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.user} {self.license_number} {self.phone_number}"

class Rental(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    car=models.ForeignKey(Car, on_delete=models.CASCADE)
    status=models.ForeignKey(RentalStatus, on_delete=models.PROTECT)
    pickup_date=models.DateField()
    return_date=models.DateField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2,null=True)
    def __str__(self):
        return f"{self.user} {self.status} {self.pickup_date} {self.return_date}"

class Payment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.method} {self.amount} {self.timestamp}"

class Invoice(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE) # Poprawka na 1:1
    invoice_number = models.CharField(max_length=50, unique=True)
    tax_id = models.CharField(max_length=20, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Faktura nr: {self.invoice_number} (Dla: {self.rental.user})"

#OBSLUGA
class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True)
    employee_id_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"

class Addon(models.Model):
    type = models.ForeignKey(AddonType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    daily_price = models.DecimalField(max_digits=6, decimal_places=2)
    def __str__(self):
        return f"{self.type} {self.name} {self.daily_price}"

class RentalAddon(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    def __str__(self):
        return f"{self.rental} {self.addon} {self.quantity}"

class DamageReport(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reported_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.car} {self.description} {self.estimated_cost} {self.reported_at}"

class Maintenance(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    item = models.ForeignKey(InspectionItem, on_delete=models.CASCADE)
    last_service_date = models.DateField()
    mileage_at_service = models.IntegerField()
    def __str__(self):
        return f"{self.car} {self.item} {self.last_service_date} {self.mileage_at_service}"