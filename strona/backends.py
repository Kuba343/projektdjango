from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned



#Pozwala użytkownikom logować się za pomocą adresu e-mail zamiast nazwy użytkownika.


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Szukamy użytkownika po polu email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            # Na wypadek, gdyby w bazie było dwóch takich samych (ale unikniemy tego dzięki unique=True)
            return User.objects.filter(email=username).first()

        # Sprawdzamy czy hasło pasuje
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None