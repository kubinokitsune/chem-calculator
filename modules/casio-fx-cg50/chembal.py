# chembal.py - equation balancer for the Casio (no sympy)
#
# Each element is a row and each species a column; reactants count negative and
# products positive. Balancing the equation means finding the null space of that
# matrix, which is done here with exact fractions (pairs of integers) so there
# is no rounding error.

from chemcore import (fmt, line, ask_text, ask_choice, parse_formula, capitalise, gcd)


def _norm(n, d):
    if d < 0:
        n, d = -n, -d
    g = gcd(n, d) or 1
    return (n // g, d // g)


def _add(a, b):
    return _norm(a[0] * b[1] + b[0] * a[1], a[1] * b[1])


def _mul(a, b):
    return _norm(a[0] * b[0], a[1] * b[1])


def _sub(a, b):
    return _add(a, (-b[0], b[1]))


def _div(a, b):
    if b[0] == 0:
        raise ValueError("Divide by zero")
    return _norm(a[0] * b[1], a[1] * b[0])


def null_space(rows, width):
    """One null-space vector of a matrix of fractions, or None."""
    m = [[_norm(v, 1) for v in row] for row in rows]
    pivots = []
    r = 0
    for c in range(width):
        pick = None
        for i in range(r, len(m)):
            if m[i][c][0] != 0:
                pick = i
                break
        if pick is None:
            continue
        m[r], m[pick] = m[pick], m[r]
        lead = m[r][c]
        m[r] = [_div(v, lead) for v in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c][0] != 0:
                factor = m[i][c]
                m[i] = [_sub(v, _mul(factor, m[r][j])) for j, v in enumerate(m[i])]
        pivots.append(c)
        r += 1
        if r == len(m):
            break
    free = [c for c in range(width) if c not in pivots]
    if len(free) != 1:
        return None if not free else False      # False: more than one answer
    f = free[0]
    vec = [(0, 1)] * width
    vec[f] = (1, 1)
    for i, c in enumerate(pivots):
        vec[c] = (-m[i][f][0], m[i][f][1])
    # scale to whole numbers
    lcm = 1
    for n, d in vec:
        lcm = lcm * d // (gcd(lcm, d) or 1)
    ints = [n * lcm // d for n, d in vec]
    g = 0
    for v in ints:
        g = gcd(g, v)
    if g > 1:
        ints = [v // g for v in ints]
    if all([v <= 0 for v in ints]):
        ints = [-v for v in ints]
    return ints


def balance(reactants, products):
    """Lists of formulas -> (reactant coefficients, product coefficients)."""
    species = reactants + products
    counts = [parse_formula(s) for s in species]
    elements = []
    for c in counts:
        for el in c:
            if el not in elements:
                elements.append(el)
    elements.sort()
    n_r = len(reactants)
    rows = []
    for el in elements:
        row = []
        for j, c in enumerate(counts):
            value = c.get(el, 0)
            row.append(-value if j < n_r else value)
        rows.append(row)
    vec = null_space(rows, len(species))
    if vec is None:
        raise ValueError("No solution - check the equation")
    if vec is False:
        raise ValueError("More than one answer - split the equation")
    for v in vec:
        if v <= 0:
            raise ValueError("A species is on the wrong side")
    return vec[:n_r], vec[n_r:]


def split_side(text):
    return [part.strip() for part in text.split("+") if part.strip()]


def menu_balance():
    print("EQUATION BALANCER")
    print("Type both sides, e.g.")
    print("  left:  C2H5OH + O2")
    print("  right: CO2 + H2O")
    left = ask_text("left:  ")
    right = ask_text("right: ")
    reactants = [capitalise(s) for s in split_side(left)]
    products = [capitalise(s) for s in split_side(right)]
    if not reactants or not products:
        print("Need both sides")
        return
    r_coeffs, p_coeffs = balance(reactants, products)
    line()
    out = ""
    for i, name in enumerate(reactants):
        if i:
            out += " + "
        out += ("" if r_coeffs[i] == 1 else str(r_coeffs[i])) + name
    out += " -> "
    for i, name in enumerate(products):
        if i:
            out += " + "
        out += ("" if p_coeffs[i] == 1 else str(p_coeffs[i])) + name
    # the screen is 29 characters wide, so wrap the answer
    while len(out) > 27:
        cut = out.rfind(" ", 0, 27)
        if cut <= 0:
            cut = 27
        print(out[:cut])
        out = "  " + out[cut:].strip()
    print(out)


MENU = [("1", "Balance an equation", menu_balance)]
