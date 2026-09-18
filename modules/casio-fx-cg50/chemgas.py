# chemgas.py - gas laws and equilibrium (IB S1.5, R2.3)

import math
from chemcore import fmt, show, line, ask_float, ask_int, ask_text, ask_choice

R = 8.31          # J/(mol K) - IB data booklet
P_UNITS = {"1": ("kPa", 1000.0), "2": ("Pa", 1.0), "3": ("atm", 101325.0), "4": ("bar", 1e5)}
V_UNITS = {"1": ("cm3", 1e-6), "2": ("dm3", 1e-3), "3": ("m3", 1.0)}


def ask_units():
    print("Pressure unit:")
    pk = ask_choice(" p? ", [(k, P_UNITS[k][0]) for k in sorted(P_UNITS)])
    print("Volume unit:")
    vk = ask_choice(" V? ", [(k, V_UNITS[k][0]) for k in sorted(V_UNITS)])
    tk = ask_choice("T in K or C? ", [("k", "K"), ("c", "degrees C")])
    return P_UNITS[pk], V_UNITS[vk], tk


def to_kelvin(value, tk):
    T = value + 273.15 if tk == "c" else value
    if T <= 0:
        raise ValueError("T must be above 0 K")
    return T


def menu_ideal():
    print("PV = nRT")
    (pname, pfac), (vname, vfac), tk = ask_units()
    tname = "C" if tk == "c" else "K"
    solve = ask_choice("Find: ", [("p", "P"), ("v", "V"), ("n", "n"), ("t", "T")])
    P = V = n = T = None
    if solve != "p":
        P = ask_float("P (" + pname + "): ", True) * pfac
    if solve != "v":
        V = ask_float("V (" + vname + "): ", True) * vfac
    if solve != "n":
        n = ask_float("n (mol): ", True)
    if solve != "t":
        T = to_kelvin(ask_float("T (" + tname + "): "), tk)
    line()
    if solve == "p":
        show("P", n * R * T / V / pfac, pname)
    elif solve == "v":
        show("V", n * R * T / P / vfac, vname)
    elif solve == "n":
        show("n", P * V / (R * T), "mol")
    else:
        T = P * V / (n * R)
        show("T", T - 273.15 if tk == "c" else T, tname)


def menu_combined():
    print("P1V1/T1 = P2V2/T2")
    (pname, pfac), (vname, vfac), tk = ask_units()
    tname = "C" if tk == "c" else "K"
    solve = ask_choice("Find: ", [("p", "P2"), ("v", "V2"), ("t", "T2")])
    P1 = ask_float("P1 (" + pname + "): ", True) * pfac
    V1 = ask_float("V1 (" + vname + "): ", True) * vfac
    T1 = to_kelvin(ask_float("T1 (" + tname + "): "), tk)
    k = P1 * V1 / T1
    if solve == "p":
        V2 = ask_float("V2 (" + vname + "): ", True) * vfac
        T2 = to_kelvin(ask_float("T2 (" + tname + "): "), tk)
        show("P2", k * T2 / V2 / pfac, pname)
    elif solve == "v":
        P2 = ask_float("P2 (" + pname + "): ", True) * pfac
        T2 = to_kelvin(ask_float("T2 (" + tname + "): "), tk)
        show("V2", k * T2 / P2 / vfac, vname)
    else:
        P2 = ask_float("P2 (" + pname + "): ", True) * pfac
        V2 = ask_float("V2 (" + vname + "): ", True) * vfac
        T2 = P2 * V2 / k
        show("T2", T2 - 273.15 if tk == "c" else T2, tname)


def menu_graham():
    print("GRAHAM: r1/r2 = sqrt(M2/M1)")
    M1 = ask_float("M1 (g/mol): ", True)
    M2 = ask_float("M2 (g/mol): ", True)
    ratio = math.sqrt(M2 / M1)
    show("rate1/rate2", ratio)
    print("Gas 1 is " + ("faster" if ratio > 1 else "slower"))


def menu_dalton():
    print("DALTON: P total = sum of parts")
    count = ask_int("How many gases? ", 1, 8)
    total = 0.0
    parts = []
    for i in range(count):
        p = ask_float("  P" + str(i + 1) + ": ", True)
        parts.append(p)
        total += p
    show("P total", total)
    for i, p in enumerate(parts):
        print("  x" + str(i + 1) + " = " + fmt(p / total, 4))


# ---- equilibrium -----------------------------------------------------------

def reaction_quotient(r_coeffs, r_conc, p_coeffs, p_conc):
    num = 1.0
    for c, x in zip(p_coeffs, p_conc):
        num *= x ** c
    den = 1.0
    for c, x in zip(r_coeffs, r_conc):
        den *= x ** c
    if den == 0:
        return None          # infinite: a reactant is used up
    return num / den


def solve_ice(r_coeffs, r_init, p_coeffs, p_init, Kc):
    """Bisection on x: Q(x) rises from 0 to infinity, so the root is bracketed."""
    def Q(x):
        rc = []
        for c, r0 in zip(r_coeffs, r_init):
            v = r0 - c * x
            rc.append(v if v > 0 else 0.0)
        pc = []
        for c, p0 in zip(p_coeffs, p_init):
            v = p0 + c * x
            pc.append(v if v > 0 else 0.0)
        return reaction_quotient(r_coeffs, rc, p_coeffs, pc)

    x_max = min([r0 / c for c, r0 in zip(r_coeffs, r_init)])
    x_min = max([-p0 / c for c, p0 in zip(p_coeffs, p_init)])
    q0 = Q(0)
    if q0 is not None and abs(q0 - Kc) < 1e-12:
        return 0.0
    if q0 is None or q0 > Kc:
        if x_min >= 0:
            raise ValueError("Needs some product to shift back")
        lo, hi = x_min, 0.0
    else:
        if x_max <= 0:
            raise ValueError("Needs some reactant to react")
        lo, hi = 0.0, x_max
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if mid == lo or mid == hi:
            break
        q = Q(mid)
        if q is None or q > Kc:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def menu_ice():
    print("ICE TABLE")
    rcount = ask_int("How many reactants? ", 1, 4)
    r_names, r_coeffs, r_init = [], [], []
    for i in range(rcount):
        r_names.append(ask_text("  reactant " + str(i + 1) + ": "))
        r_coeffs.append(ask_float("   coefficient: ", True))
        r_init.append(ask_float("   start (mol/dm3): "))
    pcount = ask_int("How many products? ", 1, 4)
    p_names, p_coeffs, p_init = [], [], []
    for i in range(pcount):
        p_names.append(ask_text("  product " + str(i + 1) + ": "))
        p_coeffs.append(ask_float("   coefficient: ", True))
        p_init.append(ask_float("   start (mol/dm3): "))
    Kc = ask_float("Kc: ", True)
    x = solve_ice(r_coeffs, r_init, p_coeffs, p_init, Kc)
    line()
    show("x", x)
    for name, c, start in zip(r_names, r_coeffs, r_init):
        print("  [" + name + "] = " + fmt(start - c * x, 4))
    for name, c, start in zip(p_names, p_coeffs, p_init):
        print("  [" + name + "] = " + fmt(start + c * x, 4))
    smallest = min([v for v in r_init if v > 0] or [0])
    if smallest:
        pct = abs(x) / smallest * 100
        print("x is " + fmt(pct, 3) + "% of the smallest")


def menu_q_vs_k():
    print("Q vs K")
    rcount = ask_int("How many reactants? ", 1, 4)
    r_coeffs, r_conc = [], []
    for i in range(rcount):
        r_coeffs.append(ask_float("  coefficient " + str(i + 1) + ": ", True))
        r_conc.append(ask_float("   [conc]: "))
    pcount = ask_int("How many products? ", 1, 4)
    p_coeffs, p_conc = [], []
    for i in range(pcount):
        p_coeffs.append(ask_float("  coefficient " + str(i + 1) + ": ", True))
        p_conc.append(ask_float("   [conc]: "))
    Kc = ask_float("Kc: ", True)
    Q = reaction_quotient(r_coeffs, r_conc, p_coeffs, p_conc)
    line()
    if Q is None:
        print("Q is infinite (a reactant is 0)")
        print("Shifts LEFT (reverse)")
        return
    show("Q", Q)
    if abs(Q - Kc) / Kc < 1e-6:
        print("Q = K: at equilibrium")
    elif Q < Kc:
        print("Q < K: shifts RIGHT (forward)")
    else:
        print("Q > K: shifts LEFT (reverse)")


def menu_le_chatelier():
    print("LE CHATELIER")
    key = ask_choice("Change: ", [("1", "concentration"), ("2", "pressure"),
                                  ("3", "temperature"), ("4", "catalyst")])
    if key == "1":
        side = ask_choice("Which: ", [("r", "a reactant"), ("p", "a product")])
        way = ask_choice("Change: ", [("i", "increase"), ("d", "decrease")])
        right = (side == "r" and way == "i") or (side == "p" and way == "d")
        print("Shifts " + ("RIGHT" if right else "LEFT"))
        print("K does not change")
    elif key == "2":
        way = ask_choice("Pressure: ", [("i", "increase"), ("d", "decrease")])
        dn = ask_float("delta n (gas prod - react): ")
        if dn == 0:
            print("No shift (equal moles of gas)")
        else:
            to_fewer = (way == "i")
            right = (dn < 0) if to_fewer else (dn > 0)
            print("Shifts " + ("RIGHT" if right else "LEFT"))
        print("K does not change")
    elif key == "3":
        way = ask_choice("Temperature: ", [("i", "increase"), ("d", "decrease")])
        kind = ask_choice("Forward is: ", [("x", "exothermic"), ("n", "endothermic")])
        right = (kind == "n" and way == "i") or (kind == "x" and way == "d")
        print("Shifts " + ("RIGHT" if right else "LEFT"))
        print("K " + ("increases" if right else "decreases"))
    else:
        print("No shift, K unchanged.")
        print("Equilibrium is reached faster.")


def menu_kc_kp():
    print("Kp = Kc(RT)^dn   R=0.0821")
    way = ask_choice("Find: ", [("p", "Kp from Kc"), ("c", "Kc from Kp")])
    K = ask_float("known K: ", True)
    T = ask_float("T (K): ", True)
    dn = ask_float("delta n (gas): ")
    factor = (0.0821 * T) ** dn
    if way == "p":
        show("Kp", K * factor, "atm")
    else:
        show("Kc", K / factor, "mol/dm3")


MENU = [
    ("1", "Ideal gas PV=nRT", menu_ideal),
    ("2", "Combined gas law", menu_combined),
    ("3", "Graham effusion", menu_graham),
    ("4", "Dalton partial P", menu_dalton),
    ("5", "ICE table", menu_ice),
    ("6", "Q vs K", menu_q_vs_k),
    ("7", "Le Chatelier", menu_le_chatelier),
    ("8", "Kc <-> Kp", menu_kc_kp),
]
