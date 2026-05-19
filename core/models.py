from django.db import models
from django.contrib.auth.models import User


class Azienda(models.Model):
    nome = models.CharField(max_length=255)
    is_cliente_fisso = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome


class UnitaLocale(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='unita_locali')
    indirizzo = models.CharField(max_length=255)
    citta = models.CharField(max_length=100)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.azienda.nome} — {self.indirizzo}"


class Veicolo(models.Model):
    targa = models.CharField(max_length=20, unique=True)
    modello = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    fuel = models.CharField(max_length=20)
    euro_class = models.CharField(max_length=20, null=True, blank=True)
    massa_vuoto_kg = models.FloatField()
    portata_kg = models.FloatField()
    co2_km_vuoto_kg = models.FloatField()
    co2_km_pieno_kg = models.FloatField()
    co2_min_kg = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.targa} — {self.modello}"


class Materiale(models.Model):
    cer = models.CharField(max_length=20, unique=True)
    descrizione = models.CharField(max_length=255)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20)       # 'biotico' / 'abiotico'
    origine = models.CharField(max_length=20, default='speciale')
    # 'urbano' or 'speciale'
    pericoloso = models.BooleanField(default=False)
    t_verg = models.FloatField(null=True, blank=True)
    t_smalt = models.FloatField()
    t_tratt = models.FloatField()
    t_ric = models.FloatField()
    resa = models.FloatField(null=True, blank=True)
    f_equiv = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.cer} — {self.nome}"


class Giro(models.Model):
    data = models.DateField()
    veicolo = models.ForeignKey(Veicolo, on_delete=models.PROTECT)
    n_clienti_totale = models.IntegerField()
    km_itinerario = models.FloatField()
    destinatario = models.CharField(max_length=255)
    indirizzo_impianto = models.CharField(max_length=255)
    op_min = models.FloatField(default=0)

    def __str__(self):
        return f"{self.data} — {self.veicolo.targa}"


class Movimentazione(models.Model):
    giro = models.ForeignKey(Giro, on_delete=models.CASCADE, related_name='movimentazioni')
    unita_locale = models.ForeignKey(UnitaLocale, on_delete=models.PROTECT)
    n_formulario = models.CharField(max_length=50)
    ora_ritiro = models.TimeField()
    quantita_kg = models.FloatField()
    materiale = models.ForeignKey(Materiale, on_delete=models.PROTECT)
    d_baricentro_km = models.FloatField()
    pericoloso = models.BooleanField()
    # Ecological footprint (gha) — null for pericolosi
    s1_gha = models.FloatField(null=True, blank=True)
    s2_gha = models.FloatField(null=True, blank=True)
    s_gha = models.FloatField(null=True, blank=True)
    s_gha_tipo = models.CharField(max_length=10, null=True, blank=True)
    gha_terreno = models.FloatField(null=True, blank=True)
    gha_netto = models.FloatField(null=True, blank=True)
    # Transport emissions (kgCO2) — always present
    t1_co2 = models.FloatField()
    t2_co2 = models.FloatField()
    co2_trasporto = models.FloatField()

    def __str__(self):
        return f"{self.giro.data} — {self.unita_locale} — {self.materiale.cer}"
