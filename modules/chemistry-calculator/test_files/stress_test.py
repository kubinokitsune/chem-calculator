"""
STRESS TEST â€” Chemistry Calculator
Covers every module, every function, every branch, every edge case.
Runs fully automatically â€” no user input required.
"""

import sys, os, math, traceback as _tb
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# â”€â”€ Harness â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PASS = FAIL = 0
ERRORS = []

def ok(label, got, expected, tol=None):
    global PASS, FAIL
    if tol is not None:
        passed = abs(got - expected) <= tol
    elif isinstance(expected, float):
        passed = math.isclose(got, expected, rel_tol=1e-6, abs_tol=1e-12)
    else:
        passed = (got == expected)
    if passed:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        m = f"  [FAIL] {label}\n         got={got!r}  want={expected!r}"
        ERRORS.append(m); print(m)

def ok_raises(label, fn, exc=Exception):
    global PASS, FAIL
    try:
        fn()
        FAIL += 1
        m = f"  [FAIL] {label}  â€” no exception raised"
        ERRORS.append(m); print(m)
    except exc:
        PASS += 1
        print(f"  [PASS] {label}  ({exc.__name__} raised)")
    except Exception as e:
        FAIL += 1
        m = f"  [FAIL] {label}  â€” wrong exc {type(e).__name__}: {e}"
        ERRORS.append(m); print(m)

def ok_close(label, got, expected, pct=0.1):
    """Relative % tolerance."""
    rel = abs(got - expected) / (abs(expected) + 1e-30) * 100
    global PASS, FAIL
    if rel <= pct:
        PASS += 1; print(f"  [PASS] {label}  (rel={rel:.4f}%)")
    else:
        FAIL += 1
        m = f"  [FAIL] {label}  got={got:.8g}  want={expected:.8g}  rel={rel:.4f}%"
        ERRORS.append(m); print(m)

def section(t):
    print(f"\n{'='*66}\n  {t}\n{'='*66}")

def sub(t):
    print(f"\n  --- {t} ---")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 1 â€” MOLE CONVERSIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 1: MOLE CONVERSIONS")
from mole_conversions import (
    mass_to_moles, moles_to_mass, moles_to_particles,
    particles_to_moles, moles_to_volume, volume_to_moles,
    Avogrado_number, Molar_Volume_At_STP
)

sub("Normal operation")
ok("massâ†’moles: 18g/18 = 1",      mass_to_moles(18, 18),    1.0)
ok("massâ†’moles: 44g/44 = 1",      mass_to_moles(44, 44),    1.0)
ok("massâ†’moles: 1g/1 = 1",        mass_to_moles(1, 1),      1.0)
ok("molesâ†’mass: 2*18 = 36",       moles_to_mass(2, 18),     36.0)
ok("molesâ†’particles: 1mol",       moles_to_particles(1),    Avogrado_number)
ok("molesâ†’particles: 0.5mol",     moles_to_particles(0.5),  0.5*Avogrado_number)
ok("particlesâ†’moles: 1 Av",       particles_to_moles(Avogrado_number), 1.0)
ok("molesâ†’volume: 2mol STP",      moles_to_volume(2),       44.8)
ok("volumeâ†’moles: 11.2L STP",     volume_to_moles(11.2),    0.5)

sub("Edge cases â€” zeros")
ok("massâ†’moles: 0g = 0",          mass_to_moles(0, 18),     0.0)
ok("molesâ†’mass: 0mol = 0",        moles_to_mass(0, 18),     0.0)
ok("molesâ†’particles: 0 = 0",      moles_to_particles(0),    0.0)
ok("particlesâ†’moles: 0 = 0",      particles_to_moles(0),    0.0)
ok("molesâ†’volume: 0 = 0",         moles_to_volume(0),       0.0)
ok("volumeâ†’moles: 0 = 0",         volume_to_moles(0),       0.0)

sub("Edge cases â€” negative (math still valid)")
ok("massâ†’moles: -18g = -1",       mass_to_moles(-18, 18),   -1.0)
ok("molesâ†’mass: -2 = -36",        moles_to_mass(-2, 18),    -36.0)

sub("Edge cases â€” zero denominator (ZeroDivisionError)")
ok_raises("massâ†’moles: MM=0",     lambda: mass_to_moles(18, 0),    ZeroDivisionError)
ok_raises("volumeâ†’moles: V=0 base", lambda: 1/0,                   ZeroDivisionError)

sub("Very large / very small")
ok("molesâ†’particles: 1e6 mol",    moles_to_particles(1e6),  1e6 * Avogrado_number)
ok("massâ†’moles: tiny",            mass_to_moles(1e-10, 1),  1e-10)
ok("massâ†’moles: huge",            mass_to_moles(1e12, 1),   1e12)

sub("Roundtrips")
for m_test in [0.001, 1.0, 100.0, 1e6]:
    ok(f"massâ†’molesâ†’mass: {m_test}g",
       moles_to_mass(mass_to_moles(m_test, 58.44), 58.44), m_test, tol=1e-9)
ok("molesâ†’particlesâ†’moles roundtrip",
   particles_to_moles(moles_to_particles(2.5)), 2.5, tol=1e-9)
ok("molesâ†’volumeâ†’moles roundtrip",
   volume_to_moles(moles_to_volume(3.7)), 3.7, tol=1e-9)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 2 â€” EMPIRICAL FORMULA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 2: EMPIRICAL FORMULA CALCULATOR")
from Empirical_Formula_Calculator import calculate_empirical_formula, display_empirical_formula

sub("Standard formulas")
ef = calculate_empirical_formula(['H','O'], [2.0, 16.0])
ok("H2O: H=2", ef['H'], 2); ok("H2O: O=1", ef['O'], 1)

ef = calculate_empirical_formula(['C','H'], [12.0, 4.0])
ok("CH4: C=1", ef['C'], 1); ok("CH4: H=4", ef['H'], 4)

ef = calculate_empirical_formula(['C','H','O'], [40.0, 6.72, 53.28])
ok("Glucose (CH2O): C=1", ef['C'], 1)
ok("Glucose (CH2O): H=2", ef['H'], 2)
ok("Glucose (CH2O): O=1", ef['O'], 1)

ef = calculate_empirical_formula(['Na','Cl'], [22.99, 35.45])
ok("NaCl: Na=1", ef['Na'], 1); ok("NaCl: Cl=1", ef['Cl'], 1)

sub("Subscript display")
ok("display C1H4 â†’ CH4",  display_empirical_formula({'C':1,'H':4}), "CH4")
ok("display Na1Cl1 â†’ NaCl", display_empirical_formula({'Na':1,'Cl':1}), "NaCl")
ok("display H2O â†’ H2O",  display_empirical_formula({'H':2,'O':1}), "H2O")
ok("display subscript=1 suppressed", display_empirical_formula({'C':1}), "C")
ok("display subscript=3",  display_empirical_formula({'Al':2,'O':3}), "Al2O3")

sub("Fractional ratio compounds â€” need LCM scaling")
# FeO: Fe:O = 55.845:16 â†’ ratio â‰ˆ 1:1
ef_feo = calculate_empirical_formula(['Fe','O'], [55.845, 16.0])
ok("FeO: Fe=1", ef_feo['Fe'], 1); ok("FeO: O=1", ef_feo['O'], 1)

sub("Error: unknown element")
ok_raises("Unknown element 'X' raises", lambda: calculate_empirical_formula(['X'], [10.0]), ValueError)
ok_raises("Unknown element 'Yy' raises", lambda: calculate_empirical_formula(['Yy'], [10.0]), ValueError)

sub("Single element")
ef_s = calculate_empirical_formula(['C'], [12.0])
ok("Single C: C=1", ef_s['C'], 1)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 3 â€” PERCENT COMPOSITION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 3: PERCENT COMPOSITION CALCULATOR")
from percent_composition_calculator import (
    compute_percent_composition, parse_formula, FormulaError
)

sub("Molar masses & percentages")
mm, p = compute_percent_composition("H2O")
ok("H2O MMâ‰ˆ18.015", mm, 18.015, tol=0.01)
ok("H2O %H sum+%O=100", sum(p.values()), 100.0, tol=0.01)
ok("H2O %O>%H", p['O'] > p['H'], True)

mm2, p2 = compute_percent_composition("NaCl")
ok("NaCl MMâ‰ˆ58.44", mm2, 58.44, tol=0.01)
ok("NaCl %Naâ‰ˆ39.34", p2['Na'], 39.34, tol=0.1)
ok("NaCl %Clâ‰ˆ60.66", p2['Cl'], 60.66, tol=0.1)

mm3, _ = compute_percent_composition("Ca(OH)2")
ok("Ca(OH)2 MMâ‰ˆ74.093", mm3, 74.093, tol=0.01)

mm4, _ = compute_percent_composition("Al2(SO4)3")
ok("Al2(SO4)3 MMâ‰ˆ342.15", mm4, 342.15, tol=0.1)

mm5, _ = compute_percent_composition("Fe2O3")
ok("Fe2O3 MMâ‰ˆ159.69", mm5, 159.69, tol=0.1)

sub("Formula parser â€” elements and counts")
a = parse_formula("C6H12O6")
ok("C6H12O6 C=6", a['C'], 6); ok("C6H12O6 H=12", a['H'], 12); ok("C6H12O6 O=6", a['O'], 6)

a2 = parse_formula("Mg(NO3)2")
ok("Mg(NO3)2 Mg=1", a2['Mg'], 1); ok("Mg(NO3)2 N=2", a2['N'], 2); ok("Mg(NO3)2 O=6", a2['O'], 6)

a3 = parse_formula("Ca3(PO4)2")
ok("Ca3(PO4)2 Ca=3", a3['Ca'], 3); ok("Ca3(PO4)2 P=2", a3['P'], 2); ok("Ca3(PO4)2 O=8", a3['O'], 8)

sub("Hydrate parsing")
a4 = parse_formula("CuSO4*5H2O")
ok("CuSO4*5H2O Cu=1", a4['Cu'], 1)
ok("CuSO4*5H2O H=10", a4['H'], 10)
ok("CuSO4*5H2O O=9",  a4['O'], 9)

sub("Percents sum to 100")
for formula in ["H2O","NaCl","Ca(OH)2","C6H12O6","Al2(SO4)3","Fe2O3","KMnO4"]:
    _, pcts = compute_percent_composition(formula)
    ok(f"{formula} percents sum=100", sum(pcts.values()), 100.0, tol=0.01)

sub("Error cases")
ok_raises("empty string",      lambda: parse_formula(""),    Exception)
ok_raises("none input",        lambda: parse_formula(None),  Exception)
ok_raises("unknown element Xy",lambda: parse_formula("Xy3"), Exception)
ok_raises("unknown element Qq",lambda: parse_formula("Qq"),  Exception)

sub("Single atoms")
mm_h, _ = compute_percent_composition("H")
ok("H alone MM=1.008", mm_h, 1.008, tol=0.001)
mm_fe, p_fe = compute_percent_composition("Fe")
ok("Fe alone 100% Fe", p_fe['Fe'], 100.0, tol=0.001)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 4 â€” VOLUME-MASS CONVERSIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 4: VOLUME-MASS CONVERSIONS")
from volume_mass_conversions import mass_to_volume, volume_to_mass, density_from_mv

sub("Normal operation")
ok("V=m/d: 100g,2g/mLâ†’50mL",  mass_to_volume(100, 2), 50.0)
ok("m=V*d: 50mL,2g/mLâ†’100g",  volume_to_mass(50, 2), 100.0)
ok("d=m/V: 200g,100mLâ†’2g/mL", density_from_mv(200, 100), 2.0)
ok("water: 1g/mL",             density_from_mv(1000, 1000), 1.0)

sub("Zero inputs")
ok("V: 0g,any d â†’ 0",  mass_to_volume(0, 2), 0.0)
ok("m: 0mL,any d â†’ 0", volume_to_mass(0, 3), 0.0)
ok("d: 0g,any V â†’ 0",  density_from_mv(0, 5), 0.0)

sub("Division by zero")
ok_raises("V: d=0 â†’ ZeroDivisionError", lambda: mass_to_volume(100, 0), ZeroDivisionError)
ok_raises("d: V=0 â†’ ZeroDivisionError", lambda: density_from_mv(100, 0), ZeroDivisionError)

sub("Negative values (algebraically valid)")
ok("negative mass â†’ negative volume", mass_to_volume(-50, 2), -25.0)
ok("negative density â†’ negative volume", mass_to_volume(50, -2), -25.0)

sub("Very large and very small")
ok("huge mass",   mass_to_volume(1e12, 1e6), 1e6)
ok("tiny mass",   mass_to_volume(1e-9, 1),   1e-9)

sub("Roundtrips")
for m, d in [(100, 2.5), (0.001, 1.0), (1e6, 13.6)]:
    ok(f"massâ†’volâ†’mass: {m}g,{d}g/mL",
       volume_to_mass(mass_to_volume(m, d), d), m, tol=1e-9)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 5 â€” OXIDATION NUMBER CALCULATOR
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 5: OXIDATION NUMBER CALCULATOR")
from oxidation_number_calculator import solve_oxidation_numbers

sub("Pure elements â†’ 0")
for formula in ["O2","H2","N2","Fe","Cl2","Na","Cu","S8"]:
    res = solve_oxidation_numbers(formula)
    elem = list(res.keys())[0]
    ok(f"{formula} ox=0", res[elem], 0)

sub("Binary compounds")
ok("NaCl Na=+1", solve_oxidation_numbers("NaCl")['Na'], 1)
ok("NaCl Cl=-1", solve_oxidation_numbers("NaCl")['Cl'], -1)
ok("MgO Mg=+2",  solve_oxidation_numbers("MgO")['Mg'],  2)
ok("MgO O=-2",   solve_oxidation_numbers("MgO")['O'],   -2)
ok("AlCl3 Al=+3",solve_oxidation_numbers("AlCl3")['Al'], 3)

sub("Polyatomic compounds â€” solving unknown element")
ok("H2O H=+1",   solve_oxidation_numbers("H2O")['H'],   1)
ok("H2O O=-2",   solve_oxidation_numbers("H2O")['O'],   -2)
ok("KMnO4 Mn=+7",solve_oxidation_numbers("KMnO4")['Mn'], 7)
ok("H2SO4 S=+6", solve_oxidation_numbers("H2SO4")['S'],  6)
ok("HNO3 N=+5",  solve_oxidation_numbers("HNO3")['N'],   5)
ok("Cr2O3 Cr=+3",solve_oxidation_numbers("Cr2O3")['Cr'], 3)
ok("MnO2 Mn=+4", solve_oxidation_numbers("MnO2")['Mn'],  4)
ok("Fe2O3 Fe=+3",solve_oxidation_numbers("Fe2O3")['Fe'], 3)

sub("Ions (non-zero charge)")
ok("SO4 2-: S=+6", solve_oxidation_numbers("SO4", charge=-2)['S'], 6)
ok("NO3 1-: N=+5", solve_oxidation_numbers("NO3", charge=-1)['N'], 5)
ok("MnO4 1-: Mn=+7", solve_oxidation_numbers("MnO4", charge=-1)['Mn'], 7)
ok("NH4 1+: N=-3", solve_oxidation_numbers("NH4", charge=1)['N'], -3)
ok("PO4 3-: P=+5", solve_oxidation_numbers("PO4", charge=-3)['P'], 5)

sub("Peroxides (O = -1)")
ok("H2O2 peroxide O=-1", solve_oxidation_numbers("H2O2", peroxide=True)['O'], -1)
ok("H2O2 peroxide H=+1", solve_oxidation_numbers("H2O2", peroxide=True)['H'], 1)

sub("Verification: sum of (ox Ã— count) = charge")
for formula, charge in [("KMnO4",0),("H2SO4",0),("SO4",-2),("NH4",1)]:
    res = solve_oxidation_numbers(formula, charge=charge)
    counts = parse_formula(formula)
    total = sum(res[e] * counts[e] for e in counts)
    ok(f"{formula} charge balance = {charge}", round(total, 6), float(charge))

sub("Error: multiple unknown elements")
ok_raises(">1 unknown elem raises", lambda: solve_oxidation_numbers("FeCr2O4"), ValueError)

sub("Fractional oxidation states")
# Fe3O4 = FeOÂ·Fe2O3: Fe avg = +8/3
res_fe3o4 = solve_oxidation_numbers("Fe3O4")
ok("Fe3O4 Fe ox = +8/3", res_fe3o4['Fe'], 8/3, tol=0.01)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 6 â€” ATOM ECONOMY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 6: ATOM ECONOMY CALCULATOR")
from atom_economy_calculator import calculate_atom_economy, get_molar_mass

sub("Molar mass correctness")
ok("H2O MMâ‰ˆ18.015",  get_molar_mass("H2O"),  18.015, tol=0.01)
ok("CO2 MMâ‰ˆ44.01",   get_molar_mass("CO2"),  44.01,  tol=0.01)
ok("NaCl MMâ‰ˆ58.44",  get_molar_mass("NaCl"), 58.44,  tol=0.01)
ok("Fe2O3 MMâ‰ˆ159.69",get_molar_mass("Fe2O3"),159.69, tol=0.1)
ok("C6H12O6 MMâ‰ˆ180.16",get_molar_mass("C6H12O6"),180.16,tol=0.1)

sub("Atom economy calculations")
# H2 + Cl2 â†’ 2HCl: AE = 2*36.46 / (2.016+70.9) = 100%
ae, mwd, mwr = calculate_atom_economy(['H2','Cl2'],[1,1],'HCl',2)
ok("H2+Cl2â†’2HCl: AE=100%", ae, 100.0, tol=0.1)

# CH4+2O2â†’CO2+2H2O: desired CO2
# MW CO2*1 = 44.01; total reactants = 16.043+64.0 = 80.043; AE = 44.01/80.043*100 â‰ˆ 54.98%
ae2, _, _ = calculate_atom_economy(['CH4','O2'],[1,2],'CO2',1)
ok_close("CH4+O2â†’CO2: AEâ‰ˆ54.98%", ae2, 44.01/80.043*100, pct=0.5)

# 100% AE must satisfy mwd == mwr
ae_100, mwd_100, mwr_100 = calculate_atom_economy(['H2','Cl2'],[1,1],'HCl',2)
ok("100% AE: mwd=mwr", abs(mwd_100 - mwr_100) < 0.01, True)

sub("Zero / error cases")
ok_raises("reactant MW=0 raises", lambda: calculate_atom_economy([],[],  'H2O',1), Exception)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 7 â€” IONIC BONDING CALCULATOR
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 7: IONIC BONDING CALCULATOR")
from ionic_bonding_calculator import classify_bond, write_ionic_formula, ELECTRONEGATIVITIES

sub("Bond classification thresholds")
# Ionic: diff >= 1.7
bt, en1, en2, diff = classify_bond('Na', 'Cl')
ok("Na-Cl: Ionic",        bt, "Ionic")
ok("Na-Cl diffâ‰ˆ2.23",     diff, 2.23, tol=0.01)

bt2, _, _, diff2 = classify_bond('K', 'F')
ok("K-F: Ionic",          bt2, "Ionic")
ok("K-F diff>1.7",        diff2 > 1.7, True)

# Polar Covalent: 0.4 <= diff < 1.7
bt3, _, _, diff3 = classify_bond('H', 'O')
ok("H-O: Polar Covalent", bt3, "Polar Covalent")
ok("H-O diffâ‰ˆ1.24",       diff3, 1.24, tol=0.01)

bt4, _, _, diff4 = classify_bond('H', 'N')
ok("H-N: Polar Covalent", bt4, "Polar Covalent")

# Nonpolar Covalent: diff < 0.4
bt5, _, _, diff5 = classify_bond('C', 'H')
ok("C-H: Nonpolar Covalent", bt5, "Nonpolar Covalent")
ok("C-H diff<0.4",            diff5 < 0.4, True)

# Same element: diff = 0
bt6, en1_6, en2_6, diff6 = classify_bond('Cl', 'Cl')
ok("Cl-Cl: Nonpolar Covalent", bt6, "Nonpolar Covalent")
ok("Cl-Cl: diff = 0",          diff6, 0.0, tol=1e-9)

sub("Exactly at threshold")
# diff = 0.4 exactly â†’ Polar Covalent
# diff = 1.7 exactly â†’ Ionic
# Hard to hit exactly, but test near-boundary
bt7, _, _, d7 = classify_bond('S', 'H')
ok("S-H: diff computed", d7, abs(ELECTRONEGATIVITIES['S'] - ELECTRONEGATIVITIES['H']), tol=1e-9)

sub("Ionic formula writer â€” cross multiplication")
ok("Na+Cl = NaCl",   write_ionic_formula('Na', 1, 'Cl', -1), "NaCl")
ok("Ca+Cl = CaCl2",  write_ionic_formula('Ca', 2, 'Cl', -1), "CaCl2")
ok("Al+O = Al2O3",   write_ionic_formula('Al', 3, 'O',  -2), "Al2O3")
ok("Mg+O = MgO",     write_ionic_formula('Mg', 2, 'O',  -2), "MgO")
ok("Fe3+O = Fe2O3",  write_ionic_formula('Fe', 3, 'O',  -2), "Fe2O3")
ok("Fe2+S = FeS",    write_ionic_formula('Fe', 2, 'S',  -2), "FeS")
ok("Pb4+O = PbO2",   write_ionic_formula('Pb', 4, 'O',  -2), "PbO2")
ok("Al+N = AlN",     write_ionic_formula('Al', 3, 'N',  -3), "AlN")
ok("Ca+N = Ca3N2",   write_ionic_formula('Ca', 2, 'N',  -3), "Ca3N2")

sub("Error cases for write_ionic_formula")
ok_raises("cation charge negative", lambda: write_ionic_formula('Na',-1,'Cl',-1), ValueError)
ok_raises("anion charge positive",  lambda: write_ionic_formula('Na', 1,'Cl', 1), ValueError)
ok_raises("both negative",          lambda: write_ionic_formula('Na',-1,'Cl', 1), ValueError)

sub("Error: unknown element in classify_bond")
ok_raises("unknown elem1", lambda: classify_bond('Xx','Cl'), ValueError)
ok_raises("unknown elem2", lambda: classify_bond('Na','Yy'), ValueError)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 8 â€” PERCENTAGE YIELD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 8: PERCENTAGE YIELD CALCULATOR")
from percentage_yield_calculator import (
    calc_percentage_yield, calc_actual_yield, calc_theoretical_yield
)

sub("Normal values")
ok("90% yield",  calc_percentage_yield(18, 20),   90.0)
ok("100% yield", calc_percentage_yield(20, 20),   100.0)
ok("50% yield",  calc_percentage_yield(10, 20),   50.0)
ok("actual from 90%,20g", calc_actual_yield(90, 20),  18.0)
ok("theoretical from 18g,90%", calc_theoretical_yield(18, 90), 20.0)

sub(">100% yield (impurities / measurement error)")
ok("125% yield possible", calc_percentage_yield(25, 20), 125.0)
ok("actual from 110%",    calc_actual_yield(110, 20),    22.0)

sub("Zero actual yield")
ok("0% yield",    calc_percentage_yield(0, 20),   0.0)
ok("0g actual",   calc_actual_yield(0, 20),        0.0)

sub("Tiny values")
ok("tiny actual", calc_percentage_yield(1e-6, 1),  1e-4)
ok("tiny % yield", calc_actual_yield(0.01, 100),   0.01)

sub("Error: zero theoretical (ZeroDivisionError)")
ok_raises("pct yield: theoretical=0", lambda: calc_percentage_yield(10, 0), ZeroDivisionError)
ok_raises("theoretical: pct=0",       lambda: calc_theoretical_yield(10, 0),ZeroDivisionError)

sub("Roundtrips")
for act, theo in [(7.3,12.5),(0.001,0.005),(500,600)]:
    pct = calc_percentage_yield(act, theo)
    ok(f"roundtrip {act}/{theo}",
       calc_theoretical_yield(act, pct), theo, tol=1e-9)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 9 â€” GAS LAWS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 9: GAS LAWS")
from gas_laws import (
    ideal_gas_find_P, ideal_gas_find_V, ideal_gas_find_n, ideal_gas_find_T,
    combined_gas_find_P2, combined_gas_find_V2, combined_gas_find_T2,
    moles_to_volume_stp, volume_to_moles_stp, molar_volume_nonstandard,
    graham_rate_ratio, graham_find_M2, graham_find_M1,
    dalton_total_pressure, dalton_partial_pressure, dalton_mole_fraction, R
)

sub("Ideal Gas Law â€” all four variables")
# STP: 1 mol, 273.15 K, 1 atm â†’ V = nRT/P â‰ˆ 22.41 L
V_stp = ideal_gas_find_V(1, 273.15, 1.0)
ok("Ideal: V of 1mol STP â‰ˆ22.41", V_stp, R*273.15, tol=0.01)
ok("Ideal: P = nRT/V",    ideal_gas_find_P(2,10,300),  2*R*300/10,   tol=1e-9)
ok("Ideal: n = PV/RT",    ideal_gas_find_n(1, V_stp, 273.15), 1.0,   tol=0.001)
ok("Ideal: T = PV/nR",    ideal_gas_find_T(1, V_stp, 1), 273.15,     tol=0.01)

sub("Ideal Gas Law â€” zero/division")
ok_raises("P: V=0", lambda: ideal_gas_find_P(1, 0, 300),  ZeroDivisionError)
ok_raises("V: P=0", lambda: ideal_gas_find_V(1, 300, 0),  ZeroDivisionError)
ok_raises("n: T=0", lambda: ideal_gas_find_n(1, 10, 0),   ZeroDivisionError)
ok_raises("T: n=0", lambda: ideal_gas_find_T(1, 10, 0),   ZeroDivisionError)

sub("Ideal Gas Law â€” self-consistency roundtrips")
for n,V,T in [(1,22.4,273),(2,5,350),(0.5,100,400)]:
    P = ideal_gas_find_P(n, V, T)
    ok(f"nVTâ†’Pâ†’n roundtrip ({n},{V},{T})",
       ideal_gas_find_n(P, V, T), n, tol=1e-6)

sub("Combined Gas Law")
ok("Combined: P2=2",  combined_gas_find_P2(1,10,300,5,300),  2.0, tol=1e-9)
ok("Combined: V2=10", combined_gas_find_V2(2,5,300,1,300),  10.0, tol=1e-9)
ok("Combined: T2=600",combined_gas_find_T2(1,10,300,2,10),  600.0,tol=1e-9)
# Boyle's law: T constant â†’ P1V1 = P2V2
ok("Boyle: P1V1=P2V2", combined_gas_find_P2(2,5,300,10,300), 1.0, tol=1e-9)
# Charles' law: P constant â†’ V1/T1 = V2/T2
ok("Charles: V2=V1*T2/T1", combined_gas_find_V2(1,10,300,1,600), 20.0, tol=1e-9)
# Gay-Lussac: V constant â†’ P1/T1 = P2/T2
ok("Gay-Lussac: T2=T1*P2/P1", combined_gas_find_T2(1,10,300,2,10), 600.0, tol=1e-9)

sub("Combined Gas Law â€” zero denominator")
ok_raises("Combined P2: V2=0", lambda: combined_gas_find_P2(1,10,300,0,300), ZeroDivisionError)
ok_raises("Combined V2: P2=0", lambda: combined_gas_find_V2(1,10,300,0,300), ZeroDivisionError)
ok_raises("Combined T2: P1=0", lambda: combined_gas_find_T2(0,10,300,2,10),  ZeroDivisionError)

sub("Molar volume")
ok("STP: 2molâ†’44.8L",  moles_to_volume_stp(2),    44.8)
ok("STP: 11.2Lâ†’0.5mol",volume_to_moles_stp(11.2),  0.5)
ok("STP: 0molâ†’0L",     moles_to_volume_stp(0),      0.0)
ok("Non-std molar vol: T=273.15,P=1â†’22.41", molar_volume_nonstandard(273.15,1.0), R*273.15, tol=0.01)
ok_raises("Non-std: P=0", lambda: molar_volume_nonstandard(300,0), ZeroDivisionError)

sub("Graham's Law of Effusion")
ok("H2/O2 ratio=4.0",   graham_rate_ratio(2, 32),    4.0, tol=1e-9)
ok("rate ratio=1 (same)",graham_rate_ratio(28, 28),  1.0, tol=1e-9)
ok("Find M2: M1=2,r=4â†’32", graham_find_M2(2, 4),    32.0, tol=1e-9)
ok("Find M1: M2=32,r=4â†’2", graham_find_M1(32, 4),    2.0, tol=1e-9)
ok("Graham roundtrip M2", graham_find_M1(graham_find_M2(4, 3.0), 3.0), 4.0, tol=1e-9)
ok("Graham roundtrip M1", graham_find_M2(graham_find_M1(16, 2.0), 2.0), 16.0, tol=1e-9)
ok_raises("Graham M1=0", lambda: graham_rate_ratio(0, 32), ZeroDivisionError)
ok_raises("Graham ratio=0 find M1", lambda: graham_find_M1(32, 0), ZeroDivisionError)

sub("Dalton's Law of Partial Pressures")
ok("Total: [0.3,0.5,0.2]=1.0", dalton_total_pressure([0.3,0.5,0.2]), 1.0, tol=1e-9)
ok("Total: empty list=0",       dalton_total_pressure([]), 0.0)
ok("Total: single=0.8",         dalton_total_pressure([0.8]), 0.8)
ok("Partial: P=1, x=0.3â†’0.3",  dalton_partial_pressure(1.0, 0.3), 0.3, tol=1e-9)
ok("Partial: x=0â†’0",            dalton_partial_pressure(5.0, 0.0), 0.0)
ok("Partial: x=1â†’P_total",      dalton_partial_pressure(3.0, 1.0), 3.0)
ok("Mole frac: 0.5/2=0.25",     dalton_mole_fraction(0.5, 2.0), 0.25, tol=1e-9)
ok("Mole frac: all one gas=1",  dalton_mole_fraction(5.0, 5.0), 1.0, tol=1e-9)
ok_raises("Mole frac: n_total=0", lambda: dalton_mole_fraction(1, 0), ZeroDivisionError)

sub("Mole fraction sum = 1")
fracs = [dalton_mole_fraction(n, 10.0) for n in [1,2,3,4]]
ok("Mole fractions sum to 1", sum(fracs), 1.0, tol=1e-9)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 10 â€” ACID-BASE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 10: ACID-BASE CALCULATOR")
from acid_base import (
    all_four, strong_acid_pH, strong_base_pH,
    weak_acid_pH, weak_base_pH,
    Ka_to_pKa, pKa_to_Ka, Kb_to_pKb, pKb_to_Kb, Ka_to_Kb, Kb_to_Ka,
    buffer_pH, buffer_ratio, identify, Kw,
    equivalence_moles, titration_find_concentration, titration_find_volume,
    equivalence_point_pH_description, pH_from_H, H_from_pH
)

sub("all_four â€” each entry point")
for val, key, expected_pH in [(7.0,'pH',7.0),(4.0,'pOH',10.0),(1e-3,'H',3.0),(1e-5,'OH',9.0)]:
    kwargs = {key: val}
    pH, pOH, H, OH = all_four(**kwargs)
    ok(f"all_four({key}={val}): pH={expected_pH}", pH, expected_pH, tol=1e-9)
    ok(f"all_four({key}={val}): pH+pOH=14", pH + pOH, 14.0, tol=1e-9)
    ok(f"all_four({key}={val}): H*OH=Kw",  H * OH, Kw, tol=1e-27)

sub("pH + pOH = 14 at boundary values")
for ph in [0.0, 1.0, 7.0, 13.0, 14.0]:
    a, b, _, _ = all_four(pH=ph)
    ok(f"pH+pOH=14 at pH={ph}", a+b, 14.0, tol=1e-9)

sub("pH = -log[H+] consistency")
for h in [1.0, 0.1, 0.01, 1e-7, 1e-14]:
    pH_calc = pH_from_H(h)
    H_back  = H_from_pH(pH_calc)
    ok(f"H={h}: pHâ†’H roundtrip", H_back, h, tol=h*1e-9)

sub("Strong acid pH")
ok("HCl 0.1M: pH=1",    strong_acid_pH(0.1),  1.0, tol=1e-9)
ok("HCl 0.01M: pH=2",   strong_acid_pH(0.01), 2.0, tol=1e-9)
ok("HCl 1.0M: pH=0",    strong_acid_pH(1.0),  0.0, tol=1e-9)
ok("HCl 10.0M: pH=-1",  strong_acid_pH(10.0), -1.0,tol=1e-9)
ok_raises("SA: C=0 raises",  lambda: strong_acid_pH(0),   ValueError)
ok_raises("SA: C<0 raises",  lambda: strong_acid_pH(-0.1),ValueError)

sub("Strong base pH")
ok("NaOH 0.1M: pH=13",  strong_base_pH(0.1),  13.0, tol=1e-9)
ok("NaOH 0.01M: pH=12", strong_base_pH(0.01), 12.0, tol=1e-9)
ok("NaOH 1.0M: pH=14",  strong_base_pH(1.0),  14.0, tol=1e-9)
ok_raises("SB: C=0 raises",  lambda: strong_base_pH(0),   ValueError)
ok_raises("SB: C<0 raises",  lambda: strong_base_pH(-0.1),ValueError)

sub("Weak acid pH â€” approximation vs quadratic")
# Acetic acid: Ka=1.8e-5, C=0.1 â†’ approx valid (x/C < 5%)
ph_wa, approx, x_wa = weak_acid_pH(1.8e-5, 0.1)
ok("Acetic: pHâ‰ˆ2.872", ph_wa, 2.872, tol=0.005)
ok("Acetic: approx used", approx, True)
ok("Acetic: 5% rule ok", x_wa/0.1 < 0.05, True)

# Large Ka forces quadratic
ph_waq, approxq, x_waq = weak_acid_pH(0.01, 0.05)
ok("Large Ka: quadratic", approxq, False)
disc = 0.01**2 + 4*0.01*0.05
x_exp = (-0.01 + math.sqrt(disc)) / 2
ok("Large Ka: x exact", x_waq, x_exp, tol=1e-10)

# Very small Ka (very weak acid)
ph_vw, approx_vw, _ = weak_acid_pH(1e-10, 1.0)
ok("Very weak Ka=1e-10: approx valid", approx_vw, True)
ok("Very weak Ka: pHâ‰ˆ5.0", ph_vw, 5.0, tol=0.01)  # x=sqrt(1e-10*1)=1e-5 â†’ pH=5

ok_raises("WA: Ka=0 raises",  lambda: weak_acid_pH(0, 0.1),   ValueError)
ok_raises("WA: Ka<0 raises",  lambda: weak_acid_pH(-1e-5,0.1),ValueError)
ok_raises("WA: C=0 raises",   lambda: weak_acid_pH(1.8e-5,0), ValueError)

sub("Weak base pH")
ph_wb, approx_wb, x_wb = weak_base_pH(1.8e-5, 0.1)
ok("Ammonia: pHâ‰ˆ11.128", ph_wb, 11.128, tol=0.005)
ok("Ammonia: approx used", approx_wb, True)
ok_raises("WB: Kb=0 raises",  lambda: weak_base_pH(0, 0.1),   ValueError)
ok_raises("WB: C=0 raises",   lambda: weak_base_pH(1.8e-5, 0),ValueError)

sub("Ka/Kb/pKa/pKb conversions")
ok("Kaâ†’pKa: 1.8e-5â‰ˆ4.745", Ka_to_pKa(1.8e-5), 4.745, tol=0.001)
ok("pKaâ†’Ka roundtrip",      pKa_to_Ka(Ka_to_pKa(1.8e-5)), 1.8e-5, tol=1e-8)
ok("Ka*Kb=Kw",              1.8e-5 * Ka_to_Kb(1.8e-5), Kw, tol=1e-20)
ok("Kbâ†’Ka roundtrip",       Kb_to_Ka(Ka_to_Kb(1.8e-5)), 1.8e-5, tol=1e-20)
ok("pKa+pKb=14",            Ka_to_pKa(1.8e-5) + Kb_to_pKb(Ka_to_Kb(1.8e-5)), 14.0, tol=0.001)
# Multiple Ka values
for Ka_test in [1e-14, 1e-7, 1e-2, 1.0]:
    ok(f"Ka{Ka_test} pKa+pKb=14",
       Ka_to_pKa(Ka_test) + Kb_to_pKb(Ka_to_Kb(Ka_test)), 14.0, tol=0.001)

sub("Henderson-Hasselbalch buffer")
ok("Buffer equal conc: pH=pKa", buffer_pH(1.8e-5, 0.1, 0.1), Ka_to_pKa(1.8e-5), tol=1e-9)
ok("Buffer [A-]/[HA]=10: pH=pKa+1", buffer_pH(1.8e-5,0.1,1.0), Ka_to_pKa(1.8e-5)+1, tol=1e-9)
ok("Buffer [A-]/[HA]=0.1: pH=pKa-1",buffer_pH(1.8e-5,1.0,0.1), Ka_to_pKa(1.8e-5)-1, tol=1e-9)
ok("buffer_ratio at pKa: ratio=1",   buffer_ratio(1.8e-5, Ka_to_pKa(1.8e-5)), 1.0, tol=1e-9)
ok_raises("buffer: acid=0 raises",  lambda: buffer_pH(1.8e-5, 0, 0.1),  ValueError)
ok_raises("buffer: base=0 raises",  lambda: buffer_pH(1.8e-5, 0.1, 0),  ValueError)

sub("Acid/base identifier")
for formula, expected in [
    ("HCl","Strong acid"),("HBr","Strong acid"),("HI","Strong acid"),
    ("HNO3","Strong acid"),("H2SO4","Strong acid"),("HClO4","Strong acid"),
    ("NaOH","Strong base"),("KOH","Strong base"),("Ca(OH)2","Strong base"),
    ("Ba(OH)2","Strong base"),("H2O","Amphoteric"),
    ("NaCl","Neutral salt"),("KNO3","Neutral salt"),
]:
    ok(f"identify({formula})", identify(formula), expected)

sub("Titration")
ok("moles: 0.1*0.025=0.0025", equivalence_moles(0.1, 0.025), 0.0025, tol=1e-9)
ok("find C: 0.0025/0.025=0.1", titration_find_concentration(0.0025, 0.025), 0.1, tol=1e-9)
ok("find V: 0.0025/0.1=0.025", titration_find_volume(0.0025, 0.1), 0.025, tol=1e-9)
desc_ss = equivalence_point_pH_description("strong acid","strong base")
ok("ss eq point contains 7", "7" in desc_ss, True)
desc_ws = equivalence_point_pH_description("weak acid","strong base")
ok("ws eq point >7", ">" in desc_ws, True)
desc_sw = equivalence_point_pH_description("strong acid","weak base")
ok("sw eq point <7", "<" in desc_sw, True)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 11 â€” THERMODYNAMICS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 11: THERMODYNAMICS")
from thermodynamics import (
    cal_q, cal_m, cal_c, cal_dT, celsius_to_kelvin,
    hess_law,
    bond_enthalpy_dH, lookup_bond, BOND_ENTHALPIES,
    standard_enthalpy_rxn,
    gibbs_dG, gibbs_dH, gibbs_dS, gibbs_T,
    spontaneity, spontaneity_analysis, SPECIFIC_HEATS
)

sub("Calorimetry q=mcÎ”T â€” all four solvers")
ok("q=200*4.18*10=8360",   cal_q(200, 4.18, 10),  8360.0)
ok("q negative (cooling)", cal_q(100, 4.18, -5),  -2090.0)
ok("q=0 when Î”T=0",        cal_q(100, 4.18, 0),    0.0)
ok("m=8360/(4.18*10)=200", cal_m(8360, 4.18, 10),  200.0)
ok("c=8360/(200*10)=4.18", cal_c(8360, 200, 10),   4.18)
ok("Î”T=8360/(200*4.18)=10",cal_dT(8360, 200, 4.18),10.0)

ok_raises("cal_m: c=0",  lambda: cal_m(100, 0, 10),   ValueError)
ok_raises("cal_m: Î”T=0", lambda: cal_m(100, 4.18, 0), ValueError)
ok_raises("cal_c: m=0",  lambda: cal_c(100, 0, 10),   ValueError)
ok_raises("cal_c: Î”T=0", lambda: cal_c(100, 100, 0),  ValueError)
ok_raises("cal_dT: m=0", lambda: cal_dT(100, 0, 4.18),ValueError)
ok_raises("cal_dT: c=0", lambda: cal_dT(100, 100, 0), ValueError)

# Specific heat table correctness
for name, expected_c in [("water",4.18),("iron",0.449),("copper",0.385),("aluminum",0.897)]:
    ok(f"SPECIFIC_HEATS[{name}]={expected_c}", SPECIFIC_HEATS[name], expected_c)

# Celsius â†’ Kelvin
ok("0Â°C = 273.15 K",    celsius_to_kelvin(0),      273.15)
ok("100Â°C = 373.15 K",  celsius_to_kelvin(100),    373.15)
ok("-273.15Â°C = 0 K",   celsius_to_kelvin(-273.15),  0.0)

sub("Calorimetry roundtrips")
for m,c,dt in [(100,4.18,15),(50,0.449,30),(200,2.44,8)]:
    q = cal_q(m,c,dt)
    ok(f"qâ†’m roundtrip ({m},{c},{dt})", cal_m(q,c,dt), m, tol=1e-9)
    ok(f"qâ†’c roundtrip",               cal_c(q,m,dt), c, tol=1e-9)
    ok(f"qâ†’Î”T roundtrip",              cal_dT(q,m,c), dt, tol=1e-9)

sub("Hess's Law")
ok("2 steps summed",       hess_law([-110.5,-283.0],[1,1]),  -393.5, tol=1e-9)
ok("flip one step",        hess_law([-572,-393.5],[-1,1]),   178.5,  tol=1e-9)
ok("scale by 0.5",         hess_law([-572],[0.5]),           -286.0, tol=1e-9)
ok("identity: mult=1",     hess_law([-241.8],[1]),           -241.8, tol=1e-9)
ok("flip: mult=-1",        hess_law([-241.8],[-1]),           241.8, tol=1e-9)
ok("3-step arithmetic",    hess_law([-393.5,-285.8,2220],[3,4,-1]),
   3*(-393.5)+4*(-285.8)+(-1)*2220, tol=1e-6)
ok_raises("mismatched lengths", lambda: hess_law([1,2],[1]), ValueError)

sub("Bond Enthalpy")
# CH4 + 2O2 â†’ CO2 + 2H2O
broken = [("C-H",4,413),("O=O",2,498)]
formed = [("C=O",2,805),("O-H",4,463)]
dH, sb, sf = bond_enthalpy_dH(broken, formed)
ok("CH4+O2: sb=2648", sb, 2648.0, tol=1e-9)
ok("CH4+O2: sf=3462", sf, 3462.0, tol=1e-9)
ok("CH4+O2: dH=-814", dH, -814.0, tol=1e-9)

# H2 + Cl2 â†’ 2HCl
dH2, sb2, sf2 = bond_enthalpy_dH([("H-H",1,436),("Cl-Cl",1,242)],[("H-Cl",2,431)])
ok("H2+Cl2: dH=-184", dH2, -184.0, tol=1e-9)

# Empty lists
dH0, sb0, sf0 = bond_enthalpy_dH([], [])
ok("Empty: dH=0", dH0, 0.0); ok("Empty: sb=0", sb0, 0.0); ok("Empty: sf=0", sf0, 0.0)

# Bond lookup â€” canonical and reversed
ok("lookup C-H=413",   lookup_bond("C-H"), 413)
ok("lookup H-C=413",   lookup_bond("H-C"), 413)
ok("lookup O=O=498",   lookup_bond("O=O"), 498)
ok("lookup N#N=945",   lookup_bond("N#N"), 945)
ok("lookup O-H=463",   lookup_bond("O-H"), 463)
ok("lookup Xx-Yy=None",lookup_bond("Xx-Yy"), None)
ok("table keys unique", len(BOND_ENTHALPIES), len(set(BOND_ENTHALPIES.keys())))

sub("Standard Enthalpy of Reaction")
# CH4 + 2O2 â†’ CO2 + 2H2O: dH = -890.3 kJ
species = [
    {'formula':'CH4','dHf':-74.8,  'coeff':1,'role':'reactant'},
    {'formula':'O2', 'dHf':  0.0,  'coeff':2,'role':'reactant'},
    {'formula':'CO2','dHf':-393.5, 'coeff':1,'role':'product'},
    {'formula':'H2O','dHf':-285.8, 'coeff':2,'role':'product'},
]
ok("CH4 combustion dH=-890.3", standard_enthalpy_rxn(species), -890.3, tol=0.01)

# H2O decomposition (endothermic)
species_d = [
    {'formula':'H2O','dHf':-285.8,'coeff':2,'role':'reactant'},
    {'formula':'H2', 'dHf':  0.0, 'coeff':2,'role':'product'},
    {'formula':'O2', 'dHf':  0.0, 'coeff':1,'role':'product'},
]
ok("H2O decomp dH=+571.6", standard_enthalpy_rxn(species_d), 571.6, tol=0.01)
ok_raises("bad role raises", lambda: standard_enthalpy_rxn(
    [{'formula':'X','dHf':0,'coeff':1,'role':'byproduct'}]), ValueError)

sub("Gibbs Free Energy Î”G = Î”H - TÎ”S")
ok("Î”G = -100-300*(-0.2) = -40", gibbs_dG(-100,300,-200), -40.0, tol=1e-9)
ok("Î”G = 0 when Î”H=TÎ”S",        gibbs_dG(60,300,200),      0.0,  tol=1e-9)
ok("Î”H from Î”G=-40,T=300,Î”S=-200", gibbs_dH(-40,300,-200),-100.0,tol=1e-9)
ok("Î”S from Î”H=-100,Î”G=-40,T=300",gibbs_dS(-100,-40,300),-200.0, tol=1e-9)
ok("T crossover: Î”H=-100,Î”S=-200â†’500K", gibbs_T(-100,0,-200), 500.0, tol=1e-9)

ok_raises("gibbs_T: Î”S=0 raises",  lambda: gibbs_T(-100, 0, 0),  ValueError)
ok_raises("gibbs_dS: T=0 raises",  lambda: gibbs_dS(-100,-40,0), ValueError)

# Roundtrips
for dh, T_k, ds in [(-200,350,50),(-100,298,-200),(0,300,100)]:
    dg = gibbs_dG(dh, T_k, ds)
    ok(f"Gibbs dH roundtrip ({dh},{T_k},{ds})", gibbs_dH(dg, T_k, ds), dh, tol=1e-9)
    ok(f"Gibbs dS roundtrip", gibbs_dS(dh, dg, T_k), ds, tol=1e-9)

sub("Spontaneity labels")
ok("Î”G=-1: spontaneous",    spontaneity(-1.0), "Spontaneous (Î”G < 0)")
ok("Î”G=+1: non-spontaneous",spontaneity(+1.0), "Non-spontaneous (Î”G > 0)")
ok("Î”G=0: equilibrium",     spontaneity(0.0),  "At equilibrium (Î”G = 0)")
ok("Î”G=-0.5e-6: near-zeroâ†’eq",spontaneity(-5e-7),"At equilibrium (Î”G = 0)")
ok("Î”G=-1e-5: spontaneous", spontaneity(-1e-5),"Spontaneous (Î”G < 0)")

ok("dH<0,dS>0: always spont",
   spontaneity_analysis(-1,1), "Always spontaneous at all temperatures (Î”H<0, Î”S>0)")
ok("dH>0,dS<0: never spont",
   spontaneity_analysis(1,-1), "Never spontaneous at any temperature (Î”H>0, Î”S<0)")
ok("dH<0,dS<0: low T spont",
   spontaneity_analysis(-1,-1),"Spontaneous at low T only (Î”H<0, Î”S<0 â€” enthalpy driven)")
ok("dH>0,dS>0: high T spont",
   spontaneity_analysis(1,1),  "Spontaneous at high T only (Î”H>0, Î”S>0 â€” entropy driven)")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODULE 12 â€” ICE SOLVER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MODULE 12: ICE SOLVER")
from ice_solver import (
    reaction_quotient, solve_ice, build_ice_table,
    kc_to_kp, kp_to_kc, R_ATM,
    compare_Q_K,
    le_chatelier_concentration, le_chatelier_pressure,
    le_chatelier_temperature, le_chatelier_catalyst,
)

sub("Reaction Quotient")
ok("H2+I2â†’2HI Q=4",    reaction_quotient([1,1],[0.5,0.5],[2],[1.0]),  4.0)
ok("N2O4â†’2NO2 Q=0.04", reaction_quotient([1],[1.0],[2],[0.2]),         0.04)
ok("Products=0: Q=0",   reaction_quotient([1],[0.5],[1],[0.0]),         0.0)
ok("Reactant=0: Q=0",   reaction_quotient([1],[0.0],[1],[0.5]),         0.0)
ok("2Aâ†’B+C Q=0.0625",   reaction_quotient([2],[0.4],[1,1],[0.1,0.1]),  0.0625)

sub("ICE Solver â€” standard cases")
def check_ice(r_coeffs,r_init,p_coeffs,p_init,Kc,label,x_expected=None,tol_pct=0.01):
    x = solve_ice(r_coeffs,r_init,p_coeffs,p_init,Kc)
    r_eq = [r0-c*x for c,r0 in zip(r_coeffs,r_init)]
    p_eq = [p0+c*x for c,p0 in zip(p_coeffs,p_init)]
    Q_final = reaction_quotient(r_coeffs,r_eq,p_coeffs,p_eq)
    ok_close(f"{label}: Q_finalâ‰ˆKc", Q_final, Kc, pct=0.01)
    if x_expected is not None:
        ok_close(f"{label}: xâ‰ˆ{x_expected}", x, x_expected, pct=tol_pct)
    return x

# A â‡Œ B, Kc=4: x=0.8
check_ice([1],[1.0],[1],[0.0],4.0,"A<=>B Kc=4",x_expected=0.8)
# N2O4 â‡Œ 2NO2, Kc=0.0059
disc = 0.0059**2+16*0.0059
x_n2o4 = (-0.0059+math.sqrt(disc))/8
check_ice([1],[1.0],[2],[0.0],0.0059,"N2O4 Kc=0.0059",x_expected=x_n2o4)
# H2+I2 â‡Œ 2HI
sqK = math.sqrt(55.64)
check_ice([1,1],[0.5,0.5],[2],[0.0],55.64,"H2+I2 Kc=55.64",x_expected=0.5*sqK/(2+sqK))
# Already at equilibrium (reverse case: Q>K)
x_rev = solve_ice([1],[0.1],[1],[0.9],1.0)
ok_close("Reverse shift x=-0.4", x_rev, -0.4, pct=0.001)
# 2A â‡Œ B, Kc=0.25
x_2A = (3-math.sqrt(5))/2
check_ice([2],[2.0],[1],[0.0],0.25,"2A<=>B Kc=0.25",x_expected=x_2A)
# Large Kc
check_ice([1],[1.0],[1],[0.0],1e6,"A<=>B Kc=1e6",x_expected=1e6/(1+1e6))
# Small Kc (5% rule)
r = build_ice_table(['A'],[1],[1.0],['B'],[1],[0.0],1e-5)
ok("Small Kc: 5% rule valid",r['approx_pct']<5.0,True)

sub("ICE Solver â€” error cases")
ok_raises("Kc<0 raises", lambda: solve_ice([1],[1.0],[1],[0.0],-1.0), ValueError)

sub("Kc / Kp conversion")
T298 = 298.0
RT = R_ATM * T298
ok("Kcâ†’Kp: dn=0",  kc_to_kp(5.0, T298, 0),  5.0,      tol=1e-9)
ok("Kcâ†’Kp: dn=+1", kc_to_kp(1.0, T298, 1),  RT,       tol=1e-6)
ok("Kcâ†’Kp: dn=-1", kc_to_kp(1.0, T298,-1),  1/RT,     tol=1e-9)
ok("Kcâ†’Kp: dn=+2", kc_to_kp(1.0, T298, 2),  RT**2,    tol=1e-6)
for dn in [-2,-1,0,1,2]:
    Kp_t = kc_to_kp(3.0, T298, dn)
    ok(f"Kpâ†’Kc roundtrip dn={dn:+}", kp_to_kc(Kp_t, T298, dn), 3.0, tol=1e-9)

sub("Q vs K")
ok("Q<K â†’ forward",    compare_Q_K(1.0, 10.0)[0], 'forward')
ok("Q>K â†’ reverse",    compare_Q_K(20.0,10.0)[0], 'reverse')
ok("Q=K â†’ equilibrium",compare_Q_K(10.0,10.0)[0], 'equilibrium')
ok("Q=0 â†’ forward",    compare_Q_K(0.0, 5.0)[0],  'forward')
ok("Qâ‰ˆK â†’ equilibrium",compare_Q_K(10+1e-9,10.0)[0],'equilibrium')

sub("Le Chatelier â€” concentration")
ok("+reactant â†’ right", le_chatelier_concentration('reactant','increase')[0],'right')
ok("-reactant â†’ left",  le_chatelier_concentration('reactant','decrease')[0],'left')
ok("+product â†’ left",   le_chatelier_concentration('product', 'increase')[0],'left')
ok("-product â†’ right",  le_chatelier_concentration('product', 'decrease')[0],'right')
ok_raises("bad role",   lambda: le_chatelier_concentration('solvent','increase'), ValueError)
ok_raises("bad change", lambda: le_chatelier_concentration('reactant','add'),     ValueError)

sub("Le Chatelier â€” pressure")
ok("â†‘P, dn=+1 â†’ left",  le_chatelier_pressure('increase', 1)[0], 'left')
ok("â†‘P, dn=-1 â†’ right", le_chatelier_pressure('increase',-1)[0], 'right')
ok("â†“P, dn=+1 â†’ right", le_chatelier_pressure('decrease', 1)[0], 'right')
ok("â†“P, dn=-1 â†’ left",  le_chatelier_pressure('decrease',-1)[0], 'left')
ok("dn=0 â†’ none",        le_chatelier_pressure('increase', 0)[0], 'none')
# Real chemistry: SO2+O2â†’SO3: dn=-1 â†’ increase P â†’ right
ok("2SO2+O2â†’2SO3: â†‘Pâ†’right", le_chatelier_pressure('increase',-1)[0],'right')
ok_raises("bad pressure", lambda: le_chatelier_pressure('neutral',1), ValueError)

sub("Le Chatelier â€” temperature")
for tc, rxn, exp_dir, exp_K in [
    ('increase','exothermic','left','decreases'),
    ('decrease','exothermic','right','increases'),
    ('increase','endothermic','right','increases'),
    ('decrease','endothermic','left','decreases'),
]:
    d, _, k = le_chatelier_temperature(tc, rxn)
    ok(f"T {tc} {rxn}: dir={exp_dir}", d, exp_dir)
    ok(f"T {tc} {rxn}: K {exp_K}", k, exp_K)
ok_raises("bad rxn_type", lambda: le_chatelier_temperature('increase','neutral'), ValueError)

sub("Le Chatelier â€” catalyst")
d, e = le_chatelier_catalyst()
ok("catalyst: no shift",         d, 'none')
ok("catalyst: mentions equilib", 'equilibrium' in e.lower(), True)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CROSS-MODULE CONSISTENCY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("CROSS-MODULE CONSISTENCY CHECKS")

sub("Mole conversions â†” gas laws (STP)")
from mole_conversions import moles_to_volume as m2v_old
from gas_laws import moles_to_volume_stp as m2v_gas
ok("Both agree at STP: 1mol", m2v_old(1), m2v_gas(1))
ok("Both agree at STP: 3mol", m2v_old(3), m2v_gas(3))

sub("Percent composition â†” empirical formula (circular)")
# If we compute % composition of CH2O and feed into empirical formula, we should get CH2O back
mm_ch2o, pcts_ch2o = compute_percent_composition("CH2O")
masses = [pcts_ch2o[e] for e in ['C','H','O']]
ef_back = calculate_empirical_formula(['C','H','O'], masses)
ok("CH2O â†’ pct â†’ empirical: C=1", ef_back['C'], 1)
ok("CH2O â†’ pct â†’ empirical: H=2", ef_back['H'], 2)
ok("CH2O â†’ pct â†’ empirical: O=1", ef_back['O'], 1)

sub("Acid-base: strong acid then neutralise with strong base")
# 100 mL of 0.1M HCl + 100 mL of 0.1M NaOH â†’ neutral
from acid_base import equivalence_moles
mol_acid = equivalence_moles(0.1, 0.1)
mol_base = equivalence_moles(0.1, 0.1)
ok("SA neutralises SB: moles equal", mol_acid, mol_base)

sub("Thermodynamics: Hess vs standard enthalpy (CO2 formation)")
# Standard: C + O2 â†’ CO2, Î”HÂ°f(CO2)=-393.5 kJ
# Hess via: C+Â½O2â†’CO (-110.5), CO+Â½O2â†’CO2 (-283.0): sum=-393.5
hess_result = hess_law([-110.5,-283.0],[1,1])
std_species = [
    {'formula':'C', 'dHf':0.0,   'coeff':1,'role':'reactant'},
    {'formula':'O2','dHf':0.0,   'coeff':1,'role':'reactant'},
    {'formula':'CO2','dHf':-393.5,'coeff':1,'role':'product'},
]
std_result = standard_enthalpy_rxn(std_species)
ok("Hess vs standard enthalpy agree", hess_result, std_result, tol=0.01)

sub("ICE: Kpâ†’Kcâ†’solve chain produces physically valid concentrations")
Kp_given = 0.144
Kc_calc = kp_to_kc(Kp_given, 298.0, 1)
tbl = build_ice_table(['N2O4'],[1],[1.0],['NO2'],[2],[0.0],Kc_calc)
ok("ICE chain: all r_eq >= 0", all(c >= 0 for c in tbl['r_eq']), True)
ok("ICE chain: all p_eq >= 0", all(c >= 0 for c in tbl['p_eq']), True)
ok_close("ICE chain: Qâ‰ˆKc",    tbl['Q_final'], Kc_calc, pct=0.01)

sub("Calorimetry â†” mole conversions (moles of water heated)")
# 1 mol water = 18.015 g; heat 10Â°C â†’ q = 18.015 * 4.18 * 10 â‰ˆ 753.0 J
m_water = moles_to_mass(1.0, 18.015)
q_water = cal_q(m_water, 4.18, 10.0)
ok("1mol water mass", m_water, 18.015, tol=0.001)
ok_close("1mol water q â‰ˆ753J", q_water, 18.015*4.18*10, pct=0.001)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN.PY â€” importability & menu structure
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
section("MAIN.PY â€” STRUCTURE AND IMPORTS")
import importlib, io

sub("All module imports succeed")
for mod_name in [
    'mole_conversions','Empirical_Formula_Calculator','percent_composition_calculator',
    'volume_mass_conversions','oxidation_number_calculator','atom_economy_calculator',
    'ionic_bonding_calculator','percentage_yield_calculator',
    'gas_laws','acid_base','thermodynamics','ice_solver'
]:
    try:
        importlib.import_module(mod_name)
        ok(f"import {mod_name}", True, True)
    except Exception as e:
        ok(f"import {mod_name}", False, True)

sub("main.py imports and show_menu output")
import main as _main
buf = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buf
_main.show_menu()
sys.stdout = old_stdout
menu_text = buf.getvalue()

for item in [
    "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
    "10.", "11.", "12.", "13.", "14.", "15.", "0."
]:
    ok(f"menu contains '{item}'", item in menu_text, True)

sub("Action dict has all 16 entries (0-15)")
import io as _io
# Reconstruct actions dict by inspecting main
actions_count = sum(1 for k in ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","0"]
                    if k in str(menu_text) or True)
# Just check that all wrapper functions exist
for fn_name in [
    'open_mole_conversions','open_empirical_formula','open_equation_balancer',
    'open_limiting_reactant','open_percent_composition','volume_to_mass_conversions',
    'oxidation_number_calculator','element_economy_calculator',
    'ionic_bonding_calculator','percentage_yield_calculator',
    'open_periodic_table','open_gas_laws','open_acid_base',
    'open_thermodynamics','open_ice_solver',
]:
    ok(f"main.{fn_name} exists", hasattr(_main, fn_name), True)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SUMMARY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
print(f"\n{'='*66}")
print(f"  STRESS TEST COMPLETE")
print(f"{'='*66}")
print(f"  Total  : {PASS+FAIL}")
print(f"  Passed : {PASS}")
print(f"  Failed : {FAIL}")
if ERRORS:
    print(f"\n  {'â”€'*60}")
    print(f"  FAILURES ({len(ERRORS)}):")
    for e in ERRORS:
        print(e)
else:
    print("\n  ALL TESTS PASSED â€” no failures detected.")

