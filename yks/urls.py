from django.urls import path
from . import views

app_name = 'yks'

urlpatterns = [
    path('', views.index, name='index'),
    # Daha sonra eklenecek diğer URL'ler
] 