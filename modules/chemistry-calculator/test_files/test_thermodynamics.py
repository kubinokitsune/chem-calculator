"""
Rigorous diagnostic for thermodynamics.py
Tests every function with known chemistry values.
"""
import sys, os, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from thermodynamics import (
    cal_q, cal_m, cal_c, cal_dT,
    hess_law,
    bond_enthalpy_dH, lookup_bond, BOND_ENTHALPIES,
    standard_enthalpy_rxn,
    gibbs_dG, gibbs_dH, gibbs_T, gibbs_dS,
    spontaneity, spontaneity_analysis,
    celsius_to_kelvin, SPECIFIC_HEATS
)

PASS = 0
FAIL = 0
ERRORS = []

def check(label, got, expected, tol=1e-6):
    global PASS, FAIL
    ok = abs(got - expected) <= tol if isinstance(expected, float) else (got == expected)
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}\n         got={got!r}  expected={expected!r}"
        ERRORS.append(msg)
        print(msg)

def check_raises(label, fn, exc=Exception):
    global PASS, FAIL
    try:
        fn()
        FAIL += 1
        msg = f"  [FAIL] {label}  â€” no exception raised"
        ERRORS.append(msg); print(msg)
    except exc:
        PASS += 1
        print(f"  [PASS] {label}  (raised {exc.__name__})")
    except Exception as e:
        FAIL += 1
        msg = f"  [FAIL] {label}  â€” wrong exception {type(e).__name__}: {e}"
        ERRORS.append(msg); print(msg)

def section(title):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print(f"{'='*62}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. CALORIMETRY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("1. CALORIMETRY  q = mcÎ”T")

# q = m*c*Î”T : water 200 g heated 10 Â°C  â†’ q = 200*4.18*10 = 8360 J
check("q = 200 g water, Î”T=10 K  â†’ 8360 J",    cal_q(200, 4.18, 10),   8360.0)
check("q = 50 g iron, Î”T=25 K   â†’ 561.25 J",   cal_q(50, 0.449, 25),   561.25)
check("q negative (cooling)",                    cal_q(100, 4.18, -5),  -2090.0)

# m = q / (c*Î”T)
check("m = 8360 / (4.18*10) = 200 g",           cal_m(8360, 4.18, 10),  200.0)

# c = q / (m*Î”T)
check("c = 8360 / (200*10) = 4.18 J/gÂ·K",       cal_c(8360, 200, 10),   4.18)

# Î”T = q / (m*c)
check("Î”T = 8360 / (200*4.18) = 10",            cal_dT(8360, 200, 4.18), 10.0)

# Î”T from T_final - T_initial
dT_manual = 35.0 - 22.5
check("Î”T = T_final - T_initial = 12.5",        dT_manual, 12.5)

# Roundtrip: solve for each variable and verify consistency
q_rt = cal_q(150, 2.44, 8)       # ethanol
m_rt = cal_m(q_rt, 2.44, 8)
c_rt = cal_c(q_rt, 150, 8)
dT_rt= cal_dT(q_rt, 150, 2.44)
check("Roundtrip qâ†’m", m_rt, 150.0, tol=1e-9)
check("Roundtrip qâ†’c", c_rt, 2.44,  tol=1e-9)
check("Roundtrip qâ†’Î”T", dT_rt, 8.0, tol=1e-9)

# Error cases
check_raises("c=0 â†’ ValueError", lambda: cal_m(100, 0, 10), ValueError)
check_raises("Î”T=0 â†’ ValueError for cal_m", lambda: cal_m(100, 4.18, 0), ValueError)
check_raises("m=0 â†’ ValueError for cal_c", lambda: cal_c(100, 0, 10), ValueError)
check_raises("c=0 â†’ ValueError for cal_dT", lambda: cal_dT(100, 50, 0), ValueError)

# Specific heat table
check("water c = 4.18 in table",    SPECIFIC_HEATS['water'],    4.18)
check("iron  c = 0.449 in table",   SPECIFIC_HEATS['iron'],     0.449)
check("copper c = 0.385 in table",  SPECIFIC_HEATS['copper'],   0.385)
check("aluminum c = 0.897 in table",SPECIFIC_HEATS['aluminum'], 0.897)

# celsius_to_kelvin
check("0Â°C = 273.15 K",   celsius_to_kelvin(0),    273.15)
check("100Â°C = 373.15 K", celsius_to_kelvin(100),  373.15)
check("-273.15Â°C = 0 K",  celsius_to_kelvin(-273.15), 0.0)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. HESS'S LAW
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("2. HESS'S LAW")

# Example: find Î”H for C + O2 â†’ CO2
# Using: (1) C + 1/2 O2 â†’ CO      Î”H1 = -110.5 kJ  (keep, Ã—+1)
#        (2) CO + 1/2 O2 â†’ CO2    Î”H2 = -283.0 kJ  (keep, Ã—+1)
# Target: C + O2 â†’ CO2  Î”H = -393.5 kJ
check("Hess: CO path â†’ CO2 = -393.5 kJ",
      hess_law([-110.5, -283.0], [1, 1]), -393.5, tol=1e-9)

# Example: flip one reaction
# (1) 2H2 + O2 â†’ 2H2O    Î”H = -572 kJ  (flip â†’ 2H2O â†’ 2H2 + O2, Ã—-1)
# (2) C + O2 â†’ CO2        Î”H = -393.5 kJ  (keep, Ã—+1)
# Î”H_total = 572 + (-393.5) = +178.5 kJ
check("Hess: flip + keep = +178.5 kJ",
      hess_law([-572, -393.5], [-1, 1]), 178.5, tol=1e-9)

# Scale a reaction by 0.5
check("Hess: scale 0.5 Ã— (-572) = -286 kJ",
      hess_law([-572], [0.5]), -286.0, tol=1e-9)

# Three-step Hess's law
# Standard formation of C3H8 (propane): known Î”HÂ°f = -103.8 kJ
# Verify via combustion steps (simplified closure test)
dH_steps = [-393.5, -285.8, 2220.0]  # CO2 formation, H2O formation, propane combustion (flipped)
mults     = [3,       4,      -1]
# 3Ã—(-393.5) + 4Ã—(-285.8) + (-1)Ã—(2220.0) = -1180.5 - 1143.2 - 2220.0 = ... closure check
expected3 = 3*(-393.5) + 4*(-285.8) + (-1)*2220.0
check("Hess 3-step arithmetic correct",
      hess_law(dH_steps, mults), expected3, tol=1e-6)

# Error: length mismatch
check_raises("Hess mismatched lengths",
             lambda: hess_law([1, 2], [1]), ValueError)

# Single step, multiplier = 1
check("Hess 1-step identity", hess_law([-241.8], [1]), -241.8, tol=1e-9)
# Single step, flip
check("Hess 1-step flip",     hess_law([-241.8], [-1]), 241.8, tol=1e-9)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. BOND ENTHALPY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("3. BOND ENTHALPY")

# CH4 + 2O2 â†’ CO2 + 2H2O
# Bonds broken: 4 C-H (413) + 2 O=O (498) = 1652 + 996 = 2648 kJ
# Bonds formed: 2 C=O (805) + 4 O-H (463) = 1610 + 1852 = 3462 kJ
# Î”H â‰ˆ 2648 - 3462 = -814 kJ
broken = [("C-H", 4, 413), ("O=O", 2, 498)]
formed = [("C=O", 2, 805), ("O-H", 4, 463)]
dH, sb, sf = bond_enthalpy_dH(broken, formed)
check("CH4+O2: sum broken = 2648 kJ",   sb,  2648.0, tol=1e-9)
check("CH4+O2: sum formed = 3462 kJ",   sf,  3462.0, tol=1e-9)
check("CH4+O2: Î”H â‰ˆ -814 kJ",           dH,  -814.0, tol=1e-9)

# H2 + Cl2 â†’ 2 HCl
# Broken: H-H (436) + Cl-Cl (242) = 678 kJ
# Formed: 2 Ã— H-Cl (431) = 862 kJ
# Î”H â‰ˆ 678 - 862 = -184 kJ
broken2 = [("H-H", 1, 436), ("Cl-Cl", 1, 242)]
formed2 = [("H-Cl", 2, 431)]
dH2, sb2, sf2 = bond_enthalpy_dH(broken2, formed2)
check("H2+Cl2: sum broken = 678 kJ",    sb2, 678.0, tol=1e-9)
check("H2+Cl2: sum formed = 862 kJ",    sf2, 862.0, tol=1e-9)
check("H2+Cl2: Î”H â‰ˆ -184 kJ",          dH2, -184.0, tol=1e-9)

# N2 + 3H2 â†’ 2NH3 (Haber process)
# Broken: N#N (945) + 3 H-H (3Ã—436=1308) = 2253 kJ
# Formed: 6 N-H (6Ã—391=2346) kJ
# Î”H â‰ˆ 2253 - 2346 = -93 kJ
broken3 = [("N#N", 1, 945), ("H-H", 3, 436)]
formed3 = [("N-H", 6, 391)]
dH3, sb3, sf3 = bond_enthalpy_dH(broken3, formed3)
check("Haber: sum broken = 2253 kJ",    sb3, 2253.0, tol=1e-9)
check("Haber: sum formed = 2346 kJ",    sf3, 2346.0, tol=1e-9)
check("Haber: Î”H â‰ˆ -93 kJ",            dH3,  -93.0, tol=1e-9)

# Zero bonds
dH_zero, sb_zero, sf_zero = bond_enthalpy_dH([], [])
check("Empty bonds: Î”H = 0",   dH_zero, 0.0)
check("Empty bonds: sb = 0",   sb_zero, 0.0)
check("Empty bonds: sf = 0",   sf_zero, 0.0)

# lookup_bond â€” canonical key
check("lookup C-H = 413",       lookup_bond("C-H"),  413)
check("lookup O=O = 498",       lookup_bond("O=O"),  498)
check("lookup N#N = 945",       lookup_bond("N#N"),  945)
# Reversed keys should also resolve
check("lookup H-C (reversed) = 413", lookup_bond("H-C"),  413)
check("lookup O-H (reversed) = 463", lookup_bond("O-H"),  463)
# Non-existent key returns None
check("lookup Xx-Yy = None",    lookup_bond("Xx-Yy"), None)

# Verify entire table has no duplicate values for canonical keys
all_keys = list(BOND_ENTHALPIES.keys())
check("All bond table keys are unique", len(all_keys), len(set(all_keys)))


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. STANDARD ENTHALPY OF REACTION
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("4. STANDARD ENTHALPY OF REACTION  dH_rxn")

# CH4(g) + 2 O2(g) â†’ CO2(g) + 2 H2O(l)
# Î”HÂ°f: CH4 = -74.8, O2 = 0, CO2 = -393.5, H2O(l) = -285.8 kJ/mol
# Î”HÂ°rxn = [1Ã—(-393.5) + 2Ã—(-285.8)] - [1Ã—(-74.8) + 2Ã—0]
#         = [-393.5 - 571.6] - [-74.8]
#         = -965.1 + 74.8 = -890.3 kJ
species_ch4 = [
    {'formula':'CH4',  'dHf':-74.8,   'coeff':1, 'role':'reactant'},
    {'formula':'O2',   'dHf': 0.0,    'coeff':2, 'role':'reactant'},
    {'formula':'CO2',  'dHf':-393.5,  'coeff':1, 'role':'product'},
    {'formula':'H2O',  'dHf':-285.8,  'coeff':2, 'role':'product'},
]
dH_rxn_ch4 = standard_enthalpy_rxn(species_ch4)
check("CH4 combustion Î”HÂ°rxn = -890.3 kJ", dH_rxn_ch4, -890.3, tol=0.01)

# Formation of water: H2 + 1/2 O2 â†’ H2O(l)  Î”HÂ°f(H2O) = -285.8 kJ
species_h2o = [
    {'formula':'H2',  'dHf': 0.0,    'coeff':1,   'role':'reactant'},
    {'formula':'O2',  'dHf': 0.0,    'coeff':0.5, 'role':'reactant'},
    {'formula':'H2O', 'dHf':-285.8,  'coeff':1,   'role':'product'},
]
check("H2O formation Î”HÂ°rxn = -285.8 kJ",
      standard_enthalpy_rxn(species_h2o), -285.8, tol=0.01)

# Decomposition (endothermic): 2 H2O â†’ 2 H2 + O2  Î”H = +571.6 kJ
species_decomp = [
    {'formula':'H2O', 'dHf':-285.8, 'coeff':2, 'role':'reactant'},
    {'formula':'H2',  'dHf': 0.0,   'coeff':2, 'role':'product'},
    {'formula':'O2',  'dHf': 0.0,   'coeff':1, 'role':'product'},
]
check("H2O decomposition Î”HÂ°rxn = +571.6 kJ",
      standard_enthalpy_rxn(species_decomp), 571.6, tol=0.01)

# Coefficient scaling: 2 CO + O2 â†’ 2 CO2
# Î”HÂ°rxn = 2Ã—(-393.5) - [2Ã—(-110.5) + 1Ã—0] = -787 - (-221) = -566 kJ
species_co = [
    {'formula':'CO',  'dHf':-110.5, 'coeff':2, 'role':'reactant'},
    {'formula':'O2',  'dHf':  0.0,  'coeff':1, 'role':'reactant'},
    {'formula':'CO2', 'dHf':-393.5, 'coeff':2, 'role':'product'},
]
check("2CO+O2 Î”HÂ°rxn = -566 kJ",
      standard_enthalpy_rxn(species_co), -566.0, tol=0.01)

# Zero case: element reacting with itself (degenerate)
species_zero = [
    {'formula':'N2', 'dHf': 0.0, 'coeff':1, 'role':'reactant'},
    {'formula':'N2', 'dHf': 0.0, 'coeff':1, 'role':'product'},
]
check("Element cycle Î”HÂ°rxn = 0",
      standard_enthalpy_rxn(species_zero), 0.0, tol=1e-9)

# Bad role
check_raises("Bad role raises ValueError",
             lambda: standard_enthalpy_rxn([
                 {'formula':'X', 'dHf':0, 'coeff':1, 'role':'byproduct'}
             ]), ValueError)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. GIBBS FREE ENERGY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("5. GIBBS FREE ENERGY  dG = dH - T*dS")

# Î”G = Î”H - T*Î”S
# Example: Î”H = -100 kJ, T = 300 K, Î”S = -200 J/K
# Î”G = -100 - 300*(-200/1000) = -100 + 60 = -40 kJ
check("Î”G = -100 - 300*(-0.2) = -40 kJ",
      gibbs_dG(-100, 300, -200), -40.0, tol=1e-9)

# Î”G = Î”H - TÎ”S: Î”H=-286, T=298, Î”S=-163.4 J/K
# Î”G = -286 - 298*(-163.4/1000) = -286 + 48.69 = -237.31 kJ  (approx. water formation)
dG_water = gibbs_dG(-285.8, 298, -163.4)
check("H2O formation Î”G â‰ˆ -237.1 kJ", dG_water, -237.1, tol=0.5)

# Solve for Î”H
dH_back = gibbs_dH(-40, 300, -200)
check("dH from dG: Î”H = -100 kJ", dH_back, -100.0, tol=1e-9)

# Solve for Î”S
dS_back = gibbs_dS(-100, -40, 300)
check("dS from dG,dH,T: Î”S = -200 J/K", dS_back, -200.0, tol=1e-9)

# Solve for T (crossover, Î”G = 0)
# At equilibrium: T = Î”H / (Î”S/1000) = -100 / (-200/1000) = 500 K
T_cross = gibbs_T(-100, 0, -200)
check("Crossover T: -100 kJ / (-0.2 kJ/K) = 500 K", T_cross, 500.0, tol=1e-9)

# Celsius conversion
check("25Â°C = 298.15 K", celsius_to_kelvin(25), 298.15, tol=1e-9)

# Spontaneity labels
check("Î”G = -1  â†’ spontaneous",     spontaneity(-1.0),    "Spontaneous (Î”G < 0)")
check("Î”G = +1  â†’ non-spontaneous", spontaneity(+1.0),    "Non-spontaneous (Î”G > 0)")
check("Î”G = 0   â†’ equilibrium",     spontaneity(0.0),     "At equilibrium (Î”G = 0)")
check("Î”G very small neg â†’ equilib", spontaneity(-1e-10),  "At equilibrium (Î”G = 0)")
check("Î”G = -1e-5 â†’ spontaneous",   spontaneity(-1e-5),   "Spontaneous (Î”G < 0)")

# Spontaneity analysis (qualitative)
check("dH<0, dS>0 â†’ always spontaneous",
      spontaneity_analysis(-100, 100),
      "Always spontaneous at all temperatures (Î”H<0, Î”S>0)")
check("dH>0, dS<0 â†’ never spontaneous",
      spontaneity_analysis(100, -100),
      "Never spontaneous at any temperature (Î”H>0, Î”S<0)")
check("dH<0, dS<0 â†’ spontaneous low T",
      spontaneity_analysis(-100, -100),
      "Spontaneous at low T only (Î”H<0, Î”S<0 â€” enthalpy driven)")
check("dH>0, dS>0 â†’ spontaneous high T",
      spontaneity_analysis(100, 100),
      "Spontaneous at high T only (Î”H>0, Î”S>0 â€” entropy driven)")

# Error cases
check_raises("gibbs_T with dS=0 raises ValueError",
             lambda: gibbs_T(-100, 0, 0), ValueError)
check_raises("gibbs_dS with T=0 raises ValueError",
             lambda: gibbs_dS(-100, -40, 0), ValueError)

# Roundtrip: compute Î”G, then recover Î”H, Î”S, T
dH_in, T_in, dS_in = -200.0, 350.0, 50.0
dG_rt = gibbs_dG(dH_in, T_in, dS_in)
check("Roundtrip dH recovery", gibbs_dH(dG_rt, T_in, dS_in),       dH_in, tol=1e-9)
check("Roundtrip dS recovery", gibbs_dS(dH_in, dG_rt, T_in),       dS_in, tol=1e-9)
check("Roundtrip T  recovery", gibbs_T(dH_in, dG_rt, dS_in),        T_in,                 tol=1e-6)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SUMMARY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print(f"\n{'='*62}")
print(f"  THERMODYNAMICS DIAGNOSTIC COMPLETE")
print(f"{'='*62}")
print(f"  Total : {PASS+FAIL}")
print(f"  Passed: {PASS}")
print(f"  Failed: {FAIL}")
if ERRORS:
    print("\nFailed tests:")
    for e in ERRORS:
        print(e)
else:
    print("\n  All tests passed!")

