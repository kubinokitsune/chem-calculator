"""
Stress tests for:
  A. gas laws with units (atm / kPa / Pa / bar / mmHg, L / dm3 / mL / cm3 / m3, K / °C)
  B. ionic equation balancing (charges, electrons, acidic / basic media)
  C. limiting reactant (moles or grams, auto-balancing)
  D. the same features through the web API

Three kinds of check, so a wrong value can't slip through:
  * known answers worked by hand (textbook / IB values),
  * independent checks that don't reuse the code under test (closed-form
    combustion coefficients, atom + charge + mass conservation counted
    separately, SI round-trips),
  * randomised property checks (thousands of cases, fixed seed).

Only failures are printed.  Run:  py test_files/stress_new_features.py
"""

import sys, os, math, random, itertools, json
from fractions import Fraction
from functools import reduce

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

random.seed(20260917)
COUNTS = {}
FAILURES = []
_section = "?"


def section(name):
    global _section
    _section = name
    COUNTS[name] = [0, 0]
    print(f"\n=== {name} ===")


def record(label, ok, detail=""):
    COUNTS[_section][0 if ok else 1] += 1
    if not ok:
        msg = f"  [FAIL] {label}" + (f"\n         {detail}" if detail else "")
        FAILURES.append(msg)
        print(msg)


def close(label, got, want, rel=1e-9, abs_=0.0):
    ok = isinstance(got, (int, float)) and math.isclose(got, want, rel_tol=rel, abs_tol=abs_)
    record(label, ok, f"got={got!r} expected={want!r}")


def sig3(label, got, want):
    """Equal when both are rounded to 3 significant figures (IB precision)."""
    r = lambda x: 0.0 if x == 0 else round(x, -int(math.floor(math.log10(abs(x)))) + 2)
    record(label, isinstance(got, (int, float)) and r(got) == r(want), f"got={got!r} expected≈{want!r}")


def equal(label, got, want):
    record(label, got == want, f"got={got!r} expected={want!r}")


def raises(label, fn, exc=ValueError):
    try:
        fn()
    except exc:
        record(label, True)
    except Exception as e:
        record(label, False, f"raised {type(e).__name__}: {e} (expected {exc.__name__})")
    else:
        record(label, False, "no exception raised")


# ═════════════════════════════════════════════════════════════════════════════
# A. GAS LAWS WITH UNITS
# ═════════════════════════════════════════════════════════════════════════════
from gas_laws import (ideal_gas_solve, combined_gas_solve, gas_mixing_solve,
                      ideal_gas_find_P, ideal_gas_find_V, ideal_gas_find_n, ideal_gas_find_T,
                      PRESSURE_UNITS, VOLUME_UNITS)

R = 8.314
# Independent unit table (written out again on purpose, not imported)
P_FACTOR = {"atm": 101325.0, "kPa": 1e3, "Pa": 1.0, "bar": 1e5, "mmHg": 101325.0 / 760, "torr": 101325.0 / 760}
V_FACTOR = {"L": 1e-3, "dm3": 1e-3, "mL": 1e-6, "cm3": 1e-6, "m3": 1.0}

section("A1 gas laws: hand-worked answers")
sig3("0.0100 mol, 25.0 °C, 250 cm³ -> P (kPa)",
     ideal_gas_solve("P", V=250, n=0.0100, T=25.0, P_unit="kPa", V_unit="cm3", T_unit="C"), 99.2)
sig3("1.00 mol, 273.15 K, 100 kPa -> V (dm³)",
     ideal_gas_solve("V", P=100, n=1.00, T=273.15, P_unit="kPa", V_unit="dm3"), 22.7)
sig3("0.500 mol, 100 kPa, 300 K -> V (m³)",
     ideal_gas_solve("V", P=100, n=0.500, T=300, P_unit="kPa", V_unit="m3"), 0.0125)
sig3("100 000 Pa, 0.0227 m³, 1 mol -> T (K)",
     ideal_gas_solve("T", P=100000, V=0.0227, n=1, P_unit="Pa", V_unit="m3"), 273.)
sig3("101.325 kPa, 24.47 dm³, 25 °C -> n",
     ideal_gas_solve("n", P=101.325, V=24.47, T=25, P_unit="kPa", V_unit="dm3", T_unit="C"), 1.00)
sig3("760 mmHg, 22.41 L, 1 mol -> T (°C)",
     ideal_gas_solve("T", P=760, V=22.41, n=1, P_unit="mmHg", V_unit="L", T_unit="C"), -0.0332)
sig3("1 bar, 1 m³, 300 K -> n",
     ideal_gas_solve("n", P=1, V=1, T=300, P_unit="bar", V_unit="m3"), 40.1)
close("760 mmHg is 1 atm",
      ideal_gas_solve("P", V=1, n=1, T=300, P_unit="mmHg") / 760,
      ideal_gas_solve("P", V=1, n=1, T=300, P_unit="atm"), rel=1e-12)
sig3("combined: 100 kPa, 2.00 dm³, 27 °C -> 150 kPa, 127 °C: V2",
     combined_gas_solve("V2", P1=100, V1=2.00, T1=27, P2=150, T2=127, P_unit="kPa", V_unit="dm3", T_unit="C"), 1.78)
sig3("combined: T doubles in K when P doubles at fixed V (0 °C -> ? °C)",
     combined_gas_solve("T2", P1=1, V1=1, T1=0, P2=2, V2=1, T_unit="C"), 273.)
sig3("combined: P2 when V halves at constant T (kPa)",
     combined_gas_solve("P2", P1=120, V1=500, T1=293, V2=250, T2=293, P_unit="kPa", V_unit="cm3"), 240.)
res, n1, n2 = gas_mixing_solve("Pf", 100, 1.0, 25, 200, 2.0, 25, Vf=3.0, Tf=25,
                               P_unit="kPa", V_unit="dm3", T_unit="C")
sig3("mixing: 1 dm³ @100 kPa + 2 dm³ @200 kPa into 3 dm³ -> P (kPa)", res, 167.)
record("°C mistake guard: combined law with °C differs from treating °C as K",
       abs(combined_gas_solve("V2", P1=1, V1=1, T1=20, P2=1, T2=40, T_unit="C") - 2.0) > 0.5)

section("A2 gas laws: SI round-trip, every unit combination")
cases = 0
for _ in range(60):
    P_si = 10 ** random.uniform(2, 7)          # 100 Pa .. 10 MPa
    V_si = 10 ** random.uniform(-7, 1)         # 0.1 cm³ .. 10 m³
    T_K = random.uniform(5, 3000)
    n_true = P_si * V_si / (R * T_K)
    for pu, vu, tu in itertools.product(P_FACTOR, V_FACTOR, ("K", "C")):
        P = P_si / P_FACTOR[pu]
        V = V_si / V_FACTOR[vu]
        T = T_K - 273.15 if tu == "C" else T_K
        kw = dict(P_unit=pu, V_unit=vu, T_unit=tu)
        close(f"P [{pu},{vu},{tu}]", ideal_gas_solve("P", V=V, n=n_true, T=T, **kw), P, rel=1e-9)
        close(f"V [{pu},{vu},{tu}]", ideal_gas_solve("V", P=P, n=n_true, T=T, **kw), V, rel=1e-9)
        close(f"n [{pu},{vu},{tu}]", ideal_gas_solve("n", P=P, V=V, T=T, **kw), n_true, rel=1e-9)
        close(f"T [{pu},{vu},{tu}]", ideal_gas_solve("T", P=P, V=V, n=n_true, **kw), T, rel=1e-9, abs_=1e-9)
        cases += 4

section("A3 gas laws: agree with the original atm/L functions")
for _ in range(300):
    n, V, T, P = random.uniform(0.01, 50), random.uniform(0.01, 500), random.uniform(50, 2000), random.uniform(0.01, 200)
    close("P atm", ideal_gas_solve("P", V=V, n=n, T=T), ideal_gas_find_P(n, V, T), rel=1e-4)
    close("V L", ideal_gas_solve("V", P=P, n=n, T=T), ideal_gas_find_V(n, T, P), rel=1e-4)
    close("n", ideal_gas_solve("n", P=P, V=V, T=T), ideal_gas_find_n(P, V, T), rel=1e-4)
    close("T K", ideal_gas_solve("T", P=P, V=V, n=n), ideal_gas_find_T(P, V, n), rel=1e-4)

section("A4 combined + mixing laws: random states in random units")
for _ in range(400):
    k = random.uniform(0.01, 1000)                   # PV/T in SI
    s = {}
    for i in "12":
        T_K = random.uniform(10, 2000)
        P_si = 10 ** random.uniform(2, 7)
        s["T" + i], s["P" + i], s["V" + i] = T_K, P_si, k * T_K / P_si
    pu, vu, tu = random.choice(list(P_FACTOR)), random.choice(list(V_FACTOR)), random.choice(("K", "C"))
    shown = {x: (s[x] / P_FACTOR[pu] if x[0] == "P" else s[x] / V_FACTOR[vu] if x[0] == "V"
                 else s[x] - 273.15 if tu == "C" else s[x]) for x in s}
    for target in shown:
        given = {x: v for x, v in shown.items() if x != target}
        got = combined_gas_solve(target, P_unit=pu, V_unit=vu, T_unit=tu, **given)
        close(f"combined {target} [{pu},{vu},{tu}]", got, shown[target], rel=1e-9, abs_=1e-9)
    # mixing: result must equal PV = (n1 + n2) R T for the final state
    Vf = random.uniform(0.1, 10) / V_FACTOR[vu] * 1e-3
    Tf = random.uniform(200, 600)
    Tf_shown = Tf - 273.15 if tu == "C" else Tf
    n1 = shown["P1"] * P_FACTOR[pu] * shown["V1"] * V_FACTOR[vu] / (R * s["T1"])
    n2 = shown["P2"] * P_FACTOR[pu] * shown["V2"] * V_FACTOR[vu] / (R * s["T2"])
    Pf, g1, g2 = gas_mixing_solve("Pf", shown["P1"], shown["V1"], shown["T1"], shown["P2"], shown["V2"],
                                  shown["T2"], Vf=Vf, Tf=Tf_shown, P_unit=pu, V_unit=vu, T_unit=tu)
    close("mixing n1", g1, n1, rel=1e-9)
    close("mixing n2", g2, n2, rel=1e-9)
    close("mixing Pf", Pf, (n1 + n2) * R * Tf / (Vf * V_FACTOR[vu]) / P_FACTOR[pu], rel=1e-9)

section("A5 gas laws: bad input is rejected")
raises("P = 0", lambda: ideal_gas_solve("V", P=0, n=1, T=300))
raises("negative V", lambda: ideal_gas_solve("P", V=-1, n=1, T=300))
raises("n = 0", lambda: ideal_gas_solve("P", V=1, n=0, T=300))
raises("T = 0 K", lambda: ideal_gas_solve("P", V=1, n=1, T=0))
raises("T = -300 °C (below absolute zero)", lambda: ideal_gas_solve("P", V=1, n=1, T=-300, T_unit="C"))
raises("T = -273.15 °C exactly", lambda: ideal_gas_solve("P", V=1, n=1, T=-273.15, T_unit="C"))
raises("unknown pressure unit", lambda: ideal_gas_solve("V", P=1, n=1, T=300, P_unit="psi"))
raises("unknown volume unit", lambda: ideal_gas_solve("P", V=1, n=1, T=300, V_unit="gal"))
raises("unknown temperature unit", lambda: ideal_gas_solve("P", V=1, n=1, T=300, T_unit="F"))
raises("missing value", lambda: ideal_gas_solve("P", V=1, T=300))
raises("missing T", lambda: ideal_gas_solve("P", V=1, n=1))
raises("NaN input", lambda: ideal_gas_solve("P", V=float("nan"), n=1, T=300))
raises("infinite input", lambda: ideal_gas_solve("P", V=float("inf"), n=1, T=300))
raises("bad solve target", lambda: ideal_gas_solve("Q", P=1, V=1, n=1, T=1))
raises("combined: missing T1", lambda: combined_gas_solve("V2", P1=1, V1=1, P2=1, T2=300))
raises("combined: T2 below absolute zero", lambda: combined_gas_solve("V2", P1=1, V1=1, T1=300, P2=1, T2=-5))
raises("mixing: bad target", lambda: gas_mixing_solve("nf", 1, 1, 300, 1, 1, 300, Vf=1, Tf=300))
for alias, unit in [("KPA", "kPa"), ("dm^3", "dm3"), ("cm³", "cm3"), ("°C", "C"), (" l ", "L")]:
    try:
        if unit in ("kPa",):
            ideal_gas_solve("V", P=1, n=1, T=300, P_unit=alias)
        elif unit == "C":
            ideal_gas_solve("P", V=1, n=1, T=300, T_unit=alias)
        else:
            ideal_gas_solve("P", V=1, n=1, T=300, V_unit=alias)
        record(f"unit alias '{alias}' accepted", True)
    except ValueError as e:
        record(f"unit alias '{alias}' accepted", False, str(e))


# ═════════════════════════════════════════════════════════════════════════════
# B. ION / EQUATION BALANCER
# ═════════════════════════════════════════════════════════════════════════════
from equation_balancer import balance_full, balance_equation, parse_equation, parse_species
from percent_composition_calculator import parse_formula


def coeffs_of(text, medium=None):
    res = balance_full(*parse_equation(text), medium)
    return ([(c, s.formula, s.charge) for c, s in res["reactants"]],
            [(c, s.formula, s.charge) for c, s in res["products"]])


def conserved(r_terms, p_terms):
    """Independent check: atoms and charge per side, positive, primitive."""
    def totals(terms):
        atoms, charge = {}, 0
        for c, formula, q in terms:
            if formula != "e":
                for el, k in parse_formula(formula).items():
                    atoms[el] = atoms.get(el, 0) + c * k
            charge += c * q
        return atoms, charge
    a1, q1 = totals(r_terms)
    a2, q2 = totals(p_terms)
    cs = [c for c, _, _ in r_terms + p_terms]
    return (a1 == a2 and q1 == q2 and all(isinstance(c, int) and c > 0 for c in cs)
            and reduce(math.gcd, cs) == 1)


section("B1 balancer: hand-checked ionic and redox equations")
KNOWN = [
    # (equation, medium, reactant terms, product terms)  — terms: (coeff, formula, charge)
    ("MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+", "acidic",
     [(1, "MnO4", -1), (5, "Fe", 2), (8, "H", 1)], [(1, "Mn", 2), (5, "Fe", 3), (4, "H2O", 0)]),
    ("Cr2O7^2- + Fe^2+ -> Cr^3+ + Fe^3+", "acidic",
     [(1, "Cr2O7", -2), (6, "Fe", 2), (14, "H", 1)], [(2, "Cr", 3), (6, "Fe", 3), (7, "H2O", 0)]),
    ("MnO4^- + C2O4^2- -> Mn^2+ + CO2", "acidic",
     [(2, "MnO4", -1), (5, "C2O4", -2), (16, "H", 1)], [(2, "Mn", 2), (10, "CO2", 0), (8, "H2O", 0)]),
    ("Cu + NO3^- -> Cu^2+ + NO", "acidic",
     [(3, "Cu", 0), (2, "NO3", -1), (8, "H", 1)], [(3, "Cu", 2), (2, "NO", 0), (4, "H2O", 0)]),
    ("MnO4^- + e- -> Mn^2+", "acidic",
     [(1, "MnO4", -1), (5, "e", -1), (8, "H", 1)], [(1, "Mn", 2), (4, "H2O", 0)]),
    ("Fe^2+ -> Fe^3+ + e-", None, [(1, "Fe", 2)], [(1, "Fe", 3), (1, "e", -1)]),
    ("Cl2 + e- -> Cl-", None, [(1, "Cl2", 0), (2, "e", -1)], [(2, "Cl", -1)]),
    ("MnO4^- + I^- -> MnO2 + I2", "basic",
     [(2, "MnO4", -1), (6, "I", -1), (4, "H2O", 0)], [(2, "MnO2", 0), (3, "I2", 0), (8, "OH", -1)]),
    ("Cr(OH)3 + ClO3^- -> CrO4^2- + Cl^-", "basic",
     [(2, "Cr(OH)3", 0), (1, "ClO3", -1), (4, "OH", -1)], [(2, "CrO4", -2), (1, "Cl", -1), (5, "H2O", 0)]),
    ("H2O2 + MnO4^- -> O2 + Mn^2+", "acidic",
     [(5, "H2O2", 0), (2, "MnO4", -1), (6, "H", 1)], [(5, "O2", 0), (2, "Mn", 2), (8, "H2O", 0)]),
    ("MnO4^- + H2O2 -> MnO2 + O2", "basic",
     [(2, "MnO4", -1), (3, "H2O2", 0)], [(2, "MnO2", 0), (3, "O2", 0), (2, "H2O", 0), (2, "OH", -1)]),
    ("H2O2 + Cr2O7^2- -> O2 + Cr^3+", "acidic",
     [(3, "H2O2", 0), (1, "Cr2O7", -2), (8, "H", 1)], [(3, "O2", 0), (2, "Cr", 3), (7, "H2O", 0)]),
    ("H2O2 + I^- -> I2 + H2O", "acidic",
     [(1, "H2O2", 0), (2, "I", -1), (2, "H", 1)], [(1, "I2", 0), (2, "H2O", 0)]),
    ("Ag^+ + Cu -> Ag + Cu^2+", None, [(2, "Ag", 1), (1, "Cu", 0)], [(2, "Ag", 0), (1, "Cu", 2)]),
    ("Zn + H^+ -> Zn^2+ + H2", None, [(1, "Zn", 0), (2, "H", 1)], [(1, "Zn", 2), (1, "H2", 0)]),
    ("Ba^2+ + SO4^2- -> BaSO4", None, [(1, "Ba", 2), (1, "SO4", -2)], [(1, "BaSO4", 0)]),
    ("S2O3^2- + I2 -> S4O6^2- + I^-", None, [(2, "S2O3", -2), (1, "I2", 0)], [(1, "S4O6", -2), (2, "I", -1)]),
    ("Fe^2+ + Ce^4+ -> Fe^3+ + Ce^3+", "acidic", [(1, "Fe", 2), (1, "Ce", 4)], [(1, "Fe", 3), (1, "Ce", 3)]),
    ("Al + Cu^2+ -> Al^3+ + Cu", None, [(2, "Al", 0), (3, "Cu", 2)], [(2, "Al", 3), (3, "Cu", 0)]),
    ("SO3^2- + MnO4^- -> SO4^2- + Mn^2+", "acidic",
     [(5, "SO3", -2), (2, "MnO4", -1), (6, "H", 1)], [(5, "SO4", -2), (2, "Mn", 2), (3, "H2O", 0)]),
    ("Zn + NO3^- -> Zn^2+ + NH4^+", "acidic",
     [(4, "Zn", 0), (1, "NO3", -1), (10, "H", 1)], [(4, "Zn", 2), (1, "NH4", 1), (3, "H2O", 0)]),
    ("Al + OH^- -> Al(OH)4^- + H2", "basic",
     [(2, "Al", 0), (2, "OH", -1), (6, "H2O", 0)], [(2, "Al(OH)4", -1), (3, "H2", 0)]),
    ("CH3OH + Cr2O7^2- -> HCOOH + Cr^3+", "acidic",
     [(3, "CH3OH", 0), (2, "Cr2O7", -2), (16, "H", 1)], [(3, "HCOOH", 0), (4, "Cr", 3), (11, "H2O", 0)]),
    ("H^+ + OH^- -> H2O", None, [(1, "H", 1), (1, "OH", -1)], [(1, "H2O", 0)]),
    ("CO3^2- + H^+ -> CO2 + H2O", None, [(1, "CO3", -2), (2, "H", 1)], [(1, "CO2", 0), (1, "H2O", 0)]),
    ("NH4^+ + OH^- -> NH3 + H2O", None, [(1, "NH4", 1), (1, "OH", -1)], [(1, "NH3", 0), (1, "H2O", 0)]),
]
for text, medium, want_r, want_p in KNOWN:
    try:
        got_r, got_p = coeffs_of(text, medium)
        # medium species may come out in either order; compare as sets
        equal(f"{text} [{medium}]", (sorted(got_r), sorted(got_p)), (sorted(want_r), sorted(want_p)))
        record(f"conserved: {text}", conserved(got_r, got_p))
    except Exception as e:
        record(f"{text} [{medium}]", False, f"{type(e).__name__}: {e}")
# hand-check the expected answers themselves, so a typo in KNOWN can't hide a bug
for text, medium, want_r, want_p in KNOWN:
    record(f"expected answer is itself balanced: {text}", conserved(want_r, want_p))

section("B2 balancer: hard molecular equations")
MOLECULAR = [
    (["KMnO4", "HCl"], ["KCl", "MnCl2", "H2O", "Cl2"], [2, 16], [2, 2, 8, 5]),
    (["K4Fe(CN)6", "KMnO4", "H2SO4"], ["KHSO4", "Fe2(SO4)3", "MnSO4", "HNO3", "CO2", "H2O"],
     [10, 122, 299], [162, 5, 122, 60, 60, 188]),
    (["C6H12O6", "O2"], ["CO2", "H2O"], [1, 6], [6, 6]),
    (["Fe2(SO4)3", "KOH"], ["K2SO4", "Fe(OH)3"], [1, 6], [3, 2]),
    (["Al", "H2SO4"], ["Al2(SO4)3", "H2"], [2, 3], [1, 3]),
    (["Ca3(PO4)2", "SiO2", "C"], ["CaSiO3", "P4", "CO"], [2, 6, 10], [6, 1, 10]),
    (["NH4NO3"], ["N2O", "H2O"], [1], [1, 2]),
    (["PbS", "O2"], ["PbO", "SO2"], [2, 3], [2, 2]),
    (["CuSO4*5H2O"], ["CuSO4", "H2O"], [1], [1, 5]),
    (["Cu", "HNO3"], ["Cu(NO3)2", "NO", "H2O"], [3, 8], [3, 2, 4]),
    (["P4O10", "H2O"], ["H3PO4"], [1, 6], [4]),
    (["C3H5(NO3)3"], ["CO2", "H2O", "N2", "O2"], [4], [12, 10, 6, 1]),
]
for r, p, wr, wp in MOLECULAR:
    try:
        got = balance_equation(r, p)
        equal(f"{' + '.join(r)} -> {' + '.join(p)}", got, (wr, wp))
        record(f"conserved: {' + '.join(r)}",
               conserved([(c, f, 0) for c, f in zip(got[0], r)], [(c, f, 0) for c, f in zip(got[1], p)]))
    except Exception as e:
        record(f"{' + '.join(r)} -> {' + '.join(p)}", False, f"{type(e).__name__}: {e}")
for r, p, wr, wp in MOLECULAR:
    record(f"expected answer is itself balanced: {' + '.join(r)}",
           conserved([(c, f, 0) for c, f in zip(wr, r)], [(c, f, 0) for c, f in zip(wp, p)]))

section("B3 balancer: closed-form combustion CxHyOz (independent formula)")
for x in range(1, 13):
    for y in range(2, 2 * x + 3, 2):
        for z in range(0, 4):
            f = f"C{x}H{y}" + (f"O{z}" if z else "")
            o2 = Fraction(x) + Fraction(y, 4) - Fraction(z, 2)
            if o2 <= 0:
                continue
            raw = [Fraction(1), o2, Fraction(x), Fraction(y, 2)]
            L = reduce(lambda a, b: a * b // math.gcd(a, b), (v.denominator for v in raw))
            ints = [int(v * L) for v in raw]
            g = reduce(math.gcd, ints)
            ints = [v // g for v in ints]
            try:
                got = balance_equation([f, "O2"], ["CO2", "H2O"])
                equal(f"combustion {f}", list(got[0]) + list(got[1]), ints)
            except Exception as e:
                record(f"combustion {f}", False, f"{type(e).__name__}: {e}")

section("B4 balancer: generated ionic families (independent formulas)")
METALS = ["Fe", "Cu", "Zn", "Al", "Cr", "Mn", "Co", "Ni", "Sn", "Pb", "Ag", "Ca", "Mg", "Ba"]
ANIONS = [("Cl", 1), ("SO4", 2), ("PO4", 3), ("OH", 1), ("NO3", 1), ("CO3", 2), ("O", 2), ("S", 2), ("N", 3)]
for m in METALS:
    for a in (1, 2, 3, 4):
        # precipitation: b M^a+ + a X^b-  ->  M_b X_a  (reduced)
        for x, b in ANIONS:
            g = math.gcd(a, b)
            mb, xa = b // g, a // g
            prod = (m + (str(mb) if mb > 1 else "")) + (f"({x}){xa}" if xa > 1 and len(x) > 1 else x + (str(xa) if xa > 1 else ""))
            try:
                got = coeffs_of(f"{m}^{a}+ + {x}^{b}- -> {prod}")
                equal(f"{m}{a}+ + {x}{b}- -> {prod}", [c for c, _, _ in got[0] + got[1]], [mb, xa, 1])
            except Exception as e:
                record(f"{m}{a}+ + {x}{b}- -> {prod}", False, f"{type(e).__name__}: {e}")
        # half-equations: M^(a+k)+ + k e- -> M^a+
        for k in (1, 2, 3):
            hi = a + k
            lo = f"{m}^{a}+" if a else m
            try:
                got = coeffs_of(f"{m}^{hi}+ + e- -> {lo}")
                equal(f"{m}{hi}+ + e- -> {m}{a}+", [c for c, _, _ in got[0] + got[1]], [1, k, 1])
            except Exception as e:
                record(f"{m}{hi}+ half-equation", False, f"{type(e).__name__}: {e}")
        # displacement: a Ag+ + ... generalised: b·M^a+ + a·N -> b·M + a·N^b+
        for n_metal, bq in (("Zn", 2), ("Al", 3), ("Mg", 2)):
            if n_metal == m:
                continue
            g = math.gcd(a, bq)
            try:
                got = coeffs_of(f"{m}^{a}+ + {n_metal} -> {m} + {n_metal}^{bq}+")
                equal(f"{m}{a}+ + {n_metal} displacement", [c for c, _, _ in got[0] + got[1]],
                      [bq // g, a // g, bq // g, a // g])
            except Exception as e:
                record(f"{m}{a}+ + {n_metal} displacement", False, f"{type(e).__name__}: {e}")

section("B5 balancer: notation, order and spacing never change the answer")
NOTATIONS = [
    ["MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+", "MnO4- + Fe2+ -> Mn2+ + Fe3+", "MnO₄⁻ + Fe²⁺ → Mn²⁺ + Fe³⁺",
     "MnO4(-) + Fe(2+) -> Mn(2+) + Fe(3+)", "MnO4 - + Fe 2+ -> Mn 2+ + Fe 3+", "mno4- + fe2+ -> mn2+ + fe3+",
     "MnO4-(aq) + Fe2+(aq) -> Mn2+(aq) + Fe3+(aq)", "MnO4-+Fe2+->Mn2++Fe3+", "MnO4^-+Fe^2+ = Mn^2++Fe^3+",
     "MnO4^- + Fe+2 -> Mn+2 + Fe+3", "MnO4- + 3Fe2+ -> Mn2+ + Fe3+"],
    ["Cr2O7^2- + Fe^2+ -> Cr^3+ + Fe^3+", "Cr2O72- + Fe2+ -> Cr3+ + Fe3+", "Cr₂O₇²⁻ + Fe²⁺ ⟶ Cr³⁺ + Fe³⁺",
     "Cr2O7 2- + Fe 2+ -> Cr 3+ + Fe 3+", "Cr2O7-- + Fe++ -> Cr+++ + Fe+++"],
    ["Ba^2+ + SO4^2- -> BaSO4", "Ba2+ + SO42- -> BaSO4(s)", "Ba2++SO42-->BaSO4", "Ba²⁺(aq) + SO₄²⁻(aq) → BaSO₄(s)"],
]
for group in NOTATIONS:
    base = None
    for text in group:
        try:
            got = coeffs_of(text, "acidic")
            key = (sorted(got[0]), sorted(got[1]))
            if base is None:
                base = key
            equal(f"same answer: {text}", key, base)
        except Exception as e:
            record(f"same answer: {text}", False, f"{type(e).__name__}: {e}")
# species order: shuffle reactants/products, coefficients follow their species
for text, medium, want_r, want_p in KNOWN:
    r, p = parse_equation(text)
    for _ in range(4):
        r2, p2 = r[:], p[:]
        random.shuffle(r2)
        random.shuffle(p2)
        try:
            res = balance_full(r2, p2, medium)
            got = (sorted((c, s.formula, s.charge) for c, s in res["reactants"]),
                   sorted((c, s.formula, s.charge) for c, s in res["products"]))
            equal(f"shuffled order: {text}", got, (sorted(want_r), sorted(want_p)))
        except Exception as e:
            record(f"shuffled order: {text}", False, f"{type(e).__name__}: {e}")
# writing H+ / H2O yourself gives the same answer as the acidic option
equal("explicit H+ and H2O == acidic option",
      tuple(map(sorted, coeffs_of("MnO4^- + H^+ + Fe^2+ -> Mn^2+ + Fe^3+ + H2O"))),
      tuple(map(sorted, coeffs_of("MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+", "acidic"))))

section("B6 balancer: species parsing")
SPECIES = [
    ("Fe^3+", "Fe", 3), ("Fe3+", "Fe", 3), ("Fe+3", "Fe", 3), ("Fe(3+)", "Fe", 3), ("Fe³⁺", "Fe", 3),
    ("Fe 3+", "Fe", 3), ("Fe+++", "Fe", 3), ("O2-", "O", -2), ("S2-", "S", -2), ("N3-", "N", -3),
    ("NH4+", "NH4", 1), ("H3O+", "H3O", 1), ("OH-", "OH", -1), ("HCO3-", "HCO3", -1),
    ("SO42-", "SO4", -2), ("SO4 2-", "SO4", -2), ("SO4--", "SO4", -2), ("SO₄²⁻", "SO4", -2),
    ("PO43-", "PO4", -3), ("Cr2O72-", "Cr2O7", -2), ("MnO₄⁻", "MnO4", -1), ("Al(OH)4^-", "Al(OH)4", -1),
    ("[Cu(NH3)4]^2+", "[Cu(NH3)4]", 2), ("Fe(CN)6^3-", "Fe(CN)6", -3), ("e-", "e", -1), ("e⁻", "e", -1),
    ("2H2O(l)", "H2O", 0), ("Cu(OH)2(s)", "Cu(OH)2", 0), ("Fe^3+(aq)", "Fe", 3), ("h+", "H", 1),
    ("NO3−", "NO3", -1), ("Cl-", "Cl", -1), ("Fe+2", "Fe", 2),
]
for text, formula, charge in SPECIES:
    try:
        sp = parse_species(text)
        equal(f"parse {text}", (sp.formula, sp.charge), (formula, charge))
    except Exception as e:
        record(f"parse {text}", False, f"{type(e).__name__}: {e}")

section("B7 balancer: bad input is rejected with a message")
BAD = [
    ("H2 + O2", None), ("H2 -> O2 -> H2O", None), ("H2 -> O2", None), ("Fe2+ -> Fe3+", None),
    ("H2 + O2 -> H2O + H2O2", None), ("-> H2O", None), ("H2 ->", None), ("H2 + + O2 -> H2O", None),
    ("Fe^0 -> Fe", None), ("Fe^x -> Fe", None), ("Xx^2+ + e- -> Xx", None), ("e- -> e-", None),
    ("Fe^3+ + e- -> Fe^2+", "neutral"), ("", None), ("Na+ + Cl- -> NaCl + H2", None),
    ("Fe+- -> Fe", None), ("E -> F", None), ("2 + H2 -> H2", None), ("H2O + Fe -> FeO + H2O", None),
]
for text, medium in BAD:
    try:
        balance_full(*parse_equation(text), medium)
        record(f"rejects: {text!r} [{medium}]", False, "no error raised")
    except ValueError as e:
        record(f"rejects: {text!r} [{medium}]", bool(str(e).strip()))
    except Exception as e:
        record(f"rejects: {text!r} [{medium}]", False, f"crashed with {type(e).__name__}: {e}")


section("B8 balancer: charges written without ^ are read correctly")
NO_CARET = [
    ("SO42-", "SO4", -2), ("SO32-", "SO3", -2), ("CO32-", "CO3", -2), ("PO43-", "PO4", -3),
    ("HPO42-", "HPO4", -2), ("H2PO4-", "H2PO4", -1), ("NH4+", "NH4", 1), ("NO3-", "NO3", -1),
    ("NO2-", "NO2", -1), ("OH-", "OH", -1), ("MnO4-", "MnO4", -1), ("CrO42-", "CrO4", -2),
    ("Cr2O72-", "Cr2O7", -2), ("C2O42-", "C2O4", -2), ("S2O32-", "S2O3", -2),
    ("S4O62-", "S4O6", -2), ("ClO4-", "ClO4", -1), ("I3-", "I3", -1), ("Hg22+", "Hg2", 2),
    ("O22-", "O2", -2), ("Fe3+", "Fe", 3), ("Cu2+", "Cu", 2), ("Al3+", "Al", 3),
    ("S2-", "S", -2), ("O2-", "O", -2), ("V5+", "V", 5), ("V4+", "V", 4), ("Os4+", "Os", 4),
    ("Ti4+", "Ti", 4), ("HCO3-", "HCO3", -1), ("CH3COO-", "CH3COO", -1),
    ("Fe(CN)64-", "Fe(CN)6", -4), ("Fe(CN)63-", "Fe(CN)6", -3), ("H3O+", "H3O", 1),
    ("so42-", "SO4", -2), ("nh4+", "NH4", 1), ("SiO44-", "SiO4", -4),
]
for text, formula, charge in NO_CARET:
    try:
        sp = parse_species(text)
        equal(f"reads {text}", (sp.formula, sp.charge), (formula, charge))
    except Exception as e:
        record(f"reads {text}", False, f"{type(e).__name__}: {e}")
record("monatomic 'V4+' has no cluster reading", parse_species("V4+").alternatives is None)
record("'SO42-' is certain (only SO4 2- is a known ion)", parse_species("SO42-").alternatives is None)
record("'N3-' keeps both readings (nitride and azide)", parse_species("N3-").alternatives is not None)

# the reading that balances wins, and a note is given only when both balance
AMBIG = [
    ("Hg22+ + e- -> Hg", [(1, "Hg2", 2), (2, "e", -1)], [(2, "Hg", 0)], False),
    ("O22- + H+ -> H2O2", [(1, "O2", -2), (2, "H", 1)], [(1, "H2O2", 0)], False),
    ("N3- + H+ -> HN3", [(1, "N3", -1), (1, "H", 1)], [(1, "HN3", 0)], False),
    ("N3- + H+ -> NH3", [(1, "N", -3), (3, "H", 1)], [(1, "NH3", 0)], False),
    ("Li + N2 -> Li+ + N3-", [(6, "Li", 0), (1, "N2", 0)], [(6, "Li", 1), (2, "N", -3)], True),
    ("I2 + I- -> I3-", [(1, "I2", 0), (1, "I", -1)], [(1, "I3", -1)], False),
    ("Fe(CN)63- + e- -> Fe(CN)64-", [(1, "Fe(CN)6", -3), (1, "e", -1)], [(1, "Fe(CN)6", -4)], False),
]
for text, want_r, want_p, want_note in AMBIG:
    try:
        res = balance_full(*parse_equation(text))
        got = ([(c, s.formula, s.charge) for c, s in res["reactants"]],
               [(c, s.formula, s.charge) for c, s in res["products"]])
        equal(f"{text}", got, (want_r, want_p))
        record(f"conserved: {text}", conserved(*got))
        equal(f"note shown only when both readings balance: {text}", bool(res["notes"]), want_note)
        if want_note:
            record(f"note says how to be explicit: {text}", "^" in res["notes"][0])
    except Exception as e:
        record(text, False, f"{type(e).__name__}: {e}")

section("B9 balancer: redox equations with more than one atom balance")
MULTI = [
    ("KMnO4 + H2O2 + H2SO4 -> K2SO4 + MnSO4 + O2 + H2O", None, [2, 5, 3], [1, 2, 5, 8]),
    ("K2Cr2O7 + H2O2 + H2SO4 -> K2SO4 + Cr2(SO4)3 + O2 + H2O", None, [1, 3, 4], [1, 1, 3, 7]),
    ("KMnO4 + H2O2 -> MnO2 + O2 + KOH + H2O", None, [2, 3], [2, 3, 2, 2]),
    ("H2O2 + MnO4- + H+ -> O2 + Mn2+ + H2O", None, [5, 2, 6], [5, 2, 8]),
    ("MnO4- + H2O2 -> MnO2 + O2 + OH- + H2O", None, [2, 3], [2, 3, 2, 2]),
    ("H2O2 + MnO4- -> O2 + Mn2+", "acidic", [5, 2, 6], [5, 2, 8]),
    ("Cr2O7^2- + H2O2 + H+ -> Cr^3+ + O2 + H2O", None, [1, 3, 8], [2, 3, 7]),
    ("H2O2 + KI + H2SO4 -> I2 + K2SO4 + H2O", None, [1, 2, 1], [1, 1, 2]),
]
for text, medium, wr, wp in MULTI:
    try:
        res = balance_full(*parse_equation(text), medium)
        got_r = [(c, s.formula, s.charge) for c, s in res["reactants"]]
        got_p = [(c, s.formula, s.charge) for c, s in res["products"]]
        equal(text, ([c for c, _, _ in got_r], [c for c, _, _ in got_p]), (wr, wp))
        record(f"conserved: {text}", conserved(got_r, got_p))
    except Exception as e:
        record(text, False, f"{type(e).__name__}: {e}")
for text in ["KMnO4 + H2O2 + H2SO4 -> K2SO4 + MnSO4 + O2 + H2O",
             "K2Cr2O7 + H2O2 + H2SO4 -> K2SO4 + Cr2(SO4)3 + O2 + H2O"]:
    r, p = parse_equation(text)
    for _ in range(6):
        random.shuffle(r)
        random.shuffle(p)
        try:
            res = balance_full(r, p)
            got = sorted((c, s.formula) for c, s in res["reactants"] + res["products"])
            want = sorted((c, s.formula) for c, s in
                          (lambda x: x["reactants"] + x["products"])(balance_full(*parse_equation(text))))
            equal(f"shuffled: {text}", got, want)
        except Exception as e:
            record(f"shuffled: {text}", False, f"{type(e).__name__}: {e}")
# genuinely two reactions in one: still refused, never guessed
for text in ["H2 + O2 -> H2O + H2O2", "Cu + HNO3 -> Cu(NO3)2 + NO + NO2 + H2O", "C + O2 -> CO + CO2",
             "Fe + O2 -> FeO + Fe2O3"]:
    try:
        balance_full(*parse_equation(text))
        record(f"refuses two-reactions-in-one: {text}", False, "no error raised")
    except ValueError as e:
        record(f"refuses two-reactions-in-one: {text}", "more than one" in str(e), str(e))

# ═════════════════════════════════════════════════════════════════════════════
# C. LIMITING REACTANT
# ═════════════════════════════════════════════════════════════════════════════
from limiting_reactant import calculate_limiting_reactant as LR, species_molar_mass
from percent_composition_calculator import compute_percent_composition

# IB-style molar masses written out independently (2 d.p. data booklet style)
MM = {"H2": 2.02, "O2": 32.00, "H2O": 18.02, "N2": 28.02, "NH3": 17.04, "Fe2O3": 159.70,
      "CO": 28.01, "Fe": 55.85, "CO2": 44.01, "Al": 26.98, "Cl2": 70.90, "AlCl3": 133.33,
      "CH4": 16.05, "Mg": 24.31, "HCl": 36.46, "MgCl2": 95.21}

section("C1 limiting reactant: hand-worked answers")
r = LR(["H2", "O2"], [4.0, 16.0], ["H2O"], unit="g")
equal("4.0 g H2 + 16.0 g O2: auto-balanced", (r["balanced"], r["equation"]), (True, "2H2 + O2 → 2H2O"))
equal("  limiting = O2", r["limiting"], ["O2"])
sig3("  H2O formed (g)", r["products"][0]["grams"], 2 * (16.0 / MM["O2"]) * MM["H2O"])
sig3("  H2 left over (g)", r["reactants"][0]["leftover_g"], 4.0 - 2 * (16.0 / MM["O2"]) * MM["H2"])
close("  mass conserved (g)", r["products"][0]["grams"] + r["reactants"][0]["leftover_g"], 20.0, rel=1e-9)

r = LR(["N2", "H2"], [28.0, 6.0], ["NH3"], unit="g")
equal("28.0 g N2 + 6.0 g H2: limiting = H2", r["limiting"], ["H2"])
close("  NH3 formed (g), within 0.5 % of 2-d.p. masses", r["products"][0]["grams"], 6.0 / MM["H2"] * 2 / 3 * MM["NH3"], rel=5e-3)

r = LR(["Fe2O3", "CO"], [160.0, 84.0], ["Fe", "CO2"], unit="g")
equal("160 g Fe2O3 + 84 g CO (close call): limiting = CO", r["limiting"], ["CO"])
sig3("  Fe formed (g)", r["products"][0]["grams"], 84.0 / MM["CO"] / 3 * 2 * MM["Fe"])

r = LR(["Al", "Cl2"], [5.40, 21.3], ["AlCl3"], unit="g")
equal("5.40 g Al + 21.3 g Cl2 (0.1000 vs 0.1001): limiting = Al", r["limiting"], ["Al"])
r = LR(["Al", "Cl2"], [5.40, 21.0], ["AlCl3"], unit="g")
equal("5.40 g Al + 21.0 g Cl2: limiting = Cl2", r["limiting"], ["Cl2"])
sig3("  AlCl3 formed (g)", r["products"][0]["grams"], 21.0 / MM["Cl2"] * 2 / 3 * MM["AlCl3"])

r = LR(["Mg", "HCl"], [0.0500, 0.0800], ["MgCl2", "H2"])
equal("0.0500 mol Mg + 0.0800 mol HCl: limiting = HCl", r["limiting"], ["HCl"])
close("  H2 formed (mol)", r["products"][1]["moles"], 0.0400, rel=1e-12)
close("  Mg left (mol)", r["reactants"][0]["leftover_mol"], 0.0100, rel=1e-9)

r = LR(["H2", "O2"], [2.0, 1.0], ["H2O"], [2, 1], [2])
equal("exact ratio: both limiting", r["limiting"], ["H2", "O2"])
equal("  nothing left over", [x["leftover_mol"] for x in r["reactants"]], [0.0, 0.0])
close("  H2O = 2.0 mol", r["products"][0]["moles"], 2.0, rel=1e-12)

r = LR(["Qa", "Qb"], [3, 5], ["Qc"], [1, 2], [1])
equal("plain names in moles work", (r["limiting"], r["products"][0]["moles"], r["products"][0]["grams"]),
      (["Qb"], 2.5, None))
r = LR(["B", "C"], [3, 5], ["B4C"], [4, 1], [1])
equal("single-letter names that are elements get masses (B, C)", r["products"][0]["grams"] is not None, True)
r = LR(["H2", "O2"], [0, 5], ["H2O"])
equal("zero amount -> that reactant limits, nothing forms",
      (r["limiting"], r["products"][0]["moles"]), (["H2"], 0.0))
r = LR(["H2", "O2"], ["4", "16"], ["H2O"], ["", ""], [""], unit="g")
equal("amounts and blank coefficients as strings (from the web form)", r["limiting"], ["O2"])
r = LR(["Fe^3+", "OH-"], [0.10, 0.20], ["Fe(OH)3"])
equal("ions work: Fe3+ + 3OH- -> Fe(OH)3", (r["equation"], r["limiting"]), ("Fe^3+ + 3OH- → Fe(OH)3", ["OH-"]))

section("C2 limiting reactant: random property checks")
CORPUS = [(r_, p_) for r_, p_, _, _ in MOLECULAR if len(r_) > 1] + [
    (["H2", "O2"], ["H2O"]), (["N2", "H2"], ["NH3"]), (["Fe2O3", "CO"], ["Fe", "CO2"]),
    (["Al", "Cl2"], ["AlCl3"]), (["C3H8", "O2"], ["CO2", "H2O"]), (["Na", "H2O"], ["NaOH", "H2"]),
    (["AgNO3", "NaCl"], ["AgCl", "NaNO3"]), (["CaCO3", "HCl"], ["CaCl2", "H2O", "CO2"]),
    (["Zn", "CuSO4"], ["ZnSO4", "Cu"]), (["C8H18", "O2"], ["CO2", "H2O"]),
]
for reactants, products in CORPUS:
    rc, pc = balance_equation(reactants, products)
    r_mm = [species_molar_mass(x) for x in reactants]
    p_mm = [species_molar_mass(x) for x in products]
    for M, f in zip(r_mm + p_mm, reactants + products):
        close(f"molar mass {f} matches percent-composition module", M, compute_percent_composition(f)[0], rel=1e-12)
    name = " + ".join(reactants)
    for trial in range(40):
        grams = [10 ** random.uniform(-3, 4) for _ in reactants]
        res = LR(reactants, grams, products, unit="g")
        rows = res["reactants"]
        # 1. exactly the limiting reactant(s) are used up; nothing goes negative
        record(f"{name}: limiting has 0 left", all(rows[i]["leftover_mol"] == 0
                                                   for i, n in enumerate(reactants) if n in res["limiting"]))
        record(f"{name}: no negative leftovers", all(x["leftover_mol"] >= 0 for x in rows))
        record(f"{name}: used ≤ available", all(x["used_mol"] <= x["moles"] * (1 + 1e-12) for x in rows))
        # 2. limiting really is the smallest moles/coefficient (checked independently)
        ratios = [g / M / c for g, M, c in zip(grams, r_mm, rc)]
        record(f"{name}: limiting is argmin", reactants[ratios.index(min(ratios))] in res["limiting"])
        # 3. mass is conserved: reactant mass used == product mass formed
        used_g = sum(x["used_mol"] * M for x, M in zip(rows, r_mm))
        made_g = sum(p["grams"] for p in res["products"])
        close(f"{name}: mass conserved", made_g, used_g, rel=1e-9)
        # 4. products follow the coefficients exactly
        ext = min(ratios)
        for p, c in zip(res["products"], pc):
            close(f"{name}: product moles", p["moles"], c * ext, rel=1e-9)
        # 5. scaling every amount by k scales every answer by k
        k = random.uniform(0.001, 1000)
        res_k = LR(reactants, [g * k for g in grams], products, unit="g")
        for p, pk in zip(res["products"], res_k["products"]):
            close(f"{name}: scales with amount", pk["moles"], p["moles"] * k, rel=1e-9)
        equal(f"{name}: same limiting after scaling", res_k["limiting"], res["limiting"])
        # 6. grams and moles give the same result
        res_m = LR(reactants, [x["moles"] for x in rows], products, unit="mol")
        for p, pm in zip(res["products"], res_m["products"]):
            close(f"{name}: g == mol input", pm["moles"], p["moles"], rel=1e-12)
        # 7. extra of a non-limiting reactant changes nothing
        lim_i = reactants.index(res["limiting"][0])
        others = [i for i in range(len(reactants)) if i != lim_i]
        if others and len(res["limiting"]) == 1:
            j = random.choice(others)
            more = grams[:]
            more[j] *= random.uniform(1, 100)
            res_x = LR(reactants, more, products, unit="g")
            for p, px in zip(res["products"], res_x["products"]):
                close(f"{name}: excess doesn't change yield", px["moles"], p["moles"], rel=1e-12)
        # 8. given coefficients == auto-balanced coefficients
        res_c = LR(reactants, grams, products, rc, pc, unit="g")
        for p, pcx in zip(res["products"], res_c["products"]):
            close(f"{name}: typed coefficients == auto", pcx["moles"], p["moles"], rel=1e-12)
        # 9. scaled coefficients (×2) give the same masses
        res_2 = LR(reactants, grams, products, [2 * c for c in rc], [2 * c for c in pc], unit="g")
        for p, p2 in zip(res["products"], res_2["products"]):
            close(f"{name}: doubled coefficients give same grams", p2["grams"], p["grams"], rel=1e-12)

# near-ties: amounts that differ by tiny fractions must still pick the right one
for eps in (1e-3, 1e-6, 1e-8):
    r = LR(["H2", "O2"], [2.0 * (1 - eps), 1.0], ["H2O"], [2, 1], [2])
    equal(f"near tie (H2 short by {eps}): limiting = H2", r["limiting"], ["H2"])
    close(f"near tie {eps}: O2 leftover", r["reactants"][1]["leftover_mol"], eps, rel=1e-6)
    r = LR(["H2", "O2"], [2.0, 1.0 * (1 - eps)], ["H2O"], [2, 1], [2])
    equal(f"near tie (O2 short by {eps}): limiting = O2", r["limiting"], ["O2"])

section("C3 limiting reactant: bad input is rejected")
raises("some coefficients blank", lambda: LR(["H2", "O2"], [1, 1], ["H2O"], [2, ""], [2]))
raises("negative amount", lambda: LR(["H2", "O2"], [-1, 1], ["H2O"]))
raises("NaN amount", lambda: LR(["H2", "O2"], [float("nan"), 1], ["H2O"]))
raises("infinite amount", lambda: LR(["H2", "O2"], [float("inf"), 1], ["H2O"]))
raises("text amount", lambda: LR(["H2", "O2"], ["abc", 1], ["H2O"]))
raises("zero coefficient", lambda: LR(["H2", "O2"], [1, 1], ["H2O"], [0, 1], [2]))
raises("negative coefficient", lambda: LR(["H2", "O2"], [1, 1], ["H2O"], [-2, 1], [2]))
raises("grams with a non-formula name", lambda: LR(["Qa", "Qb"], [1, 1], ["Qc"], [1, 1], [1], unit="g"))
raises("auto-balance with non-formula names", lambda: LR(["Qa", "Qb"], [1, 1], ["Qc"]))
raises("wrong number of amounts", lambda: LR(["H2", "O2"], [1], ["H2O"]))
raises("wrong number of coefficients", lambda: LR(["H2", "O2"], [1, 1], ["H2O"], [2], [2]))
raises("no products", lambda: LR(["H2", "O2"], [1, 1], []))
raises("no reactants", lambda: LR([], [], ["H2O"]))
raises("blank name", lambda: LR(["H2", " "], [1, 1], ["H2O"], [1, 1], [1]))
raises("bad unit", lambda: LR(["H2", "O2"], [1, 1], ["H2O"], unit="kg"))
raises("unbalanceable when auto", lambda: LR(["H2"], [1], ["O2"]))


section("C4 limiting reactant: names that aren't formulas, wrong coefficients")
r = LR(["Qa", "Qb"], [3, 5], ["Qc"], [1, 2], [1])
equal("all labels: no masses, no warning", (r["products"][0]["grams"], r["warnings"]), (None, []))
r = LR(["A", "B"], [3, 5], ["C"], [1, 2], [1])
equal("'A', 'B', 'C' labels: B and C are NOT given boron/carbon masses",
      [x["grams"] for x in r["reactants"] + r["products"]], [None, None, None])
record("  ...and the student is told why", any("A is not a chemical formula" in w for w in r["warnings"]))
close("  mole answer still right", r["products"][0]["moles"], 2.5)
r = LR(["B", "C"], [3, 5], ["B4C"], [4, 1], [1])
record("real formulas that balance keep their masses (4B + C -> B4C)",
       r["products"][0]["grams"] is not None and not r["warnings"])
r = LR(["B", "O2"], [1, 1], ["B2O3"], [1, 1], [1])
equal("unbalanced coefficients in mol: masses hidden", r["products"][0]["grams"], None)
record("  ...with a warning naming the element", any("B: 1 on the left, 2 on the right" in w for w in r["warnings"]))
raises("unbalanced coefficients in g: refused", lambda: LR(["H2", "O2"], [4, 16], ["H2O"], [1, 1], [1], unit="g"))
raises("label mixed with formulas in g: refused", lambda: LR(["H2", "Qx"], [4, 16], ["H2O"], [2, 1], [2], unit="g"))
r = LR(["Fe^3+", "OH-"], [0.1, 0.2], ["Fe(OH)3"], [1, 3], [1])
record("charges are part of the balance check (Fe3+ + 3OH- -> Fe(OH)3)",
       r["products"][0]["grams"] is not None and not r["warnings"])
r = LR(["Fe^3+", "OH-"], [0.1, 0.2], ["Fe(OH)3"], [1, 2], [1])
record("wrong coefficient caught even when only the charge/atoms are off", bool(r["warnings"]))
# every corpus equation: a single wrong coefficient is always caught
for reactants, products in CORPUS:
    rc, pc = balance_equation(reactants, products)
    for k in range(len(rc) + len(pc)):
        bad_r, bad_p = list(rc), list(pc)
        if k < len(rc):
            bad_r[k] += 1
        else:
            bad_p[k - len(rc)] += 1
        name = " + ".join(reactants)
        raises(f"{name}: wrong coefficient #{k + 1} refused in g",
               lambda: LR(reactants, [10.0] * len(reactants), products, bad_r, bad_p, unit="g"))
        res = LR(reactants, [1.0] * len(reactants), products, bad_r, bad_p)
        record(f"{name}: wrong coefficient #{k + 1} warned in mol",
               bool(res["warnings"]) and all(p["grams"] is None for p in res["products"]))
    ok_res = LR(reactants, [1.0] * len(reactants), products, rc, pc)
    record(f"{name}: correct coefficients give masses and no warning",
           not ok_res["warnings"] and all(p["grams"] is not None for p in ok_res["products"]))

# ═════════════════════════════════════════════════════════════════════════════
# D. WEB API
# ═════════════════════════════════════════════════════════════════════════════
section("D  web API for the new features")
try:
    sys.path.insert(0, os.path.join(ROOT, "ui_interface"))
    import app as webapp
except ImportError as e:
    record("flask app imports", False, str(e))
    webapp = None

if webapp:
    client = webapp.app.test_client()

    def api(url, body):
        resp = client.post(url, json=body)
        txt = resp.get_data(as_text=True)
        try:
            return resp.status_code, json.loads(txt, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        except ValueError as e:
            return resp.status_code, {"__bad_json__": str(e)}

    def api_ok(label, url, body, check):
        st, d = api(url, body)
        good = st == 200 and "error" not in d and "__bad_json__" not in d
        try:
            good = good and check(d)
        except Exception as e:
            good = False
            d = {**d, "__check_error__": repr(e)}
        record(label, good, f"status={st} body={str(d)[:300]}")

    def api_err(label, url, body):
        st, d = api(url, body)
        record(label, st == 400 and isinstance(d.get("error"), str) and d["error"].strip(), f"status={st} body={d}")

    G = "/api/gas_laws"
    api_ok("ideal P in kPa from cm³ and °C", G,
           {"type": "ideal", "solve": "P", "n": "0.0100", "v": "250", "T": "25.0", "p": "",
            "p_unit": "kPa", "v_unit": "cm3", "t_unit": "C"},
           lambda d: d["unit"] == "kPa" and round(d["result"], 1) == 99.2 and "°C" in " ".join(d["detailed"]))
    api_ok("ideal V in m³", G, {"type": "ideal", "solve": "V", "n": "0.500", "v": "", "T": "300", "p": "100",
                               "p_unit": "kPa", "v_unit": "m3", "t_unit": "K"},
           lambda d: d["unit"] == "m3" and math.isclose(d["result"], 0.012471, rel_tol=1e-4))
    api_ok("ideal T answered in °C", G, {"type": "ideal", "solve": "T", "n": "1", "v": "22.41", "T": "",
                                        "p": "760", "p_unit": "mmHg", "v_unit": "L", "t_unit": "C"},
           lambda d: d["unit"] == "°C" and abs(d["result"]) < 0.2)
    api_ok("old requests without units still mean atm / L / K", G,
           {"type": "ideal", "solve": "P", "n": "0.0100", "v": "0.250", "T": "298", "p": ""},
           lambda d: d["unit"] == "atm" and round(d["result"], 3) == 0.978)
    api_ok("combined V2 with °C", G, {"type": "combined", "solve": "V2", "P1": "100", "V1": "2.00", "T1": "27",
                                     "P2": "150", "V2": "", "T2": "127", "p_unit": "kPa", "v_unit": "dm3", "t_unit": "C"},
           lambda d: round(d["result"], 2) == 1.78 and d["unit"] == "dm3")
    api_ok("mixing Pf in kPa", G, {"type": "mixing", "solve": "Pf", "P1": "100", "V1": "1", "T1": "25",
                                  "P2": "200", "V2": "2", "T2": "25", "Vf": "3", "Tf": "25",
                                  "p_unit": "kPa", "v_unit": "dm3", "t_unit": "C"},
           lambda d: round(d["result"]) == 167)
    api_ok("mixing Pf with blank Tf defaults to 25 °C", G,
           {"type": "mixing", "solve": "Pf", "P1": "100", "V1": "1", "T1": "25", "P2": "200", "V2": "2",
            "T2": "25", "Vf": "3", "Tf": "", "p_unit": "kPa", "v_unit": "dm3", "t_unit": "C"},
           lambda d: round(d["result"]) == 167)
    api_ok("dalton in kPa", G, {"type": "dalton", "gases": [{"name": "N2", "p": "79"}, {"name": "O2", "p": "21"}],
                               "p_unit": "kPa"}, lambda d: d["total"] == 100 and "kPa" in d["compact"])
    api_err("unknown unit", G, {"type": "ideal", "solve": "P", "n": "1", "v": "1", "T": "300", "p": "", "p_unit": "psi"})
    api_err("below absolute zero", G, {"type": "ideal", "solve": "P", "n": "1", "v": "1", "T": "-300", "p": "",
                                      "t_unit": "C"})
    api_err("blank n", G, {"type": "ideal", "solve": "P", "n": "", "v": "1", "T": "300", "p": ""})
    api_err("dalton negative pressure", G, {"type": "dalton", "gases": [{"name": "N2", "p": "-1"}]})
    api_err("dalton with no gases", G, {"type": "dalton", "gases": []})

    E = "/api/equation"
    api_ok("ionic redox in acidic solution", E, {"equation": "MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+", "medium": "acidic"},
           lambda d: d["balanced"] == "MnO4⁻ + 5Fe²⁺ + 8H⁺ → Mn²⁺ + 5Fe³⁺ + 4H2O" and d["added"])
    api_ok("basic solution", E, {"equation": "MnO4- + I- -> MnO2 + I2", "medium": "basic"},
           lambda d: d["balanced"] == "2MnO4⁻ + 6I⁻ + 4H2O → 2MnO2 + 3I2 + 8OH⁻")
    api_ok("half-equation", E, {"equation": "Fe3+ + e- -> Fe2+", "medium": ""},
           lambda d: d["balanced"] == "Fe³⁺ + e⁻ → Fe²⁺")
    api_ok("medium omitted (old page)", E, {"equation": "H2 + O2 -> H2O"},
           lambda d: d["balanced"] == "2H2 + O2 → 2H2O")
    api_ok("states kept in output", E, {"equation": "Zn(s) + H+(aq) -> Zn2+(aq) + H2(g)"},
           lambda d: d["balanced"] == "Zn(s) + 2H⁺(aq) → Zn²⁺(aq) + H2(g)")
    api_err("charge doesn't balance", E, {"equation": "Fe2+ -> Fe3+"})
    api_err("bad medium", E, {"equation": "H2 + O2 -> H2O", "medium": "salty"})
    api_err("two arrows", E, {"equation": "A -> B -> C"})

    L = "/api/limiting"
    api_ok("grams + auto-balance", L,
           {"unit": "g", "reactants": [{"name": "H2", "coeff": "", "amount": "4.0"},
                                       {"name": "O2", "coeff": "", "amount": "16.0"}],
            "products": [{"name": "H2O", "coeff": ""}]},
           lambda d: d["limiting"] == "O2" and d["balanced"] and round(d["yields_g"]["H2O"], 1) == 18.0)
    api_ok("old request shape (moles key, no unit)", L,
           {"reactants": [{"name": "N2", "coeff": "1", "moles": "2.0"}, {"name": "H2", "coeff": "3", "moles": "3.0"}],
            "products": [{"name": "NH3", "coeff": "2"}]},
           lambda d: d["limiting"] == "H2" and d["yields"] == {"NH3": 2.0})
    api_ok("exact ratio lists both", L,
           {"unit": "mol", "reactants": [{"name": "H2", "coeff": "2", "amount": "2"},
                                         {"name": "O2", "coeff": "1", "amount": "1"}],
            "products": [{"name": "H2O", "coeff": "2"}]},
           lambda d: d["limiting_all"] == ["H2", "O2"])
    api_ok("non-formula names in mol give null grams (valid JSON)", L,
           {"unit": "mol", "reactants": [{"name": "Qa", "coeff": "1", "amount": "1"}],
            "products": [{"name": "H2O", "coeff": "1"}]},
           lambda d: d["yields_g"] == {"H2O": None} and "Qa is not a chemical formula" in d["warnings"][0])
    api_ok("wrong coefficients in mol: warning, no grams", L,
           {"unit": "mol", "reactants": [{"name": "H2", "coeff": "1", "amount": "1"},
                                         {"name": "O2", "coeff": "1", "amount": "1"}],
            "products": [{"name": "H2O", "coeff": "1"}]},
           lambda d: d["yields_g"] == {"H2O": None} and "not balanced" not in d["warnings"][0]
           and "O: 2 on the left, 1 on the right" in d["warnings"][0])
    api_err("wrong coefficients in g", L,
            {"unit": "g", "reactants": [{"name": "H2", "coeff": "1", "amount": "1"},
                                        {"name": "O2", "coeff": "1", "amount": "1"}],
             "products": [{"name": "H2O", "coeff": "1"}]})
    api_ok("ambiguous charge note reaches the page", E, {"equation": "Li + N2 -> Li+ + N3-"},
           lambda d: d["balanced"] == "6Li + N2 → 6Li⁺ + 2N³⁻" and "N^3-" in d["warnings"][0])
    api_ok("molecular redox with two atom balances", E,
           {"equation": "KMnO4 + H2O2 + H2SO4 -> K2SO4 + MnSO4 + O2 + H2O"},
           lambda d: d["balanced"] == "2KMnO4 + 5H2O2 + 3H2SO4 → K2SO4 + 2MnSO4 + 5O2 + 8H2O")
    api_err("grams with non-formula", L, {"unit": "g", "reactants": [{"name": "Qa", "coeff": "1", "amount": "1"}],
                                          "products": [{"name": "Qb", "coeff": "1"}]})
    api_err("partly blank coefficients", L,
            {"unit": "mol", "reactants": [{"name": "H2", "coeff": "2", "amount": "1"},
                                          {"name": "O2", "coeff": "", "amount": "1"}],
             "products": [{"name": "H2O", "coeff": "2"}]})
    api_err("blank amount", L, {"unit": "mol", "reactants": [{"name": "H2", "coeff": "", "amount": ""}],
                                "products": [{"name": "H2O", "coeff": ""}]})

    # every new/changed form field the page sends is read by the server
    html = open(os.path.join(ROOT, "ui_interface", "index.html"), encoding="utf-8").read()
    for needle in ("medium: val('eqMedium')", "unit: val('limUnit')", "amount: ins[2].value",
                   "p_unit: val('gasPU')", "...units"):
        record(f"page sends {needle}", needle in html)


# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
total_p = sum(p for p, _ in COUNTS.values())
total_f = sum(f for _, f in COUNTS.values())
for name, (p, f) in COUNTS.items():
    print(f"  {name:62} {p:6d} passed  {f:4d} failed")
print(f"\n  TOTAL  {total_p + total_f} checks   Passed: {total_p}   Failed: {total_f}")
if FAILURES:
    print(f"\n{len(FAILURES)} failure(s) — see above.")
sys.exit(1 if total_f else 0)
