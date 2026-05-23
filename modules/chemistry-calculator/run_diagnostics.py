"""
Rigorous diagnostic test suite for all chemistry calculator modules.
Runs fully automatically — no user input needed.
"""

import sys, os, math, traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0
ERRORS = []

def check(label, got, expected, tol=1e-6):
    global PASS, FAIL
    if isinstance(expected, float):
        ok = abs(got - expected) <= tol
    else:
        ok = (got == expected)
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL += 1
        msg = f"  [FAIL] {label}\n         got={got!r}  expected={expected!r}"
        ERRORS.append(msg)
        print(msg)
    else:
        PASS += 1
        print(f"  [PASS] {label}")

def check_raises(label, fn, exc_type=Exception):
    global PASS, FAIL
    try:
        fn()
        FAIL += 1
        msg = f"  [FAIL] {label}  — expected {exc_type.__name__} but no exception raised"
        ERRORS.append(msg)
        print(msg)
    except exc_type:
        PASS += 1
        print(f"  [PASS] {label}  (raised {exc_type.__name__} as expected)")
    except Exception as e:
        FAIL += 1
        msg = f"  [FAIL] {label}  — raised {type(e).__name__}: {e}"
        ERRORS.append(msg)
        print(msg)

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ─────────────────────────────────────────────────────────────
# 1. MOLE CONVERSIONS
# ─────────────────────────────────────────────────────────────
section("1. MOLE CONVERSIONS")
from mole_conversions import (
    mass_to_moles, moles_to_mass, moles_to_particles,
    particles_to_moles, moles_to_volume, volume_to_moles,
    Avogrado_number, Molar_Volume_At_STP
)

check("mass_to_moles: 18g water (MM=18)",   mass_to_moles(18, 18),    1.0)
check("mass_to_moles: 44g CO2 (MM=44)",     mass_to_moles(44, 44),    1.0)
check("moles_to_mass: 2 mol × 18 g/mol",    moles_to_mass(2, 18),     36.0)
check("moles_to_particles: 1 mol",          moles_to_particles(1),    6.022e23)
check("particles_to_moles: Avogadro num",   particles_to_moles(6.022e23), 1.0)
check("moles_to_volume: 1 mol at STP",      moles_to_volume(1),       22.4)
check("moles_to_volume: 2 mol at STP",      moles_to_volume(2),       44.8)
check("volume_to_moles: 22.4 L at STP",     volume_to_moles(22.4),    1.0)
check("volume_to_moles: 11.2 L at STP",     volume_to_moles(11.2),    0.5)
# roundtrip
check("roundtrip mass→moles→mass",
      moles_to_mass(mass_to_moles(100, 58.44), 58.44), 100.0, tol=1e-9)

# ─────────────────────────────────────────────────────────────
# 2. EMPIRICAL FORMULA
# ─────────────────────────────────────────────────────────────
section("2. EMPIRICAL FORMULA CALCULATOR")
from Empirical_Formula_Calculator import calculate_empirical_formula, display_empirical_formula

# Water H2O: H=2g, O=16g → ratio H:O = 2:1
ef = calculate_empirical_formula(['H', 'O'], [2.0, 16.0])
check("H2O empirical formula H count", ef['H'], 2)
check("H2O empirical formula O count", ef['O'], 1)

# CH4: C=12, H=4 → C1H4
ef2 = calculate_empirical_formula(['C', 'H'], [12.0, 4.0])
check("CH4 empirical formula C count", ef2['C'], 1)
check("CH4 empirical formula H count", ef2['H'], 4)

# Glucose C6H12O6 from percents: C=40%, H=6.67%, O=53.33%
ef3 = calculate_empirical_formula(['C', 'H', 'O'], [40.0, 6.72, 53.28])
check("Glucose empirical (CH2O): C", ef3['C'], 1)
check("Glucose empirical (CH2O): H", ef3['H'], 2)
check("Glucose empirical (CH2O): O", ef3['O'], 1)

# display
check("display CH4", display_empirical_formula({'C':1,'H':4}), "CH4")
check("display NaCl", display_empirical_formula({'Na':1,'Cl':1}), "NaCl")

# unknown element should raise
check_raises("Unknown element raises ValueError",
             lambda: calculate_empirical_formula(['X'], [10.0]), ValueError)

# ─────────────────────────────────────────────────────────────
# 3. PERCENT COMPOSITION
# ─────────────────────────────────────────────────────────────
section("3. PERCENT COMPOSITION CALCULATOR")
from percent_composition_calculator import compute_percent_composition, parse_formula

# H2O: H~11.19%, O~88.81%
mm, pcts = compute_percent_composition("H2O")
check("H2O molar mass ≈18.015", mm, 18.015, tol=0.01)
check("H2O %H ≈11.19", pcts['H'], 11.19, tol=0.1)
check("H2O %O ≈88.81", pcts['O'], 88.81, tol=0.1)

# NaCl: Na~39.34%, Cl~60.66%
mm2, pcts2 = compute_percent_composition("NaCl")
check("NaCl molar mass ≈58.44", mm2, 58.44, tol=0.01)
check("NaCl %Na ≈39.34", pcts2['Na'], 39.34, tol=0.1)
check("NaCl %Cl ≈60.66", pcts2['Cl'], 60.66, tol=0.1)

# Ca(OH)2
mm3, pcts3 = compute_percent_composition("Ca(OH)2")
check("Ca(OH)2 molar mass ≈74.093", mm3, 74.093, tol=0.01)

# Nested parens: Al2(SO4)3
mm4, pcts4 = compute_percent_composition("Al2(SO4)3")
check("Al2(SO4)3 molar mass ≈342.15", mm4, 342.15, tol=0.1)

# Percents sum to 100
pct_sum = sum(pcts.values())
check("H2O percents sum to 100", pct_sum, 100.0, tol=0.01)

# parse_formula roundtrip
atoms = parse_formula("C6H12O6")
check("C6H12O6 C count", atoms['C'], 6)
check("C6H12O6 H count", atoms['H'], 12)
check("C6H12O6 O count", atoms['O'], 6)

# Bad formula
check_raises("Bad formula raises FormulaError",
             lambda: parse_formula("Xy3"), Exception)

# ─────────────────────────────────────────────────────────────
# 4. VOLUME-MASS CONVERSIONS
# ─────────────────────────────────────────────────────────────
section("4. VOLUME-MASS CONVERSIONS")
from volume_mass_conversions import mass_to_volume, volume_to_mass, density_from_mv

check("mass_to_volume: 100g, d=2 g/mL → 50 mL",  mass_to_volume(100, 2),   50.0)
check("volume_to_mass: 50 mL, d=2 g/mL → 100 g", volume_to_mass(50, 2),    100.0)
check("density_from_mv: 200g, 100 mL → 2 g/mL",  density_from_mv(200, 100), 2.0)
check("density_from_mv: water 18g/18mL → 1 g/mL", density_from_mv(18, 18),  1.0)
# roundtrip
check("roundtrip mass→vol→mass",
      volume_to_mass(mass_to_volume(150, 3.5), 3.5), 150.0, tol=1e-9)

# ─────────────────────────────────────────────────────────────
# 5. OXIDATION NUMBER CALCULATOR
# ─────────────────────────────────────────────────────────────
section("5. OXIDATION NUMBER CALCULATOR")
from oxidation_number_calculator import solve_oxidation_numbers

# Pure element: O2
res = solve_oxidation_numbers("O2")
check("O2 pure element → 0", res['O'], 0)

# NaCl: Na=+1, Cl=-1
res = solve_oxidation_numbers("NaCl")
check("NaCl Na=+1", res['Na'], 1)
check("NaCl Cl=-1", res['Cl'], -1)

# H2O: H=+1, O=-2
res = solve_oxidation_numbers("H2O")
check("H2O H=+1", res['H'], 1)
check("H2O O=-2", res['O'], -2)

# KMnO4: Mn should be +7
res = solve_oxidation_numbers("KMnO4")
check("KMnO4 K=+1", res['K'], 1)
check("KMnO4 O=-2", res['O'], -2)
check("KMnO4 Mn=+7", res['Mn'], 7)

# H2SO4: S should be +6
res = solve_oxidation_numbers("H2SO4")
check("H2SO4 S=+6", res['S'], 6)

# Cr2O3: Cr should be +3
res = solve_oxidation_numbers("Cr2O3")
check("Cr2O3 Cr=+3", res['Cr'], 3)

# Peroxide H2O2: O=-1
res = solve_oxidation_numbers("H2O2", peroxide=True)
check("H2O2 peroxide O=-1", res['O'], -1)

# Ion MnO4- (charge=-1): Mn=+7
res = solve_oxidation_numbers("MnO4", charge=-1)
check("MnO4- Mn=+7", res['Mn'], 7)

# Verification: sum of (ox × count) must equal charge
from percent_composition_calculator import parse_formula as _pf
res = solve_oxidation_numbers("H2SO4")
counts = _pf("H2SO4")
total = sum(res[e] * counts[e] for e in counts)
check("H2SO4 oxidation sum = 0", total, 0, tol=0.01)

# ─────────────────────────────────────────────────────────────
# 6. ATOM ECONOMY
# ─────────────────────────────────────────────────────────────
section("6. ATOM ECONOMY (ELEMENT ECONOMY) CALCULATOR")
from atom_economy_calculator import calculate_atom_economy, get_molar_mass

# CH4 + 2 O2 -> CO2 + 2 H2O  (desired: H2O)
# Reactants: CH4(1) + O2(2) = 16.043 + 64.000 = 80.043
# H2O desired: 18.015 × 2 = 36.030
# AE = 36.030/80.043 × 100 ≈ 45.01%
ae, mw_d, mw_r = calculate_atom_economy(['CH4','O2'], [1,2], 'H2O', 2)
check("CH4+O2→H2O atom economy ≈45%", ae, 45.01, tol=0.5)

# H2 + Cl2 -> 2 HCl  (desired: HCl) — 100% AE (only one product)
ae2, _, _ = calculate_atom_economy(['H2','Cl2'], [1,1], 'HCl', 2)
check("H2+Cl2→HCl atom economy =100%", ae2, 100.0, tol=0.1)

# Molar mass checks
check("get_molar_mass H2O ≈18.015", get_molar_mass("H2O"), 18.015, tol=0.01)
check("get_molar_mass NaCl ≈58.44", get_molar_mass("NaCl"), 58.44, tol=0.01)
check("get_molar_mass CO2 ≈44.01",  get_molar_mass("CO2"),  44.01,  tol=0.01)

# ─────────────────────────────────────────────────────────────
# 7. IONIC BONDING CALCULATOR
# ─────────────────────────────────────────────────────────────
section("7. IONIC BONDING CALCULATOR")
from ionic_bonding_calculator import classify_bond, write_ionic_formula

# Na-Cl: EN diff = 3.16-0.93 = 2.23 → Ionic
bt, en1, en2, diff = classify_bond('Na', 'Cl')
check("Na-Cl bond type = Ionic", bt, "Ionic")
check("Na-Cl EN diff ≈2.23", diff, 2.23, tol=0.01)

# H-O: EN diff = 3.44-2.20 = 1.24 → Polar Covalent
bt2, _, _, diff2 = classify_bond('H', 'O')
check("H-O bond type = Polar Covalent", bt2, "Polar Covalent")
check("H-O EN diff ≈1.24", diff2, 1.24, tol=0.01)

# C-H: EN diff = 2.55-2.20 = 0.35 → Nonpolar Covalent
bt3, _, _, diff3 = classify_bond('C', 'H')
check("C-H bond type = Nonpolar Covalent", bt3, "Nonpolar Covalent")

# write_ionic_formula
check("CaCl2 formula", write_ionic_formula('Ca', 2, 'Cl', -1), "CaCl2")
check("NaCl formula",  write_ionic_formula('Na', 1, 'Cl', -1), "NaCl")
check("Al2O3 formula", write_ionic_formula('Al', 3, 'O',  -2), "Al2O3")
check("MgO formula",   write_ionic_formula('Mg', 2, 'O',  -2), "MgO")
check("Fe2O3 formula", write_ionic_formula('Fe', 3, 'O',  -2), "Fe2O3")

# Invalid charge should raise
check_raises("write_ionic_formula bad cation charge raises",
             lambda: write_ionic_formula('Na', -1, 'Cl', -1), ValueError)

# ─────────────────────────────────────────────────────────────
# 8. PERCENTAGE YIELD
# ─────────────────────────────────────────────────────────────
section("8. PERCENTAGE YIELD CALCULATOR")
from percentage_yield_calculator import (
    calc_percentage_yield, calc_actual_yield, calc_theoretical_yield
)

check("% yield: 18/20 = 90%",  calc_percentage_yield(18, 20), 90.0)
check("% yield: 20/20 = 100%", calc_percentage_yield(20, 20), 100.0)
check("% yield: 25/20 = 125%", calc_percentage_yield(25, 20), 125.0)

check("actual yield: 90%, 20g theoretical → 18g",
      calc_actual_yield(90, 20), 18.0)
check("theoretical yield: 18g actual, 90% → 20g",
      calc_theoretical_yield(18, 90), 20.0)

# roundtrip
pct = calc_percentage_yield(7.3, 12.5)
check("roundtrip % yield → theoretical",
      calc_theoretical_yield(7.3, pct), 12.5, tol=1e-9)

# ─────────────────────────────────────────────────────────────
# 9. GAS LAWS
# ─────────────────────────────────────────────────────────────
section("9. GAS LAWS")
from gas_laws import (
    ideal_gas_find_P, ideal_gas_find_V, ideal_gas_find_n, ideal_gas_find_T,
    combined_gas_find_P2, combined_gas_find_V2, combined_gas_find_T2,
    moles_to_volume_stp, volume_to_moles_stp, molar_volume_nonstandard,
    graham_rate_ratio, graham_find_M2, graham_find_M1,
    dalton_total_pressure, dalton_partial_pressure, dalton_mole_fraction, R
)

# Ideal gas: PV = nRT
# 1 mol at STP: P=1 atm, T=273.15 K → V ≈ 22.41 L
V_stp = ideal_gas_find_V(1, 273.15, 1.0)
check("Ideal gas: V of 1 mol at STP ≈22.41 L", V_stp, 22.41, tol=0.02)

# Find P: n=2, V=10, T=300 → P = 2*R*300/10
P_calc = ideal_gas_find_P(2, 10, 300)
check("Ideal gas find P", P_calc, 2*R*300/10, tol=1e-8)

# Find n: P=1, V=22.41, T=273.15 → n ≈ 1
n_calc = ideal_gas_find_n(1.0, V_stp, 273.15)
check("Ideal gas find n ≈ 1 mol", n_calc, 1.0, tol=0.001)

# Find T: P=1, V=22.41, n=1 → T ≈ 273.15
T_calc = ideal_gas_find_T(1.0, V_stp, 1.0)
check("Ideal gas find T ≈ 273.15 K", T_calc, 273.15, tol=0.01)

# Combined gas law: P1V1/T1 = P2V2/T2
# P1=1, V1=10, T1=300, V2=5, T2=300 → P2 = 2
P2 = combined_gas_find_P2(1, 10, 300, 5, 300)
check("Combined gas: P2 = 2 atm", P2, 2.0, tol=1e-9)

# V2: P1=2, V1=5, T1=300, P2=1, T2=300 → V2 = 10
V2 = combined_gas_find_V2(2, 5, 300, 1, 300)
check("Combined gas: V2 = 10 L", V2, 10.0, tol=1e-9)

# T2: P1=1, V1=10, T1=300, P2=2, V2=10 → T2 = 600
T2 = combined_gas_find_T2(1, 10, 300, 2, 10)
check("Combined gas: T2 = 600 K", T2, 600.0, tol=1e-9)

# Molar volume
check("moles_to_volume_stp: 2 mol → 44.8 L", moles_to_volume_stp(2), 44.8)
check("volume_to_moles_stp: 11.2 L → 0.5 mol", volume_to_moles_stp(11.2), 0.5)
check("molar_volume_nonstandard: T=273.15, P=1 ≈22.41",
      molar_volume_nonstandard(273.15, 1.0), 22.41, tol=0.02)

# Graham's law: H2 (M=2) vs O2 (M=32) → ratio = sqrt(32/2) = 4
ratio = graham_rate_ratio(2, 32)
check("Graham H2/O2 rate ratio = 4.0", ratio, 4.0, tol=1e-9)

# Find M2 given M1=2, ratio=4 → M2 = 2*16 = 32
M2 = graham_find_M2(2, 4)
check("Graham find M2 = 32", M2, 32.0, tol=1e-9)

# Find M1 given M2=32, ratio=4 → M1 = 32/16 = 2
M1 = graham_find_M1(32, 4)
check("Graham find M1 = 2", M1, 2.0, tol=1e-9)

# Dalton's law
check("Dalton total: [0.3, 0.5, 0.2] = 1.0 atm",
      dalton_total_pressure([0.3, 0.5, 0.2]), 1.0, tol=1e-9)
check("Dalton partial: P=1, x=0.3 → 0.3 atm",
      dalton_partial_pressure(1.0, 0.3), 0.3, tol=1e-9)
check("Dalton mole fraction: 0.5 mol / 2 mol = 0.25",
      dalton_mole_fraction(0.5, 2.0), 0.25, tol=1e-9)

# ─────────────────────────────────────────────────────────────
# 10. ACID-BASE
# ─────────────────────────────────────────────────────────────
section("10. ACID-BASE CALCULATOR")
from acid_base import (
    all_four, strong_acid_pH, strong_base_pH,
    weak_acid_pH, weak_base_pH,
    Ka_to_pKa, pKa_to_Ka, Kb_to_pKb, pKb_to_Kb, Ka_to_Kb, Kb_to_Ka,
    buffer_pH, buffer_ratio, identify, Kw,
    equivalence_moles, titration_find_concentration, titration_find_volume,
    equivalence_point_pH_description
)

# pH/pOH/[H+]/[OH-] conversions
pH, pOH, H, OH = all_four(pH=7.0)
check("pH=7: pOH=7",          pOH,  7.0,    tol=1e-9)
check("pH=7: [H+]=1e-7",      H,    1e-7,   tol=1e-15)
check("pH=7: [OH-]=1e-7",     OH,   1e-7,   tol=1e-15)

pH2, pOH2, H2, OH2 = all_four(pOH=4.0)
check("pOH=4: pH=10",         pH2,  10.0,   tol=1e-9)

pH3, pOH3, H3, OH3 = all_four(H=1e-3)
check("[H+]=1e-3: pH=3",      pH3,  3.0,    tol=1e-9)
check("[H+]=1e-3: pOH=11",    pOH3, 11.0,   tol=1e-9)

pH4, pOH4, H4, OH4 = all_four(OH=1e-5)
check("[OH-]=1e-5: pOH=5",    pOH4, 5.0,    tol=1e-9)
check("[OH-]=1e-5: pH=9",     pH4,  9.0,    tol=1e-9)

# pH + pOH = 14 invariant
for test_pH in [0.0, 3.5, 7.0, 10.2, 14.0]:
    ph_, poh_, _, _ = all_four(pH=test_pH)
    check(f"pH+pOH=14 at pH={test_pH}", ph_ + poh_, 14.0, tol=1e-9)

# Strong acid
check("Strong acid 0.1 mol/L HCl → pH=1", strong_acid_pH(0.1), 1.0, tol=1e-9)
check("Strong acid 0.01 mol/L → pH=2",    strong_acid_pH(0.01), 2.0, tol=1e-9)
check_raises("Strong acid C<=0 raises",    lambda: strong_acid_pH(0), ValueError)

# Strong base
check("Strong base 0.1 mol/L NaOH → pH=13", strong_base_pH(0.1), 13.0, tol=1e-9)
check("Strong base 0.01 mol/L → pH=12",     strong_base_pH(0.01), 12.0, tol=1e-9)

# Weak acid: acetic acid Ka=1.8e-5, C=0.1 mol/L
# [H+] = sqrt(1.8e-5 * 0.1) = sqrt(1.8e-6) ≈ 1.342e-3
# pH ≈ 2.872
# x/C = 1.342e-3/0.1 = 1.34% < 5% → approximation valid
pH_wa, used_approx, x_wa = weak_acid_pH(1.8e-5, 0.1)
check("Weak acid acetic: pH ≈ 2.872", pH_wa, 2.872, tol=0.005)
check("Weak acid acetic: used approx", used_approx, True)
check("Weak acid acetic: [H+] ≈ 1.342e-3", x_wa, math.sqrt(1.8e-5 * 0.1), tol=1e-8)

# Weak acid: large Ka forces quadratic
# Ka=0.01, C=0.05 → x_approx = sqrt(5e-4)=0.02236, x/C = 44.7% → quadratic
pH_waq, used_approxq, x_waq = weak_acid_pH(0.01, 0.05)
check("Weak acid high Ka: NOT approx (quadratic)", used_approxq, False)
# Verify quadratic: x^2 + 0.01x - 0.0005 = 0 → x = (-0.01 + sqrt(0.0001+0.002))/2
disc = 0.01**2 + 4*0.01*0.05
x_expected = (-0.01 + math.sqrt(disc)) / 2
check("Weak acid quadratic [H+]", x_waq, x_expected, tol=1e-10)

# Weak base: ammonia Kb=1.8e-5, C=0.1
pH_wb, approx_wb, x_wb = weak_base_pH(1.8e-5, 0.1)
check("Weak base ammonia: pH ≈ 11.128", pH_wb, 11.128, tol=0.005)
check("Weak base: used approx", approx_wb, True)

# Ka/Kb/pKa/pKb
check("Ka_to_pKa: 1.8e-5 ≈ 4.745", Ka_to_pKa(1.8e-5), 4.745, tol=0.001)
check("pKa_to_Ka roundtrip",        pKa_to_Ka(Ka_to_pKa(1.8e-5)), 1.8e-5, tol=1e-8)
check("Ka*Kb = Kw",                 1.8e-5 * Ka_to_Kb(1.8e-5), Kw, tol=1e-20)
check("Kb_to_Ka roundtrip",         Kb_to_Ka(Ka_to_Kb(1.8e-5)), 1.8e-5, tol=1e-20)
check("pKa + pKb = 14",
      Ka_to_pKa(1.8e-5) + Kb_to_pKb(Ka_to_Kb(1.8e-5)), 14.0, tol=0.001)

# Henderson-Hasselbalch buffer
# Ka=1.8e-5, [HA]=0.1, [A-]=0.1 → pH = pKa
pH_buf = buffer_pH(1.8e-5, 0.1, 0.1)
check("Buffer equal concentrations: pH = pKa", pH_buf, Ka_to_pKa(1.8e-5), tol=1e-9)

# [A-]/[HA] = 10 → pH = pKa + 1
pH_buf2 = buffer_pH(1.8e-5, 0.1, 1.0)
check("Buffer [A-]/[HA]=10: pH = pKa+1", pH_buf2, Ka_to_pKa(1.8e-5)+1, tol=1e-9)

# buffer_ratio
ratio_buf = buffer_ratio(1.8e-5, Ka_to_pKa(1.8e-5))
check("buffer_ratio at target=pKa → ratio=1", ratio_buf, 1.0, tol=1e-9)

# Acid/base identifier
check("HCl = Strong acid",   identify("HCl"),     "Strong acid")
check("NaOH = Strong base",  identify("NaOH"),    "Strong base")
check("H2O = Amphoteric",    identify("H2O"),     "Amphoteric")
check("NaCl = Neutral salt", identify("NaCl"),    "Neutral salt")
check("H2SO4 = Strong acid", identify("H2SO4"),   "Strong acid")
check("Ba(OH)2 = Strong base", identify("Ba(OH)2"), "Strong base")

# Titration
n_eq = equivalence_moles(0.1, 0.025)  # 0.1 mol/L × 0.025 L = 0.0025 mol
check("Titration: equivalence moles = 0.0025", n_eq, 0.0025, tol=1e-9)
C_unk = titration_find_concentration(n_eq, 0.025)
check("Titration: unknown C = 0.1 mol/L", C_unk, 0.1, tol=1e-9)
V_tit = titration_find_volume(n_eq, 0.1)
check("Titration: volume needed = 0.025 L", V_tit, 0.025, tol=1e-9)

# Equivalence point descriptions
desc_ss = equivalence_point_pH_description("strong acid", "strong base")
check("Strong/strong eq. point = pH 7", "pH ≈ 7" in desc_ss, True)
desc_ws = equivalence_point_pH_description("weak acid", "strong base")
check("Weak acid/strong base eq. point > 7", "pH > 7" in desc_ws, True)
desc_sw = equivalence_point_pH_description("strong acid", "weak base")
check("Strong acid/weak base eq. point < 7", "pH < 7" in desc_sw, True)

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  DIAGNOSTIC COMPLETE")
print(f"{'='*60}")
print(f"  Total tests : {PASS + FAIL}")
print(f"  Passed      : {PASS}")
print(f"  Failed      : {FAIL}")
if ERRORS:
    print(f"\nFailed tests:")
    for e in ERRORS:
        print(e)
else:
    print("\n  All tests passed!")
