# chemstruct.py - electron configuration, oxidation numbers, ionic formulas
# (IB S1.3, S2.1, R3.2)

from chemcore import (fmt, show, line, ask_float, ask_int, ask_text, ask_choice,
                      parse_formula, masses, gcd)

ORDER = [("1s", 2), ("2s", 2), ("2p", 6), ("3s", 2), ("3p", 6), ("4s", 2), ("3d", 10),
         ("4p", 6), ("5s", 2), ("4d", 10), ("5p", 6), ("6s", 2), ("4f", 14), ("5d", 10),
         ("6p", 6)]
NOBLE = [(2, "He"), (10, "Ne"), (18, "Ar"), (36, "Kr"), (54, "Xe"), (86, "Rn")]
# atomic numbers of the elements in chemcore's table, in order
SYMBOLS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co "
           "Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb "
           "Te I Xe Cs Ba").split()
EXCEPTIONS = {24: ("4s", "3d"), 29: ("4s", "3d"), 42: ("5s", "4d"), 47: ("5s", "4d")}

FIXED = {"F": -1, "Li": 1, "Na": 1, "K": 1, "Rb": 1, "Cs": 1, "Be": 2, "Mg": 2,
         "Ca": 2, "Sr": 2, "Ba": 2, "Al": 3, "Zn": 2, "Cd": 2, "Ag": 1, "H": 1, "O": -2}


def atomic_number(symbol):
    symbol = symbol.strip().capitalize()
    if symbol in SYMBOLS:
        return SYMBOLS.index(symbol) + 1
    raise ValueError("Not in this table: " + symbol)


def fill(electrons):
    out = []
    left = electrons
    for label, cap in ORDER:
        if left <= 0:
            break
        take = cap if cap < left else left
        out.append([label, take])
        left -= take
    if left > 0:
        raise ValueError("Too many electrons")
    return out


def configuration(Z, charge=0):
    electrons = Z - charge
    if electrons < 1:
        raise ValueError("No electrons left")
    config = fill(Z)
    if Z in EXCEPTIONS:
        s_label, d_label = EXCEPTIONS[Z]
        s_part = None
        d_part = None
        for part in config:
            if part[0] == s_label:
                s_part = part
            if part[0] == d_label:
                d_part = part
        if s_part and d_part and s_part[1] > 0:
            s_part[1] -= 1
            d_part[1] += 1
    if charge > 0:
        left = charge
        while left > 0:
            best = None
            for part in config:
                if part[1] <= 0:
                    continue
                level = int(part[0][0])
                kind = "spdf".index(part[0][1])
                key = (level, kind)
                if best is None or key > best[0]:
                    best = (key, part)
            take = best[1][1] if best[1][1] < left else left
            best[1][1] -= take
            left -= take
    elif charge < 0:
        config = fill(electrons)
    config = [p for p in config if p[1] > 0]
    config.sort(key=lambda p: (int(p[0][0]), "spdf".index(p[0][1])))
    return config


def config_text(config):
    return " ".join([p[0] + str(p[1]) for p in config])


def shorthand(config, electrons):
    core_symbol = None
    core_count = 0
    for z, sym in NOBLE:
        if z < electrons:
            core_symbol, core_count = sym, z
    if not core_symbol:
        return config_text(config)
    left = core_count
    rest = []
    for label, count in config:
        if left >= count:
            left -= count
            continue
        rest.append((label, count - left))
        left = 0
    return "[" + core_symbol + "] " + " ".join([l + str(c) for l, c in rest])


def menu_config():
    print("ELECTRON CONFIGURATION")
    raw = ask_text("Element (symbol or Z): ")
    try:
        Z = int(raw)
    except ValueError:
        Z = atomic_number(raw)
    charge = ask_float("charge (0 = atom): ", False, blank=0)
    charge = int(charge)
    config = configuration(Z, charge)
    line()
    print(SYMBOLS[Z - 1] + "  Z = " + str(Z) + "  e = " + str(Z - charge))
    print(config_text(config))
    print(shorthand(config, Z - charge))
    if Z in EXCEPTIONS and charge == 0:
        print("Exception: s electron moves to d")
    if charge > 0:
        print("Highest level empties first (4s before 3d)")


# ---- oxidation numbers -----------------------------------------------------

def oxidation_numbers(formula, charge=0, peroxide=False):
    counts = parse_formula(formula)
    if len(counts) == 1:
        only = list(counts.keys())[0]
        return {only: 0}
    fixed = {}
    for el in FIXED:
        fixed[el] = FIXED[el]
    if peroxide:
        fixed["O"] = -1
    # metal hydride: H is -1 when everything else is a metal with a + state
    if "H" in counts and len(counts) > 1:
        others_positive = True
        for el in counts:
            if el == "H":
                continue
            if el not in fixed or fixed[el] < 0:
                others_positive = False
        if others_positive:
            fixed["H"] = -1
    known = 0
    unknown = []
    for el in counts:
        if el in fixed:
            known += fixed[el] * counts[el]
        else:
            unknown.append(el)
    if len(unknown) == 0:
        return dict([(el, fixed[el]) for el in counts])
    if len(unknown) > 1:
        raise ValueError("Too many unknowns: " + ", ".join(unknown))
    el = unknown[0]
    value = (charge - known) / float(counts[el])
    out = {}
    for item in counts:
        out[item] = fixed[item] if item in fixed else value
    return out


def menu_oxidation():
    print("OXIDATION NUMBERS")
    formula = ask_text("Formula (no charge sign): ")
    charge = int(ask_float("overall charge: ", False, blank=0))
    peroxide = False
    if "O" in formula.upper():
        peroxide = ask_choice("Peroxide? ", [("n", "no"), ("y", "yes")]) == "y"
    result = oxidation_numbers(formula, charge, peroxide)
    line()
    for el in sorted(result):
        value = result[el]
        if abs(value - round(value)) < 1e-9:
            text = str(int(round(value)))
        else:
            text = fmt(value, 4)
        if not text.startswith("-"):
            text = "+" + text
        print("  " + el + ": " + text)


# ---- ionic formulas --------------------------------------------------------

def ionic_formula(cation, cation_charge, anion, anion_charge):
    if cation_charge <= 0 or anion_charge >= 0:
        raise ValueError("Cation must be +, anion must be -")
    g = gcd(cation_charge, abs(anion_charge))
    c_sub = abs(anion_charge) // g
    a_sub = cation_charge // g

    def part(symbol, sub):
        if sub == 1:
            return symbol
        many = sum([1 for ch in symbol if ch.isupper()]) > 1
        digits = any([ch.isdigit() for ch in symbol])
        if many or digits:
            return "(" + symbol + ")" + str(sub)
        return symbol + str(sub)

    return part(cation, c_sub) + part(anion, a_sub)


def menu_ionic():
    print("IONIC FORMULA (criss-cross)")
    cation = ask_text("cation (e.g. Al): ")
    c_charge = int(ask_float("  charge (+): ", True))
    anion = ask_text("anion (e.g. SO4): ")
    a_charge = int(ask_float("  charge (negative): "))
    show_text = ionic_formula(cation, c_charge, anion, a_charge)
    line()
    print("Formula: " + show_text)


MENU = [
    ("1", "Electron configuration", menu_config),
    ("2", "Oxidation numbers", menu_oxidation),
    ("3", "Ionic formula", menu_ionic),
]
