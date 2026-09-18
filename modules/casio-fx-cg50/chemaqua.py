# chemaqua.py - acids, bases, buffers and titration (IB R3.1)

import math
from chemcore import fmt, show, line, ask_float, ask_text, ask_choice

Kw = 1.0e-14      # at 25 C


def all_four(pH=None, pOH=None, H=None, OH=None):
    if pH is None:
        if pOH is not None:
            pH = 14.0 - pOH
        elif H is not None:
            pH = -math.log10(H)
        elif OH is not None:
            pH = 14.0 + math.log10(OH)
        else:
            raise ValueError("Give one value")
    return pH, 14.0 - pH, 10 ** (-pH), 10 ** (-(14.0 - pH))


def weak_acid_pH(Ka, C):
    """[H+] = sqrt(Ka C); falls back to the quadratic if x > 5% of C."""
    if Ka <= 0 or C <= 0:
        raise ValueError("Ka and C must be > 0")
    x = math.sqrt(Ka * C)
    approx = (x / C <= 0.05)
    if not approx:
        x = (-Ka + math.sqrt(Ka * Ka + 4 * Ka * C)) / 2
    return -math.log10(x), approx, x


def weak_base_pH(Kb, C):
    if Kb <= 0 or C <= 0:
        raise ValueError("Kb and C must be > 0")
    x = math.sqrt(Kb * C)
    approx = (x / C <= 0.05)
    if not approx:
        x = (-Kb + math.sqrt(Kb * Kb + 4 * Kb * C)) / 2
    return 14.0 + math.log10(x), approx, x


def print_all(pH):
    pH, pOH, H, OH = all_four(pH=pH)
    show("pH", pH)
    show("pOH", pOH)
    print("  [H+]  = " + fmt(H, 3) + " mol/dm3")
    print("  [OH-] = " + fmt(OH, 3) + " mol/dm3")


def menu_convert():
    print("pH / pOH / [H+] / [OH-]")
    key = ask_choice("You have: ", [("1", "pH"), ("2", "pOH"), ("3", "[H+]"), ("4", "[OH-]")])
    value = ask_float("value: ", key in ("3", "4"))
    if key == "1":
        pH = value
    elif key == "2":
        pH = 14.0 - value
    elif key == "3":
        pH = -math.log10(value)
    else:
        pH = 14.0 + math.log10(value)
    print_all(pH)


def menu_strong():
    kind = ask_choice("Strong: ", [("a", "acid"), ("b", "base")])
    C = ask_float("concentration (mol/dm3): ", True)
    pH = -math.log10(C) if kind == "a" else 14.0 + math.log10(C)
    print_all(pH)


def menu_weak():
    kind = ask_choice("Weak: ", [("a", "acid (Ka)"), ("b", "base (Kb)")])
    K = ask_float("Ka or Kb: ", True)
    C = ask_float("concentration (mol/dm3): ", True)
    if kind == "a":
        pH, approx, x = weak_acid_pH(K, C)
    else:
        pH, approx, x = weak_base_pH(K, C)
    print("5% rule: " + ("ok" if approx else "used quadratic"))
    print_all(pH)


def menu_buffer():
    print("pH = pKa + log([A-]/[HA])")
    Ka = ask_float("Ka: ", True)
    acid = ask_float("[HA]: ", True)
    base = ask_float("[A-]: ", True)
    pKa = -math.log10(Ka)
    show("pKa", pKa)
    print_all(pKa + math.log10(base / acid))


def menu_titration():
    print("TITRATION")
    key = ask_choice("Find: ", [("c", "concentration"), ("v", "volume of titrant")])
    ra = ask_float("mole ratio analyte: ", True)
    rt = ask_float("mole ratio titrant: ", True)
    Ct = ask_float("titrant c (mol/dm3): ", True)
    Va = ask_float("analyte V (cm3): ", True)
    if key == "c":
        Vt = ask_float("titrant V at end (cm3): ", True)
        n_t = Ct * Vt / 1000.0
        n_a = n_t * ra / rt
        show("n titrant", n_t, "mol")
        show("n analyte", n_a, "mol")
        show("c analyte", n_a / (Va / 1000.0), "mol/dm3")
    else:
        Ca = ask_float("analyte c (mol/dm3): ", True)
        n_a = Ca * Va / 1000.0
        n_t = n_a * rt / ra
        show("n analyte", n_a, "mol")
        show("V titrant", n_t / Ct * 1000.0, "cm3")


def menu_salt():
    print("SALT SOLUTION pH")
    kind = ask_choice("Salt of: ", [("a", "weak acid (give Ka)"), ("b", "weak base (give Kb)")])
    K = ask_float("Ka or Kb of parent: ", True)
    C = ask_float("concentration (mol/dm3): ", True)
    K_ion = Kw / K
    x = math.sqrt(K_ion * C)
    show("K of the ion", K_ion)
    if kind == "a":
        print("  [OH-] = " + fmt(x, 3))
        print_all(14.0 + math.log10(x))
        print("Basic (pH > 7)")
    else:
        print("  [H+] = " + fmt(x, 3))
        print_all(-math.log10(x))
        print("Acidic (pH < 7)")


def menu_half_equivalence():
    print("At half-equivalence pH = pKa")
    pH = ask_float("pH at half-equivalence: ")
    show("pKa", pH)
    show("Ka", 10 ** (-pH))


def menu_ka_kb():
    print("Ka Kb pKa pKb")
    key = ask_choice("Have: ", [("1", "Ka"), ("2", "pKa"), ("3", "Kb"), ("4", "pKb")])
    value = ask_float("value: ", key in ("1", "3"))
    if key == "1":
        Ka = value
    elif key == "2":
        Ka = 10 ** (-value)
    elif key == "3":
        Ka = Kw / value
    else:
        Ka = Kw / (10 ** (-value))
    Kb = Kw / Ka
    show("Ka", Ka)
    show("pKa", -math.log10(Ka))
    show("Kb", Kb)
    show("pKb", -math.log10(Kb))


MENU = [
    ("1", "pH / pOH converter", menu_convert),
    ("2", "Strong acid or base", menu_strong),
    ("3", "Weak acid or base", menu_weak),
    ("4", "Buffer", menu_buffer),
    ("5", "Titration", menu_titration),
    ("6", "Salt solution pH", menu_salt),
    ("7", "pKa from half-eq", menu_half_equivalence),
    ("8", "Ka/Kb/pKa/pKb", menu_ka_kb),
]
