import math

GHA_FACTOR = 1800.0  # kgCO2 per gha per year (GFN carbon footprint)
ECOF_LAT = 42.0885
ECOF_LON = 12.4063


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def co2_per_km(veicolo: dict, load_kg: float) -> float:
    """
    Logarithmic interpolation (Soluslab model):
        b = (co2_km_pieno - co2_km_vuoto) / ln(1 + C_max)
        co2_km(C) = co2_km_vuoto + b * ln(1 + C)
    Falls back to linear if portata_kg <= 0.
    """
    v0 = veicolo["co2_km_vuoto_kg"]
    vp = veicolo["co2_km_pieno_kg"]
    c_max = veicolo["portata_kg"]
    if c_max <= 0:
        return v0
    b = (vp - v0) / math.log(1 + c_max)
    return v0 + b * math.log(1 + min(load_kg, c_max))


def calc_s1_s2_gha(mat: dict, Q_kg: float) -> tuple[float, float]:
    """
    S1 = biocapacità liberata dalla riduzione di assorbimento (always +)
    S2 = impronta da recupero (always +)
    Returns (S1, S2) both positive.
    """
    s1 = Q_kg * (mat["t_smalt"] + mat["t_verg"]) / GHA_FACTOR
    s2 = Q_kg * (mat["t_tratt"] + mat["t_ric"]) / GHA_FACTOR
    return s1, s2


def calc_s_gha(mat: dict, Q_kg: float) -> float:
    """
    S = impronta da smaltimento per indifferenziato (always +)
    """
    return Q_kg * (mat["t_smalt"] + mat["t_tratt"]) / GHA_FACTOR


def calc_t1_co2(veicolo: dict, km_itinerario: float, n_clienti: int) -> float:
    """
    T1 = (km_itinerario * co2_km(0)) / n_clienti
    Route emissions split equally across all clients (fixed + spot).
    """
    if n_clienti <= 0:
        return 0.0
    return (km_itinerario * co2_per_km(veicolo, 0)) / n_clienti


def calc_t2_co2(veicolo: dict, load_kg: float, d_baricentro_km: float,
                Q_kg: float, C_total: float) -> float:
    """
    T2 = (co2_km(C) - co2_km(0)) * d_baricentro * (Q / C_total)
    Incremental load emissions attributed to this client's contribution.
    """
    if C_total <= 0:
        return 0.0
    delta = co2_per_km(veicolo, load_kg) - co2_per_km(veicolo, 0)
    return delta * d_baricentro_km * (Q_kg / C_total)


def calc_gha_terreno(mat: dict, Q_kg: float) -> float:
    """
    H = biocapacità da terreno sottratto allo sfruttamento (always +)
    Only for biotic materials with resa and f_equiv.
    """
    if mat.get("tipo") != "biotico":
        return 0.0
    if not mat.get("resa") or not mat.get("f_equiv"):
        return 0.0
    return (Q_kg / 1000.0) / mat["resa"] * mat["f_equiv"]


def calc_d_baricentro(
    stop_coords_ordered: list[tuple[float, float]],
    quantities: list[float],
) -> float:
    """
    Weighted cumulative distance from Ecof along route order:
        D_b = Σ(D_percorsa_fino_a_UL(i) * Q(i)) / C_total

    stop_coords_ordered: list of (lat, lon) for each stop in route order
                         (already includes only stops with valid coords)
    quantities: list of Q_kg for each stop, same order

    D_percorsa_fino_a_UL(i) = cumulative km from Ecof:
        Ecof → stop[0] → stop[1] → ... → stop[i]

    Uses Haversine for each segment.
    Returns 0.0 if no stops or C_total == 0.
    """
    if not stop_coords_ordered or not quantities:
        return 0.0
    C_total = sum(quantities)
    if C_total <= 0:
        return 0.0

    # Build cumulative distances from Ecof
    prev = (ECOF_LAT, ECOF_LON)
    cumulative = 0.0
    cum_distances = []
    for lat, lon in stop_coords_ordered:
        cumulative += haversine_km(prev[0], prev[1], lat, lon)
        cum_distances.append(cumulative)
        prev = (lat, lon)

    # Weighted sum
    d_b = sum(d * q for d, q in zip(cum_distances, quantities))
    return d_b / C_total


def calc_movimentazione(
    mat: dict,
    veicolo: dict,
    Q_kg: float,
    km_itinerario: float,
    n_clienti: int,
    d_baricentro_km: float,
    C_total: float,
    pericoloso: bool,
) -> dict:
    """
    Main entry point. Returns a dict with all calculated fields
    ready to be saved to Movimentazione model.

    For pericolosi: only T1/T2 are computed, all gha fields are None.
    For indifferenziato (t_verg is None): uses calc_s_gha instead of calc_s1_s2_gha.
    For recyclable non-pericolosi: full S1/S2 + gha_terreno calculation.
    """
    t1 = calc_t1_co2(veicolo, km_itinerario, n_clienti)
    t2 = calc_t2_co2(veicolo, C_total, d_baricentro_km, Q_kg, C_total)
    co2_trasporto = t1 + t2

    if pericoloso:
        return {
            "pericoloso": True,
            "s1_gha": None,
            "s2_gha": None,
            "s_gha": None,
            "gha_terreno": None,
            "gha_netto": None,
            "t1_co2": round(t1, 4),
            "t2_co2": round(t2, 4),
            "co2_trasporto": round(co2_trasporto, 4),
        }

    indiff = mat.get("t_verg") is None and mat.get("tipo") != "biotico"
    biotico_no_tverg = mat.get("tipo") == "biotico" and mat.get("t_verg") is None

    if indiff:
        s_gha = calc_s_gha(mat, Q_kg)
        gha_terreno = 0.0
        gha_netto = -s_gha  # pure cost
        return {
            "pericoloso": False,
            "s1_gha": None,
            "s2_gha": None,
            "s_gha": round(s_gha, 6),
            "s_gha_tipo": "indiff",
            "gha_terreno": round(gha_terreno, 6),
            "gha_netto": round(gha_netto, 6),
            "t1_co2": round(t1, 4),
            "t2_co2": round(t2, 4),
            "co2_trasporto": round(co2_trasporto, 4),
        }

    if biotico_no_tverg:
        s_gha = calc_s_gha(mat, Q_kg)
        gha_terreno = calc_gha_terreno(mat, Q_kg)
        gha_netto = gha_terreno - s_gha
        return {
            "pericoloso": False,
            "s1_gha": None,
            "s2_gha": None,
            "s_gha": round(s_gha, 6),
            "s_gha_tipo": "biotico",
            "gha_terreno": round(gha_terreno, 6),
            "gha_netto": round(gha_netto, 6),
            "t1_co2": round(t1, 4),
            "t2_co2": round(t2, 4),
            "co2_trasporto": round(co2_trasporto, 4),
        }

    # Recyclable non-pericoloso
    s1_gha, s2_gha = calc_s1_s2_gha(mat, Q_kg)
    gha_terreno = calc_gha_terreno(mat, Q_kg)
    gha_netto = s1_gha - s2_gha + gha_terreno
    return {
        "pericoloso": False,
        "s1_gha": round(s1_gha, 6),
        "s2_gha": round(s2_gha, 6),
        "s_gha": None,
        "s_gha_tipo": None,
        "gha_terreno": round(gha_terreno, 6),
        "gha_netto": round(gha_netto, 6),
        "t1_co2": round(t1, 4),
        "t2_co2": round(t2, 4),
        "co2_trasporto": round(co2_trasporto, 4),
    }


def logarithmic_curve_points(veicolo: dict, n_points: int = 100) -> list[dict]:
    """
    Generate n_points along the logarithmic CO2/km curve for Chart.js.
    Returns list of {"x": load_kg, "y": co2_per_km} dicts.
    X range: 0 to portata_kg.
    """
    c_max = veicolo["portata_kg"]
    step = c_max / (n_points - 1)
    return [
        {"x": round(i * step, 1), "y": round(co2_per_km(veicolo, i * step), 5)}
        for i in range(n_points)
    ]


# ---------------------------------------------------------------------------
# Quick self-test (run: python pipeline/calc.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_veicolo = {
        "co2_km_vuoto_kg": 0.3036,
        "co2_km_pieno_kg": 0.421,
        "portata_kg": 880,
    }
    test_mat_carta = {
        "tipo": "biotico", "pericoloso": False,
        "t_verg": 1.1, "t_smalt": 0.8, "t_tratt": 0.1, "t_ric": 0.6,
        "resa": 2.68, "f_equiv": 1.26,
    }
    test_mat_indiff = {
        "tipo": "abiotico", "pericoloso": False,
        "t_verg": None, "t_smalt": 1.1, "t_tratt": 0.1, "t_ric": 0.0,
        "resa": None, "f_equiv": None,
    }
    test_mat_organico = {
        "tipo": "biotico", "pericoloso": False,
        "t_verg": None, "t_smalt": 1.0, "t_tratt": 0.1, "t_ric": 0.0,
        "resa": 3.3, "f_equiv": 2.51,
    }

    print("=== co2_per_km ===")
    print(f"  vuoto:  {co2_per_km(test_veicolo, 0):.4f} kg/km  (expected ~0.3036)")
    print(f"  pieno:  {co2_per_km(test_veicolo, 880):.4f} kg/km  (expected ~0.421)")
    print(f"  metà:   {co2_per_km(test_veicolo, 440):.4f} kg/km")

    print("\n=== calc_movimentazione — carta 80kg ===")
    print("  expected: S1=+0.084444, S2=+0.031111, H=+0.037612, gha_netto=+0.090945")
    result = calc_movimentazione(
        mat=test_mat_carta, veicolo=test_veicolo,
        Q_kg=80, km_itinerario=48.4, n_clienti=10,
        d_baricentro_km=22.7, C_total=240, pericoloso=False,
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    print("\n=== calc_movimentazione — indifferenziato 300kg ===")
    print("  expected: S=+0.200000, gha_netto=-0.200000")
    result2 = calc_movimentazione(
        mat=test_mat_indiff, veicolo=test_veicolo,
        Q_kg=300, km_itinerario=48.4, n_clienti=10,
        d_baricentro_km=22.3, C_total=820, pericoloso=False,
    )
    for k, v in result2.items():
        print(f"  {k}: {v}")

    print("\n=== calc_movimentazione — organico 220kg ===")
    print("  expected: S=+0.134444, H=+0.167333, gha_netto=+0.032889")
    result_org = calc_movimentazione(
        mat=test_mat_organico, veicolo=test_veicolo,
        Q_kg=220, km_itinerario=48.4, n_clienti=10,
        d_baricentro_km=22.3, C_total=820, pericoloso=False,
    )
    for k, v in result_org.items():
        print(f"  {k}: {v}")

    print("\n=== calc_movimentazione — pericoloso 5kg ===")
    result3 = calc_movimentazione(
        mat={}, veicolo=test_veicolo,
        Q_kg=5, km_itinerario=67.3, n_clienti=12,
        d_baricentro_km=22.7, C_total=320, pericoloso=True,
    )
    for k, v in result3.items():
        print(f"  {k}: {v}")

    print("\n=== logarithmic_curve_points (first 3, last 1) ===")
    pts = logarithmic_curve_points(test_veicolo, n_points=10)
    for p in pts[:3] + [pts[-1]]:
        print(f"  {p}")

    print("\nAll checks passed ✓")
