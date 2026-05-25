# Chemistry Calculator

An interactive physical chemistry calculator built for IB Chemistry. Covers 17 core topics through both a command-line interface and a browser-based web UI.

**Developer:** Felipe "Pipe" Fonseca
**Project type:** IB Chemistry / personal STEM project

---

## Modules

| # | Module | What it does |
|---|--------|-------------|
| 1 | **Mole Conversions** | Mass ↔ moles ↔ particles ↔ volume at STP |
| 2 | **Empirical Formula** | Empirical formula from element masses or % composition |
| 3 | **Equation Balancer** | Balances chemical equations using linear algebra |
| 4 | **Limiting Reactant** | Finds the limiting reactant, leftover amounts, and theoretical yield |
| 5 | **Percent Composition** | Molar mass and per-element % composition from a formula |
| 6 | **Volume ↔ Mass** | Converts between volume and mass using density |
| 7 | **Oxidation Numbers** | Rule-based oxidation state solver with algebraic fallback for unknowns |
| 8 | **Atom Economy** | Calculates atom economy for a given reaction |
| 9 | **Ionic Bonding** | Bond classification (ionic / polar covalent / covalent) and ionic formula writer |
| 10 | **Percentage Yield** | Solves for actual yield, theoretical yield, or % yield |
| 11 | **Periodic Table** | Element lookup by name, symbol, or atomic number |
| 12 | **Gas Laws** | Ideal gas law, combined gas law, Graham's law, Dalton's law, molar volume |
| 13 | **Acid-Base Chemistry** | pH/pOH conversions, strong/weak acid-base, buffers, Ka/Kb, titration |
| 14 | **Thermodynamics** | Calorimetry (q=mcΔT), Hess's Law, bond enthalpy, ΔH°rxn, Gibbs free energy (ΔG=ΔH−TΔS) |
| 15 | **Equilibrium & ICE Solver** | ICE table builder (bisection solver), Kc↔Kp, Q vs K, Le Chatelier's principle |
| 16 | **Electrochemistry** | Cell potential, ΔG°=−nFE°, Faraday's law, Nernst equation, spontaneity checker |
| 17 | **Kinetics** | Rate law from initial rates, Arrhenius equation, half-life, integrated rate laws (0/1/2 order) |

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
0.  Exit
```

### Run the Web UI

```bash
python ui_interface/app.py
```

Then open **http://localhost:5000** in your browser.

The web UI is **CHEMCALC FX-17** — a redesigned single-page app where modules are grouped by IB Chemistry topic (Stoichiometry, Energetics, Kinetics, Equilibrium, Acids & Bases, Electrochemistry, Tools). Clicking a module opens its input form inline; the output box shows the formula used, substituted values, and result. Dark and light themes are supported.

### Run Diagnostics

```bash
python test_files/run_diagnostics.py
```

Runs the full automated test suite across all modules — no user input needed. Outputs pass/fail for every test case.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3 |
| Equation balancing | sympy |
| Web interface | Flask + HTML/JS (CHEMCALC FX-17) |
| Shared constants | `constants.py` (R, F, Avogadro, reduction potentials, bond enthalpies) |
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
│   │   ├── constants.py             # Shared physical/chemical constants
│   │   ├── ui_interface/            # Flask web app
│   │   │   ├── app.py               # REST API (one route per module)
│   │   │   └── index.html           # Front-end
│   │   ├── test_files/              # Automated test suite
│   │   │   ├── run_diagnostics.py
│   │   │   ├── stress_test.py
│   │   │   ├── test_calculator.py
│   │   │   ├── test_ice_solver.py
│   │   │   └── test_thermodynamics.py
│   │   └── requirements.txt
│   └── user interface/              # C UI (in development)
│       ├── main_menu.C
│       └── include/ui.h
├── .gitignore
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE)
