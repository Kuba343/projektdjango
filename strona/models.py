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
    def __str__(self):
        return self.name
class Role(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name
class InspectionItem(models.Model):
    name=models.CharField(max_length=50)# np. Stan opon, Hamulce
    def __str__(self):
        return self.name
class Addon(models.Model):
    name=models.CharField(max_length=50)#np. Akcesoria, Ubezpieczenie
    def __str__(self):
        return self.name
# TABELE GŁÓWNE: