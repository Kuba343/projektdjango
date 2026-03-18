from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

#formularz do rejestracji klienta
class RegistrationForm(UserCreationForm):
    email=forms.EmailField(required=True,label="Email")
    phone_number = forms.CharField(max_length=20,required=True,label="Numer telefonu")
    birth_date=forms.DateField(required=True,label="Data urodzenia")

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
        fields=UserCreationForm.Meta.fields+("email","phone_number","birth_date")
        labels = {
            "username": "Nazwa użytkownika",
        }

    def save(self, commit = True):
        user=super().save(commit=False)
        user.email=self.cleaned_data["email"]
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                license_number=self.cleaned_data["license_number"],
                phone_number=self.cleaned_data["phone_number"],
                birth_date=self.cleaned_data["birth_date"]
            )
        return user
