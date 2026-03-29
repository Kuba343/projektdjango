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
    path('faq/', views.faq, name='faq'),
    path('checkout/<int:car_id>/', views.checkout_view, name='checkout'),
    path('payment-pending/<int:rental_id>/', views.payment_pending_view, name='payment_pending'),
    path('success/<int:rental_id>/', views.success_view, name='success'),
    path('cancel-rental/<int:rental_id>/', views.cancel_rental, name='cancel_rental'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



