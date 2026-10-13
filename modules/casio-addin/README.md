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
- **F1–F6** are labelled along the bottom of the entry fields, where they type
  the symbols the keypad lacks.
- In a formula field the keypad's own printed letters are used: press the key
  with the letter on it. **ALPHA** (or F5) switches to digits, **SHIFT** (or
  F4) to small letters, and F1–F3 type `(`, `)` and the hydrate dot.
- In a number field, `(-)` makes a value negative and `EXP` starts a power of
  ten, so `1.74` `EXP` `(-)` `5` is 1.74 × 10⁻⁵.
- **Atom economy** and the **equation balancer** take the whole equation in
  one field, e.g. `CH4+2O2->CO2+2H2O` or `C3H8+O2->CO2+H2O`. **F1–F4** type
  `(` `)` `+` and `->` in any mode; in digit mode (**ALPHA**/F6 to switch) the
  keypad's own `+`, `(`, `)`, `.` and `→` keys do the same. A capital then a
  small letter (Cl, Ca) needs **SHIFT** or F5 in between. Long equations scroll
  so the end stays in view. Atom economy then asks which product is wanted: leave
  the numbers out and it balances the equation for you; type some and it uses
  them (a missing one counts as 1), but only if they balance the equation,
  otherwise it says *Numbers don't balance* so a wrong number can never give a
  wrong answer: fix it, or delete the numbers to auto-balance. The balancer
  ignores any numbers typed in front. A mistake is explained and the text stays
  for you to fix.
- For a bond enthalpy, pick the bond from the list, or choose *Type a bond* and
  use F1/F2/F3 for `-` `=` `#` (e.g. `C-H`, `O=O`, `N#N`; capitals or small
  letters both work). A bond that is not in the list asks for its kJ/mol.
- A bond count can be a fraction for per-mole equations (H₂ + ½O₂ → H₂O): press
  the `a b/c` key, `÷` or F1 for `/`, e.g. `1/2` or `3/2`. A decimal like `0.5`
  works too. Zero, negatives and `1/0` are refused.
- Where a screen says *blank to skip*, pressing EXE on the empty field moves on.
- **Every menu entry and every question carries a worked example**, shown in a
  panel marked *e.g.* — scroll a menu and the example changes with the
  highlight, so you can see what an option does before opening it, and what a
  field wants while you are typing into it.

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

## The MENU icon

`assets-cg/make_icons.py` draws `icon-uns.png` and `icon-sel.png` (92 × 64,
opaque RGB). The tile, its gradient and bevel, and the cyan selected
background come from the icon template in the fxSDK (© gint/fxSDK
contributors, MIT licence, see `assets-cg/LICENSE-fxsdk-template.txt`), kept as
`template-uns.png` and `template-sel.png`; the script recolours the tile orange
and draws the white flask. The calculator prints the name "ChemCalc" under the
icon itself, so none is drawn. The same script writes `src/ui/flask_mark.h`,
the flask at 3x that the menus show as a pale watermark. Regenerate both with
`py assets-cg/make_icons.py` (needs Pillow).

## The text

Body text - menu rows, prompts, what you type, the lines of an answer - is set
in an 11 × 22 pixel bitmap font, so 34 characters fit across. Rows are 24 px
apart, as the calculator's are, which leaves 7: a result page shows its heading
and 6 lines, and a menu 7 rows (6 when it has an example line along the bottom,
as the main menu does). Headings and answers use the bold cut. The small print - the status
strip, the softkey labels, the grey hints and the "e.g." examples - stays in
gint's own 8 × 9 font, as the calculator's does.

`assets-cg/make_font.py` writes `font-body.png` and `font-bold.png`, and
`assets-cg/fxconv-metadata.txt` has fxconv turn them into the gint fonts
`font_body` and `font_bold`. The font is a bitmap conversion of the 11×22
ter-u22n/ter-u22b glyphs from Terminus Font by Dimitar Toshkov Zhekov (SIL OFL
1.1); not an official Terminus release. The glyphs come from the Debian/Ubuntu
package `xfonts-terminus` and the licence is `assets-cg/LICENSE-terminus-OFL.txt`. Regenerate the PNGs with
`py assets-cg/make_font.py` (needs Pillow).

## The status strip and the menus

- The **battery** at the top left is the calculator's own icon, not an
  estimate: `src/ui/battery.c` has the OS draw its status bar into the OS's
  VRAM (`DisplayStatusArea`, syscall 0x1D81, inside a gint world switch), once
  without and once with the battery, and copies the pixels that differ. So it
  always matches the status bar of the built-in apps (levels, low-battery
  state and all), whatever the battery type. No syscall that returns the
  battery *level* is documented, and the voltage ones (0x1186, 0x12D5) give a
  raw reading with no published thresholds (and a scale that community tools
  correct by about 10 % on the fx-CG50), so those are not used. If the OS
  draws no battery the strip shows none rather than a made-up one. It asks the
  OS at most every 30 seconds. Not yet checked on a real calculator: the OS
  may keep the level it measured when ChemCalc started, instead of
  re-measuring while it runs. If the OS calls ever misbehave on some
  calculator or OS version, add `-DCHEMCALC_NO_BATTERY` to
  `target_compile_options` in `CMakeLists.txt` and rebuild: ChemCalc then
  leaves the OS alone and draws no battery.
- The letter mode beside it is drawn as the calculator's own ALPHA indicator
  is (Software User's Guide, "Status Bar"): a red box with a white **A** for
  capitals or **a** for small letters, and the yellow padlock of alpha-lock,
  since ALPHA stays on until it is pressed again. In digit mode there is no
  box, as on the calculator. SHIFT only toggles small letters here, so it has
  no indicator of its own. The entry fields read ALPHA and SHIFT as keys of
  their own: gint's `getkey()` would swallow them as modifiers.
- Menus are drawn over a gradient from white to light orange with a pale flask,
  like the calculator's own application menus; entry and result screens stay
  white, as theirs do. The gradient is dithered where one colour step gives way
  to the next, so it does not show bands.
- A long answer scrolls with the arrows (magenta arrows say which way), and a
  message too wide for its box wraps onto up to three lines of about 30
  characters.

## How it is laid out, and how it is tested

```
src/core/      the chemistry: plain C99, no calculator headers at all
src/ui/        status strip, softkeys, menus, entry fields, result pages
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

826 checks at present: 459 for the chemistry and 367 for the screens, among
them that nothing is drawn past the screen's right edge. The
expected values are the same hand-worked IB figures the desktop calculator and
the Python port are tested against, so the three cannot quietly disagree.

`test/gen_elements.py` regenerates `src/core/elements.c` from the desktop
calculator's tables — edit that script rather than the generated file.
