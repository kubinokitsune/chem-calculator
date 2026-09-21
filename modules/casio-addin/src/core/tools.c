/* tools.c - see tools.h. Plain C99. */

#include "tools.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

/* ---- solutions ---------------------------------------------------------- */

double tools_concentration(double moles, double volume)
{
    return (volume > 0.0) ? moles / volume : 0.0;
}

double tools_moles_from_concentration(double concentration, double volume)
{
    return concentration * volume;
}

chem_error_t tools_dilution(double c1, double v1, double c2, double *v2)
{
    if (c2 <= 0.0)
        return CHEM_ERR_RANGE;
    *v2 = c1 * v1 / c2;
    return CHEM_OK;
}

double tools_mass_concentration(double concentration, double molar_mass)
{
    return concentration * molar_mass;
}

double tools_ppm(double solute_mass, double solution_mass)
{
    return (solution_mass > 0.0) ? solute_mass / solution_mass * 1.0e6 : 0.0;
}

/* ---- limiting reactant -------------------------------------------------- */

chem_error_t tools_limiting_reactant(const double *moles, const int *coefficients,
                                     int count, tools_limiting_t *result)
{
    double smallest = 0.0;
    int i, limiting = -1;

    if (count < 1 || count > CHEM_MAX_ATOMS)
        return CHEM_ERR_RANGE;

    for (i = 0; i < count; i++) {
        double ratio;

        if (coefficients[i] < 1 || moles[i] < 0.0)
            return CHEM_ERR_RANGE;
        ratio = moles[i] / coefficients[i];
        if (limiting < 0 || ratio < smallest) {
            smallest = ratio;
            limiting = i;
        }
    }
    result->limiting = limiting;
    result->reacting = smallest;
    for (i = 0; i < count; i++)
        result->left_over[i] = moles[i] - smallest * coefficients[i];
    return CHEM_OK;
}

/* ---- electron configuration --------------------------------------------- */

/* The order the subshells fill, as the diagonal rule gives it. */
static const struct { int n; char letter; int room; } filling_order[] = {
    {1, 's', 2},  {2, 's', 2},  {2, 'p', 6},  {3, 's', 2},  {3, 'p', 6},
    {4, 's', 2},  {3, 'd', 10}, {4, 'p', 6},  {5, 's', 2},  {4, 'd', 10},
    {5, 'p', 6},  {6, 's', 2},  {4, 'f', 14}, {5, 'd', 10}, {6, 'p', 6},
    {7, 's', 2},  {5, 'f', 14}, {6, 'd', 10}, {7, 'p', 6},
};
static const int filling_count =
    (int)(sizeof filling_order / sizeof filling_order[0]);

/* Chromium and copper and the ones below them take one electron from s to
 * leave a half-filled or full d subshell. */
static int is_exception(int z)
{
    return z == 24 || z == 29 || z == 42 || z == 47 || z == 79;
}

/* Where a subshell sits when the configuration is written in n order. */
static int compare_shells(const tools_subshell_t *a, const tools_subshell_t *b)
{
    static const char order[] = "spdf";
    if (a->n != b->n)
        return a->n - b->n;
    return (int)(strchr(order, a->letter) - order)
         - (int)(strchr(order, b->letter) - order);
}

int tools_configuration(int z, int charge, tools_subshell_t *out, int max)
{
    tools_subshell_t shells[TOOLS_MAX_SUBSHELLS];
    int electrons, count = 0, i, j;

    if (z < 1 || z > CHEM_ELEMENT_COUNT)
        return -1;
    if (z - charge < 0 || z - charge > CHEM_ELEMENT_COUNT + 10)
        return -1;
    /* A positive ion is worked out by filling the neutral atom and then taking
     * electrons off the outside, which is what actually happens: iron loses
     * its 4s electrons before any 3d one. A negative ion just keeps filling. */
    electrons = (charge > 0) ? z : z - charge;

    for (i = 0; i < filling_count && electrons > 0 && count < TOOLS_MAX_SUBSHELLS; i++) {
        int room = filling_order[i].room;
        int put = (electrons < room) ? electrons : room;

        shells[count].n = filling_order[i].n;
        shells[count].letter = filling_order[i].letter;
        shells[count].electrons = put;
        electrons -= put;
        count++;
    }

    /* The exceptions: move one electron from the outer s to the d below it. */
    if (charge == 0 && is_exception(z)) {
        for (i = 0; i < count; i++) {
            if (shells[i].letter == 'd' && i > 0 && shells[i - 1].letter == 's'
                && shells[i - 1].electrons == 2
                && (shells[i].electrons == 4 || shells[i].electrons == 9)) {
                shells[i - 1].electrons = 1;
                shells[i].electrons += 1;
            }
        }
    }

    /* Take the electrons off a cation from the outside in: the highest shell
     * first, and within one shell the outermost subshell (f, then d, p, s).
     * That is why iron empties 4s before it touches 3d, and then loses 3d
     * rather than 3p: Fe3+ is [Ar] 3d5. */
    if (charge > 0) {
        static const char subshell_order[] = "spdf";
        int to_remove = charge;

        while (to_remove > 0) {
            int best = -1;

            for (i = 0; i < count; i++) {
                if (shells[i].electrons <= 0)
                    continue;
                if (best < 0 || shells[i].n > shells[best].n
                    || (shells[i].n == shells[best].n
                        && strchr(subshell_order, shells[i].letter)
                           > strchr(subshell_order, shells[best].letter)))
                    best = i;
            }
            if (best < 0)
                break;
            shells[best].electrons--;
            to_remove--;
        }
    }

    /* Write it in n order, which is how it is read out. */
    for (i = 1; i < count; i++) {
        tools_subshell_t key = shells[i];
        j = i - 1;
        while (j >= 0 && compare_shells(&shells[j], &key) > 0) {
            shells[j + 1] = shells[j];
            j--;
        }
        shells[j + 1] = key;
    }

    /* Drop any empty subshell left behind. */
    j = 0;
    for (i = 0; i < count && j < max; i++) {
        if (shells[i].electrons > 0)
            out[j++] = shells[i];
    }
    return j;
}

void tools_configuration_text(const tools_subshell_t *shells, int count,
                              char *out, int length)
{
    int i, used = 0;

    if (length <= 0)
        return;
    out[0] = 0;
    for (i = 0; i < count; i++) {
        char part[16];
        int wrote = snprintf(part, sizeof part, "%s%d%c%d", (i == 0) ? "" : " ",
                             shells[i].n, shells[i].letter, shells[i].electrons);
        if (used + wrote >= length)
            return;
        memcpy(out + used, part, (size_t)wrote + 1);
        used += wrote;
    }
}

int tools_noble_core(int z)
{
    static const int nobles[] = {2, 10, 18, 36, 54, 86};
    int i, core = 0;

    for (i = 0; i < 6; i++) {
        if (nobles[i] < z)
            core = nobles[i];
    }
    return core;
}

/* ---- oxidation numbers -------------------------------------------------- */

/* The oxidation number an element takes when it is not the unknown one.
 * Returns 1 when a rule applies and writes it to *value. */
static int fixed_oxidation(const char *symbol, int z, int peroxide,
                           int has_oxygen, int has_fluorine, double *value)
{
    int group = chem_group(z);

    if (strcmp(symbol, "F") == 0) {
        *value = -1;
        return 1;
    }
    if (strcmp(symbol, "O") == 0) {
        if (has_fluorine)
            return 0;              /* OF2 and friends: let the algebra decide */
        *value = peroxide ? -1 : -2;
        return 1;
    }
    if (strcmp(symbol, "H") == 0) {
        *value = 1;
        return 1;
    }
    if (group == 1)
        { *value = 1; return 1; }
    if (group == 2)
        { *value = 2; return 1; }
    if (strcmp(symbol, "Al") == 0)
        { *value = 3; return 1; }
    if (strcmp(symbol, "Zn") == 0)
        { *value = 2; return 1; }
    if (strcmp(symbol, "Ag") == 0)
        { *value = 1; return 1; }
    if (group == 17 && !has_oxygen && !has_fluorine)
        { *value = -1; return 1; }
    return 0;
}

chem_error_t tools_oxidation_numbers(const chem_formula_t *formula, int charge,
                                     int peroxide, double *numbers)
{
    int has_oxygen = 0, has_fluorine = 0;
    int unknown = -1, unknown_count = 0;
    double total = 0.0;
    int i;

    if (formula->n < 1)
        return CHEM_ERR_EMPTY;

    /* An element on its own is always zero. */
    if (formula->n == 1 && charge == 0) {
        numbers[0] = 0.0;
        return CHEM_OK;
    }

    for (i = 0; i < formula->n; i++) {
        if (strcmp(formula->atoms[i].symbol, "O") == 0)
            has_oxygen = 1;
        if (strcmp(formula->atoms[i].symbol, "F") == 0)
            has_fluorine = 1;
    }

    for (i = 0; i < formula->n; i++) {
        int z = chem_symbol_z(formula->atoms[i].symbol);
        double value = 0.0;

        if (z == 0)
            return CHEM_ERR_UNKNOWN_ELEMENT;
        if (fixed_oxidation(formula->atoms[i].symbol, z, peroxide,
                            has_oxygen, has_fluorine, &value)) {
            numbers[i] = value;
            total += value * formula->atoms[i].count;
        } else {
            unknown = i;
            unknown_count++;
        }
    }

    if (unknown_count == 0) {
        /* Everything was fixed: the numbers must already add up. */
        return (fabs(total - charge) < 1e-9) ? CHEM_OK : CHEM_ERR_RANGE;
    }
    if (unknown_count > 1)
        return CHEM_ERR_RANGE;

    numbers[unknown] = (charge - total) / formula->atoms[unknown].count;
    return CHEM_OK;
}

/* ---- ionic formulas ----------------------------------------------------- */

static int gcd_int(int a, int b)
{
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b != 0) {
        int t = a % b;
        a = b;
        b = t;
    }
    return a ? a : 1;
}

/* Wrap a group in brackets when it needs more than one of it: (OH)2. */
static void append_part(char *out, int length, const char *symbol, int count)
{
    char part[32];
    int capitals = 0, i;
    int compound;

    for (i = 0; symbol[i]; i++) {
        if (symbol[i] >= 'A' && symbol[i] <= 'Z')
            capitals++;
    }
    /* Ca(OH)2, not CaOH2: anything with a second capital letter or a number
     * in it is a group of atoms and has to be bracketed. */
    compound = (capitals > 1) || (strpbrk(symbol, "0123456789") != NULL);

    if (count == 1)
        snprintf(part, sizeof part, "%s", symbol);
    else if (compound)
        snprintf(part, sizeof part, "(%s)%d", symbol, count);
    else
        snprintf(part, sizeof part, "%s%d", symbol, count);
    strncat(out, part, (size_t)(length - (int)strlen(out) - 1));
}

chem_error_t tools_ionic_formula(const char *cation, int cation_charge,
                                 const char *anion, int anion_charge,
                                 char *out, int length)
{
    int a, b, divisor;

    if (cation_charge <= 0 || anion_charge >= 0)
        return CHEM_ERR_RANGE;

    a = -anion_charge;          /* how many cations */
    b = cation_charge;          /* how many anions */
    divisor = gcd_int(a, b);
    a /= divisor;
    b /= divisor;

    if (length <= 0)
        return CHEM_ERR_RANGE;
    out[0] = 0;
    append_part(out, length, cation, a);
    append_part(out, length, anion, b);
    return CHEM_OK;
}

/* ---- isotopes ----------------------------------------------------------- */

chem_error_t tools_relative_atomic_mass(const double *masses,
                                        const double *abundances,
                                        int count, double *ar)
{
    double total = 0.0, weighted = 0.0;
    int i;

    if (count < 1)
        return CHEM_ERR_RANGE;
    for (i = 0; i < count; i++) {
        if (masses[i] <= 0.0 || abundances[i] < 0.0)
            return CHEM_ERR_RANGE;
        weighted += masses[i] * abundances[i];
        total += abundances[i];
    }
    if (total <= 0.0)
        return CHEM_ERR_RANGE;
    *ar = weighted / total;
    return CHEM_OK;
}

chem_error_t tools_abundances_from_ar(double mass_1, double mass_2, double ar,
                                      double *percent_1, double *percent_2)
{
    double fraction;

    if (mass_1 == mass_2)
        return CHEM_ERR_RANGE;
    fraction = (ar - mass_2) / (mass_1 - mass_2);
    if (fraction < 0.0 || fraction > 1.0)
        return CHEM_ERR_RANGE;      /* Ar is not between the two masses */
    *percent_1 = fraction * 100.0;
    *percent_2 = 100.0 - *percent_1;
    return CHEM_OK;
}

/* ---- uncertainties ------------------------------------------------------ */

double tools_percent_uncertainty(double value, double absolute)
{
    return (value != 0.0) ? fabs(absolute / value) * 100.0 : 0.0;
}

double tools_absolute_uncertainty(double value, double percent)
{
    return fabs(value) * percent / 100.0;
}

double tools_combine_sum(const double *absolutes, int count)
{
    double total = 0.0;
    int i;

    for (i = 0; i < count; i++)
        total += fabs(absolutes[i]);
    return total;
}

double tools_combine_product(const double *percents, int count)
{
    double total = 0.0;
    int i;

    for (i = 0; i < count; i++)
        total += fabs(percents[i]);
    return total;
}

double tools_combine_power(double percent, double power)
{
    return fabs(percent * power);
}

double tools_percent_error(double measured, double accepted)
{
    if (accepted == 0.0)
        return 0.0;
    return fabs((measured - accepted) / accepted) * 100.0;
}

/* ---- index of hydrogen deficiency --------------------------------------- */

double tools_ihd(const chem_formula_t *formula, int charge)
{
    double carbon = 0, hydrogen = 0, nitrogen = 0, halogen = 0;
    int i;

    for (i = 0; i < formula->n; i++) {
        const char *symbol = formula->atoms[i].symbol;
        int count = formula->atoms[i].count;
        int z = chem_symbol_z(symbol);

        if (strcmp(symbol, "C") == 0)
            carbon += count;
        else if (strcmp(symbol, "H") == 0)
            hydrogen += count;
        else if (strcmp(symbol, "N") == 0 || strcmp(symbol, "P") == 0)
            nitrogen += count;
        else if (z > 0 && chem_group(z) == 17)
            halogen += count;
        /* oxygen and sulfur make no difference */
    }
    (void)charge;
    return (2.0 * carbon + 2.0 + nitrogen - hydrogen - halogen) / 2.0;
}
