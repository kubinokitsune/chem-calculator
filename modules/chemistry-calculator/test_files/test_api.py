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
section("Contract: every URL in index.html is a POST route")
html = open(os.path.join(ROOT, "ui_interface", "index.html"), encoding="utf-8").read()
urls = sorted(set(re.findall(r"post\('(/api/[a-z_]+)'", html)))
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
