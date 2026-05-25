
# gas_laws.py

R = 0.08206  # L·atm / (mol·K)
MOLAR_VOLUME_STP = 22.4  # L/mol at STP (0°C, 1 atm)


# ── Ideal Gas Law: PV = nRT ──────────────────────────────────────────────────

def ideal_gas_find_P(n, V, T):
    return (n * R * T) / V

def ideal_gas_find_V(n, T, P):
    return (n * R * T) / P

def ideal_gas_find_n(P, V, T):
    return (P * V) / (R * T)

def ideal_gas_find_T(P, V, n):
    return (P * V) / (n * R)


# ── Combined Gas Law: P1V1/T1 = P2V2/T2 ─────────────────────────────────────

def combined_gas_find_P2(P1, V1, T1, V2, T2):
    return (P1 * V1 * T2) / (T1 * V2)

def combined_gas_find_V2(P1, V1, T1, P2, T2):
    return (P1 * V1 * T2) / (T1 * P2)

def combined_gas_find_T2(P1, V1, T1, P2, V2):
    return (P2 * V2 * T1) / (P1 * V1)


# ── Molar Volume ─────────────────────────────────────────────────────────────

def moles_to_volume_stp(moles):
    return moles * MOLAR_VOLUME_STP

def volume_to_moles_stp(volume):
    return volume / MOLAR_VOLUME_STP

def molar_volume_nonstandard(T, P):
    """Returns molar volume (L/mol) at any T (K) and P (atm) via ideal gas law."""
    return R * T / P


# ── Graham's Law of Effusion: rate1/rate2 = sqrt(M2/M1) ────────────────────

def graham_rate_ratio(M1, M2):
    """Returns rate1/rate2 given molar masses M1 and M2."""
    return (M2 / M1) ** 0.5

def graham_find_M2(M1, rate_ratio):
    """Finds M2 given M1 and the ratio rate1/rate2."""
    return M1 * (rate_ratio ** 2)

def graham_find_M1(M2, rate_ratio):
    """Finds M1 given M2 and the ratio rate1/rate2."""
    return M2 / (rate_ratio ** 2)


# ── Dalton's Law of Partial Pressures: P_total = sum(P_i) ───────────────────

def dalton_total_pressure(partial_pressures):
    return sum(partial_pressures)

def dalton_partial_pressure(P_total, mole_fraction):
    return P_total * mole_fraction

def dalton_mole_fraction(moles_i, total_moles):
    return moles_i / total_moles


# ── Menu helpers ─────────────────────────────────────────────────────────────

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


def _get_temp_K(prompt):
    """Get a temperature in K with absolute-zero check."""
    while True:
        val = _get_float(prompt, "temperature (K)")
        if val <= 0:
            print("  [ERROR] Temperature must be above absolute zero (> 0 K).")
            continue
        return val


def ideal_gas_menu():
    print("\n-- Ideal Gas Law (PV = nRT) --")
    print("Solve for:")
    print("1. Pressure (P)")
    print("2. Volume (V)")
    print("3. Moles (n)")
    print("4. Temperature (T)")
    choice = input("Select (1-4): ").strip()

    try:
        if choice == "1":
            n = _get_float("Moles (mol): ", "moles", positive=True)
            V = _get_float("Volume (L): ", "volume", positive=True)
            T = _get_temp_K("Temperature (K): ")
            print(f"Pressure = {ideal_gas_find_P(n, V, T):.4f} atm")
        elif choice == "2":
            n = _get_float("Moles (mol): ", "moles", positive=True)
            T = _get_temp_K("Temperature (K): ")
            P = _get_float("Pressure (atm): ", "pressure", positive=True)
            print(f"Volume = {ideal_gas_find_V(n, T, P):.4f} L")
        elif choice == "3":
            P = _get_float("Pressure (atm): ", "pressure", positive=True)
            V = _get_float("Volume (L): ", "volume", positive=True)
            T = _get_temp_K("Temperature (K): ")
            print(f"Moles = {ideal_gas_find_n(P, V, T):.4f} mol")
        elif choice == "4":
            P = _get_float("Pressure (atm): ", "pressure", positive=True)
            V = _get_float("Volume (L): ", "volume", positive=True)
            n = _get_float("Moles (mol): ", "moles", positive=True)
            print(f"Temperature = {ideal_gas_find_T(P, V, n):.4f} K")
        else:
            print("Invalid choice.")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def combined_gas_menu():
    print("\n-- Combined Gas Law (P1V1/T1 = P2V2/T2) --")
    print("Solve for:")
    print("1. P2")
    print("2. V2")
    print("3. T2")
    choice = input("Select (1-3): ").strip()

    try:
        if choice == "1":
            P1 = _get_float("P1 (atm): ", "P1", positive=True)
            V1 = _get_float("V1 (L): ",  "V1", positive=True)
            T1 = _get_temp_K("T1 (K): ")
            V2 = _get_float("V2 (L): ",  "V2", positive=True)
            T2 = _get_temp_K("T2 (K): ")
            print(f"P2 = {combined_gas_find_P2(P1, V1, T1, V2, T2):.4f} atm")
        elif choice == "2":
            P1 = _get_float("P1 (atm): ", "P1", positive=True)
            V1 = _get_float("V1 (L): ",  "V1", positive=True)
            T1 = _get_temp_K("T1 (K): ")
            P2 = _get_float("P2 (atm): ", "P2", positive=True)
            T2 = _get_temp_K("T2 (K): ")
            print(f"V2 = {combined_gas_find_V2(P1, V1, T1, P2, T2):.4f} L")
        elif choice == "3":
            P1 = _get_float("P1 (atm): ", "P1", positive=True)
            V1 = _get_float("V1 (L): ",  "V1", positive=True)
            T1 = _get_temp_K("T1 (K): ")
            P2 = _get_float("P2 (atm): ", "P2", positive=True)
            V2 = _get_float("V2 (L): ",  "V2", positive=True)
            print(f"T2 = {combined_gas_find_T2(P1, V1, T1, P2, V2):.4f} K")
        else:
            print("Invalid choice.")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def molar_volume_menu():
    print("\n-- Molar Volume --")
    print("1. Moles → Volume at STP (22.4 L/mol)")
    print("2. Volume at STP → Moles")
    print("3. Molar volume at non-standard T and P")
    choice = input("Select (1-3): ").strip()

    try:
        if choice == "1":
            n = _get_float("Moles (mol): ", "moles", positive=True)
            print(f"Volume at STP = {moles_to_volume_stp(n):.4f} L")
        elif choice == "2":
            V = _get_float("Volume at STP (L): ", "volume", positive=True)
            print(f"Moles = {volume_to_moles_stp(V):.4f} mol")
        elif choice == "3":
            T = _get_temp_K("Temperature (K): ")
            P = _get_float("Pressure (atm): ", "pressure", positive=True)
            print(f"Molar volume = {molar_volume_nonstandard(T, P):.4f} L/mol")
        else:
            print("Invalid choice.")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def graham_menu():
    print("\n-- Graham's Law of Effusion --")
    print("  rate₁/rate₂ = √(M₂/M₁)")
    print("1. Find rate ratio (rate1/rate2) given M1 and M2")
    print("2. Find M2 given M1 and rate ratio")
    print("3. Find M1 given M2 and rate ratio")
    choice = input("Select (1-3): ").strip()

    try:
        if choice == "1":
            M1 = _get_float("Molar mass of gas 1 (g/mol): ", "molar mass M1", positive=True)
            M2 = _get_float("Molar mass of gas 2 (g/mol): ", "molar mass M2", positive=True)
            print(f"rate1/rate2 = {graham_rate_ratio(M1, M2):.4f}")
        elif choice == "2":
            M1    = _get_float("Molar mass of gas 1 (g/mol): ", "molar mass M1", positive=True)
            ratio = _get_float("rate1/rate2: ", "rate ratio", positive=True)
            print(f"M2 = {graham_find_M2(M1, ratio):.4f} g/mol")
        elif choice == "3":
            M2    = _get_float("Molar mass of gas 2 (g/mol): ", "molar mass M2", positive=True)
            ratio = _get_float("rate1/rate2: ", "rate ratio", positive=True)
            print(f"M1 = {graham_find_M1(M2, ratio):.4f} g/mol")
        else:
            print("Invalid choice.")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def dalton_menu():
    print("\n-- Dalton's Law of Partial Pressures --")
    print("1. Total pressure from partial pressures")
    print("2. Partial pressure from mole fraction and total pressure")
    print("3. Mole fraction of a gas")
    choice = input("Select (1-3): ").strip()

    try:
        if choice == "1":
            n = int(_get_float("Number of gases: ", "number of gases", positive=True))
            pressures = [_get_float(f"Partial pressure of gas {i} (atm): ", f"pressure {i}", positive=True)
                         for i in range(1, n + 1)]
            print(f"Total pressure = {dalton_total_pressure(pressures):.4f} atm")
        elif choice == "2":
            P_total = _get_float("Total pressure (atm): ", "total pressure", positive=True)
            x = _get_float("Mole fraction of gas (0-1): ", "mole fraction")
            if not 0 <= x <= 1:
                print("  [ERROR] Mole fraction must be between 0 and 1.")
                return
            print(f"Partial pressure = {dalton_partial_pressure(P_total, x):.4f} atm")
        elif choice == "3":
            n_i     = _get_float("Moles of gas i: ", "moles of gas i", positive=True)
            n_total = _get_float("Total moles: ", "total moles", positive=True)
            print(f"Mole fraction = {dalton_mole_fraction(n_i, n_total):.4f}")
        else:
            print("Invalid choice.")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def gas_laws_menu():
    while True:
        print("\n=== Gas Laws Calculator ===")
        print("1. Ideal Gas Law (PV = nRT)")
        print("2. Combined Gas Law (P1V1/T1 = P2V2/T2)")
        print("3. Molar Volume")
        print("4. Graham's Law of Effusion")
        print("5. Dalton's Law of Partial Pressures")
        print("0. Return to Main Menu")

        choice = input("Select an option (0-5): ").strip()

        if choice == "1":
            ideal_gas_menu()
        elif choice == "2":
            combined_gas_menu()
        elif choice == "3":
            molar_volume_menu()
        elif choice == "4":
            graham_menu()
        elif choice == "5":
            dalton_menu()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")
