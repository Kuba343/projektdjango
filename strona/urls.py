from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .models import Car
from .views import calculator_view, mail_view

urlpatterns = [
    path('', views.home, name="home"),
    path('cars/', views.car_list, name='car_list'),
    path('rejestracja/',views.register,name='register'),
    path('login/', views.login, name='login'),
    path('kontakt/', views.contact_view, name='contact'),
    path('o-nas/', views.about_view, name='about'),
    path('mail/', mail_view, name='mail'),
    path('kalkulator/', calculator_view, name='calculator'),
    path('logout/', views.logout_view, name='logout'), # Tu używamy TWOJEJ funkcji wylogowania

    #Przekierowanie do szczegółów auta po kliknięciu kafelka
    path("cars/<int:car_id>/", views.car_detail, name="car_detail"),
]
#potrzebne do wstawianie zdjęc z bazy
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#to jest do tego aby po kliknieciu wyloguj dawalo nas na strone glowna
