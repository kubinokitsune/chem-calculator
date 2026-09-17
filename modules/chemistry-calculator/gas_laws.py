
# gas_laws.py

import math

R = 0.08206  # L·atm / (mol·K)
from constants import MOLAR_VOLUME_STP  # 22.7 L/mol at STP (0 °C, 100 kPa), same as mole_conversions


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


# ── Units (IB uses kPa / Pa and dm³ / m³) ────────────────────────────────────
# Everything is converted to SI (Pa, m³, K) and solved with R = 8.314 J/(mol·K).

from constants import R as R_SI

PRESSURE_UNITS = {"atm": 101325.0, "kPa": 1000.0, "Pa": 1.0, "bar": 1.0e5,
                  "mmHg": 101325.0 / 760, "torr": 101325.0 / 760}
VOLUME_UNITS = {"L": 1e-3, "dm3": 1e-3, "mL": 1e-6, "cm3": 1e-6, "m3": 1.0}
TEMPERATURE_UNITS = ("K", "C")

_UNIT_ALIASES = {
    "atm": "atm", "kpa": "kPa", "pa": "Pa", "bar": "bar", "mmhg": "mmHg", "torr": "torr",
    "l": "L", "dm3": "dm3", "dm^3": "dm3", "dm³": "dm3",
    "ml": "mL", "cm3": "cm3", "cm^3": "cm3", "cm³": "cm3",
    "m3": "m3", "m^3": "m3", "m³": "m3",
    "k": "K", "c": "C", "°c": "C", "degc": "C",
}


def _unit(u, allowed, kind):
    key = _UNIT_ALIASES.get(str(u).strip().lower())
    if key not in allowed:
        raise ValueError(f"Unknown {kind} unit '{u}'. Use one of: {', '.join(allowed)}.")
    return key


def pressure_to_Pa(value, unit="atm"):
    return value * PRESSURE_UNITS[_unit(unit, PRESSURE_UNITS, "pressure")]

def pressure_from_Pa(value, unit="atm"):
    return value / PRESSURE_UNITS[_unit(unit, PRESSURE_UNITS, "pressure")]

def volume_to_m3(value, unit="L"):
    return value * VOLUME_UNITS[_unit(unit, VOLUME_UNITS, "volume")]

def volume_from_m3(value, unit="L"):
    return value / VOLUME_UNITS[_unit(unit, VOLUME_UNITS, "volume")]

def temperature_to_K(value, unit="K"):
    k = value + 273.15 if _unit(unit, TEMPERATURE_UNITS, "temperature") == "C" else value
    if k <= 0:
        raise ValueError("Temperature must be above absolute zero (0 K = -273.15 °C).")
    return k

def temperature_from_K(value, unit="K"):
    return value - 273.15 if _unit(unit, TEMPERATURE_UNITS, "temperature") == "C" else value


def _positive(name, value):
    if value is None:
        raise ValueError(f"Missing value: {name}")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def ideal_gas_solve(solve, P=None, V=None, n=None, T=None,
                    P_unit="atm", V_unit="L", T_unit="K"):
    """
    PV = nRT with units. Give three of P, V, n, T and name the fourth in
    `solve` ('P', 'V', 'n' or 'T'). The answer comes back in the unit given
    for that quantity (n always in mol).
    """
    if solve not in ("P", "V", "n", "T"):
        raise ValueError("solve must be 'P', 'V', 'n' or 'T'.")
    P_Pa = pressure_to_Pa(_positive("P", P), P_unit) if solve != "P" else None
    V_m3 = volume_to_m3(_positive("V", V), V_unit) if solve != "V" else None
    n_mol = _positive("n", n) if solve != "n" else None
    if solve != "T" and T is None:
        raise ValueError("Missing value: T")
    T_K = temperature_to_K(float(T), T_unit) if solve != "T" else None
    # validate units of the unknown too
    _unit(P_unit, PRESSURE_UNITS, "pressure"); _unit(V_unit, VOLUME_UNITS, "volume")
    _unit(T_unit, TEMPERATURE_UNITS, "temperature")
    if solve == "P":
        return pressure_from_Pa(n_mol * R_SI * T_K / V_m3, P_unit)
    if solve == "V":
        return volume_from_m3(n_mol * R_SI * T_K / P_Pa, V_unit)
    if solve == "n":
        return P_Pa * V_m3 / (R_SI * T_K)
    return temperature_from_K(P_Pa * V_m3 / (n_mol * R_SI), T_unit)


def combined_gas_solve(solve, P1=None, V1=None, T1=None, P2=None, V2=None, T2=None,
                       P_unit="atm", V_unit="L", T_unit="K"):
    """
    P1V1/T1 = P2V2/T2 with units (temperatures are converted to K first, so
    °C input is handled correctly). `solve` is one of P1, V1, T1, P2, V2, T2.
    """
    names = ("P1", "V1", "T1", "P2", "V2", "T2")
    if solve not in names:
        raise ValueError(f"solve must be one of {', '.join(names)}.")
    vals = dict(zip(names, (P1, V1, T1, P2, V2, T2)))
    si = {}
    for k, v in vals.items():
        if k == solve:
            continue
        if k[0] == "T":
            if v is None:
                raise ValueError(f"Missing value: {k}")
            si[k] = temperature_to_K(float(v), T_unit)
        else:
            si[k] = _positive(k, v)
            si[k] = pressure_to_Pa(si[k], P_unit) if k[0] == "P" else volume_to_m3(si[k], V_unit)
    _unit(P_unit, PRESSURE_UNITS, "pressure"); _unit(V_unit, VOLUME_UNITS, "volume")
    _unit(T_unit, TEMPERATURE_UNITS, "temperature")
    # k = PV/T is the same for both states
    known = "1" if solve[1] == "2" else "2"
    k = si["P" + known] * si["V" + known] / si["T" + known]
    other = solve[1]
    q = solve[0]
    if q == "P":
        return pressure_from_Pa(k * si["T" + other] / si["V" + other], P_unit)
    if q == "V":
        return volume_from_m3(k * si["T" + other] / si["P" + other], V_unit)
    return temperature_from_K(si["P" + other] * si["V" + other] / k, T_unit)


def gas_mixing_solve(solve, P1, V1, T1, P2, V2, T2, Pf=None, Vf=None, Tf=None,
                     P_unit="atm", V_unit="L", T_unit="K"):
    """
    Two gas samples combined into one container. n_total = n1 + n2 (from
    PV = nRT for each sample), then PfVf = n_total·R·Tf is solved for
    `solve` ('Pf', 'Vf' or 'Tf'). Returns (result, n1, n2) with the result
    in the given unit.
    """
    n1 = ideal_gas_solve("n", P=P1, V=V1, T=T1, P_unit=P_unit, V_unit=V_unit, T_unit=T_unit)
    n2 = ideal_gas_solve("n", P=P2, V=V2, T=T2, P_unit=P_unit, V_unit=V_unit, T_unit=T_unit)
    target = {"Pf": "P", "Vf": "V", "Tf": "T"}.get(solve)
    if target is None:
        raise ValueError("solve must be 'Pf', 'Vf' or 'Tf'.")
    result = ideal_gas_solve(target, P=Pf, V=Vf, n=n1 + n2, T=Tf,
                             P_unit=P_unit, V_unit=V_unit, T_unit=T_unit)
    return result, n1, n2


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


def _ask_units():
    """Ask for P, V and T units (Enter keeps atm / L / K)."""
    while True:
        try:
            pu = input("Pressure unit [atm/kPa/Pa/bar/mmHg] (Enter = atm): ").strip() or "atm"
            vu = input("Volume unit [L/dm3/mL/cm3/m3] (Enter = L): ").strip() or "L"
            tu = input("Temperature unit [K/C] (Enter = K): ").strip() or "K"
            return (_unit(pu, PRESSURE_UNITS, "pressure"), _unit(vu, VOLUME_UNITS, "volume"),
                    _unit(tu, TEMPERATURE_UNITS, "temperature"))
        except ValueError as e:
            print(f"  [ERROR] {e}")


def _t_label(tu):
    return "°C" if tu == "C" else "K"


def ideal_gas_menu():
    print("\n-- Ideal Gas Law (PV = nRT) --")
    print("Solve for:")
    print("1. Pressure (P)")
    print("2. Volume (V)")
    print("3. Moles (n)")
    print("4. Temperature (T)")
    choice = input("Select (1-4): ").strip()
    solve = {"1": "P", "2": "V", "3": "n", "4": "T"}.get(choice)
    if not solve:
        print("Invalid choice.")
        return
    pu, vu, tu = _ask_units()
    vals = {}
    try:
        if solve != "P":
            vals["P"] = _get_float(f"Pressure ({pu}): ", "pressure", positive=True)
        if solve != "V":
            vals["V"] = _get_float(f"Volume ({vu}): ", "volume", positive=True)
        if solve != "n":
            vals["n"] = _get_float("Moles (mol): ", "moles", positive=True)
        if solve != "T":
            vals["T"] = _get_float(f"Temperature ({_t_label(tu)}): ", "temperature")
        result = ideal_gas_solve(solve, P_unit=pu, V_unit=vu, T_unit=tu, **vals)
        unit = {"P": pu, "V": vu, "n": "mol", "T": _t_label(tu)}[solve]
        print(f"{solve} = {result:.4g} {unit}   (R = 8.314 J/(mol·K), SI units internally)")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def combined_gas_menu():
    print("\n-- Combined Gas Law (P1V1/T1 = P2V2/T2) --")
    print("Solve for:")
    print("1. P2")
    print("2. V2")
    print("3. T2")
    choice = input("Select (1-3): ").strip()
    solve = {"1": "P2", "2": "V2", "3": "T2"}.get(choice)
    if not solve:
        print("Invalid choice.")
        return
    pu, vu, tu = _ask_units()
    labels = {"P": pu, "V": vu, "T": _t_label(tu)}
    vals = {}
    try:
        for name in ("P1", "V1", "T1", "P2", "V2", "T2"):
            if name == solve:
                continue
            vals[name] = _get_float(f"{name} ({labels[name[0]]}): ", name,
                                    positive=name[0] != "T")
        result = combined_gas_solve(solve, P_unit=pu, V_unit=vu, T_unit=tu, **vals)
        print(f"{solve} = {result:.4g} {labels[solve[0]]}")
    except (ZeroDivisionError, ValueError) as e:
        print(f"  [ERROR] {e}")


def molar_volume_menu():
    print("\n-- Molar Volume --")
    print(f"1. Moles → Volume at STP ({MOLAR_VOLUME_STP} L/mol, 0 °C, 100 kPa)")
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
