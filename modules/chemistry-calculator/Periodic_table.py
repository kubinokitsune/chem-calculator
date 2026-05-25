
"""Periodic_table module

Provides element metadata (atomic number, symbol, name, atomic weight)
and an interactive lookup menu.
"""


ELEMENTS = [
    # (Z, symbol, name, standard_atomic_weight)
    (1, 'H', 'hydrogen', 1.008),
    (2, 'He', 'helium', 4.0026),
    (3, 'Li', 'lithium', 6.94),
    (4, 'Be', 'beryllium', 9.0122),
    (5, 'B', 'boron', 10.81),
    (6, 'C', 'carbon', 12.011),
    (7, 'N', 'nitrogen', 14.007),
    (8, 'O', 'oxygen', 15.999),
    (9, 'F', 'fluorine', 18.998),
    (10, 'Ne', 'neon', 20.180),
    (11, 'Na', 'sodium', 22.990),
    (12, 'Mg', 'magnesium', 24.305),
    (13, 'Al', 'aluminum', 26.982),
    (14, 'Si', 'silicon', 28.085),
    (15, 'P', 'phosphorus', 30.974),
    (16, 'S', 'sulfur', 32.06),
    (17, 'Cl', 'chlorine', 35.45),
    (18, 'Ar', 'argon', 39.948),
    (19, 'K', 'potassium', 39.098),
    (20, 'Ca', 'calcium', 40.078),
    (21, 'Sc', 'scandium', 44.956),
    (22, 'Ti', 'titanium', 47.867),
    (23, 'V', 'vanadium', 50.942),
    (24, 'Cr', 'chromium', 51.996),
    (25, 'Mn', 'manganese', 54.938),
    (26, 'Fe', 'iron', 55.845),
    (27, 'Co', 'cobalt', 58.933),
    (28, 'Ni', 'nickel', 58.693),
    (29, 'Cu', 'copper', 63.546),
    (30, 'Zn', 'zinc', 65.38),
    (31, 'Ga', 'gallium', 69.723),
    (32, 'Ge', 'germanium', 72.630),
    (33, 'As', 'arsenic', 74.922),
    (34, 'Se', 'selenium', 78.971),
    (35, 'Br', 'bromine', 79.904),
    (36, 'Kr', 'krypton', 83.798),
    (37, 'Rb', 'rubidium', 85.468),
    (38, 'Sr', 'strontium', 87.62),
    (39, 'Y', 'yttrium', 88.906),
    (40, 'Zr', 'zirconium', 91.224),
    (41, 'Nb', 'niobium', 92.906),
    (42, 'Mo', 'molybdenum', 95.95),
    (43, 'Tc', 'technetium', 98.0),
    (44, 'Ru', 'ruthenium', 101.07),
    (45, 'Rh', 'rhodium', 102.91),
    (46, 'Pd', 'palladium', 106.42),
    (47, 'Ag', 'silver', 107.8682),
    (48, 'Cd', 'cadmium', 112.414),
    (49, 'In', 'indium', 114.818),
    (50, 'Sn', 'tin', 118.710),
    (51, 'Sb', 'antimony', 121.760),
    (52, 'Te', 'tellurium', 127.60),
    (53, 'I', 'iodine', 126.90447),
    (54, 'Xe', 'xenon', 131.293),
    (55, 'Cs', 'cesium', 132.905),
    (56, 'Ba', 'barium', 137.327),
    (57, 'La', 'lanthanum', 138.905),
    (58, 'Ce', 'cerium', 140.116),
    (59, 'Pr', 'praseodymium', 140.90766),
    (60, 'Nd', 'neodymium', 144.242),
    (61, 'Pm', 'promethium', 145.0),
    (62, 'Sm', 'samarium', 150.36),
    (63, 'Eu', 'europium', 151.964),
    (64, 'Gd', 'gadolinium', 157.25),
    (65, 'Tb', 'terbium', 158.925),
    (66, 'Dy', 'dysprosium', 162.500),
    (67, 'Ho', 'holmium', 164.930),
    (68, 'Er', 'erbium', 167.259),
    (69, 'Tm', 'thulium', 168.934),
    (70, 'Yb', 'ytterbium', 173.045),
    (71, 'Lu', 'lutetium', 174.967),
    (72, 'Hf', 'hafnium', 178.49),
    (73, 'Ta', 'tantalum', 180.948),
    (74, 'W', 'tungsten', 183.84),
    (75, 'Re', 'rhenium', 186.207),
    (76, 'Os', 'osmium', 190.23),
    (77, 'Ir', 'iridium', 192.217),
    (78, 'Pt', 'platinum', 195.084),
    (79, 'Au', 'gold', 196.967),
    (80, 'Hg', 'mercury', 200.592),
    (81, 'Tl', 'thallium', 204.38),
    (82, 'Pb', 'lead', 207.2),
    (83, 'Bi', 'bismuth', 208.9804),
    (84, 'Po', 'polonium', 209.0),
    (85, 'At', 'astatine', 210.0),
    (86, 'Rn', 'radon', 222.0),
    (87, 'Fr', 'francium', 223.0),
    (88, 'Ra', 'radium', 226.0),
    (89, 'Ac', 'actinium', 227.0),
    (90, 'Th', 'thorium', 232.038),
    (91, 'Pa', 'protactinium', 231.036),
    (92, 'U', 'uranium', 238.029),
    (93, 'Np', 'neptunium', 237.0),
    (94, 'Pu', 'plutonium', 244.0),
    (95, 'Am', 'americium', 243.0),
    (96, 'Cm', 'curium', 247.0),
    (97, 'Bk', 'berkelium', 247.0),
    (98, 'Cf', 'californium', 251.0),
    (99, 'Es', 'einsteinium', 252.0),
    (100, 'Fm', 'fermium', 257.0),
    (101, 'Md', 'mendelevium', 258.0),
    (102, 'No', 'nobelium', 259.0),
    (103, 'Lr', 'lawrencium', 262.0),
    (104, 'Rf', 'rutherfordium', 267.0),
    (105, 'Db', 'dubnium', 270.0),
    (106, 'Sg', 'seaborgium', 271.0),
    (107, 'Bh', 'bohrium', 270.0),
    (108, 'Hs', 'hassium', 277.0),
    (109, 'Mt', 'meitnerium', 276.0),
    (110, 'Ds', 'darmstadtium', 281.0),
    (111, 'Rg', 'roentgenium', 282.0),
    (112, 'Cn', 'copernicium', 285.0),
    (113, 'Nh', 'nihonium', 286.0),
    (114, 'Fl', 'flerovium', 289.0),
    (115, 'Mc', 'moscovium', 288.0),
    (116, 'Lv', 'livermorium', 293.0),
    (117, 'Ts', 'tennessine', 294.0),
    (118, 'Og', 'oganesson', 294.0),
]


def _normalize(s: str) -> str:
    return s.strip().lower()


def show_periodic_table():
    print("\n== Periodic Table ==")
    print("Z   Sym  Name                 Atomic Weight")
    print("--  ---- -------------------- --------------")
    for z, sym, name, weight in ELEMENTS:
        print(f"{z:3d}  {sym:3s}  {name.capitalize():20s} {weight:14g}")


def get_element_by_name(name: str):
    key = _normalize(name)
    for z, sym, n, w in ELEMENTS:
        if _normalize(n) == key:
            return {'number': z, 'symbol': sym, 'name': n, 'atomic_weight': w}
    return None


def get_element_by_symbol(symbol: str):
    key = _normalize(symbol)
    for z, sym, n, w in ELEMENTS:
        if _normalize(sym) == key:
            return {'number': z, 'symbol': sym, 'name': n, 'atomic_weight': w}
    return None


def get_element_by_number(number: int):
    if not isinstance(number, int):
        return None
    if 1 <= number <= len(ELEMENTS):
        z, sym, n, w = ELEMENTS[number - 1]
        return {'number': z, 'symbol': sym, 'name': n, 'atomic_weight': w}
    return None


def periodic_table_menu():
    while True:
        print("\n--- Periodic Table ---")
        print("1. Show full periodic table")
        print("2. Lookup by name")
        print("3. Lookup by symbol")
        print("4. Lookup by atomic number")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-4): ").strip()
        if choice == '1':
            show_periodic_table()
        elif choice == '2':
            q = input("Enter element name (e.g., Oxygen): ").strip()
            if not q:
                print("[ERROR] Please enter an element name.")
                continue
            res = get_element_by_name(q)
            if res:
                print(f"Found: {res['number']}: {res['symbol']} - {res['name'].capitalize()} (atomic weight: {res['atomic_weight']})")
            else:
                print(f"Element '{q}' not found. Try a different name or check spelling.")
        elif choice == '3':
            from constants import capitalize_formula
            q = capitalize_formula(input("Enter element symbol (e.g., O): ").strip())
            if not q:
                print("[ERROR] Please enter an element symbol.")
                continue
            res = get_element_by_symbol(q)
            if res:
                print(f"Found: {res['number']}: {res['symbol']} - {res['name'].capitalize()} (atomic weight: {res['atomic_weight']})")
            else:
                print(f"Element symbol '{q}' not found. Try a different symbol or check spelling.")
        elif choice == '4':
            q = input("Enter atomic number (e.g., 8): ").strip()
            if not q:
                print("[ERROR] Please enter an atomic number.")
                continue
            try:
                num = int(q)
                if num < 1:
                    print("[ERROR] Atomic number must be at least 1.")
                    continue
            except ValueError:
                print(f"[ERROR] Invalid input: expected a whole number for atomic number, got '{q}'.")
                continue
            res = get_element_by_number(num)
            if res:
                print(f"{res['number']}: {res['symbol']} - {res['name'].capitalize()} (atomic weight: {res['atomic_weight']})")
            else:
                print(f"No element with atomic number {num} in this table.")
        elif choice in ('0', 'exit'):
            break
        else:
            print("Invalid choice. Please try again.")

