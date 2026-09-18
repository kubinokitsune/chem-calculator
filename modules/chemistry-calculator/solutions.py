"""
solutions.py — concentration, dilution and standard solutions (IB S1.4)

Volumes are handled in cm³ or dm³ (IB uses both), concentrations in
mol dm⁻³ or g dm⁻³.  1 dm³ = 1000 cm³ = 1 L.
"""

import math

VOLUME_UNITS = {"dm3": 1.0, "cm3": 1e-3, "L": 1.0, "mL": 1e-3, "m3": 1000.0}
_VOLUME_ALIASES = {
    "dm3": "dm3", "dm^3": "dm3", "dm³": "dm3", "l": "L", "litre": "L", "liter": "L",
    "cm3": "cm3", "cm^3": "cm3", "cm³": "cm3", "ml": "mL", "m3": "m3", "m^3": "m3", "m³": "m3",
}


def volume_to_dm3(value, unit="dm3"):
    """Convert a volume to dm³ (= litres)."""
    key = _VOLUME_ALIASES.get(str(unit).strip().lower())
    if key is None:
        raise ValueError(f"Unknown volume unit '{unit}'. Use dm3, cm3, mL, L or m3.")
    v = float(value)
    if not math.isfinite(v) or v <= 0:
        raise ValueError("Volume must be greater than zero.")
    return v * VOLUME_UNITS[key]


def volume_from_dm3(value, unit="dm3"):
    key = _VOLUME_ALIASES.get(str(unit).strip().lower())
    if key is None:
        raise ValueError(f"Unknown volume unit '{unit}'. Use dm3, cm3, mL, L or m3.")
    return value / VOLUME_UNITS[key]


def _positive(name, value):
    v = float(value)
    if not math.isfinite(v) or v <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return v


# ── c = n / V ────────────────────────────────────────────────────────────────

def concentration(moles, volume_dm3):
    """c = n / V  (mol dm⁻³)."""
    return _positive("Moles", moles) / _positive("Volume", volume_dm3)


def moles_from_concentration(conc, volume_dm3):
    """n = c × V  (mol)."""
    return _positive("Concentration", conc) * _positive("Volume", volume_dm3)


def volume_from_concentration(moles, conc):
    """V = n / c  (dm³)."""
    return _positive("Moles", moles) / _positive("Concentration", conc)


# ── mass concentration and ppm ───────────────────────────────────────────────

def mass_concentration(mass_g, volume_dm3):
    """Mass concentration = mass / volume  (g dm⁻³)."""
    return _positive("Mass", mass_g) / _positive("Volume", volume_dm3)


def concentration_from_mass(mass_g, molar_mass, volume_dm3):
    """c = (mass / M) / V  (mol dm⁻³)."""
    return _positive("Mass", mass_g) / _positive("Molar mass", molar_mass) / _positive("Volume", volume_dm3)


def mass_for_solution(conc, volume_dm3, molar_mass):
    """Mass of solute needed to make a standard solution: m = c × V × M  (g)."""
    return (_positive("Concentration", conc) * _positive("Volume", volume_dm3)
            * _positive("Molar mass", molar_mass))


def g_per_dm3_to_mol_per_dm3(g_per_dm3, molar_mass):
    return _positive("Mass concentration", g_per_dm3) / _positive("Molar mass", molar_mass)


def mol_per_dm3_to_g_per_dm3(mol_per_dm3, molar_mass):
    return _positive("Concentration", mol_per_dm3) * _positive("Molar mass", molar_mass)


def ppm_from_mass(solute_mg, solution_dm3):
    """ppm for a dilute aqueous solution: mg of solute per dm³ of solution
    (1 dm³ of water ≈ 1 kg, so mg dm⁻³ ≈ mg kg⁻¹ = ppm)."""
    return _positive("Solute mass", solute_mg) / _positive("Volume", solution_dm3)


def mass_from_ppm(ppm, solution_dm3):
    """Milligrams of solute in a given volume at a given ppm."""
    return _positive("ppm", ppm) * _positive("Volume", solution_dm3)


# ── Dilution: c₁V₁ = c₂V₂ ────────────────────────────────────────────────────

def dilution_solve(solve, c1=None, V1=None, c2=None, V2=None):
    """
    c₁V₁ = c₂V₂ — give three of them and name the fourth ('c1', 'V1', 'c2', 'V2').
    Volumes must already be in the same unit; the answer comes back in that unit.
    """
    if solve not in ("c1", "V1", "c2", "V2"):
        raise ValueError("solve must be 'c1', 'V1', 'c2' or 'V2'.")
    vals = {"c1": c1, "V1": V1, "c2": c2, "V2": V2}
    for key, v in vals.items():
        if key == solve:
            continue
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"Missing value: {key}")
        vals[key] = _positive(key, v)
    if solve == "c1":
        return vals["c2"] * vals["V2"] / vals["V1"]
    if solve == "V1":
        return vals["c2"] * vals["V2"] / vals["c1"]
    if solve == "c2":
        return vals["c1"] * vals["V1"] / vals["V2"]
    return vals["c1"] * vals["V1"] / vals["c2"]


def dilution_factor(c1, c2):
    """How many times the solution is diluted (stock ÷ diluted)."""
    c1, c2 = _positive("Stock concentration", c1), _positive("Diluted concentration", c2)
    if c2 > c1:
        raise ValueError("The diluted solution cannot be more concentrated than the stock.")
    return c1 / c2


def water_to_add(V1, V2):
    """Volume of water added when V1 is made up to V2 (same units)."""
    V1, V2 = _positive("V1", V1), _positive("V2", V2)
    if V2 < V1:
        raise ValueError("The final volume must be larger than the starting volume.")
    return V2 - V1


# ── Menu ─────────────────────────────────────────────────────────────────────

def _get_float(prompt, label=None, positive=True):
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


def _get_volume(prompt):
    v = _get_float(prompt + " value: ", "volume")
    unit = input("  Unit [dm3/cm3/mL/L/m3] (Enter = cm3): ").strip() or "cm3"
    try:
        return volume_to_dm3(v, unit), unit
    except ValueError as e:
        print(f"  [ERROR] {e}")
        return None, None


def solutions_menu():
    while True:
        print("\n--- Solutions: Concentration & Dilution ---")
        print("1. Concentration from moles and volume  (c = n/V)")
        print("2. Moles from concentration and volume  (n = cV)")
        print("3. Volume from moles and concentration  (V = n/c)")
        print("4. Concentration from a mass of solute")
        print("5. Mass needed to make a standard solution")
        print("6. g/dm³ ↔ mol/dm³")
        print("7. Dilution (c₁V₁ = c₂V₂)")
        print("8. ppm (dilute aqueous solution)")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-8): ").strip()
        try:
            if choice == "1":
                n = _get_float("Moles (mol): ")
                V, _ = _get_volume("Volume")
                if V is None:
                    continue
                print(f"  c = {concentration(n, V):.4g} mol/dm³")
            elif choice == "2":
                c = _get_float("Concentration (mol/dm³): ")
                V, _ = _get_volume("Volume")
                if V is None:
                    continue
                print(f"  n = {moles_from_concentration(c, V):.4g} mol")
            elif choice == "3":
                n = _get_float("Moles (mol): ")
                c = _get_float("Concentration (mol/dm³): ")
                V = volume_from_concentration(n, c)
                print(f"  V = {V:.4g} dm³ = {V * 1000:.4g} cm³")
            elif choice == "4":
                m = _get_float("Mass of solute (g): ")
                M = _get_float("Molar mass (g/mol): ")
                V, _ = _get_volume("Volume")
                if V is None:
                    continue
                print(f"  c = {concentration_from_mass(m, M, V):.4g} mol/dm³")
            elif choice == "5":
                c = _get_float("Concentration wanted (mol/dm³): ")
                V, _ = _get_volume("Volume of solution")
                if V is None:
                    continue
                M = _get_float("Molar mass (g/mol): ")
                print(f"  Weigh out {mass_for_solution(c, V, M):.4g} g and make up to the mark.")
            elif choice == "6":
                M = _get_float("Molar mass (g/mol): ")
                which = input("Convert (g) g/dm³ → mol/dm³ or (m) mol/dm³ → g/dm³? ").strip().lower()
                if which.startswith("g"):
                    v = _get_float("Mass concentration (g/dm³): ")
                    print(f"  c = {g_per_dm3_to_mol_per_dm3(v, M):.4g} mol/dm³")
                else:
                    v = _get_float("Concentration (mol/dm³): ")
                    print(f"  = {mol_per_dm3_to_g_per_dm3(v, M):.4g} g/dm³")
            elif choice == "7":
                print("  Leave the unknown out: solve for c1, V1, c2 or V2.")
                target = input("  Solve for [c1/V1/c2/V2]: ").strip()
                if target not in ("c1", "V1", "c2", "V2"):
                    print("  [ERROR] Choose c1, V1, c2 or V2.")
                    continue
                vals = {}
                for key, prompt in (("c1", "Stock concentration c₁ (mol/dm³): "),
                                    ("V1", "Stock volume V₁ (cm³): "),
                                    ("c2", "Diluted concentration c₂ (mol/dm³): "),
                                    ("V2", "Final volume V₂ (cm³): ")):
                    if key != target:
                        vals[key] = _get_float(prompt)
                result = dilution_solve(target, **vals)
                unit = "mol/dm³" if target.startswith("c") else "cm³"
                print(f"  {target} = {result:.4g} {unit}")
            elif choice == "8":
                mg = _get_float("Mass of solute (mg): ")
                V, _ = _get_volume("Volume of solution")
                if V is None:
                    continue
                print(f"  {ppm_from_mass(mg, V):.4g} ppm")
            elif choice in ("0", "exit"):
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError as e:
            print(f"  [ERROR] {e}")
