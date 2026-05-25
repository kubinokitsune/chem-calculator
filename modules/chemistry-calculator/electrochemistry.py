"""
electrochemistry.py — Electrochemistry module
Covers: cell potential, Gibbs energy, Faraday's law, Nernst equation,
        spontaneity checker, and galvanic/electrolytic identifier.
"""

import math
from constants import F, R, REDUCTION_POTENTIALS, get_reduction_potential

# ── Pure calculation functions (no I/O) ───────────────────────────────────────

def cell_potential(E_cathode: float, E_anode: float) -> float:
    """E°cell = E°cathode − E°anode (V)."""
    return E_cathode - E_anode


def assign_electrodes(E1: float, E2: float) -> tuple:
    """Return (E_cathode, E_anode) — higher reduction potential is cathode."""
    if E1 >= E2:
        return E1, E2
    return E2, E1


def gibbs_from_cell(n: int, E_cell: float) -> float:
    """ΔG° = −nFE°  (returns kJ/mol)."""
    if n <= 0:
        raise ValueError("n must be a positive integer (electrons transferred).")
    return -n * F * E_cell / 1000  # J → kJ


def n_from_gibbs(dG_kJ: float, E_cell: float) -> float:
    """Solve n = −ΔG° / (F × E°).  E_cell must be non-zero."""
    if E_cell == 0:
        raise ValueError("E°cell is zero — n is undefined.")
    n = -dG_kJ * 1000 / (F * E_cell)
    if n <= 0:
        raise ValueError(f"Computed n={n:.4f} is non-positive — check signs.")
    return n


def E_from_gibbs(n: int, dG_kJ: float) -> float:
    """Solve E° = −ΔG° / (nF)."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    return -dG_kJ * 1000 / (n * F)


# Faraday's Law:  mass = (I × t × M) / (n × F)

def faraday_mass(I: float, t: float, M: float, n: int) -> float:
    """Mass deposited in grams."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if F == 0:
        raise ZeroDivisionError("Faraday constant is zero.")
    return (I * t * M) / (n * F)


def faraday_current(mass: float, t: float, M: float, n: int) -> float:
    """Current (A) required to deposit *mass* grams in time *t* seconds."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if t == 0:
        raise ZeroDivisionError("Time cannot be zero.")
    if M == 0:
        raise ZeroDivisionError("Molar mass cannot be zero.")
    return (mass * n * F) / (t * M)


def faraday_time(mass: float, I: float, M: float, n: int) -> float:
    """Time (s) to deposit *mass* grams at current *I* amperes."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if I == 0:
        raise ZeroDivisionError("Current cannot be zero.")
    if M == 0:
        raise ZeroDivisionError("Molar mass cannot be zero.")
    return (mass * n * F) / (I * M)


def faraday_molar_mass(mass: float, I: float, t: float, n: int) -> float:
    """Molar mass (g/mol) of the deposited species."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if I == 0:
        raise ZeroDivisionError("Current cannot be zero.")
    if t == 0:
        raise ZeroDivisionError("Time cannot be zero.")
    return (mass * n * F) / (I * t)


# Nernst Equation:  E = E° − (RT / nF) × ln(Q)

def nernst(E_std: float, n: int, Q: float, T: float = 298.15) -> float:
    """Non-equilibrium cell potential E (V).
    Uses full RT/nF form; at 25 °C this equals E° − (0.05916/n)×log10(Q).
    """
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if Q <= 0:
        raise ValueError("Q (reaction quotient) must be positive.")
    return E_std - (R * T / (n * F)) * math.log(Q)


def nernst_Q(E: float, E_std: float, n: int, T: float = 298.15) -> float:
    """Solve Q given measured E."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    exponent = (E_std - E) * n * F / (R * T)
    return math.exp(exponent)


def nernst_E_std(E: float, n: int, Q: float, T: float = 298.15) -> float:
    """Solve E° given measured E and Q."""
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if Q <= 0:
        raise ValueError("Q must be positive.")
    return E + (R * T / (n * F)) * math.log(Q)


def spontaneity_check(E_cell: float, tol: float = 1e-9) -> str:
    """Return 'spontaneous', 'non-spontaneous', or 'equilibrium'."""
    if abs(E_cell) < tol:
        return "equilibrium"
    return "spontaneous" if E_cell > 0 else "non-spontaneous"


def cell_type(E_cell: float, tol: float = 1e-9) -> str:
    """Return 'galvanic', 'electrolytic', or 'equilibrium'."""
    if abs(E_cell) < tol:
        return "equilibrium"
    return "galvanic" if E_cell > 0 else "electrolytic"


# ── Helper: pick a half-cell from dictionary or enter custom value ─────────────

def _pick_half_cell(prompt_label: str) -> tuple:
    """Ask the user to choose from the table or enter a custom E° value.
    Returns (label, E_value).
    """
    print(f"\n  {prompt_label}")
    print("  [1] Choose from reduction potentials table")
    print("  [2] Enter a custom E° value")
    while True:
        ch = input("  Choice (1/2): ").strip()
        if ch == "1":
            _print_reduction_table()
            key = input("  Enter half-cell key exactly as shown (e.g. Cu2+/Cu): ").strip()
            try:
                val = get_reduction_potential(key)
                print(f"  → E°({key}) = {val:+.3f} V")
                return key, val
            except KeyError as e:
                print(f"  [ERROR] {e}")
        elif ch == "2":
            label = input("  Half-cell label (for display): ").strip() or "custom"
            raw = input("  E° value (V): ").strip()
            try:
                val = float(raw)
                return label, val
            except ValueError:
                print("  [ERROR] Please enter a numeric value.")
        else:
            print("  Invalid choice.")


def _print_reduction_table():
    print("\n  ┌─────────────────────────────────┐")
    print("  │  Standard Reduction Potentials  │")
    print("  ├───────────────┬─────────────────┤")
    print("  │ Half-cell     │   E° (V)        │")
    print("  ├───────────────┼─────────────────┤")
    for key, val in REDUCTION_POTENTIALS.items():
        print(f"  │ {key:<13} │  {val:+8.3f}       │")
    print("  └───────────────┴─────────────────┘")


def _get_n(prompt: str = "  Electrons transferred (n): ") -> int:
    while True:
        raw = input(prompt).strip()
        try:
            n = int(raw)
            if n > 0:
                return n
            print("  [ERROR] n must be a positive integer.")
        except ValueError:
            print("  [ERROR] Enter a whole number.")


def _get_float(prompt: str, positive: bool = False, label: str = None) -> float:
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


# ── Sub-menus ──────────────────────────────────────────────────────────────────

def menu_cell_potential():
    print("\n=== Standard Cell Potential ===")
    print("  Enter two half-cells. The one with the higher E° becomes the cathode.")

    label1, E1 = _pick_half_cell("Half-cell 1")
    label2, E2 = _pick_half_cell("Half-cell 2")

    E_cat, E_an = assign_electrodes(E1, E2)
    cat_label = label1 if E1 >= E2 else label2
    an_label  = label2 if E1 >= E2 else label1

    E_cell = cell_potential(E_cat, E_an)
    status = spontaneity_check(E_cell)
    ctype  = cell_type(E_cell)

    print("\n  ── Results ──────────────────────────────────")
    print(f"  Cathode (reduction) : {cat_label}  E° = {E_cat:+.3f} V")
    print(f"  Anode   (oxidation) : {an_label}   E° = {E_an:+.3f} V")
    print(f"  E°cell = E°cathode − E°anode = {E_cat:+.3f} − ({E_an:+.3f}) = {E_cell:+.4f} V")
    print(f"  Spontaneity : {status.upper()}")
    print(f"  Cell type   : {ctype.upper()}")
    print("  ─────────────────────────────────────────────")


def menu_gibbs():
    print("\n=== Gibbs Free Energy from Cell Potential ===")
    print("  ΔG° = −nFE°   (F = 96 485 C/mol)")
    print("\n  Solve for:")
    print("  [1] ΔG° (given n and E°cell)")
    print("  [2] n   (given ΔG° and E°cell)")
    print("  [3] E°  (given ΔG° and n)")

    ch = input("  Choice (1-3): ").strip()

    if ch == "1":
        n      = _get_n()
        E_cell = _get_float("  E°cell (V): ")
        dG     = gibbs_from_cell(n, E_cell)
        status = spontaneity_check(E_cell)
        print(f"\n  ΔG° = −{n} × {F} × ({E_cell:+.4f}) / 1000")
        print(f"  ΔG° = {dG:+.4f} kJ/mol")
        print(f"  Spontaneity: {status.upper()}")

    elif ch == "2":
        dG     = _get_float("  ΔG° (kJ/mol): ")
        E_cell = _get_float("  E°cell (V, non-zero): ")
        try:
            n = n_from_gibbs(dG, E_cell)
            print(f"\n  n = −ΔG° / (F × E°) = {n:.4f}")
            print("  (Round to nearest whole number for the actual electron count.)")
        except ValueError as e:
            print(f"  [ERROR] {e}")

    elif ch == "3":
        dG = _get_float("  ΔG° (kJ/mol): ")
        n  = _get_n()
        try:
            E_cell = E_from_gibbs(n, dG)
            status = spontaneity_check(E_cell)
            print(f"\n  E°cell = −ΔG° / (nF) = {E_cell:+.4f} V")
            print(f"  Spontaneity: {status.upper()}")
        except ValueError as e:
            print(f"  [ERROR] {e}")

    else:
        print("  Invalid choice.")


def menu_faraday():
    print("\n=== Faraday's Law — Electrolysis ===")
    print("  mass = (I × t × M) / (n × F)")
    print("  I = current (A) | t = time (s) | M = molar mass (g/mol) | n = electrons")
    print("\n  Solve for:")
    print("  [1] Mass deposited (g)")
    print("  [2] Current I (A)")
    print("  [3] Time t (s)")
    print("  [4] Molar mass M (g/mol)")

    ch = input("  Choice (1-4): ").strip()

    try:
        if ch == "1":
            I    = _get_float("  Current I (A, >0): ", positive=True)
            t    = _get_float("  Time t (s, >0): ", positive=True)
            M    = _get_float("  Molar mass M (g/mol, >0): ", positive=True)
            n    = _get_n()
            mass = faraday_mass(I, t, M, n)
            print(f"\n  mass = ({I} × {t} × {M}) / ({n} × {F})")
            print(f"  mass = {mass:.5f} g")

        elif ch == "2":
            mass = _get_float("  Mass deposited (g, >0): ", positive=True)
            t    = _get_float("  Time t (s, >0): ", positive=True)
            M    = _get_float("  Molar mass M (g/mol, >0): ", positive=True)
            n    = _get_n()
            I    = faraday_current(mass, t, M, n)
            print(f"\n  I = (mass × n × F) / (t × M)")
            print(f"  I = ({mass} × {n} × {F}) / ({t} × {M})")
            print(f"  I = {I:.5f} A")

        elif ch == "3":
            mass = _get_float("  Mass deposited (g, >0): ", positive=True)
            I    = _get_float("  Current I (A, >0): ", positive=True)
            M    = _get_float("  Molar mass M (g/mol, >0): ", positive=True)
            n    = _get_n()
            t    = faraday_time(mass, I, M, n)
            mins = t / 60
            hrs  = t / 3600
            print(f"\n  t = (mass × n × F) / (I × M)")
            print(f"  t = ({mass} × {n} × {F}) / ({I} × {M})")
            print(f"  t = {t:.2f} s  ({mins:.2f} min  /  {hrs:.4f} h)")

        elif ch == "4":
            mass = _get_float("  Mass deposited (g, >0): ", positive=True)
            I    = _get_float("  Current I (A, >0): ", positive=True)
            t    = _get_float("  Time t (s, >0): ", positive=True)
            n    = _get_n()
            M    = faraday_molar_mass(mass, I, t, n)
            print(f"\n  M = (mass × n × F) / (I × t)")
            print(f"  M = ({mass} × {n} × {F}) / ({I} × {t})")
            print(f"  M = {M:.4f} g/mol")

        else:
            print("  Invalid choice.")

    except (ValueError, ZeroDivisionError) as e:
        print(f"  [ERROR] {e}")


def menu_nernst():
    print("\n=== Nernst Equation (HL) ===")
    print("  E = E° − (RT / nF) × ln(Q)")
    print("  At 25 °C:  E = E° − (0.05916 / n) × log₁₀(Q)")
    print("\n  Solve for:")
    print("  [1] E  (non-standard cell potential)")
    print("  [2] Q  (reaction quotient)")
    print("  [3] E° (standard cell potential)")

    ch = input("  Choice (1-3): ").strip()

    try:
        if ch == "1":
            E_std = _get_float("  E°cell (V): ")
            n     = _get_n()
            Q     = _get_float("  Q (reaction quotient, >0): ", positive=True)
            T_raw = input("  Temperature (K) [press Enter for 298.15]: ").strip()
            T     = float(T_raw) if T_raw else 298.15
            E     = nernst(E_std, n, Q, T)
            factor = 0.05916 / n
            print(f"\n  E = {E_std:+.4f} − (0.05916 / {n}) × log₁₀({Q})")
            print(f"  E = {E_std:+.4f} − {factor:.5f} × {math.log10(Q):.4f}")
            print(f"  E = {E:+.5f} V")

        elif ch == "2":
            E     = _get_float("  Measured E (V): ")
            E_std = _get_float("  E°cell (V): ")
            n     = _get_n()
            T_raw = input("  Temperature (K) [press Enter for 298.15]: ").strip()
            T     = float(T_raw) if T_raw else 298.15
            Q     = nernst_Q(E, E_std, n, T)
            print(f"\n  Q = exp( (E° − E) × nF / RT )")
            print(f"  Q = {Q:.6e}")

        elif ch == "3":
            E     = _get_float("  Measured E (V): ")
            n     = _get_n()
            Q     = _get_float("  Q (reaction quotient, >0): ", positive=True)
            T_raw = input("  Temperature (K) [press Enter for 298.15]: ").strip()
            T     = float(T_raw) if T_raw else 298.15
            E_std = nernst_E_std(E, n, Q, T)
            print(f"\n  E° = E + (RT / nF) × ln(Q)")
            print(f"  E° = {E_std:+.5f} V")

        else:
            print("  Invalid choice.")

    except (ValueError, ZeroDivisionError) as e:
        print(f"  [ERROR] {e}")


def menu_spontaneity():
    print("\n=== Activity Series / Spontaneity Checker ===")
    print("  Will the redox reaction occur spontaneously?")
    print("  Enter the two half-reactions; the program determines cathode/anode.")

    label1, E1 = _pick_half_cell("Half-cell 1")
    label2, E2 = _pick_half_cell("Half-cell 2")

    E_cat, E_an = assign_electrodes(E1, E2)
    cat_label = label1 if E1 >= E2 else label2
    an_label  = label2 if E1 >= E2 else label1

    E_cell = cell_potential(E_cat, E_an)
    status = spontaneity_check(E_cell)

    print("\n  ── Result ───────────────────────────────────")
    print(f"  {cat_label} is reduced (cathode)  E° = {E_cat:+.3f} V")
    print(f"  {an_label} is oxidised (anode)    E° = {E_an:+.3f} V")
    print(f"  E°cell = {E_cell:+.4f} V")
    if status == "spontaneous":
        print("  → YES — the reaction is SPONTANEOUS (E°cell > 0, ΔG° < 0)")
    elif status == "non-spontaneous":
        print("  → NO  — the reaction is NON-SPONTANEOUS (E°cell < 0, ΔG° > 0)")
        print("          Energy input (electrolysis) would be required to drive it.")
    else:
        print("  → The system is at EQUILIBRIUM (E°cell = 0)")
    print("  ─────────────────────────────────────────────")


def menu_cell_type():
    print("\n=== Galvanic vs Electrolytic Cell Identifier ===")
    raw = input("  Enter E°cell (V): ").strip()
    try:
        E_cell = float(raw)
    except ValueError:
        print("  [ERROR] Enter a numeric value.")
        return

    ctype  = cell_type(E_cell)
    status = spontaneity_check(E_cell)

    print(f"\n  E°cell = {E_cell:+.4f} V")
    if ctype == "galvanic":
        print("  Cell type : GALVANIC (voltaic)")
        print("  → Spontaneous reaction — the cell produces electrical energy.")
        print("  → E°cell > 0  →  ΔG° < 0")
    elif ctype == "electrolytic":
        print("  Cell type : ELECTROLYTIC")
        print("  → Non-spontaneous — electrical energy must be supplied.")
        print("  → E°cell < 0  →  ΔG° > 0")
    else:
        print("  Cell type : EQUILIBRIUM")
        print("  → E°cell = 0 — no net driving force.")


# ── Main menu ──────────────────────────────────────────────────────────────────

def electrochemistry_menu():
    while True:
        print("\n=== Electrochemistry Calculator ===")
        print("1. Standard Cell Potential (E°cell)")
        print("2. Gibbs Free Energy from Cell Potential (ΔG° = −nFE°)")
        print("3. Faraday's Law — Electrolysis (mass / I / t / M)")
        print("4. Nernst Equation — Non-Standard Potential (HL)")
        print("5. Spontaneity Checker (Activity Series)")
        print("6. Galvanic vs Electrolytic Cell Identifier")
        print("0. Back to main menu")

        choice = input("Select (0-6): ").strip()

        if choice == "1":
            menu_cell_potential()
        elif choice == "2":
            menu_gibbs()
        elif choice == "3":
            menu_faraday()
        elif choice == "4":
            menu_nernst()
        elif choice == "5":
            menu_spontaneity()
        elif choice == "6":
            menu_cell_type()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
