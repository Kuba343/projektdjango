from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, ContactForm
from .models import Car, Addon, Branch, Rental
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as django_logout
from django.db.models import Q
from .models import Car, Addon
from django.shortcuts import render
from datetime import datetime, date


def home(request):
    cars = Car.objects.all() # Pobieramy wszystkie auta
    return render(request, 'home.html', {'cars': cars})
#podstrona cars
def car_list(request):
    city = request.GET.get('city')
    start = request.GET.get('start')
    end = request.GET.get('end')
    cars = Car.objects.all()

    if city:
        cars=cars.filter(branch__city__icontains=city)
    return render(request, "rentalrent.html", {"cars": cars, "city": city})

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, "rejestracja.html", {"form": form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                # Szukamy usera po mailu
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)

                if user is not None:
                    auth_login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, "Błędne hasło.")
            except User.DoesNotExist:
                messages.error(request, "Użytkownik o takim adresie e-mail nie istnieje.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    django_logout(request) # To wylogowuje użytkownika
    return redirect('home')

def contact_view(request):
    # Na razie tylko wyświetlamy pustą stronę, żeby błąd zniknął
    return render(request, 'contact.html')

def about_view(request):
    # Na razie tylko wyświetlamy pustą stronę, żeby błąd zniknął
    return render(request, 'about.html')

def calculator_view(request):
    # Na razie tylko wyświetlamy pustą stronę, żeby błąd zniknął
    return render(request, 'calculator.html')


def contact_view(request):
    oddzialy = Branch.objects.all()


    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            temat = f"Nowa wiadomość od: {contact.name}"

            tresc = f"""
Masz nową wiadomość z formularza kontaktowego:

Od: {contact.name}
E-mail klienta: {contact.email}

Treść wiadomości:
{contact.body}

---
Wiadomość zapisana w bazie o ID: {contact.id}
"""

            try:
                send_mail(
                    temat,
                    tresc,
                    settings.EMAIL_HOST_USER,
                    ['wypozyczalniastrona@gmail.com'],
                    fail_silently=False,
                )


                send_mail(
                    "Dziękujemy za kontakt",
                    "Otrzymaliśmy Twoją wiadomość. Odpowiemy wkrótce.",
                    settings.EMAIL_HOST_USER,
                    [contact.email],
                    fail_silently=False,
                )

                messages.success(request, 'Dziękujemy! Wiadomość została wysłana.')

            except Exception as e:
                print(f"Błąd wysyłki: {e}")
                messages.warning(
                    request,
                    'Wiadomość zapisana, ale wystąpił problem z e-mailem.'
                )

            return redirect('contact')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


#Podstrona calculator
def get_available_cars(start, end):
    return Car.objects.exclude(
        rental__pickup_date__lt=end,
        rental__return_date__gt=start
    )

def search_cars(request):
    cars = Car.objects.none()
    start_date = None
    end_date = None

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

            cars = get_available_cars(start, end)

    return render(request, "calculator.html", {
        "cars": cars,
        "start_date": start_date,
        "end_date": end_date
    })



def calculate_rental_price(car, start, end, addons=None):
    days = (end - start).days

    if days <= 0:
        days = 1

    base_price = car.price_per_day * days

    addons_cost = 0
    if addons:
        for addon in addons:
            addons_cost += addon.daily_price * days

    return base_price + addons_cost


def calculate_view(request, car_id):
    car = Car.objects.get(id=car_id)

    # Pobieramy daty z GET
    start = request.GET.get("start")
    end = request.GET.get("end")

    # Jeśli GET jest pusty → STOP
    if not start or not end:
        return HttpResponse("Brak dat w zapytaniu. Wróć do wyszukiwarki aut.")

    # Zamieniamy GET na date
    start = datetime.strptime(start, "%Y-%m-%d").date()
    end = datetime.strptime(end, "%Y-%m-%d").date()

    addons = []
    price = None

    # Obsługa POST
    if request.method == "POST":
        addons_ids = request.POST.getlist("addons")
        addons = Addon.objects.filter(id__in=addons_ids)

        price = calculate_rental_price(car, start, end, addons)

    return render(request, "calculate.html", {
        "car": car,
        "addons": addons,
        "price": price,
        "start": start,
        "end": end
    })
def rent_page(request):
    city=request.GET.get("city")
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = date.today()
    today_str = str(today)

    cars=Car.objects.all()

    #to filtruje po miescie
    if city and city != "":
        cars = cars.filter(current_branch__street__city__name__icontains=city)    #to filtruje po terminie

    #blokada to samo co w skrypcie zeby szukac tylko w przyszlosci
    if start_date and start_date < today_str:
        start_date=today_str

    if start_date and end_date and end_date < start_date:
        end_date = start_date

    #tutaj filtruje po dostepnosci rental
    if start_date and end_date:
        try:
            # Szukamy rezerwacji nakładających się na termin
            occupied_cars_ids = Rental.objects.filter(
                Q(pickup_date__range=[start_date, end_date]) |
                Q(return_date__range=[start_date, end_date]) |
                Q(pickup_date__lte=start_date, return_date__gte=end_date)
            ).values_list('car_id', flat=True)

        # Wykluczamy te auta z listy dostępnych
            cars = cars.exclude(id__in=occupied_cars_ids)
        except ValueError:
            # kolejna zapora przed blednymi datami
            pass
    context = {
        "cars": cars,
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "today": today_str
    }
    return render(request, "rent.html", context)

