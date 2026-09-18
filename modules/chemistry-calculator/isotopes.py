"""
isotopes.py — relative atomic mass from isotope abundances (IB S1.2)

Ar = Σ(isotope mass × abundance) / Σ(abundance)

Abundances can be percentages (adding to 100) or relative peak heights from a
mass spectrum — both work, because the total is divided out.
"""

import math


def _check(isotopes):
    """isotopes: list of (mass, abundance). Returns a cleaned list."""
    cleaned = []
    for i, item in enumerate(isotopes, 1):
        try:
            mass, abundance = float(item[0]), float(item[1])
        except (TypeError, ValueError, IndexError):
            raise ValueError(f"Isotope {i} needs a mass and an abundance.")
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError(f"Isotope {i}: mass must be greater than zero.")
        if not math.isfinite(abundance) or abundance < 0:
            raise ValueError(f"Isotope {i}: abundance cannot be negative.")
        cleaned.append((mass, abundance))
    if len(cleaned) < 2:
        raise ValueError("Enter at least two isotopes.")
    if sum(a for _, a in cleaned) <= 0:
        raise ValueError("The abundances cannot all be zero.")
    return cleaned


def relative_atomic_mass(isotopes):
    """Ar from [(mass, abundance), ...] — abundances may be % or peak heights."""
    data = _check(isotopes)
    total = sum(a for _, a in data)
    return sum(m * a for m, a in data) / total


def percentage_abundances(isotopes):
    """The same abundances expressed as percentages of the total."""
    data = _check(isotopes)
    total = sum(a for _, a in data)
    return [a / total * 100 for _, a in data]


def abundance_from_Ar(Ar, mass_1, mass_2):
    """
    Two isotopes and a known Ar: what percentage of each?
    Ar = (x·m₁ + (100 − x)·m₂) / 100  →  x = 100(Ar − m₂)/(m₁ − m₂)
    Returns (percent_of_mass_1, percent_of_mass_2).
    """
    Ar, m1, m2 = float(Ar), float(mass_1), float(mass_2)
    if not all(math.isfinite(v) for v in (Ar, m1, m2)):
        raise ValueError("Ar and both isotope masses must be numbers.")
    if m1 == m2:
        raise ValueError("The two isotope masses must be different.")
    if not (min(m1, m2) <= Ar <= max(m1, m2)):
        raise ValueError(f"Ar = {Ar:g} must lie between the two isotope masses "
                         f"({min(m1, m2):g} and {max(m1, m2):g}).")
    x = 100 * (Ar - m2) / (m1 - m2)
    return x, 100 - x


def mass_spectrum_summary(isotopes, symbol=""):
    """Lines of working for an Ar calculation."""
    data = _check(isotopes)
    total = sum(a for _, a in data)
    Ar = relative_atomic_mass(data)
    name = symbol.strip() or "the element"
    lines = [f"Isotopes of {name}:"]
    lines += [f"  mass {m:g}, abundance {a:g}" + (f" ({a / total * 100:.2f} %)" if total != 100 else "")
              for m, a in data]
    lines.append("Ar = Σ(mass × abundance) ÷ Σ(abundance)")
    lines.append("Ar = (" + " + ".join(f"{m:g} × {a:g}" for m, a in data) + f") ÷ {total:g}")
    lines.append(f"Ar = {Ar:.4f}")
    return lines


# ── Menu ─────────────────────────────────────────────────────────────────────

def _get_float(prompt, label=None, positive=False):
    label = label or prompt.strip().rstrip(':')
    while True:
        raw = input(prompt).strip()
        try:
            v = float(raw)
        except ValueError:
            print(f"  [ERROR] Invalid input: expected a number for {label}.")
            continue
        if positive and v <= 0:
            print(f"  [ERROR] {label} must be greater than zero.")
            continue
        return v


def isotopes_menu():
    while True:
        print("\n--- Isotopes & Relative Atomic Mass ---")
        print("1. Ar from isotope masses and abundances")
        print("2. Abundances from Ar (two isotopes)")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-2): ").strip()
        if choice == "1":
            symbol = input("Element symbol (optional): ").strip()
            raw = input("How many isotopes? ").strip()
            try:
                count = int(raw)
                if count < 2:
                    print("  [ERROR] Enter at least two isotopes.")
                    continue
            except ValueError:
                print("  [ERROR] Expected a whole number.")
                continue
            data = []
            for i in range(count):
                m = _get_float(f"  Isotope {i+1} mass: ", "mass", positive=True)
                a = _get_float(f"  Isotope {i+1} abundance (% or peak height): ", "abundance")
                data.append((m, a))
            try:
                for line in mass_spectrum_summary(data, symbol):
                    print("  " + line)
            except ValueError as e:
                print(f"  [ERROR] {e}")
        elif choice == "2":
            Ar = _get_float("Relative atomic mass Ar: ", "Ar", positive=True)
            m1 = _get_float("Mass of isotope 1: ", "mass 1", positive=True)
            m2 = _get_float("Mass of isotope 2: ", "mass 2", positive=True)
            try:
                p1, p2 = abundance_from_Ar(Ar, m1, m2)
                print(f"  Isotope {m1:g}: {p1:.2f} %")
                print(f"  Isotope {m2:g}: {p2:.2f} %")
            except ValueError as e:
                print(f"  [ERROR] {e}")
        elif choice in ("0", "exit"):
            break
        else:
            print("Invalid choice. Please try again.")
