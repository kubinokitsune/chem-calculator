# chemcore.py - shared helpers for ChemCalc on the Casio fx-CG50
# MicroPython: no f-strings, ASCII only, keep it small.

import math

# Elements 1-54 plus the heavier ones IB uses, packed into one string to save
# memory: symbol then relative atomic mass, separated by spaces.
_TABLE = (
    "H:1.01 He:4.00 Li:6.94 Be:9.01 B:10.81 C:12.01 N:14.01 O:16.00 F:19.00 "
    "Ne:20.18 Na:22.99 Mg:24.31 Al:26.98 Si:28.09 P:30.97 S:32.07 Cl:35.45 "
    "Ar:39.95 K:39.10 Ca:40.08 Sc:44.96 Ti:47.87 V:50.94 Cr:52.00 Mn:54.94 "
    "Fe:55.85 Co:58.93 Ni:58.69 Cu:63.55 Zn:65.38 Ga:69.72 Ge:72.63 As:74.92 "
    "Se:78.97 Br:79.90 Kr:83.80 Rb:85.47 Sr:87.62 Y:88.91 Zr:91.22 Nb:92.91 "
    "Mo:95.95 Ag:107.87 Cd:112.41 In:114.82 Sn:118.71 Sb:121.76 Te:127.60 "
    "I:126.90 Xe:131.29 Cs:132.91 Ba:137.33 La:138.91 Ce:140.12 Pt:195.08 "
    "Au:196.97 Hg:200.59 Tl:204.38 Pb:207.20 Bi:208.98 Ra:226.00 Th:232.04 "
    "U:238.03 W:183.84 Pd:106.42 Ru:101.07 Rh:102.91 Os:190.23 Ir:192.22 "
    "Re:186.21 Ta:180.95 Hf:178.49 At:210.00 Rn:222.00 Fr:223.00 Po:209.00"
)

_MASSES = None


def masses():
    """Element symbol -> relative atomic mass (built once, then reused)."""
    global _MASSES
    if _MASSES is None:
        _MASSES = {}
        for item in _TABLE.split():
            sym, value = item.split(":")
            _MASSES[sym] = float(value)
    return _MASSES


def element_mass(symbol):
    m = masses().get(symbol)
    if m is None:
        raise ValueError("Unknown element: " + symbol)
    return m


# ---- number formatting (MicroPython has no nice %g for every case) ----------

def fmt(x, figures=4):
    """Round to significant figures and write it in a short, readable way."""
    if x is None:
        return "-"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    if x != x or x in (float("inf"), float("-inf")):
        return "n/a"
    if x == 0:
        return "0"
    e = int(math.floor(math.log10(abs(x))))
    if e >= 6 or e <= -4:
        mant = x / (10.0 ** e)
        return str(round(mant, figures - 1)) + "e" + str(e)
    r = round(x, figures - 1 - e)
    if abs(r - int(r)) < 1e-12 and abs(r) < 1e9:
        return str(int(r))
    return str(r)


def show(label, value, unit=""):
    text = label + " = " + fmt(value)
    if unit:
        text = text + " " + unit
    print(text)


def line(char="-", width=27):
    print(char * width)


# ---- input helpers ---------------------------------------------------------

def ask_float(prompt, positive=False, blank=None):
    """Read a number. Enter on its own returns `blank` when one is given."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and blank is not None:
            return blank
        try:
            value = float(raw)
        except ValueError:
            print("  Enter a number.")
            continue
        if positive and value <= 0:
            print("  Must be greater than 0.")
            continue
        return value


def ask_int(prompt, low=None, high=None):
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  Enter a whole number.")
            continue
        if low is not None and value < low:
            print("  Too small.")
            continue
        if high is not None and value > high:
            print("  Too big.")
            continue
        return value


def ask_text(prompt):
    return input(prompt).strip()


def ask_choice(prompt, options):
    """options: list of (key, label). Returns the key that was chosen."""
    for key, label in options:
        print(" " + key + ") " + label)
    keys = [k for k, _ in options]
    while True:
        raw = input(prompt).strip().lower()
        if raw in keys:
            return raw
        print("  Choose: " + "/".join(keys))


def pause():
    input("[EXE] ")


# ---- formula parsing -------------------------------------------------------

def _read_number(text, i):
    n = len(text)
    if i >= n or not text[i].isdigit():
        return 1, i
    j = i
    while j < n and text[j].isdigit():
        j += 1
    return int(text[i:j]), j


def _read_group(text, i, depth):
    counts = {}
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "(":
            inner, i = _read_group(text, i + 1, depth + 1)
            mult, i = _read_number(text, i)
            for el in inner:
                counts[el] = counts.get(el, 0) + inner[el] * mult
            continue
        if ch == ")":
            if depth == 0:
                raise ValueError("Unmatched ) in formula")
            return counts, i + 1
        if ch.isalpha() and ch == ch.upper():
            j = i + 1
            if j < n and text[j].isalpha() and text[j] == text[j].lower():
                j += 1
            symbol = text[i:j]
            mult, i = _read_number(text, j)
            counts[symbol] = counts.get(symbol, 0) + mult
            continue
        raise ValueError("Bad character '" + ch + "' in formula")
    if depth > 0:
        raise ValueError("Missing ) in formula")
    return counts, i


def capitalise(formula):
    """'nacl' -> 'NaCl'. Leaves anything already containing capitals alone."""
    text = formula.strip().replace(" ", "")
    if text == "":
        return text
    for ch in text:
        if ch.isalpha() and ch == ch.upper():
            return text
    table = masses()
    out = ""
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if not ch.isalpha():
            out += ch
            i += 1
            continue
        two = ""
        if i + 1 < n and text[i + 1].isalpha():
            two = ch.upper() + text[i + 1].lower()
        # 'co' is usually C + O, 'nh' is N + H: prefer the split for these
        if two in ("Co", "No", "Nh", "Cn", "Hf", "Po", "Sc", "Ho", "Cf", "Hs"):
            two = ""
        if two != "" and two in table:
            out += two
            i += 2
        else:
            out += ch.upper()
            i += 1
    return out


def parse_formula(formula):
    """'Ca(OH)2' -> {'Ca':1, 'O':2, 'H':2}. Hydrates: CuSO4.5H2O or CuSO4*5H2O."""
    text = capitalise(formula)
    if text == "":
        raise ValueError("Enter a formula")
    total = {}
    for part in text.replace("*", ".").split("."):
        if part == "":
            continue
        lead = 1
        i = 0
        while i < len(part) and part[i].isdigit():
            i += 1
        if i > 0:
            lead = int(part[:i])
            part = part[i:]
        counts, end = _read_group(part, 0, 0)
        if end != len(part):
            raise ValueError("Bad formula: " + part)
        for el in counts:
            total[el] = total.get(el, 0) + counts[el] * lead
    table = masses()
    for el in total:
        if el not in table:
            raise ValueError("Unknown element: " + el)
    return total


def molar_mass(formula):
    """Relative molecular mass of a formula string."""
    counts = parse_formula(formula)
    table = masses()
    total = 0.0
    for el in counts:
        total += table[el] * counts[el]
    return total


def mass_or_formula(text):
    """Accept '58.44' or 'NaCl' and return the molar mass."""
    text = text.strip()
    if text == "":
        raise ValueError("Enter a molar mass or a formula")
    try:
        value = float(text)
    except ValueError:
        return molar_mass(text)
    if value <= 0:
        raise ValueError("Molar mass must be > 0")
    return value


def formula_text(counts):
    """{'C':6,'H':12,'O':6} -> 'C6H12O6' (C and H first, then alphabetical)."""
    order = []
    for el in ("C", "H"):
        if el in counts:
            order.append(el)
    rest = []
    for el in counts:
        if el not in ("C", "H"):
            rest.append(el)
    rest.sort()
    out = ""
    for el in order + rest:
        out += el
        if counts[el] != 1:
            out += str(counts[el])
    return out


def gcd(a, b):
    a, b = abs(int(a)), abs(int(b))
    while b:
        a, b = b, a % b
    return a
