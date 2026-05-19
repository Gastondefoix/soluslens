# SolusLens

Dashboard Django per l'analisi delle movimentazioni rifiuti (Ecof Italia), con calcolo dell'impatto ecologico in **gha** (global hectares) e delle emissioni di trasporto in **kgCO₂**. I dati grezzi arrivano da PrometeoRifiuti via export Excel; il pipeline li ingerisce, geocodifica gli indirizzi clienti, calcola gli indicatori e li espone in una dashboard con KPI, grafici e tabelle.

> **Documentazione tecnica approfondita:** vedi [`CLAUDE.md`](./CLAUDE.md) e [`DESIGN.md`](./DESIGN.md). Questo README serve solo a far partire l'ambiente.

---

## Stack

- **Backend:** Django 5 + Django REST Framework
- **Database:** SQLite (locale, mai in produzione condivisa)
- **Frontend:** template Django + HTMX per i partial, Chart.js / Plotly per i grafici
- **Static files:** WhiteNoise
- **Pipeline:** `pipeline/calc.py` (calcoli gha/CO₂) + `pipeline/geocoding.py` (Nominatim con rate limit 1.1 s e cache JSON)
- **Python:** 3.12+ raccomandato (sviluppato su 3.14)

---

## Setup primo avvio

### 1. Clona il repo

```bash
git clone git@github.com:Gastondefoix/soluslens.git
cd soluslens
```

### 2. Crea il virtualenv e installa le dipendenze

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS/WSL
# .venv\Scripts\activate           # PowerShell su Windows nativo

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

```bash
cp .env.example .env
```

Apri `.env` e imposta almeno `SECRET_KEY`. Per generare una chiave Django valida:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`DEBUG=True` va bene per sviluppo locale. `ALLOWED_HOSTS=localhost,127.0.0.1` è già il default.

### 4. Applica le migrazioni e crea un superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Avvia il server

```bash
python manage.py runserver
```

Vai su [http://localhost:8000/admin/](http://localhost:8000/admin/) e fai login con il superuser. Vedrai i modelli vuoti.

A questo punto l'applicazione **gira**, ma la dashboard è vuota perché non ci sono dati. Vedi sezione successiva.

---

## Dati: dove stanno e come averli

I file dati **non sono in git**, per scelta — `data/`, `db.sqlite3` e tutti i `.env` sono nel `.gitignore`. Le motivazioni:

- Contengono indirizzi reali e dati di clienti (Pfizer e altri).
- Il codice ha la sua history versionata; i dati hanno il loro ciclo di vita separato.
- Le credenziali e i dump si scambiano fuori-git (1Password / Bitwarden / canale cifrato), non sul repo.

### Cosa ti serve per popolare la dashboard

Tre file dentro `data/` (chiedili a Giacomo):

| File | Contenuto | Sorgente |
|---|---|---|
| `data/prova3.xlsx` | Export movimentazioni rifiuti | PrometeoRifiuti |
| `data/dataset_automezzi.json` | Parco veicoli con fattori CO₂ | Anagrafica Ecof |
| `data/materiali.json` | CER + coefficienti ecologici | Curato manualmente |

Una volta messi in `data/`, lancia:

```bash
python manage.py import_data
```

Cosa fa, in ordine (è idempotente, puoi rilanciarlo):

1. Legge i tre file
2. Upsert di `Veicolo` e `Materiale`
3. Geocoding di tutti gli indirizzi clienti via Nominatim (1.1 s tra una richiesta e l'altra — la prima volta è lento, poi tutto in cache su `data/geocache.json`)
4. Upsert di `Azienda` + `UnitaLocale`
5. Raggruppa righe per `(data, targa)` in `Giro`, calcola km itinerario + baricentro pesato
6. Per ogni riga chiama `calc_movimentazione()` e salva `Movimentazione` con tutti i KPI ecologici e di trasporto già pre-calcolati

> **Scorciatoia:** se Giacomo ti passa anche un `db.sqlite3` già popolato, mettilo nella root e salta il punto sopra — apri l'applicazione e i dati sono già lì.

### Vedere la dashboard come utente

Il superuser vede solo l'admin. Per vedere la dashboard ti serve un utente associato a un'`Azienda`:

1. Admin → `Azienda` → crea o seleziona un'azienda
2. Admin → `User` → crea un utente
3. Admin → `Azienda` → modifica → campo `user` → seleziona l'utente appena creato
4. Logout, login con il nuovo utente, vai su `/dashboard/`

---

## Modificare dati esistenti (indirizzi, veicoli, materiali)

**Tutte le modifiche di dati si fanno dall'admin Django**, non toccando file:

- **Indirizzi clienti** → `UnitaLocale` (campo `indirizzo`, `lat`, `lon`)
- **Veicoli** → `Veicolo`
- **Materiali / CER** → `Materiale`
- **Singole movimentazioni** → `Movimentazione`

Se modifichi un indirizzo, al prossimo `import_data` la `geocache.json` si aggiornerà automaticamente per il nuovo testo. Se vuoi forzare un nuovo geocoding immediatamente, cancella la riga corrispondente da `geocache.json`.

> **Non modificare mai a mano i campi `s1_gha`, `s2_gha`, `gha_netto`, `t1_co2`, ecc.** Sono pre-calcolati da `pipeline/calc.py`. Per ricalcolarli, rilancia `import_data`.

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
└── data/                      ❌ NON in git — chiedere a Giacomo
```

**Regola architetturale:** `core/` può importare da `pipeline/`, ma `pipeline/` non deve mai importare da `core/views` o `core/api_views`. Il pipeline è puro calcolo, riusabile fuori da Django.

---

## API

Tutti gli endpoint richiedono autenticazione (session auth, `IsAuthenticated`). JSON-only.

| Endpoint | Cosa |
|---|---|
| `GET /api/movimentazioni/` | Lista movimentazioni |
| `GET /api/movimentazioni/<id>/` | Dettaglio movimentazione |
| `GET /api/giri/<id>/` | Dettaglio giro |
| `GET /api/veicoli/` | Lista veicoli |
| `GET /api/materiali/` | Lista materiali |
| `GET /api/kpi/` | KPI aggregati (gha + CO₂) |

---

## Workflow git

Per ora siamo in due, quindi nessuna burocrazia eccessiva. Indicazioni:

- **Branch:** lavora su un branch dedicato per ogni feature (`feature/nome-corto`) o fix (`fix/bug-corto`). Non pushare su `main` direttamente per cose non triviali.
- **Pull Request:** apri una PR su GitHub anche per cose piccole, così entrambi vediamo le modifiche prima del merge. Per fix di una riga o typo, push diretto su `main` va bene.
- **Commit message:** in inglese, imperativo, sintetici. Es: `add ALLOWED_HOSTS validation`, `fix gha_netto sign for biotico`.
- **Mai committare:** `.env`, contenuto di `data/`, `db.sqlite3`, virtualenv. Il `.gitignore` li protegge ma è bene tenerlo in mente.

---

## Comandi utili

```bash
# Avvia il dev server
python manage.py runserver

# Apri una shell Django con i modelli caricati
python manage.py shell

# Re-importa i dati (cancella e ricrea — vedi import_data per i dettagli)
python manage.py import_data

# Esegue i test (se presenti)
python manage.py test

# Genera una nuova migration dopo aver modificato models.py
python manage.py makemigrations
python manage.py migrate

# Raccoglie static files (solo prima del deploy, non in dev)
python manage.py collectstatic
```

---

## Cose che fanno inciampare la prima volta

- **`SECRET_KEY` non impostata** → `.env` non esiste o non è stato copiato da `.env.example`. Django dà un errore esplicito al primo `runserver`.
- **Dashboard vuota dopo `import_data`** → l'utente con cui sei loggato non è collegato a un'`Azienda`. Vedi sezione "Vedere la dashboard come utente".
- **`import_data` lentissimo la prima volta** → è il geocoding di Nominatim (1.1 s per indirizzo per rispettare i termini d'uso). Dalla seconda esecuzione tutto è in cache.
- **Errore `no such table` su `import_data`** → ti sei dimenticato di lanciare `migrate` prima.
- **Static files non si caricano in `DEBUG=False`** → in locale lavora sempre con `DEBUG=True`. WhiteNoise serve gli static solo se hai fatto `collectstatic` prima.

---

## Contatti

Per qualsiasi cosa non chiara, problemi di setup, accesso ai file `data/` o al dump del DB di sviluppo: scrivi a Giacomo direttamente. Non aprire issue pubbliche su GitHub per richieste di credenziali o dati.
