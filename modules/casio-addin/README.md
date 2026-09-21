# ChemCalc — a native add-in for the Casio fx-CG50

The IB chemistry calculator as a real calculator application: its own icon in
the MENU screen next to Statistics and Financial, F1–F6 softkeys, arrow-key
navigation, and colour. It starts instantly and needs no Python app.

This is the third form of the same calculator in this repository:

| | What it is | Where |
|---|---|---|
| Desktop | Python CLI + web UI | `modules/chemistry-calculator` |
| Python port | scripts for the calculator's Python app | `modules/casio-fx-cg50` |
| **Add-in** | **a compiled `.g3a` application** | **here** |

## Why an add-in and not Python

The fx-CG50's Python app has **no way to read a keypress**. `input()` is all
there is, so softkeys, arrow keys and a MENU icon are impossible from a `.py`
file — Casio only added `getkey()` on the newer fx-CG100. Anything that behaves
like the calculator's own applications has to be a native add-in, written in C.

## Put it on the calculator

1. Connect the calculator and choose **USB Flash** on its screen.
2. Copy **`ChemCalc.g3a`** into the root of the drive that appears.
3. Eject it. ChemCalc is now in the **MENU** screen — press its icon.

Nothing else needs to be copied, and the Python version can stay alongside it.

## Using it

- **Arrows** move, **EXE** chooses, **EXIT** goes back one level, and EXIT at
  the topic list leaves the add-in.
- A menu entry can also be picked by typing its number.
- **F1–F6** are labelled along the bottom of every screen.
- In a formula field the keypad's own printed letters are used: press the key
  with the letter on it. **ALPHA** (or F5) switches to digits, **SHIFT** (or
  F4) to small letters, and F1–F3 type `(`, `)` and the hydrate dot.
- In a number field, `(-)` makes a value negative and `EXP` starts a power of
  ten, so `1.74` `EXP` `(-)` `5` is 1.74 × 10⁻⁵.
- Where a screen says *blank to skip*, pressing EXE on the empty field moves on.

## What it covers

| Topic | Screens |
|---|---|
| Stoichiometry | moles ↔ mass ↔ particles ↔ volume, percent composition, empirical and molecular formula, percentage yield, atom economy |
| Gases and equilibrium | pV = nRT, the combined gas law, Graham's law, Kc ↔ Kp, an ICE table |
| Acids and bases | pH/pOH/[H⁺]/[OH⁻], strong and weak acids and bases, buffers, Ka/Kb/pKa/pKb |
| Energy, cells, rates | calorimetry, bond enthalpies, Gibbs energy and K, cell potential, electrolysis, Arrhenius and half-life |
| Equation balancer | any ordinary equation, in exact whole numbers |
| Periodic table | all 118 elements, group/period listings, bond type from electronegativity |
| Structure and data | electron configuration, oxidation numbers, ionic formulas, isotopes and Ar, uncertainties, index of hydrogen deficiency |

Data-booklet values throughout: R = 8.31, molar volume 22.7 dm³ mol⁻¹ at STP,
F = 96500, Kw = 1.00 × 10⁻¹⁴, c(water) = 4.18, answers to 4 significant figures.

## Building it yourself

The add-in is built with the [fxSDK and gint](https://git.planet-casio.com/Lephenixnoir/fxsdk),
which run on Linux (WSL is fine on Windows):

```bash
sudo apt install git build-essential cmake pkg-config python3 python3-pil \
    libpng-dev libusb-1.0-0-dev libudisks2-dev libncurses-dev libsdl2-dev
git clone https://git.planet-casio.com/Lephenixnoir/GiteaPC.git
cd GiteaPC && make install
giteapc install Lephenixnoir/fxsdk Lephenixnoir/sh-elf-gcc Lephenixnoir/gint
```

Then, in this folder:

```bash
fxsdk build-cg
```

which produces `ChemCalc.g3a`. `python3-pil` is not optional — gint converts
its fonts with it, and the build fails late without it.

## How it is laid out, and how it is tested

```
src/core/      the chemistry: plain C99, no calculator headers at all
src/ui/        title bar, softkeys, menus, entry fields, result pages
src/screens/   one file per topic, built out of the two above
test/          tests that run on a PC
```

The split matters: because `src/core` never includes a calculator header, the
same files compile for the add-in **and** for the tests, so the chemistry is
checked without a calculator in the loop.

The screens are tested too. `test/fake_gint.c` stands in for the screen and the
keypad: it records everything drawn and hands out keypresses the test queued,
including working out the ALPHA and SHIFT presses needed to type `CaCO3`. The
tests therefore drive the real menus and the real entry fields.

```bash
make -C test          # both suites
make -C test core     # the chemistry only
make -C test screens  # the menus and screens
```

315 checks at present: 280 for the chemistry and 35 for the screens. The
expected values are the same hand-worked IB figures the desktop calculator and
the Python port are tested against, so the three cannot quietly disagree.

`test/gen_elements.py` regenerates `src/core/elements.c` from the desktop
calculator's tables — edit that script rather than the generated file.
