# Chemistry Calculator (modules/chemistry-calculator)

## Setup

1. Create and activate a Python virtual environment (recommended):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies (sympy for the balancer, flask for the web UI):

   ```bash
   python -m pip install -r requirements.txt
   ```

## Running

From this directory:

```bash
python main.py              # terminal menu (17 modules)
python ui_interface/app.py  # web UI at http://localhost:5000
```

Modules are lazy-loaded when selected from the menu.

## Tests

```bash
python test_files/run_diagnostics.py      # every function + regression checks
python test_files/stress_test.py          # edge cases and error handling
python test_files/test_ice_solver.py
python test_files/test_thermodynamics.py
python test_files/test_ib_chemistry.py    # IB-style worked problems (3 s.f.)
python test_files/test_api.py             # web page <-> Flask API contract
python test_files/stress_new_features.py  # gas units, ionic balancing, limiting reactant
python test_files/test_ui.py              # browser click-through (see below)
```

For the browser tests:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
```

All suites also run in GitHub Actions on every push.

## Notes

- Formulas can be typed in lower case (`nh3`, `kmno4`).
- The equation balancer handles ions (`Fe^3+`, `SO42-`), electrons (`e-`) and acidic/basic solutions.
- Gas laws accept atm/kPa/Pa/bar/mmHg, L/dm³/mL/cm³/m³ and K/°C (R = 8.314 J K⁻¹ mol⁻¹).
- Molar volume at STP is 22.7 dm³ mol⁻¹ (0 °C, 100 kPa), set once in `constants.py`.
- The web page is `ui_interface/index.html` plus `ui_interface/static/style.css` and `static/app.js`; only `static/` is served to the browser.
- Debug mode is off unless `CHEMCALC_DEBUG=1`, and the server listens on `127.0.0.1` unless `CHEMCALC_HOST` is set.
