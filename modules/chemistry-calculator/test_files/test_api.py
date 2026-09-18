"""
Front-end ↔ back-end contract tests for ui_interface/app.py.

Each request mirrors what index.html sends (values are strings taken straight
from the input boxes), and each check reads the same response fields the page
reads. Also verifies that:
  * every /api/... URL used by index.html exists as a POST route,
  * every response is strict JSON (no NaN / Infinity, which browsers reject),
  * bad input comes back as {error: ...} with HTTP 400, never a 500.

Run:  py test_files/test_api.py      (needs flask: py -m pip install -r requirements.txt)
"""

import sys, os, re, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ui_interface"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import app as webapp

client = webapp.app.test_client()
PASS = FAIL = 0
FAILURES = []


def _record(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}" + (f"\n         {detail}" if detail else "")
        FAILURES.append(msg)
        print(msg)


def _reject_constant(name):
    raise ValueError(f"non-standard JSON constant {name}")


def call(url, body):
    """POST like the page does; return (status, parsed strict JSON or None)."""
    resp = client.post(url, json=body)
    text = resp.get_data(as_text=True)
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except ValueError as e:
        return resp.status_code, {"__invalid_json__": f"{e}: {text[:120]}"}
    return resp.status_code, data


def ok(label, url, body, **expect):
    """Expect success. `expect` maps a response field to a value (3 s.f. match
    for numbers), a callable predicate, or ... (field must just exist)."""
    status, d = call(url, body)
    if "__invalid_json__" in d:
        return _record(label, False, d["__invalid_json__"])
    if status != 200 or "error" in d:
        return _record(label, False, f"status={status} body={d}")
    for field, want in expect.items():
        if field not in d:
            return _record(label, False, f"missing field '{field}' in {sorted(d)}")
        got = d[field]
        if want is ...:
            continue
        if callable(want):
            good = want(got)
        elif isinstance(want, float):
            good = isinstance(got, (int, float)) and math.isclose(got, want, rel_tol=5e-3)
        else:
            good = got == want
        if not good:
            return _record(label, False, f"{field}: got={got!r} expected={want!r}")
    _record(label, True)
    return d


def err(label, url, body):
    """Expect a clean 400 with a readable error message."""
    status, d = call(url, body)
    if "__invalid_json__" in d:
        return _record(label, False, d["__invalid_json__"])
    good = status == 400 and isinstance(d.get("error"), str) and d["error"].strip() != ""
    _record(label, good, f"status={status} body={d}")
    return d


def section(t):
    print(f"\n=== {t} ===")


TEXT = dict(compact=lambda v: isinstance(v, str) and v, detailed=lambda v: isinstance(v, list) and v)

# ─────────────────────────────────────────────────────────────────────────────
section("Contract: every URL the page calls is a POST route")


def page_source():
    """index.html + the split-out static/style.css and static/app.js."""
    parts = []
    for rel in (("index.html",), ("static", "style.css"), ("static", "app.js")):
        parts.append(open(os.path.join(ROOT, "ui_interface", *rel), encoding="utf-8").read())
    return "\n".join(parts)


html = page_source()
urls = sorted(set(re.findall(r"post\('(/api/[a-z_]+)'", html)))
_record("page is split into index.html + static/style.css + static/app.js",
        all(os.path.exists(os.path.join(ROOT, "ui_interface", *rel))
            for rel in (("index.html",), ("static", "style.css"), ("static", "app.js"), ("static", "fonts"))))
_record("index.html links the split files",
        'href="static/style.css"' in open(os.path.join(ROOT, "ui_interface", "index.html"), encoding="utf-8").read()
        and 'src="static/app.js"' in open(os.path.join(ROOT, "ui_interface", "index.html"), encoding="utf-8").read())
routes = {r.rule: r.methods for r in webapp.app.url_map.iter_rules()}
for u in urls:
    _record(f"route exists: {u}", u in routes and "POST" in routes[u])
status = client.get("/").status_code
_record("GET / serves index.html", status == 200, f"status={status}")

# ─────────────────────────────────────────────────────────────────────────────
section("1 Mole conversions")
ok("mass→moles 10.0 g CaCO3", "/api/mole", {"type": "mass_to_moles", "a": "10.0", "b": "100.09"},
   result=0.0999, **TEXT)
ok("moles→volume at STP", "/api/mole", {"type": "moles_to_volume", "a": "0.500"}, result=11.35)
err("blank value", "/api/mole", {"type": "mass_to_moles", "a": "", "b": "18"})
err("molar mass 0", "/api/mole", {"type": "mass_to_moles", "a": "5", "b": "0"})

section("2 Empirical formula")
ok("C 85.7 / H 14.3", "/api/empirical", {"elements": ["C", "H"], "masses": ["85.7", "14.3"]},
   formula="CH2", **TEXT)
ok("Fe 72.4 / O 27.6 (needs ×3)", "/api/empirical", {"elements": ["Fe", "O"], "masses": ["72.4", "27.6"]},
   formula="Fe3O4")
ok("lowercase symbols", "/api/empirical", {"elements": ["c", "h", "o"], "masses": ["40.0", "6.7", "53.3"]},
   formula="CH2O")
err("unknown element", "/api/empirical", {"elements": ["Xx"], "masses": ["10"]})
err("blank mass", "/api/empirical", {"elements": ["C", "H"], "masses": ["85.7", ""]})

section("3 Equation balancer")
ok("ethanol combustion", "/api/equation", {"equation": "C2H5OH + O2 -> CO2 + H2O"},
   balanced="C2H5OH + 3O2 → 2CO2 + 3H2O", **TEXT)
ok("with brackets", "/api/equation", {"equation": "H3PO4 + Ca(OH)2 -> Ca3(PO4)2 + H2O"},
   balanced="2H3PO4 + 3Ca(OH)2 → Ca3(PO4)2 + 6H2O")
ok("typed in lowercase", "/api/equation", {"equation": "nh3 + o2 -> no + h2o"},
   balanced="4NH3 + 5O2 → 4NO + 6H2O")
ok("arrow typed as →", "/api/equation", {"equation": "H2 + O2 → H2O"},
   balanced="2H2 + O2 → 2H2O")
err("no arrow", "/api/equation", {"equation": "H2 + O2"})
err("impossible", "/api/equation", {"equation": "H2 -> O2"})

section("4 Limiting reactant")
ok("N2 + 3H2 -> 2NH3", "/api/limiting",
   {"reactants": [{"name": "N2", "coeff": "1", "moles": "2.0"}, {"name": "H2", "coeff": "3", "moles": "3.0"}],
    "products": [{"name": "NH3", "coeff": "2"}]},
   limiting="H2", yields={"NH3": 2.0}, **TEXT)
err("blank coefficient", "/api/limiting",
    {"reactants": [{"name": "N2", "coeff": "", "moles": "2"}], "products": [{"name": "NH3", "coeff": "2"}]})
err("zero coefficient", "/api/limiting",
    {"reactants": [{"name": "N2", "coeff": "0", "moles": "2"}], "products": [{"name": "NH3", "coeff": "2"}]})

section("5 Percent composition")
ok("H2O", "/api/percent", {"formula": "H2O"}, percents=lambda p: abs(p["O"] - 88.81) < 0.05, **TEXT)
ok("hydrate with dot", "/api/percent", {"formula": "CuSO4.5H2O"}, molar_mass=lambda m: abs(m - 249.7) < 0.3)
ok("lowercase nh4cl", "/api/percent", {"formula": "nh4cl"}, molar_mass=lambda m: abs(m - 53.49) < 0.05)
err("bad formula", "/api/percent", {"formula": "Ca(OH"})

section("6 Volume / mass")
ok("density", "/api/volume", {"type": "density", "a": "10", "b": "4"}, result=2.5, **TEXT)
err("zero density", "/api/volume", {"type": "mass_to_volume", "a": "10", "b": "0"})

section("7 Oxidation numbers")
ok("Cr in K2Cr2O7", "/api/oxidation", {"formula": "K2Cr2O7", "charge": 0, "peroxide": False},
   numbers=lambda n: n["Cr"] == 6, **TEXT)
ok("Mn in MnO4-", "/api/oxidation", {"formula": "MnO4", "charge": -1, "peroxide": False},
   numbers=lambda n: n["Mn"] == 7)
ok("lowercase kmno4", "/api/oxidation", {"formula": "kmno4", "charge": 0, "peroxide": False},
   numbers=lambda n: n.get("Mn") == 7)
err("charge NaN from parseInt('abc')", "/api/oxidation", {"formula": "SO4", "charge": None, "peroxide": False})

section("8 Atom economy")
ok("fermentation", "/api/atom_eco",
   {"reactants": [{"formula": "C6H12O6", "coeff": "1"}], "desired": {"formula": "C2H5OH", "coeff": "2"}},
   atom_economy=51.15, **TEXT)
err("unknown element", "/api/atom_eco",
    {"reactants": [{"formula": "Qq", "coeff": "1"}], "desired": {"formula": "H2O", "coeff": "1"}})

section("9 Ionic bonding")
ok("classify Na Cl", "/api/ionic", {"action": "classify", "elem1": "Na", "elem2": "Cl"}, bond_type="Ionic", **TEXT)
ok("classify lowercase", "/api/ionic", {"action": "classify", "elem1": "na", "elem2": "cl"}, bond_type="Ionic")
ok("Ca2+ PO4 3-", "/api/ionic", {"action": "formula", "cation": "Ca", "cation_charge": "2",
                                "anion": "PO4", "anion_charge": "-3"}, formula="Ca3(PO4)2")
ok("charge typed +2", "/api/ionic", {"action": "formula", "cation": "Mg", "cation_charge": "+2",
                                     "anion": "N", "anion_charge": "-3"}, formula="Mg3N2")
err("blank charge", "/api/ionic", {"action": "formula", "cation": "Mg", "cation_charge": "",
                                   "anion": "N", "anion_charge": "-3"})

section("10 Percentage yield")
ok("percent", "/api/yield_calc", {"type": "percent", "a": "7.50", "b": "10.0"}, result=75.0, **TEXT)
err("zero theoretical", "/api/yield_calc", {"type": "percent", "a": "7.5", "b": "0"})

section("11 Periodic table")
ok("symbol fe", "/api/periodic", {"type": "symbol", "query": "fe"}, found=True, number=26, **TEXT)
ok("name Iron", "/api/periodic", {"type": "name", "query": "Iron"}, found=True, symbol="Fe")
ok("unknown returns found=false", "/api/periodic", {"type": "symbol", "query": "Zz"}, found=False)
err("number not an integer", "/api/periodic", {"type": "number", "query": "abc"})

section("12 Gas laws")
ok("ideal P", "/api/gas_laws", {"type": "ideal", "solve": "P", "n": "0.0100", "v": "0.250", "T": "298", "p": ""},
   result=0.978, unit="atm")
ok("combined V2", "/api/gas_laws", {"type": "combined", "solve": "V2", "P1": "100", "V1": "2.00", "T1": "300",
                                    "P2": "150", "V2": "", "T2": "400"}, result=1.78)
ok("graham", "/api/gas_laws", {"type": "graham", "M1": "2.016", "M2": "32.00"}, result=3.98)
ok("dalton", "/api/gas_laws", {"type": "dalton", "gases": [{"name": "N2", "p": "0.78"}, {"name": "O2", "p": "0.21"}]},
   total=0.99, **TEXT)
ok("mixing Pf", "/api/gas_laws", {"type": "mixing", "solve": "Pf", "P1": "1", "V1": "1", "T1": "298",
                                  "P2": "1", "V2": "1", "T2": "298", "Vf": "2", "Tf": "298"}, result=1.0)
err("ideal P with missing n", "/api/gas_laws", {"type": "ideal", "solve": "P", "n": "", "v": "1", "T": "298", "p": ""})
err("ideal V with P = 0", "/api/gas_laws", {"type": "ideal", "solve": "V", "n": "1", "v": "", "T": "298", "p": "0"})

section("13 Acid-base")
ok("strong acid", "/api/acid_base", {"type": "strong_acid", "conc": "0.0100"}, pH=2.0, pOH=12.0, H=..., OH=...)
ok("weak acid", "/api/acid_base", {"type": "weak_acid", "Ka": "1.74e-5", "conc": "0.100"}, pH=2.88)
ok("weak base", "/api/acid_base", {"type": "weak_base", "Kb": "1.78e-5", "conc": "0.100"}, pH=11.12)
ok("buffer", "/api/acid_base", {"type": "buffer", "Ka": "1.74e-5", "acid": "0.100", "base": "0.200"}, pH=5.06)
ok("pH convert", "/api/acid_base", {"type": "ph_convert", "input_type": "pH", "value": "3.50"}, H=3.16e-4)
ok("identify", "/api/acid_base", {"type": "identify", "formula": "hno3"}, identity="Strong acid", formula=...)
err("negative concentration", "/api/acid_base", {"type": "strong_acid", "conc": "-1"})
err("Ka zero", "/api/acid_base", {"type": "weak_acid", "Ka": "0", "conc": "0.1"})

section("14 Thermodynamics")
ok("calorimetry q", "/api/thermo", {"type": "calorimetry", "solve": "q", "q": "", "m": "50.0", "c": "4.18", "dT": "12.0"},
   result=2508.0, unit="J")
ok("calorimetry with ΔT = 0 typed as '0'", "/api/thermo",
   {"type": "calorimetry", "solve": "q", "q": "", "m": "50", "c": "4.18", "dT": "0"}, result=0.0)
ok("hess", "/api/thermo", {"type": "hess", "steps": [{"dH": "-393.5", "mult": "1"}, {"dH": "-283.0", "mult": "-1"}]},
   result=-110.5)
ok("bond enthalpy from table", "/api/thermo", {"type": "bond",
   "broken": [{"bond": "C-H", "count": "4", "kJ": ""}, {"bond": "O=O", "count": "2", "kJ": ""}],
   "formed": [{"bond": "C=O", "count": "2", "kJ": ""}, {"bond": "O-H", "count": "4", "kJ": ""}]},
   result=-808.0, sum_broken=2652.0, sum_formed=3460.0)
# IB gives ΔS in J K-1 mol-1: ΔH = -92.2 kJ, ΔS = -199 J/K, 298 K  ->  ΔG = -32.9 kJ
ok("gibbs with IB units (ΔS in J/K)", "/api/thermo", {"type": "gibbs", "dH": "-92.2", "dS": "-199", "T": "298"},
   result=-32.9, spontaneous=True)
err("bond not in table", "/api/thermo", {"type": "bond", "broken": [{"bond": "Xx-Yy", "count": "1", "kJ": ""}],
                                         "formed": []})
err("calorimetry missing m", "/api/thermo", {"type": "calorimetry", "solve": "q", "q": "", "m": "", "c": "4.18", "dT": "5"})

section("15 ICE solver")
d = ok("H2 + I2 ⇌ 2HI", "/api/ice", {"reactants": [{"name": "H2", "coeff": "1", "initial": "1.00"},
                                                    {"name": "I2", "coeff": "1", "initial": "1.00"}],
                                      "products": [{"name": "HI", "coeff": "2", "initial": "0"}], "Kc": "50"},
       x=0.7795, Q_final=50.0, approx_pct=..., r_eq=..., p_eq=..., r_names=..., p_names=...)
ok("start from product only (reverse)", "/api/ice",
   {"reactants": [{"name": "H2", "coeff": "1", "initial": "0"}, {"name": "I2", "coeff": "1", "initial": "0"}],
    "products": [{"name": "HI", "coeff": "2", "initial": "1.00"}], "Kc": "50"},
   Q_final=50.0, x=lambda x: x < 0)
err("nothing can react", "/api/ice",
    {"reactants": [{"name": "A", "coeff": "1", "initial": "0"}],
     "products": [{"name": "B", "coeff": "1", "initial": "0"}], "Kc": "5"})

section("16 Electrochemistry")
ok("Daniell cell", "/api/electrochem", {"type": "cell", "E_cat": "0.34", "E_ano": "-0.76", "n": "2"},
   E_cell=1.10, dG=-212.3, spontaneity=..., cell_type=...)
ok("Faraday mass", "/api/electrochem", {"type": "faraday", "solve": "mass", "mass": "", "I": "2.00",
                                        "t": "1930", "M": "63.55", "n": "2"}, result=1.271, unit="g")
ok("Nernst", "/api/electrochem", {"type": "nernst", "E0": "1.10", "n": "2", "Q": "10", "T": "298.15"}, E=1.0704)
err("n blank", "/api/electrochem", {"type": "cell", "E_cat": "0.34", "E_ano": "-0.76", "n": ""})
err("Nernst Q = 0", "/api/electrochem", {"type": "nernst", "E0": "1.1", "n": "2", "Q": "0", "T": "298"})

section("17 Kinetics")
ok("order", "/api/kinetics", {"type": "order", "c1": "0.10", "c2": "0.20", "r1": "1.0e-3", "r2": "4.0e-3"},
   order=2.0, k=0.1, k_units=...)
ok("Arrhenius Ea", "/api/kinetics", {"type": "arrhenius", "solve": "Ea", "k1": "1.0e-3", "T1": "300",
                                     "k2": "4.0e-3", "T2": "320", "Ea": ""}, Ea_kJ=55.3, Ea_J=...)
ok("Arrhenius k2", "/api/kinetics", {"type": "arrhenius", "solve": "k2", "k1": "1.0e-3", "T1": "300",
                                     "k2": "", "T2": "320", "Ea": "55300"}, k2=4.0e-3)
ok("half-life", "/api/kinetics", {"type": "halflife", "solve": "t_half", "k": "0.0231", "t_half": ""}, t_half=30.0)
ok("k units", "/api/kinetics", {"type": "kunits", "order": "2"}, order=2, units=...)
err("half-life k = 0", "/api/kinetics", {"type": "halflife", "solve": "t_half", "k": "0", "t_half": ""})
err("same temperatures", "/api/kinetics", {"type": "arrhenius", "solve": "Ea", "k1": "1", "T1": "300",
                                           "k2": "2", "T2": "300", "Ea": ""})

section("Batch 1 — moles: molar mass from a formula")
ok("10.0 g CaCO3 (formula instead of M)", "/api/mole", {"type": "mass_to_moles", "a": "10.0", "b": "CaCO3"},
   result=0.0999, detailed=lambda d: "CaCO3" in d[0])
ok("2.00 mol h2o (lower case)", "/api/mole", {"type": "moles_to_mass", "a": "2.00", "b": "h2o"}, result=36.03)
ok("number still works", "/api/mole", {"type": "moles_to_mass", "a": "2", "b": "18.02"}, result=36.04)
err("not a number or formula", "/api/mole", {"type": "mass_to_moles", "a": "10", "b": "Xq"})

section("Batch 1 — thermodynamics")
CH4 = [{"formula": "CH4", "coeff": "1", "dHf": "-74.0", "role": "reactant"},
       {"formula": "O2", "coeff": "2", "dHf": "0", "role": "reactant"},
       {"formula": "CO2", "coeff": "1", "dHf": "-393.5", "role": "product"},
       {"formula": "H2O", "coeff": "2", "dHf": "-285.8", "role": "product"}]
ok("ΔH°rxn of CH4 combustion from ΔHf", "/api/thermo", {"type": "std_enthalpy", "species": CH4},
   result=-891.1, sum_products=-965.1, sum_reactants=-74.0, warnings=[], **TEXT)
bad_o2 = [dict(x) for x in CH4]
bad_o2[1]["dHf"] = "-10"
ok("warns when an element's ΔHf isn't 0", "/api/thermo", {"type": "std_enthalpy", "species": bad_o2},
   warnings=lambda w: any("O2" in x for x in w))
ok("blank coefficient counts as 1", "/api/thermo", {"type": "std_enthalpy", "species": [
    {"formula": "N2O4", "coeff": "", "dHf": "9.2", "role": "reactant"},
    {"formula": "NO2", "coeff": "2", "dHf": "33.2", "role": "product"}]}, result=57.2)
err("needs a product", "/api/thermo", {"type": "std_enthalpy", "species": CH4[:2]})
err("blank ΔHf", "/api/thermo", {"type": "std_enthalpy", "species": [
    {"formula": "CH4", "coeff": "1", "dHf": "", "role": "reactant"}, CH4[2]]})
err("bad role", "/api/thermo", {"type": "std_enthalpy", "species": [
    {"formula": "CH4", "coeff": "1", "dHf": "1", "role": "catalyst"}, CH4[2]]})
err("negative coefficient", "/api/thermo", {"type": "std_enthalpy", "species": [
    {"formula": "CH4", "coeff": "-1", "dHf": "1", "role": "reactant"}, CH4[2]]})

ok("ΔG° from K = 1.00e3 at 298 K", "/api/thermo", {"type": "gibbs_k", "solve": "dG", "K": "1.00e3", "T": "298"},
   result=-17.11, **TEXT)
ok("K from ΔG° = −32.9 kJ at 298 K", "/api/thermo", {"type": "gibbs_k", "solve": "K", "dG": "-32.9", "T": "298"},
   result=5.85e5)
ok("K = 1 gives ΔG° = 0", "/api/thermo", {"type": "gibbs_k", "solve": "dG", "K": "1", "T": "298"},
   result=lambda v: abs(v) < 1e-12, detailed=lambda d: "neither" in d[-1])
ok("blank T defaults to 298.15 K", "/api/thermo", {"type": "gibbs_k", "solve": "dG", "K": "10", "T": ""},
   result=-8.314 * 298.15 * math.log(10) / 1000)
ok("positive ΔG° gives K < 1", "/api/thermo", {"type": "gibbs_k", "solve": "K", "dG": "10", "T": "298"},
   result=lambda v: 0 < v < 1)
err("K = 0", "/api/thermo", {"type": "gibbs_k", "solve": "dG", "K": "0", "T": "298"})
err("K too large to show", "/api/thermo", {"type": "gibbs_k", "solve": "K", "dG": "-5000", "T": "298"})
err("T = 0", "/api/thermo", {"type": "gibbs_k", "solve": "dG", "K": "5", "T": "0"})
err("unknown target", "/api/thermo", {"type": "gibbs_k", "solve": "x", "K": "5"})

ok("Haber: spontaneous below 463 K", "/api/thermo", {"type": "spontaneity", "dH": "-92.2", "dS": "-199"},
   T_crossover=463.3, compact=lambda c: "low T" in c)
ok("endothermic + entropy up: spontaneous above crossover", "/api/thermo",
   {"type": "spontaneity", "dH": "178", "dS": "161"}, T_crossover=1105.6, detailed=lambda d: "above" in d[-1])
ok("always spontaneous: no crossover", "/api/thermo", {"type": "spontaneity", "dH": "-100", "dS": "50"},
   T_crossover=None, compact=lambda c: c.startswith("Always"))
ok("ΔH = 0, ΔS > 0 is always spontaneous", "/api/thermo", {"type": "spontaneity", "dH": "0", "dS": "10"},
   compact=lambda c: c.startswith("Always"))
ok("ΔH > 0, ΔS = 0 is never spontaneous", "/api/thermo", {"type": "spontaneity", "dH": "10", "dS": "0"},
   compact=lambda c: c.startswith("Never"))
err("blank ΔS", "/api/thermo", {"type": "spontaneity", "dH": "10", "dS": ""})

section("Batch 1 — equilibrium tools")
ok("Kc → Kp, Δn = −2, 500 K", "/api/ice", {"type": "kc_kp", "solve": "Kp", "K": "0.500", "T": "500", "delta_n": "-2"},
   result=2.97e-4, **TEXT)
ok("Kp → Kc undoes it", "/api/ice", {"type": "kc_kp", "solve": "Kc", "K": str(0.5 * (0.08206 * 500) ** -2),
                                     "T": "500", "delta_n": "-2"}, result=0.5)
ok("Δn = 0 → Kp = Kc with a note", "/api/ice", {"type": "kc_kp", "solve": "Kp", "K": "4", "T": "300", "delta_n": "0"},
   result=4.0, warnings=lambda w: len(w) == 1)
err("T blank", "/api/ice", {"type": "kc_kp", "solve": "Kp", "K": "4", "T": "", "delta_n": "1"})
err("K negative", "/api/ice", {"type": "kc_kp", "solve": "Kp", "K": "-4", "T": "300", "delta_n": "1"})

HI_R = [{"name": "H2", "coeff": "1", "initial": "0.20"}, {"name": "I2", "coeff": "1", "initial": "0.20"}]
HI_P = [{"name": "HI", "coeff": "2", "initial": "1.0"}]
ok("Q = 25 < K = 50 → forward", "/api/ice", {"type": "q_vs_k", "reactants": HI_R, "products": HI_P, "Kc": "50"},
   Q=25.0, direction="forward", **TEXT)
ok("Q > K → reverse", "/api/ice", {"type": "q_vs_k", "reactants": HI_R, "products": HI_P, "Kc": "10"},
   direction="reverse")
ok("Q = K → equilibrium", "/api/ice", {"type": "q_vs_k", "reactants": HI_R, "products": HI_P, "Kc": "25"},
   direction="equilibrium")
ok("reactant at zero: Q infinite (sent as null) → reverse", "/api/ice",
   {"type": "q_vs_k", "reactants": [{"name": "A", "coeff": "1", "initial": "0"}],
    "products": [{"name": "B", "coeff": "1", "initial": "1"}], "Kc": "5"}, Q=None, direction="reverse")
err("all zero", "/api/ice", {"type": "q_vs_k", "reactants": [{"name": "A", "coeff": "1", "initial": "0"}],
                             "products": [{"name": "B", "coeff": "1", "initial": "0"}], "Kc": "5"})
err("negative concentration", "/api/ice", {"type": "q_vs_k", "reactants": [{"name": "A", "coeff": "1", "initial": "-1"}],
                                           "products": HI_P, "Kc": "5"})
err("ICE table: negative initial", "/api/ice", {"type": "table", "reactants": [{"name": "A", "coeff": "1", "initial": "-1"}],
                                                "products": HI_P, "Kc": "5"})
err("ICE table: zero coefficient", "/api/ice", {"reactants": [{"name": "A", "coeff": "0", "initial": "1"}],
                                                "products": HI_P, "Kc": "5"})
err("ICE table: Kc = 0", "/api/ice", {"reactants": HI_R, "products": HI_P, "Kc": "0"})

LC = "/api/ice"
for label, body, want_dir, want_k in [
    ("add reactant → right", {"disturbance": "concentration", "role": "reactant", "change": "increase"}, "right", "unchanged"),
    ("remove product → right", {"disturbance": "concentration", "role": "product", "change": "decrease"}, "right", "unchanged"),
    ("add product → left", {"disturbance": "concentration", "role": "product", "change": "increase"}, "left", "unchanged"),
    ("more pressure, Δn = −2 → right", {"disturbance": "pressure", "change": "increase", "delta_n": "-2"}, "right", "unchanged"),
    ("more pressure, Δn = +1 → left", {"disturbance": "pressure", "change": "increase", "delta_n": "1"}, "left", "unchanged"),
    ("less pressure, Δn = −2 → left", {"disturbance": "pressure", "change": "decrease", "delta_n": "-2"}, "left", "unchanged"),
    ("pressure, Δn = 0 → none", {"disturbance": "pressure", "change": "increase", "delta_n": "0"}, "none", "unchanged"),
    ("heat exothermic → left, K down", {"disturbance": "temperature", "change": "increase", "rxn_type": "exothermic"}, "left", "decreases"),
    ("cool exothermic → right, K up", {"disturbance": "temperature", "change": "decrease", "rxn_type": "exothermic"}, "right", "increases"),
    ("heat endothermic → right, K up", {"disturbance": "temperature", "change": "increase", "rxn_type": "endothermic"}, "right", "increases"),
    ("catalyst → none", {"disturbance": "catalyst"}, "none", "unchanged"),
]:
    ok(f"Le Chatelier: {label}", LC, {"type": "le_chatelier", **body}, direction=want_dir, k_effect=want_k, **TEXT)
err("Le Chatelier: no disturbance", LC, {"type": "le_chatelier", "disturbance": ""})
err("Le Chatelier: pressure without Δn", LC, {"type": "le_chatelier", "disturbance": "pressure", "change": "increase", "delta_n": ""})
err("Le Chatelier: bad reaction type", LC, {"type": "le_chatelier", "disturbance": "temperature", "change": "increase", "rxn_type": "warm"})

section("Batch 1 — integrated rate laws")
K = "/api/kinetics"
ok("1st order [A] after 60 s", K, {"type": "integrated", "order": "1", "solve": "At", "A0": "0.800", "k": "0.0231", "t": "60", "At": ""},
   result=0.2001, half_life=30.01, **TEXT)
ok("0th order [A]", K, {"type": "integrated", "order": "0", "solve": "At", "A0": "1.0", "k": "0.01", "t": "30", "At": ""},
   result=0.70, half_life=50.0)
ok("2nd order time to halve = t½", K, {"type": "integrated", "order": "2", "solve": "t", "A0": "0.5", "k": "0.1", "t": "", "At": "0.25"},
   result=20.0, half_life=20.0)
ok("1st order time to reach 25 %", K, {"type": "integrated", "order": "1", "solve": "t", "A0": "1", "k": "0.0231", "t": "", "At": "0.25"},
   result=60.01)
ok("t = 0 gives [A]0", K, {"type": "integrated", "order": "2", "solve": "At", "A0": "0.4", "k": "3", "t": "0", "At": ""}, result=0.4)
err("0th order used up before t", K, {"type": "integrated", "order": "0", "solve": "At", "A0": "1", "k": "1", "t": "5", "At": ""})
err("order 3", K, {"type": "integrated", "order": "3", "solve": "At", "A0": "1", "k": "1", "t": "5", "At": ""})
err("[A]t bigger than [A]0", K, {"type": "integrated", "order": "1", "solve": "t", "A0": "1", "k": "1", "t": "", "At": "2"})
err("k = 0", K, {"type": "integrated", "order": "1", "solve": "At", "A0": "1", "k": "0", "t": "5", "At": ""})
err("negative time", K, {"type": "integrated", "order": "1", "solve": "At", "A0": "1", "k": "1", "t": "-5", "At": ""})
err("blank [A]0", K, {"type": "integrated", "order": "1", "solve": "At", "A0": "", "k": "1", "t": "5", "At": ""})

section("Batch 1 — titration")
A = "/api/acid_base"
ok("HCl conc from 20.0 cm³ of 0.100 NaOH into 25.0 cm³", A,
   {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.100", "V_titrant": "20.0", "V_analyte": "25.0",
    "ratio_analyte": "1", "ratio_titrant": "1"}, result=0.0800, unit="mol/dm³", **TEXT)
ok("H2SO4 with 2 NaOH (ratio 1:2)", A,
   {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.100", "V_titrant": "20.0", "V_analyte": "25.0",
    "ratio_analyte": "1", "ratio_titrant": "2", "acid_strength": "strong", "base_strength": "strong"},
   result=0.0400, detailed=lambda d: "pH ≈ 7" in d[-1])
ok("volume of 0.100 NaOH for 25.0 cm³ of 0.0500 HCl", A,
   {"type": "titration", "solve": "titrant_volume", "C_titrant": "0.100", "C_analyte": "0.0500", "V_analyte": "25.0",
    "ratio_analyte": "1", "ratio_titrant": "1"}, result=12.5, unit="cm³")
ok("volume for H3PO4 + 3 NaOH", A,
   {"type": "titration", "solve": "titrant_volume", "C_titrant": "0.150", "C_analyte": "0.100", "V_analyte": "10.0",
    "ratio_analyte": "1", "ratio_titrant": "3"}, result=20.0)
ok("blank ratio means 1:1", A,
   {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.1", "V_titrant": "10", "V_analyte": "10",
    "ratio_analyte": "", "ratio_titrant": ""}, result=0.1)
ok("weak acid + strong base → pH > 7", A,
   {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.1", "V_titrant": "10", "V_analyte": "10",
    "acid_strength": "weak", "base_strength": "strong"}, detailed=lambda d: "pH > 7" in d[-1])
err("titrant volume missing", A, {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.1", "V_titrant": "", "V_analyte": "10"})
err("zero concentration", A, {"type": "titration", "solve": "titrant_volume", "C_titrant": "0", "C_analyte": "0.1", "V_analyte": "10"})
err("zero ratio", A, {"type": "titration", "solve": "analyte_conc", "C_titrant": "0.1", "V_titrant": "10", "V_analyte": "10",
                      "ratio_analyte": "0", "ratio_titrant": "1"})
err("unknown target", A, {"type": "titration", "solve": "pH", "C_titrant": "0.1", "V_analyte": "10"})

section("Batch 1 — electrochemistry half-cell picker")
resp = client.get("/api/reduction_potentials")
table = json.loads(resp.get_data(as_text=True))["half_cells"]
_record("half-cell table: 21 entries", len(table) == 21, f"{len(table)}")
_record("half-cell table sorted high → low", all(a["E"] >= b["E"] for a, b in zip(table, table[1:])))
E = "/api/electrochem"
ok("Daniell cell (order doesn't matter)", E, {"type": "cell_pick", "half1": "Zn2+/Zn", "half2": "Cu2+/Cu"},
   E_cell=1.10, n=2, dG=-212.3, cathode="Cu2+/Cu", anode="Zn2+/Zn",
   equation="Cu²⁺ + Zn → Cu + Zn²⁺", cell_type="galvanic", **TEXT)
ok("MnO4-/Fe2+ in acid, n = 5", E, {"type": "cell_pick", "half1": "MnO4-/Mn2+", "half2": "Fe3+/Fe2+"},
   E_cell=0.74, n=5, equation="MnO4⁻ + 5Fe²⁺ + 8H⁺ → Mn²⁺ + 5Fe³⁺ + 4H2O")
ok("Cr2O7 2- with hydrogen, n = 6", E, {"type": "cell_pick", "half1": "H+/H2", "half2": "Cr2O72-/Cr3+"},
   n=6, equation="Cr2O7²⁻ + 3H2 + 8H⁺ → 2Cr³⁺ + 7H2O")
ok("iron comproportionation", E, {"type": "cell_pick", "half1": "Fe2+/Fe", "half2": "Fe3+/Fe2+"},
   n=2, equation="2Fe³⁺ + Fe → 3Fe²⁺")
ok("silver / aluminium, n = 3", E, {"type": "cell_pick", "half1": "Ag+/Ag", "half2": "Al3+/Al"},
   E_cell=2.46, n=3, equation="3Ag⁺ + Al → 3Ag + Al³⁺")
err("same half-cell twice", E, {"type": "cell_pick", "half1": "Cu2+/Cu", "half2": "Cu2+/Cu"})
err("unknown half-cell", E, {"type": "cell_pick", "half1": "Xx/Yy", "half2": "Cu2+/Cu"})
err("missing half-cell", E, {"type": "cell_pick", "half1": "", "half2": "Cu2+/Cu"})

from equation_balancer import parse_species
import itertools as _it
bad_pairs = []
for a_, b_ in _it.permutations([h["label"] for h in table], 2):
    st, dd = call(E, {"type": "cell_pick", "half1": a_, "half2": b_})
    try:
        good = (st == 200 and dd["E_cell"] > 0 and dd["n"] >= 1 and not dd["warnings"]
                and math.isclose(dd["dG"], -dd["n"] * 96485 * dd["E_cell"] / 1000, rel_tol=1e-9)
                and dd["cathode"] != dd["anode"])
        # the overall equation must conserve atoms and charge (counted independently)
        if good:
            totals = []
            for side in dd["equation"].split(" → "):
                atoms, charge = {}, 0
                for term in side.split(" + "):
                    m_ = re.match(r"(\d*)(.+)", term)
                    coeff = int(m_.group(1) or 1)
                    sp_ = parse_species(m_.group(2))
                    for el, k in sp_.counts.items():
                        atoms[el] = atoms.get(el, 0) + coeff * k
                    charge += coeff * sp_.charge
                totals.append((atoms, charge))
            good = totals[0] == totals[1]
    except Exception:
        good = False
    if not good:
        bad_pairs.append((a_, b_, st, dd.get("error") or dd.get("warnings")))
_record(f"all {len(table) * (len(table) - 1)} half-cell pairs: E > 0, n ≥ 1, ΔG = −nFE, equation conserves atoms and charge",
        not bad_pairs, str(bad_pairs[:3]))

html_now = page_source()
for needle in ["type: 'std_enthalpy'", "type: t, solve: val('gkSolve')", "type: 'integrated'",
               "type: 'cell_pick'", "fetch('/api/reduction_potentials')", "type: tool, reactants",
               "val('tiSolve')", "val('lcDist')", "val('kpSolve')", 'id="mB" type="text"']:
    _record(f"page wires up: {needle}", needle in html_now)

section("Batch 2 — numeric answers for the significant-figures setting")


def answers_of(url, body):
    st, dd = call(url, body)
    return st, dd, {a["label"]: (a["value"], a["unit"]) for a in dd.get("answers", [])}


def ans_ok(label, url, body, expect, headline=None):
    """expect: {answer label: (value, unit)} — values compared to 0.1 %."""
    st, dd, got = answers_of(url, body)
    good = st == 200 and "__invalid_json__" not in dd
    detail = f"status={st} answers={got} headline={dd.get('headline')!r}"
    for k, (v, u) in expect.items():
        if k not in got or got[k][1] != u or not math.isclose(got[k][0], v, rel_tol=1e-3):
            good = False
    if headline is not None and dd.get("headline") != headline:
        good = False
    _record(label, good, detail)


ans_ok("mole: full-precision n", "/api/mole", {"type": "mass_to_moles", "a": "10.0", "b": "CaCO3"},
       {"Moles": (0.0999141, "mol")})
ans_ok("particles: no unit", "/api/mole", {"type": "moles_to_particles", "a": "0.25"}, {"Particles": (1.5055e23, "")})
ans_ok("volume: density not rounded to 4 d.p.", "/api/volume", {"type": "density", "a": "0.001", "b": "3"},
       {"Density": (0.000333333, "g/mL")})
ans_ok("% yield keeps the % unit", "/api/yield_calc", {"type": "percent", "a": "7.50", "b": "10.0"}, {"% Yield": (75.0, "%")})
ans_ok("limiting: grams + headline", "/api/limiting",
       {"unit": "g", "reactants": [{"name": "H2", "coeff": "", "amount": "4.0"}, {"name": "O2", "coeff": "", "amount": "16.0"}],
        "products": [{"name": "H2O", "coeff": ""}]},
       {"H2O (theoretical)": (18.0161, "g")}, headline="Limiting reactant: O2")
ans_ok("limiting: moles when no masses", "/api/limiting",
       {"unit": "mol", "reactants": [{"name": "Qa", "coeff": "1", "amount": "2"}], "products": [{"name": "Qb", "coeff": "3"}]},
       {"Qb (theoretical)": (6.0, "mol")})
ans_ok("percent composition: M and each %", "/api/percent", {"formula": "H2O"},
       {"M(H2O)": (18.015, "g/mol"), "% H": (11.1907, "%"), "% O": (88.8093, "%")})
ans_ok("atom economy full precision", "/api/atom_eco",
       {"reactants": [{"formula": "C6H12O6", "coeff": "1"}], "desired": {"formula": "C2H5OH", "coeff": "2"}},
       {"Atom economy": (51.1435, "%")})
ans_ok("gas ideal in kPa", "/api/gas_laws", {"type": "ideal", "solve": "P", "n": "0.0100", "v": "250", "T": "25", "p": "",
                                             "p_unit": "kPa", "v_unit": "cm3", "t_unit": "C"}, {"P": (99.153, "kPa")})
ans_ok("gas combined uses dm³ label", "/api/gas_laws", {"type": "combined", "solve": "V2", "P1": "100", "V1": "2", "T1": "27",
                                                        "P2": "150", "V2": "", "T2": "127", "p_unit": "kPa", "v_unit": "dm3",
                                                        "t_unit": "C"}, {"V2": (1.7776, "dm³")})
ans_ok("dalton total", "/api/gas_laws", {"type": "dalton", "gases": [{"name": "a", "p": "79"}, {"name": "b", "p": "21"}],
                                         "p_unit": "kPa"}, {"P_total": (100.0, "kPa")})
ans_ok("graham ratio", "/api/gas_laws", {"type": "graham", "M1": "2.016", "M2": "32.00"}, {"Rate₁/Rate₂": (3.9841, "")})
ans_ok("acid-base: all four", "/api/acid_base", {"type": "weak_acid", "Ka": "1.74e-5", "conc": "0.100"},
       {"pH": (2.8797, ""), "pOH": (11.1203, ""), "[H⁺]": (1.3191e-3, "mol/dm³"), "[OH⁻]": (7.581e-12, "mol/dm³")})
ans_ok("titration", "/api/acid_base", {"type": "titration", "solve": "titrant_volume", "C_titrant": "0.1",
                                       "C_analyte": "0.05", "V_analyte": "25"}, {"Titrant volume at equivalence": (12.5, "cm³")})
ans_ok("calorimetry", "/api/thermo", {"type": "calorimetry", "solve": "q", "q": "", "m": "50", "c": "4.18", "dT": "12"},
       {"q": (2508.0, "J")})
ans_ok("bond enthalpy unit from text", "/api/thermo", {"type": "bond",
       "broken": [{"bond": "C-H", "count": "4", "kJ": ""}, {"bond": "O=O", "count": "2", "kJ": ""}],
       "formed": [{"bond": "C=O", "count": "2", "kJ": ""}, {"bond": "O-H", "count": "4", "kJ": ""}]},
       {"ΔH": (-808.0, "kJ/mol")})
ans_ok("gibbs + spontaneity headline", "/api/thermo", {"type": "gibbs", "dH": "-92.2", "dS": "-199", "T": "298"},
       {"ΔG": (-32.898, "kJ/mol")}, headline="Spontaneous")
ans_ok("gibbs non-spontaneous headline", "/api/thermo", {"type": "gibbs", "dH": "92.2", "dS": "199", "T": "298"},
       {"ΔG": (32.898, "kJ/mol")}, headline="Non-spontaneous")
ans_ok("ΔG° ↔ K", "/api/thermo", {"type": "gibbs_k", "solve": "K", "dG": "-32.9", "T": "298"}, {"K": (5.849e5, "")})
ans_ok("spontaneity crossover", "/api/thermo", {"type": "spontaneity", "dH": "178", "dS": "161"},
       {"Crossover T": (1105.59, "K")})
ans_ok("ICE: x and every concentration", "/api/ice",
       {"reactants": [{"name": "H2", "coeff": "1", "initial": "1"}, {"name": "I2", "coeff": "1", "initial": "1"}],
        "products": [{"name": "HI", "coeff": "2", "initial": "0"}], "Kc": "50"},
       {"x": (0.779519, "mol/dm³"), "[H2]": (0.220481, "mol/dm³"), "[HI]": (1.55904, "mol/dm³")})
ans_ok("Q vs K headline", "/api/ice", {"type": "q_vs_k",
       "reactants": [{"name": "H2", "coeff": "1", "initial": "0.2"}, {"name": "I2", "coeff": "1", "initial": "0.2"}],
       "products": [{"name": "HI", "coeff": "2", "initial": "1"}], "Kc": "50"}, {"Q": (25.0, "")}, headline="Shifts forward")
st, dd, got = answers_of("/api/ice", {"type": "q_vs_k", "reactants": [{"name": "A", "coeff": "1", "initial": "0"}],
                                      "products": [{"name": "B", "coeff": "1", "initial": "1"}], "Kc": "5"})
_record("infinite Q gives no numeric answer (valid JSON)", st == 200 and got == {} and dd["headline"] == "Shifts reverse", str(dd)[:200])
ans_ok("cell from table", "/api/electrochem", {"type": "cell_pick", "half1": "Cu2+/Cu", "half2": "Zn2+/Zn"},
       {"E°cell": (1.10, "V"), "ΔG°": (-212.267, "kJ/mol")}, headline="spontaneous (galvanic cell)")
ans_ok("manual cell", "/api/electrochem", {"type": "cell", "E_cat": "0.34", "E_ano": "-0.76", "n": "2"},
       {"E°cell": (1.10, "V")})
ans_ok("faraday", "/api/electrochem", {"type": "faraday", "solve": "mass", "mass": "", "I": "2", "t": "1930", "M": "63.55", "n": "2"},
       {"mass": (1.2712, "g")})
ans_ok("nernst (blank T = 298.15 K)", "/api/electrochem", {"type": "nernst", "E0": "1.10", "n": "2", "Q": "10", "T": ""},
       {"E": (1.07042, "V")})
ans_ok("kinetics order: k + headline", "/api/kinetics", {"type": "order", "c1": "0.1", "c2": "0.2", "r1": "1e-3", "r2": "4e-3"},
       {"k": (0.1, "L·mol⁻¹·s⁻¹")}, headline="Order ≈ 2")
ans_ok("arrhenius Ea", "/api/kinetics", {"type": "arrhenius", "solve": "Ea", "k1": "1e-3", "T1": "300", "k2": "4e-3", "T2": "320", "Ea": ""},
       {"Ea": (55.323, "kJ/mol")})
ans_ok("arrhenius k2", "/api/kinetics", {"type": "arrhenius", "solve": "k2", "k1": "1e-3", "T1": "300", "k2": "", "T2": "320", "Ea": "55323"},
       {"k₂": (4.0e-3, "")})
ans_ok("half-life", "/api/kinetics", {"type": "halflife", "solve": "t_half", "k": "0.0231", "t_half": ""}, {"t½": (30.006, "s")})
ans_ok("k from half-life", "/api/kinetics", {"type": "halflife", "solve": "k", "k": "", "t_half": "30"}, {"k": (0.0231049, "s⁻¹")})
ans_ok("integrated rate law", "/api/kinetics", {"type": "integrated", "order": "1", "solve": "t", "A0": "1", "k": "0.0231", "t": "", "At": "0.25"},
       {"t": (60.0127, "s")})
for label, url, body in [
    ("balancer has no numeric answer", "/api/equation", {"equation": "H2 + O2 -> H2O"}),
    ("ionic formula has no numeric answer", "/api/ionic", {"action": "formula", "cation": "Al", "cation_charge": "3", "anion": "SO4", "anion_charge": "-2"}),
    ("k units has no numeric answer", "/api/kinetics", {"type": "kunits", "order": "2"}),
    ("Le Chatelier has no numeric answer", "/api/ice", {"type": "le_chatelier", "disturbance": "catalyst"}),
]:
    st, dd, got = answers_of(url, body)
    _record(label, st == 200 and got == {} and dd.get("compact"), str(dd)[:160])
st, dd = call("/api/mole", {"type": "mass_to_moles", "a": "", "b": "18"})
_record("errors are left alone (no answers added)", st == 400 and set(dd) == {"error"}, str(dd))
st, dd = call("/api/periodic", {"type": "symbol", "query": "Zz"})
_record("not-found periodic result unchanged", st == 200 and dd == {"found": False}, str(dd))
resp = client.get("/")
_record("page itself is not modified by the answers hook", resp.status_code == 200 and b"<html" in resp.data[:200])

html_now = page_source()
for needle in ['id="sfSelect"', 'onclick="copyOutput()"', 'id="historyPanel"', 'id="exampleBtn"',
               'id="chainBar"', "e.key === 'Enter'", "function render(d", "showChainToYield(d);",
               "--label-fg:", "const store = {"]:
    _record(f"page has: {needle}", needle in html_now)
calcs = html_now[html_now.index("const CALCS = {"):]
_record("every result goes through render()", "showResult(`" not in calcs and "showOutput(d.compact" not in calcs)
_record("no direct localStorage use outside the safe wrapper",
        html_now.count("localStorage.") == 2, f"{html_now.count('localStorage.')} uses")
examples = re.findall(r"^  '(\d+(?::\w+)?)':", html_now, re.M)
subtypes = {
    "1": ["mass_to_moles", "moles_to_mass", "moles_to_particles", "particles_to_moles", "moles_to_volume", "volume_to_moles"],
    "6": ["mass_to_volume", "volume_to_mass", "density"], "9": ["classify", "formula"],
    "10": ["percent", "actual", "theoretical"], "12": ["ideal", "combined", "graham", "dalton", "mixing"],
    "13": ["ph_convert", "strong_acid", "strong_base", "weak_acid", "weak_base", "buffer", "titration", "identify"],
    "14": ["calorimetry", "hess", "bond", "std_enthalpy", "gibbs", "gibbs_k", "spontaneity"],
    "15": ["table", "q_vs_k", "le_chatelier", "kc_kp"], "16": ["cell_pick", "cell", "faraday", "nernst"],
    "17": ["order", "arrhenius", "halflife", "integrated", "kunits"],
}
missing = [f"{m}:{t}" for m, ts in subtypes.items() for t in ts if f"{m}:{t}" not in examples]
missing += [m for m in ("2", "3", "4", "5", "7", "8", "11") if m not in examples]
_record("every module and option has a worked example", not missing, f"missing: {missing}")

section("Hosting: only the static folder is served")
for path in ("/app.py", "/server.log", "/index.html", "/../app.py", "/static/../app.py"):
    code = client.get(path).status_code
    _record(f"not downloadable: {path}", code in (308, 404), f"status={code}")
for path, kind in (("/static/app.js", "javascript"), ("/static/style.css", "css"),
                   ("/static/fonts/VT323/VT323-Regular.ttf", "font")):
    r = client.get(path)
    _record(f"served: {path}", r.status_code == 200 and len(r.data) > 100, f"status={r.status_code}")
r = client.get("/")
for header, needle in (("X-Content-Type-Options", "nosniff"), ("Content-Security-Policy", "default-src 'self'"),
                       ("Referrer-Policy", "no-referrer"), ("X-Frame-Options", "SAMEORIGIN")):
    _record(f"security header on the page: {header}", needle in r.headers.get(header, ""), r.headers.get(header))
r2 = client.post("/api/mole", json={"type": "moles_to_volume", "a": "1"})
_record("security headers on API responses too", "nosniff" in r2.headers.get("X-Content-Type-Options", ""))
_record("debug mode is not on by default", webapp.app.debug is False)

section("Robustness")
for url in urls:
    status, d = call(url, {})
    _record(f"empty body → clean response: {url}", status in (200, 400) and "__invalid_json__" not in d,
            f"status={status} body={d}")
resp = client.post("/api/mole", data="not json", content_type="text/plain")
_record("non-JSON body → 400/415 not 500", resp.status_code in (400, 415), f"status={resp.status_code}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  API tests  Total: {PASS + FAIL}   Passed: {PASS}   Failed: {FAIL}")
if FAILURES:
    print("\nFailures:")
    print("\n".join(FAILURES))
sys.exit(1 if FAIL else 0)
