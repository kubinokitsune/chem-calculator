/* energy.h - energetics, electrochemistry and kinetics.
 *
 * IB data booklet values: R = 8.31 J K-1 mol-1, F = 96500 C mol-1,
 * c(water) = 4.18 J g-1 K-1, and the booklet's bond enthalpies.
 */
#ifndef ENERGY_H
#define ENERGY_H

#include "chem.h"

#define CHEM_FARADAY    96500.0
#define CHEM_C_WATER    4.18

typedef struct {
    const char *bond;     /* "C-H", "O=O", "N#N" (# is a triple bond) */
    int enthalpy;         /* kJ mol-1 */
} energy_bond_t;

extern const energy_bond_t energy_bonds[];
extern const int energy_bond_count;

typedef struct {
    const char *half_cell; /* "Zn2+/Zn" */
    float potential;       /* volts */
} energy_half_cell_t;

extern const energy_half_cell_t energy_half_cells[];
extern const int energy_half_cell_count;

/* Bond enthalpy by name, either way round ("H-O" finds "O-H"); 0 if unknown. */
int energy_bond_enthalpy(const char *bond);

/* Standard half-cell potential by name; returns CHEM_ERR_RANGE if unknown. */
chem_error_t energy_half_cell(const char *name, double *potential);

/* q = m c dT, in joules. */
double energy_heat(double mass, double heat_capacity, double delta_t);

/* Molar enthalpy change in kJ mol-1 from the heat released and the moles that
 * reacted. The sign is flipped: heat given out is an exothermic negative dH. */
chem_error_t energy_molar_enthalpy(double heat_joules, double moles, double *delta_h);

/* Bond enthalpies: dH = bonds broken - bonds formed, in kJ mol-1. */
double energy_from_bonds(double broken, double formed);

/* dG = dH - T dS, with dH in kJ mol-1 and dS in J K-1 mol-1. */
double energy_gibbs(double delta_h, double temperature, double delta_s);

/* The temperature at which dG = 0. */
chem_error_t energy_crossover_temperature(double delta_h, double delta_s, double *t);

/* dG = -RT ln K and back again, dG in kJ mol-1. */
chem_error_t energy_gibbs_from_k(double k, double temperature, double *delta_g);
chem_error_t energy_k_from_gibbs(double delta_g, double temperature, double *k);

/* dG = -nFE, in kJ mol-1. */
double energy_gibbs_from_cell(int electrons, double emf);

/* Faraday: the mass deposited by a current I for a time t, in grams. */
chem_error_t energy_electrolysis_mass(double current, double seconds,
                                      double molar_mass, int charge, double *mass);

/* Arrhenius: k = A exp(-Ea/RT). Ea in kJ mol-1. */
chem_error_t energy_rate_constant(double a, double activation_energy,
                                  double temperature, double *k);

/* Ea from two (k, T) pairs, in kJ mol-1. */
chem_error_t energy_activation_from_two(double k1, double t1, double k2, double t2,
                                        double *activation_energy);

/* Half-life of a first-order reaction, and the rate constant from it. */
chem_error_t energy_half_life(double k, double *half_life);
chem_error_t energy_k_from_half_life(double half_life, double *k);

#endif /* ENERGY_H */
