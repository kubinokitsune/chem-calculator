# Empirical Formula_Calculator.py
from constants import capitalize_formula

def calculate_empirical_formula(elements, masses):
    """Calculates the empirical formula from lists of elements and their masses (in grams or %). Returns a dictionary with element symbols as keys and subscripts as values."""
    molar_masses = {
        'H': 1.008, 'He': 4.0026, 'Li': 6.94, 'Be': 9.0122, 'B': 10.81,
        'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
        'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.085, 'P': 30.974,
        'S': 32.06, 'Cl': 35.45, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
        'Sc': 44.956, 'Ti': 47.867, 'V': 50.941, 'Cr': 51.996, 'Mn': 54.938,
        'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.38,
        'Ga': 69.723, 'Ge': 72.630, 'As': 74.922, 'Se': 78.971, 'Br': 79.904,
        'Kr': 83.798, 'Rb': 85.467, 'Sr': 87.62, 'Y': 88.906, 'Zr': 91.224,
        'Nb': 92.906, 'Mo': 95.95, 'Tc': 98, 'Ru': 101.07, 'Rh': 102.91,
        'Pd': 106.42, 'Ag': 107.87, 'Cd': 112.41, 'In': 114.82, 'Sn': 118.71,
        'Sb': 121.76, 'Te': 127.60, 'I': 126.90, 'Xe': 131.29, 'Cs': 132.91,
        'Ba': 137.33, 'La': 138.91, 'Ce': 140.12, 'Pr': 140.91, 'Nd': 144.24,
        'Pm': 145, 'Sm': 150.36, 'Eu': 151.96, 'Gd': 157.25, 'Tb': 158.93,
        'Dy': 162.50, 'Ho': 164.93, 'Er': 167.26, 'Tm': 168.93, 'Yb': 173.04,
        'Lu': 174.97, 'Hf': 178.49, 'Ta': 180.95, 'W': 183.84, 'Re': 186.21,
        'Os': 190.23, 'Ir': 192.22, 'Pt': 195.08, 'Au': 196.97, 'Hg': 200.59,
        'Tl': 204.38, 'Pb': 207.2, 'Bi': 208.98, 'Po': 209, 'At': 210,
        'Rn': 222, 'Fr': 223, 'Ra': 226, 'Ac': 227, 'Th': 232.04,
        'Pa': 231.04, 'U': 238.03, 'Np': 237, 'Pu': 244, 'Am': 243,
        'Cm': 247, 'Bk': 247, 'Cf': 251, 'Es': 252, 'Fm': 257, 'Md': 258,
        'No': 259, 'Lr': 262, 'Rf': 267, 'Db': 270, 'Sg': 271, 'Bh': 270,
        'Hs': 277, 'Mt': 276, 'Ds': 281, 'Rg': 282, 'Cn': 285, 'Nh': 286,
        'Fl': 289, 'Mc': 288, 'Lv': 293, 'Ts': 294, 'Og': 294
    }
    if not elements or len(elements) != len(masses):
        raise ValueError("Provide one mass for each element.")
    if any(m <= 0 for m in masses):
        raise ValueError("Every element mass (or %) must be greater than zero.")

    # Step 1: Convert masses to moles
    moles = []
    for i in range(len(elements)):
        element = elements[i]
        if element not in molar_masses:
            raise ValueError(f"Element '{element}' not found in molar masses dictionary.")
        moles.append(masses[i] / molar_masses[element])

    # Step 2: Divide by the smallest number of moles to normalize
    min_moles = min(moles)
    ratios = [m / min_moles for m in moles]

    # Step 3: Find the smallest multiplier that makes every ratio a whole
    # number (within 0.1, the usual lab-data tolerance). If none does, use
    # the multiplier that gets closest.
    def _max_err(mult):
        return max(abs(r * mult - round(r * mult)) for r in ratios)

    multiplier = next((m for m in range(1, 13) if _max_err(m) <= 0.1), None)
    if multiplier is None:
        multiplier = min(range(1, 13), key=_max_err)
    whole_numbers = [int(round(r * multiplier)) for r in ratios]

    # Step 4: Create empirical formula dictionary
    empirical_formula = {}
    for i in range(len(elements)):
        empirical_formula[elements[i]] = whole_numbers[i]

    return empirical_formula

def molecular_formula(empirical, molar_mass, empirical_mass=None):
    """
    Molecular formula from the empirical formula and the molecular mass.
    n = Mr(molecular) / Mr(empirical), rounded to the nearest whole number.
    `empirical` is a dict like {'C': 1, 'H': 2, 'O': 1}.
    Returns (formula dict, multiplier n, empirical mass).
    """
    from percent_composition_calculator import MOLAR_MASS
    if not empirical:
        raise ValueError("Enter the empirical formula first.")
    molar_mass = float(molar_mass)
    if molar_mass <= 0:
        raise ValueError("The molecular mass must be greater than zero.")
    if empirical_mass is None:
        unknown = [el for el in empirical if el not in MOLAR_MASS]
        if unknown:
            raise ValueError("Unknown element(s): " + ", ".join(unknown))
        empirical_mass = sum(MOLAR_MASS[el] * n for el, n in empirical.items())
    if empirical_mass <= 0:
        raise ValueError("The empirical formula mass must be greater than zero.")
    ratio = molar_mass / empirical_mass
    n = round(ratio)
    if n < 1:
        raise ValueError(f"The molecular mass ({molar_mass:g}) is smaller than the empirical "
                         f"formula mass ({empirical_mass:.2f}).")
    if abs(ratio - n) > 0.1 * n:
        raise ValueError(f"Mr ÷ empirical mass = {ratio:.3f}, which is not close to a whole "
                         "number — check the values.")
    return {el: count * n for el, count in empirical.items()}, n, empirical_mass


def combustion_analysis(mass_CO2, mass_H2O, sample_mass=None, mass_N=0.0):
    """
    Empirical formula from a combustion experiment.
      moles C  = mass CO2 / 44.009
      moles H  = 2 × mass H2O / 18.015
      mass O   = sample mass − mass C − mass H − mass N   (if the sample mass is known)

    A leftover oxygen mass within 1 % of the sample is treated as rounding, not
    as oxygen, so a hydrocarbon does not pick up a stray O.
    Returns (elements, masses, notes) ready for calculate_empirical_formula.
    """
    from percent_composition_calculator import MOLAR_MASS
    M_CO2 = MOLAR_MASS["C"] + 2 * MOLAR_MASS["O"]
    M_H2O = 2 * MOLAR_MASS["H"] + MOLAR_MASS["O"]
    mass_CO2, mass_H2O = float(mass_CO2), float(mass_H2O)
    if mass_CO2 < 0 or mass_H2O < 0:
        raise ValueError("Masses cannot be negative.")
    if mass_CO2 == 0 and mass_H2O == 0:
        raise ValueError("Enter the mass of CO2 and/or H2O produced.")
    mass_C = mass_CO2 / M_CO2 * MOLAR_MASS["C"]
    mass_H = 2 * mass_H2O / M_H2O * MOLAR_MASS["H"]
    elements, masses, notes = [], [], []
    if mass_C > 0:
        elements.append("C"); masses.append(mass_C)
    if mass_H > 0:
        elements.append("H"); masses.append(mass_H)
    if mass_N:
        mass_N = float(mass_N)
        if mass_N < 0:
            raise ValueError("Masses cannot be negative.")
        if mass_N > 0:
            elements.append("N"); masses.append(mass_N)
    if sample_mass is not None and str(sample_mass) != "":
        sample_mass = float(sample_mass)
        if sample_mass <= 0:
            raise ValueError("The sample mass must be greater than zero.")
        mass_O = sample_mass - mass_C - mass_H - (mass_N or 0.0)
        rounding = 0.01 * sample_mass
        if mass_O < -rounding:
            raise ValueError(f"The masses of C ({mass_C:.4g} g) and H ({mass_H:.4g} g) already "
                             f"add up to more than the sample ({sample_mass:g} g) — check the data.")
        if mass_O > rounding:
            elements.append("O"); masses.append(mass_O)
        else:
            notes.append("C and H account for the whole sample (to within 1 %), "
                         "so the compound contains no oxygen.")
    else:
        notes.append("No sample mass given, so any oxygen in the compound is not included.")
    return elements, masses, notes


def display_empirical_formula(empirical_formula):
    """Convert formula dictionary to a readable string like C6H12O6"""
    result = ""
    for element, subscript in empirical_formula.items():
        result += element
        if subscript > 1:
            result += str(subscript)
    return result

def empirical_formula_menu():
    while True:
        print("\n--- Empirical Formula Calculator ---")
        print("1. Calculate Empirical Formula")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-1): ").strip()
        if choice == '1':
            raw_n = input("Enter the number of different elements: ").strip()
            try:
                num_elements = int(raw_n)
                if num_elements < 1:
                    print("  [ERROR] Number of elements must be at least 1.")
                    continue
            except ValueError:
                print("  [ERROR] Invalid input: expected a whole number for element count.")
                continue

            elements = []
            masses = []
            valid = True
            for i in range(num_elements):
                raw_elem = input(f"Enter element symbol #{i+1} (e.g., C, H, O): ").strip()
                element = capitalize_formula(raw_elem)
                raw_mass = input(f"Enter mass or percent of {element}: ").strip()
                try:
                    mass = float(raw_mass)
                except ValueError:
                    print(f"  [ERROR] Invalid input: expected a number for mass of {element}.")
                    valid = False
                    break
                if mass <= 0:
                    print(f"  [ERROR] Mass/percent of {element} must be greater than zero.")
                    valid = False
                    break
                elements.append(element)
                masses.append(mass)

            if not valid:
                continue

            try:
                formula = calculate_empirical_formula(elements, masses)
                formula_str = display_empirical_formula(formula)
                print(f"\nEmpirical Formula: {formula_str}")
            except ValueError as e:
                print(f"  [ERROR] {e}")
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")