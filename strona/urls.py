from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .models import Car

urlpatterns = [
    path('', views.home, name="home"),
    path('cars/', views.car_list, name='car_list'),
    path('rejestracja/',views.register,name='rejestacja'),
    #Przekierowanie do szczegółów auta po kliknięciu kafelka
    path("cars/<int:car_id>/", views.car_detail, name="car_detail"),
]
#potrzebne do wstawianie zdjęc z bazy
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)