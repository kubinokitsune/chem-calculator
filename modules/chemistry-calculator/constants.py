"""
constants.py — shared physical/chemical constants for all calculator modules.
Import what you need: from constants import R, BOND_ENTHALPIES, get_bond_enthalpy, ...
"""

from Periodic_table import ELEMENTS as _TABLE

# ── Universal Constants ────────────────────────────────────────────────────────
R            = 8.314          # J/mol·K  (ideal gas constant)
R_ATM        = 0.08206        # L·atm/mol·K
F            = 96485          # C/mol    (Faraday constant)
AVOGADRO     = 6.022e23       # mol⁻¹
PLANCK       = 6.626e-34      # J·s
SPEED_LIGHT  = 3.00e8         # m/s

# ── Thermodynamic Constants ────────────────────────────────────────────────────
Kw                  = 1.0e-14  # water ion product at 25 °C
T_STANDARD          = 298.15   # K  (standard temperature)
T_STP               = 273.15   # K  (STP temperature)
P_STP               = 100.0    # kPa
MOLAR_VOLUME_STP    = 22.7     # L/mol at STP  (100 kPa, 0 °C)
MOLAR_VOLUME_SATP   = 24.8     # L/mol at SATP (100 kPa, 25 °C)
SPECIFIC_HEAT_WATER = 4.18     # J/g·K

# ── Standard Reduction Potentials (V vs SHE) ──────────────────────────────────
# Keys are "oxidised/reduced" pairs matching common textbook notation.
REDUCTION_POTENTIALS = {
    "F2/F-":          +2.87,
    "MnO4-/Mn2+":    +1.51,
    "Cl2/Cl-":        +1.36,
    "Cr2O72-/Cr3+":  +1.33,
    "Br2/Br-":        +1.07,
    "Ag+/Ag":         +0.80,
    "Fe3+/Fe2+":      +0.77,
    "I2/I-":          +0.54,
    "Cu2+/Cu":        +0.34,
    "H+/H2":           0.00,
    "Pb2+/Pb":        -0.13,
    "Sn2+/Sn":        -0.14,
    "Ni2+/Ni":        -0.26,
    "Fe2+/Fe":        -0.44,
    "Zn2+/Zn":        -0.76,
    "Al3+/Al":        -1.66,
    "Mg2+/Mg":        -2.37,
    "Na+/Na":         -2.71,
    "Ca2+/Ca":        -2.87,
    "K+/K":           -2.92,
    "Li+/Li":         -3.04,
}

# ── Bond Enthalpies (kJ/mol), IB Chemistry data booklet ────────────────────────
BOND_ENTHALPIES = {
    "H-H":   436,
    "O=O":   498,
    "O-O":   144,
    "O-H":   463,
    "N#N":   945,
    "N=N":   470,
    "N-N":   158,
    "N-H":   391,
    "N-O":   201,
    "N=O":   587,
    "C-C":   346,
    "C=C":   614,
    "C#C":   839,
    "C-H":   414,
    "C-O":   358,
    "C=O":   804,
    "C-N":   305,
    "C=N":   615,
    "C#N":   890,
    "C-F":   492,
    "C-Cl":  324,
    "C-Br":  285,
    "F-F":   159,
    "Cl-Cl": 242,
    "Br-Br": 193,
    "I-I":   151,
    "H-F":   567,
    "H-Cl":  431,
    "H-Br":  366,
    "H-I":   298,
    "H-N":   391,
    "S=O":   523,
    "S-H":   364,
}

# ── Getter Functions ───────────────────────────────────────────────────────────

def get_bond_enthalpy(bond: str) -> float:
    """Return bond enthalpy in kJ/mol for *bond* (e.g. 'C-H', 'O=O', 'N#N').

    Tries the key as given, then tries reversing the two atom labels around the
    bond-order symbol so 'H-C' finds 'C-H'.  Raises KeyError with a clear
    message if the bond is not in the table.
    """
    if bond in BOND_ENTHALPIES:
        return BOND_ENTHALPIES[bond]

    # Try reversed: split on the bond-order character (#, =, -)
    for sep in ("#", "=", "-"):
        if sep in bond:
            parts = bond.split(sep, 1)
            reversed_key = f"{parts[1]}{sep}{parts[0]}"
            if reversed_key in BOND_ENTHALPIES:
                return BOND_ENTHALPIES[reversed_key]
            break

    available = ", ".join(sorted(BOND_ENTHALPIES.keys()))
    raise KeyError(
        f"Bond '{bond}' not found in BOND_ENTHALPIES table.\n"
        f"Available bonds: {available}"
    )


def get_reduction_potential(half_cell: str) -> float:
    """Return standard reduction potential in V for *half_cell* (e.g. 'Cu2+/Cu').

    Raises KeyError with a clear message if the half-cell is not in the table.
    """
    if half_cell in REDUCTION_POTENTIALS:
        return REDUCTION_POTENTIALS[half_cell]

    available = ", ".join(sorted(REDUCTION_POTENTIALS.keys()))
    raise KeyError(
        f"Half-cell '{half_cell}' not found in REDUCTION_POTENTIALS table.\n"
        f"Available half-cells: {available}"
    )


# ── Formula Capitalizer ────────────────────────────────────────────────────────

# All valid element symbols, from the one element table in Periodic_table.py.
_ELEMENTS = {symbol for _z, symbol, _name, _mass in _TABLE}

# Two-letter symbols whose letters are also two valid single-element symbols,
# where the split reading is far more common in lowercase input:
# 'nh3' is NH3 not Nh3, 'hno3' is HNO3 not HNo3, 'co2' is CO2, 'hcn' is HCN,
# 'kscn' is KSCN, 'ch3cho' is CH3CHO, 'po4' is PO4, 'hf' is HF, 'cf4' is CF4.
# Type the proper capitalisation (e.g. 'CoCl2') to get the element instead.
_PREFER_SPLIT = {"Nh", "No", "Co", "Cn", "Sc", "Ho", "Po", "Hf", "Hs", "Bh", "Cf"}


def capitalize_formula(formula: str) -> str:
    """Properly capitalise a chemical formula typed in any case.

    Uses element-aware greedy matching: tries a 2-letter symbol first
    (e.g. 'na' → 'Na'), falls back to single-letter if the 2-letter
    combination is not a valid element.

    Ambiguity note: some 2-letter sequences are valid elements but may
    represent two separate elements in common formulas (e.g. 'co' = Co
    (cobalt) OR C+O as in CO2).  Symbols in _PREFER_SPLIT are read as two
    elements; for everything else the 2-letter element wins.  If a formula
    looks wrong, type it with correct capitalisation (e.g. 'CoCl2').

    Non-letter characters (digits, parentheses, *, .) are passed through
    unchanged.  If *formula* is empty or None, it is returned as-is.

    Examples
    --------
    'nacl'      → 'NaCl'
    'h2so4'     → 'H2SO4'
    'ca(oh)2'   → 'Ca(OH)2'
    'kmno4'     → 'KMnO4'
    'fe2o3'     → 'Fe2O3'
    'al2(so4)3' → 'Al2(SO4)3'
    'cuso4*5h2o'→ 'CuSO4*5H2O'
    """
    if not formula:
        return formula
    s = formula.strip()
    # If formula already has uppercase letters, treat it as already capitalised
    # and only fix the first character to be uppercase (trust user's casing).
    if any(c.isupper() for c in s):
        return s[0].upper() + s[1:] if s else s
    result = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isalpha():
            # Try 2-letter element first
            if i + 1 < len(s) and s[i + 1].isalpha():
                two = s[i].upper() + s[i + 1].lower()
                splittable = (two in _PREFER_SPLIT
                              and s[i].upper() in _ELEMENTS
                              and s[i + 1].upper() in _ELEMENTS)
                if two in _ELEMENTS and not splittable:
                    result.append(two)
                    i += 2
                    continue
            # Single-letter element
            result.append(s[i].upper())
            i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)


# ── Reading numbers at the keyboard ────────────────────────────────────────────
# The menus ask for numbers in one of two ways, and they are kept apart on
# purpose: some re-ask until the answer is usable, others give up after one try
# and let the caller decide (their callers check for None).

def ask_float(prompt, label=None, positive=False):
    """Ask until a number is typed. positive=True refuses zero and negatives too."""
    label = label or prompt.strip().rstrip(':')
    while True:
        raw = input(prompt).strip()
        try:
            val = float(raw)
        except ValueError:
            print(f"  [ERROR] Invalid input: expected a number for {label}.")
            continue
        if positive and val <= 0:
            print(f"  [ERROR] {label} must be greater than zero.")
            continue
        return val


def try_float(prompt, label=None, positive=False, allow_blank=False):
    """Ask once. Returns None for an unusable answer, and "" for an empty one
    when allow_blank is set."""
    label = label or prompt.strip().rstrip(':')
    raw = input(prompt).strip()
    if allow_blank and not raw:
        return ""
    try:
        val = float(raw)
    except ValueError:
        print(f"  [ERROR] Invalid input: expected a number for {label}.")
        return None
    if positive and val <= 0:
        print(f"  [ERROR] {label} must be greater than zero.")
        return None
    return val
