# SolusLens

Dashboard Django per l'analisi delle movimentazioni rifiuti (Ecof Italia), con calcolo dell'impatto ecologico in **gha** (global hectares) e delle emissioni di trasporto in **kgCO₂**.

> **Documentazione tecnica approfondita:** vedi [`CLAUDE.md`](./CLAUDE.md) e [`DESIGN.md`](./DESIGN.md). Questo README serve solo a far partire l'ambiente.

---

## Stack

- **Backend:** Django 5 + Django REST Framework
- **Database:** SQLite (locale)
- **Frontend:** template Django + HTMX, Chart.js / Plotly
- **Static files:** WhiteNoise
- **Pipeline:** `pipeline/calc.py` (calcoli gha/CO₂) + `pipeline/geocoding.py` (Nominatim con cache JSON)
- **Python:** 3.12+ raccomandato (sviluppato su 3.14)

---

## Setup primo avvio

```bash
git clone git@github.com:Gastondefoix/soluslens.git
cd soluslens

python -m venv .venv
.venv\Scripts\activate           # PowerShell su Windows nativo
# source .venv/bin/activate      # Linux/macOS/WSL

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env             # imposta almeno SECRET_KEY (vedi sotto)

python manage.py migrate
python manage.py runserver
```

Per generare una `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Vai su [http://localhost:8000](http://localhost:8000) e loggati con:

| Utente | Password | Cosa vede |
|--------|----------|-----------|
| `pfizer` | `demo1234` | Dashboard Pfizer con dati marzo 2026 |
| `admin` | `demo1234` | Solo pannello `/admin/` |

Il database con i dati è già nel repo — non serve nessun passaggio aggiuntivo.

---

## Aggiungere nuovi dati

Metti i file aggiornati in `data/` e lancia:

```bash
python manage.py import_data
```

Il comando è idempotente. La prima esecuzione è lenta per il geocoding (Nominatim, 1.1 s/indirizzo) — dalla seconda tutto è in cache su `data/geocache.json`.

---

## Struttura del progetto

```
soluslens/
├── core/                      App Django principale
│   ├── models.py              6 tabelle (Azienda, UnitaLocale, Veicolo,
│   │                          Materiale, Giro, Movimentazione)
│   ├── views.py               Dashboard, partial HTMX, detail page
│   ├── api_views.py           Endpoint DRF (/api/...)
│   ├── admin.py               Admin Django
│   ├── templatetags/          Filtri custom (gha_fmt, co2_fmt, saldo_fmt)
│   └── management/commands/
│       └── import_data.py     Pipeline di ingestione
│
├── pipeline/                  Motore di calcolo (puro, niente Django views)
│   ├── calc.py                ⚠️ CUORE PRODOTTO — calcoli gha e CO₂
│   └── geocoding.py           Nominatim + cache
│
├── soluslens/                 Config Django (settings, urls, wsgi)
├── templates/                 HTML + partial HTMX
├── static/                    CSS / JS sorgenti
└── data/                      File dati (geocache in git, Excel/JSON raw no)
```

**Regola architetturale:** `core/` può importare da `pipeline/`, mai il contrario.

---

## API

Tutti gli endpoint richiedono autenticazione. JSON-only.

| Endpoint | Cosa |
|----------|------|
| `GET /api/movimentazioni/` | Lista movimentazioni |
| `GET /api/movimentazioni/<id>/` | Dettaglio movimentazione |
| `GET /api/giri/<id>/` | Dettaglio giro |
| `GET /api/veicoli/` | Lista veicoli |
| `GET /api/materiali/` | Lista materiali |
| `GET /api/kpi/` | KPI aggregati (gha + CO₂) |

---

## Comandi utili

```bash
python manage.py runserver
python manage.py import_data      # re-importa dati da data/
python manage.py shell
python manage.py test
python manage.py makemigrations && python manage.py migrate
python manage.py collectstatic    # solo pre-deploy
```

---

## Cose che fanno inciampare

- **`SECRET_KEY` non impostata** → `.env` non esiste. Copia `.env.example` e imposta la chiave.
- **Static files non si caricano** → assicurati di essere in `DEBUG=True` in locale.
- **Dashboard vuota per un nuovo utente** → deve essere collegato a un'`Azienda` dall'admin.
- **HTML/CSS non si caricano** → assicurati che `.env` abbia `DEBUG=True`. Se manca la riga, aggiungila.
