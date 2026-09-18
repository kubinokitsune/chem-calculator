# ChemCalc for the Casio fx-CG50

The IB chemistry calculator, cut down to run in the **Python app** of a Casio
fx-CG50 (and the fx-9750GIII / fx-9860GIII, which run the same MicroPython).

Everything runs offline on the calculator. No add-in, no unlocking, no cable
software beyond the one Casio ships.

## Put it on the calculator

1. Connect the calculator with the USB cable and choose **USB Flash** on the
   calculator's screen. It appears as a removable drive.
2. Copy **all nine `.py` files** from this folder into the root of that drive
   (not into a subfolder - the Python app only lists files in the root).
3. Eject the drive, then on the calculator open **MENU -> Python**.
4. Highlight `chem.py`, press **F1 (RUN)**, then **F6 (RUN)** at the prompt.

To update later, copy the changed files over the old ones the same way.

## Files

| File | Size | What it holds |
|---|---|---|
| `chem.py` | 2 KB | the top menu; loads the others only when you pick a topic |
| `chemcore.py` | 8 KB | element masses, formula parsing, number formatting, all the input prompts |
| `chemstoi.py` | 12 KB | moles, percent composition, empirical/molecular, solutions, limiting reactant, yield, atom economy |
| `chemgas.py` | 9 KB | ideal gas, combined gas, Graham, Dalton, ICE, Q vs K, Le Chatelier, Kc <-> Kp |
| `chemaqua.py` | 5 KB | pH/pOH, strong and weak acids and bases, buffers, titration, salt pH, Ka/Kb |
| `chemener.py` | 12 KB | calorimetry, Hess, bond enthalpies, dHf, entropy, Gibbs, cells, Faraday, rate order, Arrhenius, half-life, integrated rate laws |
| `chemstruct.py` | 7 KB | electron configuration, oxidation numbers, ionic formulae |
| `chemtools.py` | 7 KB | isotopes and Ar, uncertainties, index of hydrogen deficiency |
| `chembal.py` | 4 KB | equation balancer (exact fractions, no external libraries) |

About 80 KB in total. The calculator has 16 MB of storage, so space is not the
constraint - **RAM is**. `chem.py` imports one topic module at a time for that
reason; do not merge the files into one.

## Using it

- Menus take the letter or number shown at the left, then **EXE**.
- Blank input means "solve for this one" wherever a prompt offers it, and
  **0** or blank goes back a level.
- Formulae are typed the way you write them: `H2O`, `Ca(OH)2`, brackets and
  hydrate dots included (`CuSO4.5H2O`). Case matters (`Co` is cobalt, `CO` is
  carbon monoxide), but the calculator will also read all-lowercase input such
  as `hno3`.
- Equations for the balancer are typed as `H2 + O2 = H2O` (`=`, `->` and `>`
  all work).
- Answers come out to 4 significant figures, and switch to scientific notation
  only outside 1e-4 .. 1e6, which is what the screen reads best.

## Data-booklet conventions

Same as the desktop version: R = 8.31 J K-1 mol-1, molar volume 22.7 dm3 mol-1
at STP (0 C, 100 kPa), F = 96500 C mol-1, Kw = 1.00e-14, c(water) = 4.18
J g-1 K-1.

## What the calculator version does not do

- **No structural/organic drawing, no reaction prediction, no spectra.**
- The balancer handles ordinary equations by exact linear algebra, but it takes
  **neutral formulae only**: no charges (`Fe^3+`) and no half-equation
  (acidic/basic medium) balancing, both of which the desktop version does.
- Element data is masses only. There are no names, groups, or electronegativity
  values; the fx-CG50's own periodic table (the Physium add-in) is a separate
  program and cannot be read from Python.
- Text is ASCII only, so it prints `dH`, `dG`, `dm3` rather than the symbols.

## Testing

The port is tested from the desktop machine - the test driver feeds scripted
keypresses to each menu and checks the printed output:

```bash
py modules/chemistry-calculator/test_files/test_casio.py
```

221 checks: every menu path, the IB worked answers, and the MicroPython
constraints (ASCII only, no f-strings, no classes or generators, no imports
the calculator does not have).
