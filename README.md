# Chemistry Calculator

[![tests](https://github.com/kubinokitsune/chem-calculator/actions/workflows/tests.yml/badge.svg)](https://github.com/kubinokitsune/chem-calculator/actions/workflows/tests.yml)

An interactive physical chemistry calculator built for IB Chemistry. Covers 22 topics through a command-line interface, a browser-based web UI, and a cut-down port that runs on a **Casio fx-CG50** graphing calculator (see [modules/casio-fx-cg50](modules/casio-fx-cg50/README.md)).

**Developer:** Felipe "Pipe" Fonseca
**Project type:** IB Chemistry / personal STEM project

---

## Modules

| # | Module | What it does |
|---|--------|-------------|
| 1 | **Mole Conversions** | Mass ↔ moles ↔ particles ↔ volume at STP (22.7 dm³/mol) |
| 2 | **Empirical Formula** | From masses or % composition, from **combustion analysis**, and the **molecular formula** from Mr |
| 3 | **Equation Balancer** | Balances molecular and ionic equations and half-equations (linear algebra + half-equation method), with acidic/basic solutions |
| 4 | **Limiting Reactant** | Limiting reactant, leftovers and theoretical yield from moles or grams, with auto-balancing |
| 5 | **Percent Composition** | Molar mass and per-element % composition from a formula |
| 6 | **Volume ↔ Mass** | Converts between volume and mass using density |
| 7 | **Oxidation Numbers** | Rule-based oxidation state solver with algebraic fallback for unknowns |
| 8 | **Atom Economy** | Calculates atom economy for a given reaction |
| 9 | **Ionic Bonding** | Bond classification (ionic / polar covalent / covalent) and ionic formula writer |
| 10 | **Percentage Yield** | Solves for actual yield, theoretical yield, or % yield |
| 11 | **Periodic Table** | Element lookup by name, symbol, or atomic number |
| 12 | **Gas Laws** | Ideal, combined, mixing, Graham's and Dalton's laws in atm/kPa/Pa, L/dm³/cm³/m³, K/°C |
| 13 | **Acid-Base Chemistry** | pH/pOH conversions, strong/weak acid-base, buffers, Ka/Kb, titration, salt pH, pKa from half-equivalence |
| 14 | **Thermodynamics** | Calorimetry (q=mcΔT), Hess's Law, IB bond enthalpies, ΔH°rxn, ΔS°rxn, ΔG=ΔH−TΔS, ΔG°=−RT ln K |
| 15 | **Equilibrium & ICE Solver** | ICE table builder (bisection solver), Kc↔Kp, Q vs K, Le Chatelier's principle |
| 16 | **Electrochemistry** | Cell potential, ΔG°=−nFE°, Faraday's law, Nernst equation, spontaneity checker |
| 17 | **Kinetics** | Rate law from initial rates, Arrhenius equation (including the ln k vs 1/T graph method), half-life, integrated rate laws |
| 18 | **Solutions** | c = n/V, dilutions (c₁V₁ = c₂V₂), standard solutions, g dm⁻³ ↔ mol dm⁻³, ppm |
| 19 | **Isotopes** | Relative atomic mass from isotope abundances, and abundances from Ar |
| 20 | **Uncertainties** | Absolute ↔ %, combining measurements, powers, % error, significant figures |
| 21 | **Electron Configuration** | Full and noble-gas shorthand for atoms and ions, with the Cr/Cu exceptions |
| 22 | **Index of Hydrogen Deficiency** | Rings and π bonds from a molecular formula |

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/kubinokitsune/chem-calculator.git
cd chem-calculator/modules/chemistry-calculator

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the CLI

```bash
python main.py
```

```
=== Physical Chemistry Calculator ===
1.  Mole Conversions
2.  Empirical Formula Calculator
3.  Balanced Chemical Equations
4.  Limiting Reactant Calculator
5.  Percent Composition Calculator
6.  Volume-to-Mass Conversions
7.  Oxidation Number Calculator
8.  Element Economy Calculator
9.  Ionic Bonding Calculator
10. Percentage Yield Calculator
11. Periodic Table
12. Gas Laws Calculator
13. Acid-Base Chemistry Calculator
14. Thermodynamics
15. Equilibrium & ICE Table Solver
16. Electrochemistry
17. Kinetics
18. Solutions (concentration & dilution)
19. Isotopes & Relative Atomic Mass
20. Uncertainties & Significant Figures
21. Electron Configuration
22. Index of Hydrogen Deficiency
0.  Exit
```

### Run the Web UI

```bash
python ui_interface/app.py
```

Then open **http://localhost:5000** in your browser.

> Debug mode is off by default and the server listens on localhost only.

The web UI is **CHEMCALC FX-17** — a single-page app where modules are grouped by IB Chemistry topic (Stoichiometry, Energetics, Kinetics, Equilibrium, Acids & Bases, Electrochemistry, Tools). Clicking a module opens its input form inline; the output box shows the formula used, substituted values, and result.

Every module option is available on the page, and it also has:

- **Answers: Auto / 2–6 s.f.** — rounds answers to the significant figures you want (formulas are never touched)
- **★ Try example** — a worked IB-style example for every module and option
- **⧉ Copy**, **Enter to calculate**, **⟲ Recent** (your last 20 answers), dark/light themes
- **→ % Yield** — sends a theoretical yield from Limiting Reactant into % Yield

| Environment variable | Default | Meaning |
|----------------------|---------|---------|
| `CHEMCALC_DEBUG` | off | `1` enables Flask's debugger (local use only) |
| `CHEMCALC_HOST` | `127.0.0.1` | `0.0.0.0` to allow other machines |
| `PORT` | `5000` | port to listen on |

Only `ui_interface/static/` is served to the browser, so the Python source and the server log are not downloadable.

### Run the Tests

```bash
python test_files/run_diagnostics.py      # every function + regression checks
python test_files/test_ib_chemistry.py    # IB-style worked problems, checked to 3 s.f.
python test_files/test_api.py             # web page <-> Flask API contract
python test_files/stress_new_features.py  # ~36 000 checks: gas units, ionic balancing, limiting reactant
python test_files/test_ui.py              # clicks through the real page in a browser (needs playwright)
python test_files/test_casio.py           # the Casio fx-CG50 port: every menu, plus its MicroPython limits
```

All of these run in GitHub Actions on every push.

Also `stress_test.py`, `test_ice_solver.py` and `test_thermodynamics.py`. No user input needed; each prints pass/fail and a summary. See the [Diagnostics wiki page](https://github.com/kubinokitsune/chem-calculator/wiki/Diagnostics).

### Input tips

- Formulas can be typed in lower case: `nh3`, `kmno4`, `ca(oh)2`
- Ions: `Fe^3+`, `MnO4-`, `SO4^2-` (or `SO42-`), electrons `e-`
- Equations: `MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+`, then pick **Acidic** solution
- Gas laws: pick the units the question uses (kPa, cm³, °C…) — conversion is automatic

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3 |
| Equation balancing | sympy |
| Web interface | Flask + HTML/JS (CHEMCALC FX-17) |
| Shared constants | `constants.py` (R, F, Avogadro, molar volume, reduction potentials, formula capitalisation) |
| C UI prototype | C (in development) |

---

## Project Structure

```
chem-calculator/
├── modules/
│   ├── chemistry-calculator/        # Python backend + web UI
│   │   ├── main.py                  # CLI entry point
│   │   ├── mole_conversions.py
│   │   ├── Empirical_Formula_Calculator.py
│   │   ├── equation_balancer.py
│   │   ├── limiting_reactant.py
│   │   ├── percent_composition_calculator.py
│   │   ├── volume_mass_conversions.py
│   │   ├── oxidation_number_calculator.py
│   │   ├── atom_economy_calculator.py
│   │   ├── ionic_bonding_calculator.py
│   │   ├── percentage_yield_calculator.py
│   │   ├── Periodic_table.py
│   │   ├── gas_laws.py
│   │   ├── acid_base.py
│   │   ├── thermodynamics.py
│   │   ├── ice_solver.py
│   │   ├── electrochemistry.py
│   │   ├── kinetics.py
│   │   ├── solutions.py
│   │   ├── isotopes.py
│   │   ├── uncertainties.py
│   │   ├── electron_config.py
│   │   ├── organic_tools.py
│   │   ├── constants.py             # Shared physical/chemical constants
│   │   ├── ui_interface/            # Flask web app
│   │   │   ├── app.py               # REST API (one route per module)
│   │   │   ├── index.html           # Front-end markup
│   │   │   └── static/              # the only folder served to the browser
│   │   │       ├── style.css
│   │   │       ├── app.js
│   │   │       └── fonts/
│   │   ├── test_files/              # Automated test suites
│   │   │   ├── run_diagnostics.py
│   │   │   ├── stress_test.py
│   │   │   ├── stress_new_features.py
│   │   │   ├── test_api.py
│   │   │   ├── test_calculator.py
│   │   │   ├── test_ib_chemistry.py
│   │   │   ├── test_ice_solver.py
│   │   │   ├── test_thermodynamics.py
│   │   │   ├── test_ui.py           # browser click-through (playwright)
│   │   │   └── test_casio.py        # drives the Casio port's menus
│   │   └── requirements.txt
│   ├── casio-fx-cg50/               # port for the Casio fx-CG50 (MicroPython)
│   │   ├── chem.py                  # run this one on the calculator
│   │   ├── chemcore.py              # masses, formula parsing, prompts
│   │   ├── chemstoi.py  chemgas.py  chemaqua.py  chemener.py
│   │   ├── chemstruct.py  chemtools.py  chembal.py
│   │   ├── chemptab.py              # all 118 elements + group/period/block
│   │   └── README.md                # how to copy it onto the calculator
│   └── user interface/              # C UI (in development)
│       ├── main_menu.C
│       └── include/ui.h
├── .github/workflows/tests.yml      # runs all 9 suites on every push
├── .gitignore
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE)
