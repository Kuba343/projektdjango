from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, validate_age, ContactMessage
from django.core.exceptions import ValidationError
from django.db import transaction


#formularz do rejestracji klienta
class RegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="Nazwa użytkownika",
        widget=forms.TextInput(attrs={'placeholder': 'Wpisz nazwę...'})
    )
    first_name = forms.CharField(max_length=30, required=True, label="Imię")
    last_name = forms.CharField(max_length=30, required=True, label="Nazwisko")
    email = forms.EmailField(required=True, label="Email")
    phone_number = forms.CharField(max_length=20, required=True, label="Numer telefonu")
    birth_date = forms.DateField(
        required=True,
        label="Data urodzenia",
        # validators=[validate_age], # Odkomentuj jeśli masz ten walidator
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    password1 = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Hasło musi mieć min. 8 znaków."
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    # --- WALIDACJA ---

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Użytkownik z tym adresem e-mail już istnieje.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if UserProfile.objects.filter(phone_number=phone).exists():
            raise ValidationError("Ten numer telefonu jest już przypisany do innego konta.")
        return phone

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Hasła nie są identyczne.")
        return p2

    # --- ZAPIS ---

    def save(self, commit=True):
        dane = self.cleaned_data

        # Używamy transaction.atomic, żeby mieć pewność, że jeśli profil padnie,
        # to użytkownik też nie zostanie stworzony (wszystko albo nic)
        with transaction.atomic():
            # 1. Tworzymy Usera
            user = User.objects.create_user(
                username=dane.get('username'),
                email=dane.get('email'),
                password=dane.get('password1'),
                first_name=dane.get('first_name'),
                last_name=dane.get('last_name')
            )

            # 2. Tworzymy powiązany UserProfile
            UserProfile.objects.create(
                user=user,
                phone_number=dane.get('phone_number'),
                birth_date=dane.get('birth_date')
            )

        return user

#formularz logowanie po emailu i hasle tylko
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Adres E-mail",
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.com', 'class': 'form-control'})
    )
    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={'placeholder': '********', 'class': 'form-control'})
    )

#formularz do wysylania maila
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'body']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Twoje imię i nazwisko', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Twój adres e-mail', 'class': 'form-control'}),
            'body': forms.Textarea(attrs={'placeholder': 'W czym możemy pomóc?', 'rows': 5, 'class': 'form-control'}),
        }