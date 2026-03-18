from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, validate_age


#formularz do rejestracji klienta
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Imię")
    last_name = forms.CharField(max_length=30, required=True, label="Nazwisko")
    email=forms.EmailField(required=True,label="Email")
    phone_number = forms.CharField(max_length=20,required=True,label="Numer telefonu")
    birth_date = forms.DateField(
        required=True,
        label="Data urodzenia",
        validators=[validate_age],
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ""
        self.fields['password1'].help_text = "Hasło musi mieć min. 8 znaków i nie może być zbyt proste."
        self.fields['password2'].help_text = ""

    password1 = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",  # Rząd 1 (na całą szerokość)
            "first_name", "last_name",  # Para 1 (Rząd 2)
            "email", "phone_number",  # Para 2 (Rząd 3)
            "password1", "password2",  # Para 3 (Rząd 4)
            "birth_date",  # Rząd 5 (na całą szerokość)
        )
        labels = {
            "username": "Nazwa użytkownika",
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        if UserProfile.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Użytkownik z tym numerem telefonu już istnieje.")

        # Zawsze musisz zwrócić wartość, jeśli jest poprawna!
        return phone_number

    def save(self, commit = True):
        user=super().save(commit=False)
        user.email=self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if user.last_login is None:
            user.last_login = timezone.now()

        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data["phone_number"],
                birth_date=self.cleaned_data["birth_date"],
                license_number=None
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