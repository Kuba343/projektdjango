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
from .models import Car, Addon, Branch, Rental, City, RentalStatus, PaymentMethod, UserProfile, RentalAddon
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as django_logout
from django.db.models import Q
from .models import Car, Addon
from django.shortcuts import render
from datetime import datetime, date
from django.db import transaction, InternalError, connection
from django.utils import timezone
from datetime import timedelta, date

def home(request):
    cars = Car.objects.all()[:6] # Pokazujemy np. tylko 6 aut na start
    cities = City.objects.all()
    return render(request, 'home.html', {'cars': cars, 'cities': cities})



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

    return render(request, 'contact.html', {'form': form, 'oddzialy': oddzialy})


@login_required(login_url='login')
def rent_page(request):
    # Pobieranie parametrów z GET
    city = request.GET.get("city")
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort_by = request.GET.get('sort')

    today = date.today()
    today_str = str(today)
    cars = Car.objects.all()

    # 1. Sprawdzenie prawa jazdy dla komunikatu (strażnik profilu)
    profile = UserProfile.objects.filter(user=request.user).first()
    has_license = bool(profile and profile.license_number and profile.license_number.strip())

    # 2. Filtrowanie
    if city and city != "":
        cars = cars.filter(current_branch__street__city__name__icontains=city)

    # 3. Logika dostępności (5 minut)
    if start_date and end_date:
        try:
            expiration_time = timezone.now() - timedelta(minutes=5)
            occupied_cars_ids = Rental.objects.filter(
                Q(pickup_date__lte=end_date, return_date__gte=start_date) &
                (Q(status__name="Opłacona") | Q(status__name="W trakcie", created_at__gte=expiration_time))
            ).values_list('car_id', flat=True)

            cars = cars.exclude(id__in=occupied_cars_ids)
        except (ValueError, TypeError):
            pass

    # 4. Sortowanie
    if sort_by == 'price_low':
        cars = cars.order_by('price_per_day')
    elif sort_by == 'price_high':
        cars = cars.order_by('-price_per_day')
    elif sort_by == 'year_new':
        cars = cars.order_by('-year')
    elif sort_by == 'mileage_low':
        cars = cars.order_by('mileage')
    else:
        cars = cars.order_by('id')

    context = {
        "cars": cars,
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "today": today_str,
        "sort": sort_by,
        "has_license": has_license
    }
    return render(request, "rent.html", context)


@login_required(login_url='login')
def checkout_view(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    profile = get_object_or_404(UserProfile, user=request.user)
    addons = Addon.objects.all()

    # Pobieramy daty z GET (z linku "Wypożycz teraz")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    # Strażnik dat
    if not start_date_str or not end_date_str:
        messages.warning(request, "Proszę najpierw wybrać daty wynajmu!")
        return redirect('rent')

    # --- OBLICZANIE CENY PRZEZ FUNKCJĘ SQL ---
    try:
        d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
        days = (d2 - d1).days
        if days <= 0: days = 1

        with connection.cursor() as cursor:
            # Wywołujemy funkcję SQL (f_id_addon ustawiamy na NULL/None na początku)
            cursor.execute(
                "SELECT oblicz_cene_wypozyczenia(%s, %s, %s, %s)",
                [car.id, None, days, profile.id]
            )
            total_price = round(cursor.fetchone()[0], 2)
    except Exception as e:
        messages.error(request, f"Błąd podczas obliczania ceny: {e}")
        return redirect('rent')

    # --- ZAPIS "W LOCIE" (GET) ---
    rental = None
    if request.method == 'GET':
        try:
            with transaction.atomic():
                status_pending, _ = RentalStatus.objects.get_or_create(name="W trakcie")

                # Tworzymy rezerwację (Trigger w Neonie sprawdzi tu prawo jazdy)
                rental = Rental.objects.create(
                    user=profile,
                    car=car,
                    pickup_date=start_date_str,
                    return_date=end_date_str,
                    status=status_pending,
                    total_price=total_price
                )
        except InternalError as e:
            # Obsługa błędu z triggera (np. brak prawa jazdy)
            messages.error(request, str(e).split('CONTEXT:')[0])
            return redirect('rent')

    # --- FINALIZACJA (POST) ---
    if request.method == 'POST':
        # Szukamy rezerwacji, która właśnie została stworzona
        rental = Rental.objects.filter(user=profile, car=car, status__name="W trakcie").last()

        if rental:
            try:
                with transaction.atomic():
                    # Zmiana statusu na opłaconą
                    status_paid, _ = RentalStatus.objects.get_or_create(name="Opłacona")
                    rental.status = status_paid

                    # Dodawanie wybranych dodatków i aktualizacja ceny końcowej
                    selected_addons = request.POST.getlist('selected_addons')
                    final_calculated_price = total_price  # Zaczynamy od bazowej

                    for addon_id in selected_addons:
                        addon_obj = Addon.objects.get(id=addon_id)
                        RentalAddon.objects.create(rental=rental, addon=addon_obj)

                        # Ponowne wywołanie funkcji SQL dla każdego dodatku, aby doliczyć go do ceny
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "SELECT oblicz_cene_wypozyczenia(%s, %s, %s, %s)",
                                [car.id, addon_id, days, profile.id]
                            )
                            # Twoja funkcja liczy auto+dodatek, więc doliczamy różnicę lub aktualizujemy
                            # Zakładając, że funkcja zwraca (auto + konkretny_dodatek) po rabatach:
                            final_calculated_price = cursor.fetchone()[0]

                    rental.total_price = final_calculated_price
                    rental.save()

                messages.success(request, "Płatność udana! Auto zostało zarezerwowane.")
                return redirect('my_rentals')
            except Exception as e:
                messages.error(request, f"Błąd podczas finalizacji: {e}")

    return render(request, "checkout.html", {
        'car': car,
        'addons': addons,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_price': total_price,  # Cena z funkcji SQL
        'rental': rental
    })
#FAQ
def faq(request):
    faq_wynajem = [
        ("Czy samochód może prowadzić inna osoba niż ta z umowy?",
         "Tak, ale tylko pod warunkiem, że dodatkowy kierowca zostanie dopisany do umowy przed rozpoczęciem wynajmu. "
         "Każda osoba musi okazać ważne prawo jazdy oraz dokument tożsamości. Dopisanie kierowcy wiąże się z opłatą "
         "20 zł za dzień. Niedozwolone jest przekazywanie pojazdu osobom nieuprawnionym, ponieważ w przypadku szkody "
         "ubezpieczenie może nie obowiązywać."),

        ("Czy mogę wynająć samochód bez kaucji?",
         "Tak, oferujemy opcję wynajmu bez kaucji, jednak wymaga to wykupienia rozszerzonego pakietu ubezpieczenia. "
         "Opcja ta jest dostępna dla większości klas pojazdów, z wyłączeniem aut premium i sportowych."),

        ("Czy mogę przedłużyć wynajem?",
         "Tak, przedłużenie wynajmu jest możliwe, o ile pojazd jest dostępny w danym terminie. Wystarczy skontaktować "
         "się z nami telefonicznie lub mailowo. Opłata za dodatkowe dni naliczana jest zgodnie z obowiązującym cennikiem."),

        ("Czy mogę odebrać auto w innym mieście?",
         "Tak, oferujemy usługę podstawienia pojazdu do dowolnego miasta w Polsce. Koszt zależy od odległości od "
         "najbliższego oddziału. Usługa musi zostać zgłoszona minimum 24 godziny wcześniej."),

        ("Czy mogę zwrócić auto poza godzinami pracy?",
         "Tak, w wielu lokalizacjach dostępne są specjalne skrytki lub parkingi umożliwiające zwrot pojazdu 24/7. "
         "W takim przypadku kluczyki należy pozostawić w dedykowanej skrzynce, a pojazd zaparkować w wyznaczonym miejscu."),

        ("Czy mogę wyjechać autem za granicę?",
         "Tak, ale wymaga to wcześniejszego zgłoszenia oraz dopłaty. Nie wszystkie kraje są objęte ubezpieczeniem, "
         "dlatego przed wyjazdem konieczne jest potwierdzenie dostępności tej opcji."),

        ("Czy mogę wynająć auto na miesiąc?",
         "Tak, oferujemy atrakcyjne pakiety wynajmu średnioterminowego i długoterminowego. Im dłuższy okres wynajmu, "
         "tym niższa cena za dobę. Pakiety obejmują serwis, ubezpieczenie i wsparcie techniczne."),

        ("Czy mogę zmienić termin rezerwacji?",
         "Tak, o ile pojazd jest dostępny w nowym terminie. Zmiana terminu może wiązać się z różnicą w cenie, jeśli "
         "nowy okres przypada na sezon wysokiego popytu."),

        ("Czy mogę wybrać konkretny model auta?",
         "Gwarantujemy klasę pojazdu, natomiast konkretny model zależy od dostępności w danym oddziale. Jeśli masz "
         "preferencje, postaramy się je uwzględnić."),

        ("Czy mogę wynająć auto bez limitu kilometrów?",
         "Tak, oferujemy pakiety bez limitu kilometrów, idealne na dłuższe podróże. Opcja ta jest dostępna dla większości "
         "klas pojazdów."),

        ("Czy mogę wynająć auto na firmę?",
         "Tak, wystawiamy faktury VAT oraz oferujemy specjalne warunki współpracy dla firm, w tym wynajem flotowy."),

        ("Czy mogę otrzymać auto z automatem?",
         "Tak, posiadamy dużą liczbę pojazdów z automatyczną skrzynią biegów. Warto zaznaczyć tę opcję podczas rezerwacji."),

        ("Czy mogę zwrócić auto w innym oddziale?",
         "Tak, możliwy jest zwrot w innej lokalizacji za dodatkową opłatą. Koszt zależy od odległości między oddziałami."),
    ]

    faq_platnosci = [
        ("Po jakim czasie odblokowywana jest kaucja?",
         "Kaucja jest zwalniana zazwyczaj w ciągu 24–72 godzin od zwrotu pojazdu. Czas ten zależy od banku, rodzaju "
         "karty oraz obciążenia systemów płatniczych. W przypadku kart kredytowych blokada znika szybciej, natomiast "
         "przy kartach debetowych proces może potrwać nieco dłużej. Jeśli kaucja nie wróci po 5 dniach roboczych, "
         "zalecamy kontakt z bankiem."),

        ("Jakie formy płatności akceptujecie?",
         "Akceptujemy płatności kartą debetową, kredytową, BLIK, szybkie przelewy oraz gotówkę w wybranych oddziałach. "
         "W przypadku wynajmu samochodów klasy premium wymagane jest posiadanie karty kredytowej. Wszystkie płatności "
         "są realizowane w bezpiecznym systemie płatniczym zgodnym z normami PCI DSS."),

        ("Czy mogę zapłacić gotówką?",
         "Tak, ale w przypadku płatności gotówką nadal wymagane jest zabezpieczenie kaucji kartą. Gotówka nie jest "
         "akceptowana przy wynajmie aut premium."),
    ]

    faq_uzytkowanie = [
        ("Czy samochód musi być zwrócony z pełnym bakiem?",
         "Tak, pojazd należy zwrócić z takim samym poziomem paliwa, z jakim został wydany. Jeśli auto zostanie zwrócone "
         "z mniejszą ilością paliwa, naliczona zostanie opłata za brakujące litry według aktualnego cennika oraz "
         "koszt obsługi. Można również wykupić opcję zwrotu bez tankowania."),

        ("Czy pobieracie opłatę za spóźnienie?",
         "Tak, w przypadku zwrotu pojazdu po czasie naliczana jest opłata za kolejną rozpoczętą godzinę lub dobę, "
         "w zależności od regulaminu. Jeśli przewidujesz opóźnienie, skontaktuj się z nami wcześniej."),

        ("Czy auta mają GPS?",
         "Większość pojazdów posiada wbudowaną nawigację lub obsługę Android Auto i Apple CarPlay. Jeśli potrzebujesz "
         "dedykowanego urządzenia GPS, poinformuj nas o tym podczas rezerwacji."),

        ("Czy auta mają klimatyzację?",
         "Tak, wszystkie nasze pojazdy są wyposażone w klimatyzację. W autach wyższej klasy dostępna jest również "
         "klimatyzacja dwustrefowa lub trzystrefowa."),
    ]

    faq_ubezpieczenia = [
        ("Czy samochód jest ubezpieczony?",
         "Tak, wszystkie nasze pojazdy posiadają pełne ubezpieczenie OC, AC oraz Assistance. W zależności od wybranego "
         "pakietu może obowiązywać udział własny w szkodzie. Istnieje możliwość wykupienia pakietu redukującego udział "
         "własny do zera, co zapewnia pełen komfort podczas podróży."),

        ("Czy auta mają pełne ubezpieczenie?",
         "Tak, ale udział własny w szkodzie zależy od wybranego pakietu. Można wykupić pakiet redukujący udział własny "
         "do zera, co zapewnia pełną ochronę."),

        ("Czy samochody są regularnie serwisowane?",
         "Tak, każdy pojazd przechodzi regularne przeglądy techniczne oraz kontrole bezpieczeństwa. Dbamy o to, aby "
         "nasza flota była w idealnym stanie technicznym i wizualnym."),

        ("Czy auta są dezynfekowane?",
         "Tak, każdy pojazd jest dokładnie czyszczony i dezynfekowany przed wydaniem. Dbamy o najwyższe standardy "
         "higieny i bezpieczeństwa."),
    ]

    faq_wyposazenie = [
        ("Czy samochody są wyposażone w zimowe opony?",
         "Tak, w sezonie zimowym wszystkie pojazdy są wyposażone w opony zimowe zgodnie z obowiązującymi przepisami. "
         "W niektórych regionach dostępne są również łańcuchy śniegowe na życzenie."),

        ("Czy mogę zamówić fotelik dziecięcy?",
         "Tak, oferujemy foteliki dla dzieci w różnych kategoriach wagowych. Fotelik należy zarezerwować wcześniej, "
         "aby zagwarantować jego dostępność. Montaż fotelika leży po stronie klienta."),

        ("Czy mogę dodać drugiego kierowcę?",
         "Tak, koszt dopisania dodatkowego kierowcy wynosi 20 zł za dzień. Każdy kierowca musi spełniać wymagania "
         "dotyczące wieku i stażu jazdy."),
    ]

    return render(request, "faq.html", {
        "faq_wynajem": faq_wynajem,
        "faq_platnosci": faq_platnosci,
        "faq_uzytkowanie": faq_uzytkowanie,
        "faq_ubezpieczenia": faq_ubezpieczenia,
        "faq_wyposazenie": faq_wyposazenie,
    })


def payment_pending_view(request):
    return render(request, "payment_pending.html")

def success_view(request):
    return render(request, "success.html")


def cancel_rental(request, rental_id):
    # 1. Znajdź rezerwację w bazie (get_object_or_404 to zabezpieczenie)
    from django.shortcuts import get_object_or_404
    rental = get_object_or_404(Rental, id=rental_id)

    # 2. Skasuj ją (to zwalnia auto w Twoim filtrze rent_page)
    rental.delete()

    # 3. Dodaj komunikat (opcjonalnie)
    from django.contrib import messages
    messages.info(request, "Anulowano rezerwację. Auto jest już dostępne dla innych.")

    # 4. Wrzuć użytkownika na stronę z autami
    return redirect('rent') # 'rent' to nazwa Twojego URL-a od listy aut