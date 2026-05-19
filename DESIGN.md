# SolusLens Design System
*Adapted from Linear — constrained to SolusLens rules*

## 1. Visual Theme & Atmosphere

SolusLens is a dark-native dashboard built on a pure `#000000` OLED canvas. Like Linear, content emerges from darkness — but where Linear uses translucency and soft radius to soften edges, SolusLens uses hard 2px borders and zero radius to project precision engineering. The aesthetic is clinical and deliberate: a data instrument, not a product page.

The typographic system pairs **DM Sans** for all UI prose with **JetBrains Mono** for every numeric value, CER code, license plate, and form number. This split is semantic: prose explains, mono measures. There are no animations, no transitions, no hover effects beyond functional state changes.

Color is restrained. The sl-* palette provides five accent colors with strict functional roles: `sl-blue` for positive process biocapacity, `sl-magenta` for ecological footprint and negative balances, `sl-coral` for data bars and highlights, `sl-green` for the ecological balance when positive. Everything else is near-black surfaces and cool-gray text.

**Key Characteristics:**
- OLED black everywhere: `#000000` base, `#0a0a0a` surface, no soft near-black variants
- `border-radius: 0` on every element — no exceptions
- 2px solid borders using `sl-border` (`#2a2a2a`) or `sl-border-b` (`#404040`)
- Zero animations, zero transitions, zero fancy hover effects
- DM Sans (UI text) + JetBrains Mono (all numbers and codes) — no other fonts
- Five accent colors, each with a fixed semantic role — not decorative
- Tailwind CDN + `@layer components` only — no custom CSS files

---

## 2. Color Palette & Roles

### Background Surfaces

| Token | Value | Use |
|-------|-------|-----|
| `#000000` | OLED black | Page background, deepest canvas |
| `sl-surface` (`#0a0a0a`) | Panel and card backgrounds | |
| `#111111` | Slightly elevated rows, hover state on table rows | |

### Accent Colors (functional — not decorative)

| Token | Value | Role |
|-------|-------|------|
| `sl-blue` | `#0975BD` | Process Biocapacity ≥ 0, primary interactive elements |
| `sl-magenta` | `#CA1F7A` | Ecological Footprint, negative balances, danger states |
| `sl-coral` | `#FF6B35` | Data bars, sparklines, highlights |
| `sl-green` | `#6BDDAE` | Ecological Balance when `gha_netto ≥ 0`, success states |

> **Rule**: Never apply an accent color outside its semantic role. `sl-magenta` is not a generic secondary color — it means "negative / ecological cost".

### Text

| Role | Value | Use |
|------|-------|-----|
| Primary | `#f0f0f0` | Headings, key values, labels |
| Secondary | `#a0a0a0` | Body text, descriptions |
| Muted | `#606060` | Timestamps, metadata, placeholders |
| Disabled | `#404040` | Inactive states |

### Borders

| Token | Value | Use |
|-------|-------|-----|
| `sl-border` (`#2a2a2a`) | 2px solid | Default border on cards, tables, inputs |
| `sl-border-b` (`#404040`) | 2px solid | Emphasized separation, active/focus states |

> **Rule**: All borders are 2px solid. No 1px, no semi-transparent rgba, no box-shadow as border substitute.

---

## 3. Typography Rules

### Font Families

- **UI / prose**: `DM Sans` — all labels, headings, body, navigation, buttons
- **Numeric / code**: `JetBrains Mono` — every number, KPI value, CER code, license plate, form field with numeric input

### When to use JetBrains Mono

Apply `font-mono` (JetBrains Mono) to:
- KPI values (gha, kgCO₂, kg quantities)
- CER waste codes
- Vehicle license plates
- Route distance and transport values
- Table cells containing numeric data
- Any `<input>` with `type="number"`

Apply `font-sans` (DM Sans) to everything else.

### Hierarchy

| Role | Size | Weight | Use |
|------|------|--------|-----|
| Page title | 20px | 600 | Dashboard section headers |
| Card heading | 16px | 600 | Card titles, section labels |
| Body | 14px | 400 | Descriptions, nav links, body text |
| Label | 13px | 500 | Form labels, table headers (`sl-th`) |
| Caption | 12px | 400 | Metadata, timestamps, footnotes |
| KPI value | 28–32px | 600 | Primary KPI numbers (mono) |
| KPI unit | 13px | 400 | Unit labels below KPI (mono) |
| Table value | 14px | 400 | Table cell numbers (mono) |

### Principles

- **Mono is semantic, not aesthetic**: Don't use JetBrains Mono for non-numeric content just because it looks technical.
- **No letter-spacing manipulation**: DM Sans and JetBrains Mono work at default tracking. Do not add artificial letter-spacing.
- **Weight ceiling is 600**: No bold (700) or heavier. Max emphasis = 600 semibold.

---

## 4. Component Stylings

All components are implemented as `@layer components` Tailwind classes in `base.html`. Use these classes directly — do not re-implement with inline utility variants.

### Cards — `sl-card`
- Background: `sl-surface` (`#0a0a0a`)
- Border: `2px solid sl-border` (`#2a2a2a`)
- Radius: 0
- Padding: 16px (use Tailwind `p-4`)
- No shadow

### Labels — `sl-label`
- Font: DM Sans 12px weight 500
- Color: `#a0a0a0`
- Uppercase tracking: default (no artificial letter-spacing)
- Use: above KPI values, form field labels

### KPI values — `sl-kpi`
- Font: JetBrains Mono 28px weight 600
- Color: determined by semantic role (sl-blue / sl-magenta / sl-green)
- Use: primary dashboard metrics

### Units — `sl-unit`
- Font: JetBrains Mono 13px weight 400
- Color: `#606060`
- Use: unit labels (gha, kgCO₂, kg) adjacent to `sl-kpi`

### Buttons

**Primary — `sl-btn`**
- Background: `sl-blue` (`#0975BD`)
- Text: `#ffffff` 14px DM Sans weight 500
- Padding: 8px 16px
- Border: none
- Radius: 0

**Ghost — `sl-btn-ghost`**
- Background: transparent
- Text: `#a0a0a0`
- Border: `2px solid sl-border` (`#2a2a2a`)
- Radius: 0
- Hover: border color → `sl-border-b` (`#404040`), text → `#f0f0f0`

**Active / Selected — `sl-btn-active`**
- Background: `sl-blue` at 15% opacity or solid `#0a1a2a`
- Text: `sl-blue` (`#0975BD`)
- Border: `2px solid sl-blue`
- Radius: 0

### Table

**Header cell — `sl-th`**
- Font: DM Sans 13px weight 500
- Color: `#606060`
- Border-bottom: `2px solid sl-border` (`#2a2a2a`)
- Padding: 8px 12px
- Background: `#000000`

**Data cell — `sl-td`**
- Font: JetBrains Mono 14px for numbers, DM Sans 14px for text
- Color: `#f0f0f0`
- Border-bottom: `1px solid sl-border` (`#2a2a2a`)
- Padding: 8px 12px

### Badges

**Default — `sl-badge`**
- Background: `#1a1a1a`
- Text: `#a0a0a0` 12px weight 500
- Border: `1px solid sl-border`
- Radius: 0
- Padding: 2px 8px

**Danger — `sl-badge-danger`**
- Background: transparent
- Text: `sl-magenta` (`#CA1F7A`)
- Border: `1px solid sl-magenta`

**Bio — `sl-badge-bio`**
- Background: transparent
- Text: `sl-green` (`#6BDDAE`)
- Border: `1px solid sl-green`

**Neutral — `sl-badge-neutral`**
- Background: `#1a1a1a`
- Text: `#606060`
- Border: `1px solid sl-border`

### Bars — `sl-bar-track`, `sl-bar-coral`, `sl-bar-blue`, `sl-bar-magenta`
- Track: `#1a1a1a`, height 4px, radius 0
- Fill colors: `sl-coral`, `sl-blue`, `sl-magenta` respectively
- No animation on fill — static width set by inline style

### Metric rows — `sl-metric`, `sl-metric-label`, `sl-metric-value`
- Row: flex space-between, border-bottom `1px solid sl-border`, padding 8px 0
- Label: DM Sans 13px `#606060`
- Value: JetBrains Mono 14px `#f0f0f0`

### Detail cells — `sl-detail-label`, `sl-detail-value`
- Label: DM Sans 12px `#606060` uppercase
- Value: JetBrains Mono 14px `#f0f0f0`

---

## 5. Layout Principles

### Spacing
- Base unit: 4px
- Scale in use: 4, 8, 12, 16, 24, 32, 48px
- Tailwind mapping: `p-1` (4px) → `p-2` (8px) → `p-3` (12px) → `p-4` (16px) → `p-6` (24px) → `p-8` (32px)

### Grid
- Dashboard KPIs: 4-column grid on desktop, 2-column on tablet, 1-column on mobile
- Tables: full-width, no card wrapping
- Detail page: 2-column (chart left, metrics right) collapsing to single column on mobile

### Whitespace philosophy
- Separation is done by borders and spacing — not by background color variation or whitespace alone
- Section gaps: 32px (`gap-8`) between major sections
- Never use empty decorative spacer elements

### No elevation system
Unlike Linear, SolusLens has no shadow-based depth. Hierarchy is expressed purely through:
1. Border presence / absence
2. Text color (primary → secondary → muted)
3. Font weight (600 → 500 → 400)
4. Accent color (only on semantically meaningful elements)

---

## 6. Data Visualization

### Chart.js (Dashboard)
- Background: `#000000`
- Grid lines: `#2a2a2a` 1px
- Tick labels: `#606060` 12px JetBrains Mono
- Dataset colors: `sl-coral` as primary, `sl-blue` as secondary
- No animations (`animation: false`)
- No rounded bars

### Plotly (Movement detail — logarithmic curve)
- Paper and plot background: `#000000`
- Line color: `sl-blue` for curve, `sl-magenta` for current load marker
- Font: JetBrains Mono for axis labels
- No hover animations

---

## 7. Sign & Color Convention for Calculations

This is the most critical design rule — it maps directly to `pipeline/calc.py` output.

| Value | Display font | Color | Sign |
|-------|-------------|-------|------|
| S1, S2, S, H | JetBrains Mono | neutral (`#f0f0f0`) | no sign — operator shown in HTML |
| T1, T2 | JetBrains Mono | neutral (`#f0f0f0`) | no sign |
| `gha_netto ≥ 0` | JetBrains Mono | `sl-green` | explicit `+` via `saldo_fmt` |
| `gha_netto < 0` | JetBrains Mono | `sl-magenta` | explicit `−` via `saldo_fmt` |
| `gha_processo ≥ 0` | JetBrains Mono | `sl-blue` | labeled "Process Biocapacity" |
| `gha_processo < 0` | JetBrains Mono | `sl-magenta` | labeled "Ecological Footprint" |

**Template filter rules:**
- `gha_fmt` → absolute value, 4 decimal places, Italian comma — for S1, S2, S, H
- `co2_fmt` → absolute value, 2 decimal places, Italian comma — for T1, T2
- `saldo_fmt` → explicit +/− sign, 4 decimal places — **only** for `gha_netto`

---

## 8. Do's and Don'ts

### Do
- Use `border-radius: 0` on every element — components, buttons, inputs, modals, badges
- Use 2px borders (`sl-border` `#2a2a2a` default, `sl-border-b` `#404040` for emphasis)
- Use JetBrains Mono for every number, KPI, code, plate, unit
- Use DM Sans for all prose, labels, navigation, button text
- Apply accent colors only for their designated semantic role
- Use `saldo_fmt` exclusively on `gha_netto`
- Use `gha_fmt` / `co2_fmt` on S1, S2, S, H, T1, T2 (absolute, no sign)
- Show the logical sign for S1/S2/S/H via explicit HTML operators (`−`, `+`, `=`)
- Keep all styling in Tailwind CDN + `@layer components` in `base.html`
- Use Italian date format `dd/mm/yyyy` everywhere in the UI

### Don't
- Don't add `border-radius` to anything — not even 2px
- Don't add CSS animations, transitions, or hover effects beyond color/border state changes
- Don't create a `base.css` or any custom CSS file
- Don't use `saldo_fmt` on S1, S2, S, H, T1, or T2
- Don't convert T1/T2 to gha — they stay in kgCO₂
- Don't use `sl-magenta` or `sl-green` decoratively — they carry calculation meaning
- Don't modify `GHA_FACTOR = 1800.0` without explicit discussion
- Don't import `core/views` or `api/` from `pipeline/`
- Don't modify `calc.py` without running regression tests first
- Don't use rounded corners on Chart.js bars

---

## 9. Agent Prompt Guide

### Quick Reference

```
Background:    #000000 (OLED)
Surface:       #0a0a0a  (sl-surface)
Border:        #2a2a2a 2px solid  (sl-border)
Border emph:   #404040 2px solid  (sl-border-b)
Text primary:  #f0f0f0
Text secondary:#a0a0a0
Text muted:    #606060
Accent blue:   #0975BD  (sl-blue)   → positive biocapacity
Accent magenta:#CA1F7A  (sl-magenta)→ footprint / negative
Accent coral:  #FF6B35  (sl-coral)  → bars / highlights
Accent green:  #6BDDAE  (sl-green)  → positive balance
UI font:       DM Sans
Data font:     JetBrains Mono
Radius:        0 everywhere
Borders:       2px solid, always
Animations:    none
```

### Example Prompts

- "Build a KPI card using `sl-card`. `sl-label` for the title above. `sl-kpi` for the value in JetBrains Mono, colored `sl-blue`. `sl-unit` for the unit below. No radius, no shadow."

- "Create a data table: full width, `sl-th` for headers (DM Sans 13px `#606060`), `sl-td` for cells (JetBrains Mono 14px for numbers). `border-bottom 1px solid #2a2a2a` on each row."

- "Design a movement detail metric row using `sl-metric`: flex space-between, label DM Sans 13px `#606060`, value JetBrains Mono 14px `#f0f0f0`, border-bottom `1px solid #2a2a2a`."

- "Add a balance display: value in JetBrains Mono with `saldo_fmt` filter. If positive → `sl-green` + label 'Ecological Balance'. If negative → `sl-magenta` + label 'Ecological Footprint'. No radius, 2px border."

- "Build a filter bar: ghost buttons (`sl-btn-ghost`) for each filter option. Active state with `sl-btn-active` shows `sl-blue` border and text. No radius, no transitions."
