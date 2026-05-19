from django.contrib import admin
from .models import Azienda, UnitaLocale, Veicolo, Materiale, Giro, Movimentazione


@admin.register(Azienda)
class AziendaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'is_cliente_fisso', 'user']


@admin.register(UnitaLocale)
class UnitaLocaleAdmin(admin.ModelAdmin):
    list_display = ['azienda', 'indirizzo', 'citta', 'lat', 'lon']
    list_filter = ['azienda']


@admin.register(Veicolo)
class VeicoloAdmin(admin.ModelAdmin):
    list_display = ['targa', 'modello', 'tipo', 'fuel', 'euro_class', 'portata_kg']


@admin.register(Materiale)
class MaterialeAdmin(admin.ModelAdmin):
    list_display = ['cer', 'nome', 'tipo', 'pericoloso']
    list_filter = ['tipo', 'pericoloso']


@admin.register(Giro)
class GiroAdmin(admin.ModelAdmin):
    list_display = ['data', 'veicolo', 'n_clienti_totale', 'km_itinerario']
    list_filter = ['data', 'veicolo']


@admin.register(Movimentazione)
class MovimentazioneAdmin(admin.ModelAdmin):
    list_display = ['giro', 'unita_locale', 'materiale', 'quantita_kg', 'pericoloso', 'gha_netto', 'co2_trasporto']
    list_filter = ['pericoloso', 'materiale', 'giro__data']
    search_fields = ['n_formulario', 'unita_locale__azienda__nome']
