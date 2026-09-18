# chemener.py - energetics, electrochemistry and kinetics (IB R1, R2.2, R3.2)

import math
from chemcore import fmt, show, line, ask_float, ask_int, ask_text, ask_choice

R = 8.31
F = 96500

BONDS = {
    "C-H": 414, "C-C": 346, "C=C": 614, "C#C": 839, "C-O": 358, "C=O": 804,
    "C-N": 305, "C=N": 615, "C#N": 890, "C-Cl": 324, "C-Br": 285, "C-F": 492,
    "H-H": 436, "O-H": 463, "N-H": 391, "S-H": 364, "H-F": 567, "H-Cl": 431,
    "H-Br": 366, "H-I": 298, "O=O": 498, "O-O": 144, "N-N": 158, "N=N": 470,
    "N#N": 945, "F-F": 159, "Cl-Cl": 242, "Br-Br": 193, "I-I": 151, "S-S": 266,
}

HALF_CELLS = [
    ("F2/F-", 2.87), ("MnO4-/Mn2+", 1.51), ("Cl2/Cl-", 1.36), ("Cr2O72-/Cr3+", 1.33),
    ("Br2/Br-", 1.07), ("Ag+/Ag", 0.80), ("Fe3+/Fe2+", 0.77), ("I2/I-", 0.54),
    ("Cu2+/Cu", 0.34), ("H+/H2", 0.00), ("Pb2+/Pb", -0.13), ("Sn2+/Sn", -0.14),
    ("Ni2+/Ni", -0.26), ("Fe2+/Fe", -0.44), ("Zn2+/Zn", -0.76), ("Al3+/Al", -1.66),
    ("Mg2+/Mg", -2.37), ("Na+/Na", -2.71), ("Ca2+/Ca", -2.87), ("K+/K", -2.92),
    ("Li+/Li", -3.04),
]


def menu_calorimetry():
    print("q = m c dT")
    solve = ask_choice("Find: ", [("q", "q"), ("m", "m"), ("c", "c"), ("t", "dT")])
    if solve != "q":
        q = ask_float("q (J): ")
    if solve != "m":
        m = ask_float("m (g): ", True)
    if solve != "c":
        c = ask_float("c (J/g/K) [water 4.18]: ", True)
    if solve != "t":
        dT = ask_float("dT (K): ")
    line()
    if solve == "q":
        show("q", m * c * dT, "J")
        show("q", m * c * dT / 1000.0, "kJ")
    elif solve == "m":
        show("m", q / (c * dT), "g")
    elif solve == "c":
        show("c", q / (m * dT), "J/g/K")
    else:
        show("dT", q / (m * c), "K")


def menu_hess():
    print("HESS: sum of (dH x multiplier)")
    count = ask_int("How many steps? ", 1, 6)
    total = 0.0
    for i in range(count):
        dH = ask_float("  dH" + str(i + 1) + " (kJ): ")
        mult = ask_float("   multiplier: ")
        total += dH * mult
    show("dH rxn", total, "kJ/mol")


def bond_energy(name):
    """'c-h', 'H-C' and 'C-H' all find the same bond. None if not in the table."""
    text = name.strip().replace(" ", "")
    for sep in ("#", "=", "-"):
        if sep in text:
            left, right = text.split(sep, 1)
            left = left.capitalize()
            right = right.capitalize()
            for key in (left + sep + right, right + sep + left):
                if key in BONDS:
                    return BONDS[key]
            return None
    return BONDS.get(text.capitalize())


def menu_bonds():
    print("dH = broken - formed")
    print("Blank name ends the list.")
    totals = []
    for label in ("BROKEN", "FORMED"):
        print(label + ":")
        total = 0.0
        while True:
            name = ask_text("  bond (e.g. C-H): ")
            if name == "":
                break
            value = bond_energy(name)
            if value is None:
                value = ask_float("   not in table, kJ/mol: ", True)
            count = ask_float("   how many: ", True)
            total += value * count
        totals.append(total)
    show("broken", totals[0], "kJ")
    show("formed", totals[1], "kJ")
    show("dH", totals[0] - totals[1], "kJ/mol")


def menu_formation():
    print("dH = sum products - sum reactants")
    total = 0.0
    for role, sign in (("REACTANTS", -1), ("PRODUCTS", 1)):
        print(role + " (blank name ends):")
        while True:
            name = ask_text("  species: ")
            if name == "":
                break
            coeff = ask_float("   coefficient: ", True)
            value = ask_float("   dHf (kJ/mol): ")
            total += sign * coeff * value
    show("dH rxn", total, "kJ/mol")


def menu_entropy():
    print("dS = sum products - sum reactants")
    total = 0.0
    for role, sign in (("REACTANTS", -1), ("PRODUCTS", 1)):
        print(role + " (blank name ends):")
        while True:
            name = ask_text("  species: ")
            if name == "":
                break
            coeff = ask_float("   coefficient: ", True)
            value = ask_float("   S (J/mol/K): ", True)
            total += sign * coeff * value
    show("dS rxn", total, "J/mol/K")
    print("Entropy " + ("increases" if total > 0 else "decreases" if total < 0 else "unchanged"))


def menu_gibbs():
    print("dG = dH - T dS")
    solve = ask_choice("Find: ", [("g", "dG"), ("t", "T when dG=0"), ("k", "dG from K"), ("q", "K from dG")])
    if solve == "g":
        dH = ask_float("dH (kJ/mol): ")
        dS = ask_float("dS (J/mol/K): ")
        T = ask_float("T (K) [298]: ", True, blank=298.0)
        dG = dH - T * dS / 1000.0
        show("dG", dG, "kJ/mol")
        print("Spontaneous" if dG < 0 else "Not spontaneous" if dG > 0 else "At equilibrium")
    elif solve == "t":
        dH = ask_float("dH (kJ/mol): ")
        dS = ask_float("dS (J/mol/K): ")
        if dS == 0:
            print("dS = 0: no crossover")
            return
        T = dH * 1000.0 / dS
        show("T", T, "K")
        print("Spontaneous " + ("below" if dH < 0 else "above") + " this T")
    elif solve == "k":
        K = ask_float("K: ", True)
        T = ask_float("T (K) [298]: ", True, blank=298.0)
        show("dG", -R * T * math.log(K) / 1000.0, "kJ/mol")
    else:
        dG = ask_float("dG (kJ/mol): ")
        T = ask_float("T (K) [298]: ", True, blank=298.0)
        power = -dG * 1000.0 / (R * T)
        if power > 300:
            print("K is too large to show")
            return
        show("K", math.exp(power))


def menu_cell():
    print("E cell = E cat - E an")
    print("Table (EXE to skip):")
    for i, (name, value) in enumerate(HALF_CELLS):
        print(" " + str(i + 1) + " " + name + " " + fmt(value, 3))
    a = ask_float("half-cell 1 number (or E): ")
    b = ask_float("half-cell 2 number (or E): ")

    def value_of(x):
        if abs(x - round(x)) < 1e-9 and 1 <= x <= len(HALF_CELLS):
            return HALF_CELLS[int(round(x)) - 1][1], HALF_CELLS[int(round(x)) - 1][0]
        return x, "E = " + fmt(x, 3)

    Ea, na = value_of(a)
    Eb, nb = value_of(b)
    cat, an = (Ea, Eb) if Ea >= Eb else (Eb, Ea)
    cat_name, an_name = (na, nb) if Ea >= Eb else (nb, na)
    E = cat - an
    line()
    print("Cathode: " + cat_name)
    print("Anode:   " + an_name)
    show("E cell", E, "V")
    n = ask_float("electrons n: ", True)
    show("dG", -n * F * E / 1000.0, "kJ/mol")
    print("Spontaneous" if E > 0 else "Not spontaneous" if E < 0 else "At equilibrium")
    print(("Galvanic" if E > 0 else "Electrolytic") + " cell")


def menu_faraday():
    print("m = I t M / (n F)")
    solve = ask_choice("Find: ", [("m", "mass"), ("i", "current"), ("t", "time"), ("n", "molar mass")])
    if solve != "m":
        mass = ask_float("mass (g): ", True)
    if solve != "i":
        I = ask_float("current (A): ", True)
    if solve != "t":
        t = ask_float("time (s): ", True)
    if solve != "n":
        M = ask_float("molar mass (g/mol): ", True)
    n = ask_float("electrons n: ", True)
    line()
    if solve == "m":
        show("mass", I * t * M / (n * F), "g")
    elif solve == "i":
        show("current", mass * n * F / (t * M), "A")
    elif solve == "t":
        show("time", mass * n * F / (I * M), "s")
    else:
        show("M", mass * n * F / (I * t), "g/mol")


def menu_order():
    print("ORDER FROM 2 EXPERIMENTS")
    c1 = ask_float("[A]1: ", True)
    r1 = ask_float("rate1: ", True)
    c2 = ask_float("[A]2: ", True)
    r2 = ask_float("rate2: ", True)
    if c1 == c2:
        print("Concentrations must differ")
        return
    order = math.log(r2 / r1) / math.log(c2 / c1)
    show("order", order)
    print("  nearest whole number: " + str(int(round(order))))
    show("k", r1 / (c1 ** order))


def menu_arrhenius():
    print("ARRHENIUS")
    key = ask_choice("Find: ", [("e", "Ea from 2 points"), ("k", "k2 from Ea"),
                                ("g", "Ea and A from a graph")])
    if key == "e":
        k1 = ask_float("k1: ", True)
        T1 = ask_float("T1 (K): ", True)
        k2 = ask_float("k2: ", True)
        T2 = ask_float("T2 (K): ", True)
        if T1 == T2:
            print("Temperatures must differ")
            return
        Ea = -R * math.log(k2 / k1) / (1.0 / T2 - 1.0 / T1)
        show("Ea", Ea, "J/mol")
        show("Ea", Ea / 1000.0, "kJ/mol")
    elif key == "k":
        k1 = ask_float("k1: ", True)
        T1 = ask_float("T1 (K): ", True)
        T2 = ask_float("T2 (K): ", True)
        Ea = ask_float("Ea (J/mol): ", True)
        show("k2", k1 * math.exp(-Ea / R * (1.0 / T2 - 1.0 / T1)))
    else:
        print("Enter points, blank T ends")
        xs, ys = [], []
        while True:
            T = ask_float("  T (K): ", False, blank=0)
            if not T:
                break
            k = ask_float("  k: ", True)
            xs.append(1.0 / T)
            ys.append(math.log(k))
        if len(xs) < 2:
            print("Need at least 2 points")
            return
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        sxx = sum([(x - mx) ** 2 for x in xs])
        sxy = sum([(x - mx) * (y - my) for x, y in zip(xs, ys)])
        if sxx == 0:
            print("All temperatures are the same")
            return
        grad = sxy / sxx
        inter = my - grad * mx
        ss_tot = sum([(y - my) ** 2 for y in ys])
        ss_res = sum([(y - (grad * x + inter)) ** 2 for x, y in zip(xs, ys)])
        show("gradient", grad)
        show("Ea", -R * grad / 1000.0, "kJ/mol")
        show("A", math.exp(inter))
        if ss_tot > 0:
            show("r2", 1 - ss_res / ss_tot)


def menu_half_life():
    print("FIRST ORDER t1/2 = ln2 / k")
    key = ask_choice("Find: ", [("t", "t1/2 from k"), ("k", "k from t1/2")])
    if key == "t":
        k = ask_float("k (1/s): ", True)
        t = math.log(2) / k
        show("t1/2", t, "s")
        show("t1/2", t / 60.0, "min")
    else:
        t = ask_float("t1/2 (s): ", True)
        show("k", math.log(2) / t, "1/s")


def menu_rate_law():
    print("INTEGRATED RATE LAW")
    order = ask_int("order (0, 1 or 2): ", 0, 2)
    A0 = ask_float("[A]0: ", True)
    k = ask_float("k: ", True)
    key = ask_choice("Find: ", [("a", "[A] after t"), ("t", "time to reach [A]")])
    if key == "a":
        t = ask_float("t (s): ", True)
        if order == 0:
            A = A0 - k * t
            if A < 0:
                print("All used up before t")
                return
        elif order == 1:
            A = A0 * math.exp(-k * t)
        else:
            A = 1.0 / (1.0 / A0 + k * t)
        show("[A]", A, "mol/dm3")
    else:
        A = ask_float("[A] wanted: ", True)
        if A > A0:
            print("[A] cannot be above [A]0")
            return
        if order == 0:
            t = (A0 - A) / k
        elif order == 1:
            t = math.log(A0 / A) / k
        else:
            t = (1.0 / A - 1.0 / A0) / k
        show("t", t, "s")
    half = A0 / (2 * k) if order == 0 else (math.log(2) / k if order == 1 else 1.0 / (k * A0))
    show("t1/2", half, "s")


MENU = [
    ("1", "Calorimetry q=mcdT", menu_calorimetry),
    ("2", "Hess's law", menu_hess),
    ("3", "Bond enthalpies", menu_bonds),
    ("4", "dH from dHf", menu_formation),
    ("5", "dS from S values", menu_entropy),
    ("6", "Gibbs dG / K", menu_gibbs),
    ("7", "Cell potential", menu_cell),
    ("8", "Faraday", menu_faraday),
    ("9", "Order and k", menu_order),
    ("a", "Arrhenius", menu_arrhenius),
    ("b", "Half-life", menu_half_life),
    ("c", "Integrated rate law", menu_rate_law),
]
