/* energy.c - see energy.h. Plain C99.
 *
 * The bond enthalpies and standard electrode potentials are the IB data
 * booklet values, the same numbers the desktop calculator and the Python port
 * use.
 */

#include "energy.h"
#include "solution.h"      /* CHEM_R */

#include <math.h>
#include <string.h>

const energy_bond_t energy_bonds[] = {
    {"C-H", 414}, {"C-C", 346}, {"C=C", 614}, {"C#C", 839}, {"C-O", 358},
    {"C=O", 804}, {"C-N", 305}, {"C=N", 615}, {"C#N", 890}, {"C-Cl", 324},
    {"C-Br", 285}, {"C-F", 492}, {"H-H", 436}, {"O-H", 463}, {"N-H", 391},
    {"S-H", 364}, {"H-F", 567}, {"H-Cl", 431}, {"H-Br", 366}, {"H-I", 298},
    {"O=O", 498}, {"O-O", 144}, {"N-N", 158}, {"N=N", 470}, {"N#N", 945},
    {"F-F", 159}, {"Cl-Cl", 242}, {"Br-Br", 193}, {"I-I", 151}, {"S-S", 266},
};
const int energy_bond_count = (int)(sizeof energy_bonds / sizeof energy_bonds[0]);

const energy_half_cell_t energy_half_cells[] = {
    {"F2/F-", 2.87f}, {"MnO4-/Mn2+", 1.51f}, {"Cl2/Cl-", 1.36f},
    {"Cr2O72-/Cr3+", 1.33f}, {"Br2/Br-", 1.07f}, {"Ag+/Ag", 0.80f},
    {"Fe3+/Fe2+", 0.77f}, {"I2/I-", 0.54f}, {"Cu2+/Cu", 0.34f},
    {"H+/H2", 0.00f}, {"Pb2+/Pb", -0.13f}, {"Sn2+/Sn", -0.14f},
    {"Ni2+/Ni", -0.26f}, {"Fe2+/Fe", -0.44f}, {"Zn2+/Zn", -0.76f},
    {"Al3+/Al", -1.66f}, {"Mg2+/Mg", -2.37f}, {"Na+/Na", -2.71f},
    {"Ca2+/Ca", -2.87f}, {"K+/K", -2.92f}, {"Li+/Li", -3.04f},
};
const int energy_half_cell_count =
    (int)(sizeof energy_half_cells / sizeof energy_half_cells[0]);

/* "H-O" and "O-H" are the same bond, so compare both ways round. */
static int same_bond(const char *a, const char *b)
{
    const char *dash;
    char flipped[16];
    size_t left, right, len;

    if (strcmp(a, b) == 0)
        return 1;

    dash = strpbrk(b, "-=#");
    if (dash == NULL)
        return 0;
    left = (size_t)(dash - b);
    right = strlen(dash + 1);
    len = left + right + 1;
    if (len >= sizeof flipped)
        return 0;
    memcpy(flipped, dash + 1, right);
    flipped[right] = *dash;
    memcpy(flipped + right + 1, b, left);
    flipped[len] = 0;
    return strcmp(a, flipped) == 0;
}

int energy_bond_enthalpy(const char *bond)
{
    int i;

    if (bond == NULL || bond[0] == 0)
        return 0;
    for (i = 0; i < energy_bond_count; i++) {
        if (same_bond(bond, energy_bonds[i].bond))
            return energy_bonds[i].enthalpy;
    }
    return 0;
}

chem_error_t energy_half_cell(const char *name, double *potential)
{
    int i;

    for (i = 0; i < energy_half_cell_count; i++) {
        if (strcmp(name, energy_half_cells[i].half_cell) == 0) {
            *potential = energy_half_cells[i].potential;
            return CHEM_OK;
        }
    }
    return CHEM_ERR_RANGE;
}

double energy_heat(double mass, double heat_capacity, double delta_t)
{
    return mass * heat_capacity * delta_t;
}

chem_error_t energy_molar_enthalpy(double heat_joules, double moles, double *delta_h)
{
    if (moles <= 0)
        return CHEM_ERR_RANGE;
    *delta_h = -heat_joules / 1000.0 / moles;
    return CHEM_OK;
}

double energy_from_bonds(double broken, double formed)
{
    return broken - formed;
}

double energy_gibbs(double delta_h, double temperature, double delta_s)
{
    return delta_h - temperature * delta_s / 1000.0;
}

chem_error_t energy_crossover_temperature(double delta_h, double delta_s, double *t)
{
    if (delta_s == 0.0)
        return CHEM_ERR_RANGE;
    *t = delta_h * 1000.0 / delta_s;
    return CHEM_OK;
}

chem_error_t energy_gibbs_from_k(double k, double temperature, double *delta_g)
{
    if (k <= 0 || temperature <= 0)
        return CHEM_ERR_RANGE;
    *delta_g = -CHEM_R * temperature * log(k) / 1000.0;
    return CHEM_OK;
}

chem_error_t energy_k_from_gibbs(double delta_g, double temperature, double *k)
{
    double power;

    if (temperature <= 0)
        return CHEM_ERR_RANGE;
    power = -delta_g * 1000.0 / (CHEM_R * temperature);
    if (power > 700.0 || power < -700.0)
        return CHEM_ERR_RANGE;         /* would overflow a double */
    *k = exp(power);
    return CHEM_OK;
}

double energy_gibbs_from_cell(int electrons, double emf)
{
    return -(double)electrons * CHEM_FARADAY * emf / 1000.0;
}

chem_error_t energy_electrolysis_mass(double current, double seconds,
                                      double molar_mass, int charge, double *mass)
{
    if (current < 0 || seconds < 0 || molar_mass <= 0 || charge < 1)
        return CHEM_ERR_RANGE;
    *mass = current * seconds / CHEM_FARADAY * molar_mass / charge;
    return CHEM_OK;
}

chem_error_t energy_rate_constant(double a, double activation_energy,
                                  double temperature, double *k)
{
    if (a <= 0 || temperature <= 0)
        return CHEM_ERR_RANGE;
    *k = a * exp(-activation_energy * 1000.0 / (CHEM_R * temperature));
    return CHEM_OK;
}

chem_error_t energy_activation_from_two(double k1, double t1, double k2, double t2,
                                        double *activation_energy)
{
    if (k1 <= 0 || k2 <= 0 || t1 <= 0 || t2 <= 0 || t1 == t2)
        return CHEM_ERR_RANGE;
    /* ln(k2/k1) = -Ea/R (1/T2 - 1/T1) */
    *activation_energy = -CHEM_R * log(k2 / k1) / (1.0 / t2 - 1.0 / t1) / 1000.0;
    return CHEM_OK;
}

chem_error_t energy_half_life(double k, double *half_life)
{
    if (k <= 0)
        return CHEM_ERR_RANGE;
    *half_life = log(2.0) / k;
    return CHEM_OK;
}

chem_error_t energy_k_from_half_life(double half_life, double *k)
{
    if (half_life <= 0)
        return CHEM_ERR_RANGE;
    *k = log(2.0) / half_life;
    return CHEM_OK;
}
