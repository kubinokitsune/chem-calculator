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
    close_to("Ar(S) = 32.07 (the IB booklet value)", chem_element(16)->mass, 32.07, 0.001);
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

    printf("\n============================================================\n");
    printf("  Core tests  Total: %d   Passed: %d   Failed: %d\n",
           passed + failed, passed, failed);
    return failed ? 1 : 0;
}
