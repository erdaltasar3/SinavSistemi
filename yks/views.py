from django.shortcuts import render
from .models import YKSOturum

def index(request):
    """YKS anasayfası"""
    # Sadece durumu "Bekliyor" olan oturumları getir
    oturumlar = YKSOturum.objects.filter(durum=YKSOturum.DURUM_BEKLIYOR).order_by('sinav_tarihi')
    
    context = {
        'oturumlar': oturumlar,
    }
    return render(request, 'yks/index.html', context)
