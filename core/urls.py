from django.urls import path
from . import api_views, views

urlpatterns = [
    # HTML pages
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/partial/', views.dashboard_partial, name='dashboard_partial'),
    path('movimentazioni/<int:pk>/', views.movimentazione_detail, name='movimentazione_detail'),
    path('tabelle/veicoli/', views.tabella_veicoli, name='tabella_veicoli'),
    path('tabelle/materiali/', views.tabella_materiali, name='tabella_materiali'),

    # API
    path('api/movimentazioni/', api_views.MovimentazioniListAPI.as_view()),
    path('api/movimentazioni/<int:pk>/', api_views.MovimentazioneDetailAPI.as_view()),
    path('api/giri/<int:pk>/', api_views.GiroDetailAPI.as_view()),
    path('api/veicoli/', api_views.VeicoliListAPI.as_view()),
    path('api/materiali/', api_views.MaterialiListAPI.as_view()),
    path('api/kpi/', api_views.KPIAPI.as_view()),
]
