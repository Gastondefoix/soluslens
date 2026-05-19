from rest_framework import serializers
from .models import Azienda, UnitaLocale, Veicolo, Materiale, Giro, Movimentazione


class UnitaLocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitaLocale
        fields = ['id', 'indirizzo', 'citta', 'lat', 'lon']


class VeicoloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veicolo
        fields = [
            'id', 'targa', 'modello', 'tipo', 'fuel', 'euro_class',
            'massa_vuoto_kg', 'portata_kg',
            'co2_km_vuoto_kg', 'co2_km_pieno_kg', 'co2_min_kg',
        ]


class MaterialeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materiale
        fields = [
            'id', 'cer', 'nome', 'descrizione', 'tipo', 'origine', 'pericoloso',
            't_verg', 't_smalt', 't_tratt', 't_ric', 'resa', 'f_equiv',
        ]


class GiroSerializer(serializers.ModelSerializer):
    veicolo = VeicoloSerializer(read_only=True)

    class Meta:
        model = Giro
        fields = [
            'id', 'data', 'veicolo', 'n_clienti_totale',
            'km_itinerario', 'destinatario', 'indirizzo_impianto', 'op_min',
        ]


class MovimentazioneListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    ul_indirizzo = serializers.CharField(source='unita_locale.indirizzo')
    ul_citta = serializers.CharField(source='unita_locale.citta')
    materiale_nome = serializers.CharField(source='materiale.nome')
    materiale_cer = serializers.CharField(source='materiale.cer')
    materiale_pericoloso = serializers.BooleanField(source='materiale.pericoloso')
    data = serializers.DateField(source='giro.data')
    targa = serializers.CharField(source='giro.veicolo.targa')
    modello_veicolo = serializers.CharField(source='giro.veicolo.modello')

    class Meta:
        model = Movimentazione
        fields = [
            'id', 'data', 'ul_indirizzo', 'ul_citta',
            'materiale_cer', 'materiale_nome', 'materiale_pericoloso',
            'n_formulario', 'ora_ritiro', 'quantita_kg',
            'targa', 'modello_veicolo',
            'pericoloso',
            's1_gha', 's2_gha', 's_gha',
            'gha_terreno', 'gha_netto',
            't1_co2', 't2_co2', 'co2_trasporto',
        ]


class MovimentazioneDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view — includes giro and curve data."""
    unita_locale = UnitaLocaleSerializer(read_only=True)
    materiale = MaterialeSerializer(read_only=True)
    giro = GiroSerializer(read_only=True)
    # Logarithmic curve points for Chart.js
    curva_logaritmica = serializers.SerializerMethodField()

    class Meta:
        model = Movimentazione
        fields = [
            'id', 'giro', 'unita_locale', 'materiale',
            'n_formulario', 'ora_ritiro', 'quantita_kg',
            'd_baricentro_km', 'pericoloso',
            's1_gha', 's2_gha', 's_gha',
            'gha_terreno', 'gha_netto',
            't1_co2', 't2_co2', 'co2_trasporto',
            'curva_logaritmica',
        ]

    def get_curva_logaritmica(self, obj):
        from pipeline.calc import logarithmic_curve_points, co2_per_km
        from django.db.models import Sum
        veicolo = obj.giro.veicolo
        veicolo_dict = {
            'co2_km_vuoto_kg': veicolo.co2_km_vuoto_kg,
            'co2_km_pieno_kg': veicolo.co2_km_pieno_kg,
            'portata_kg': veicolo.portata_kg,
        }
        points = logarithmic_curve_points(veicolo_dict, n_points=100)
        carico_giro_kg = obj.giro.movimentazioni.aggregate(
            total=Sum('quantita_kg')
        )['total'] or 0.0
        return {
            'points': points,
            'carico_giro_kg': round(carico_giro_kg, 1),
            'co2_at_load': round(co2_per_km(veicolo_dict, carico_giro_kg), 5),
            'co2_vuoto': veicolo.co2_km_vuoto_kg,
            'co2_pieno': veicolo.co2_km_pieno_kg,
            'portata_kg': veicolo.portata_kg,
        }
