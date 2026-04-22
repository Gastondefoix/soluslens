# SolusLens Design System
*Linear design language applied to a data dashboard*

## 1. Visual Theme & Atmosphere

SolusLens is a dark-native dashboard. The design language is borrowed from Linear: a near-black canvas where content emerges through luminance stepping, semi-transparent surfaces, and a single chromatic accent. The impression is precision engineering — clean, dense, intentional.

Unlike a generic dark theme, depth is communicated through background opacity stepping (`rgba(255,255,255,0.02)` → `0.04` → `0.05`) rather than shadows or heavy borders. Borders are whisper-thin semi-transparent white. The only chromatic presence outside UI chrome is the semantic accent palette for ecological calculations.

**Key Characteristics:**
- Near-black canvas: `#08090a` page, `#0f1011` panels, `#191a1b` elevated surfaces
- Inter Variable with `"cv01", "ss03"` for all UI text
- Berkeley Mono (fallback: JetBrains Mono) for numbers, codes, plates, units
- Single interactive accent: indigo-violet `#5e6ad2` / `#7170ff`
- Semantic calculation accents: blue, magenta, green, coral — reserved for data meaning
- Semi-transparent white borders: `rgba(255,255,255,0.05)` to `rgba(255,255,255,0.08)`
- Subtle border-radius: 6px buttons/inputs, 8px cards, 12px panels
- Minimal motion: only functional state transitions (no decorative animations)
- Tailwind CDN + `@layer components` in `base.html` — no custom CSS files

---

## 2. Color Palette & Roles

### Background Surfaces

| Value | Role |
|-------|------|
| `#010102` / `#08090a` | Page background — the deepest canvas |
| `#0f1011` | Panel and sidebar backgrounds |
| `#191a1b` | Elevated cards, dropdowns, containers |
| `#28282c` | Hover states, slightly elevated components |

### Text

| Value | Role |
|-------|------|
| `#f7f8f8` | Primary text — near-white (not pure white) |
| `#d0d6e0` | Secondary text — body, descriptions |
| `#8a8f98` | Tertiary — placeholders, metadata |
| `#62666d` | Quaternary — timestamps, disabled, subtle labels |

### Interactive Accent (UI chrome only)

| Token | Value | Use |
|-------|-------|-----|
| Brand Indigo | `#5e6ad2` | Primary CTA backgrounds, active borders |
| Accent Violet | `#7170ff` | Links, active states, selected items |
| Accent Hover | `#828fff` | Hover on accent elements |

### Semantic Calculation Accents

These colors carry specific meaning tied to `pipeline/calc.py` output. **Do not use them decoratively.**

| Token | Value | Meaning |
|-------|-------|---------|
| `sl-blue` `#0975BD` | Process Biocapacity (`gha_processo ≥ 0`) |
| `sl-magenta` `#CA1F7A` | Ecological Footprint / negative balance (`gha_processo < 0`, `gha_netto < 0`) |
| `sl-green` `#6BDDAE` | Ecological Balance positive (`gha_netto ≥ 0`) |
| `sl-coral` `#FF6B35` | Data bars, sparklines, chart highlights |

### Borders

| Value | Use |
|-------|-----|
| `rgba(255,255,255,0.05)` | Default — cards, containers, subtle separations |
| `rgba(255,255,255,0.08)` | Standard — inputs, code blocks, prominent cards |
| `#23252a` | Solid fallback for bordered elements |

---

## 3. Typography

### Font Families

- **UI text**: `Inter Variable` — feature-settings `"cv01", "ss03"` globally
  - Fallbacks: `SF Pro Display, -apple-system, system-ui, Helvetica Neue`
- **Data / code**: `Berkeley Mono` — for all numbers, KPI values, CER codes, license plates, units
  - Fallbacks: `JetBrains Mono, ui-monospace, SF Mono, Menlo`

### When to use Berkeley Mono

Apply monospace to:
- KPI values (gha, kgCO₂, kg)
- CER waste codes
- Vehicle license plates
- Route distances and transport values
- Table cells with numeric data
- Form inputs with `type="number"`

Apply Inter Variable to everything else.

### Hierarchy

| Role | Size | Weight | Letter-spacing | Use |
|------|------|--------|----------------|-----|
| Display | 48px | 510 | -1.056px | Hero section headlines |
| Heading 1 | 32px | 400 | -0.704px | Page titles |
| Heading 2 | 24px | 400 | -0.288px | Section headings |
| Heading 3 | 20px | 590 | -0.24px | Card headers, feature titles |
| Body | 16px | 400 | normal | Standard text |
| Body Medium | 16px | 510 | normal | Navigation, labels |
| Small | 15px | 400 | -0.165px | Secondary body |
| Caption | 13px | 400–510 | -0.13px | Metadata, timestamps |
| Label | 12px | 400–590 | normal | Button text, small labels |
| KPI value | 28–32px | 600 | normal | Primary KPI numbers (mono) |
| KPI unit | 13px | 400 | normal | Unit labels (mono) |
| Table value | 14px | 400 | normal | Table cell numbers (mono) |

### Principles

- **510 is the signature weight**: Between regular (400) and medium (500) — the default for navigation, labels, emphasized UI text
- **Compression at scale**: Display text always runs negative letter-spacing; below 16px, tracking returns to normal
- **`"cv01", "ss03"` are non-negotiable**: Without them, it's generic Inter — these features define the visual identity
- **Weight ceiling 590**: No bold (700). Hierarchy through 400 → 510 → 590

---

## 4. Component Stylings

All components are implemented as `@layer components` Tailwind classes in `base.html`.

### Cards — `sl-card`
- Background: `rgba(255,255,255,0.02)`
- Border: `1px solid rgba(255,255,255,0.08)`
- Radius: 8px
- Padding: 16px
- Shadow: none at rest; `rgba(0,0,0,0.2) 0px 0px 0px 1px` on hover

### Buttons

**Primary — `sl-btn`**
- Background: `#5e6ad2`
- Text: `#ffffff`, Inter Variable 14px weight 510
- Padding: 8px 16px
- Radius: 6px
- Hover: background → `#828fff`

**Ghost — `sl-btn-ghost`**
- Background: `rgba(255,255,255,0.02)`
- Text: `#e2e4e7`
- Border: `1px solid rgba(255,255,255,0.08)`
- Radius: 6px
- Hover: background → `rgba(255,255,255,0.05)`

**Active / Selected — `sl-btn-active`**
- Background: `rgba(94,106,210,0.15)`
- Text: `#7170ff`
- Border: `1px solid #5e6ad2`
- Radius: 6px

### Labels — `sl-label`
- Font: Inter Variable 12px weight 510
- Color: `#8a8f98`
- Feature-settings: `"cv01", "ss03"`

### KPI values — `sl-kpi`
- Font: Berkeley Mono 28px weight 600
- Color: determined by semantic role (sl-blue / sl-magenta / sl-green)

### Units — `sl-unit`
- Font: Berkeley Mono 13px weight 400
- Color: `#62666d`

### Table

**Header — `sl-th`**
- Font: Inter Variable 13px weight 510
- Color: `#62666d`
- Border-bottom: `1px solid rgba(255,255,255,0.08)`
- Padding: 8px 12px

**Cell — `sl-td`**
- Font: Berkeley Mono 14px for numbers, Inter Variable 14px for text
- Color: `#d0d6e0`
- Border-bottom: `1px solid rgba(255,255,255,0.05)`
- Padding: 8px 12px

### Badges

**Default — `sl-badge`**
- Background: `rgba(255,255,255,0.05)`
- Text: `#f7f8f8`, 12px weight 510
- Border: `1px solid rgba(255,255,255,0.05)`
- Radius: 2px
- Padding: 2px 8px

**Danger — `sl-badge-danger`**
- Background: transparent
- Text: `sl-magenta` (`#CA1F7A`)
- Border: `1px solid rgba(202,31,122,0.4)`
- Radius: 2px

**Bio — `sl-badge-bio`**
- Background: transparent
- Text: `sl-green` (`#6BDDAE`)
- Border: `1px solid rgba(107,221,174,0.4)`
- Radius: 2px

**Neutral — `sl-badge-neutral`**
- Background: transparent
- Text: `#8a8f98`
- Border: `1px solid rgba(255,255,255,0.08)`
- Radius: 2px

### Bars — `sl-bar-track`, `sl-bar-coral`, `sl-bar-blue`, `sl-bar-magenta`
- Track: `rgba(255,255,255,0.05)`, height 4px, radius 2px
- Fill: `sl-coral`, `sl-blue`, `sl-magenta` respectively
- Transition: `width 0.2s ease` (functional, not decorative)

### Metric rows — `sl-metric`, `sl-metric-label`, `sl-metric-value`
- Row: flex space-between, border-bottom `1px solid rgba(255,255,255,0.05)`, padding 8px 0
- Label: Inter Variable 13px `#8a8f98`
- Value: Berkeley Mono 14px `#d0d6e0`

### Detail cells — `sl-detail-label`, `sl-detail-value`
- Label: Inter Variable 12px `#62666d`
- Value: Berkeley Mono 14px `#d0d6e0`

---

## 5. Layout Principles

### Spacing
- Base unit: 8px
- Scale: 4, 8, 12, 16, 24, 32, 48px
- Tailwind: `p-1`=4px, `p-2`=8px, `p-3`=12px, `p-4`=16px, `p-6`=24px, `p-8`=32px

### Border Radius Scale
| Value | Use |
|-------|-----|
| 2px | Inline badges, toolbar micro-buttons |
| 6px | Buttons, inputs, functional elements |
| 8px | Cards, dropdowns, containers |
| 12px | Panels, featured sections |

### Grid
- Dashboard KPIs: 4-column desktop, 2-column tablet, 1-column mobile
- Tables: full-width, inside `sl-card` wrapper
- Detail page: 2-column (chart + metrics), collapsing to single on mobile

### Elevation (luminance stepping — no shadows)
| Level | Background | Use |
|-------|-----------|-----|
| 0 | `#08090a` | Page canvas |
| 1 | `#0f1011` | Panels, sidebar |
| 2 | `rgba(255,255,255,0.02)` | Cards, containers |
| 3 | `rgba(255,255,255,0.04)` | Hover state |
| 4 | `rgba(255,255,255,0.05)` | Active/focused container |

---

## 6. Data Visualization

### Chart.js (Dashboard)
- Background: `#08090a`
- Grid lines: `rgba(255,255,255,0.05)` 1px
- Tick labels: `#8a8f98` 12px Berkeley Mono
- Dataset colors: `sl-coral` primary, `sl-blue` secondary
- Bar radius: 2px
- Animation: `duration: 300` (functional feedback, not decorative)

### Plotly (Movement detail — logarithmic curve)
- Paper + plot background: `#08090a`
- Line color: `sl-blue` for curve, `sl-magenta` for current load marker
- Font: Berkeley Mono for axis labels, color `#8a8f98`

---

## 7. Sign & Color Convention for Calculations

Maps `pipeline/calc.py` output to display. **Do not alter this mapping.**

| Value | Font | Color | Sign |
|-------|------|-------|------|
| S1, S2, S, H | Berkeley Mono | `#d0d6e0` | none — operator shown in HTML |
| T1, T2 | Berkeley Mono | `#d0d6e0` | none |
| `gha_netto ≥ 0` | Berkeley Mono | `sl-green` `#6BDDAE` | explicit `+` via `saldo_fmt` |
| `gha_netto < 0` | Berkeley Mono | `sl-magenta` `#CA1F7A` | explicit `−` via `saldo_fmt` |
| `gha_processo ≥ 0` | Berkeley Mono | `sl-blue` `#0975BD` | labeled "Process Biocapacity" |
| `gha_processo < 0` | Berkeley Mono | `sl-magenta` `#CA1F7A` | labeled "Ecological Footprint" |

**Template filters:**
- `gha_fmt` → absolute value, 4 decimals, Italian comma — S1, S2, S, H
- `co2_fmt` → absolute value, 2 decimals, Italian comma — T1, T2
- `saldo_fmt` → explicit +/− sign, 4 decimals — **only** `gha_netto`

---

## 8. Do's and Don'ts

### Do
- Use Inter Variable with `"cv01", "ss03"` on ALL UI text — non-negotiable
- Use weight 510 as default emphasis (navigation, labels, UI text)
- Use Berkeley Mono for every number, KPI, CER code, plate, unit
- Use semi-transparent white borders (`rgba(255,255,255,0.05–0.08)`)
- Communicate elevation through background luminance stepping, not shadows
- Keep semantic calculation colors (`sl-blue`, `sl-magenta`, `sl-green`, `sl-coral`) for their designated roles only
- Use `saldo_fmt` exclusively on `gha_netto`
- Use `gha_fmt` / `co2_fmt` on S1, S2, S, H, T1, T2 (absolute values)
- Keep all styling in Tailwind CDN + `@layer components` in `base.html`
- Use Italian date format `dd/mm/yyyy`

### Don't
- Don't use `#ffffff` as primary text — use `#f7f8f8`
- Don't use solid dark borders on dark backgrounds — use semi-transparent white
- Don't skip `"cv01", "ss03"` on Inter — it reverts to generic Inter
- Don't use weight 700 — max is 590, workhorse is 510
- Don't apply semantic accent colors (sl-blue, sl-magenta, sl-green) for decoration
- Don't use `saldo_fmt` on S1, S2, S, H, T1, T2
- Don't convert T1/T2 to gha — stays in kgCO₂
- Don't create a `base.css` or any custom CSS file
- Don't modify `GHA_FACTOR = 1800.0` without explicit discussion
- Don't import `core/views` or `api/` from `pipeline/`

---

## 9. Agent Prompt Guide

### Quick Reference

```
Page background:   #08090a
Panel background:  #0f1011
Card surface:      rgba(255,255,255,0.02)
Hover surface:     rgba(255,255,255,0.04)
Border default:    1px solid rgba(255,255,255,0.05)
Border standard:   1px solid rgba(255,255,255,0.08)
Primary text:      #f7f8f8
Secondary text:    #d0d6e0
Muted text:        #8a8f98
Subtle text:       #62666d
UI accent:         #5e6ad2 (bg) / #7170ff (interactive)
Bio-blue:          #0975BD  → positive biocapacity
Magenta:           #CA1F7A  → footprint / negative
Coral:             #FF6B35  → bars / charts
Green:             #6BDDAE  → positive balance
UI font:           Inter Variable, "cv01" "ss03"
Data font:         Berkeley Mono
Radius scale:      2px badge | 6px button | 8px card | 12px panel
```

### Example Prompts

- "KPI card: `sl-card` (8px radius, `rgba(255,255,255,0.02)` bg, `1px solid rgba(255,255,255,0.08)` border). `sl-label` title in Inter Variable 12px weight 510 `#8a8f98`. Value in Berkeley Mono 28px weight 600 colored `#0975BD`. Unit in Berkeley Mono 13px `#62666d`."

- "Data table: `sl-th` headers Inter Variable 13px 510 `#62666d`, bottom `1px solid rgba(255,255,255,0.08)`. `sl-td` cells Berkeley Mono 14px `#d0d6e0` for numbers, Inter Variable for text. Row separator `1px solid rgba(255,255,255,0.05)`."

- "Navigation: sticky header on `#0f1011`, bottom `1px solid rgba(255,255,255,0.05)`. Links Inter Variable 14px 510 `#d0d6e0`. Active link `#7170ff`. Primary CTA `sl-btn` (`#5e6ad2`, 6px radius)."

- "Balance display: Berkeley Mono value with `saldo_fmt`. If `gha_netto ≥ 0` → color `#6BDDAE`, label 'Ecological Balance'. If negative → `#CA1F7A`, label 'Ecological Footprint'. Badge `sl-badge-bio` or `sl-badge-danger`."
