"""
IB Chemistry acceptance tests.

Worked problems in the style of IB Chemistry (SL/HL) questions, organised by
syllabus topic. Expected answers were worked by hand using IB data-booklet
conventions (R = 8.31 J K-1 mol-1, molar volume 22.7 dm3 mol-1 at STP,
F = 96 500 C mol-1, Kw = 1.00e-14, c(water) = 4.18 J g-1 K-1) and are checked
to 3 significant figures, which is how IB mark schemes award answers.

Run:  py test_files/test_ib_chemistry.py
"""

import sys, os, math

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PASS = FAIL = 0
FAILURES = []


def _sig3(x):
    """Round to 3 significant figures (IB answer precision)."""
    if x == 0:
        return 0.0
    return round(x, -int(math.floor(math.log10(abs(x)))) + 2)


def check(label, got, expected, rel=None):
    """Numbers: equal at 3 s.f. (or within `rel` relative tolerance).
    Anything else: exact equality."""
    global PASS, FAIL
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            if rel is not None:
                ok = abs(got - expected) <= rel * abs(expected)
            else:
                ok = _sig3(got) == _sig3(expected)
        except TypeError:
            ok = False
    else:
        ok = got == expected
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}\n         got={got!r}  expected={expected!r}"
        FAILURES.append(msg)
        print(msg)


def check_raises(label, fn, exc_type=ValueError):
    """The call must raise; that is the correct behaviour for bad input."""
    global PASS, FAIL
    try:
        fn()
    except exc_type:
        PASS += 1
        print(f"  [PASS] {label}")
        return
    except Exception as e:
        got = f"raised {type(e).__name__}: {e}"
    else:
        got = "no exception"
    FAIL += 1
    msg = f"  [FAIL] {label}\n         {got} (expected {exc_type.__name__})"
    FAILURES.append(msg)
    print(msg)


def section(title):
    print(f"\n=== {title} ===")


# ─────────────────────────────────────────────────────────────────────────────
section("S1.4 Counting particles by mass: the mole")
from mole_conversions import mass_to_moles, moles_to_particles, moles_to_volume, volume_to_moles
from percent_composition_calculator import compute_percent_composition
from Empirical_Formula_Calculator import calculate_empirical_formula, display_empirical_formula

mm_caco3, _ = compute_percent_composition("CaCO3")
check("Mr of CaCO3", mm_caco3, 100.09, rel=1e-3)
check("n in 10.0 g CaCO3", mass_to_moles(10.0, mm_caco3), 0.0999)
check("particles in 0.250 mol", moles_to_particles(0.250), 1.51e23)
_, pct_h2o = compute_percent_composition("H2O")
check("% O in H2O", pct_h2o["O"], 88.8)
mm_hyd, pct_hyd = compute_percent_composition("CuSO4·5H2O")
check("Mr of CuSO4·5H2O", mm_hyd, 249.7, rel=1e-3)
check("% water in CuSO4·5H2O", 5 * compute_percent_composition("H2O")[0] / mm_hyd * 100, 36.1)
check("V of 0.500 mol gas at STP (dm3)", moles_to_volume(0.500), 11.35, rel=1e-3)
check("n in 4.54 dm3 gas at STP", volume_to_moles(4.54), 0.200)

check("empirical: C 85.7 %, H 14.3 %",
      display_empirical_formula(calculate_empirical_formula(["C", "H"], [85.7, 14.3])), "CH2")
check("empirical: 2.43 g Mg + 1.60 g O",
      display_empirical_formula(calculate_empirical_formula(["Mg", "O"], [2.43, 1.60])), "MgO")
check("empirical: C 40.0 %, H 6.7 %, O 53.3 %",
      display_empirical_formula(calculate_empirical_formula(["C", "H", "O"], [40.0, 6.7, 53.3])), "CH2O")
check("empirical: Fe 72.4 %, O 27.6 % (Fe3O4)",
      display_empirical_formula(calculate_empirical_formula(["Fe", "O"], [72.4, 27.6])), "Fe3O4")
check("empirical: P 43.6 %, O 56.4 % (P2O5)",
      display_empirical_formula(calculate_empirical_formula(["P", "O"], [43.6, 56.4])), "P2O5")

# ─────────────────────────────────────────────────────────────────────────────
section("R2.1 How much? The amount of chemical change")
from equation_balancer import balance_equation
from atom_economy_calculator import calculate_atom_economy
from percentage_yield_calculator import calc_percentage_yield

for eq, r, p, want in [
    ("ethanol combustion", ["C2H5OH", "O2"], ["CO2", "H2O"], ([1, 3], [2, 3])),
    ("octane combustion", ["C8H18", "O2"], ["CO2", "H2O"], ([2, 25], [16, 18])),
    ("blast furnace", ["Fe2O3", "CO"], ["Fe", "CO2"], ([1, 3], [2, 3])),
    ("Ostwald step 1", ["NH3", "O2"], ["NO", "H2O"], ([4, 5], [4, 6])),
    ("Cu + dilute HNO3", ["Cu", "HNO3"], ["Cu(NO3)2", "NO", "H2O"], ([3, 8], [3, 2, 4])),
    ("thermal decomposition", ["NaHCO3"], ["Na2CO3", "H2O", "CO2"], ([2], [1, 1, 1])),
    ("neutralisation", ["H3PO4", "Ca(OH)2"], ["Ca3(PO4)2", "H2O"], ([2, 3], [1, 6])),
    ("photosynthesis", ["CO2", "H2O"], ["C6H12O6", "O2"], ([6, 6], [1, 6])),
]:
    try:
        check(f"balance {eq}", balance_equation(r, p), want)
    except Exception as e:
        check(f"balance {eq}", f"{type(e).__name__}: {e}", want)

ae, _, _ = calculate_atom_economy(["C6H12O6"], [1], "C2H5OH", 2)
check("atom economy of fermentation", ae, 51.1)
ae, _, _ = calculate_atom_economy(["C2H4", "H2O"], [1, 1], "C2H5OH", 1)
check("atom economy of hydration", ae, 100.0)
check("percentage yield 7.50 g of 10.0 g", calc_percentage_yield(7.50, 10.0), 75.0)

# ─────────────────────────────────────────────────────────────────────────────
section("S1.5 Ideal gases")
from gas_laws import ideal_gas_find_P, ideal_gas_find_n, combined_gas_find_V2, graham_rate_ratio

# 0.0100 mol at 298 K in 250 cm3 -> 99.1 kPa = 0.978 atm (module works in atm, L)
check("PV=nRT: P (atm)", ideal_gas_find_P(0.0100, 0.250, 298), 0.978)
check("PV=nRT: P converted to kPa", ideal_gas_find_P(0.0100, 0.250, 298) * 101.325, 99.1)
check("PV=nRT: n from 1.00 atm, 2.00 dm3, 273 K", ideal_gas_find_n(1.00, 2.00, 273), 0.0893)
check("combined gas law V2", combined_gas_find_V2(100, 2.00, 300, 150, 400), 1.78)
check("Graham H2 vs O2 rate ratio", graham_rate_ratio(2.016, 32.00), 3.98)

# ─────────────────────────────────────────────────────────────────────────────
section("R1.1 / R1.2 Energetics")
from thermodynamics import (cal_q, cal_dT, hess_law, bond_enthalpy_dH, lookup_bond,
                            standard_enthalpy_rxn, gibbs_dG, gibbs_T, spontaneity)

check("q = mcΔT: 50.0 g water, ΔT 12.0 K (J)", cal_q(50.0, 4.18, 12.0), 2508.0, rel=1e-9)
check("ΔT from 1.05 kJ into 100 g water", cal_dT(1050, 100, 4.18), 2.51)
bb = [("C-H", 4, lookup_bond("C-H")), ("O=O", 2, lookup_bond("O=O"))]
bf = [("C=O", 2, lookup_bond("C=O")), ("O-H", 4, lookup_bond("O-H"))]
check("bond enthalpy ΔH of CH4 combustion (kJ)", bond_enthalpy_dH(bb, bf)[0], -808.0, rel=1e-9)
check("bond enthalpy lookup reversed H-O", lookup_bond("H-O"), 463)
check("bond enthalpy lookup N≡N typed as N#N", lookup_bond("N#N"), 945)
check("bond enthalpy lookup lowercase cl-cl", lookup_bond("cl-cl"), 242)
check("Hess cycle: ΔH1 − ΔH2 + 2ΔH3",
      hess_law([-393.5, -283.0, -110.5], [1, -1, 2]), -331.5, rel=1e-9)
check("ΔH from ΔHf: CH4 combustion", standard_enthalpy_rxn([
    {"formula": "CH4", "dHf": -74.0, "coeff": 1, "role": "reactant"},
    {"formula": "O2", "dHf": 0.0, "coeff": 2, "role": "reactant"},
    {"formula": "CO2", "dHf": -393.5, "coeff": 1, "role": "product"},
    {"formula": "H2O", "dHf": -285.8, "coeff": 2, "role": "product"},
]), -891.1, rel=1e-9)

section("R1.4 Entropy and spontaneity (HL)")
check("ΔG of Haber process at 298 K (kJ)", gibbs_dG(-92.2, 298, -199), -32.9)
check("T where ΔG = 0 (K)", gibbs_T(-92.2, 0, -199), 463.)
check("spontaneity label, ΔG = −32.9", spontaneity(-32.9).startswith("Spontaneous"), True)
from thermodynamics import gibbs_from_K, K_from_gibbs  # ΔG° = −RT ln K
check("ΔG° from K = 1.00e3 at 298 K (kJ)", gibbs_from_K(1.00e3, 298), -17.1)
check("K from ΔG° = −32.9 kJ at 298 K", K_from_gibbs(-32.9, 298), 5.85e5)

# ─────────────────────────────────────────────────────────────────────────────
section("R2.2 / R2.3 Kinetics (HL)")
from kinetics import (determine_order, rate_constant_from_experiment, arrhenius_Ea,
                      arrhenius_k2, half_life_from_k, irl_concentration)

check("order when [A]×2 gives rate×4", determine_order(0.10, 0.20, 1.0e-3, 4.0e-3), 2.0, rel=1e-9)
check("order when [A]×2 gives no change", determine_order(0.10, 0.20, 1.0e-3, 1.0e-3), 0.0, rel=1e-9)
check("k for rate = k[A][B]²", rate_constant_from_experiment(2.0e-3, [0.10, 0.20], [1, 2]), 0.500)
check("Ea from k at 300 K and 320 K (kJ)", arrhenius_Ea(1.0e-3, 300, 4.0e-3, 320) / 1000, 55.3)
check("k2 at 320 K from Ea = 55.3 kJ", arrhenius_k2(1.0e-3, 300, 320, 55.3e3), 4.00e-3)
check("first-order half-life, k = 0.0231 s-1", half_life_from_k(0.0231), 30.0)
check("first-order [A] after 60 s, half-life 30 s", irl_concentration(1, 0.800, 0.0231, 60), 0.200)

# ─────────────────────────────────────────────────────────────────────────────
section("R2.3 Equilibrium")
from ice_solver import solve_ice, reaction_quotient, compare_Q_K, kc_to_kp

x = solve_ice([1, 1], [1.00, 1.00], [2], [0.00], 50.0)
check("H2 + I2 ⇌ 2HI, [HI]eq (Kc = 50.0)", 2 * x, 1.56)
x = solve_ice([1], [0.100], [2], [0.00], 4.6e-3)
check("N2O4 ⇌ 2NO2, [NO2]eq (Kc = 4.6e-3)", 2 * x, 0.0203)
x = solve_ice([1, 3], [1.00, 3.00], [2], [0.00], 0.500)
check("Haber ICE satisfies Kc", (2 * x) ** 2 / ((1 - x) * (3 - 3 * x) ** 3), 0.500, rel=1e-6)
q = reaction_quotient([1, 1], [0.20, 0.20], [2], [1.0])
check("Q for H2 + I2 ⇌ 2HI", q, 25.0)
check("Q < K shifts forward", compare_Q_K(q, 50.0)[0], "forward")
check("Kp from Kc, Δn = −2 at 500 K", kc_to_kp(0.500, 500, -2), 2.97e-4)

# ─────────────────────────────────────────────────────────────────────────────
section("R3.1 Proton transfer reactions")
from acid_base import (strong_acid_pH, strong_base_pH, weak_acid_pH, weak_base_pH,
                       pKa_to_Ka, Ka_to_Kb, H_from_pH, buffer_pH, all_four,
                       titration_find_concentration, identify)

check("pH of 0.0100 mol dm-3 HCl", strong_acid_pH(0.0100), 2.00)
check("pH of 0.0500 mol dm-3 NaOH", strong_base_pH(0.0500), 12.7)
check("[H+] at pH 3.50", H_from_pH(3.50), 3.16e-4)
check("pOH when pH = 4.20", all_four(pH=4.20)["pOH"] if isinstance(all_four(pH=4.20), dict)
      else all_four(pH=4.20)[1], 9.80)
check("Ka from pKa 4.76 (ethanoic acid)", pKa_to_Ka(4.76), 1.74e-5)
check("pH of 0.100 mol dm-3 ethanoic acid", weak_acid_pH(1.74e-5, 0.100)[0], 2.88)
check("pH of 0.100 mol dm-3 NH3 (Kb 1.78e-5)", weak_base_pH(1.78e-5, 0.100)[0], 11.1)
check("Kb of ethanoate", Ka_to_Kb(1.74e-5), 5.75e-10)
check("buffer pH, equal concentrations", buffer_pH(1.74e-5, 0.100, 0.100), 4.76)
check("buffer pH, [A-]/[HA] = 2", buffer_pH(1.74e-5, 0.100, 0.200), 5.06)
check("titration: 20.0 cm3 of 0.100 NaOH vs 25.0 cm3 HCl",
      titration_find_concentration(0.100 * 0.0200, 0.0250), 0.0800)
check("identify H2SO4", identify("H2SO4"), "Strong acid")
check("identify ethanoic acid", "acid" in identify("CH3COOH").lower(), True)
check("identify ammonia", "base" in identify("NH3").lower(), True)

# ─────────────────────────────────────────────────────────────────────────────
section("R3.2 Electron transfer reactions")
from oxidation_number_calculator import solve_oxidation_numbers as ox
from electrochemistry import cell_potential, gibbs_from_cell, faraday_mass
from constants import get_reduction_potential

for formula, charge, elem, want in [
    ("K2Cr2O7", 0, "Cr", 6), ("KMnO4", 0, "Mn", 7), ("S2O3", -2, "S", 2),
    ("NH4", 1, "N", -3), ("H2SO4", 0, "S", 6), ("Fe2O3", 0, "Fe", 3),
    ("C2O4", -2, "C", 3), ("ClO", -1, "Cl", 1), ("NO3", -1, "N", 5),
    ("H2O2", 0, "O", -1), ("NaH", 0, "H", -1), ("VO2", 1, "V", 5),
]:
    try:
        res = ox(formula, charge, peroxide=(formula == "H2O2"))
        check(f"oxidation state of {elem} in {formula} ({charge:+d})", res[elem], want)
    except Exception as e:
        check(f"oxidation state of {elem} in {formula} ({charge:+d})", str(e), want)

e_cell = cell_potential(get_reduction_potential("Cu2+/Cu"), get_reduction_potential("Zn2+/Zn"))
check("Daniell cell E° (V)", e_cell, 1.10)
check("ΔG° of Daniell cell (kJ)", gibbs_from_cell(2, e_cell), -212.)
check("Ag/Cu cell E° (V)", cell_potential(get_reduction_potential("Ag+/Ag"),
                                         get_reduction_potential("Cu2+/Cu")), 0.46)
# 3860 C = 0.0400 mol e-  ->  0.0200 mol Cu
check("mass of Cu from 2.00 A for 1930 s (g)", faraday_mass(2.00, 1930, 63.55, 2), 1.27)

# ─────────────────────────────────────────────────────────────────────────────
section("S2.1 / S2.2 Bonding")
from ionic_bonding_calculator import write_ionic_formula, classify_bond

check("formula Mg2+ + N3-", write_ionic_formula("Mg", 2, "N", -3), "Mg3N2")
check("formula Ca2+ + PO4 3-", write_ionic_formula("Ca", 2, "PO4", -3), "Ca3(PO4)2")
check("formula NH4+ + SO4 2-", write_ionic_formula("NH4", 1, "SO4", -2), "(NH4)2SO4")
check("formula Al3+ + O2-", write_ionic_formula("Al", 3, "O", -2), "Al2O3")
check("NaCl is ionic", classify_bond("Na", "Cl")[0], "Ionic")
check("HCl is polar covalent", classify_bond("H", "Cl")[0], "Polar Covalent")
check("Cl2 is non-polar", classify_bond("Cl", "Cl")[0], "Nonpolar Covalent")

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
section("S1.4 Solutions: concentration and dilution")
from solutions import (concentration, moles_from_concentration, volume_from_concentration,
                       concentration_from_mass, mass_for_solution, g_per_dm3_to_mol_per_dm3,
                       mol_per_dm3_to_g_per_dm3, dilution_solve, dilution_factor,
                       ppm_from_mass, volume_to_dm3)

check("0.0500 mol in 250 cm³", concentration(0.0500, volume_to_dm3(250, "cm3")), 0.200)
check("n in 25.0 cm³ of 0.100 mol dm⁻³", moles_from_concentration(0.100, volume_to_dm3(25.0, "cm3")), 2.50e-3)
check("volume of 0.0125 mol at 0.500 mol dm⁻³ (dm³)", volume_from_concentration(0.0125, 0.500), 0.0250)
check("5.85 g NaCl (58.44) in 500 cm³", concentration_from_mass(5.85, 58.44, 0.500), 0.200)
check("mass of NaCl for 250 cm³ of 0.100 mol dm⁻³", mass_for_solution(0.100, 0.250, 58.44), 1.461)
check("g dm⁻³ → mol dm⁻³ (NaCl)", g_per_dm3_to_mol_per_dm3(5.844, 58.44), 0.1000)
check("mol dm⁻³ → g dm⁻³ (NaCl)", mol_per_dm3_to_g_per_dm3(0.100, 58.44), 5.844)
check("dilution: V₁ of 2.00 for 100 cm³ of 0.250", dilution_solve("V1", c1=2.00, c2=0.250, V2=100), 12.5)
check("dilution: c₂ from 25.0 cm³ of 2.00 made up to 250 cm³",
      dilution_solve("c2", c1=2.00, V1=25.0, V2=250), 0.200)
check("dilution factor 2.00 → 0.250", dilution_factor(2.00, 0.250), 8.0)
check("5.0 mg in 2.0 dm³ = 2.5 ppm", ppm_from_mass(5.0, 2.0), 2.5)
check_raises("volume of zero rejected", lambda: concentration(1, 0), ValueError)
check_raises("unknown volume unit rejected", lambda: volume_to_dm3(1, "gallons"), ValueError)

section("S1.2 Isotopes and relative atomic mass")
from isotopes import relative_atomic_mass, abundance_from_Ar, percentage_abundances

check("Ar of chlorine", relative_atomic_mass([(34.969, 75.77), (36.966, 24.23)]), 35.45)
check("Ar of magnesium (3 isotopes)",
      relative_atomic_mass([(23.985, 78.99), (24.986, 10.00), (25.982, 11.01)]), 24.31)
check("Ar from peak heights (not %)", relative_atomic_mass([(10.013, 19.9), (11.009, 80.1)]), 10.81)
p1, p2 = abundance_from_Ar(63.546, 62.930, 64.928)
check("copper-63 abundance from Ar", p1, 69.17)
check("copper-65 abundance from Ar", p2, 30.83)
check("abundances add to 100 %", p1 + p2, 100.0, rel=1e-9)
check("peak heights converted to %", percentage_abundances([(10, 1), (11, 3)])[1], 75.0)
check_raises("Ar outside the isotope masses rejected",
             lambda: abundance_from_Ar(70.0, 62.930, 64.928), ValueError)
check_raises("one isotope is not enough", lambda: relative_atomic_mass([(12.0, 100)]), ValueError)

section("S1.4 Molecular formula and combustion analysis")
from Empirical_Formula_Calculator import molecular_formula, combustion_analysis

mol, n, emp_mass = molecular_formula({"C": 1, "H": 2, "O": 1}, 180.16)
check("CH₂O with Mr 180.16 → C₆H₁₂O₆", display_empirical_formula(mol), "C6H12O6")
check("  multiplier n = 6", n, 6)
check("  empirical formula mass", emp_mass, 30.03)
check("CH with Mr 78.11 → C₆H₆",
      display_empirical_formula(molecular_formula({"C": 1, "H": 1}, 78.11)[0]), "C6H6")
check("NO₂ with Mr 92.02 → N₂O₄",
      display_empirical_formula(molecular_formula({"N": 1, "O": 2}, 92.02)[0]), "N2O4")
check_raises("Mr smaller than the empirical mass rejected",
             lambda: molecular_formula({"C": 1, "H": 2, "O": 1}, 12.0), ValueError)

els, masses, notes = combustion_analysis(0.2641, 0.1081, 0.1802)
check("combustion: 0.2641 g CO₂ + 0.1081 g H₂O from 0.1802 g → CH₂O",
      display_empirical_formula(calculate_empirical_formula(els, masses)), "CH2O")
els, masses, notes = combustion_analysis(1.3203, 0.2702, 0.3906)
check("combustion of a hydrocarbon → CH (no oxygen)",
      display_empirical_formula(calculate_empirical_formula(els, masses)), "CH")
check("  and it says the compound has no oxygen", bool(notes), True)
check_raises("C and H heavier than the sample is rejected",
             lambda: combustion_analysis(1.0, 1.0, 0.1), ValueError)

section("Tools: uncertainties and significant figures")
from uncertainties import (percentage_uncertainty, absolute_uncertainty, combine_add_subtract,
                           combine_multiply_divide, power_uncertainty, percentage_error,
                           round_to_sig_figs, sig_figs_of, format_with_uncertainty)

check("25.00 ± 0.05 is 0.2 %", percentage_uncertainty(25.00, 0.05), 0.200)
check("0.2 % of 25.00 is ± 0.05", absolute_uncertainty(25.00, 0.2), 0.0500)
r, a, p = combine_add_subtract([24.80, -1.20], [0.05, 0.05])
check("subtracting burette readings: value", r, 23.60)
check("  absolute uncertainties add", a, 0.100)
r, a, p = combine_multiply_divide([0.100, 25.0], [0.5, 0.2])
check("multiplying: value", r, 2.50)
check("  percentage uncertainties add", p, 0.700)
check("  absolute uncertainty", a, 0.0175)
r, a, p = power_uncertainty(2.50, 1.2, 2)
check("squaring doubles the % uncertainty", p, 2.40)
check("  value squared", r, 6.25)
check("percentage error vs accepted value", percentage_error(1.23, 1.20), 2.50)
check("round 0.0824567 to 3 s.f.", round_to_sig_figs(0.0824567, 3), 0.0825)
check("round 1234 to 2 s.f.", round_to_sig_figs(1234, 2), 1200.0)
check("significant figures of '0.00420'", sig_figs_of("0.00420"), 3)
check("significant figures of '1.0e3'", sig_figs_of("1.0e3"), 2)
check("written with its uncertainty", format_with_uncertainty(0.08245, 0.0005), "0.0824 ± 0.0005")
check_raises("negative uncertainty rejected", lambda: percentage_uncertainty(1.0, -0.1), ValueError)

section("R1.4 Entropy from standard entropies")
from thermodynamics import standard_entropy_rxn

check("ΔS° of the Haber process", standard_entropy_rxn([
    {"formula": "N2", "S": 191.6, "coeff": 1, "role": "reactant"},
    {"formula": "H2", "S": 130.7, "coeff": 3, "role": "reactant"},
    {"formula": "NH3", "S": 192.5, "coeff": 2, "role": "product"}]), -198.7, rel=1e-3)
check("ΔS° of CaCO₃ → CaO + CO₂ (gas made, so positive)", standard_entropy_rxn([
    {"formula": "CaCO3", "S": 92.9, "coeff": 1, "role": "reactant"},
    {"formula": "CaO", "S": 39.7, "coeff": 1, "role": "product"},
    {"formula": "CO2", "S": 213.7, "coeff": 1, "role": "product"}]), 160.5, rel=1e-3)

section("R2.2 Arrhenius from a graph of ln k against 1/T")
from kinetics import arrhenius_from_data
_Ea, _A = 52_000.0, 3.5e8          # build data from a known Ea and A
_temps = [290, 300, 310, 320, 330]
_ks = [_A * math.exp(-_Ea / (8.314 * T)) for T in _temps]
_fit = arrhenius_from_data(_temps, _ks)
check("Ea recovered from the graph (kJ/mol)", _fit["Ea_kJ"], _Ea / 1000, rel=1e-3)
check("A recovered from the intercept", _fit["A"] / _A, 1.0, rel=1e-3)
check("straight line, r² = 1", _fit["r2"], 1.0, rel=1e-6)
check_raises("a single point is not a graph", lambda: arrhenius_from_data([300], [1e-3]), ValueError)
check_raises("all temperatures the same is rejected",
             lambda: arrhenius_from_data([300, 300], [1e-3, 2e-3]), ValueError)

section("R3.1 Salt solutions and pKa from half-equivalence")
from acid_base import salt_pH, pKa_from_half_equivalence

check("0.100 mol dm⁻³ CH₃COONa is basic", salt_pH("weak_acid_salt", 1.74e-5, 0.100)[0], 8.88)
check("0.100 mol dm⁻³ NH₄Cl is acidic", salt_pH("weak_base_salt", 1.78e-5, 0.100)[0], 5.13)
check("  Kb of ethanoate = Kw/Ka", salt_pH("weak_acid_salt", 1.74e-5, 0.100)[1], 5.747e-10)
check("pKa from pH at half-equivalence", pKa_from_half_equivalence(4.76)[0], 4.76)
check("  and the Ka that goes with it", pKa_from_half_equivalence(4.76)[1], 1.738e-5)
check_raises("salt kind must be given", lambda: salt_pH("something", 1e-5, 0.1), ValueError)

section("S1.3 Electron configuration")
from electron_config import electron_configuration, noble_gas_shorthand, valence_electrons

check("carbon", electron_configuration("C")[0], "1s² 2s² 2p²")
check("calcium", electron_configuration("Ca")[0], "1s² 2s² 2p⁶ 3s² 3p⁶ 4s²")
check("iron", electron_configuration("Fe")[0], "1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁶ 4s²")
check("chromium is an exception (3d⁵ 4s¹)", electron_configuration("Cr")[0],
      "1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁵ 4s¹")
check("copper is an exception (3d¹⁰ 4s¹)", electron_configuration("Cu")[0],
      "1s² 2s² 2p⁶ 3s² 3p⁶ 3d¹⁰ 4s¹")
check("Fe²⁺ loses the 4s electrons first", electron_configuration("Fe", 2)[0],
      "1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁶")
check("Fe³⁺ is 3d⁵", electron_configuration("Fe", 3)[0], "1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁵")
check("Cl⁻ has the argon configuration", electron_configuration("Cl", -1)[0],
      electron_configuration("Ar")[0])
check("Na⁺ has the neon configuration", electron_configuration("Na", 1)[0],
      electron_configuration("Ne")[0])
check("shorthand for iron", noble_gas_shorthand("Fe"), "[Ar] 3d⁶ 4s²")
check("shorthand for bromine", noble_gas_shorthand("Br"), "[Ar] 3d¹⁰ 4s² 4p⁵")
check("by name and by atomic number agree",
      electron_configuration("iron")[0], electron_configuration(26)[0])
check("chlorine has 7 outer electrons", valence_electrons("Cl")[0], 7)
check_raises("unknown element rejected", lambda: electron_configuration("Xx"), ValueError)
check_raises("removing more electrons than it has is rejected",
             lambda: electron_configuration("H", 2), ValueError)

section("S3.2 Index of hydrogen deficiency")
from organic_tools import index_of_hydrogen_deficiency as IHD

for formula, want in [("C6H6", 4), ("C6H14", 0), ("C6H12", 1), ("C2H4", 1), ("C2H2", 2),
                      ("C3H6O", 1), ("C6H5Cl", 4), ("C6H5NO2", 5), ("C8H10N4O2", 6),
                      ("C9H8O4", 6), ("CH4", 0), ("C4H6", 2)]:
    check(f"IHD of {formula}", IHD(formula), want)
check_raises("too many hydrogens rejected", lambda: IHD("C2H10"), ValueError)
check_raises("a formula with no carbon is rejected", lambda: IHD("H2O"), ValueError)

print("\n" + "=" * 60)
print(f"  IB tests  Total: {PASS + FAIL}   Passed: {PASS}   Failed: {FAIL}")
if FAILURES:
    print("\nFailures:")
    print("\n".join(FAILURES))
sys.exit(1 if FAIL else 0)
