# chemtools.py - isotopes, uncertainties and IHD (IB S1.2, S3.2, Tools)

import math
from chemcore import (fmt, show, line, ask_float, ask_int, ask_text, ask_choice,
                      parse_formula)


# ---- isotopes --------------------------------------------------------------

def relative_atomic_mass(pairs):
    """pairs: list of (mass, abundance). Abundances may be % or peak heights."""
    if len(pairs) < 2:
        raise ValueError("Need at least 2 isotopes")
    total = 0.0
    weighted = 0.0
    for mass, abundance in pairs:
        if mass <= 0:
            raise ValueError("Mass must be > 0")
        if abundance < 0:
            raise ValueError("Abundance cannot be negative")
        total += abundance
        weighted += mass * abundance
    if total <= 0:
        raise ValueError("Abundances cannot all be 0")
    return weighted / total


def abundance_from_Ar(Ar, m1, m2):
    if m1 == m2:
        raise ValueError("Masses must differ")
    low, high = (m1, m2) if m1 < m2 else (m2, m1)
    if Ar < low or Ar > high:
        raise ValueError("Ar must lie between the masses")
    x = 100.0 * (Ar - m2) / (m1 - m2)
    return x, 100.0 - x


def menu_isotopes():
    print("ISOTOPES")
    key = ask_choice("Find: ", [("1", "Ar from abundances"), ("2", "abundances from Ar")])
    if key == "1":
        count = ask_int("How many isotopes? ", 2, 6)
        pairs = []
        for i in range(count):
            mass = ask_float("  mass " + str(i + 1) + ": ", True)
            ab = ask_float("  abundance " + str(i + 1) + ": ", True)
            pairs.append((mass, ab))
        total = sum([a for _, a in pairs])
        show("Ar", relative_atomic_mass(pairs))
        for mass, ab in pairs:
            print("  " + fmt(mass, 5) + ": " + fmt(ab / total * 100, 4) + " %")
    else:
        Ar = ask_float("Ar: ", True)
        m1 = ask_float("mass 1: ", True)
        m2 = ask_float("mass 2: ", True)
        p1, p2 = abundance_from_Ar(Ar, m1, m2)
        print("  " + fmt(m1, 5) + ": " + fmt(p1, 4) + " %")
        print("  " + fmt(m2, 5) + ": " + fmt(p2, 4) + " %")


# ---- uncertainties ---------------------------------------------------------

def round_sig(x, figures):
    if x == 0:
        return 0.0
    if figures < 1:
        raise ValueError("Need at least 1 figure")
    return round(x, -int(math.floor(math.log10(abs(x)))) + (figures - 1))


def with_uncertainty(value, absolute):
    """'0.0824 +/- 0.0005' - uncertainty to 1 s.f., value to the same place."""
    if absolute <= 0:
        return fmt(value)
    unc = round_sig(absolute, 1)
    places = int(-math.floor(math.log10(abs(unc))))
    if places < 0:
        places = 0
    fmt_str = "%." + str(places) + "f"
    return (fmt_str % value) + " +/- " + (fmt_str % unc)


def menu_uncertainty():
    print("UNCERTAINTY")
    key = ask_choice("Find: ", [
        ("1", "abs <-> %"), ("2", "add/subtract"), ("3", "multiply/divide"),
        ("4", "power"), ("5", "% error"), ("6", "sig figs")])
    if key == "1":
        value = ask_float("measurement: ")
        which = ask_choice("You have: ", [("a", "absolute"), ("p", "percentage")])
        if which == "a":
            absolute = ask_float("absolute (+/-): ", True)
            show("% uncertainty", absolute / abs(value) * 100, "%")
        else:
            pct = ask_float("percentage (%): ", True)
            absolute = pct / 100.0 * abs(value)
            show("absolute", absolute)
        print("  " + with_uncertainty(value, absolute))
    elif key == "2":
        print("Negative value = subtract it")
        count = ask_int("How many measurements? ", 2, 6)
        total = 0.0
        unc = 0.0
        for i in range(count):
            total += ask_float("  value " + str(i + 1) + ": ")
            unc += ask_float("  absolute +/- : ", True)
        show("result", total)
        show("absolute", unc)
        if total != 0:
            show("percentage", unc / abs(total) * 100, "%")
        print("  " + with_uncertainty(total, unc))
    elif key == "3":
        count = ask_int("How many measurements? ", 2, 6)
        result = None
        pct = 0.0
        for i in range(count):
            value = ask_float("  value " + str(i + 1) + ": ")
            pct += ask_float("  percentage % : ", True)
            if result is None:
                result = value
            else:
                op = ask_choice("   times or divide: ", [("x", "x"), ("d", "/")])
                if op == "x":
                    result *= value
                else:
                    if value == 0:
                        print("Cannot divide by 0")
                        return
                    result /= value
        show("result", result)
        show("percentage", pct, "%")
        absolute = abs(result) * pct / 100.0
        show("absolute", absolute)
        print("  " + with_uncertainty(result, absolute))
    elif key == "4":
        value = ask_float("value: ")
        pct = ask_float("percentage %: ", True)
        power = ask_float("power: ")
        result = value ** power
        new_pct = pct * abs(power)
        show("result", result)
        show("percentage", new_pct, "%")
        show("absolute", abs(result) * new_pct / 100.0)
    elif key == "5":
        exp = ask_float("experimental: ")
        acc = ask_float("accepted: ")
        if acc == 0:
            print("Accepted value cannot be 0")
            return
        show("% error", abs(exp - acc) / abs(acc) * 100, "%")
    else:
        value = ask_float("value: ")
        figures = ask_int("significant figures: ", 1, 10)
        show("rounded", round_sig(value, figures))


# ---- index of hydrogen deficiency ------------------------------------------

def ihd(formula):
    counts = parse_formula(formula)
    if "C" not in counts:
        raise ValueError("Needs carbon")
    C = counts.get("C", 0)
    H = counts.get("H", 0)
    N = counts.get("N", 0)
    X = 0
    for hal in ("F", "Cl", "Br", "I"):
        X += counts.get(hal, 0)
    twice = 2 * C + 2 + N - H - X
    if twice < 0:
        raise ValueError("Too many hydrogens")
    if twice % 2:
        raise ValueError("Formula cannot exist")
    return twice // 2


def menu_ihd():
    print("IHD = (2C + 2 + N - H - X)/2")
    formula = ask_text("Formula: ")
    value = ihd(formula)
    show("IHD", value)
    if value == 0:
        print("Saturated: no rings or C=C")
    elif value == 1:
        print("1 ring or 1 double bond")
    elif value == 4:
        print("Often a benzene ring")
    else:
        print(str(value) + " rings and/or pi bonds")


MENU = [
    ("1", "Isotopes and Ar", menu_isotopes),
    ("2", "Uncertainties", menu_uncertainty),
    ("3", "IHD (organic)", menu_ihd),
]
