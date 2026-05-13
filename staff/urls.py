from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('kelola-member/', views.kelola_member_view, name='kelola_member'),
    path('kelola-klaim/', views.kelola_klaim_view, name='kelola_klaim'),
    path('kelola-hadiah/', views.kelola_hadiah_view, name='kelola_hadiah'),
    path('kelola-mitra/', views.kelola_mitra_view, name='kelola_mitra'),
    path('laporan/', views.laporan_view, name='laporan'),
    path('dashboard/', views.dashboard, name='staff-dashboard'),
]