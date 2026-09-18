"""
uncertainties.py — uncertainties and significant figures for IB practical work

IB rules used here:
  * adding or subtracting  → add the ABSOLUTE uncertainties
  * multiplying or dividing → add the PERCENTAGE uncertainties
  * raising to a power n    → multiply the percentage uncertainty by |n|
  * an answer is quoted to the same precision as the data it came from
"""

import math


def _finite(name, value):
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{name} must be a number.")
    return v


def _positive(name, value):
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return v


def _non_negative(name, value):
    v = _finite(name, value)
    if v < 0:
        raise ValueError(f"{name} cannot be negative.")
    return v


# ── absolute ↔ percentage ────────────────────────────────────────────────────

def percentage_uncertainty(value, absolute):
    """% uncertainty = absolute ÷ |value| × 100."""
    value = _finite("Value", value)
    absolute = _non_negative("Absolute uncertainty", absolute)
    if value == 0:
        raise ValueError("Percentage uncertainty is undefined when the value is zero.")
    return absolute / abs(value) * 100


def absolute_uncertainty(value, percent):
    """Absolute uncertainty = % ÷ 100 × |value|."""
    value = _finite("Value", value)
    percent = _non_negative("Percentage uncertainty", percent)
    return percent / 100 * abs(value)


# ── combining measurements ───────────────────────────────────────────────────

def combine_add_subtract(values, absolutes):
    """
    Adding or subtracting: the absolute uncertainties add.
    `values` are signed (use a negative value to subtract that measurement).
    Returns (result, absolute uncertainty, percentage uncertainty).
    """
    if len(values) != len(absolutes) or not values:
        raise ValueError("Give one uncertainty for each measurement.")
    result = sum(_finite("Value", v) for v in values)
    total = sum(_non_negative("Absolute uncertainty", a) for a in absolutes)
    pct = (total / abs(result) * 100) if result != 0 else float("inf")
    return result, total, pct


def combine_multiply_divide(values, percents, operations=None):
    """
    Multiplying or dividing: the percentage uncertainties add.
    `operations` is a list like ['*', '/', ...] applied to the values after the
    first (default: all multiply).
    Returns (result, absolute uncertainty, percentage uncertainty).
    """
    if len(values) != len(percents) or not values:
        raise ValueError("Give one uncertainty for each measurement.")
    ops = list(operations or ["*"] * (len(values) - 1))
    if len(ops) != len(values) - 1:
        raise ValueError("Give one operation between each pair of measurements.")
    result = _finite("Value", values[0])
    for value, op in zip(values[1:], ops):
        v = _finite("Value", value)
        if op == "*":
            result *= v
        elif op == "/":
            if v == 0:
                raise ValueError("Cannot divide by zero.")
            result /= v
        else:
            raise ValueError(f"Unknown operation '{op}' — use * or /.")
    pct = sum(_non_negative("Percentage uncertainty", p) for p in percents)
    return result, abs(result) * pct / 100, pct


def power_uncertainty(value, percent, power):
    """Raising to a power: the percentage uncertainty is multiplied by |n|."""
    value = _finite("Value", value)
    percent = _non_negative("Percentage uncertainty", percent)
    power = _finite("Power", power)
    result = value ** power
    pct = percent * abs(power)
    return result, abs(result) * pct / 100, pct


def percentage_error(experimental, accepted):
    """% error = |experimental − accepted| ÷ |accepted| × 100 (accuracy, not precision)."""
    experimental = _finite("Experimental value", experimental)
    accepted = _finite("Accepted value", accepted)
    if accepted == 0:
        raise ValueError("The accepted value cannot be zero.")
    return abs(experimental - accepted) / abs(accepted) * 100


# ── significant figures and rounding ─────────────────────────────────────────

def round_to_sig_figs(value, figures):
    """Round to a number of significant figures (returns a float)."""
    value = _finite("Value", value)
    figures = int(figures)
    if figures < 1 or figures > 15:
        raise ValueError("Significant figures must be between 1 and 15.")
    if value == 0:
        return 0.0
    return round(value, -int(math.floor(math.log10(abs(value)))) + (figures - 1))


def sig_figs_of(text):
    """How many significant figures a written number has ('0.00420' → 3)."""
    s = str(text).strip().lower().replace("−", "-")
    if "e" in s:
        s = s.split("e")[0]
    s = s.lstrip("+-")
    if not s or not any(ch.isdigit() for ch in s):
        raise ValueError(f"'{text}' is not a number.")
    if "." in s:
        whole, frac = s.split(".", 1)
        digits = (whole + frac).lstrip("0")
        return len(digits) if digits else len(frac)   # 0.00 → the zeros after the point count
    return len(s.rstrip("0")) if s.strip("0") else 1


def format_with_uncertainty(value, absolute, figures=None):
    """'0.0824 ± 0.0005' — the uncertainty is quoted to 1 s.f. and the value is
    rounded to the same decimal place."""
    value = _finite("Value", value)
    absolute = _non_negative("Absolute uncertainty", absolute)
    if absolute == 0:
        return f"{value:g} (no uncertainty given)"
    unc = round_to_sig_figs(absolute, 1)
    places = max(0, -int(math.floor(math.log10(abs(unc)))))
    if figures:
        value = round_to_sig_figs(value, figures)
    return f"{value:.{places}f} ± {unc:.{places}f}"


# ── Menu ─────────────────────────────────────────────────────────────────────

def _get_float(prompt, label=None):
    label = label or prompt.strip().rstrip(':')
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  [ERROR] Invalid input: expected a number for {label}.")


def uncertainties_menu():
    while True:
        print("\n--- Uncertainties & Significant Figures ---")
        print("1. Absolute → percentage uncertainty")
        print("2. Percentage → absolute uncertainty")
        print("3. Adding / subtracting measurements")
        print("4. Multiplying / dividing measurements")
        print("5. Raising to a power")
        print("6. Percentage error (vs accepted value)")
        print("7. Round to significant figures")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-7): ").strip()
        try:
            if choice == "1":
                v = _get_float("Measurement: ")
                a = _get_float("Absolute uncertainty (±): ")
                print(f"  {percentage_uncertainty(v, a):.3g} %")
                print(f"  {format_with_uncertainty(v, a)}")
            elif choice == "2":
                v = _get_float("Measurement: ")
                p = _get_float("Percentage uncertainty (%): ")
                a = absolute_uncertainty(v, p)
                print(f"  ± {a:.3g}")
                print(f"  {format_with_uncertainty(v, a)}")
            elif choice == "3":
                n = int(input("How many measurements? ").strip() or "2")
                values, uncs = [], []
                for i in range(n):
                    values.append(_get_float(f"  Value {i+1} (negative to subtract): "))
                    uncs.append(_get_float(f"  Absolute uncertainty {i+1} (±): "))
                r, a, p = combine_add_subtract(values, uncs)
                print(f"  Result = {r:.4g} ± {a:.3g}  ({p:.3g} %)")
                print(f"  {format_with_uncertainty(r, a)}")
            elif choice == "4":
                n = int(input("How many measurements? ").strip() or "2")
                values, pcts, ops = [], [], []
                for i in range(n):
                    if i > 0:
                        ops.append(input(f"  Operation before value {i+1} [*//]: ").strip() or "*")
                    values.append(_get_float(f"  Value {i+1}: "))
                    pcts.append(_get_float(f"  Percentage uncertainty {i+1} (%): "))
                r, a, p = combine_multiply_divide(values, pcts, ops)
                print(f"  Result = {r:.4g} ± {a:.3g}  ({p:.3g} %)")
                print(f"  {format_with_uncertainty(r, a)}")
            elif choice == "5":
                v = _get_float("Value: ")
                p = _get_float("Percentage uncertainty (%): ")
                n = _get_float("Power: ")
                r, a, pct = power_uncertainty(v, p, n)
                print(f"  Result = {r:.4g} ± {a:.3g}  ({pct:.3g} %)")
            elif choice == "6":
                e = _get_float("Experimental value: ")
                acc = _get_float("Accepted (literature) value: ")
                print(f"  Percentage error = {percentage_error(e, acc):.3g} %")
            elif choice == "7":
                v = _get_float("Value: ")
                f = int(input("Significant figures: ").strip() or "3")
                print(f"  {round_to_sig_figs(v, f):g}")
            elif choice in ("0", "exit"):
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError as e:
            print(f"  [ERROR] {e}")
