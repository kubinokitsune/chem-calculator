
# acid_base.py

import math

Kw = 1.0e-14  # at 25°C


# ── Constants ────────────────────────────────────────────────────────────────

STRONG_ACIDS = {"HCl", "HBr", "HI", "HNO3", "H2SO4", "HClO4"}
STRONG_BASES = {"LiOH", "NaOH", "KOH", "RbOH", "CsOH", "Ca(OH)2", "Sr(OH)2", "Ba(OH)2"}
AMPHOTERIC   = {"H2O", "HCO3-", "HSO4-", "H2PO4-", "HPO4(2-)"}
NEUTRAL      = {"NaCl", "KNO3", "KBr", "NaBr", "NaI", "KI"}


# ── Core math ────────────────────────────────────────────────────────────────

def pH_from_H(H):
    return -math.log10(H)

def pOH_from_OH(OH):
    return -math.log10(OH)

def H_from_pH(pH):
    return 10 ** (-pH)

def OH_from_pOH(pOH):
    return 10 ** (-pOH)

def all_four(*, pH=None, pOH=None, H=None, OH=None):
    """Given any one value return (pH, pOH, H, OH)."""
    if pH is not None:
        pH = float(pH)
    elif pOH is not None:
        pH = 14.0 - float(pOH)
    elif H is not None:
        pH = pH_from_H(float(H))
    elif OH is not None:
        pH = 14.0 + math.log10(float(OH))
    else:
        raise ValueError("Provide at least one value.")
    pOH = 14.0 - pH
    H   = H_from_pH(pH)
    OH  = OH_from_pOH(pOH)
    return pH, pOH, H, OH


# ── Strong acid / base ───────────────────────────────────────────────────────

def strong_acid_pH(concentration):
    """[H+] = C for strong monoprotic acid."""
    if concentration <= 0:
        raise ValueError("Concentration must be positive.")
    return pH_from_H(concentration)

def strong_base_pH(concentration):
    """[OH-] = C for strong monobasic base."""
    if concentration <= 0:
        raise ValueError("Concentration must be positive.")
    pOH = pOH_from_OH(concentration)
    return 14.0 - pOH


# ── Weak acid / base ─────────────────────────────────────────────────────────

def weak_acid_pH(Ka, C):
    """
    Approximation: [H+] ≈ sqrt(Ka * C).
    Falls back to quadratic if x > 5% of C.
    Quadratic: x^2 + Ka*x - Ka*C = 0
    """
    if Ka <= 0 or C <= 0:
        raise ValueError("Ka and C must be positive.")
    x_approx = math.sqrt(Ka * C)
    if x_approx / C <= 0.05:
        return pH_from_H(x_approx), True, x_approx
    # quadratic: x^2 + Ka*x - Ka*C = 0
    discriminant = Ka ** 2 + 4 * Ka * C
    x = (-Ka + math.sqrt(discriminant)) / 2
    return pH_from_H(x), False, x

def weak_base_pH(Kb, C):
    """
    Same logic as weak acid but finds [OH-] first.
    Returns (pH, used_approx, x)
    """
    if Kb <= 0 or C <= 0:
        raise ValueError("Kb and C must be positive.")
    x_approx = math.sqrt(Kb * C)
    if x_approx / C <= 0.05:
        pOH = pOH_from_OH(x_approx)
        return 14.0 - pOH, True, x_approx
    discriminant = Kb ** 2 + 4 * Kb * C
    x = (-Kb + math.sqrt(discriminant)) / 2
    pOH = pOH_from_OH(x)
    return 14.0 - pOH, False, x


# ── Ka / Kb / pKa / pKb ─────────────────────────────────────────────────────

def Ka_to_pKa(Ka):
    return -math.log10(Ka)

def pKa_to_Ka(pKa):
    return 10 ** (-pKa)

def Kb_to_pKb(Kb):
    return -math.log10(Kb)

def pKb_to_Kb(pKb):
    return 10 ** (-pKb)

def Ka_to_Kb(Ka):
    return Kw / Ka

def Kb_to_Ka(Kb):
    return Kw / Kb


# ── Henderson-Hasselbalch ────────────────────────────────────────────────────

def buffer_pH(Ka, acid_conc, base_conc):
    """pH = pKa + log([A-]/[HA])"""
    if acid_conc <= 0 or base_conc <= 0:
        raise ValueError("Concentrations must be positive.")
    return Ka_to_pKa(Ka) + math.log10(base_conc / acid_conc)

def buffer_ratio(Ka, target_pH):
    """Returns [A-]/[HA] needed to reach target_pH."""
    return 10 ** (target_pH - Ka_to_pKa(Ka))


# ── Acid/Base identifier ─────────────────────────────────────────────────────

def identify(formula):
    f = formula.strip()
    if f in STRONG_ACIDS:
        return "Strong acid"
    if f in STRONG_BASES:
        return "Strong base"
    if f in AMPHOTERIC:
        return "Amphoteric"
    if f in NEUTRAL:
        return "Neutral salt"
    # Heuristic fallback
    if f.startswith("H") and f not in {"H2O"}:
        return "Likely weak acid (not in strong-acid list)"
    if f.endswith("OH"):
        return "Likely weak base (not in strong-base list)"
    return "Unknown / likely neutral or weak"


# ── Titration ────────────────────────────────────────────────────────────────

def equivalence_moles(C, V_L):
    return C * V_L

def titration_find_concentration(n_equivalence, V_unknown_L):
    return n_equivalence / V_unknown_L

def titration_find_volume(n_equivalence, C_titrant):
    return n_equivalence / C_titrant

def equivalence_point_pH_description(acid_type, base_type):
    a = acid_type.lower()
    b = base_type.lower()
    if "strong" in a and "strong" in b:
        return "pH ≈ 7 (neutral salt)"
    if "weak" in a and "strong" in b:
        return "pH > 7 (basic — conjugate base of weak acid)"
    if "strong" in a and "weak" in b:
        return "pH < 7 (acidic — conjugate acid of weak base)"
    return "pH depends on relative Ka/Kb values"


# ── Input helper ─────────────────────────────────────────────────────────────

def _get_float(prompt, label=None, positive=False):
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


# ── Sub-menus ────────────────────────────────────────────────────────────────

def menu_converter():
    print("\n-- pH / pOH / [H⁺] / [OH⁻] Converter --")
    print("Enter one known value:")
    print("1. pH")
    print("2. pOH")
    print("3. [H⁺] concentration (mol/L)")
    print("4. [OH⁻] concentration (mol/L)")
    choice = input("Select (1-4): ").strip()

    try:
        if choice == "1":
            val = _get_float("pH: ")
            pH, pOH, H, OH = all_four(pH=val)
        elif choice == "2":
            val = _get_float("pOH: ")
            pH, pOH, H, OH = all_four(pOH=val)
        elif choice == "3":
            val = _get_float("[H⁺] (mol/L): ")
            pH, pOH, H, OH = all_four(H=val)
        elif choice == "4":
            val = _get_float("[OH⁻] (mol/L): ")
            pH, pOH, H, OH = all_four(OH=val)
        else:
            print("Invalid choice."); return

        print(f"\n  pH          = {pH:.4f}")
        print(f"  pOH         = {pOH:.4f}")
        print(f"  [H⁺]        = {H:.4e} mol/L")
        print(f"  [OH⁻]       = {OH:.4e} mol/L")
        solution = "acidic" if pH < 7 else ("basic" if pH > 7 else "neutral")
        print(f"  Solution is {solution} at 25°C")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_strong():
    print("\n-- Strong Acid / Base pH Calculator --")
    print("1. Strong acid")
    print("2. Strong base")
    choice = input("Select (1-2): ").strip()

    if choice not in ("1", "2"):
        print("Invalid choice."); return

    if choice == "1":
        from constants import capitalize_formula
        print("  Common strong acids: HCl, HBr, HI, HNO3, H2SO4, HClO4")
        formula = capitalize_formula(input("  Formula (optional, press Enter to skip): ").strip())
        C = _get_float("  Concentration (mol/L): ", "concentration", positive=True)
        try:
            pH = strong_acid_pH(C)
            _, pOH, H, OH = all_four(pH=pH)
            if formula:
                print(f"\n  {formula} — strong acid")
            print(f"  pH   = {pH:.4f}")
            print(f"  pOH  = {pOH:.4f}")
            print(f"  [H⁺] = {H:.4e} mol/L")
        except ValueError as e:
            print(f"  Error: {e}")
    else:
        from constants import capitalize_formula
        print("  Common strong bases: NaOH, KOH, Ca(OH)2, Ba(OH)2")
        formula = capitalize_formula(input("  Formula (optional, press Enter to skip): ").strip())
        C = _get_float("  Concentration (mol/L): ", "concentration", positive=True)
        try:
            pH = strong_base_pH(C)
            _, pOH, H, OH = all_four(pH=pH)
            if formula:
                print(f"\n  {formula} — strong base")
            print(f"  pH    = {pH:.4f}")
            print(f"  pOH   = {pOH:.4f}")
            print(f"  [OH⁻] = {OH:.4e} mol/L")
        except ValueError as e:
            print(f"  Error: {e}")


def menu_weak():
    print("\n-- Weak Acid / Base pH Calculator --")
    print("1. Weak acid  (uses Ka)")
    print("2. Weak base  (uses Kb)")
    choice = input("Select (1-2): ").strip()

    if choice not in ("1", "2"):
        print("Invalid choice."); return

    if choice == "1":
        Ka = _get_float("  Ka (e.g. 1.8e-5): ", "Ka", positive=True)
        C  = _get_float("  Initial concentration (mol/L): ", "concentration", positive=True)
        try:
            pH, approx, x = weak_acid_pH(Ka, C)
            _, pOH, H, OH = all_four(pH=pH)
            method = "approximation (x < 5% of C)" if approx else "quadratic formula (approximation failed)"
            print(f"\n  Method: {method}")
            print(f"  [H⁺] = {x:.4e} mol/L")
            print(f"  pH   = {pH:.4f}")
            print(f"  pOH  = {pOH:.4f}")
            if not approx:
                print(f"  Note: x/C = {x/C*100:.2f}% — quadratic was necessary.")
        except ValueError as e:
            print(f"  Error: {e}")
    else:
        Kb = _get_float("  Kb (e.g. 1.8e-5): ", "Kb", positive=True)
        C  = _get_float("  Initial concentration (mol/L): ", "concentration", positive=True)
        try:
            pH, approx, x = weak_base_pH(Kb, C)
            _, pOH, H, OH = all_four(pH=pH)
            method = "approximation (x < 5% of C)" if approx else "quadratic formula (approximation failed)"
            print(f"\n  Method: {method}")
            print(f"  [OH⁻] = {x:.4e} mol/L")
            print(f"  pH    = {pH:.4f}")
            print(f"  pOH   = {pOH:.4f}")
            if not approx:
                print(f"  Note: x/C = {x/C*100:.2f}% — quadratic was necessary.")
        except ValueError as e:
            print(f"  Error: {e}")


def menu_Ka_Kb():
    print("\n-- Ka / Kb / pKa / pKb Converter --")
    print("1. Ka  → pKa, Kb, pKb")
    print("2. pKa → Ka,  Kb, pKb")
    print("3. Kb  → pKb, Ka, pKa")
    print("4. pKb → Kb,  Ka, pKa")
    choice = input("Select (1-4): ").strip()

    try:
        if choice == "1":
            Ka  = _get_float("  Ka: ")
            pKa = Ka_to_pKa(Ka)
            Kb  = Ka_to_Kb(Ka)
            pKb = Kb_to_pKb(Kb)
        elif choice == "2":
            pKa = _get_float("  pKa: ")
            Ka  = pKa_to_Ka(pKa)
            Kb  = Ka_to_Kb(Ka)
            pKb = Kb_to_pKb(Kb)
        elif choice == "3":
            Kb  = _get_float("  Kb: ")
            pKb = Kb_to_pKb(Kb)
            Ka  = Kb_to_Ka(Kb)
            pKa = Ka_to_pKa(Ka)
        elif choice == "4":
            pKb = _get_float("  pKb: ")
            Kb  = pKb_to_Kb(pKb)
            Ka  = Kb_to_Ka(Kb)
            pKa = Ka_to_pKa(Ka)
        else:
            print("Invalid choice."); return

        print(f"\n  Ka  = {Ka:.4e}")
        print(f"  pKa = {pKa:.4f}")
        print(f"  Kb  = {Kb:.4e}")
        print(f"  pKb = {pKb:.4f}")
        print(f"  (Ka × Kb = {Ka*Kb:.2e}, Kw = 1.00×10⁻¹⁴)")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_buffer():
    print("\n-- Buffer pH (Henderson-Hasselbalch) --")
    print("  pH = pKa + log([A⁻]/[HA])")
    print("1. Calculate pH of a buffer")
    print("2. Find [A⁻]/[HA] ratio for a target pH")
    choice = input("Select (1-2): ").strip()

    print("  Enter Ka or pKa?")
    ka_choice = input("  (1) Ka  (2) pKa: ").strip()
    try:
        if ka_choice == "1":
            Ka = _get_float("  Ka: ")
        elif ka_choice == "2":
            pKa = _get_float("  pKa: ")
            Ka  = pKa_to_Ka(pKa)
        else:
            print("  Invalid."); return

        if choice == "1":
            HA  = _get_float("  [HA] weak acid concentration (mol/L): ")
            A   = _get_float("  [A⁻] conjugate base concentration (mol/L): ")
            pH  = buffer_pH(Ka, HA, A)
            print(f"\n  Buffer pH = {pH:.4f}")
            print(f"  pKa       = {Ka_to_pKa(Ka):.4f}")
            print(f"  [A⁻]/[HA] = {A/HA:.4f}")
        elif choice == "2":
            target = _get_float("  Target pH: ")
            ratio  = buffer_ratio(Ka, target)
            print(f"\n  Required [A⁻]/[HA] = {ratio:.4f}")
            print(f"  pKa                 = {Ka_to_pKa(Ka):.4f}")
            print(f"  (e.g. 1.00 mol/L acid + {ratio:.4f} mol/L conjugate base)")
        else:
            print("  Invalid choice.")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_identifier():
    from constants import capitalize_formula
    print("\n-- Acid/Base Identifier --")
    print("  Strong acids: HCl, HBr, HI, HNO3, H2SO4, HClO4")
    print("  Strong bases: LiOH, NaOH, KOH, RbOH, CsOH, Ca(OH)2, Sr(OH)2, Ba(OH)2")
    raw = input("  Enter formula: ").strip()
    if not raw:
        print("  [ERROR] Please enter a formula.")
        return
    formula = capitalize_formula(raw)
    result  = identify(formula)
    print(f"\n  {formula}  →  {result}")


def menu_titration():
    print("\n-- Titration Calculator --")
    print("1. Find unknown concentration  (know volume of unknown + titrant data)")
    print("2. Find volume of titrant needed  (know both concentrations)")
    print("3. Equivalence point pH description")
    choice = input("Select (1-3): ").strip()

    try:
        if choice == "1":
            C_titrant  = _get_float("  Concentration of titrant (mol/L): ", "titrant concentration", positive=True)
            V_titrant  = _get_float("  Volume of titrant at equivalence point (mL): ", "titrant volume", positive=True)
            V_unknown  = _get_float("  Volume of unknown solution (mL): ", "unknown volume", positive=True)
            n          = equivalence_moles(C_titrant, V_titrant / 1000)
            C_unknown  = titration_find_concentration(n, V_unknown / 1000)
            print(f"\n  Moles at equivalence = {n:.4e} mol")
            print(f"  Concentration of unknown = {C_unknown:.4f} mol/L")

        elif choice == "2":
            C_titrant  = _get_float("  Concentration of titrant (mol/L): ", "titrant concentration", positive=True)
            C_unknown  = _get_float("  Concentration of unknown (mol/L): ", "unknown concentration", positive=True)
            V_unknown  = _get_float("  Volume of unknown (mL): ", "unknown volume", positive=True)
            n          = equivalence_moles(C_unknown, V_unknown / 1000)
            V_titrant  = titration_find_volume(n, C_titrant) * 1000
            print(f"\n  Moles at equivalence = {n:.4e} mol")
            print(f"  Volume of titrant needed = {V_titrant:.4f} mL")

        elif choice == "3":
            print("  Acid type examples: strong acid, weak acid")
            acid = input("  Acid type: ").strip()
            base = input("  Base type: ").strip()
            desc = equivalence_point_pH_description(acid, base)
            print(f"\n  Equivalence point: {desc}")

        else:
            print("  Invalid choice.")
    except ValueError as e:
        print(f"  Error: {e}")


# ── Main menu ────────────────────────────────────────────────────────────────

def acid_base_menu():
    while True:
        print("\n=== Acid-Base Chemistry Calculator ===")
        print("1. pH / pOH / [H⁺] / [OH⁻] Converter")
        print("2. Strong Acid / Base pH")
        print("3. Weak Acid / Base pH (with quadratic fallback)")
        print("4. Ka / Kb / pKa / pKb Converter")
        print("5. Buffer pH — Henderson-Hasselbalch")
        print("6. Acid / Base Identifier")
        print("7. Titration Calculator")
        print("0. Return to Main Menu")

        choice = input("Select an option (0-7): ").strip()

        if choice == "1":
            menu_converter()
        elif choice == "2":
            menu_strong()
        elif choice == "3":
            menu_weak()
        elif choice == "4":
            menu_Ka_Kb()
        elif choice == "5":
            menu_buffer()
        elif choice == "6":
            menu_identifier()
        elif choice == "7":
            menu_titration()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")
