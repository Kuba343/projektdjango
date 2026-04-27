import hashlib
import os
from django.contrib.staticfiles import finders
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, ContactForm
from .models import Car, Addon, Branch, Rental, City, RentalStatus, PaymentMethod, UserProfile, RentalAddon, Invoice
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as django_logout
from django.db.models import Q
from .models import Car, Addon
from django.shortcuts import render
from datetime import datetime, date
from django.db import transaction, InternalError, connection, IntegrityError
from django.utils import timezone
from datetime import timedelta, date
from .forms import RegistrationForm, LoginForm, ContactForm, UserUpdateForm, ProfileUpdateForm
from weasyprint import HTML
from django.http import HttpResponse
from django.template.loader import render_to_string
from decimal import Decimal
from django.templatetags.static import static

import json
import requests #pokazuje blad ale dziala nie usuwac


def home(request):
    payment_status = request.GET.get('status')
    rental_id = request.GET.get('rental_id')

    if payment_status == 'success' and rental_id:
        # 1. Szukamy rezerwacji (uproszczony filtr)
        # Jeśli w modelu Rental masz user = ForeignKey(UserProfile), zostaw user__user
        rezerwacja = Rental.objects.filter(id=rental_id, user__user=request.user).first()

        if rezerwacja:
            # 2. Sprawdzamy czy rezerwacja ma status "Oczekująca" (ID=7)
            if rezerwacja.status.id == 7:
                # 3. Pobieramy status "Opłacona" (ID=6)
                status_oplacona = RentalStatus.objects.get(id=6)

                rezerwacja.status = status_oplacona
                rezerwacja.save()  # <--- TO ODPALI TRIGGER FAKTUR, KTÓRY DODASZ ZA CHWILĘ

                messages.success(request, "Dziękujemy! Płatność potwierdzona, faktura wygenerowana.")
                return redirect('home')
            else:
                messages.info(request, f"Ta rezerwacja ma już status: {rezerwacja.status.name}")
        else:
            messages.error(request, "Nie znaleziono Twojej rezerwacji.")

    # --- STANDARDOWA LOGIKA HOME ---
    cars = Car.objects.all()
    branches = Branch.objects.all()
    return render(request, 'home.html', {'cars': cars, 'cities': branches})



def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                return redirect('home')
            except IntegrityError as e:
                if 'check_wiek_18' in str(e):
                    form.add_error('birth_date', "Musisz mieć ukończone 18 lat, aby założyć konto.")
                else:
                    form.add_error(None, "Wystąpił błąd bazy danych. Spróbuj ponownie.")
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

            if form.is_valid():
                contact = form.save()
                # ZAKOMENTUJ TO:
                # try:
                #     send_mail(...)
                #     send_mail(...)
                #     messages.success(request, 'Wysłano!')
                # except Exception as e:
                #     pass

                # ZOSTAW TYLKO TO:
        messages.success(request, 'Zapisano wiadomość w bazie (test bez maila)!')
        return redirect('contact')


@login_required(login_url='login')
def rent_page(request):
    city = request.GET.get("city")
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort_by = request.GET.get('sort')

    today = date.today()
    cars = Car.objects.filter(is_available=True)

    profile = UserProfile.objects.filter(user=request.user).first()
    has_license = bool(profile and profile.license_number and profile.license_number.strip())#strip usuwa biale znaki

    if city and city != "":
        cars = cars.filter(current_branch__street__city__name__icontains=city)

    # Logika dostępności uwzględniająca 5-minutową blokadę "Oczekujących"
    if start_date and end_date:
        try:
            # Granica czasu dla rezerwacji tymczasowych (5 minut temu)
            expiration_time = timezone.now() - timedelta(minutes=5)

            # Pobieramy ID aut, które są zajęte:
            # 1. Mają status "Opłacona" lub "W trakcie" w tych datach
            # 2. Mają status "Oczekujący" i zostały stworzone mniej niż 5 minut temu
            occupied_cars_ids = Rental.objects.filter(
                Q(pickup_date__lte=end_date, return_date__gte=start_date) &#lte to <= less than or equal a gte to >= greater than or equal
                (
                    Q(status__name__in=["Opłacona", "W trakcie"]) |
                    (Q(status__name="Oczekująca") & Q(created_at__gte=expiration_time))
                )
            ).values_list('car_id', flat=True)

            cars = cars.exclude(id__in=occupied_cars_ids)
        except (ValueError, TypeError):
            pass

    # Sortowanie
    sort_dict = {
        'price_low': 'price_per_day',
        'price_high': '-price_per_day',
        'year_new': '-year',
        'mileage_low': 'mileage'
    }
    cars = cars.order_by(sort_dict.get(sort_by, 'id'))

    context = {
        "cars": cars,
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "today": str(today),
        "sort": sort_by,
        "has_license": has_license
    }
    return render(request, "rent.html", context)


@login_required(login_url='login')
def checkout_view(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)


    #sprawdz czy jest wprowadzony nr prawka
    if not profile.license_number or profile.license_number.strip() == "":
        messages.error(request, "Musisz uzupełnić numer prawa jazdy w swoim profilu, aby móc wypożyczyć auto!")
        return redirect('rent')

    addons_queryset = Addon.objects.all()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if not start_date_str or not end_date_str:
        return redirect('rent')

    # 1. Obliczanie bazowej liczby dni i ceny auta
    try:
        d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
        days = (d2 - d1).days
        if days <= 0: days = 1

        with connection.cursor() as cursor:
            cursor.execute("SELECT oblicz_cene_wypozyczenia(%s, %s, %s, %s)", [car.id, None, days, profile.id])
            base_total_price = round(cursor.fetchone()[0], 2)
    except Exception as e:
        messages.error(request, f"Błąd danych: {e}")
        return redirect('rent')

    # 2. REZERWACJA WSTĘPNA (Blokada 5 min)
    status_awaiting, _ = RentalStatus.objects.get_or_create(name="Oczekująca")

    rental, created = Rental.objects.get_or_create(
        user=profile,
        car=car,
        pickup_date=start_date_str,
        return_date=end_date_str,
        status=status_awaiting,
        defaults={'total_price': base_total_price}
    )

    # 3. OBSŁUGA PRZYCISKU "ZAPŁAĆ" (POST)
    if request.method == 'POST':
        try:
            with transaction.atomic():#atomic w skrocie oznacza wszystko albo nic jak powstanie gdzies blad nawet pod koniec to wszystko nie dziala z tego
                # Pobierz wybrane ID dodatków z formularza
                selected_addons_ids = request.POST.getlist('selected_addons')

                # Oblicz sumę cen wybranych dodatków
                addons_total_price = 0
                if selected_addons_ids:
                    selected_addons = Addon.objects.filter(id__in=selected_addons_ids)
                    for addon in selected_addons:
                        addons_total_price += float(addon.daily_price) * days

                # AKTUALIZACJA CENY KOŃCOWEJ (Auto + Dodatki)
                final_total = float(base_total_price) + float(addons_total_price)
                rental.total_price = round(final_total, 2)

                # Zapisujemy wybrane dodatki do sesji (skoro nie masz ManyToMany w Rental)
                request.session['temp_addons'] = selected_addons_ids

                rental.save()

                return redirect('tpay_json_process', rental_id=rental.id)
        except Exception as e:
            messages.error(request, f"Błąd finalizacji: {e}")
            return redirect('rent')

    return render(request, "checkout.html", {
        'car': car,
        'addons': addons_queryset,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_price': base_total_price,
        'rental': rental
    })
#FAQ
def faq(request):
    return render(request, "faq.html")

def cancel_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user__user=request.user)

    # Pobieramy lub tworzymy status "Anulowana"
    status_canceled, _ = RentalStatus.objects.get_or_create(name="Anulowana")

    rental.status = status_canceled
    rental.save()

    messages.info(request, "Rezerwacja została anulowana.")

    # Przekierowujemy z powrotem do wyszukiwarki, zachowując daty jeśli to możliwe
    return redirect('rent')


def tpay_json_redirect(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)

    # Dane do tpay
    client_id = "01KNZ2JFMG4P9F74T8JQ79NT32-01KNZ35MAX1H1EMBNQPCBFC1E9"
    secret = "ef85248e567cf5bdd39b916d00cf0d2d8b15e131d8343c64512fe472bdef3373"

    # 1. Pobieramy Token dostępu od Tpay
    auth_url = "https://openapi.sandbox.tpay.com/oauth/auth"
    auth_data = {
        "client_id": client_id,
        "client_secret": secret,
        "scope": "read write"
    }

    try:
        auth_response = requests.post(auth_url, data=auth_data)
        token = auth_response.json().get('access_token')

        # 2. Tworzymy transakcję przez API
        transaction_url = "https://openapi.sandbox.tpay.com/transactions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "amount": float(rental.total_price),
            "description": f"Wynajem auta #{rental.id}",
            "hiddenDescription": f"rental_{rental.id}",
            "payer": {
                "email": request.user.email,
                "name": request.user.get_full_name() or request.user.username
            },
            "callbacks": {
                "payerUrls": {
                    "success": request.build_absolute_uri(f'/?status=success&rental_id={rental.id}'),
                    "error": request.build_absolute_uri('/rent/?payment=failed')
                }
            }
        }

        transaction_response = requests.post(transaction_url, headers=headers, json=payload)
        res_data = transaction_response.json()

        # 3. Pobieramy link do płatności i przekierowujemy użytkownika
        payment_url = res_data.get('transactionPaymentUrl')

        if payment_url:
            return redirect(payment_url)
        else:
            messages.error(request, "Błąd Tpay: Nie udało się wygenerować linku.")
            return redirect('checkout', car_id=rental.car.id)

    except Exception as e:
        messages.error(request, f"Błąd komunikacji z Tpay: {e}")
        return redirect('checkout', car_id=rental.car.id)

#Podstrona Dane konta
@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Dane zostały zaktualizowane.")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, "profile.html", {
        "u_form": u_form,
        "p_form": p_form,
    })

#Podstrona Faktury
@login_required
def invoice_view(request):
    profile = request.user.profile

    invoices = Invoice.objects.filter(
        rental__user=profile
    ).select_related("rental").order_by("-issued_at")

    return render(request, "invoice.html", {
        "invoices": invoices
    })

#Podstrona Historia Wypożyczeń
@login_required
def rental_history_view(request):
    # Tu pobieramy tylko LISTĘ wszystkich wypożyczeń usera
    rentals = Rental.objects.filter(user__user=request.user).order_by('-pickup_date')
    return render(request, 'rental_history.html', {'rentals': rentals})


@login_required
def rental_detail_view(request, pk):
    # Pobieramy TĘ JEDNĄ konkretną rezerwację
    rental = get_object_or_404(Rental, pk=pk)

    # Pobieramy protokoły dla tej rezerwacji
    inspections = rental.inspections.all()
    today = timezone.now().date()

    # Logika przycisków
    can_create_pickup = (today == rental.pickup_date and
                         not inspections.filter(inspection_type='PICKUP').exists())

    can_create_return = (today == rental.return_date and
                         inspections.filter(inspection_type='PICKUP').exists() and
                         not inspections.filter(inspection_type='RETURN').exists())

    return render(request, 'rental_detail.html', {
        'rental': rental,
        'inspections': inspections,
        'can_create_pickup': can_create_pickup,
        'can_create_return': can_create_return,
    })
#Wyświetlenie faktury
@login_required
def invoice_detail_view(request, invoice_id):
    profile = request.user.profile

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "rental__car__model__brand",
            "rental__user",
        ),
        id=invoice_id,
        rental__user=profile
    )

    return render(request, "invoice_detail.html", {
        "invoice": invoice
    })

#Wyświetlenie zamówienia
@login_required
def rental_detail_view(request, rental_id):
    profile = request.user.profile

    rental = get_object_or_404(
        Rental.objects.select_related(
            "car__model__brand",
            "status",
            "user"
        ),
        id=rental_id,
        user=profile
    )

    return render(request, "rental_detail.html", {
        "rental": rental
    })


def invoice_pdf(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    rental = invoice.rental

    # Zamiast build_absolute_uri, szukamy pliku na dysku serwera:
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'MV-R.png')

    result = finders.find('images/MV-R.png')
    if result:
        logo_url = f"file://{result}"
    else:
        logo_url = f"file://{logo_path}"

    price_brutto = rental.total_price
    price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"))
    vat_amount = (price_brutto - price_netto).quantize(Decimal("0.01"))

    context = {
        "invoice": invoice,
        "price_brutto": price_brutto,
        "price_netto": price_netto,
        "vat_amount": vat_amount,
        "logo_url": logo_url,
    }

    html = render_to_string("invoice_pdf_template.html", context)


    pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=faktura_{invoice.invoice_number}.pdf"
    return response

