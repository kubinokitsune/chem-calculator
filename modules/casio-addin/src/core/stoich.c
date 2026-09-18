/* stoich.c - see stoich.h. Plain C99. */

#include "stoich.h"

#include <math.h>

void stoich_percent_composition(const chem_formula_t *formula, float *percent)
{
    float total = chem_formula_mass(formula);
    int i;

    for (i = 0; i < formula->n; i++) {
        float part = chem_element_mass(formula->atoms[i].symbol)
                     * (float)formula->atoms[i].count;
        percent[i] = (total > 0.0f) ? 100.0f * part / total : 0.0f;
    }
}

chem_error_t stoich_empirical(const char *const *symbols, const float *amounts,
                              int n, int *counts)
{
    double moles[CHEM_MAX_ATOMS];
    double smallest = 0.0;
    double best_error;
    int multiplier, best_multiplier;
    int i;

    if (n < 1 || n > CHEM_MAX_ATOMS)
        return CHEM_ERR_RANGE;

    for (i = 0; i < n; i++) {
        float mass = chem_element_mass(symbols[i]);
        if (mass <= 0.0f)
            return CHEM_ERR_UNKNOWN_ELEMENT;
        if (amounts[i] < 0.0f)
            return CHEM_ERR_RANGE;
        moles[i] = (double)amounts[i] / (double)mass;
        if (moles[i] > 0.0 && (smallest == 0.0 || moles[i] < smallest))
            smallest = moles[i];
    }
    if (smallest == 0.0)
        return CHEM_ERR_RANGE;

    /* Divide by the smallest, then scale up until every ratio is close to a
     * whole number - that is what turns 1 : 1.5 into 2 : 3. */
    best_multiplier = 1;
    best_error = 1e9;
    for (multiplier = 1; multiplier <= 12; multiplier++) {
        double worst = 0.0;
        for (i = 0; i < n; i++) {
            double ratio = moles[i] / smallest * multiplier;
            double gap = fabs(ratio - floor(ratio + 0.5));
            if (gap > worst)
                worst = gap;
        }
        if (worst < best_error - 1e-9) {
            best_error = worst;
            best_multiplier = multiplier;
        }
        if (worst < 0.06)      /* close enough for experimental data */
            break;
    }
    for (i = 0; i < n; i++) {
        double ratio = moles[i] / smallest * best_multiplier;
        counts[i] = (int)floor(ratio + 0.5);
        if (counts[i] < 0)
            counts[i] = 0;
    }
    return CHEM_OK;
}

int stoich_formula_multiplier(float empirical_mass, float molar_mass)
{
    int n;

    if (empirical_mass <= 0.0f || molar_mass <= 0.0f)
        return 1;
    n = (int)floor((double)molar_mass / (double)empirical_mass + 0.5);
    return n < 1 ? 1 : n;
}

float stoich_percent_yield(float actual, float theoretical)
{
    if (theoretical == 0.0f)
        return 0.0f;
    return 100.0f * actual / theoretical;
}

float stoich_atom_economy(float wanted_mass, float total_mass)
{
    if (total_mass == 0.0f)
        return 0.0f;
    return 100.0f * wanted_mass / total_mass;
}
