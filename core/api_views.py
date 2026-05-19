from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404
from collections import defaultdict

from .models import Azienda, UnitaLocale, Veicolo, Materiale, Giro, Movimentazione
from .serializers import (
    MovimentazioneListSerializer, MovimentazioneDetailSerializer,
    VeicoloSerializer, MaterialeSerializer,
)


def get_azienda(user):
    """Returns the Azienda linked to the logged-in user."""
    return get_object_or_404(Azienda, user=user)


def filter_movimentazioni(user, ul_id=None, mese=None):
    """
    Returns queryset of Movimentazione filtered by:
    - user's azienda (always)
    - ul_id (optional)
    - mese as 'YYYY-MM' string (optional)
    """
    az = get_azienda(user)
    qs = Movimentazione.objects.filter(
        unita_locale__azienda=az
    ).select_related(
        'giro__veicolo', 'unita_locale', 'materiale'
    )

    if ul_id:
        qs = qs.filter(unita_locale__id=ul_id)

    if mese:
        try:
            anno, m = mese.split('-')
            qs = qs.filter(giro__data__year=int(anno), giro__data__month=int(m))
        except (ValueError, AttributeError):
            pass

    return qs.order_by('giro__data', 'ora_ritiro')


class MovimentazioniListAPI(APIView):
    """
    GET /api/movimentazioni/
    Query params: ?ul=<id>&mese=YYYY-MM
    Returns list of movimentazioni for the logged-in user's azienda.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ul_id = request.query_params.get('ul')
        mese = request.query_params.get('mese')
        qs = filter_movimentazioni(request.user, ul_id=ul_id, mese=mese)
        serializer = MovimentazioneListSerializer(qs, many=True)
        return Response(serializer.data)


class MovimentazioneDetailAPI(APIView):
    """
    GET /api/movimentazioni/<id>/
    Returns full detail including logarithmic curve data.
    User must own the record.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        az = get_azienda(request.user)
        mov = get_object_or_404(
            Movimentazione,
            pk=pk,
            unita_locale__azienda=az,
        )
        serializer = MovimentazioneDetailSerializer(mov)
        return Response(serializer.data)


class GiroDetailAPI(APIView):
    """
    GET /api/giri/<id>/
    Returns giro detail. User must have at least one movimentazione in this giro.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        az = get_azienda(request.user)
        has_access = Movimentazione.objects.filter(
            giro__id=pk,
            unita_locale__azienda=az,
        ).exists()
        if not has_access:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        giro = get_object_or_404(Giro, pk=pk)
        from .serializers import GiroSerializer
        return Response(GiroSerializer(giro).data)


class VeicoliListAPI(APIView):
    """
    GET /api/veicoli/
    Public endpoint — no auth required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Veicolo.objects.all().order_by('targa')
        return Response(VeicoloSerializer(qs, many=True).data)


class MaterialiListAPI(APIView):
    """
    GET /api/materiali/
    Public endpoint — no auth required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Materiale.objects.all().order_by('cer')
        return Response(MaterialeSerializer(qs, many=True).data)


class KPIAPI(APIView):
    """
    GET /api/kpi/
    Query params: ?ul=<id>&mese=YYYY-MM
    Returns aggregated KPIs + time series for the logged-in user's azienda.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ul_id = request.query_params.get('ul')
        mese = request.query_params.get('mese')
        qs = filter_movimentazioni(request.user, ul_id=ul_id, mese=mese)

        # Aggregate — exclude pericolosi from ecological metrics
        non_peric = qs.filter(pericoloso=False)

        agg = non_peric.aggregate(
            gha_processo_s1=Sum('s1_gha'),
            gha_processo_s2=Sum('s2_gha'),
            gha_processo_s=Sum('s_gha'),
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

        gha_processo = (
            (agg['gha_processo_s1'] or 0.0) -
            (agg['gha_processo_s2'] or 0.0) -
            (agg['gha_processo_s'] or 0.0)
        )

        # Time series: group by date
        by_date = defaultdict(lambda: {
            'gha_processo': 0.0,
            'gha_terreno': 0.0,
            'co2_trasporto': 0.0,
        })

        for mov in qs.values(
            'giro__data', 'pericoloso',
            's1_gha', 's2_gha', 's_gha', 'gha_terreno', 'co2_trasporto'
        ):
            d = str(mov['giro__data'])
            by_date[d]['co2_trasporto'] += mov['co2_trasporto'] or 0.0
            if not mov['pericoloso']:
                by_date[d]['gha_processo'] += (
                    (mov['s1_gha'] or 0.0) -
                    (mov['s2_gha'] or 0.0) -
                    (mov['s_gha'] or 0.0)
                )
                by_date[d]['gha_terreno'] += mov['gha_terreno'] or 0.0

        serie = [
            {
                'data': d,
                'gha_processo': round(v['gha_processo'], 6),
                'gha_terreno': round(v['gha_terreno'], 6),
                'co2_trasporto': round(v['co2_trasporto'], 4),
            }
            for d, v in sorted(by_date.items())
        ]

        # UL list for filter buttons
        az = get_azienda(request.user)
        ul_list = list(
            UnitaLocale.objects.filter(azienda=az).values('id', 'indirizzo', 'citta')
        )

        # Available months
        mesi = list(
            Movimentazione.objects.filter(unita_locale__azienda=az)
            .values_list('giro__data__year', 'giro__data__month')
            .distinct()
            .order_by('giro__data__year', 'giro__data__month')
        )
        mesi_str = [f"{y:04d}-{m:02d}" for y, m in mesi]

        return Response({
            'gha_processo': round(gha_processo, 6),
            'gha_s1': round(agg['gha_processo_s1'] or 0.0, 6),
            'gha_s2': round(agg['gha_processo_s2'] or 0.0, 6),
            'gha_s': round(agg['gha_processo_s'] or 0.0, 6),
            'gha_terreno': round(agg['gha_terreno'] or 0.0, 6),
            'gha_netto': round(agg['gha_netto'] or 0.0, 6),
            'co2_trasporto': round(trasporto['co2_trasporto'] or 0.0, 4),
            't1_totale': round(trasporto['t1'] or 0.0, 4),
            't2_totale': round(trasporto['t2'] or 0.0, 4),
            'kg_totale': round(trasporto['kg'] or 0.0, 1),
            'n_movimentazioni': counts['n_tot'],
            'n_pericolosi': counts['n_peric'],
            'serie_temporale': serie,
            'unita_locali': ul_list,
            'mesi_disponibili': mesi_str,
        })
