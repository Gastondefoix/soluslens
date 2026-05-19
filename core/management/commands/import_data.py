"""
Usage: python manage.py import_data

Reads:
  data/prova3.xlsx
  data/dataset_automezzi.json
  data/materiali.json

Populates all models. Idempotent (safe to run multiple times).
"""

import json
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand

from core.models import (
    Azienda, UnitaLocale, Veicolo, Materiale, Giro, Movimentazione
)
from pipeline.calc import (
    calc_movimentazione, calc_d_baricentro, haversine_km,
    ECOF_LAT, ECOF_LON
)
from pipeline.geocoding import geocode, load_cache, save_cache

DATA_DIR = Path("data")

# CER codes considered pericolosi (EU list 2000/532/CE — asterisk codes)
CER_PERICOLOSI = {
    "160505", "170603", "180103",
    "150110", "150111", "160107", "160209", "160211",
    "160213", "200121", "200123", "200135",
}

# Fixed clients — partial name match (case-insensitive)
CLIENTI_FISSI = [
    "ENEL ITALIA", "LUISS", "COMPASS GROUP", "PFIZER", "PHYGISPACE",
    "TELECOM ITALIA", "LINK CAMPUS", "BANCA NAZIONALE DEL LAVORO",
    "CONFEDERAZIONE COOPERATIVE", "VERISURE", "OPEN FIBER", "ALMAVIVA",
    "INARCASSA", "TELESPAZIO", "MAX-PLANCK", "INVESTIRE SGR", "PEDEVILLA",
    "ISMEA", "WARNER BROS", "HUAWEI", "CONFCOOPER",
    "CASSA NAZIONALE", "SIRTI", "BONELLI EREDE", "SABA ITALIA",
    "BRUNO FARMACEUTICI", "DLA PIPER", "CAT BALOU", "ANIA",
    "CASSA ITALIANA", "CASSA DEI GEOMETRI", "ROME CITY INSTITUTE",
    "WWF", "GRUPPO BUFFETTI", "AGECONTROL", "FONDAZIONE ENASARCO",
    "I.CON REAL ESTATE", "CASAGIT", "NOVOMATIC", "LUISS BUSINESS",
    "TELEPASS", "EXPEDIA", "HONDA MOTOR", "RADIO DIMENSIONE SUONO",
    "ENGIE", "FULL SERVICES", "GIANNI & ORIGONI", "UNICEF",
    "ZTE ITALIA", "SACE", "AMBASCIATA", "TINEXTA", "AGEA",
    "NOTARTEL", "RAIT", "GROUPAMA", "ADMIRAL", "FRATELLI D'AMICO",
    "ROHDE", "SKY ITALIA", "D'AMICO SOCIETA", "E-GEOS", "SACE BT",
    "CENTRALE DEL LATTE", "TRAVELPORT",
]


def is_cliente_fisso(nome: str) -> bool:
    nome_up = nome.upper()
    return any(k.upper() in nome_up for k in CLIENTI_FISSI)


class Command(BaseCommand):
    help = "Import data from Excel + JSON into SolusLens database"

    def handle(self, *args, **options):
        self.stdout.write("=== SolusLens Import ===\n")

        # --- 1. Load source files ---
        self.stdout.write("Loading source files...")
        df = pd.read_excel(DATA_DIR / "prova3.xlsx")
        df.columns = [c.strip() for c in df.columns]
        df = df.dropna(subset=["Produttore", "TargaAutomezzo"])
        df["cer_str"] = df["C.E.R."].apply(
            lambda x: str(int(x)).zfill(6) if pd.notna(x) else None
        )
        df["data_str"] = pd.to_datetime(df["Data Ricezione"]).dt.strftime("%Y-%m-%d")

        with open(DATA_DIR / "dataset_automezzi.json") as f:
            veicoli_json = json.load(f)

        with open(DATA_DIR / "materiali.json") as f:
            materiali_json = json.load(f)

        # --- 2. Upsert Veicoli ---
        self.stdout.write("Importing veicoli...")
        veicoli_map = {}  # targa → Veicolo instance
        for v in veicoli_json:
            obj, created = Veicolo.objects.update_or_create(
                targa=v["targa"],
                defaults={
                    "modello": v["modello"],
                    "tipo": v["tipo"],
                    "fuel": v["fuel"],
                    "euro_class": v.get("euro_class"),
                    "massa_vuoto_kg": v["massa_vuoto_kg"],
                    "portata_kg": v["portata_kg"],
                    "co2_km_vuoto_kg": v["co2_km_vuoto_kg"],
                    "co2_km_pieno_kg": v["co2_km_pieno_kg"],
                    "co2_min_kg": v.get("co2_min_kg"),
                },
            )
            veicoli_map[v["targa"]] = obj
            self.stdout.write(f"  {'[NEW]' if created else '[UPD]'} {v['targa']} {v['modello']}")

        # --- 3. Upsert Materiali ---
        self.stdout.write("Importing materiali...")
        materiali_map = {}  # cer → Materiale instance
        for cer, m in materiali_json.items():
            pericoloso = cer in CER_PERICOLOSI
            obj, created = Materiale.objects.update_or_create(
                cer=cer,
                defaults={
                    "nome": m["nome"],
                    "descrizione": m.get("descrizione", m["nome"]),
                    "tipo": m["tipo"],
                    "origine": m.get("origine", "speciale"),
                    "pericoloso": pericoloso,
                    "t_verg": m.get("t_verg"),
                    "t_smalt": m["t_smalt"],
                    "t_tratt": m["t_tratt"],
                    "t_ric": m["t_ric"],
                    "resa": m.get("resa"),
                    "f_equiv": m.get("f_equiv"),
                },
            )
            materiali_map[cer] = obj
            self.stdout.write(f"  {'[NEW]' if created else '[UPD]'} {cer} {m['nome']}")

        # --- 4. Geocode addresses ---
        self.stdout.write("Geocoding addresses...")
        cache = load_cache()

        addr_set = set()
        for _, row in df.iterrows():
            addr = str(row.get("Indirizzo UL", "")).strip()
            city = str(row.get("Città UL", "Roma")).strip()
            if addr:
                addr_set.add((addr, city))

        coords_map = {}  # (addr, city) → (lat, lon)
        for addr, city in sorted(addr_set):
            coords = geocode(addr, city, cache)
            coords_map[(addr, city)] = coords
            self.stdout.write(f"  {addr[:50]:<50} → {coords[0]:.4f},{coords[1]:.4f}")

        save_cache(cache)
        self.stdout.write(f"  Geocache saved ({len(cache)} entries)")

        # --- 5. Upsert Aziende + UnitaLocali ---
        self.stdout.write("Importing aziende e unità locali...")
        ul_map = {}  # (produttore, indirizzo) → UnitaLocale instance

        aziende_seen = {}
        for _, row in df.iterrows():
            nome = str(row["Produttore"]).strip()
            indirizzo = str(row.get("Indirizzo UL", "")).strip()
            city = str(row.get("Città UL", "Roma")).strip()

            if nome not in aziende_seen:
                az, _ = Azienda.objects.get_or_create(
                    nome=nome,
                    defaults={"is_cliente_fisso": is_cliente_fisso(nome)},
                )
                aziende_seen[nome] = az
            az = aziende_seen[nome]

            key = (nome, indirizzo)
            if key not in ul_map:
                coords = coords_map.get((indirizzo, city), (41.9028, 12.4964))
                ul, _ = UnitaLocale.objects.get_or_create(
                    azienda=az,
                    indirizzo=indirizzo,
                    defaults={
                        "citta": city,
                        "lat": coords[0],
                        "lon": coords[1],
                    },
                )
                ul_map[key] = ul

        self.stdout.write(f"  {len(aziende_seen)} aziende, {len(ul_map)} unità locali")

        # --- 6. Process giri and movimentazioni ---
        self.stdout.write("Processing giri e movimentazioni...")
        n_giri = 0
        n_mov = 0

        giro_keys = df[["data_str", "TargaAutomezzo"]].drop_duplicates()

        for _, gk in giro_keys.iterrows():
            data_s = gk["data_str"]
            targa = gk["TargaAutomezzo"]

            veicolo_obj = veicoli_map.get(targa)
            if not veicolo_obj:
                self.stdout.write(f"  [SKIP] No vehicle for {targa}")
                continue

            giro_df = df[
                (df["data_str"] == data_s) & (df["TargaAutomezzo"] == targa)
            ].copy().sort_values("Ora In.Trasp.")

            # Build veicolo dict for calc functions
            veicolo_dict = {
                "co2_km_vuoto_kg": veicolo_obj.co2_km_vuoto_kg,
                "co2_km_pieno_kg": veicolo_obj.co2_km_pieno_kg,
                "portata_kg": veicolo_obj.portata_kg,
                "co2_min_kg": veicolo_obj.co2_min_kg,
            }

            # Total load and client count for entire giro (fixed + spot)
            C_total = float(giro_df["Q.tà a Destino"].sum())
            n_clienti = len(giro_df)

            # op_min for compattatori/costipatori
            op_min = 0.0
            if veicolo_obj.co2_min_kg:
                ora_col = giro_df["Ora In.Trasp."].dropna().tolist()
                if len(ora_col) >= 2:
                    from datetime import datetime
                    def parse_time(t):
                        return datetime.strptime(str(t)[:5], "%H:%M")
                    t_min = parse_time(min(ora_col))
                    t_max = parse_time(max(ora_col))
                    op_min = (t_max - t_min).seconds / 60.0

            # Impianto destinatario
            dest_col = giro_df["Destinatario"].dropna()
            dest_addr_col = giro_df["Destinatario: Indirizzo"].dropna()
            destinatario = str(dest_col.iloc[0]).strip() if not dest_col.empty else ""
            indirizzo_impianto = str(dest_addr_col.iloc[0]).strip() if not dest_addr_col.empty else ""

            # Ordered stop coords for all stops in giro
            stop_coords = []
            stop_qtys = []
            for _, row in giro_df.iterrows():
                addr = str(row.get("Indirizzo UL", "")).strip()
                city = str(row.get("Città UL", "Roma")).strip()
                coords = coords_map.get((addr, city))
                if coords:
                    stop_coords.append(coords)
                    stop_qtys.append(float(row["Q.tà a Destino"]))

            # Total itinerario km via Haversine circuit:
            # Ecof → stop1 → stop2 → ... → impianto → Ecof
            impianto_coords = (41.9028, 12.4964)  # fallback
            imp_addr = indirizzo_impianto
            if imp_addr:
                impianto_coords = coords_map.get((imp_addr, "Roma"), impianto_coords)

            circuit = [(ECOF_LAT, ECOF_LON)] + stop_coords + [impianto_coords, (ECOF_LAT, ECOF_LON)]
            km_itinerario = sum(
                haversine_km(circuit[i][0], circuit[i][1], circuit[i+1][0], circuit[i+1][1])
                for i in range(len(circuit) - 1)
            )

            # d_baricentro for entire giro
            d_baricentro = calc_d_baricentro(stop_coords, stop_qtys)

            # Upsert Giro
            giro_obj, created = Giro.objects.update_or_create(
                data=data_s,
                veicolo=veicolo_obj,
                defaults={
                    "n_clienti_totale": n_clienti,
                    "km_itinerario": round(km_itinerario, 2),
                    "destinatario": destinatario,
                    "indirizzo_impianto": indirizzo_impianto,
                    "op_min": round(op_min, 1),
                },
            )
            if created:
                n_giri += 1

            # Process each row → Movimentazione
            for _, row in giro_df.iterrows():
                cer = row.get("cer_str")
                if not cer:
                    continue

                mat_obj = materiali_map.get(cer)
                if not mat_obj:
                    self.stdout.write(f"  [SKIP MOV] Unknown CER {cer}")
                    continue

                produttore = str(row["Produttore"]).strip()
                indirizzo = str(row.get("Indirizzo UL", "")).strip()
                ul_obj = ul_map.get((produttore, indirizzo))
                if not ul_obj:
                    continue

                Q_kg = float(row["Q.tà a Destino"])
                pericoloso = cer in CER_PERICOLOSI

                mat_dict = {
                    "tipo": mat_obj.tipo,
                    "pericoloso": mat_obj.pericoloso,
                    "t_verg": mat_obj.t_verg,
                    "t_smalt": mat_obj.t_smalt,
                    "t_tratt": mat_obj.t_tratt,
                    "t_ric": mat_obj.t_ric,
                    "resa": mat_obj.resa,
                    "f_equiv": mat_obj.f_equiv,
                }

                calc = calc_movimentazione(
                    mat=mat_dict,
                    veicolo=veicolo_dict,
                    Q_kg=Q_kg,
                    km_itinerario=km_itinerario,
                    n_clienti=n_clienti,
                    d_baricentro_km=d_baricentro,
                    C_total=C_total,
                    pericoloso=pericoloso,
                )

                ora_str = str(row.get("Ora In.Trasp.", "00:00"))[:5]

                Movimentazione.objects.update_or_create(
                    n_formulario=str(row["N. Formulario"]).strip(),
                    defaults={
                        "giro": giro_obj,
                        "unita_locale": ul_obj,
                        "ora_ritiro": ora_str,
                        "quantita_kg": Q_kg,
                        "materiale": mat_obj,
                        "d_baricentro_km": round(d_baricentro, 2),
                        "pericoloso": pericoloso,
                        "s1_gha": calc["s1_gha"],
                        "s2_gha": calc["s2_gha"],
                        "s_gha": calc["s_gha"],
                        "s_gha_tipo": calc.get("s_gha_tipo"),
                        "gha_terreno": calc["gha_terreno"],
                        "gha_netto": calc["gha_netto"],
                        "t1_co2": calc["t1_co2"],
                        "t2_co2": calc["t2_co2"],
                        "co2_trasporto": calc["co2_trasporto"],
                    },
                )
                n_mov += 1

        self.stdout.write(f"\n✓ Import complete: {n_giri} giri, {n_mov} movimentazioni")

        # --- 7. Summary ---
        self.stdout.write(f"\n  Aziende totali:        {Azienda.objects.count()}")
        self.stdout.write(f"  Clienti fissi:         {Azienda.objects.filter(is_cliente_fisso=True).count()}")
        self.stdout.write(f"  Unità locali:          {UnitaLocale.objects.count()}")
        self.stdout.write(f"  Veicoli:               {Veicolo.objects.count()}")
        self.stdout.write(f"  Materiali:             {Materiale.objects.count()}")
        self.stdout.write(f"  Giri:                  {Giro.objects.count()}")
        self.stdout.write(f"  Movimentazioni totali: {Movimentazione.objects.count()}")
