"""
organic_tools.py — index of hydrogen deficiency (IB S3.2 / R3.4)

IHD (degrees of unsaturation) counts the rings and π bonds in a molecule:

    IHD = (2C + 2 + N − H − X) / 2

where X is any halogen (F, Cl, Br, I).  Oxygen and sulfur do not change it.
Each unit is one ring or one double bond; a triple bond counts as two.
"""

from percent_composition_calculator import parse_formula, FormulaError
from constants import capitalize_formula

HALOGENS = ("F", "Cl", "Br", "I", "At")


def index_of_hydrogen_deficiency(formula, charge=0):
    """IHD for a molecular formula such as 'C6H6' (benzene → 4)."""
    text = capitalize_formula(str(formula).strip())
    if not text:
        raise ValueError("Enter a molecular formula, e.g. C6H6.")
    try:
        counts = parse_formula(text)
    except FormulaError as e:
        raise ValueError(str(e))
    if "C" not in counts:
        raise ValueError("IHD is for organic (carbon-containing) molecules.")
    C = counts.get("C", 0)
    H = counts.get("H", 0)
    N = counts.get("N", 0)
    X = sum(counts.get(h, 0) for h in HALOGENS)
    ihd2 = 2 * C + 2 + N - H - X - int(charge)
    if ihd2 < 0:
        raise ValueError(f"That formula has too many hydrogens for {C} carbon atom(s) — check it.")
    if ihd2 % 2:
        raise ValueError("That formula cannot exist as written: the hydrogen count makes "
                         "the IHD a half number (check the formula).")
    return ihd2 // 2


def ihd_lines(formula, charge=0):
    """Lines of working, with what the answer suggests."""
    text = capitalize_formula(str(formula).strip())
    counts = parse_formula(text)
    C, H = counts.get("C", 0), counts.get("H", 0)
    N = counts.get("N", 0)
    X = sum(counts.get(h, 0) for h in HALOGENS)
    ihd = index_of_hydrogen_deficiency(formula, charge)
    meaning = {
        0: "no rings or double bonds — the molecule is saturated",
        1: "one ring or one C=C / C=O double bond",
        2: "two of: rings, double bonds, or one triple bond",
        4: "often a benzene ring (3 C=C + 1 ring)",
    }.get(ihd, f"{ihd} rings and/or π bonds in total")
    return [
        f"Formula: {text}",
        "IHD = (2C + 2 + N − H − X) ÷ 2   (X = halogens; O and S do not count)",
        f"C = {C}, H = {H}, N = {N}, halogens = {X}",
        f"IHD = (2×{C} + 2 + {N} − {H} − {X}) ÷ 2",
        f"IHD = {ihd}",
        f"That means: {meaning}.",
    ]


# ── Menu ─────────────────────────────────────────────────────────────────────

def organic_tools_menu():
    while True:
        print("\n--- Index of Hydrogen Deficiency ---")
        print("Enter a molecular formula (0 to return). Examples: C6H6, C4H8, C3H6O")
        raw = input("Formula: ").strip()
        if raw.lower() in ("0", "exit", ""):
            break
        try:
            for line in ihd_lines(raw):
                print("  " + line)
        except (ValueError, FormulaError) as e:
            print(f"  [ERROR] {e}")
