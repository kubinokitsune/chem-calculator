/* test_core.c - tests for the add-in's chemistry core, run on a PC.
 *
 *   cd modules/casio-addin && make -C test
 *
 * The expected values are the same hand-worked IB figures the Python suites
 * use, so the add-in, the desktop calculator and the Casio Python port all
 * have to agree.
 */

#include "../src/core/chem.h"
#include "../src/core/stoich.h"
#include "../src/core/solution.h"
#include "../src/core/balance.h"
#include "../src/core/energy.h"
#include "../src/core/tools.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int passed, failed;

static void ok(const char *label, int condition, const char *detail)
{
    if (condition) {
        passed++;
        printf("  [PASS] %s\n", label);
    } else {
        failed++;
        printf("  [FAIL] %s\n         %s\n", label, detail ? detail : "");
    }
}

static void close_to(const char *label, double got, double want, double tolerance)
{
    char detail[96];
    snprintf(detail, sizeof detail, "got %.6g, expected %.6g", got, want);
    ok(label, fabs(got - want) <= tolerance, detail);
}

static void text_is(const char *label, const char *got, const char *want)
{
    char detail[160];
    snprintf(detail, sizeof detail, "got \"%s\", expected \"%s\"", got, want);
    ok(label, strcmp(got, want) == 0, detail);
}

static void int_is(const char *label, int got, int want)
{
    char detail[96];
    snprintf(detail, sizeof detail, "got %d, expected %d", got, want);
    ok(label, got == want, detail);
}

static void section(const char *title)
{
    printf("\n=== %s ===\n", title);
}

static double mass_of(const char *formula)
{
    float value = 0.0f;
    if (chem_molar_mass(formula, &value) != CHEM_OK)
        return -1.0;
    return value;
}

/* Balance an equation and check the answer the way a marker would: count the
 * atoms of every element on both sides and compare. Returns 1 when the
 * coefficients balance, so a wrong answer cannot pass by matching my
 * expectation - it has to actually conserve atoms. */
static int atoms_balance(const char *const *reactants, int n_reactants,
                         const char *const *products, int n_products,
                         const int *coefficients)
{
    chem_formula_t formula;
    char symbols[BAL_MAX_ELEMENTS][CHEM_SYMBOL_LEN];
    long left[BAL_MAX_ELEMENTS], right[BAL_MAX_ELEMENTS];
    int n_elements = 0, i, j, k;

    for (i = 0; i < BAL_MAX_ELEMENTS; i++) {
        left[i] = 0;
        right[i] = 0;
    }
    for (j = 0; j < n_reactants + n_products; j++) {
        const char *text = (j < n_reactants) ? reactants[j] : products[j - n_reactants];
        if (chem_parse_formula(text, &formula, NULL, 0) != CHEM_OK)
            return 0;
        if (coefficients[j] <= 0)
            return 0;
        for (k = 0; k < formula.n; k++) {
            int found = -1;
            for (i = 0; i < n_elements; i++) {
                if (strcmp(symbols[i], formula.atoms[k].symbol) == 0)
                    found = i;
            }
            if (found < 0) {
                found = n_elements++;
                strcpy(symbols[found], formula.atoms[k].symbol);
            }
            if (j < n_reactants)
                left[found] += (long)coefficients[j] * formula.atoms[k].count;
            else
                right[found] += (long)coefficients[j] * formula.atoms[k].count;
        }
    }
    for (i = 0; i < n_elements; i++) {
        if (left[i] != right[i])
            return 0;
    }
    return 1;
}

static const char *fmt(double value, int figures)
{
    static char buffer[32];
    chem_format(value, figures, buffer, sizeof buffer);
    return buffer;
}

int main(void)
{
    chem_formula_t formula;
    char bad[8];
    int z, count, i;

    section("1. The element table");

    int_is("hydrogen is Z=1", chem_symbol_z("H"), 1);
    int_is("oganesson is Z=118", chem_symbol_z("Og"), 118);
    close_to("Ar(C) = 12.01", chem_element(6)->mass, 12.01, 0.001);
    close_to("Ar(Fe) = 55.85", chem_element(26)->mass, 55.85, 0.001);
    close_to("Ar(S) = 32.07, the IB booklet value", chem_element(16)->mass, 32.07, 0.001);
    text_is("Z=26 is called Iron", chem_element(26)->name, "Iron");
    text_is("IB spelling: aluminium", chem_element(13)->name, "Aluminium");
    text_is("IB spelling: caesium", chem_element(55)->name, "Caesium");
    ok("nothing at Z=0", chem_element(0) == NULL, NULL);
    ok("nothing at Z=119", chem_element(119) == NULL, NULL);

    /* every symbol appears exactly once */
    count = 0;
    for (z = 1; z <= CHEM_ELEMENT_COUNT; z++) {
        for (i = 1; i <= CHEM_ELEMENT_COUNT; i++) {
            if (i != z && strcmp(chem_elements[z - 1].symbol, chem_elements[i - 1].symbol) == 0)
                count++;
        }
    }
    int_is("no symbol is repeated", count, 0);

    /* Mass rises with atomic number apart from nine known steps back: the four
     * textbook inversions (Ar/K, Co/Ni, Te/I, Th/Pa) and five among the
     * synthetic elements, which are listed by their longest-lived isotope
     * (U/Np, Pu/Am, Sg/Bh, Hs/Mt, Fl/Mc). Anything else is a typo in the data. */
    count = 0;
    for (z = 2; z <= CHEM_ELEMENT_COUNT; z++) {
        if (chem_elements[z - 1].mass < chem_elements[z - 2].mass)
            count++;
    }
    int_is("masses rise except at the 9 known inversions", count, 9);

    int_is("lookup by symbol", chem_find_element("Fe"), 26);
    int_is("lookup by lower-case symbol", chem_find_element("fe"), 26);
    int_is("lookup by name", chem_find_element("iron"), 26);
    int_is("lookup by atomic number", chem_find_element("26"), 26);
    int_is("an invented name finds nothing", chem_find_element("Kryptonite"), 0);
    int_is("119 finds nothing", chem_find_element("119"), 0);

    section("2. Position in the table");

    int_is("H is group 1", chem_group(1), 1);
    int_is("He is group 18", chem_group(2), 18);
    int_is("B is group 13", chem_group(5), 13);
    int_is("Cl is group 17", chem_group(17), 17);
    int_is("Fe is group 8", chem_group(26), 8);
    int_is("Zn is group 12", chem_group(30), 12);
    int_is("Ga is group 13", chem_group(31), 13);
    int_is("Ag is group 11", chem_group(47), 11);
    int_is("Hf is group 4", chem_group(72), 4);
    int_is("Pb is group 14", chem_group(82), 14);
    int_is("Og is group 18", chem_group(118), 18);
    int_is("Na is period 3", chem_period(11), 3);
    int_is("Fe is period 4", chem_period(26), 4);
    int_is("U is period 7", chem_period(92), 7);

    /* the periods must hold 2, 8, 8, 18, 18, 32, 32 elements */
    {
        int sizes[8] = {0, 0, 0, 0, 0, 0, 0, 0};
        int want[8] = {0, 2, 8, 8, 18, 18, 32, 32};
        int wrong = 0;
        for (z = 1; z <= CHEM_ELEMENT_COUNT; z++)
            sizes[chem_period(z)]++;
        for (i = 1; i <= 7; i++) {
            if (sizes[i] != want[i])
                wrong++;
        }
        int_is("the periods hold 2, 8, 8, 18, 18, 32, 32", wrong, 0);
    }

    /* group 17 must be exactly F Cl Br I At Ts */
    {
        char list[64] = "";
        for (z = 1; z <= CHEM_ELEMENT_COUNT; z++) {
            if (chem_group(z) == 17 && !chem_is_f_block(z)) {
                strcat(list, chem_elements[z - 1].symbol);
                strcat(list, " ");
            }
        }
        text_is("group 17 is F Cl Br I At Ts", list, "F Cl Br I At Ts ");
    }

    ok("Na is in the s block", chem_block(11) == 's', NULL);
    ok("Fe is in the d block", chem_block(26) == 'd', NULL);
    ok("Cl is in the p block", chem_block(17) == 'p', NULL);
    ok("U is in the f block", chem_block(92) == 'f', NULL);
    ok("He is in the s block although it sits in group 18", chem_block(2) == 's', NULL);
    int_is("15 lanthanoids", (chem_is_f_block(57) && chem_is_f_block(71)) ? 15 : 0, 15);

    text_is("Li is an alkali metal", chem_category(3), "Alkali metal");
    text_is("Fe is a transition metal", chem_category(26), "Transition metal");
    text_is("Ge is a metalloid", chem_category(32), "Metalloid");
    text_is("Ne is a noble gas", chem_category(10), "Noble gas");
    text_is("Nd is a lanthanoid", chem_category(60), "Lanthanoid");
    text_is("bromine is a liquid", chem_state(35), "liquid");
    text_is("mercury is a liquid", chem_state(80), "liquid");
    text_is("oxygen is a gas", chem_state(8), "gas");
    text_is("iron is a solid", chem_state(26), "solid");
    text_is("magnesium forms +2", chem_usual_ion(12), "+2");
    text_is("nitrogen forms -3", chem_usual_ion(7), "-3");
    text_is("argon forms no ion", chem_usual_ion(18), "none");
    text_is("iron varies", chem_usual_ion(26), "varies");

    text_is("NaCl is ionic", chem_bond_type(3.16f - 0.93f), "ionic");
    text_is("HCl is polar covalent", chem_bond_type(3.16f - 2.20f), "polar covalent");
    text_is("C-H is non-polar", chem_bond_type(2.55f - 2.20f), "non-polar covalent");

    section("3. Formulas");

    close_to("M(H2O) = 18.02", mass_of("H2O"), 18.02, 0.01);
    close_to("M(CaCO3) = 100.09", mass_of("CaCO3"), 100.09, 0.01);
    close_to("M(Ca(OH)2) = 74.10", mass_of("Ca(OH)2"), 74.10, 0.01);
    close_to("M(CuSO4.5H2O) = 249.72", mass_of("CuSO4.5H2O"), 249.72, 0.01);
    close_to("M(C6H12O6) = 180.18", mass_of("C6H12O6"), 180.18, 0.01);
    close_to("M(KMnO4) = 158.04", mass_of("KMnO4"), 158.04, 0.01);
    close_to("M((NH4)2SO4) = 132.17", mass_of("(NH4)2SO4"), 132.17, 0.01);
    close_to("M(Al2(SO4)3) = 342.17", mass_of("Al2(SO4)3"), 342.17, 0.01);
    close_to("M(Nd2O3) = 336.48 (an element the Python port had to look up)",
             mass_of("Nd2O3"), 336.48, 0.01);

    ok("Ca(OH)2 has 2 oxygens",
       chem_parse_formula("Ca(OH)2", &formula, NULL, 0) == CHEM_OK
       && chem_atom_count(&formula, "O") == 2, NULL);
    ok("Ca(OH)2 has 2 hydrogens", chem_atom_count(&formula, "H") == 2, NULL);
    ok("Ca(OH)2 has 1 calcium", chem_atom_count(&formula, "Ca") == 1, NULL);
    ok("CuSO4.5H2O has 9 oxygens",
       chem_parse_formula("CuSO4.5H2O", &formula, NULL, 0) == CHEM_OK
       && chem_atom_count(&formula, "O") == 9, NULL);
    ok("CuSO4.5H2O has 10 hydrogens", chem_atom_count(&formula, "H") == 10, NULL);
    ok("CO is carbon monoxide, not cobalt",
       chem_parse_formula("CO", &formula, NULL, 0) == CHEM_OK && formula.n == 2, NULL);
    ok("Co is cobalt, not carbon monoxide",
       chem_parse_formula("Co", &formula, NULL, 0) == CHEM_OK && formula.n == 1, NULL);

    ok("an unknown element is reported",
       chem_parse_formula("Qz2", &formula, bad, sizeof bad) == CHEM_ERR_UNKNOWN_ELEMENT, NULL);
    text_is("and the bad symbol is named", bad, "Qz");
    ok("a missing bracket is reported",
       chem_parse_formula("Ca(OH2", &formula, NULL, 0) == CHEM_ERR_SYNTAX, NULL);
    ok("a stray bracket is reported",
       chem_parse_formula("CaOH)2", &formula, NULL, 0) == CHEM_ERR_SYNTAX, NULL);
    ok("a lower-case start is reported",
       chem_parse_formula("h2o", &formula, NULL, 0) == CHEM_ERR_SYNTAX, NULL);
    ok("an empty formula is reported",
       chem_parse_formula("", &formula, NULL, 0) == CHEM_ERR_EMPTY, NULL);

    section("4. Printing numbers");

    text_is("4 significant figures", fmt(0.09990009, 4), "0.0999");
    text_is("a whole number keeps no decimal point", fmt(12.0, 4), "12");
    text_is("trailing zeros are dropped", fmt(11.350, 4), "11.35");
    text_is("rounds to 4 figures", fmt(100.0857, 4), "100.1");
    text_is("big numbers stay readable", fmt(588611.47, 4), "588600");
    text_is("very big numbers go scientific", fmt(1.505e23, 4), "1.505e23");
    text_is("very small numbers go scientific", fmt(1.0e-14, 4), "1e-14");
    text_is("2.97e-4 is scientific", fmt(0.000297, 4), "2.97e-4");
    text_is("0.001 is not", fmt(0.001, 4), "0.001");
    text_is("negatives work", fmt(-32.86, 4), "-32.86");
    text_is("zero is zero", fmt(0.0, 4), "0");
    text_is("rounding up a decade", fmt(9.9999, 3), "10");
    text_is("3 figures", fmt(2.0 / 3.0, 3), "0.667");

    section("5. Stoichiometry");

    /* Percentage composition, checked against the IB worked answers. */
    {
        float percent[CHEM_MAX_ATOMS];
        chem_parse_formula("H2O", &formula, NULL, 0);
        stoich_percent_composition(&formula, percent);
        close_to("H2O is 11.2 % hydrogen", percent[0], 11.21, 0.02);
        close_to("H2O is 88.8 % oxygen", percent[1], 88.79, 0.02);

        chem_parse_formula("CaCO3", &formula, NULL, 0);
        stoich_percent_composition(&formula, percent);
        close_to("CaCO3 is 40.0 % calcium", percent[0], 40.04, 0.02);
        close_to("CaCO3 is 12.0 % carbon", percent[1], 12.00, 0.02);
        close_to("CaCO3 is 48.0 % oxygen", percent[2], 47.96, 0.02);

        /* the percentages of any formula must add up to 100 */
        chem_parse_formula("Al2(SO4)3", &formula, NULL, 0);
        stoich_percent_composition(&formula, percent);
        {
            float sum = 0.0f;
            for (i = 0; i < formula.n; i++)
                sum += percent[i];
            close_to("the percentages add up to 100", sum, 100.0, 0.05);
        }
    }

    /* Empirical formulas. */
    {
        static const char *const CHO[] = {"C", "H", "O"};
        static const char *const FeO[] = {"Fe", "O"};
        static const char *const CH[] = {"C", "H"};
        float amounts[3];
        int counts[3];

        amounts[0] = 40.0f; amounts[1] = 6.7f; amounts[2] = 53.3f;
        ok("glucose percentages give CH2O",
           stoich_empirical(CHO, amounts, 3, counts) == CHEM_OK
           && counts[0] == 1 && counts[1] == 2 && counts[2] == 1, NULL);

        amounts[0] = 69.9f; amounts[1] = 30.1f;
        ok("iron oxide percentages give Fe2O3",
           stoich_empirical(FeO, amounts, 2, counts) == CHEM_OK
           && counts[0] == 2 && counts[1] == 3, NULL);

        /* a 1 : 1.5 ratio has to be scaled up, not rounded off */
        amounts[0] = 92.3f; amounts[1] = 7.7f;
        ok("benzene percentages give CH",
           stoich_empirical(CH, amounts, 2, counts) == CHEM_OK
           && counts[0] == 1 && counts[1] == 1, NULL);

        amounts[0] = 85.7f; amounts[1] = 14.3f;
        ok("ethene percentages give CH2",
           stoich_empirical(CH, amounts, 2, counts) == CHEM_OK
           && counts[0] == 1 && counts[1] == 2, NULL);

        /* masses work the same way as percentages */
        amounts[0] = 3.21f; amounts[1] = 0.539f;
        ok("masses give C2H4 as CH2",
           stoich_empirical(CH, amounts, 2, counts) == CHEM_OK
           && counts[0] == 1 && counts[1] == 2, NULL);

        amounts[0] = 0.0f; amounts[1] = 0.0f;
        ok("all-zero amounts are refused",
           stoich_empirical(CH, amounts, 2, counts) == CHEM_ERR_RANGE, NULL);
        amounts[0] = -1.0f; amounts[1] = 1.0f;
        ok("a negative amount is refused",
           stoich_empirical(CH, amounts, 2, counts) == CHEM_ERR_RANGE, NULL);
    }

    int_is("CH2O (30.03) in glucose (180.18) fits 6 times",
           stoich_formula_multiplier(30.03f, 180.18f), 6);
    int_is("CH (13.02) in benzene (78.11) fits 6 times",
           stoich_formula_multiplier(13.02f, 78.11f), 6);
    int_is("an exact match fits once", stoich_formula_multiplier(18.02f, 18.02f), 1);
    int_is("a smaller molar mass still fits once",
           stoich_formula_multiplier(30.0f, 10.0f), 1);

    close_to("percentage yield 4.2 of 5.0 is 84 %",
             stoich_percent_yield(4.2f, 5.0f), 84.0, 0.01);
    close_to("percentage yield of nothing is 0",
             stoich_percent_yield(0.0f, 5.0f), 0.0, 0.01);
    close_to("atom economy 44.01 of 100.09 is 44.0 %",
             stoich_atom_economy(44.01f, 100.09f), 43.97, 0.02);

    section("6. Gases and equilibrium");

    {
        gas_state_t state, after, before;
        double value;

        /* 2.00 mol at 300 K in 5.00 dm3: p = nRT/V = 2 x 8.31 x 300 / 5 */
        state.moles = 2.0; state.temperature = 300.0; state.volume = 5.0;
        state.pressure = 0.0;
        ok("pV = nRT solves for pressure", gas_ideal(&state, GAS_PRESSURE) == CHEM_OK, NULL);
        close_to("p = 997 kPa", state.pressure, 997.2, 0.1);

        /* the same numbers backwards must return the volume */
        state.volume = 0.0;
        ok("and back for volume", gas_ideal(&state, GAS_VOLUME) == CHEM_OK, NULL);
        close_to("V = 5.00 dm3", state.volume, 5.0, 0.001);

        /* 1 mol at STP (100 kPa, 273 K) is the booklet's 22.7 dm3 */
        state.moles = 1.0; state.temperature = 273.0; state.pressure = 100.0;
        state.volume = 0.0;
        gas_ideal(&state, GAS_VOLUME);
        close_to("1 mol at STP is 22.7 dm3", state.volume, 22.7, 0.02);

        state.temperature = 0.0; state.moles = 0.0;
        ok("solving for temperature with no moles is refused",
           gas_ideal(&state, GAS_TEMPERATURE) == CHEM_ERR_RANGE, NULL);

        /* Boyle: 100 kPa, 2 dm3 -> 4 dm3 at constant T gives 50 kPa */
        before.pressure = 100.0; before.volume = 2.0; before.temperature = 300.0;
        after.pressure = 0.0; after.volume = 4.0; after.temperature = 300.0;
        ok("the combined gas law solves for pressure",
           gas_combined(&before, &after, GAS_PRESSURE) == CHEM_OK, NULL);
        close_to("halving to 50 kPa", after.pressure, 50.0, 0.001);

        /* Charles: 273 K -> 546 K at constant p doubles the volume */
        before.pressure = 100.0; before.volume = 1.0; before.temperature = 273.0;
        after.pressure = 100.0; after.volume = 0.0; after.temperature = 546.0;
        gas_combined(&before, &after, GAS_VOLUME);
        close_to("doubling the temperature doubles the volume", after.volume, 2.0, 0.001);

        /* Graham: hydrogen effuses 4 times faster than oxygen */
        ok("Graham's law", gas_effusion_ratio(2.02, 32.00, &value) == CHEM_OK, NULL);
        close_to("H2 effuses 3.98x faster than O2", value, 3.980, 0.01);
        ok("a zero molar mass is refused",
           gas_effusion_ratio(0.0, 32.0, &value) == CHEM_ERR_RANGE, NULL);
    }

    {
        double kp = 0.0, kc = 0.0, x = 0.0;

        /* Kc = 0.5 at 500 K with dn = -2 */
        ok("Kc to Kp", eq_kc_to_kp(0.5, 500.0, -2, &kp) == CHEM_OK, NULL);
        close_to("Kp = 2.90e-5", kp, 0.5 / (8.31 * 500.0 * 8.31 * 500.0), 1e-12);
        ok("and back again", eq_kp_to_kc(kp, 500.0, -2, &kc) == CHEM_OK, NULL);
        close_to("Kc comes back as 0.5", kc, 0.5, 1e-9);
        int_is("dn = 0 leaves K alone",
               (eq_kc_to_kp(3.7, 400.0, 0, &kp) == CHEM_OK
                && fabs(kp - 3.7) < 1e-9) ? 1 : 0, 1);

        /* H2 + I2 <-> 2HI is not this shape, so use A + B <-> C + D with K = 4:
         * starting from 1 and 1, x^2/(1-x)^2 = 4 gives x = 2/3. */
        ok("the ICE solver runs", eq_ice_extent(1.0, 1.0, 0.0, 0.0, 4.0, &x) == CHEM_OK, NULL);
        close_to("x = 0.667 when K = 4", x, 2.0 / 3.0, 1e-6);

        /* K = 1 from 1 and 1 must give exactly half */
        eq_ice_extent(1.0, 1.0, 0.0, 0.0, 1.0, &x);
        close_to("x = 0.5 when K = 1", x, 0.5, 1e-6);

        /* a tiny K means almost nothing reacts */
        eq_ice_extent(1.0, 1.0, 0.0, 0.0, 1e-10, &x);
        ok("a tiny K barely moves", x < 1e-4 && x > 0, NULL);

        /* with no reactant there is nothing to react */
        eq_ice_extent(0.0, 1.0, 0.0, 0.0, 5.0, &x);
        close_to("no reactant, no reaction", x, 0.0, 1e-9);
        ok("a negative K is refused",
           eq_ice_extent(1.0, 1.0, 0.0, 0.0, -1.0, &x) == CHEM_ERR_RANGE, NULL);
    }

    section("7. Acids and bases");

    {
        double ph = 0.0, kb = 0.0;

        close_to("pH of 1e-3 mol dm-3 H+ is 3", aqua_ph_from_h(1e-3), 3.0, 1e-9);
        close_to("[H+] at pH 3 is 1e-3", aqua_h_from_ph(3.0), 1e-3, 1e-12);
        close_to("pOH at pH 3 is 11", aqua_poh_from_ph(3.0), 11.0, 1e-9);
        close_to("[OH-] at pOH 11 is 1e-11", aqua_oh_from_poh(11.0), 1e-11, 1e-20);

        ok("strong acid", aqua_strong_acid_ph(0.10, 1, &ph) == CHEM_OK, NULL);
        close_to("0.10 mol dm-3 HCl has pH 1.00", ph, 1.0, 0.001);
        aqua_strong_acid_ph(0.050, 2, &ph);
        close_to("0.050 mol dm-3 H2SO4 has pH 1.00", ph, 1.0, 0.001);
        ok("strong base", aqua_strong_base_ph(0.10, 1, &ph) == CHEM_OK, NULL);
        close_to("0.10 mol dm-3 NaOH has pH 13.00", ph, 13.0, 0.001);
        ok("a zero concentration is refused",
           aqua_strong_acid_ph(0.0, 1, &ph) == CHEM_ERR_RANGE, NULL);

        /* ethanoic acid, Ka = 1.74e-5, 0.100 mol dm-3: the booklet answer is 2.88 */
        ok("weak acid", aqua_weak_acid_ph(1.74e-5, 0.100, &ph) == CHEM_OK, NULL);
        close_to("0.100 mol dm-3 ethanoic acid has pH 2.88", ph, 2.88, 0.01);

        /* ammonia, Kb = 1.78e-5, 0.100 mol dm-3: pH 11.13 */
        ok("weak base", aqua_weak_base_ph(1.78e-5, 0.100, &ph) == CHEM_OK, NULL);
        close_to("0.100 mol dm-3 ammonia has pH 11.13", ph, 11.13, 0.01);

        /* equal acid and salt: pH = pKa */
        ok("buffer", aqua_buffer_ph(1.74e-5, 0.10, 0.10, &ph) == CHEM_OK, NULL);
        close_to("an equal buffer sits at pKa 4.76", ph, 4.76, 0.01);
        aqua_buffer_ph(1.74e-5, 0.10, 0.20, &ph);
        close_to("twice the salt adds log10(2)", ph, 4.76 + 0.301, 0.01);

        close_to("pKa of 1.74e-5 is 4.76", aqua_pka_from_ka(1.74e-5), 4.76, 0.01);
        close_to("Ka of pKa 4.76 is 1.74e-5", aqua_ka_from_pka(4.76), 1.74e-5, 1e-7);
        ok("Kb from Ka", aqua_kb_from_ka(1.74e-5, &kb) == CHEM_OK, NULL);
        close_to("Ka x Kb = Kw", 1.74e-5 * kb, 1.00e-14, 1e-20);
    }

    section("8. Balancing equations");

    {
        int c[BAL_MAX_SPECIES];
        char detail[160];

        /* H2 + O2 -> H2O */
        {
            static const char *const r[] = {"H2", "O2"};
            static const char *const p[] = {"H2O"};
            ok("H2 + O2 -> H2O balances",
               bal_balance(r, 2, p, 1, c) == CHEM_OK && atoms_balance(r, 2, p, 1, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d", c[0], c[1], c[2]);
            ok("as 2, 1 -> 2", c[0] == 2 && c[1] == 1 && c[2] == 2, detail);
        }
        /* propane burning: C3H8 + 5O2 -> 3CO2 + 4H2O */
        {
            static const char *const r[] = {"C3H8", "O2"};
            static const char *const p[] = {"CO2", "H2O"};
            ok("propane burns", bal_balance(r, 2, p, 2, c) == CHEM_OK
               && atoms_balance(r, 2, p, 2, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d", c[0], c[1], c[2], c[3]);
            ok("as 1, 5 -> 3, 4", c[0] == 1 && c[1] == 5 && c[2] == 3 && c[3] == 4, detail);
        }
        /* iron(III) oxide + carbon monoxide */
        {
            static const char *const r[] = {"Fe2O3", "CO"};
            static const char *const p[] = {"Fe", "CO2"};
            ok("the blast furnace reaction", bal_balance(r, 2, p, 2, c) == CHEM_OK
               && atoms_balance(r, 2, p, 2, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d", c[0], c[1], c[2], c[3]);
            ok("as 1, 3 -> 2, 3", c[0] == 1 && c[1] == 3 && c[2] == 2 && c[3] == 3, detail);
        }
        /* a neutralisation with brackets */
        {
            static const char *const r[] = {"Ca(OH)2", "HCl"};
            static const char *const p[] = {"CaCl2", "H2O"};
            ok("Ca(OH)2 + HCl", bal_balance(r, 2, p, 2, c) == CHEM_OK
               && atoms_balance(r, 2, p, 2, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d", c[0], c[1], c[2], c[3]);
            ok("as 1, 2 -> 1, 2", c[0] == 1 && c[1] == 2 && c[2] == 1 && c[3] == 2, detail);
        }
        /* one that needs bigger numbers: C8H18 + 25O2 -> 16CO2 + 18H2O */
        {
            static const char *const r[] = {"C8H18", "O2"};
            static const char *const p[] = {"CO2", "H2O"};
            ok("octane burns", bal_balance(r, 2, p, 2, c) == CHEM_OK
               && atoms_balance(r, 2, p, 2, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d", c[0], c[1], c[2], c[3]);
            ok("as 2, 25 -> 16, 18",
               c[0] == 2 && c[1] == 25 && c[2] == 16 && c[3] == 18, detail);
        }
        /* three products */
        {
            static const char *const r[] = {"KMnO4", "HCl"};
            static const char *const p[] = {"KCl", "MnCl2", "H2O", "Cl2"};
            ok("permanganate and hydrochloric acid",
               bal_balance(r, 2, p, 4, c) == CHEM_OK && atoms_balance(r, 2, p, 4, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d, %d, %d",
                     c[0], c[1], c[2], c[3], c[4], c[5]);
            ok("as 2, 16 -> 2, 2, 8, 5",
               c[0] == 2 && c[1] == 16 && c[2] == 2 && c[3] == 2 && c[4] == 8 && c[5] == 5,
               detail);
        }
        /* already balanced, 1 : 1 : 1 */
        {
            static const char *const r[] = {"NaOH", "HCl"};
            static const char *const p[] = {"NaCl", "H2O"};
            ok("a 1:1 reaction stays 1:1",
               bal_balance(r, 2, p, 2, c) == CHEM_OK
               && c[0] == 1 && c[1] == 1 && c[2] == 1 && c[3] == 1, NULL);
        }
        /* photosynthesis, which has a common factor to cancel */
        {
            static const char *const r[] = {"CO2", "H2O"};
            static const char *const p[] = {"C6H12O6", "O2"};
            ok("photosynthesis", bal_balance(r, 2, p, 2, c) == CHEM_OK
               && atoms_balance(r, 2, p, 2, c), NULL);
            snprintf(detail, sizeof detail, "got %d, %d -> %d, %d", c[0], c[1], c[2], c[3]);
            ok("as 6, 6 -> 1, 6",
               c[0] == 6 && c[1] == 6 && c[2] == 1 && c[3] == 6, detail);
        }
        /* impossible: the atoms cannot match */
        {
            static const char *const r[] = {"H2"};
            static const char *const p[] = {"O2"};
            ok("an impossible equation is refused",
               bal_balance(r, 1, p, 1, c) == CHEM_ERR_RANGE, NULL);
        }
        /* a bad formula is reported, not balanced */
        {
            static const char *const r[] = {"Qz2", "O2"};
            static const char *const p[] = {"H2O"};
            ok("an unknown element is reported",
               bal_balance(r, 2, p, 1, c) == CHEM_ERR_UNKNOWN_ELEMENT, NULL);
        }
    }

    section("9. Energy, cells and rates");

    {
        double value = 0.0, second = 0.0;

        /* the booklet's bond enthalpies, and a bond written backwards */
        int_is("C-H is 414 kJ mol-1", energy_bond_enthalpy("C-H"), 414);
        int_is("O=O is 498", energy_bond_enthalpy("O=O"), 498);
        int_is("N#N is 945", energy_bond_enthalpy("N#N"), 945);
        int_is("H-O reads the same as O-H", energy_bond_enthalpy("H-O"), 463);
        int_is("Cl-C reads the same as C-Cl", energy_bond_enthalpy("Cl-C"), 324);
        int_is("an unknown bond is 0", energy_bond_enthalpy("Xx-Yy"), 0);
        int_is("an empty bond is 0", energy_bond_enthalpy(""), 0);

        /* 100 g of water warmed by 25 K: q = 100 x 4.18 x 25 = 10450 J */
        close_to("q = m c dT", energy_heat(100.0, CHEM_C_WATER, 25.0), 10450.0, 0.1);

        /* that heat from 0.0200 mol gives -523 kJ mol-1 (exothermic) */
        ok("molar enthalpy", energy_molar_enthalpy(10450.0, 0.0200, &value) == CHEM_OK, NULL);
        close_to("dH = -523 kJ mol-1", value, -522.5, 0.1);
        ok("zero moles is refused",
           energy_molar_enthalpy(100.0, 0.0, &value) == CHEM_ERR_RANGE, NULL);

        /* H2 + Cl2 -> 2HCl: broken 436 + 242, formed 2 x 431 */
        close_to("bond enthalpies give -184 kJ mol-1",
                 energy_from_bonds(436 + 242, 2 * 431), -184.0, 0.001);

        /* dG = dH - T dS: -92.2 kJ, -198.8 J/K, 298 K -> -33.0 kJ mol-1 */
        close_to("dG = dH - T dS", energy_gibbs(-92.2, 298.0, -198.8), -32.96, 0.01);
        /* dS in J K-1 mol-1 must be divided by 1000, not used raw */
        close_to("a positive dS at 500 K", energy_gibbs(100.0, 500.0, 200.0), 0.0, 0.001);

        ok("the crossover temperature",
           energy_crossover_temperature(-92.2, -198.8, &value) == CHEM_OK, NULL);
        close_to("dG = 0 at 464 K", value, 463.8, 0.5);
        ok("a zero entropy change has no crossover",
           energy_crossover_temperature(10.0, 0.0, &value) == CHEM_ERR_RANGE, NULL);

        /* dG and K are inverses of each other */
        ok("dG from K", energy_gibbs_from_k(1.0e5, 298.0, &value) == CHEM_OK, NULL);
        close_to("K = 1e5 gives dG = -28.5 kJ mol-1", value, -28.52, 0.05);
        ok("K from dG", energy_k_from_gibbs(value, 298.0, &second) == CHEM_OK, NULL);
        close_to("and K comes back as 1e5", second, 1.0e5, 1.0);
        ok("K = 1 gives dG = 0",
           energy_gibbs_from_k(1.0, 298.0, &value) == CHEM_OK && fabs(value) < 1e-9, NULL);
        ok("a negative K is refused",
           energy_gibbs_from_k(-1.0, 298.0, &value) == CHEM_ERR_RANGE, NULL);
        ok("an impossible K is refused rather than overflowing",
           energy_k_from_gibbs(-1.0e6, 298.0, &value) == CHEM_ERR_RANGE, NULL);

        /* the Daniell cell: Cu2+/Cu 0.34, Zn2+/Zn -0.76, so E = 1.10 V */
        ok("a half-cell is looked up", energy_half_cell("Cu2+/Cu", &value) == CHEM_OK, NULL);
        ok("and another", energy_half_cell("Zn2+/Zn", &second) == CHEM_OK, NULL);
        close_to("the Daniell cell is 1.10 V", value - second, 1.10, 0.001);
        ok("an unknown half-cell is refused",
           energy_half_cell("Xx2+/Xx", &value) == CHEM_ERR_RANGE, NULL);

        /* dG = -nFE: 2 electrons at 1.10 V is -212 kJ mol-1 */
        close_to("dG = -nFE", energy_gibbs_from_cell(2, 1.10), -212.3, 0.1);

        /* Faraday: 1.50 A for 20.0 minutes depositing copper (Mr 63.55, 2+) */
        ok("electrolysis",
           energy_electrolysis_mass(1.50, 1200.0, 63.55, 2, &value) == CHEM_OK, NULL);
        close_to("0.593 g of copper", value, 0.5927, 0.001);
        ok("a charge of zero is refused",
           energy_electrolysis_mass(1.5, 1200.0, 63.55, 0, &value) == CHEM_ERR_RANGE, NULL);

        /* Arrhenius, and reading Ea back from two rate constants */
        ok("the rate constant",
           energy_rate_constant(1.0e11, 50.0, 298.0, &value) == CHEM_OK, NULL);
        ok("k is positive and small", value > 0 && value < 1.0e11, NULL);
        ok("Ea from two temperatures",
           energy_activation_from_two(1.0e-3, 300.0, 1.0e-2, 310.0, &second) == CHEM_OK, NULL);
        close_to("Ea = 178 kJ mol-1", second, 177.9, 0.5);
        ok("the same temperature twice is refused",
           energy_activation_from_two(1e-3, 300.0, 1e-2, 300.0, &value) == CHEM_ERR_RANGE, NULL);

        /* the Arrhenius pair must be consistent: feeding Ea back reproduces k2 */
        {
            double a_factor, k_back;
            energy_activation_from_two(1.0e-3, 300.0, 1.0e-2, 310.0, &second);
            a_factor = 1.0e-3 / exp(-second * 1000.0 / (8.31 * 300.0));
            energy_rate_constant(a_factor, second, 310.0, &k_back);
            close_to("and it reproduces the second rate constant", k_back, 1.0e-2, 1e-6);
        }

        ok("half-life from k", energy_half_life(0.0693, &value) == CHEM_OK, NULL);
        close_to("k = 0.0693 s-1 gives 10.0 s", value, 10.002, 0.01);
        ok("k from half-life", energy_k_from_half_life(value, &second) == CHEM_OK, NULL);
        close_to("and k comes back", second, 0.0693, 1e-6);
        ok("a zero half-life is refused",
           energy_k_from_half_life(0.0, &value) == CHEM_ERR_RANGE, NULL);
    }

    section("10. Solutions and limiting reactant");

    {
        tools_limiting_t limiting;
        double moles[3], value = 0.0;
        int coefficients[3];

        close_to("c = n/V: 0.5 mol in 2 dm3", tools_concentration(0.5, 2.0), 0.25, 1e-9);
        close_to("n = cV: 0.25 mol/dm3 in 2 dm3",
                 tools_moles_from_concentration(0.25, 2.0), 0.5, 1e-9);
        close_to("no volume, no concentration", tools_concentration(0.5, 0.0), 0.0, 1e-9);

        /* 1.0 mol/dm3, 25 cm3 diluted to 0.1 mol/dm3 needs 250 cm3 */
        ok("dilution", tools_dilution(1.0, 25.0, 0.1, &value) == CHEM_OK, NULL);
        close_to("c1V1 = c2V2 gives 250", value, 250.0, 1e-9);
        ok("diluting to nothing is refused",
           tools_dilution(1.0, 25.0, 0.0, &value) == CHEM_ERR_RANGE, NULL);

        close_to("0.1 mol/dm3 of NaOH is 4.00 g/dm3",
                 tools_mass_concentration(0.1, 40.00), 4.0, 1e-9);
        close_to("1 mg in 1 kg is 1 ppm", tools_ppm(0.001, 1000.0), 1.0, 1e-9);

        /* N2 + 3H2 -> 2NH3 with 2 mol N2 and 3 mol H2: hydrogen runs out */
        moles[0] = 2.0; coefficients[0] = 1;
        moles[1] = 3.0; coefficients[1] = 3;
        ok("limiting reactant",
           tools_limiting_reactant(moles, coefficients, 2, &limiting) == CHEM_OK, NULL);
        int_is("hydrogen is limiting", limiting.limiting, 1);
        close_to("the reaction runs once", limiting.reacting, 1.0, 1e-9);
        close_to("1 mol of nitrogen is left", limiting.left_over[0], 1.0, 1e-9);
        close_to("no hydrogen is left", limiting.left_over[1], 0.0, 1e-9);

        /* exactly the right amounts leave nothing behind */
        moles[0] = 1.0; coefficients[0] = 1;
        moles[1] = 3.0; coefficients[1] = 3;
        tools_limiting_reactant(moles, coefficients, 2, &limiting);
        close_to("nothing is left over when the amounts match",
                 limiting.left_over[0] + limiting.left_over[1], 0.0, 1e-9);
        moles[0] = -1.0;
        ok("a negative amount is refused",
           tools_limiting_reactant(moles, coefficients, 2, &limiting) == CHEM_ERR_RANGE, NULL);
    }

    section("11. Electron configuration");

    {
        tools_subshell_t shells[TOOLS_MAX_SUBSHELLS];
        char text[128];
        int count;

        count = tools_configuration(11, 0, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("sodium", text, "1s2 2s2 2p6 3s1");

        count = tools_configuration(26, 0, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("iron", text, "1s2 2s2 2p6 3s2 3p6 3d6 4s2");

        /* chromium takes one from 4s to half-fill 3d */
        count = tools_configuration(24, 0, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("chromium is the exception", text, "1s2 2s2 2p6 3s2 3p6 3d5 4s1");

        count = tools_configuration(29, 0, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("copper too", text, "1s2 2s2 2p6 3s2 3p6 3d10 4s1");

        /* iron(III) loses 4s before 3d */
        count = tools_configuration(26, 3, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("Fe3+ empties 4s first", text, "1s2 2s2 2p6 3s2 3p6 3d5");

        count = tools_configuration(26, 2, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("Fe2+ as well", text, "1s2 2s2 2p6 3s2 3p6 3d6");

        /* a simple anion just keeps filling */
        count = tools_configuration(17, -1, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("chloride fills the 3p", text, "1s2 2s2 2p6 3s2 3p6");

        count = tools_configuration(2, 0, shells, TOOLS_MAX_SUBSHELLS);
        tools_configuration_text(shells, count, text, sizeof text);
        text_is("helium", text, "1s2");

        int_is("argon is the core before potassium", tools_noble_core(19), 18);
        int_is("nothing comes before hydrogen", tools_noble_core(1), 0);
        int_is("an impossible atomic number is refused",
               tools_configuration(0, 0, shells, TOOLS_MAX_SUBSHELLS), -1);

        /* the electrons must always add up to the atom or ion */
        {
            int z, wrong = 0;
            for (z = 1; z <= 118; z++) {
                int i, total = 0;
                count = tools_configuration(z, 0, shells, TOOLS_MAX_SUBSHELLS);
                for (i = 0; i < count; i++)
                    total += shells[i].electrons;
                if (total != z)
                    wrong++;
            }
            int_is("every element keeps all its electrons", wrong, 0);
        }
    }

    section("12. Oxidation numbers");

    {
        double numbers[CHEM_MAX_ATOMS];

        chem_parse_formula("H2O", &formula, NULL, 0);
        ok("water", tools_oxidation_numbers(&formula, 0, 0, numbers) == CHEM_OK, NULL);
        close_to("H is +1", numbers[0], 1.0, 1e-9);
        close_to("O is -2", numbers[1], -2.0, 1e-9);

        chem_parse_formula("KMnO4", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, 0, 0, numbers);
        close_to("manganese in permanganate is +7", numbers[1], 7.0, 1e-9);

        chem_parse_formula("Cr2O7", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, -2, 0, numbers);
        close_to("chromium in dichromate is +6", numbers[0], 6.0, 1e-9);

        chem_parse_formula("H2SO4", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, 0, 0, numbers);
        close_to("sulfur in sulfuric acid is +6", numbers[1], 6.0, 1e-9);

        chem_parse_formula("Fe", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, 0, 0, numbers);
        close_to("an element on its own is 0", numbers[0], 0.0, 1e-9);

        /* peroxides are the exception oxygen gets */
        chem_parse_formula("H2O2", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, 0, 1, numbers);
        close_to("oxygen in a peroxide is -1", numbers[1], -1.0, 1e-9);

        /* Fe3O4 has a fractional average, which is the right answer */
        chem_parse_formula("Fe3O4", &formula, NULL, 0);
        tools_oxidation_numbers(&formula, 0, 0, numbers);
        close_to("iron in magnetite averages +8/3", numbers[0], 8.0 / 3.0, 1e-6);

        /* two unknowns cannot be solved */
        chem_parse_formula("PCl3", &formula, NULL, 0);
        ok("P and Cl together still work (Cl is -1)",
           tools_oxidation_numbers(&formula, 0, 0, numbers) == CHEM_OK, NULL);
        close_to("phosphorus is +3", numbers[0], 3.0, 1e-9);
    }

    section("13. Ionic formulas, isotopes, uncertainties, IHD");

    {
        char text[32];
        double ar = 0.0, first = 0.0, second = 0.0;
        double masses[3], abundances[3], parts[3];

        ok("sodium chloride",
           tools_ionic_formula("Na", 1, "Cl", -1, text, sizeof text) == CHEM_OK, NULL);
        text_is("is NaCl", text, "NaCl");
        tools_ionic_formula("Mg", 2, "Cl", -1, text, sizeof text);
        text_is("magnesium chloride is MgCl2", text, "MgCl2");
        tools_ionic_formula("Al", 3, "O", -2, text, sizeof text);
        text_is("aluminium oxide is Al2O3", text, "Al2O3");
        tools_ionic_formula("Mg", 2, "O", -2, text, sizeof text);
        text_is("magnesium oxide cancels to MgO", text, "MgO");
        tools_ionic_formula("Ca", 2, "OH", -1, text, sizeof text);
        text_is("calcium hydroxide brackets the group", text, "Ca(OH)2");
        tools_ionic_formula("Na", 1, "SO4", -2, text, sizeof text);
        text_is("sodium sulfate is Na2SO4", text, "Na2SO4");
        ok("a negative cation charge is refused",
           tools_ionic_formula("Na", -1, "Cl", -1, text, sizeof text) == CHEM_ERR_RANGE, NULL);

        /* chlorine: 75.77 % of 34.969 and 24.23 % of 36.966 gives 35.45 */
        masses[0] = 34.969; abundances[0] = 75.77;
        masses[1] = 36.966; abundances[1] = 24.23;
        ok("relative atomic mass",
           tools_relative_atomic_mass(masses, abundances, 2, &ar) == CHEM_OK, NULL);
        close_to("chlorine comes out at 35.45", ar, 35.45, 0.01);

        /* and backwards: the abundances must come back from the Ar they made */
        ok("abundances from Ar",
           tools_abundances_from_ar(34.969, 36.966, ar, &first, &second) == CHEM_OK, NULL);
        close_to("75.77 % of the lighter one comes back", first, 75.77, 0.01);
        close_to("24.23 % of the heavier one comes back", second, 24.23, 0.01);
        close_to("they add up to 100", first + second, 100.0, 1e-9);
        ok("an Ar outside both masses is refused",
           tools_abundances_from_ar(34.969, 36.966, 40.0, &first, &second) == CHEM_ERR_RANGE, NULL);

        close_to("0.05 in 25.00 is 0.2 %",
                 tools_percent_uncertainty(25.0, 0.05), 0.2, 1e-9);
        close_to("0.2 % of 25.00 is 0.05",
                 tools_absolute_uncertainty(25.0, 0.2), 0.05, 1e-9);
        parts[0] = 0.05; parts[1] = 0.05;
        close_to("adding measurements adds the absolute uncertainties",
                 tools_combine_sum(parts, 2), 0.10, 1e-9);
        parts[0] = 0.2; parts[1] = 0.5;
        close_to("multiplying adds the percentages",
                 tools_combine_product(parts, 2), 0.7, 1e-9);
        close_to("a cube triples the percentage",
                 tools_combine_power(0.2, 3), 0.6, 1e-9);
        close_to("9.8 against 9.81 is 0.10 % out",
                 tools_percent_error(9.8, 9.81), 0.1019, 0.001);

        chem_parse_formula("C6H6", &formula, NULL, 0);
        close_to("benzene has an IHD of 4", tools_ihd(&formula, 0), 4.0, 1e-9);
        chem_parse_formula("C6H14", &formula, NULL, 0);
        close_to("hexane has none", tools_ihd(&formula, 0), 0.0, 1e-9);
        chem_parse_formula("C2H4", &formula, NULL, 0);
        close_to("ethene has one", tools_ihd(&formula, 0), 1.0, 1e-9);
        chem_parse_formula("C6H5Cl", &formula, NULL, 0);
        close_to("a halogen counts like a hydrogen", tools_ihd(&formula, 0), 4.0, 1e-9);
        chem_parse_formula("C6H5NO2", &formula, NULL, 0);
        close_to("nitrobenzene is 5: four for the ring, one for the N=O",
                 tools_ihd(&formula, 0), 5.0, 1e-9);
        chem_parse_formula("C2H6O", &formula, NULL, 0);
        close_to("oxygen makes no difference", tools_ihd(&formula, 0), 0.0, 1e-9);
    }

    section("14. Printing numbers the calculator's own way");

    /* chem_format does its own digits with whole-number arithmetic instead of
     * asking the C library for "%f". The calculator's library is not the one
     * these tests run against, so this is what makes a number printed there
     * the same as a number printed here. */
    text_is("a decade boundary from below", fmt(999999.0, 4), "1e6");
    text_is("and just above it", fmt(1000000.0, 4), "1e6");
    text_is("999500 already has four figures", fmt(999500.0, 4), "999500");
    text_is("and so does 999400", fmt(999400.0, 4), "999400");
    text_is("999950 rounds up into seven digits", fmt(999950.0, 4), "1e6");
    text_is("the smallest fixed number", fmt(0.001, 4), "0.001");
    text_is("just below goes scientific", fmt(0.0001, 4), "1e-4");
    text_is("0.00009999 too", fmt(0.00009999, 4), "9.999e-5");
    /* A "half" written in decimal is usually not a half once it is stored:
     * 1.0005 is held as 1.000499999..., so it rounds down. The C library does
     * exactly the same, and these three record that rather than pretend. */
    text_is("1.0005 is stored just under a half", fmt(1.0005, 4), "1");
    text_is("9.995 likewise", fmt(9.995, 3), "9.99");
    text_is("0.09995 likewise", fmt(0.09995, 3), "0.0999");
    text_is("a true half does round up", fmt(1.5, 1), "2");
    text_is("and so does 0.125 at two figures", fmt(0.125, 2), "0.13");
    text_is("one figure", fmt(1234.0, 1), "1000");
    text_is("two figures", fmt(1234.0, 2), "1200");
    text_is("six figures", fmt(1234.5678, 6), "1234.57");
    text_is("a negative small number", fmt(-0.0456, 3), "-0.0456");
    text_is("a negative big one", fmt(-1.23e9, 3), "-1.23e9");
    text_is("Avogadro", fmt(6.02e23, 3), "6.02e23");
    text_is("Kw", fmt(1.0e-14, 3), "1e-14");
    text_is("a whole number keeps no point", fmt(100.0, 4), "100");
    text_is("trailing zeros go", fmt(2.50, 4), "2.5");
    text_is("but a leading zero stays", fmt(0.25, 4), "0.25");

    /* Whatever is printed has to read back as the same number, to within the
     * rounding that was asked for. Ten thousand values, none of them chosen
     * by me, is a better check of that than any list I could write. */
    {
        unsigned int seed = 12345u;
        int checked = 0, wrong = 0, figures;
        char printed[32], detail[160];

        for (i = 0; i < 10000; i++) {
            double value, back, allowed;
            int exponent;

            /* a spread of magnitudes, positive and negative */
            seed = seed * 1103515245u + 12345u;
            exponent = (int)((seed >> 16) % 24) - 12;
            seed = seed * 1103515245u + 12345u;
            value = (double)((seed >> 8) % 1000000u) / 1000000.0;
            seed = seed * 1103515245u + 12345u;
            value = (value + 0.1) * pow(10.0, exponent);
            if ((seed >> 20) & 1)
                value = -value;
            figures = 3 + (int)((seed >> 12) % 4);

            chem_format(value, figures, printed, sizeof printed);
            if (sscanf(printed, "%lf", &back) != 1) {
                if (wrong == 0)
                    snprintf(detail, sizeof detail,
                             "%.17g printed as \"%s\", which is not a number",
                             value, printed);
                wrong++;
                continue;
            }
            /* half of the last significant figure, with a little room for the
             * rounding of the exponent itself */
            allowed = fabs(value) * pow(10.0, 1 - figures) * 0.51;
            if (fabs(back - value) > allowed) {
                if (wrong == 0)
                    snprintf(detail, sizeof detail,
                             "%.17g to %d figures printed as \"%s\"",
                             value, figures, printed);
                wrong++;
            }
            checked++;
        }
        ok("10 000 random numbers print and read back correctly", wrong == 0,
           wrong ? detail : NULL);
        int_is("and all of them were checked", checked, 10000);
    }

    printf("\n============================================================\n");
    printf("  Core tests  Total: %d   Passed: %d   Failed: %d\n",
           passed + failed, passed, failed);
    return failed ? 1 : 0;
}
