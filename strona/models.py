from datetime import date

from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, connection


#funkcja walidujaca wiek
def validate_age(value):
    today = timezone.now().date()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError("Musisz mieć ukończone 18 lat, aby założyć konto.")


# TABELE SŁOWNIKOWE:
#Lista marek
class Brand(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name
#Segmenty aut
class CarCategory(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name
#Typ paliwa
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
#Etapy rezerwacji
class RentalStatus(models.Model):
    STATUS_CHOICES=[
        ('Oczekująca','Oczekująca'),#Czeka na platnosc
        ('Opłacona', 'Opłacona'),#Zaplacone
        ('W trakcie', 'W trakcie'),#Samochod  u klienta
        ('Zwrócona', 'Zwrócona'),#Samochód wrocil
        ('Anulowana','Anulowana'),#Anulowane
    ]
    name=models.CharField(max_length=20,choices=STATUS_CHOICES)
    def __str__(self):
        return self.name
#Dostepne metody platnosci
class PaymentMethod(models.Model):
    PAYMENT_CHOICES=[
        ('Blik','Blik'),
        ('Karta', 'Karta'),
        ('Przelew', 'Przelew'),
    ]
    name=models.CharField(max_length=20,choices=PAYMENT_CHOICES)
    def __str__(self):
        return self.name
#Miasta w ktorych mamy oddzialy
class City(models.Model):
    name=models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)  # np. 00-001
    def __str__(self):
        return f"{self.zip_code} {self.name}"
#Stanowisko pracownika
class Role(models.Model):
    name=models.CharField(max_length=50) # np. mechanik, administrator itp.
    def __str__(self):
        return self.name
#Elementy sprawdzane podczas serwisu
class InspectionItem(models.Model):
    name=models.CharField(max_length=50)# np. Stan opon, Hamulce
    def __str__(self):
        return self.name
#Rodzaje dodatkow typu akcesoria, ubezpieczenie
class AddonType(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name
# TABELE GŁÓWNE:
#FLOTA
#Łączy marke z konkretna nazwa modelu
class CarModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name
#Lista ulic w konkretnych miastach
class Street(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
#Oddzialy naszej firmy
class Branch(models.Model):
    street = models.ForeignKey(Street, on_delete=models.CASCADE)
    building_number = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20)

    def get_car_count(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT public.oblicz_ilosc_aut_w_oddziale(%s)", [self.id])
            result = cursor.fetchone()
        return result[0] if result else 0

    def __str__(self):
        return f"{self.street} {self.building_number} {self.phone_number}"
#Konkretne auto
class Car(models.Model):
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    category = models.ForeignKey(CarCategory, on_delete=models.PROTECT)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.PROTECT)
    current_branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    horsepower = models.IntegerField()
    mileage=models.IntegerField()
    year = models.IntegerField()
    color=models.CharField(max_length=50)
    price_per_day=models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='cars/', null=True, blank=True)
    def __str__(self):
        return f"{self.model} {self.category}"

#Historia przemieszczania auta
class Transfer(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    from_branch = models.ForeignKey(Branch,verbose_name="Z oddziału", related_name='transfers_from', on_delete=models.CASCADE)
    to_branch = models.ForeignKey(Branch,verbose_name="Do oddziału", related_name='transfers_to', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

# 1. Zasada:dokładnie 9 cyfr lub format z ukośnikami
license_validator = RegexValidator(
    regex=r'^[0-9]{5}/[0-9]{2}/[0-9]{2}$|^[0-9]{9}$',
    message="Numer prawa jazdy musi mieć 9 cyfr (np. 123456789) lub format 12345/67/89."
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    license_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,  #jeden numer dokumentu na jedno konto
        validators=[license_validator]
    )
    phone_validator = RegexValidator(
        regex=r'^\d{9,15}$',
        message="Numer telefonu musi składać się wyłącznie z cyfr (od 9 do 15)."
    )

    phone_number = models.CharField(
        max_length=15,
        validators=[phone_validator],
        help_text="Wpisz numer bez spacji i znaku '+' z początkiem kierunkowym"
    )
    birth_date = models.DateField(validators=[validate_age], verbose_name="Data urodzenia")

    def clean(self):
        # To wymusza uruchomienie walidatorów pól w panelu Admina i formularzach
        super().clean()
        if self.birth_date:
            validate_age(self.birth_date)

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"

#REZERWACJE
#Tabela ktora laczy klienta z samochodem i datami wypozyczen
class Rental(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    car=models.ForeignKey(Car, on_delete=models.CASCADE)
    status=models.ForeignKey(RentalStatus, on_delete=models.PROTECT)
    pickup_date=models.DateField()
    return_date=models.DateField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user} {self.status} {self.pickup_date} {self.return_date}"
#Rejestr wplat
class Payment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rental=models.ForeignKey(Rental, on_delete=models.CASCADE,related_name='payments', null=True)
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.method} {self.amount} {self.timestamp}"
#Faktura do konkretnego wynajmu
class Invoice(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE) # Poprawka na 1:1
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Faktura nr: {self.invoice_number} (Dla: {self.rental.user})"

    STATUS_CHOICES = [
        ("PAID", "Opłacona"),
        ("PENDING", "Oczekująca"),
        ("CANCELLED", "Anulowana"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PAID")

#OBSLUGA
#Dane pracownikow
class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True)
    work_phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"
#Konkretne produkty dodatkowe
class Addon(models.Model):
    type = models.ForeignKey(AddonType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    daily_price = models.DecimalField(max_digits=6, decimal_places=2)
    def __str__(self):
        return f"{self.type} {self.name} {self.daily_price}"
#Tabela laczaca jakie dodatki i ilosci klient dobral
class RentalAddon(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    def __str__(self):
        return f"{self.rental} {self.addon} {self.quantity}"
#Rejestr szkod
class DamageReport(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reported_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.car} {self.description} {self.estimated_cost} {self.reported_at}"
#Ksiazka serwisowa auta
class Maintenance(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    item = models.ForeignKey(InspectionItem, on_delete=models.CASCADE)
    last_service_date = models.DateField()
    mileage_at_service = models.IntegerField()

    def __str__(self):
        return f"{self.car} {self.item} - {self.last_service_date}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) # Data odebrania wiadomości

    def __str__(self):
        return f"Wiadomość od {self.name} ({self.email})"
#Odpowiada za stan przed i po
class RentalInspection(models.Model):
    INSPECTION_TYPES = [
        ('PICKUP', 'Wydanie (Stan Przed)'),
        ('RETURN', 'Zwrot (Stan Po)'),
    ]

    rental = models.ForeignKey('Rental', on_delete=models.CASCADE, related_name='inspections')
    inspection_type = models.CharField(max_length=10, choices=INSPECTION_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    mileage = models.PositiveIntegerField(
        verbose_name="Przebieg",
        blank=True,
        null=True
    )

    fuel_level = models.PositiveIntegerField(default=100, verbose_name="Poziom paliwa %")
    description = models.TextField(blank=True, null=True, verbose_name="Uwagi / Uszkodzenia")

    class Meta:
        unique_together = ('rental', 'inspection_type')

    def __str__(self):
        return f"{self.get_inspection_type_display()} - Rezerwacja {self.rental.id}"

    def save(self, *args, **kwargs):
        # 1. Jeśli to wydanie (PICKUP) i pole przebiegu jest puste,
        # pobieramy aktualny przebieg z auta
        if self.inspection_type == 'PICKUP' and not self.mileage:
            if self.rental.car:
                self.mileage = self.rental.car.mileage

        # 2. Zapisujemy protokół
        super().save(*args, **kwargs)

        # 3. Jeśli to zwrot (RETURN) i podano przebieg, aktualizujemy auto
        if self.inspection_type == 'RETURN' and self.mileage:
            car = self.rental.car
            if car:
                car.mileage = self.mileage
                car.save()