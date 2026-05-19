from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Azienda, UnitaLocale, Movimentazione
from django.db.models import Sum, Count, Q
from collections import defaultdict
import json
import math


def get_azienda_or_redirect(request):
    try:
        return request.user.azienda
    except Exception:
        return None


@login_required
def dashboard(request):
    azienda = get_azienda_or_redirect(request)
    if not azienda:
        return redirect('/admin/')

    unita_locali = UnitaLocale.objects.filter(azienda=azienda).order_by('indirizzo')

    # Available months
    mesi = list(
        Movimentazione.objects.filter(unita_locale__azienda=azienda)
        .values_list('giro__data__year', 'giro__data__month')
        .distinct()
        .order_by('giro__data__year', 'giro__data__month')
    )
    mesi_str = [f"{y:04d}-{m:02d}" for y, m in mesi]

    # Default: most recent month
    mese_default = request.GET.get('mese', mesi_str[-1] if mesi_str else '')
    ul_id = str(request.GET.get('ul', ''))

    # Compute KPI server-side
    kpi = compute_kpi(azienda, ul_id=ul_id, mese=mese_default)
    movs = get_movimentazioni(azienda, ul_id=ul_id, mese=mese_default)

    return render(request, 'dashboard.html', {
        'azienda': azienda,
        'unita_locali': unita_locali,
        'mesi': mesi_str,
        'mese_attivo': mese_default,
        'ul_attivo': ul_id,
        'kpi': kpi,
        'movs': movs,
    })


@login_required
def dashboard_partial(request):
    """
    HTMX partial — returns only the dashboard content div.
    Called when UL filter or mese changes.
    """
    azienda = get_azienda_or_redirect(request)
    if not azienda:
        return HttpResponse(status=403)

    mese = request.GET.get('mese', '')
    ul_id = str(request.GET.get('ul', ''))

    kpi = compute_kpi(azienda, ul_id=ul_id, mese=mese)
    movs = get_movimentazioni(azienda, ul_id=ul_id, mese=mese)

    return render(request, 'partials/dashboard_content.html', {
        'kpi': kpi,
        'movs': movs,
        'mese_attivo': mese,
        'ul_attivo': ul_id,
    })


def compute_kpi(azienda, ul_id=None, mese=None):
    qs = _base_qs(azienda, ul_id, mese)
    non_peric = qs.filter(pericoloso=False)

    agg = non_peric.aggregate(
        gha_s1=Sum('s1_gha'),
        gha_s2=Sum('s2_gha'),
        gha_s=Sum('s_gha'),
        gha_terreno=Sum('gha_terreno'),
        gha_netto=Sum('gha_netto'),
    )
    trasporto = qs.aggregate(
        t1=Sum('t1_co2'),
        t2=Sum('t2_co2'),
        co2_trasporto=Sum('co2_trasporto'),
        kg=Sum('quantita_kg'),
    )
    counts = qs.aggregate(
        n_tot=Count('id'),
        n_peric=Count('id', filter=Q(pericoloso=True)),
    )

    s1 = agg['gha_s1'] or 0.0
    s2 = agg['gha_s2'] or 0.0
    s = agg['gha_s'] or 0.0
    gha_processo = s1 - s2 - s

    # Time series for charts
    by_date = defaultdict(lambda: {'co2_trasporto': 0.0, 'gha_processo': 0.0, 'gha_terreno': 0.0})
    for row in qs.values('giro__data', 'pericoloso', 's1_gha', 's2_gha', 's_gha', 'gha_terreno', 'co2_trasporto'):
        d = str(row['giro__data'])
        by_date[d]['co2_trasporto'] += row['co2_trasporto'] or 0.0
        if not row['pericoloso']:
            by_date[d]['gha_processo'] += (row['s1_gha'] or 0) - (row['s2_gha'] or 0) - (row['s_gha'] or 0)
            by_date[d]['gha_terreno'] += row['gha_terreno'] or 0.0

    serie = [{'data': d, **v} for d, v in sorted(by_date.items())]

    t1 = trasporto['t1'] or 0.0
    t2 = trasporto['t2'] or 0.0

    return {
        'gha_processo': round(gha_processo, 6),
        'gha_s1': round(s1, 6),
        'gha_s2': round(s2, 6),
        'gha_s': round(s, 6),
        'gha_s1_abs': round(abs(s1), 6),
        'gha_s2_abs': round(abs(s2), 6),
        'gha_s_abs':  round(abs(s), 6),
        'gha_processo_abs': round(abs(s1 - s2 - s), 6),
        'gha_max_p':  round(max(
            abs(s1) if s1 else 0,
            abs(s2) if s2 else 0,
            abs(s) if s else 0,
            0.0001
        ), 6),
        'gha_max_t':  round(max(abs(t1), abs(t2), 0.0001), 6),
        'gha_terreno': round(agg['gha_terreno'] or 0.0, 6),
        'gha_netto': round(agg['gha_netto'] or 0.0, 6),
        'co2_trasporto': round(trasporto['co2_trasporto'] or 0.0, 4),
        't1': round(t1, 4),
        't2': round(t2, 4),
        'kg': round(trasporto['kg'] or 0.0, 1),
        'n_mov': counts['n_tot'],
        'n_peric': counts['n_peric'],
        'serie': serie,
    }


def get_movimentazioni(azienda, ul_id=None, mese=None):
    qs = _base_qs(azienda, ul_id, mese)
    return list(
        qs.select_related('giro__veicolo', 'unita_locale', 'materiale')
        .order_by('giro__data', 'ora_ritiro')
        .values(
            'id', 'giro__data', 'unita_locale__indirizzo',
            'materiale__cer', 'materiale__nome', 'materiale__pericoloso',
            'n_formulario', 'quantita_kg', 'pericoloso',
            's1_gha', 's2_gha', 's_gha', 'gha_netto',
            't1_co2', 't2_co2', 'co2_trasporto',
        )
    )


def _base_qs(azienda, ul_id=None, mese=None):
    qs = Movimentazione.objects.filter(unita_locale__azienda=azienda)
    if ul_id:
        qs = qs.filter(unita_locale__id=ul_id)
    if mese:
        try:
            anno, m = mese.split('-')
            qs = qs.filter(giro__data__year=int(anno), giro__data__month=int(m))
        except (ValueError, AttributeError):
            pass
    return qs


@login_required
def tabella_veicoli(request):
    from core.models import Veicolo
    from pipeline.calc import logarithmic_curve_points
    veicoli = Veicolo.objects.all().order_by('targa')

    veicoli_data = []
    for v in veicoli:
        vdict = {
            'co2_km_vuoto_kg': v.co2_km_vuoto_kg,
            'co2_km_pieno_kg': v.co2_km_pieno_kg,
            'portata_kg': v.portata_kg,
        }
        pts = logarithmic_curve_points(vdict, n_points=50)
        b = (v.co2_km_pieno_kg - v.co2_km_vuoto_kg) / math.log(1 + v.portata_kg)
        veicoli_data.append({
            'obj': v,
            'curve_json': json.dumps({
                'x': [p['x'] for p in pts],
                'y': [p['y'] for p in pts],
            }),
            'b': round(b, 6),
        })

    return render(request, 'tabelle/veicoli.html', {
        'veicoli_data': veicoli_data,
    })


@login_required
def tabella_materiali(request):
    from core.models import Materiale
    GHA_FACTOR = 1800.0

    materiali = Materiale.objects.all().order_by('cer')

    def to_gha_t(val):
        if val is None:
            return None
        return round(val / GHA_FACTOR * 1000, 4)

    materiali_data = []
    for m in materiali:
        materiali_data.append({
            'obj': m,
            'tv_gha': to_gha_t(m.t_verg),
            'ts_gha': to_gha_t(m.t_smalt),
            'tt_gha': to_gha_t(m.t_tratt),
            'tr_gha': to_gha_t(m.t_ric),
        })

    return render(request, 'tabelle/materiali.html', {
        'materiali_data': materiali_data,
    })


@login_required
def movimentazione_detail(request, pk):
    azienda = get_azienda_or_redirect(request)
    if not azienda:
        return redirect('/admin/')

    mov = get_object_or_404(
        Movimentazione,
        pk=pk,
        unita_locale__azienda=azienda,
    )

    veicolo = mov.giro.veicolo
    materiale = mov.materiale

    from pipeline.calc import logarithmic_curve_points, co2_per_km
    veicolo_dict = {
        'co2_km_vuoto_kg': veicolo.co2_km_vuoto_kg,
        'co2_km_pieno_kg': veicolo.co2_km_pieno_kg,
        'portata_kg': veicolo.portata_kg,
    }
    curve_points = logarithmic_curve_points(veicolo_dict, n_points=200)

    carico_giro_kg = mov.giro.movimentazioni.aggregate(
        total=Sum('quantita_kg')
    )['total'] or 0.0

    co2_at_load = co2_per_km(veicolo_dict, carico_giro_kg)

    b = (veicolo.co2_km_pieno_kg - veicolo.co2_km_vuoto_kg) / math.log(1 + veicolo.portata_kg)

    curve_json = json.dumps({
        'x': [p['x'] for p in curve_points],
        'y': [p['y'] for p in curve_points],
        'carico_kg': round(carico_giro_kg, 1),
        'co2_at_load': round(co2_at_load, 5),
        'co2_vuoto': veicolo.co2_km_vuoto_kg,
        'co2_pieno': veicolo.co2_km_pieno_kg,
        'portata_kg': veicolo.portata_kg,
        'b': round(b, 6),
    })

    return render(request, 'movimentazione_detail.html', {
        'mov': mov,
        'veicolo': veicolo,
        'materiale': materiale,
        'giro': mov.giro,
        'curve_json': curve_json,
        'carico_giro_kg': round(carico_giro_kg, 1),
        'co2_at_load': round(co2_at_load, 5),
        'b': round(b, 6),
    })
