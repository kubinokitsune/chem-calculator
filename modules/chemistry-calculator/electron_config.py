"""
electron_config.py — electron configurations (IB S1.3)

Sub-levels are filled in the order given by the Madelung (n + l) rule, written
as 1s² 2s² 2p⁶ ... .  Chromium and copper (and the ones below them) are the
usual exceptions: a half-full or full d sub-level is more stable, so one 4s
electron moves across.

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
# Atoms whose ground state moves one s electron into the d sub-level
EXCEPTIONS = {
    24: "Cr", 29: "Cu", 41: "Nb", 42: "Mo", 44: "Ru", 45: "Rh", 47: "Ag", 78: "Pt", 79: "Au",
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
    """Move one s electron into the d sub-level for Cr, Cu and friends."""
    if Z not in EXCEPTIONS:
        return config
    s_label = {24: "4s", 29: "4s", 41: "5s", 42: "5s", 44: "5s", 45: "5s", 47: "5s",
               78: "6s", 79: "6s"}[Z]
    d_label = {24: "3d", 29: "3d", 41: "4d", 42: "4d", 44: "4d", 45: "4d", 47: "4d",
               78: "5d", 79: "5d"}[Z]
    moved = 2 if Z == 45 else 1          # Rh keeps 5s⁰
    s = next((p for p in config if p[0] == s_label), None)
    d = next((p for p in config if p[0] == d_label), None)
    if s and d and s[1] >= moved:
        s[1] -= moved
        d[1] += moved
        if s[1] == 0:
            config = [p for p in config if p is not s]
    return config


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
    remaining, left = [], core_electrons
    for label, count in config:
        if left >= count:
            left -= count
            continue
        remaining.append((label, count - left))
        left = 0
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
        lines.append(f"Note: {element['symbol']} is an exception — an s electron moves into the "
                     "d sub-level because a half-full or full d sub-level is more stable.")
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
