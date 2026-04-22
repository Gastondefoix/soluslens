# CLAUDE.md — SolusLens

Operational guide for Claude Code. Read the whole file before starting any task.

---

## 1. What SolusLens is

Django dashboard for Ecof Italia that crosses waste movement data (PrometeoRifiuti) with ecological impact calculations (gha / kgCO₂). Previously named Ecof / Soluslab.

Demo user: `pfizer` / `demo1234` → Pfizer S.r.l. (2 operational units).

---

## 2. Stack

- **Backend**: Python 3.11, Django 5.x, DRF, SQLite
- **Frontend**: Tailwind CSS via CDN (NO custom CSS file), HTMX, Chart.js (dashboard), Plotly (movement detail)
- **Static**: Whitenoise
- **Repo**: `git@github.com:Gastondefoix/soluslens.git`
- **Local path**: `~/soluslens`
- **Venv**: `.venv/` — activate with `source .venv/bin/activate`

---

## 3. Base commands

```bash
# Activate venv (ALWAYS do this first)
source .venv/bin/activate

# Dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Re-import data from scratch
python manage.py import_data

# Django shell
python manage.py shell

# Static files (only if you touch static/)
python manage.py collectstatic --noinput
```

---

## 4. Project structure (keep the separation)

```
soluslens/
├── core/                     # models, admin, UI views, HTMX partials
├── pipeline/                 # calc.py, importer, data transformations
│   └── calc.py               # ⚠️ PRODUCT CORE — changes require tests
├── api/                      # DRF serializers + viewsets
├── templates/                # base.html + pages
│   └── base.html             # Tailwind config + @layer components
├── core/templatetags/        # dashboard_filters.py
└── static/                   # static assets (NO custom CSS)
```

**Golden rule**: `pipeline/` never imports from `core/views` or `api/`. Only from models. This keeps the calculation engine testable in isolation.

---

## 5. Calculation model (pipeline/calc.py)

### Constant

```python
GHA_FACTOR = 1800.0  # kgCO₂ per gha/year
```

### Variables (always positive in the calculation)

- **S1** = Q × (t_smalt + t_verg) / GHA_FACTOR — biocapacity freed (reduced emission absorption)
- **S2** = Q × (t_tratt + t_ric) / GHA_FACTOR — ecological footprint from recovery processes
- **S**  = Q × (t_smalt + t_tratt) / GHA_FACTOR — ecological footprint from undifferentiated waste
- **H**  = (Q/1000) / yield × f_equiv — biocapacity freed from reduced land exploitation

### Branch logic (evaluation order)

1. **hazardous** → only T1 and T2, `gha = None`
2. `t_verg is None` AND `tipo != 'biotico'` → **indiff branch**: `gha_netto = -S`, `s_gha_tipo = 'indiff'`
3. `t_verg is None` AND `tipo == 'biotico'` → **biotico_no_tverg**: `gha_netto = H - S`, `s_gha_tipo = 'biotico'`
4. `t_verg is not None` → **recyclable**: `gha_netto = S1 - S2 + H`, `s_gha_tipo = None`

### Transport (always kgCO₂, NEVER converted to gha)

- **T1** = (itinerary_km × co2_km(0)) / n_clients
- **T2** = (co2_km(C) − co2_km(0)) × barycenter_distance × (Q/C)
- Logarithmic curve: `co2_km(C) = co2_empty + b × ln(1+C)`

### ⚠️ Sign rules — DO NOT VIOLATE

- S1, S2, S, H, T1, T2 are **always positive** in the data returned by the calculation
- The logical sign is communicated **in the UI** via explicit operators (−, +, =) and color
- **Only `gha_netto` carries an explicit sign** (+/−)
- If you modify `calc.py`, update/run the regression tests before committing

---

## 6. UI — Final naming

| KPI | Name | Condition / Color |
|-----|------|-------------------|
| 1 | Process Biocapacity | if `gha_processo ≥ 0` → sl-blue |
| 1 | Ecological Footprint | if `gha_processo < 0` → sl-magenta |
| 2 | Freed Biocapacity | H from land → sl-blue |
| 3 | Ecological Balance | `gha_netto`: sl-green if ≥ 0, sl-magenta if < 0 — **only value with explicit sign** |
| 4 | Delivered Quantity | kg |

---

## 7. Template filters (core/templatetags/dashboard_filters.py)

- **`gha_fmt`** → absolute value, 4 decimals, Italian comma
- **`co2_fmt`** → absolute value, 2 decimals, Italian comma
- **`saldo_fmt`** → explicit +/− sign, 4 decimals

**Rule**: `saldo_fmt` is used **only** on `gha_netto`. For S1/S2/S/H/T1/T2 always use `gha_fmt` or `co2_fmt` (the sign is rendered by the operator in the HTML).

---

## 8. Design system (Linear-inspired, see DESIGN.md)

### Palette

```js
'sl-blue':     '#0975BD'   // Process Biocapacity ≥ 0
'sl-magenta':  '#CA1F7A'   // Ecological Footprint / negative balance
'sl-coral':    '#FF6B35'   // Bars, sparklines, chart highlights
'sl-green':    '#6BDDAE'   // Ecological Balance ≥ 0
```

Interactive accent (UI chrome, not calculations):
```
Brand Indigo:  #5e6ad2     // Primary CTAs, active borders
Accent Violet: #7170ff     // Links, active states
```

### Fonts

- **Inter Variable** with `font-feature-settings: "cv01", "ss03"` → all UI text
- **Berkeley Mono** (fallback: JetBrains Mono) → all numbers, KPI values, CER codes, plates, units

### Backgrounds & Borders

- Page: `#08090a`, Panels: `#0f1011`, Cards: `rgba(255,255,255,0.02)`
- Borders: `1px solid rgba(255,255,255,0.05)` default, `rgba(255,255,255,0.08)` standard
- Elevation via background luminance stepping — no drop shadows

### Border radius

- 2px: inline badges
- 6px: buttons, inputs
- 8px: cards
- 12px: panels

### Motion

- Only functional transitions (e.g. bar width `0.2s ease`)
- No decorative animations, no hover scale/translate effects

---

## 9. URL structure

```
/                           → redirect to dashboard
/login/                     → LoginView
/logout/                    → LogoutView → /login/
/dashboard/                 → dashboard view
/dashboard/partial/         → HTMX partial
/movimentazioni/<id>/       → detail + Plotly curve
/tabelle/veicoli/           → fleet + sparklines
/tabelle/materiali/         → emission factors gha/T
/api/movimentazioni/        → DRF list
/api/movimentazioni/<id>/   → DRF detail
/api/giri/<id>/             → DRF giro
/api/veicoli/               → DRF public
/api/materiali/             → DRF public
/api/kpi/                   → aggregates + time series
/admin/                     → Django admin
```

---

## 10. Data state

- 1405 movements, 144 routes, 133 companies, 63 fixed clients, 166 operational units, 15 vehicles, 28 materials
- **Vehicles missing** from `dataset_automezzi.json`: `FD603GV`, `GR306PC`

---

## 11. ⚠️ Things NOT to do

- **DO NOT reintroduce custom CSS** (`base.css` was deleted for a reason). All styling goes in Tailwind CDN + `@layer components` in `base.html`.
- **DO NOT modify `GHA_FACTOR = 1800.0`** without explicit discussion.
- **DO NOT convert T1/T2 to gha**: transport stays in kgCO₂.
- **DO NOT make `pipeline/` depend on `core/views` or `api/`**.
- **DO NOT modify `calc.py` without running regression tests afterwards** (when they exist).
- **DO NOT use `saldo_fmt` on values other than `gha_netto`**.
- **DO NOT use semantic accent colors (sl-blue, sl-magenta, sl-green) decoratively** — they carry calculation meaning.
- **DO NOT skip `"cv01", "ss03"`** on Inter Variable — it reverts to generic Inter.
- **DO NOT use font-weight 700** — max is 590, workhorse is 510.
- **DO NOT use `#ffffff` as primary text** — use `#f7f8f8`.
- **DO NOT use solid dark borders on dark backgrounds** — use semi-transparent white (`rgba(255,255,255,0.05–0.08)`).

---

## 12. Recommended task workflow

1. **Read this file** before starting.
2. For non-trivial tasks (>1 file, refactor, new features), **propose a plan first** before writing code. Wait for confirmation.
3. After each completed task: **one atomic commit** with a descriptive message in English (imperative: "add", "fix", "refactor").
4. If you touch `pipeline/calc.py`: run the tests (when present) **before** committing.
5. If you're unsure about the sign convention, **ask** instead of guessing.

---

## 13. Pending (suggested order)

1. Fix S2 display without sign (use `saldo_fmt` only for `gha_netto`)
2. Add FD603GV and GR306PC to `dataset_automezzi.json`
3. Regression tests on `pipeline/calc.py` (one case per branch)
4. Migrate UI to Linear design system (Inter Variable + Berkeley Mono, new surfaces/borders)
5. Complete `@layer components` refactor across templates
6. Task 12: Deploy Railway + GitHub Actions CI/CD
7. OSRM for real road distances (replaces Haversine) — requires caching
8. Update Soluslab with the new sign convention

---

## 14. Historical bugs to remember

- **Recurring base.css corruption** → solved by deleting the file and migrating to Tailwind CDN. **Do not recreate** `base.css` or equivalents.
- **Chart spikes** → caused by incorrect aggregations on dates; always check temporal grouping.
- **Chart overflow** → keep containers with fixed `height` and `overflow: hidden`.
- **Italian dates**: always use `dd/mm/yyyy` format in the UI.
