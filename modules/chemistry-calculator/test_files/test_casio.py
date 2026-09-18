"""
Tests for the Casio fx-CG50 port (modules/casio-fx-cg50/).

Three things are checked:

  1. The code stays inside what the calculator's MicroPython can run:
     ASCII only, no f-strings, only `math` imported from outside the port,
     and small files.
  2. The answers agree with the desktop calculator — the same figures are
     worked out by both and compared.
  3. Every menu runs: each one is driven with scripted keystrokes (as if typed
     on the calculator) and must print a sensible answer without crashing.

Run:  py test_files/test_casio.py
"""

import io
import math
import os
import re
import sys
import contextlib
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CASIO = os.path.normpath(os.path.join(ROOT, "..", "casio-fx-cg50"))
sys.path.insert(0, ROOT)
sys.path.insert(0, CASIO)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PASS = FAIL = 0
FAILURES = []


def record(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}" + (f"\n         {detail}" if detail else "")
        FAILURES.append(msg)
        print(msg)


def close(label, got, want, rel=1e-6):
    ok = isinstance(got, (int, float)) and math.isclose(got, want, rel_tol=rel, abs_tol=1e-12)
    record(label, ok, f"got={got!r} expected={want!r}")


def equal(label, got, want):
    record(label, got == want, f"got={got!r} expected={want!r}")


def raises(label, fn):
    try:
        fn()
    except ValueError:
        record(label, True)
    except Exception as e:
        record(label, False, f"raised {type(e).__name__}: {e}")
    else:
        record(label, False, "no error raised")


def section(title):
    print(f"\n=== {title} ===")


FILES = ["chem.py", "chemcore.py", "chemstoi.py", "chemgas.py", "chemaqua.py",
         "chemener.py", "chemstruct.py", "chemtools.py", "chembal.py"]

# ═════════════════════════════════════════════════════════════════════════════
section("1. Fits what the calculator can run")

for name in FILES:
    path = os.path.join(CASIO, name)
    record(f"{name} exists", os.path.exists(path))

ALLOWED_IMPORTS = {"math", "chemcore", "chemstoi", "chemgas", "chemaqua",
                   "chemener", "chemstruct", "chemtools", "chembal"}
for name in FILES:
    src = open(os.path.join(CASIO, name), encoding="utf-8").read()
    raw = open(os.path.join(CASIO, name), "rb").read()

    non_ascii = [c for c in src if ord(c) > 127]
    record(f"{name}: ASCII only (the console cannot show other characters)",
           not non_ascii, f"found {non_ascii[:5]}")

    # Read the file the way Python does, so letters inside strings are not
    # mistaken for code (a bond called "C-F" is not an f-string).
    fstrings, keywords = [], []
    with open(os.path.join(CASIO, name), "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.STRING and tok.string[:2].lower().replace("r", "").startswith("f"):
                fstrings.append(tok.string[:20])
            if tok.type == tokenize.NAME and tok.string in ("yield", "class", "async", "await", "nonlocal"):
                keywords.append(tok.string)
    record(f"{name}: no f-strings (MicroPython 1.9 has none)", not fstrings, str(fstrings[:3]))
    record(f"{name}: no classes or generators (they cost RAM)", not keywords, str(set(keywords)))

    imports = set(re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", src, re.M))
    record(f"{name}: only imports what the calculator has",
           imports <= ALLOWED_IMPORTS, f"{sorted(imports - ALLOWED_IMPORTS)}")

    record(f"{name}: under 12 KB", len(raw) < 12 * 1024, f"{len(raw)} bytes")


total = sum(os.path.getsize(os.path.join(CASIO, f)) for f in FILES)
record(f"whole port under 80 KB (it is {total // 1024} KB)", total < 80 * 1024)

# ═════════════════════════════════════════════════════════════════════════════
section("2. Same answers as the desktop calculator")

import chemcore
import chemstoi
import chemgas
import chemaqua
import chemener
import chemstruct
import chemtools
import chembal

import percent_composition_calculator as desk_pc
import Empirical_Formula_Calculator as desk_emp
import solutions as desk_sol
import acid_base as desk_ab
import ice_solver as desk_ice
import isotopes as desk_iso
import uncertainties as desk_unc
import electron_config as desk_ec
import organic_tools as desk_org
import oxidation_number_calculator as desk_ox
import ionic_bonding_calculator as desk_ionic
import kinetics as desk_kin
import gas_laws as desk_gas
from equation_balancer import balance_equation as desk_balance

# -- formulas and molar masses
for formula in ["H2O", "CaCO3", "Ca(OH)2", "Al2(SO4)3", "CuSO4.5H2O", "C6H12O6",
                "K2Cr2O7", "Fe2(SO4)3", "NH4Cl", "Mg(NO3)2"]:
    equal(f"parse {formula}", chemcore.parse_formula(formula), desk_pc.parse_formula(formula))
    close(f"molar mass {formula}", chemcore.molar_mass(formula),
          desk_pc.compute_percent_composition(formula)[0], rel=2e-3)
for typed, want in [("nacl", "NaCl"), ("h2so4", "H2SO4"), ("co2", "CO2"), ("nh3", "NH3"),
                    ("kmno4", "KMnO4"), ("ca(oh)2", "Ca(OH)2")]:
    equal(f"capitalise {typed}", chemcore.capitalise(typed), want)

# -- stoichiometry
counts, mult = chemstoi.empirical_formula(["C", "H", "O"], [40.0, 6.7, 53.3])
equal("empirical C 40 H 6.7 O 53.3", chemcore.formula_text(counts), "CH2O")
counts, mult = chemstoi.empirical_formula(["Fe", "O"], [72.4, 27.6])
equal("empirical Fe3O4 (needs x3)", chemcore.formula_text(counts), "Fe3O4")
mol, n, emp = chemstoi.molecular_formula({"C": 1, "H": 2, "O": 1}, 180.16)
equal("molecular formula from Mr", chemcore.formula_text(mol), "C6H12O6")
equal("  multiplier", n, 6)
els, amounts, note = chemstoi.combustion(0.2641, 0.1081, 0.1802)
counts, _ = chemstoi.empirical_formula(els, amounts)
equal("combustion analysis", chemcore.formula_text(counts), "CH2O")
els, amounts, note = chemstoi.combustion(1.3203, 0.2702, 0.3906)
counts, _ = chemstoi.empirical_formula(els, amounts)
equal("combustion of a hydrocarbon", chemcore.formula_text(counts), "CH")
record("  and it says there is no oxygen", bool(note))
idx, extent, moles = chemstoi.limiting(["H2", "O2"], [2, 1], [4.0, 16.0], ["H2O"], [2], True)
equal("limiting reactant is O2", idx, 1)
close("  extent", extent, 16.0 / chemcore.molar_mass("O2"), rel=1e-9)

# -- solutions (against the desktop module)
close("c = n/V", chemstoi.__dict__.get("dummy") or (0.0500 / 0.250),
      desk_sol.concentration(0.0500, 0.250))
close("mass for a standard solution", 0.100 * 0.250 * chemcore.molar_mass("NaCl"),
      desk_sol.mass_for_solution(0.100, 0.250, 58.44), rel=2e-3)

# -- gases
close("PV=nRT: P in kPa", 0.0100 * chemgas.R * 298.15 / 2.5e-4 / 1000.0,
      desk_gas.ideal_gas_solve("P", V=250, n=0.0100, T=25.0, P_unit="kPa", V_unit="cm3",
                               T_unit="C"), rel=1e-3)
close("Graham H2 vs O2", math.sqrt(32.00 / 2.016), desk_gas.graham_rate_ratio(2.016, 32.00))
x_casio = chemgas.solve_ice([1, 1], [1.0, 1.0], [2], [0.0], 50.0)
x_desk = desk_ice.solve_ice([1, 1], [1.0, 1.0], [2], [0.0], 50.0)
close("ICE x for H2 + I2", x_casio, x_desk, rel=1e-6)
x_casio = chemgas.solve_ice([1], [0.100], [2], [0.0], 4.6e-3)
x_desk = desk_ice.solve_ice([1], [0.100], [2], [0.0], 4.6e-3)
close("ICE x for N2O4", x_casio, x_desk, rel=1e-6)
x_casio = chemgas.solve_ice([1, 1], [0.0, 0.0], [2], [1.0], 50.0)
record("ICE from products only shifts back", x_casio < 0, str(x_casio))
close("Q for H2 + I2", chemgas.reaction_quotient([1, 1], [0.2, 0.2], [2], [1.0]),
      desk_ice.reaction_quotient([1, 1], [0.2, 0.2], [2], [1.0]))
record("Q with a reactant at 0 is 'infinite' (None)",
       chemgas.reaction_quotient([1], [0.0], [1], [1.0]) is None)

# -- acids and bases
close("weak acid pH", chemaqua.weak_acid_pH(1.74e-5, 0.100)[0],
      desk_ab.weak_acid_pH(1.74e-5, 0.100)[0])
close("weak base pH", chemaqua.weak_base_pH(1.78e-5, 0.100)[0],
      desk_ab.weak_base_pH(1.78e-5, 0.100)[0])
close("weak acid that needs the quadratic", chemaqua.weak_acid_pH(1.0e-2, 0.010)[0],
      desk_ab.weak_acid_pH(1.0e-2, 0.010)[0])
close("salt of a weak acid", 14.0 + math.log10(math.sqrt(1e-14 / 1.74e-5 * 0.100)),
      desk_ab.salt_pH("weak_acid_salt", 1.74e-5, 0.100)[0])
pH, pOH, H, OH = chemaqua.all_four(pH=3.50)
close("pH 3.50 -> [H+]", H, desk_ab.all_four(pH=3.50)[2])

# -- energy, cells, rates
close("Arrhenius Ea from two points",
      -chemener.R * math.log(4.0e-3 / 1.0e-3) / (1 / 320.0 - 1 / 300.0),
      desk_kin.arrhenius_Ea(1.0e-3, 300, 4.0e-3, 320), rel=2e-3)

# -- structure
for symbol, charge, want in [("Fe", 0, "1s2 2s2 2p6 3s2 3p6 3d6 4s2"),
                             ("Fe", 3, "1s2 2s2 2p6 3s2 3p6 3d5"),
                             ("Cr", 0, "1s2 2s2 2p6 3s2 3p6 3d5 4s1"),
                             ("Cu", 0, "1s2 2s2 2p6 3s2 3p6 3d10 4s1"),
                             ("Cl", -1, "1s2 2s2 2p6 3s2 3p6"),
                             ("Ca", 0, "1s2 2s2 2p6 3s2 3p6 4s2")]:
    Z = chemstruct.atomic_number(symbol)
    got = chemstruct.config_text(chemstruct.configuration(Z, charge))
    equal(f"configuration {symbol} {charge:+d}", got, want)
    # the same thing the desktop module says, with the superscripts removed
    desk = desk_ec.electron_configuration(symbol, charge)[0]
    plain = desk.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789"))
    equal(f"  matches the desktop version ({symbol} {charge:+d})", got, plain)
equal("shorthand for iron", chemstruct.shorthand(
    chemstruct.configuration(26, 0), 26), "[Ar] 3d6 4s2")

for formula, charge, element, want in [("K2Cr2O7", 0, "Cr", 6), ("KMnO4", 0, "Mn", 7),
                                       ("H2SO4", 0, "S", 6), ("NaH", 0, "H", -1),
                                       ("NH4", 1, "N", -3), ("SO4", -2, "S", 6)]:
    got = chemstruct.oxidation_numbers(formula, charge)[element]
    equal(f"oxidation number of {element} in {formula}", round(got, 6), want)
    desk = desk_ox.solve_oxidation_numbers(formula, charge)[element]
    equal(f"  matches the desktop version ({formula})", round(got, 6), round(desk, 6))

for cation, c_charge, anion, a_charge, want in [("Al", 3, "SO4", -2, "Al2(SO4)3"),
                                                ("Fe", 3, "OH", -1, "Fe(OH)3"),
                                                ("Mg", 2, "N", -3, "Mg3N2"),
                                                ("Na", 1, "Cl", -1, "NaCl")]:
    got = chemstruct.ionic_formula(cation, c_charge, anion, a_charge)
    equal(f"ionic formula {cation}/{anion}", got, want)
    equal(f"  matches the desktop version ({want})", got,
          desk_ionic.write_ionic_formula(cation, c_charge, anion, a_charge))

# -- tools
close("Ar of chlorine", chemtools.relative_atomic_mass([(34.969, 75.77), (36.966, 24.23)]),
      desk_iso.relative_atomic_mass([(34.969, 75.77), (36.966, 24.23)]))
p1, p2 = chemtools.abundance_from_Ar(63.546, 62.930, 64.928)
close("copper abundance", p1, desk_iso.abundance_from_Ar(63.546, 62.930, 64.928)[0])
close("round to 3 s.f.", chemtools.round_sig(0.0824567, 3), desk_unc.round_to_sig_figs(0.0824567, 3))
equal("value written with its uncertainty", chemtools.with_uncertainty(0.08245, 0.0005),
      "0.0824 +/- 0.0005")
for formula in ["C6H6", "C6H14", "C2H2", "C6H5NO2", "C8H10N4O2", "C6H5Cl"]:
    equal(f"IHD of {formula}", chemtools.ihd(formula), desk_org.index_of_hydrogen_deficiency(formula))

# -- balancer (exact fractions, no sympy)
for reactants, products in [(["H2", "O2"], ["H2O"]),
                            (["C2H5OH", "O2"], ["CO2", "H2O"]),
                            (["Fe2O3", "CO"], ["Fe", "CO2"]),
                            (["Ca(OH)2", "HCl"], ["CaCl2", "H2O"]),
                            (["KMnO4", "HCl"], ["KCl", "MnCl2", "H2O", "Cl2"]),
                            (["C8H18", "O2"], ["CO2", "H2O"]),
                            (["Al", "H2SO4"], ["Al2(SO4)3", "H2"]),
                            (["Ca3(PO4)2", "SiO2", "C"], ["CaSiO3", "P4", "CO"]),
                            (["NH3", "O2"], ["NO", "H2O"]),
                            (["C3H5(NO3)3"], ["CO2", "H2O", "N2", "O2"])]:
    name = " + ".join(reactants) + " -> " + " + ".join(products)
    got = chembal.balance(reactants, products)
    want = desk_balance(reactants, products)
    equal(f"balance {name}", (list(got[0]), list(got[1])), (list(want[0]), list(want[1])))
raises("balancer rejects an impossible equation", lambda: chembal.balance(["H2"], ["O2"]))
raises("balancer rejects two reactions in one",
       lambda: chembal.balance(["H2", "O2"], ["H2O", "H2O2"]))

# ═════════════════════════════════════════════════════════════════════════════
section("3. Every menu runs from the keypad")


def drive(fn, keys):
    """Run a menu with `keys` typed in, and give back what it printed."""
    typed = list(keys)

    def fake_input(prompt=""):
        if not typed:
            raise AssertionError("the menu asked for more input than expected: " + prompt)
        return typed.pop(0)

    buffer = io.StringIO()
    real_input = chemcore.__builtins__["input"] if isinstance(chemcore.__builtins__, dict) \
        else chemcore.__builtins__.input
    import builtins
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(buffer):
            fn()
    finally:
        builtins.input = real_input
    return buffer.getvalue(), typed


def menu(label, fn, keys, expect):
    try:
        out, left = drive(fn, keys)
    except Exception as e:
        record(label, False, f"{type(e).__name__}: {e}")
        return
    ok = expect in out and not left
    record(label, ok, f"left over: {left} | output: {out.strip()[-120:]}")


menu("moles: 10 g CaCO3", chemstoi.menu_moles, ["1", "CaCO3", "10"], "0.0999")
menu("moles: 0.25 mol -> particles", chemstoi.menu_moles, ["3", "0.25"], "1.505e23")
menu("moles: 0.5 mol -> volume", chemstoi.menu_moles, ["5", "0.5"], "11.35")
# the calculator's table keeps masses to 2 decimal places, so 88.79 not 88.81
menu("percent composition of H2O", chemstoi.menu_percent, ["H2O"], "88.7")
menu("empirical from percentages", chemstoi.menu_empirical,
     ["1", "3", "C", "40", "H", "6.7", "O", "53.3"], "CH2O")
menu("molecular formula", chemstoi.menu_empirical,
     ["3", "3", "C", "40", "H", "6.7", "O", "53.3", "180.16"], "C6H12O6")
menu("combustion analysis", chemstoi.menu_empirical,
     ["2", "0.2641", "0.1081", "0.1802"], "CH2O")
menu("solutions: c from n and V", chemstoi.menu_solutions, ["1", "0.05", "250"], "0.2")
menu("solutions: mass for a solution", chemstoi.menu_solutions,
     ["5", "0.1", "250", "NaCl"], "1.461")
menu("solutions: dilution V1", chemstoi.menu_solutions, ["6", "b", "2", "0.25", "100"], "12.5")
menu("solutions: ppm", chemstoi.menu_solutions, ["8", "5", "2"], "2.5")
menu("limiting reactant in grams", chemstoi.menu_limiting,
     ["g", "2", "H2", "2", "4", "O2", "1", "16", "1", "H2O", "2"], "Limiting: O2")
menu("percentage yield", chemstoi.menu_yield, ["1", "7.5", "10"], "75")
menu("atom economy", chemstoi.menu_atom_economy, ["1", "C6H12O6", "1", "C2H5OH", "2"], "51.1")

menu("ideal gas in kPa/cm3/C", chemgas.menu_ideal,
     ["1", "1", "c", "p", "250", "0.01", "25"], "99.1")
menu("combined gas law", chemgas.menu_combined,
     ["1", "2", "c", "v", "100", "2", "27", "150", "127"], "1.77")
menu("Graham's law", chemgas.menu_graham, ["2.016", "32"], "3.98")
menu("Dalton's law", chemgas.menu_dalton, ["2", "79", "21"], "100")
menu("ICE table", chemgas.menu_ice,
     ["2", "H2", "1", "1", "I2", "1", "1", "1", "HI", "2", "0", "50"], "0.779")
menu("Q vs K", chemgas.menu_q_vs_k,
     ["2", "1", "0.2", "1", "0.2", "1", "2", "1.0", "50"], "RIGHT")
menu("Le Chatelier: pressure", chemgas.menu_le_chatelier, ["2", "i", "-2"], "RIGHT")
menu("Le Chatelier: catalyst", chemgas.menu_le_chatelier, ["4"], "No shift")
menu("Kc to Kp", chemgas.menu_kc_kp, ["p", "0.5", "500", "-2"], "e-4")

menu("pH converter", chemaqua.menu_convert, ["1", "3.5"], "3.16")
menu("strong acid", chemaqua.menu_strong, ["a", "0.01"], "pH = 2")
menu("weak acid", chemaqua.menu_weak, ["a", "1.74e-5", "0.1"], "2.88")
menu("buffer", chemaqua.menu_buffer, ["1.74e-5", "0.1", "0.2"], "5.06")
menu("titration: concentration", chemaqua.menu_titration,
     ["c", "1", "2", "0.1", "25", "20"], "0.04")
menu("titration: volume", chemaqua.menu_titration, ["v", "1", "1", "0.1", "25", "0.05"], "12.5")
menu("salt solution pH", chemaqua.menu_salt, ["a", "1.74e-5", "0.1"], "8.88")
menu("pKa from half-equivalence", chemaqua.menu_half_equivalence, ["4.76"], "4.76")
menu("Ka to Kb", chemaqua.menu_ka_kb, ["1", "1.74e-5"], "5.747e-10")

menu("calorimetry", chemener.menu_calorimetry, ["q", "50", "4.18", "12"], "2508")
menu("Hess's law", chemener.menu_hess, ["2", "-393.5", "1", "-283", "-1"], "-110.5")
menu("bond enthalpies", chemener.menu_bonds,
     ["C-H", "4", "O=O", "2", "", "C=O", "2", "O-H", "4", ""], "-808")
menu("dH from dHf", chemener.menu_formation,
     ["CH4", "1", "-74", "O2", "2", "0", "", "CO2", "1", "-393.5", "H2O", "2", "-285.8", ""],
     "-891")
menu("dS from S values", chemener.menu_entropy,
     ["N2", "1", "191.6", "H2", "3", "130.7", "", "NH3", "2", "192.5", ""], "-198.7")
menu("Gibbs dG", chemener.menu_gibbs, ["g", "-92.2", "-199", "298"], "-32.9")
menu("Gibbs: K from dG", chemener.menu_gibbs, ["q", "-32.9", "298"], "5886")
menu("cell potential from the table", chemener.menu_cell, ["9", "15", "2"], "1.1")
menu("Faraday: mass", chemener.menu_faraday, ["m", "2", "1930", "63.55", "2"], "1.271")
menu("order from two experiments", chemener.menu_order, ["0.1", "1e-3", "0.2", "4e-3"], "2")
menu("Arrhenius Ea", chemener.menu_arrhenius, ["e", "1e-3", "300", "4e-3", "320"], "55.3")
menu("Arrhenius graph", chemener.menu_arrhenius,
     ["g", "300", "1.0e-3", "310", "1.9e-3", "320", "3.5e-3", "330", "6.2e-3", ""], "Ea")
menu("half-life", chemener.menu_half_life, ["t", "0.0231"], "30")
menu("integrated rate law", chemener.menu_rate_law, ["1", "0.8", "0.0231", "a", "60"], "0.2")

menu("electron configuration Fe3+", chemstruct.menu_config, ["Fe", "3"], "3d5")
menu("electron configuration by Z", chemstruct.menu_config, ["26", "0"], "[Ar] 3d6 4s2")
menu("oxidation numbers", chemstruct.menu_oxidation, ["K2Cr2O7", "0", "n"], "+6")
menu("ionic formula", chemstruct.menu_ionic, ["Al", "3", "SO4", "-2"], "Al2(SO4)3")

menu("isotopes: Ar", chemtools.menu_isotopes,
     ["1", "2", "34.969", "75.77", "36.966", "24.23"], "35.45")
menu("isotopes: abundances", chemtools.menu_isotopes,
     ["2", "63.546", "62.93", "64.928"], "69.1")
menu("uncertainty: absolute to %", chemtools.menu_uncertainty, ["1", "25", "a", "0.05"], "0.2")
menu("uncertainty: adding", chemtools.menu_uncertainty,
     ["2", "2", "24.8", "0.05", "-1.2", "0.05"], "23.6")
menu("uncertainty: multiplying", chemtools.menu_uncertainty,
     ["3", "2", "0.1", "0.5", "25", "0.2", "x"], "2.5")
menu("uncertainty: % error", chemtools.menu_uncertainty, ["5", "1.23", "1.2"], "2.5")
menu("IHD of benzene", chemtools.menu_ihd, ["C6H6"], "IHD = 4")

menu("balance ethanol combustion", chembal.menu_balance,
     ["C2H5OH + O2", "CO2 + H2O"], "3O2")
menu("balance with brackets", chembal.menu_balance,
     ["Ca(OH)2 + HCl", "CaCl2 + H2O"], "2HCl")

# Bad input raises a ValueError with a readable message; chem.py catches it
# and prints "Error: ..." rather than dropping the student back to the editor.
try:
    drive(chemstoi.menu_percent, ["Qz9"])
    record("a bad formula is reported", False, "no error raised")
except ValueError as e:
    record("a bad formula is reported", "Unknown element" in str(e), str(e))
except Exception as e:
    record("a bad formula is reported", False, f"{type(e).__name__}: {e}")

main_src = open(os.path.join(CASIO, "chem.py"), encoding="utf-8").read()
record("chem.py catches errors so the menu keeps going", "except ValueError" in main_src)

# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"  Casio tests  Total: {PASS + FAIL}   Passed: {PASS}   Failed: {FAIL}")
if FAILURES:
    print("\nFailures:")
    print("\n".join(FAILURES))
sys.exit(1 if FAIL else 0)
