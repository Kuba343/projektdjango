from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import RegistrationForm, LoginForm
from .models import Car, Addon
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as django_logout

def home(request):
    return render(request, "home.html")
#podstrona cars
def car_list(request):
    cars = Car.objects.all()
    return render(request, "car_list.html", {"cars": cars})

#podstrona cars/car_detail
def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    addons = Addon.objects.all()
    return render(request, "car_detail.html", {"car": car, "addons": addons})

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

def mail_view(request):
    # Na razie tylko wyświetlamy pustą stronę, żeby błąd zniknął
    return render(request, 'mail.html')

def calculator_view(request):
    # Na razie tylko wyświetlamy pustą stronę, żeby błąd zniknął
    return render(request, 'calculator.html')