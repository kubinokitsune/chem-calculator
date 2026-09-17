# equation_balancer.py
#
# Balances molecular AND ionic equations (including half-equations with e-)
# by solving for the null space of the element + charge conservation matrix.
#
# Species notation accepted (charge on the end):
#   Fe^3+  Fe3+  Fe+3  Fe(3+)  Fe³⁺  Fe 3+     -> Fe, charge +3
#   MnO4^-  MnO4-  MnO₄⁻                        -> MnO4, charge -1
#   SO4^2-  SO42-  SO4 2-  SO4--                -> SO4, charge -2
#   e-  e^-  e⁻                                 -> electron
# State symbols (aq) (s) (l) (g) and leading coefficients (2H2O) are ignored.
# Without a caret, digits before the sign are the charge for a single-element
# ion (Fe3+); for polyatomic ions a single digit is a subscript (NH4+) and with
# two or more digits the last one is the charge (SO42- = SO4 2-). Use ^ to be
# explicit.

import itertools
import re
from math import gcd
from functools import reduce

from sympy import Matrix, lcm
from mole_conversions import mole_conversion_menu
from percent_composition_calculator import parse_formula
from constants import capitalize_formula

_SUPERSCRIPT_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"
_FROM_SUPERSCRIPT = str.maketrans(_SUPERSCRIPT_CHARS, "0123456789+-")
_TO_SUPERSCRIPT = str.maketrans("0123456789+-", _SUPERSCRIPT_CHARS)
_FROM_SUBSCRIPT = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

MEDIA = ("acidic", "basic")

# Common ions (formula, charge). Used to read charges written without ^,
# e.g. SO42- (SO4 2-), NH4+ (NH4 +), I3- (I3 -), Fe3+ (Fe 3+).
KNOWN_IONS = {
    # monatomic cations
    ("H", 1), ("Li", 1), ("Na", 1), ("K", 1), ("Rb", 1), ("Cs", 1), ("Ag", 1), ("Cu", 1),
    ("Au", 1), ("Tl", 1), ("Hg", 1), ("Be", 2), ("Mg", 2), ("Ca", 2), ("Sr", 2), ("Ba", 2),
    ("Ra", 2), ("Zn", 2), ("Cd", 2), ("Hg", 2), ("Cu", 2), ("Fe", 2), ("Fe", 3), ("Co", 2),
    ("Co", 3), ("Ni", 2), ("Mn", 2), ("Mn", 3), ("Cr", 2), ("Cr", 3), ("Pb", 2), ("Pb", 4),
    ("Sn", 2), ("Sn", 4), ("Al", 3), ("Ga", 3), ("Au", 3), ("Ti", 2), ("Ti", 3), ("Ti", 4),
    ("V", 2), ("V", 3), ("Ce", 3), ("Ce", 4), ("Bi", 3), ("Sc", 3), ("La", 3),
    # monatomic anions
    ("H", -1), ("F", -1), ("Cl", -1), ("Br", -1), ("I", -1), ("O", -2), ("S", -2),
    ("Se", -2), ("Te", -2), ("N", -3), ("P", -3), ("As", -3),
    # polyatomic
    ("NH4", 1), ("H3O", 1), ("Hg2", 2), ("VO", 2), ("VO2", 1),
    ("OH", -1), ("NO3", -1), ("NO2", -1), ("SO4", -2), ("SO3", -2), ("HSO4", -1),
    ("HSO3", -1), ("S2O3", -2), ("S4O6", -2), ("S2O8", -2), ("PO4", -3), ("HPO4", -2),
    ("H2PO4", -1), ("PO3", -3), ("CO3", -2), ("HCO3", -1), ("C2O4", -2), ("HC2O4", -1),
    ("CN", -1), ("SCN", -1), ("OCN", -1), ("MnO4", -1), ("MnO4", -2), ("CrO4", -2),
    ("Cr2O7", -2), ("ClO", -1), ("ClO2", -1), ("ClO3", -1), ("ClO4", -1), ("BrO", -1),
    ("BrO3", -1), ("IO", -1), ("IO3", -1), ("IO4", -1), ("O2", -2), ("HO2", -1),
    ("CH3COO", -1), ("C2H3O2", -1), ("HCOO", -1), ("SiO3", -2), ("SiO4", -4),
    ("AsO4", -3), ("BO3", -3), ("B4O7", -2), ("AlO2", -1), ("ZnO2", -2), ("I3", -1),
    ("N3", -1), ("S2", -2), ("HS", -1), ("NH2", -1), ("BF4", -1), ("PF6", -1),
    ("Al(OH)4", -1), ("Zn(OH)4", -2), ("Fe(CN)6", -3), ("Fe(CN)6", -4),
    ("[Cu(NH3)4]", 2), ("[Ag(NH3)2]", 1), ("[Fe(CN)6]", -3), ("[Fe(CN)6]", -4),
}


def format_subscript(compound):
    return compound


def normalize_arrow(equation):
    """Turn the arrow variants people type or paste (→, ⟶, =>, ⇌, <=>, =) into '->'."""
    for arrow in ("<=>", "<->", "⇌", "⇄", "⟶", "→", "=>", "="):
        equation = equation.replace(arrow, "->")
    return equation


def parse_compound(compound):
    """Parse a chemical compound into a dictionary of elements and counts.

    Handles parentheses, hydrates and leading multipliers, and rejects
    unknown elements (raises ValueError).
    """
    return parse_formula(compound)


# ── Species (formula + charge) ───────────────────────────────────────────────

class Species:
    def __init__(self, formula, counts, charge=0, state=""):
        self.formula = formula      # e.g. 'MnO4', or 'e' for an electron
        self.counts = counts        # element -> count
        self.charge = charge
        self.state = state          # '(aq)' etc., display only
        self.alternatives = None    # other possible readings when the charge was ambiguous
        self.text = ""              # what the user typed (for notes)

    @property
    def is_electron(self):
        return self.formula == "e"

    def display(self, with_state=True):
        return (self.formula + format_charge(self.charge)
                + (self.state if with_state else ""))

    def __repr__(self):
        return f"Species({self.display()!r})"


def format_charge(charge):
    """+3 -> '³⁺', -1 -> '⁻', 0 -> ''."""
    if charge == 0:
        return ""
    mag = "" if abs(charge) == 1 else str(abs(charge))
    return (mag + ("+" if charge > 0 else "-")).translate(_TO_SUPERSCRIPT)


def _ascii_charge(charge):
    return f"{abs(charge) if abs(charge) != 1 else ''}{'+' if charge > 0 else '-'}"


def _charge_readings(base, digits, sign):
    """Possible (base, charge) readings of a species typed without ^, such as
    'SO42-', 'NH4+', 'I3-' or 'Fe3+'. The most likely reading comes first; a
    single reading is returned when only one of them is a known ion."""
    b = base.replace(" ", "")
    monatomic = re.fullmatch(r"[A-Z][a-z]?", capitalize_formula(b)) is not None
    default_j = len(digits) if monatomic else (1 if len(digits) >= 2 else 0)
    cands = []
    for j in range(0, min(2, len(digits)) + 1):
        sub_, ch = digits[:len(digits) - j], digits[len(digits) - j:]
        if ch.startswith("0"):
            continue
        q = sign * (int(ch) if ch else 1)
        if abs(q) > 8:
            continue
        formula = capitalize_formula(b + sub_)
        try:
            if not parse_formula(formula):
                continue
        except ValueError:
            continue
        cands.append((j, b + sub_, q, formula))
    known = [c for c in cands if (c[3], c[2]) in KNOWN_IONS]
    if monatomic:
        # 'V4+' is V 4+, not a V4 cluster, unless the cluster is a real ion (I3-, Hg2 2+)
        cands = [c for c in cands if c[0] == default_j or c in known] or cands
    pool = known or cands
    pool.sort(key=lambda c: c[0] != default_j)
    return [(c[1], c[2]) for c in pool]


def _charge_value(text):
    """'3+', '+3', '+', '2-', '--' -> signed int."""
    t = text.replace(" ", "")
    m = re.fullmatch(r"(\d*)([+-])|([+-])(\d+)|(\++|-+)", t)
    if not m:
        raise ValueError(f"Can't read the charge '{text}'. Write it like 3+ or 2-.")
    if m.group(5):
        mag, sign = len(m.group(5)), m.group(5)[0]
    elif m.group(2):
        mag, sign = int(m.group(1)) if m.group(1) else 1, m.group(2)
    else:
        mag, sign = int(m.group(4)), m.group(3)
    if mag == 0:
        raise ValueError(f"Can't read the charge '{text}': a charge of 0 needs no sign.")
    return mag if sign == "+" else -mag


def parse_species(text):
    """Parse one species such as 'Fe^3+(aq)', 'SO4 2-', '2H2O(l)' or 'e-'."""
    s = text.strip().replace("−", "-").replace("–", "-").translate(_FROM_SUBSCRIPT)
    if not s:
        raise ValueError("Empty species in equation.")

    # Unicode superscript charges: Fe³⁺ -> Fe^3+
    i = next((k for k, ch in enumerate(s) if ch in _SUPERSCRIPT_CHARS), None)
    if i is not None:
        s = s[:i] + "^" + s[i:].translate(_FROM_SUPERSCRIPT)

    state = ""
    m = re.search(r"\s*\((aq|s|l|g)\)\s*$", s, re.IGNORECASE)
    if m:
        state = f"({m.group(1).lower()})"
        s = s[:m.start()]

    # Leading coefficient typed by the user (2H2O) is ignored
    s = re.sub(r"^\d+\s*(?=[A-Za-z(\[{])", "", s).strip()

    if re.fullmatch(r"[eE]\s*\^?\s*-?", s):
        return Species("e", {}, -1)

    base, charge = s, 0
    readings = None
    m_sign_end = re.fullmatch(r"(.*?[A-Za-z)\]}])(\d*)([+-]+)", s)
    if "^" in s:
        base, ch = s.split("^", 1)
        charge = _charge_value(ch)
    elif re.search(r"[(\[{]\s*(\d*[+-]|[+-]\d+)\s*[)\]}]$", s):
        m = re.search(r"[(\[{]\s*(\d*[+-]|[+-]\d+)\s*[)\]}]$", s)
        base, charge = s[:m.start()], _charge_value(m.group(1))
    elif re.search(r"\s+(\d*[+-]|[+-]\d+)$", s):
        m = re.search(r"\s+(\d*[+-]|[+-]\d+)$", s)
        base, charge = s[:m.start()], _charge_value(m.group(1))
    elif m_sign_end:
        base, digits, signs = m_sign_end.groups()
        sign = 1 if signs[0] == "+" else -1
        if len(signs) > 1:
            if len(set(signs)) > 1:
                raise ValueError(f"Can't read the charge in '{text}'. Use ^, e.g. SO4^2-.")
            base, charge = base + digits, sign * len(signs)
        elif not digits:
            charge = sign
        else:
            # Fe3+ -> Fe 3+,  NH4+ -> NH4 +,  SO42- -> SO4 2-,  I3- -> I3 -
            readings = _charge_readings(base, digits, sign)
            if not readings:
                raise ValueError(f"Can't read the species '{text}'. Use ^ for the charge, e.g. SO4^2-.")
            base, charge = readings[0]
    else:
        m = re.fullmatch(r"(.*?[A-Za-z)\]}])([+-])(\d+)", s)
        if m:
            base, charge = m.group(1), _charge_value(m.group(2) + m.group(3))

    formula = capitalize_formula(base.replace(" ", ""))
    if not formula:
        raise ValueError(f"Can't read the species '{text}'.")
    if re.fullmatch(r"[eE]", formula):
        raise ValueError("Electrons must be written as e- (charge -1).")
    counts = parse_formula(formula)
    if not counts:
        raise ValueError(f"Can't read the species '{text}': it has no elements.")
    sp = Species(formula, counts, charge, state)
    sp.text = text.strip()
    if readings and len(readings) > 1:
        sp.alternatives = [sp]
        for b, q in readings[1:]:
            f = capitalize_formula(b.replace(" ", ""))
            alt = Species(f, parse_formula(f), q, state)
            alt.text = sp.text
            sp.alternatives.append(alt)
    return sp


# ── Equation text -> species strings ─────────────────────────────────────────

def _split_no_space(side):
    """Split 'H2+O2' on '+', but keep charge signs: 'Fe3++Cu', 'Fe^3+', 'H+'."""
    parts, cur = [], ""
    for i, ch in enumerate(side):
        if ch == "+":
            nxt = side[i + 1] if i + 1 < len(side) else ""
            after_digits = re.match(r"\d+(.|$)", side[i + 1:])
            is_charge = bool(cur) and (
                nxt in ("", "+", "(", ")", "]", "}")
                # 'Fe+3' / 'Fe+3+Cu': sign-then-digits at the end of a species
                or (after_digits is not None and after_digits.group(1) in ("", "+"))
                or re.search(r"\^\s*\d*$", cur) is not None
                or re.search(r"[(\[{]\s*\d*$", cur) is not None)
            if is_charge:
                cur += ch
                continue
            if not cur.strip():
                raise ValueError("Two '+' signs in a row: check the equation.")
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def split_side(side):
    """One side of an equation -> list of species strings."""
    side = side.strip()
    if not side:
        return []
    # With spaces, ' + ' (or ' +') separates species; charges stay attached.
    pieces = re.split(r"\s+\+\s*", side) if re.search(r"\s\+", side) else [side]
    out = []
    for piece in pieces:
        out += _split_no_space(piece.strip())
    out = [p.strip() for p in out]
    if any(not p for p in out):
        raise ValueError("Empty species in equation: check the '+' signs.")
    return out


def parse_equation(text):
    """'Fe3+ + Cu -> Fe2+ + Cu2+' -> (['Fe3+', 'Cu'], ['Fe2+', 'Cu2+'])."""
    t = normalize_arrow(text.strip())
    if t.count("->") != 1:
        raise ValueError("Use exactly one arrow (->) between reactants and products.")
    left, right = t.split("->")
    reactants, products = split_side(left), split_side(right)
    if not reactants or not products:
        raise ValueError("You must provide both reactants and products.")
    return reactants, products


# ── Balancing ────────────────────────────────────────────────────────────────

_MULTI_MSG = ("This equation has more than one independent way to balance it "
              "(it is really two or more reactions combined, e.g. two different "
              "products of the same element). Split it into separate equations.")


class _NoSolution(ValueError):
    pass


class _MultipleSolutions(ValueError):
    pass


def _solve(r_sp, p_sp, extras):
    """Smallest whole-number coefficients for reactants + products + extras.
    Extras may come out negative (meaning: product side) or zero (not needed);
    reactants and products must all come out positive."""
    species = r_sp + p_sp + extras
    signs = [-1] * len(r_sp) + [1] * len(p_sp) + [-1] * len(extras)
    elements = sorted({e for s in species for e in s.counts})
    rows = [[sg * s.counts.get(e, 0) for s, sg in zip(species, signs)] for e in elements]
    rows.append([sg * s.charge for s, sg in zip(species, signs)])

    null_space = Matrix(rows).nullspace()
    if not null_space:
        raise _NoSolution()
    if len(null_space) > 1:
        raise _MultipleSolutions()

    vec = null_space[0]
    ints = [int(v * lcm([x.q for x in vec])) for v in vec]
    ints = _primitive(ints)
    n_orig = len(r_sp) + len(p_sp)
    if all(c <= 0 for c in ints[:n_orig]):
        ints = [-c for c in ints]
    if any(c <= 0 for c in ints[:n_orig]):
        raise ValueError(
            "No valid balance: some species would need a zero or negative "
            "coefficient. Check that every species belongs on its side.")
    return ints


def _primitive(ints):
    g = reduce(gcd, (abs(c) for c in ints if c), 0) or 1
    return [c // g for c in ints]


def _half_equation(g_r, g_p, medium):
    """Textbook half-equation method for one redox pair.
    Returns [coeffs of g_r + g_p..., H2O, H+ or OH-, e-] where the last three
    are signed (positive = reactant side), or None if the pair doesn't work."""
    group = g_r + g_p
    signs = [-1] * len(g_r) + [1] * len(g_p)
    others = sorted({e for s in group for e in s.counts} - {"H", "O"})
    # 1. balance atoms other than O and H (use O, then H, only if still needed)
    vec = None
    for keys in (others, others + ["O"], others + ["O", "H"]):
        if not keys:
            continue
        rows = [[sg * s.counts.get(e, 0) for s, sg in zip(group, signs)] for e in keys]
        ns = Matrix(rows).nullspace()
        if len(ns) == 1:
            vec = ns[0]
            break
        if not ns:
            return None
    if vec is None:
        return None
    c = _primitive([int(v * lcm([x.q for x in vec])) for v in vec])
    if all(x <= 0 for x in c):
        c = [-x for x in c]
    if any(x <= 0 for x in c):
        return None

    def net(fn):
        return sum(-sg * x * fn(s) for x, s, sg in zip(c, group, signs))

    w = -net(lambda s: s.counts.get("O", 0))                 # 2. O with H2O
    h = -(net(lambda s: s.counts.get("H", 0)) + 2 * w)       # 3. H with H+
    e = net(lambda s: s.charge) + h                          # 4. charge with e-
    oh = 0
    if medium == "basic":                                    # H+ + OH- -> H2O
        w, oh, h = w + h, -h, 0
    return c + [w, h if medium == "acidic" else oh, e]


def _solve_by_half_equations(r_sp, p_sp, extras, medium):
    """Split the species into an oxidation and a reduction half-equation,
    balance each by the textbook method, and combine so electrons cancel.

    Water, H+ and OH- (written by the user or added for the medium) are the
    free species of the method. With no medium chosen, both the acidic and
    the basic method are tried, and any H2O / H+ / OH- the user did not write
    must cancel out. Returns coefficients in the same layout as _solve."""
    found = set()
    for med in ([medium] if medium else list(MEDIA)):
        found |= _half_equation_solutions(r_sp, p_sp, extras, med)
    if len(found) != 1:
        raise ValueError(_MULTI_MSG)
    return list(found.pop())


def _half_equation_solutions(r_sp, p_sp, extras, medium):
    water, ion = ("H2O", 0), (("H", 1) if medium == "acidic" else ("OH", -1))
    wrong_ion = ("OH", -1) if medium == "acidic" else ("H", 1)
    orig = [(s, 1) for s in r_sp] + [(s, -1) for s in p_sp]   # +1 = reactant side
    n = len(orig)
    keys = [(sp.formula, sp.charge) for sp, _ in orig]
    if wrong_ion in keys:
        return set()
    core = [i for i in range(n) if keys[i] not in (water, ion)]
    written = {keys[i]: i for i in range(n) if keys[i] in (water, ion)}
    extra_at = {(sp.formula, sp.charge): n + j for j, sp in enumerate(extras)}
    found = set()
    m = len(core)
    for mask in range(1, 2 ** m - 1):
        if not mask & 1:            # core species 0 always in half A: no mirror duplicates
            continue
        halves = []
        for grp in ([core[k] for k in range(m) if mask >> k & 1],
                    [core[k] for k in range(m) if not mask >> k & 1]):
            ri = [i for i in grp if orig[i][1] > 0]
            pi = [i for i in grp if orig[i][1] < 0]
            if not ri or not pi:
                break
            v = _half_equation([orig[i][0] for i in ri], [orig[i][0] for i in pi], medium)
            if v is None:
                break
            halves.append((dict(zip(ri + pi, v)), v[-3:]))
        if len(halves) != 2:
            continue
        (ca, (wa, xa, ea)), (cb, (wb, xb, eb)) = halves
        if ea == 0 or eb == 0 or (ea > 0) == (eb > 0):
            continue                # one half must gain electrons, the other lose them
        fa, fb = abs(eb), abs(ea)
        vec = [0] * (n + len(extras))
        for i, x in ca.items():
            vec[i] += fa * x
        for i, x in cb.items():
            vec[i] += fb * x
        ok = True
        for key, net in ((water, fa * wa + fb * wb), (ion, fa * xa + fb * xb)):
            if key in written:
                i = written[key]
                vec[i] = net * orig[i][1]       # must end up on the side it was written
                if vec[i] <= 0:
                    ok = False
            elif key in extra_at:
                vec[extra_at[key]] = net        # extras: positive = reactant side
            elif net != 0:
                ok = False                      # not written and no medium chosen
        if ok and all(vec[i] > 0 for i in range(n)):
            found.add(tuple(_primitive(vec)))
    return found


def balance_full(reactants, products, medium=None):
    """
    Balance a molecular or ionic equation.

    reactants / products : lists of species strings (or Species objects)
    medium               : None, 'acidic' (adds H+ / H2O as needed) or
                           'basic' (adds OH- / H2O as needed)

    Returns a dict:
      reactants : [(coeff, Species), ...]
      products  : [(coeff, Species), ...]
      equation  : balanced equation string
      added     : display names of species added for the medium
      notes     : how charges typed without ^ were read
    """
    medium = (medium or "").strip().lower() or None
    if medium not in (None, "none") + MEDIA:
        raise ValueError("Medium must be 'acidic', 'basic' or none.")
    if medium == "none":
        medium = None

    r_sp = [s if isinstance(s, Species) else parse_species(s) for s in reactants]
    p_sp = [s if isinstance(s, Species) else parse_species(s) for s in products]
    if not r_sp or not p_sp:
        raise ValueError("You must provide both reactants and products.")

    species = r_sp + p_sp
    amb = [i for i, sp in enumerate(species) if sp.alternatives]
    if not amb:
        res = _balance_core(r_sp, p_sp, medium)
        res["notes"] = []
        return res

    # Charges typed without ^ that could be read more than one way: keep the
    # readings that balance, preferring the most likely one.
    valid, first_error = [], None
    for tries, combo in enumerate(itertools.product(*(species[i].alternatives for i in amb))):
        if tries >= 256:
            break
        trial = list(species)
        for i, alt in zip(amb, combo):
            trial[i] = alt
        try:
            valid.append((combo, _balance_core(trial[:len(r_sp)], trial[len(r_sp):], medium)))
        except ValueError as e:
            first_error = first_error or e
    if not valid:
        raise first_error
    combo, res = valid[0]
    notes = []
    for k, (i, alt) in enumerate(zip(amb, combo)):
        shown = alt.display(with_state=False)
        others = sorted({c[k].display(with_state=False) for c, _ in valid[1:]} - {shown})
        if others:
            notes.append(f"Read '{species[i].text}' as {shown}; as written it could also be "
                         f"{', '.join(others)}. Type {alt.formula}^{_ascii_charge(alt.charge)} "
                         f"to be explicit.")
    res["notes"] = notes
    return res


def _balance_core(r_sp, p_sp, medium):
    both = {(s.formula, s.charge) for s in r_sp} & {(s.formula, s.charge) for s in p_sp}
    if both:
        names = ", ".join(sorted(f + format_charge(q) for f, q in both))
        raise ValueError(f"{names} appears on both sides; write each species on one side only.")

    extras = []
    if medium:
        present = {(s.formula, s.charge) for s in r_sp + p_sp}
        wanted = [("H2O", 0), ("H", 1)] if medium == "acidic" else [("H2O", 0), ("OH", -1)]
        for formula, charge in wanted:
            if (formula, charge) not in present:
                extras.append(Species(formula, parse_formula(formula), charge))

    try:
        ints = _solve(r_sp, p_sp, extras)
    except _MultipleSolutions:
        # Water/H+/OH- can take part in the redox (e.g. H2O2 + MnO4-), so
        # the atom balance alone is not unique: use the half-equation method.
        if any(s.is_electron for s in r_sp + p_sp):
            raise ValueError(_MULTI_MSG)
        ints = _solve_by_half_equations(r_sp, p_sp, extras, medium)
    except _NoSolution:
        hint = ""
        if (any(s.charge for s in r_sp + p_sp) and not medium
                and not any(s.is_electron for s in r_sp + p_sp)):
            hint = (" Check the charges: half-equations need e-, and redox "
                    "equations in solution may need the acidic/basic option.")
        raise ValueError("No solution found for the given equation." + hint)
    n_orig = len(r_sp) + len(p_sp)

    r_out = list(zip(ints[:len(r_sp)], r_sp))
    p_out = list(zip(ints[len(r_sp):n_orig], p_sp))
    added = []
    for c, s in zip(ints[n_orig:], extras):
        if c > 0:
            r_out.append((c, s))
        elif c < 0:
            p_out.append((-c, s))
        if c:
            added.append(s.display())

    return {
        "reactants": r_out,
        "products": p_out,
        "equation": format_equation(r_out, p_out),
        "added": added,
    }


def format_equation(r_out, p_out):
    side = lambda terms: " + ".join(f"{'' if c == 1 else c}{s.display()}" for c, s in terms)
    return f"{side(r_out)} → {side(p_out)}"


def balance_equation(reactants, products):
    """Balance a chemical equation given lists of reactants and products.
    Returns (reactant_coeffs, product_coeffs) in the order given."""
    res = balance_full(reactants, products)
    return [c for c, _ in res["reactants"]], [c for c, _ in res["products"]]


def equation_balancer_menu():
    while True:
        print("\n--- Chemical Equation Balancer ---")
        print("Examples: H2 + O2 -> H2O")
        print("          MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+   (then choose 'acidic')")
        print("          Fe^3+ + e- -> Fe^2+")
        print("Type '0' or 'exit' to return to Main Menu.")
        equation = input("Enter the unbalanced equation: ").strip()

        if equation.lower() in ("0", "exit"):
            break

        if not equation:
            print("[ERROR] Please enter an equation.")
            continue

        try:
            reactants, products = parse_equation(equation)
            medium = None
            charged = any(parse_species(s).charge for s in reactants + products)
            if charged:
                m = input("Reaction medium - (a)cidic, (b)asic, or Enter for none: ").strip().lower()
                medium = {"a": "acidic", "acidic": "acidic", "b": "basic", "basic": "basic"}.get(m)

            res = balance_full(reactants, products, medium)
            print(f"\n[OK] Balanced Equation: {res['equation']}\n")
            if res["added"]:
                print(f"     Added for {medium} solution: {', '.join(res['added'])}")
            for note in res["notes"]:
                print(f"     Note: {note}")

            if not charged:
                do_moles = input("Do a mole conversion for this equation? (y/n): ").strip().lower()
                if do_moles == 'y':
                    mole_conversion_menu([s.formula for _, s in res["reactants"]],
                                         [s.formula for _, s in res["products"]],
                                         [c for c, _ in res["reactants"]],
                                         [c for c, _ in res["products"]])

        except Exception as e:
            print(f"[ERROR] {e}")
            print("Make sure you input the equation correctly, e.g., H2 + O2 -> H2O")
            continue
