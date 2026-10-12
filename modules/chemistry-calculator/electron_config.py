"""
electron_config.py — electron configurations (IB S1.3)

Sub-levels are filled in the order given by the Madelung (n + l) rule, written
as 1s² 2s² 2p⁶ ... .  Chromium and copper (and the ones below them, plus a few
f-block atoms) are the exceptions in EXCEPTIONS: a half-full or full d sub-level
is more stable, so an s electron moves across.

For ions, electrons are removed from the highest main level first — so for
transition metals the 4s electrons go before the 3d ones.
"""

from Periodic_table import (ELEMENTS, get_element_by_symbol, get_element_by_number,
                           get_element_by_name)

# Sub-level filling order (Madelung), with capacities
ORDER = [
    ("1s", 2), ("2s", 2), ("2p", 6), ("3s", 2), ("3p", 6), ("4s", 2), ("3d", 10),
    ("4p", 6), ("5s", 2), ("4d", 10), ("5p", 6), ("6s", 2), ("4f", 14), ("5d", 10),
    ("6p", 6), ("7s", 2), ("5f", 14), ("6d", 10), ("7p", 6),
]
NOBLE_GASES = [(2, "He"), (10, "Ne"), (18, "Ar"), (36, "Kr"), (54, "Xe"), (86, "Rn")]
# Ground states that break the Madelung order: Z -> (from, to, electrons moved).
# Source: NIST Atomic Spectra Database, "Ground Levels and Ionization Energies
# for the Neutral Atoms" (physics.nist.gov/PhysRefData/IonEnergy/tblNew.html),
# cross-checked with the CRC Handbook table "Electron Configuration of Neutral
# Atoms in the Ground State". The IB syllabus (S1.3, Z <= 36) only expects Cr
# and Cu; the rest are kept because they are the real ground states.
# casio-addin/src/core/tools.c carries the same table; test_ib_chemistry.py
# parses it and checks the two agree.
EXCEPTIONS = {
    24: ("4s", "3d", 1),   # Cr  [Ar] 3d5 4s1
    29: ("4s", "3d", 1),   # Cu  [Ar] 3d10 4s1
    41: ("5s", "4d", 1),   # Nb  [Kr] 4d4 5s1
    42: ("5s", "4d", 1),   # Mo  [Kr] 4d5 5s1
    44: ("5s", "4d", 1),   # Ru  [Kr] 4d7 5s1
    45: ("5s", "4d", 1),   # Rh  [Kr] 4d8 5s1
    46: ("5s", "4d", 2),   # Pd  [Kr] 4d10
    47: ("5s", "4d", 1),   # Ag  [Kr] 4d10 5s1
    57: ("4f", "5d", 1),   # La  [Xe] 5d1 6s2
    58: ("4f", "5d", 1),   # Ce  [Xe] 4f1 5d1 6s2
    64: ("4f", "5d", 1),   # Gd  [Xe] 4f7 5d1 6s2
    78: ("6s", "5d", 1),   # Pt  [Xe] 4f14 5d9 6s1
    79: ("6s", "5d", 1),   # Au  [Xe] 4f14 5d10 6s1
    89: ("5f", "6d", 1),   # Ac  [Rn] 6d1 7s2
    90: ("5f", "6d", 2),   # Th  [Rn] 6d2 7s2
    91: ("5f", "6d", 1),   # Pa  [Rn] 5f2 6d1 7s2
    92: ("5f", "6d", 1),   # U   [Rn] 5f3 6d1 7s2
    93: ("5f", "6d", 1),   # Np  [Rn] 5f4 6d1 7s2
    96: ("5f", "6d", 1),   # Cm  [Rn] 5f7 6d1 7s2
}
_SUPER = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _fill(electrons):
    """Fill sub-levels in order; returns [(label, count), ...]."""
    left, out = electrons, []
    for label, capacity in ORDER:
        if left <= 0:
            break
        n = min(capacity, left)
        out.append([label, n])
        left -= n
    if left > 0:
        raise ValueError("Too many electrons for the sub-levels in this table.")
    return out


def _apply_exception(config, Z):
    """Move the electrons the ground state moves (see EXCEPTIONS)."""
    if Z not in EXCEPTIONS:
        return config
    src, dst, moved = EXCEPTIONS[Z]
    counts = dict(config)
    counts[src] -= moved
    counts[dst] = counts.get(dst, 0) + moved
    return [[label, n] for label, n in counts.items() if n > 0]


def _sort_for_writing(config):
    """Write sub-levels by main level, then by sub-level (3d before 4s)."""
    return sorted(config, key=lambda p: (int(p[0][0]), "spdf".index(p[0][1])))


def electron_configuration(symbol_or_number, charge=0):
    """
    Full configuration, e.g. 'Fe' → '1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁶ 4s²',
    'Fe' with charge +3 → '1s² 2s² 2p⁶ 3s² 3p⁶ 3d⁵'.
    Returns (text, list of (label, count), element dict).
    """
    text = str(symbol_or_number).strip()
    if text.isdigit():
        element = get_element_by_number(int(text))
    else:
        element = get_element_by_symbol(text) or get_element_by_name(text)
    if not element:
        raise ValueError(f"'{symbol_or_number}' is not an element in the table.")
    try:
        charge = int(charge)
    except (TypeError, ValueError):
        raise ValueError("Charge must be a whole number such as 0, 2 or -1.")
    Z = element["number"]
    electrons = Z - charge
    if electrons < 1:
        raise ValueError(f"A charge of {charge:+d} would leave {element['symbol']} with no electrons.")
    if electrons > 118:
        raise ValueError("That is more electrons than this table covers.")

    config = _fill(electrons)
    if charge == 0:
        config = _apply_exception(config, Z)
    elif charge > 0:
        # cations: strip from the highest main level first (4s before 3d)
        config = _fill(Z)
        config = _apply_exception(config, Z)
        to_remove = charge
        while to_remove > 0:
            highest = max(int(p[0][0]) for p in config if p[1] > 0)
            pick = max((p for p in config if p[1] > 0 and int(p[0][0]) == highest),
                       key=lambda p: "spdf".index(p[0][1]))
            take = min(pick[1], to_remove)
            pick[1] -= take
            to_remove -= take
        config = [p for p in config if p[1] > 0]

    config = _sort_for_writing([p for p in config if p[1] > 0])
    text = " ".join(f"{label}{str(count).translate(_SUPER)}" for label, count in config)
    return text, [(l, c) for l, c in config], element


def noble_gas_shorthand(symbol_or_number, charge=0):
    """'Fe' → '[Ar] 3d⁶ 4s²'."""
    text, config, element = electron_configuration(symbol_or_number, charge)
    electrons = element["number"] - int(charge)
    core_symbol, core_electrons = None, 0
    for z, sym in NOBLE_GASES:
        if z < electrons:
            core_symbol, core_electrons = sym, z
    if not core_symbol:
        return text
    # the core is a set of sub-levels (Madelung order), not the first electrons written
    core = dict(electron_configuration(core_electrons)[1])
    remaining = [(label, count - core.get(label, 0)) for label, count in config
                 if count > core.get(label, 0)]
    shown = " ".join(f"{label}{str(count).translate(_SUPER)}" for label, count in remaining)
    return f"[{core_symbol}] {shown}".strip()


def valence_electrons(symbol_or_number, charge=0):
    """
    (s and p electrons in the highest occupied main level,
     d electrons in that level or the one below — the ones transition metals
     also use in bonding).
    """
    _, config, _ = electron_configuration(symbol_or_number, charge)
    highest = max(int(label[0]) for label, _ in config)
    outer = sum(c for label, c in config if int(label[0]) == highest and label[1] in "sp")
    d_electrons = sum(c for label, c in config
                      if label[1] == "d" and int(label[0]) in (highest, highest - 1))
    return outer, d_electrons


def configuration_lines(symbol_or_number, charge=0):
    """Lines of working for the menus and the web page."""
    text, config, element = electron_configuration(symbol_or_number, charge)
    short = noble_gas_shorthand(symbol_or_number, charge)
    outer, d_electrons = valence_electrons(symbol_or_number, charge)
    name = element["name"].capitalize()
    label = element["symbol"] + (f"{abs(int(charge))}{'+' if int(charge) > 0 else '-'}" if charge else "")
    lines = [
        f"{label} — {name}, Z = {element['number']}, {element['number'] - int(charge)} electrons",
        "Filling order (Madelung): " + " → ".join(l for l, _ in ORDER[:len(config) + 2]),
        f"Full configuration: {text}",
        f"Noble-gas shorthand: {short}",
        f"Outer-level (s and p) electrons: {outer}"
        + (f", plus {d_electrons} in the d sub-level" if d_electrons else ""),
    ]
    if int(charge) == 0 and element["number"] in EXCEPTIONS:
        src, dst, moved = EXCEPTIONS[element["number"]]
        lines.append(f"Note: {element['symbol']} is an exception — {moved} electron"
                     f"{'s' if moved > 1 else ''} move{'' if moved > 1 else 's'} from {src} into {dst} "
                     "(the measured ground state; a half-full or full sub-level is more stable).")
    if int(charge) > 0:
        lines.append("Electrons are removed from the highest main level first "
                     "(so 4s goes before 3d).")
    return lines


# ── Menu ─────────────────────────────────────────────────────────────────────

def electron_config_menu():
    while True:
        print("\n--- Electron Configuration ---")
        print("Enter an element symbol, name or atomic number (0 to return).")
        raw = input("Element: ").strip()
        if raw.lower() in ("0", "exit", ""):
            break
        charge_raw = input("Charge (0 for a neutral atom, e.g. 2 or -1): ").strip() or "0"
        try:
            for line in configuration_lines(raw, int(charge_raw)):
                print("  " + line)
        except ValueError as e:
            print(f"  [ERROR] {e}")
