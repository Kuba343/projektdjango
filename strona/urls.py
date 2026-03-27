from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .models import Car
from .views import calculator_view
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('wypozycz/', views.rent_page, name='rent'),
    path('rejestracja/',views.register,name='register'),
    path('login/', views.login, name='login'),
    path('kontakt/', views.contact_view, name='contact'),
    path('o-nas/', views.about_view, name='about'),
    path('kalkulator/', calculator_view, name='calculator'),
    path('logout/', views.logout_view, name='logout'),



    #urle do podstrony calculator
    path("search/", views.search_cars, name="search_cars"),
    path("calculate/<int:car_id>/", views.calculate_view, name="calculate"),
]
#potrzebne do wstawianie zdjęc z bazy
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#to jest do tego aby po kliknieciu wyloguj dawalo nas na strone glowna
