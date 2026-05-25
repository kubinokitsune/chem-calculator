"""
Rigorous diagnostic for ice_solver.py
Tests every solver with known chemistry values.
"""
import sys, os, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ice_solver import (
    reaction_quotient, solve_ice, build_ice_table,
    kc_to_kp, kp_to_kc, R_ATM,
    compare_Q_K,
    le_chatelier_concentration, le_chatelier_pressure,
    le_chatelier_temperature, le_chatelier_catalyst,
)

PASS = 0
FAIL = 0
ERRORS = []

def check(label, got, expected, tol=1e-9):
    global PASS, FAIL
    if isinstance(expected, float):
        ok = abs(got - expected) <= tol
    else:
        ok = (got == expected)
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}\n         got={got!r}  expected={expected!r}"
        ERRORS.append(msg); print(msg)

def check_approx(label, got, expected, tol_pct=0.01):
    """Relative tolerance check (percent)."""
    global PASS, FAIL
    rel = abs(got - expected) / (abs(expected) + 1e-30) * 100
    ok = rel <= tol_pct
    if ok:
        PASS += 1
        print(f"  [PASS] {label}  (rel err={rel:.4f}%)")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}\n         got={got:.8f}  expected={expected:.8f}  rel={rel:.4f}%"
        ERRORS.append(msg); print(msg)

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
        msg = f"  [FAIL] {label}  â€” wrong exc {type(e).__name__}: {e}"
        ERRORS.append(msg); print(msg)

def section(t):
    print(f"\n{'='*64}\n  {t}\n{'='*64}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. REACTION QUOTIENT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("1. REACTION QUOTIENT")

# H2 + I2 <=> 2HI: Q = [HI]^2 / ([H2][I2])
Q = reaction_quotient([1,1],[0.5,0.5],[2],[1.0])
check("H2+I2->2HI: Q = 1.0^2/(0.5*0.5) = 4.0", Q, 4.0)

# N2O4 <=> 2NO2: Q = [NO2]^2/[N2O4]
Q2 = reaction_quotient([1],[1.0],[2],[0.2])
check("N2O4->2NO2: Q = 0.04/1.0 = 0.04", Q2, 0.04)

# All products zero â†’ Q = 0
Q3 = reaction_quotient([1],[0.5],[1],[0.0])
check("Product = 0 -> Q = 0.0", Q3, 0.0)

# Reactant = 0 â†’ Q = 0 (return 0 convention)
Q4 = reaction_quotient([1],[0.0],[1],[0.5])
check("Reactant = 0 -> Q = 0.0", Q4, 0.0)

# Multi-coefficient: 2A <=> B+C, [A]=0.4, [B]=0.1, [C]=0.1
# Q = (0.1*0.1) / 0.4^2 = 0.01/0.16 = 0.0625
Q5 = reaction_quotient([2],[0.4],[1,1],[0.1,0.1])
check("2A<=>B+C: Q = 0.0625", Q5, 0.0625)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. ICE TABLE SOLVER â€” core solve_ice
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("2. ICE TABLE SOLVER (solve_ice)")

# --- Test A: Simple A <=> B, Kc=4, [A]0=1.0
# x/(1-x) = 4  =>  x = 4/5 = 0.8
x_A = solve_ice([1],[1.0],[1],[0.0], Kc=4.0)
check_approx("A<=>B, Kc=4: x=0.8", x_A, 0.8, tol_pct=0.001)
check_approx("A<=>B: [A]_eq = 0.2", 1.0 - x_A, 0.2, tol_pct=0.01)
check_approx("A<=>B: [B]_eq = 0.8", x_A, 0.8, tol_pct=0.001)
# Verify Q = Kc
Q_A = reaction_quotient([1],[1.0-x_A],[1],[x_A])
check_approx("A<=>B verify Q=Kc=4", Q_A, 4.0, tol_pct=0.001)

# --- Test B: N2O4 <=> 2NO2, Kc=0.0059, [N2O4]0=1.0
# 4x^2/(1-x) = 0.0059
# 4x^2 + 0.0059x - 0.0059 = 0
# x = (-0.0059 + sqrt(0.0059^2 + 4*4*0.0059)) / 8 â‰ˆ 0.03767
disc = 0.0059**2 + 4*4*0.0059
x_expected_B = (-0.0059 + math.sqrt(disc)) / 8
x_B = solve_ice([1],[1.0],[2],[0.0], Kc=0.0059)
check_approx("N2O4 decomp: x â‰ˆ 0.03767", x_B, x_expected_B, tol_pct=0.01)
Q_B = reaction_quotient([1],[1.0-x_B],[2],[2*x_B])
check_approx("N2O4 verify Q=Kc=0.0059", Q_B, 0.0059, tol_pct=0.1)

# --- Test C: H2 + I2 <=> 2HI, Kc=55.64, [H2]=[I2]=0.5
# Kc = (2x)^2 / ((0.5-x)^2)  =>  sqrt(Kc) = 2x/(0.5-x)
# x = 0.5*sqrt(Kc) / (2 + sqrt(Kc))
sqrtK = math.sqrt(55.64)
x_expected_C = 0.5 * sqrtK / (2 + sqrtK)
x_C = solve_ice([1,1],[0.5,0.5],[2],[0.0], Kc=55.64)
check_approx("H2+I2->2HI: x correct", x_C, x_expected_C, tol_pct=0.001)
r_eq_C = [0.5 - x_C, 0.5 - x_C]
p_eq_C = [2*x_C]
Q_C = reaction_quotient([1,1], r_eq_C, [2], p_eq_C)
check_approx("H2+I2 verify Q=55.64", Q_C, 55.64, tol_pct=0.01)

# --- Test D: Already at equilibrium
# A <=> B, Kc=4.0, [A]=0.2, [B]=0.8 (Q=4=Kc)
x_D = solve_ice([1],[0.2],[1],[0.8], Kc=4.0)
check_approx("Already at eq: x â‰ˆ 0", x_D, 0.0, tol_pct=0.001)

# --- Test E: Reverse shift Q > Kc
# A <=> B, Kc=1.0, [A]=0.1, [B]=0.9 â†’ Q=9 > 1
# Reverse: products decrease by x, reactants increase by x
# Eq: (0.9+x)/(0.1-x)... wait, sign convention:
# In solve_ice, x < 0 means reverse. So r_initial=[A]=0.1, p_initial=[B]=0.9
# At eq: [A] = 0.1 - 1*x, [B] = 0.9 + 1*x, with x negative
# Kc=1: (0.9+x)/(0.1-x) = 1 => 0.9+x = 0.1-x => 2x=-0.8 => x=-0.4
# [A]_eq = 0.5, [B]_eq = 0.5
x_E = solve_ice([1],[0.1],[1],[0.9], Kc=1.0)
check_approx("Reverse shift: x = -0.4", x_E, -0.4, tol_pct=0.001)
check_approx("Reverse [A]_eq = 0.5", 0.1 - x_E, 0.5, tol_pct=0.01)
check_approx("Reverse [B]_eq = 0.5", 0.9 + x_E, 0.5, tol_pct=0.01)
Q_E = reaction_quotient([1],[0.1-x_E],[1],[0.9+x_E])
check_approx("Reverse verify Q=1.0", Q_E, 1.0, tol_pct=0.01)

# --- Test F: Very small Kc (5% approx should be valid)
# A <=> B, Kc=1e-4, [A]=1.0
# x/(1-x) â‰ˆ x â‰ˆ 1e-4  (approx valid: x/[A]=0.01%)
x_F = solve_ice([1],[1.0],[1],[0.0], Kc=1e-4)
check_approx("Small Kc=1e-4: x â‰ˆ 9.999e-5", x_F, 1e-4/(1+1e-4), tol_pct=0.01)
r_table = build_ice_table(['A'],  [1], [1.0], ['B'], [1], [0.0], 1e-4)
check("5% rule: approx_pct < 5%", r_table['approx_pct'] < 5.0, True)

# --- Test G: build_ice_table returns correct structure
r_tbl = build_ice_table(['H2','I2'],[1,1],[0.5,0.5],['HI'],[2],[0.0], 55.64)
check_approx("build_ice_table Q_final â‰ˆ 55.64", r_tbl['Q_final'], 55.64, tol_pct=0.01)
check("build_ice_table has x key", 'x' in r_tbl, True)
check("build_ice_table has r_eq", len(r_tbl['r_eq']), 2)
check("build_ice_table has p_eq", len(r_tbl['p_eq']), 1)

# --- Error cases ---
check_raises("Kc < 0 raises ValueError",
             lambda: solve_ice([1],[1.0],[1],[0.0], Kc=-1.0), ValueError)
# When products start at 0 and Kc=0: Q=0=Kc, so x=0 (trivially at equilibrium)
x_zero_kc = solve_ice([1],[0.5],[1],[0.0], Kc=0.0)
check_approx("Kc=0, products=0: already at eq (x=0)", x_zero_kc, 0.0, tol_pct=0.001)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. Kc / Kp CONVERTER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("3. Kc / Kp CONVERTER")

# N2O4(g) <=> 2NO2(g): delta_n = +1, T=298 K
# Kp = Kc * (RT)^1 = Kc * 0.08206 * 298
T = 298.0
dn = 1
Kc_n = 0.0059
RT = R_ATM * T
Kp_expected = Kc_n * RT ** dn
Kp_calc = kc_to_kp(Kc_n, T, dn)
check_approx("N2O4: Kp = Kc*(RT)^1", Kp_calc, Kp_expected, tol_pct=0.001)

# Roundtrip Kc -> Kp -> Kc
Kc_back = kp_to_kc(Kp_calc, T, dn)
check_approx("Kc->Kp->Kc roundtrip", Kc_back, Kc_n, tol_pct=0.001)

# delta_n = 0: Kp = Kc
check_approx("delta_n=0: Kp = Kc", kc_to_kp(5.0, T, 0), 5.0, tol_pct=0.001)

# delta_n = -1: Kp = Kc / RT
Kp_neg = kc_to_kp(1.0, T, -1)
check_approx("delta_n=-1: Kp = Kc/RT", Kp_neg, 1.0 / RT, tol_pct=0.001)

# delta_n = +2
Kp_2 = kc_to_kp(1.0, T, 2)
check_approx("delta_n=+2: Kp = (RT)^2", Kp_2, RT**2, tol_pct=0.001)

# kp_to_kc roundtrip for various delta_n
for dn_test in [-2, -1, 0, 1, 2]:
    Kp_t = kc_to_kp(3.0, T, dn_test)
    Kc_t = kp_to_kc(Kp_t, T, dn_test)
    check_approx(f"Roundtrip delta_n={dn_test:+d}", Kc_t, 3.0, tol_pct=0.001)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. Q vs K COMPARISON
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("4. Q vs K COMPARISON")

# Q < K â†’ forward
direction, msg = compare_Q_K(1.0, 10.0)
check("Q<K -> forward", direction, 'forward')
check("Q<K message has 'RIGHT'", 'RIGHT' in msg.upper(), True)

# Q > K â†’ reverse
direction2, msg2 = compare_Q_K(20.0, 10.0)
check("Q>K -> reverse", direction2, 'reverse')
check("Q>K message has 'LEFT'", 'LEFT' in msg2.upper(), True)

# Q = K â†’ equilibrium
direction3, msg3 = compare_Q_K(10.0, 10.0)
check("Q=K -> equilibrium", direction3, 'equilibrium')
check("Q=K message has 'equilibrium'", 'equilibrium' in msg3.lower(), True)

# Very close to K within tolerance
direction4, _ = compare_Q_K(10.0 + 1e-9, 10.0)
check("Qâ‰ˆK within tol -> equilibrium", direction4, 'equilibrium')

# Q = 0 (reactants only)
direction5, _ = compare_Q_K(0.0, 5.0)
check("Q=0 -> forward", direction5, 'forward')


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. LE CHATELIER PREDICTOR
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("5. LE CHATELIER PREDICTOR")

# --- Concentration ---
d, e = le_chatelier_concentration('reactant', 'increase')
check("conc: +reactant -> right", d, 'right')
check("conc: +reactant explanation mentions Q", 'Q' in e or 'shift' in e.lower(), True)

d, e = le_chatelier_concentration('reactant', 'decrease')
check("conc: -reactant -> left", d, 'left')

d, e = le_chatelier_concentration('product', 'increase')
check("conc: +product -> left", d, 'left')

d, e = le_chatelier_concentration('product', 'decrease')
check("conc: -product -> right", d, 'right')

# Invalid input raises
check_raises("conc bad role raises",
             lambda: le_chatelier_concentration('solvent', 'increase'), ValueError)
check_raises("conc bad change raises",
             lambda: le_chatelier_concentration('reactant', 'add'), ValueError)

# --- Pressure ---
d, e = le_chatelier_pressure('increase', 1)
check("pressure: increase, dn=+1 -> left", d, 'left')

d, e = le_chatelier_pressure('increase', -1)
check("pressure: increase, dn=-1 -> right", d, 'right')

d, e = le_chatelier_pressure('decrease', 1)
check("pressure: decrease, dn=+1 -> right", d, 'right')

d, e = le_chatelier_pressure('decrease', -1)
check("pressure: decrease, dn=-1 -> left", d, 'left')

d, e = le_chatelier_pressure('increase', 0)
check("pressure: dn=0 -> none", d, 'none')

d, e = le_chatelier_pressure('decrease', 0)
check("pressure: decrease, dn=0 -> none", d, 'none')

# Invalid pressure change raises
check_raises("pressure bad change raises",
             lambda: le_chatelier_pressure('neutral', 1), ValueError)

# --- Temperature ---
d, e, k = le_chatelier_temperature('increase', 'exothermic')
check("temp: increase exothermic -> left",     d, 'left')
check("temp: increase exothermic K decreases", k, 'decreases')

d, e, k = le_chatelier_temperature('decrease', 'exothermic')
check("temp: decrease exothermic -> right",    d, 'right')
check("temp: decrease exothermic K increases", k, 'increases')

d, e, k = le_chatelier_temperature('increase', 'endothermic')
check("temp: increase endothermic -> right",   d, 'right')
check("temp: increase endothermic K increases",k, 'increases')

d, e, k = le_chatelier_temperature('decrease', 'endothermic')
check("temp: decrease endothermic -> left",    d, 'left')
check("temp: decrease endothermic K decreases",k, 'decreases')

# Invalid raises
check_raises("temp bad rxn_type raises",
             lambda: le_chatelier_temperature('increase', 'neutral'), ValueError)

# --- Catalyst ---
d, e = le_chatelier_catalyst()
check("catalyst -> none (no shift)", d, 'none')
check("catalyst explanation mentions equilibrium", 'equilibrium' in e.lower(), True)
check("catalyst explanation mentions K unchanged", 'K' in e, True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 6. CROSS-CHECKS & EDGE CASES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
section("6. CROSS-CHECKS & EDGE CASES")

# ICE: 2A <=> B, Kc=0.25, [A]=2.0, [B]=0
# Kc = x / (2-2x)^2 = 0.25
# Let y = 2x (moles shifted from A): Kc = y/2 / (2-y)^2
# 0.25*(2-y)^2 = y/2  ... simpler: let [B]=x, [A]=2-2x
# 0.25 = x / (2-2x)^2 = x / 4(1-x)^2
# x = 1 - (1-x) â†’ 0.25 * 4 * (1-x)^2 = x â†’ (1-x)^2 = x â†’ 1 - 2x + x^2 = x
# x^2 - 3x + 1 = 0 â†’ x = (3 - sqrt(5)) / 2 â‰ˆ 0.3820
x_expected_2A = (3 - math.sqrt(5)) / 2
x_2A = solve_ice([2],[2.0],[1],[0.0], Kc=0.25)
check_approx("2A<=>B: x(ice var) gives [B]_eq", 0.0 + 1*x_2A, x_expected_2A, tol_pct=0.01)
Q_2A = reaction_quotient([2],[2.0 - 2*x_2A],[1],[x_2A])
check_approx("2A<=>B verify Q=0.25", Q_2A, 0.25, tol_pct=0.01)

# ICE: large Kc (essentially complete reaction)
# A <=> B, Kc=1e6, [A]=1.0 â†’ x â‰ˆ 1 - 1e-6
x_large = solve_ice([1],[1.0],[1],[0.0], Kc=1e6)
check_approx("Large Kc=1e6: x â‰ˆ 0.999999", x_large, 1e6/(1+1e6), tol_pct=0.001)

# ICE: Kp->Kc->ICE chain
# N2O4 <=> 2NO2, given Kp=0.144 atm at T=298K
# Kc = Kp / (RT)^1 = 0.144 / (0.08206*298) = 0.144 / 24.45 â‰ˆ 0.005889
Kc_from_Kp = kp_to_kc(0.144, 298.0, 1)
check_approx("Kp->Kc: 0.144 at 298K -> ~0.00589", Kc_from_Kp, 0.00589, tol_pct=1.0)
x_chain = solve_ice([1],[1.0],[2],[0.0], Kc_from_Kp)
Q_chain = reaction_quotient([1],[1.0-x_chain],[2],[2*x_chain])
check_approx("Chain Kp->Kc->ICE: Q â‰ˆ Kc", Q_chain, Kc_from_Kp, tol_pct=0.1)

# Q=K consistency between compare_Q_K and reaction_quotient
Q_direct = reaction_quotient([1],[0.2],[1],[0.8])  # = 4.0
dir_check, _ = compare_Q_K(Q_direct, 4.0)
check("Q=K check consistent with reaction_quotient", dir_check, 'equilibrium')

# Le Chatelier + pressure + chemistry sense
# 2SO2 + O2 <=> 2SO3: dn = 2 - 3 = -1 (more moles reactant side)
# Increase pressure -> fewer moles -> RIGHT (forward) âœ“
d_so3, _ = le_chatelier_pressure('increase', -1)
check("2SO2+O2<=>2SO3: increase P -> right", d_so3, 'right')

# Haber process N2 + 3H2 <=> 2NH3: dn = 2 - 4 = -2
# Decrease pressure -> more moles -> reactant side -> LEFT
d_haber, _ = le_chatelier_pressure('decrease', -2)
check("Haber: decrease P -> left", d_haber, 'left')

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SUMMARY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print(f"\n{'='*64}")
print(f"  ICE SOLVER DIAGNOSTIC COMPLETE")
print(f"{'='*64}")
print(f"  Total : {PASS+FAIL}")
print(f"  Passed: {PASS}")
print(f"  Failed: {FAIL}")
if ERRORS:
    print("\nFailed tests:")
    for e in ERRORS:
        print(e)
else:
    print("\n  All tests passed!")

