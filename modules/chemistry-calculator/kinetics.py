"""
kinetics.py — Chemical Kinetics module
Covers: rate law from initial rates, Arrhenius equation, half-life (1st order),
        integrated rate laws (0/1/2 order), rate constant units.
"""

import math
from constants import R

# ── Pure calculation functions ─────────────────────────────────────────────────

def celsius_to_kelvin(T_C: float) -> float:
    return T_C + 273.15


def k_units(order: int) -> str:
    """Return the correct units string for k given overall reaction order."""
    units = {
        0: "mol·L⁻¹·s⁻¹",
        1: "s⁻¹",
        2: "L·mol⁻¹·s⁻¹",
        3: "L²·mol⁻²·s⁻¹",
    }
    if order in units:
        return units[order]
    # General form: L^(n-1) · mol^(1-n) · s⁻¹
    n = order
    return f"L^{n-1}·mol^{1-n}·s⁻¹"


def determine_order(c1: float, c2: float, r1: float, r2: float) -> float:
    """Compute reaction order for one reactant from two experiments.
    order = log(r2/r1) / log(c2/c1)
    Raises ValueError if concentrations are equal (can't determine order).
    """
    if c1 <= 0 or c2 <= 0 or r1 <= 0 or r2 <= 0:
        raise ValueError("Concentrations and rates must be positive.")
    if math.isclose(c1, c2, rel_tol=1e-9):
        raise ValueError(
            "The two concentrations are equal — choose experiments where "
            "this reactant's concentration differs."
        )
    return math.log(r2 / r1) / math.log(c2 / c1)


def rate_constant_from_experiment(rate: float, concentrations: list, orders: list) -> float:
    """k = rate / Π[conc_i ^ order_i]"""
    denom = 1.0
    for c, n in zip(concentrations, orders):
        if c <= 0:
            raise ValueError("Concentrations must be positive.")
        denom *= c ** n
    if denom == 0:
        raise ZeroDivisionError("Denominator is zero — check concentrations and orders.")
    return rate / denom


# Arrhenius ────────────────────────────────────────────────────────────────────

def arrhenius_Ea(k1: float, T1_K: float, k2: float, T2_K: float) -> float:
    """Activation energy (J/mol) from k at two temperatures.
    ln(k2/k1) = −Ea/R × (1/T2 − 1/T1)
    """
    if k1 <= 0 or k2 <= 0:
        raise ValueError("Rate constants must be positive.")
    if T1_K <= 0 or T2_K <= 0:
        raise ValueError("Temperatures must be positive (K).")
    if math.isclose(T1_K, T2_K, rel_tol=1e-9):
        raise ValueError("T1 and T2 must differ to calculate Ea.")
    inv_diff = 1 / T2_K - 1 / T1_K
    if inv_diff == 0:
        raise ZeroDivisionError("1/T2 − 1/T1 is zero.")
    return -R * math.log(k2 / k1) / inv_diff  # J/mol


def arrhenius_k2(k1: float, T1_K: float, T2_K: float, Ea_J: float) -> float:
    """Rate constant at T2 given k1 at T1 and activation energy Ea (J/mol)."""
    if k1 <= 0:
        raise ValueError("k1 must be positive.")
    if T1_K <= 0 or T2_K <= 0:
        raise ValueError("Temperatures must be positive (K).")
    exponent = -Ea_J / R * (1 / T2_K - 1 / T1_K)
    return k1 * math.exp(exponent)


# Half-life (first order only) ─────────────────────────────────────────────────

def half_life_from_k(k: float) -> float:
    """t½ = ln(2) / k   (first order)"""
    if k <= 0:
        raise ValueError("k must be positive.")
    return math.log(2) / k


def k_from_half_life(t_half: float) -> float:
    """k = ln(2) / t½   (first order)"""
    if t_half <= 0:
        raise ValueError("t½ must be positive.")
    return math.log(2) / t_half


# Integrated Rate Laws ─────────────────────────────────────────────────────────

def irl_concentration(order: int, A0: float, k: float, t: float) -> float:
    """[A] at time t.
    0th: [A]t = [A]0 − kt
    1st: [A]t = [A]0 × e^(−kt)
    2nd: 1/[A]t = 1/[A]0 + kt  →  [A]t = 1 / (1/[A]0 + kt)
    """
    if A0 <= 0:
        raise ValueError("[A]₀ must be positive.")
    if k <= 0:
        raise ValueError("k must be positive.")
    if t < 0:
        raise ValueError("Time cannot be negative.")

    if order == 0:
        At = A0 - k * t
        if At < 0:
            raise ValueError(
                f"[A]t = {At:.6f} < 0 — the reactant is fully consumed before t = {t} s."
            )
        return At
    elif order == 1:
        return A0 * math.exp(-k * t)
    elif order == 2:
        denom = 1 / A0 + k * t
        if denom == 0:
            raise ZeroDivisionError("1/[A]0 + kt = 0 — invalid.")
        return 1 / denom
    else:
        raise ValueError(f"Order {order} not supported (0, 1, or 2 only).")


def irl_time(order: int, A0: float, At: float, k: float) -> float:
    """Time elapsed to go from [A]₀ to [A]t.
    0th: t = ([A]0 − [A]t) / k
    1st: t = ln([A]0 / [A]t) / k
    2nd: t = (1/[A]t − 1/[A]0) / k
    """
    if A0 <= 0 or At <= 0:
        raise ValueError("Concentrations must be positive.")
    if At > A0:
        raise ValueError("[A]t cannot be greater than [A]₀.")
    if k <= 0:
        raise ValueError("k must be positive.")

    if order == 0:
        return (A0 - At) / k
    elif order == 1:
        return math.log(A0 / At) / k
    elif order == 2:
        return (1 / At - 1 / A0) / k
    else:
        raise ValueError(f"Order {order} not supported (0, 1, or 2 only).")


# ── Input helpers ──────────────────────────────────────────────────────────────

def _get_float(prompt: str, positive: bool = False) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            val = float(raw)
            if positive and val <= 0:
                print("  [ERROR] Value must be greater than zero.")
            else:
                return val
        except ValueError:
            print("  [ERROR] Enter a numeric value.")


def _get_int(prompt: str, minimum: int = 0) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val < minimum:
                print(f"  [ERROR] Value must be ≥ {minimum}.")
            else:
                return val
        except ValueError:
            print("  [ERROR] Enter a whole number.")


def _get_order(prompt: str = "  Reaction order (0, 1, or 2): ") -> int:
    while True:
        val = _get_int(prompt, minimum=0)
        if val in (0, 1, 2):
            return val
        print("  [ERROR] Only orders 0, 1, and 2 are supported.")


def _get_temp_K(prompt: str = "  Temperature (°C): ") -> float:
    T_C = _get_float(prompt)
    T_K = celsius_to_kelvin(T_C)
    print(f"  → {T_C} °C = {T_K:.2f} K")
    return T_K


# ── Sub-menus ──────────────────────────────────────────────────────────────────

def menu_rate_law():
    print("\n=== Rate Law from Initial Rates ===")
    print("  You will enter experimental data (concentrations + rates).")
    print("  The solver finds the order for each reactant and calculates k.\n")

    n_reactants = _get_int("  Number of reactants: ", minimum=1)
    reactant_names = []
    for i in range(n_reactants):
        name = input(f"  Name of reactant {i+1} (e.g. A, B, NO): ").strip() or f"R{i+1}"
        reactant_names.append(name)

    n_exp = _get_int("  Number of experiments: ", minimum=2)
    print(f"\n  Enter data for {n_exp} experiments.")
    print(f"  Columns: {', '.join(f'[{r}] (mol/L)' for r in reactant_names)}, Rate (mol/L·s)\n")

    experiments = []
    for i in range(n_exp):
        print(f"  Experiment {i+1}:")
        concs = []
        for r in reactant_names:
            c = _get_float(f"    [{r}]: ", positive=True)
            concs.append(c)
        rate = _get_float("    Rate: ", positive=True)
        experiments.append({"concs": concs, "rate": rate})

    # Determine order for each reactant
    orders = []
    print("\n  ── Determining orders ──────────────────────────────")
    for ri, rname in enumerate(reactant_names):
        # Find a pair of experiments where this reactant differs and others are as close as possible
        best_pair = None
        best_ratio = None
        for i in range(n_exp):
            for j in range(i + 1, n_exp):
                c1 = experiments[i]["concs"][ri]
                c2 = experiments[j]["concs"][ri]
                if math.isclose(c1, c2, rel_tol=1e-6):
                    continue  # concentrations equal — can't use
                # Check how well other reactants are controlled (prefer pairs where others match)
                others_match = all(
                    math.isclose(experiments[i]["concs"][k], experiments[j]["concs"][k], rel_tol=0.01)
                    for k in range(n_reactants) if k != ri
                )
                if others_match or best_pair is None:
                    ratio = abs(math.log(c2 / c1))
                    if best_pair is None or others_match or ratio > best_ratio:
                        best_pair = (i, j)
                        best_ratio = ratio

        if best_pair is None:
            print(f"  [WARN] Could not find varying experiments for [{rname}] — assuming order 0.")
            orders.append(0)
            continue

        i, j = best_pair
        c1 = experiments[i]["concs"][ri]
        c2 = experiments[j]["concs"][ri]
        r1 = experiments[i]["rate"]
        r2 = experiments[j]["rate"]

        try:
            raw_order = determine_order(c1, c2, r1, r2)
        except ValueError as e:
            print(f"  [WARN] {e} — assuming order 0 for [{rname}].")
            orders.append(0)
            continue

        rounded = round(raw_order)
        print(f"  [{rname}]: experiments {i+1} & {j+1}  →  "
              f"log({r2}/{r1}) / log({c2}/{c1}) = {raw_order:.4f}  →  order = {rounded}")
        orders.append(rounded)

    overall_order = sum(orders)

    # Calculate k from every experiment and average
    k_values = []
    for i, exp in enumerate(experiments):
        try:
            k = rate_constant_from_experiment(exp["rate"], exp["concs"], orders)
            k_values.append(k)
        except (ValueError, ZeroDivisionError) as e:
            print(f"  [WARN] Experiment {i+1}: {e}")

    if not k_values:
        print("  [ERROR] Could not compute k from any experiment.")
        return

    k_avg = sum(k_values) / len(k_values)
    units = k_units(overall_order)

    print("\n  ── Results ──────────────────────────────────────────")
    rate_terms = " × ".join(
        f"[{r}]^{o}" if o != 1 else f"[{r}]"
        for r, o in zip(reactant_names, orders)
    )
    print(f"  Rate law   : rate = k × {rate_terms}")
    for r, o in zip(reactant_names, orders):
        print(f"  Order in [{r}] : {o}")
    print(f"  Overall order : {overall_order}")
    print(f"  k values per experiment: {[f'{v:.4e}' for v in k_values]}")
    print(f"  Average k  : {k_avg:.4e} {units}")
    print("  ─────────────────────────────────────────────────────")


def menu_arrhenius():
    print("\n=== Arrhenius Equation ===")
    print("  k = A·e^(−Ea/RT)")
    print("\n  Solve for:")
    print("  [1] Ea  — given k at two temperatures")
    print("  [2] k₂  — given Ea, k₁, and a new temperature")

    ch = input("  Choice (1/2): ").strip()

    try:
        if ch == "1":
            print("\n  Enter k and temperature for experiment 1:")
            k1 = _get_float("  k₁: ", positive=True)
            T1 = _get_temp_K("  T₁ (°C): ")
            print("\n  Enter k and temperature for experiment 2:")
            k2 = _get_float("  k₂: ", positive=True)
            T2 = _get_temp_K("  T₂ (°C): ")

            Ea_J  = arrhenius_Ea(k1, T1, k2, T2)
            Ea_kJ = Ea_J / 1000

            print(f"\n  ln(k₂/k₁) = −Ea/R × (1/T₂ − 1/T₁)")
            print(f"  ln({k2}/{k1}) = −Ea / {R} × (1/{T2:.2f} − 1/{T1:.2f})")
            print(f"\n  Ea = {Ea_J:.2f} J/mol  =  {Ea_kJ:.4f} kJ/mol")

        elif ch == "2":
            print("\n  Enter reference rate constant and temperature:")
            k1    = _get_float("  k₁: ", positive=True)
            T1    = _get_temp_K("  T₁ (°C): ")
            Ea_kJ = _get_float("  Ea (kJ/mol, >0): ", positive=True)
            Ea_J  = Ea_kJ * 1000
            print("\n  Enter the new temperature:")
            T2    = _get_temp_K("  T₂ (°C): ")

            k2 = arrhenius_k2(k1, T1, T2, Ea_J)
            print(f"\n  k₂ = k₁ × exp(−Ea/R × (1/T₂ − 1/T₁))")
            print(f"  k₂ = {k1} × exp(−{Ea_J}/{R} × (1/{T2:.2f} − 1/{T1:.2f}))")
            print(f"  k₂ = {k2:.6e}")

        else:
            print("  Invalid choice.")

    except (ValueError, ZeroDivisionError) as e:
        print(f"  [ERROR] {e}")


def menu_half_life():
    print("\n=== Half-Life (First Order) ===")
    print("  t½ = ln(2) / k   →   k = ln(2) / t½")
    print("\n  Solve for:")
    print("  [1] t½  given k")
    print("  [2] k   given t½")

    ch = input("  Choice (1/2): ").strip()

    try:
        if ch == "1":
            k   = _get_float("  Rate constant k (s⁻¹, >0): ", positive=True)
            t_h = half_life_from_k(k)
            print(f"\n  t½ = ln(2) / {k} = {math.log(2):.6f} / {k}")
            print(f"  t½ = {t_h:.6f} s")
            if t_h >= 3600:
                print(f"     = {t_h/3600:.4f} h")
            elif t_h >= 60:
                print(f"     = {t_h/60:.4f} min")

        elif ch == "2":
            t_h = _get_float("  Half-life t½ (s, >0): ", positive=True)
            k   = k_from_half_life(t_h)
            print(f"\n  k = ln(2) / {t_h} = {math.log(2):.6f} / {t_h}")
            print(f"  k = {k:.6e} s⁻¹")

        else:
            print("  Invalid choice.")

    except ValueError as e:
        print(f"  [ERROR] {e}")


def menu_integrated_rate_law():
    print("\n=== Integrated Rate Laws ===")
    print("  0th order:  [A]t = [A]₀ − kt")
    print("  1st order:  ln[A]t = ln[A]₀ − kt")
    print("  2nd order:  1/[A]t = 1/[A]₀ + kt")
    print("\n  Solve for:")
    print("  [1] Concentration [A]t  at time t")
    print("  [2] Time t  to reach concentration [A]t")

    ch = input("  Choice (1/2): ").strip()

    order = _get_order()

    try:
        if ch == "1":
            A0 = _get_float("  Initial concentration [A]₀ (mol/L, >0): ", positive=True)
            k  = _get_float("  Rate constant k (>0): ", positive=True)
            t  = _get_float("  Time t (s, ≥0): ")
            if t < 0:
                print("  [ERROR] Time cannot be negative.")
                return
            At = irl_concentration(order, A0, k, t)
            _print_irl_result(order, A0, At, k, t, solved_for="At")

        elif ch == "2":
            A0 = _get_float("  Initial concentration [A]₀ (mol/L, >0): ", positive=True)
            At = _get_float("  Final concentration [A]t (mol/L, >0, ≤ [A]₀): ", positive=True)
            k  = _get_float("  Rate constant k (>0): ", positive=True)
            t  = irl_time(order, A0, At, k)
            _print_irl_result(order, A0, At, k, t, solved_for="t")

        else:
            print("  Invalid choice.")

    except (ValueError, ZeroDivisionError) as e:
        print(f"  [ERROR] {e}")


def _print_irl_result(order, A0, At, k, t, solved_for):
    print("\n  ── Results ─────────────────────────────────────")
    if order == 0:
        print(f"  [A]t = [A]₀ − kt = {A0} − {k}×{t} = {At:.6f} mol/L")
    elif order == 1:
        print(f"  [A]t = [A]₀ × e^(−kt) = {A0} × e^(−{k}×{t}) = {At:.6f} mol/L")
        pct_remaining = (At / A0) * 100
        print(f"  {pct_remaining:.2f}% of [A]₀ remains")
    elif order == 2:
        print(f"  1/[A]t = 1/[A]₀ + kt = 1/{A0} + {k}×{t} = {1/At:.6f}")
        print(f"  [A]t = {At:.6f} mol/L")
    if solved_for == "t":
        print(f"  Time elapsed : {t:.4f} s")
        if t >= 3600:
            print(f"               = {t/3600:.4f} h")
        elif t >= 60:
            print(f"               = {t/60:.4f} min")
    print("  ────────────────────────────────────────────────")


def menu_k_units():
    print("\n=== Rate Constant Units ===")
    order = _get_int("  Overall reaction order: ", minimum=0)
    units = k_units(order)
    print(f"\n  For a {order}-order reaction:")
    print(f"  Units of k = {units}")
    print()
    print("  Reference:")
    print("  Order 0 → mol·L⁻¹·s⁻¹")
    print("  Order 1 → s⁻¹")
    print("  Order 2 → L·mol⁻¹·s⁻¹")
    print("  Order 3 → L²·mol⁻²·s⁻¹")


# ── Main menu ──────────────────────────────────────────────────────────────────

def kinetics_menu():
    while True:
        print("\n=== Kinetics Calculator ===")
        print("1. Rate Law from Initial Rates")
        print("2. Arrhenius Equation  (Ea / k at new T)")
        print("3. Half-Life  (first order only)")
        print("4. Integrated Rate Laws  (0th / 1st / 2nd order)")
        print("5. Rate Constant Units")
        print("0. Back to main menu")

        choice = input("Select (0-5): ").strip()

        if choice == "1":
            menu_rate_law()
        elif choice == "2":
            menu_arrhenius()
        elif choice == "3":
            menu_half_life()
        elif choice == "4":
            menu_integrated_rate_law()
        elif choice == "5":
            menu_k_units()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
