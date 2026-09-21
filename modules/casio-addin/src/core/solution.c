/* solution.c - see solution.h. Plain C99. */

#include "solution.h"

#include <math.h>

/* ---- gases -------------------------------------------------------------- */

chem_error_t gas_ideal(gas_state_t *state, gas_unknown_t unknown)
{
    switch (unknown) {
    case GAS_PRESSURE:
        if (state->volume <= 0)
            return CHEM_ERR_RANGE;
        state->pressure = state->moles * CHEM_R * state->temperature / state->volume;
        break;
    case GAS_VOLUME:
        if (state->pressure <= 0)
            return CHEM_ERR_RANGE;
        state->volume = state->moles * CHEM_R * state->temperature / state->pressure;
        break;
    case GAS_MOLES:
        if (state->temperature <= 0)
            return CHEM_ERR_RANGE;
        state->moles = state->pressure * state->volume / (CHEM_R * state->temperature);
        break;
    case GAS_TEMPERATURE:
        if (state->moles <= 0)
            return CHEM_ERR_RANGE;
        state->temperature = state->pressure * state->volume / (CHEM_R * state->moles);
        break;
    default:
        return CHEM_ERR_RANGE;
    }
    return CHEM_OK;
}

chem_error_t gas_combined(const gas_state_t *before, gas_state_t *after,
                          gas_unknown_t unknown)
{
    double p1 = before->pressure, v1 = before->volume, t1 = before->temperature;
    double p2 = after->pressure, v2 = after->volume, t2 = after->temperature;

    if (t1 <= 0)
        return CHEM_ERR_RANGE;

    switch (unknown) {
    case GAS_PRESSURE:
        if (v2 <= 0 || t2 <= 0)
            return CHEM_ERR_RANGE;
        after->pressure = p1 * v1 * t2 / (t1 * v2);
        break;
    case GAS_VOLUME:
        if (p2 <= 0 || t2 <= 0)
            return CHEM_ERR_RANGE;
        after->volume = p1 * v1 * t2 / (t1 * p2);
        break;
    case GAS_TEMPERATURE:
        if (p1 <= 0 || v1 <= 0)
            return CHEM_ERR_RANGE;
        after->temperature = t1 * p2 * v2 / (p1 * v1);
        break;
    default:
        return CHEM_ERR_RANGE;
    }
    return CHEM_OK;
}

chem_error_t gas_effusion_ratio(double molar_mass_1, double molar_mass_2,
                                double *ratio)
{
    if (molar_mass_1 <= 0 || molar_mass_2 <= 0)
        return CHEM_ERR_RANGE;
    *ratio = sqrt(molar_mass_2 / molar_mass_1);
    return CHEM_OK;
}

/* ---- equilibrium -------------------------------------------------------- */

/* R in dm3 kPa K-1 mol-1 is the same 8.31 as in J K-1 mol-1. */
chem_error_t eq_kc_to_kp(double kc, double temperature, int delta_n, double *kp)
{
    if (temperature <= 0 || kc < 0)
        return CHEM_ERR_RANGE;
    *kp = kc * pow(CHEM_R * temperature, (double)delta_n);
    return CHEM_OK;
}

chem_error_t eq_kp_to_kc(double kp, double temperature, int delta_n, double *kc)
{
    if (temperature <= 0 || kp < 0)
        return CHEM_ERR_RANGE;
    *kc = kp / pow(CHEM_R * temperature, (double)delta_n);
    return CHEM_OK;
}

/* Q - K at an extent of x, for A + B <-> C + D. */
static double ice_gap(double x, double a, double b, double c, double d, double k)
{
    double left = (a - x) * (b - x);
    double right = (c + x) * (d + x);

    if (left <= 0)
        return 1e30;          /* past the limiting reactant */
    return right / left - k;
}

chem_error_t eq_ice_extent(double a, double b, double c, double d,
                           double k, double *extent)
{
    double low, high, middle, limit;
    int i;

    if (a < 0 || b < 0 || c < 0 || d < 0 || k <= 0)
        return CHEM_ERR_RANGE;

    limit = (a < b) ? a : b;
    if (limit <= 0) {
        *extent = 0.0;
        return CHEM_OK;
    }

    /* The reaction quotient rises without bound as x approaches the limiting
     * amount, so the answer is bracketed between 0 and that amount. */
    low = 0.0;
    high = limit;
    if (ice_gap(low, a, b, c, d, k) > 0) {
        *extent = 0.0;         /* already past equilibrium: nothing goes forward */
        return CHEM_OK;
    }
    for (i = 0; i < 200; i++) {
        middle = 0.5 * (low + high);
        if (ice_gap(middle, a, b, c, d, k) > 0)
            high = middle;
        else
            low = middle;
    }
    *extent = 0.5 * (low + high);
    return CHEM_OK;
}

/* ---- acids and bases ---------------------------------------------------- */

double aqua_ph_from_h(double h)
{
    return (h > 0) ? -log10(h) : 0.0;
}

double aqua_h_from_ph(double ph)
{
    return pow(10.0, -ph);
}

double aqua_poh_from_ph(double ph)
{
    return 14.0 - ph;
}

double aqua_oh_from_poh(double poh)
{
    return pow(10.0, -poh);
}

chem_error_t aqua_strong_acid_ph(double concentration, int basicity, double *ph)
{
    if (concentration <= 0 || basicity < 1)
        return CHEM_ERR_RANGE;
    *ph = -log10(concentration * basicity);
    return CHEM_OK;
}

chem_error_t aqua_strong_base_ph(double concentration, int acidity, double *ph)
{
    double oh;

    if (concentration <= 0 || acidity < 1)
        return CHEM_ERR_RANGE;
    oh = concentration * acidity;
    *ph = 14.0 + log10(oh);
    return CHEM_OK;
}

/* Ka = x^2 / (c - x) solved exactly, rather than the usual x = sqrt(Ka c). */
static double weak_x(double k, double c)
{
    return 0.5 * (-k + sqrt(k * k + 4.0 * k * c));
}

chem_error_t aqua_weak_acid_ph(double ka, double concentration, double *ph)
{
    if (ka <= 0 || concentration <= 0)
        return CHEM_ERR_RANGE;
    *ph = -log10(weak_x(ka, concentration));
    return CHEM_OK;
}

chem_error_t aqua_weak_base_ph(double kb, double concentration, double *ph)
{
    if (kb <= 0 || concentration <= 0)
        return CHEM_ERR_RANGE;
    *ph = 14.0 + log10(weak_x(kb, concentration));
    return CHEM_OK;
}

chem_error_t aqua_buffer_ph(double ka, double acid, double salt, double *ph)
{
    if (ka <= 0 || acid <= 0 || salt <= 0)
        return CHEM_ERR_RANGE;
    *ph = -log10(ka) + log10(salt / acid);
    return CHEM_OK;
}

double aqua_pka_from_ka(double ka)
{
    return (ka > 0) ? -log10(ka) : 0.0;
}

double aqua_ka_from_pka(double pka)
{
    return pow(10.0, -pka);
}

chem_error_t aqua_kb_from_ka(double ka, double *kb)
{
    if (ka <= 0)
        return CHEM_ERR_RANGE;
    *kb = CHEM_KW / ka;
    return CHEM_OK;
}
