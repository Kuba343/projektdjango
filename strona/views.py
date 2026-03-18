from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404

from .forms import RegistrationForm
from .models import Car, Addon

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