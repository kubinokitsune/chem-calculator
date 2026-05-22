Chemistry Calculator (modules/chemistry-calculator)

Setup

1. Create and activate a Python virtual environment (recommended):

   powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install dependencies:

   python -m pip install -r requirements.txt

Running

From this directory run:

   python main.py

This will open the interactive Physical Chemistry Calculator main menu. The Periodic Table and Equation Balancer are lazy-loaded when selected from the menu.

Notes

- `sympy` is required for the equation balancer.
- The periodic table includes basic element metadata (atomic number, symbol, name, atomic weight) and an interactive lookup.
