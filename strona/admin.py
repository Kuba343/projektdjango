from django.contrib import admin
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db import InternalError, transaction
from django.contrib import messages
from django import forms
from .models import *

# Rejestracja słowników
admin.site.register([
    Brand, CarCategory, FuelType, RentalStatus,
    PaymentMethod, City, Role, InspectionItem, AddonType
])

# Rejestracja ważnych tabel


#prosty formularz do wpisania procentu zeby podniesc cene aut
class PriceChangeForm(forms.Form):
    procent = forms.DecimalField(label="O ile procent zmienić cenę?", max_digits=5, decimal_places=2)

#formularz zeby admin wybral dostepny typ serwisu z bazy
class ServiceSelectionForm(forms.Form):
    serwis = forms.ModelChoiceField(
        queryset=InspectionItem.objects.all(),
        label="Wybierz typ serwisu",
        empty_label="-- Wybierz z listy --"
    )

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('model', 'price_per_day', 'is_available')
    list_filter = ('is_available',)
    actions = ['uruchom_serwis_masowy', 'zmien_cene_procentowo']

    def save_model(self, request, obj, form, change):
        try:
            # Używamy transaction.atomic, aby błąd triggera nie "zepsuł"
            # całego połączenia z bazą danych
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except InternalError as e:
            # Tutaj przechwytujemy Twój komunikat "Nie można cofnąć przebiegu!!!!!"
            # Wyciągamy samą treść błędu bez zbędnych technicznych dopisków
            error_message = str(e).split('\n')[0]

            # Dodajemy ładny komunikat, który pojawi się nad formularzem
            self.message_user(request, f"Błąd zapisu: {error_message}", messages.ERROR)

            # Zwracamy None, aby Django nie próbowało robić nic więcej
            return None

    def response_change(self, request, obj):
        # Jeśli wystąpił błąd w save_model (np. nasz InternalError),
        # musimy powstrzymać Django przed przekierowaniem na listę aut
        if "_continue" not in request.POST and messages.get_messages(request):
            # Zostajemy na tej samej stronie edycji
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)



    def zmien_cene_procentowo(self, request, queryset):
        form = None
        if 'apply' in request.POST:
            form = PriceChangeForm(request.POST)
            if form.is_valid():
                procent = form.cleaned_data['procent']
                branch_id = queryset.first().current_branch.id
                with connection.cursor() as cursor:
                    cursor.execute("CALL pr_zmien_ceny_w_oddziale(%s,%s)", [branch_id, procent])
                self.message_user(request, f"Zmieniono ceny o {procent}% w oddziale {branch_id}")
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = PriceChangeForm()
        return render(request, 'admin/price_change_form.html', {
            'items': queryset,
            'form': form,
            'title': 'Podaj wartość procentową'
        })

    zmien_cene_procentowo.short_description = "Zmień ceny (podaj własny %%)"

    def uruchom_serwis_masowy(self, request, queryset):
        form = None
        if 'apply' in request.POST:
            form = ServiceSelectionForm(request.POST)
            if form.is_valid():
                item_id = form.cleaned_data['serwis'].id
                branch_id = queryset.first().current_branch.id
                with connection.cursor() as cursor:
                    cursor.execute("CALL pr_serwis_aut(%s,%s)", [branch_id, item_id])
                self.message_user(request, f" Dodano serwis '{form.cleaned_data['serwis']}' dla oddziału.")
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = ServiceSelectionForm()
        return render(request, 'admin/service_selection_form.html', {
            'items': queryset,
            'form': form,
            'title': 'Wybierz rodzaj serwisu dla floty'
        })
    uruchom_serwis_masowy.short_description = " Masowy serwis (wybierz typ)"

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'pickup_date', 'return_date', 'status')
    list_filter = ('status',)

    actions = ['wymus_czyszczenie_oczekujacych']

    def wymus_czyszczenie_oczekujacych(self, request, queryset):
        with connection.cursor() as cursor:
            cursor.execute("CALL zwolnij_dlugo_oczekujace_rezerwacje()")

        self.message_user(request, "PROCEDURA SQL: Usunięto blokady aut które były zbyt długo oczekujące")

    wymus_czyszczenie_oczekujacych.short_description = "Zwolnij blokady 5-minutowe (PROCEDURA)"


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
