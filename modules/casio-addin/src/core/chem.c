/* chem.c - elements, formula parsing and number formatting.
 * Plain C99: no calculator headers, so the PC tests build it unchanged.
 */

#include "chem.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

/* ---- small helpers ------------------------------------------------------ */

static char lower(char c)
{
    return (c >= 'A' && c <= 'Z') ? (char)(c - 'A' + 'a') : c;
}

static int same_text(const char *a, const char *b)
{
    while (*a && *b) {
        if (lower(*a) != lower(*b))
            return 0;
        a++;
        b++;
    }
    return *a == 0 && *b == 0;
}

static int is_digit(char c)
{
    return c >= '0' && c <= '9';
}

static int is_upper(char c)
{
    return c >= 'A' && c <= 'Z';
}

static int is_lower(char c)
{
    return c >= 'a' && c <= 'z';
}

const char *chem_error_text(chem_error_t error)
{
    switch (error) {
    case CHEM_OK:                   return "";
    case CHEM_ERR_UNKNOWN_ELEMENT:  return "Unknown element";
    case CHEM_ERR_SYNTAX:           return "Check the formula";
    case CHEM_ERR_TOO_MANY:         return "Formula too long";
    case CHEM_ERR_RANGE:            return "Out of range";
    case CHEM_ERR_EMPTY:            return "Nothing typed";
    }
    return "Error";
}

/* ---- elements ----------------------------------------------------------- */

const chem_element_t *chem_element(int z)
{
    if (z < 1 || z > CHEM_ELEMENT_COUNT)
        return NULL;
    return &chem_elements[z - 1];
}

int chem_symbol_z(const char *symbol)
{
    int z;

    if (symbol == NULL || symbol[0] == 0)
        return 0;
    for (z = 1; z <= CHEM_ELEMENT_COUNT; z++) {
        if (strcmp(chem_elements[z - 1].symbol, symbol) == 0)
            return z;
    }
    return 0;
}

int chem_find_element(const char *text)
{
    int z, value;
    const char *p;

    if (text == NULL)
        return 0;
    while (*text == ' ')
        text++;
    if (*text == 0)
        return 0;

    if (is_digit(*text)) {
        value = 0;
        for (p = text; *p; p++) {
            if (!is_digit(*p))
                return 0;
            value = value * 10 + (*p - '0');
            if (value > CHEM_ELEMENT_COUNT)
                return 0;
        }
        return value;
    }
    for (z = 1; z <= CHEM_ELEMENT_COUNT; z++) {
        if (same_text(chem_elements[z - 1].symbol, text)
            || same_text(chem_elements[z - 1].name, text))
            return z;
    }
    return 0;
}

float chem_element_mass(const char *symbol)
{
    int z = chem_symbol_z(symbol);
    return z ? chem_elements[z - 1].mass : 0.0f;
}

int chem_is_f_block(int z)
{
    return (z >= 57 && z <= 71) || (z >= 89 && z <= 103);
}

/* First element of each period. */
static const int period_start[7] = {1, 3, 11, 19, 37, 55, 87};

int chem_period(int z)
{
    int i, period = 1;

    if (z < 1 || z > CHEM_ELEMENT_COUNT)
        return 0;
    for (i = 0; i < 7; i++) {
        if (z >= period_start[i])
            period = i + 1;
    }
    return period;
}

int chem_group(int z)
{
    int period, offset;

    period = chem_period(z);
    if (period == 0)
        return 0;
    offset = z - period_start[period - 1];

    if (period == 1)
        return (z == 1) ? 1 : 18;
    if (period == 2 || period == 3)
        return (offset < 2) ? offset + 1 : offset + 11;
    if (period == 4 || period == 5)
        return offset + 1;
    /* periods 6 and 7: two s-block elements, then the f block, then d and p */
    if (offset < 2)
        return offset + 1;
    if (offset <= 16)
        return 3;
    return offset - 13;
}

char chem_block(int z)
{
    int group;

    if (chem_is_f_block(z))
        return 'f';
    group = chem_group(z);
    if (z == 2 || group <= 2)
        return 's';
    if (group <= 12)
        return 'd';
    return 'p';
}

static int in_list(const char *symbol, const char *const *list, int n)
{
    int i;
    for (i = 0; i < n; i++) {
        if (strcmp(symbol, list[i]) == 0)
            return 1;
    }
    return 0;
}

static const char *const metalloids[] = {"B", "Si", "Ge", "As", "Sb", "Te", "Po"};
static const char *const non_metals[] = {"H", "C", "N", "O", "P", "S", "Se"};
static const char *const gases[] = {"H", "He", "N", "O", "F", "Ne", "Cl",
                                    "Ar", "Kr", "Xe", "Rn"};
static const char *const liquids[] = {"Br", "Hg"};

const char *chem_category(int z)
{
    const chem_element_t *e = chem_element(z);
    int group;

    if (e == NULL)
        return "";
    if (z >= 57 && z <= 71)
        return "Lanthanoid";
    if (z >= 89 && z <= 103)
        return "Actinoid";
    group = chem_group(z);
    if (group == 18)
        return "Noble gas";
    if (group == 17)
        return "Halogen";
    if (group == 1)
        return (z == 1) ? "Non-metal" : "Alkali metal";
    if (group == 2)
        return "Alkaline earth";
    if (group <= 12)
        return "Transition metal";
    if (in_list(e->symbol, metalloids, (int)(sizeof metalloids / sizeof *metalloids)))
        return "Metalloid";
    if (in_list(e->symbol, non_metals, (int)(sizeof non_metals / sizeof *non_metals)))
        return "Non-metal";
    return "Metal";
}

const char *chem_state(int z)
{
    const chem_element_t *e = chem_element(z);

    if (e == NULL)
        return "";
    if (in_list(e->symbol, gases, (int)(sizeof gases / sizeof *gases)))
        return "gas";
    if (in_list(e->symbol, liquids, (int)(sizeof liquids / sizeof *liquids)))
        return "liquid";
    return "solid";
}

const char *chem_usual_ion(int z)
{
    int group;

    if (chem_element(z) == NULL)
        return "";
    if (chem_is_f_block(z))
        return "+3";
    group = chem_group(z);
    switch (group) {
    case 1:  return "+1";
    case 2:  return "+2";
    case 13: return "+3";
    case 15: return "-3";
    case 16: return "-2";
    case 17: return "-1";
    case 18: return "none";
    default: return "varies";
    }
}

const char *chem_bond_type(float en_gap)
{
    if (en_gap < 0)
        en_gap = -en_gap;
    if (en_gap >= 1.8f)
        return "ionic";
    if (en_gap >= 0.4f)
        return "polar covalent";
    return "non-polar covalent";
}

/* ---- formula parsing ---------------------------------------------------- */

static chem_error_t add_atom(chem_formula_t *formula, const char *symbol, int count)
{
    int i;

    for (i = 0; i < formula->n; i++) {
        if (strcmp(formula->atoms[i].symbol, symbol) == 0) {
            formula->atoms[i].count += count;
            return CHEM_OK;
        }
    }
    if (formula->n >= CHEM_MAX_ATOMS)
        return CHEM_ERR_TOO_MANY;
    strcpy(formula->atoms[formula->n].symbol, symbol);
    formula->atoms[formula->n].count = count;
    formula->n++;
    return CHEM_OK;
}

static int read_number(const char *text, int *i)
{
    int value = 0;

    if (!is_digit(text[*i]))
        return 1;
    while (is_digit(text[*i])) {
        value = value * 10 + (text[*i] - '0');
        (*i)++;
    }
    return value;
}

/* One group of a formula, i.e. everything up to a ')' or the end. */
static chem_error_t parse_group(const char *text, int *i, int depth,
                                chem_formula_t *out, int multiplier,
                                char *bad, int bad_len)
{
    char symbol[CHEM_SYMBOL_LEN];
    chem_formula_t inner;
    chem_error_t error;
    int count, j, k;

    while (text[*i] != 0) {
        char c = text[*i];

        if (c == ' ') {
            (*i)++;
            continue;
        }
        if (c == '(') {
            (*i)++;
            inner.n = 0;
            error = parse_group(text, i, depth + 1, &inner, 1, bad, bad_len);
            if (error != CHEM_OK)
                return error;
            if (text[*i] != ')')
                return CHEM_ERR_SYNTAX;
            (*i)++;
            count = read_number(text, i);
            for (j = 0; j < inner.n; j++) {
                error = add_atom(out, inner.atoms[j].symbol,
                                 inner.atoms[j].count * count * multiplier);
                if (error != CHEM_OK)
                    return error;
            }
            continue;
        }
        if (c == ')') {
            if (depth == 0)
                return CHEM_ERR_SYNTAX;
            return CHEM_OK;
        }
        if (c == '.') {
            /* a hydrate: "CuSO4.5H2O" - the rest is multiplied by the number */
            if (depth != 0)
                return CHEM_ERR_SYNTAX;
            (*i)++;
            count = read_number(text, i);
            inner.n = 0;
            error = parse_group(text, i, depth, &inner, 1, bad, bad_len);
            if (error != CHEM_OK)
                return error;
            for (j = 0; j < inner.n; j++) {
                error = add_atom(out, inner.atoms[j].symbol,
                                 inner.atoms[j].count * count * multiplier);
                if (error != CHEM_OK)
                    return error;
            }
            continue;
        }
        if (!is_upper(c))
            return CHEM_ERR_SYNTAX;

        k = 0;
        symbol[k++] = c;
        (*i)++;
        if (is_lower(text[*i]))
            symbol[k++] = text[(*i)++];
        symbol[k] = 0;
        if (chem_symbol_z(symbol) == 0) {
            if (bad != NULL && bad_len > 0) {
                for (j = 0; j < k && j < bad_len - 1; j++)
                    bad[j] = symbol[j];
                bad[j] = 0;
            }
            return CHEM_ERR_UNKNOWN_ELEMENT;
        }
        count = read_number(text, i);
        error = add_atom(out, symbol, count * multiplier);
        if (error != CHEM_OK)
            return error;
    }
    if (depth > 0)
        return CHEM_ERR_SYNTAX;
    return CHEM_OK;
}

chem_error_t chem_parse_formula(const char *text, chem_formula_t *out,
                                char *bad, int bad_len)
{
    chem_error_t error;
    int i = 0;

    if (bad != NULL && bad_len > 0)
        bad[0] = 0;
    out->n = 0;
    if (text == NULL)
        return CHEM_ERR_EMPTY;
    while (text[i] == ' ')
        i++;
    if (text[i] == 0)
        return CHEM_ERR_EMPTY;

    error = parse_group(text, &i, 0, out, 1, bad, bad_len);
    if (error != CHEM_OK)
        return error;
    if (text[i] != 0)
        return CHEM_ERR_SYNTAX;
    if (out->n == 0)
        return CHEM_ERR_EMPTY;
    return CHEM_OK;
}

float chem_formula_mass(const chem_formula_t *formula)
{
    float total = 0.0f;
    int i;

    for (i = 0; i < formula->n; i++)
        total += chem_element_mass(formula->atoms[i].symbol) * (float)formula->atoms[i].count;
    return total;
}

chem_error_t chem_molar_mass(const char *text, float *out)
{
    chem_formula_t formula;
    chem_error_t error;

    error = chem_parse_formula(text, &formula, NULL, 0);
    if (error != CHEM_OK)
        return error;
    *out = chem_formula_mass(&formula);
    return CHEM_OK;
}

int chem_atom_count(const chem_formula_t *formula, const char *symbol)
{
    int i;

    for (i = 0; i < formula->n; i++) {
        if (strcmp(formula->atoms[i].symbol, symbol) == 0)
            return formula->atoms[i].count;
    }
    return 0;
}

/* ---- numbers ------------------------------------------------------------ */

/* Write `count` significant digits of `magnitude` (which must be positive)
 * into `digits`, and return the exponent of the first one. The digits are
 * produced with whole-number arithmetic: the calculator's C library is not the
 * one the tests run against, and a number printed there has to be the number
 * printed here. */
static int significant_digits(double magnitude, int count, char *digits)
{
    long long scaled, limit;
    int exponent, i;

    exponent = (int)floor(log10(magnitude));
    scaled = (long long)floor(magnitude / pow(10.0, exponent - count + 1) + 0.5);

    /* Rounding can carry into another decade: 9.99 to 3 figures is 10.0. */
    limit = 1;
    for (i = 0; i < count; i++)
        limit *= 10;
    if (scaled >= limit) {
        scaled /= 10;
        exponent++;
    }
    /* And the other way: log10 can be one out at a decade boundary. */
    if (scaled < limit / 10 && scaled > 0) {
        exponent--;
        scaled = (long long)floor(magnitude / pow(10.0, exponent - count + 1) + 0.5);
    }

    for (i = count - 1; i >= 0; i--) {
        digits[i] = (char)('0' + (int)(scaled % 10));
        scaled /= 10;
    }
    digits[count] = 0;
    return exponent;
}

void chem_format(double value, int figures, char *out, int len)
{
    char digits[24], text[40];
    double magnitude;
    int exponent, negative, used = 0, i;

    if (len <= 0)
        return;
    if (figures < 1)
        figures = 1;
    if (figures > 17)
        figures = 17;
    if (value != value || value > 1e308 || value < -1e308) {
        snprintf(out, (size_t)len, "n/a");
        return;
    }
    if (value == 0.0) {
        snprintf(out, (size_t)len, "0");
        return;
    }

    negative = (value < 0);
    magnitude = negative ? -value : value;
    exponent = significant_digits(magnitude, figures, digits);

    if (negative)
        text[used++] = '-';

    if (exponent >= 6 || exponent <= -4) {
        /* Scientific: one digit, the point, the rest, then the exponent. */
        text[used++] = digits[0];
        if (figures > 1) {
            int last = figures - 1;
            while (last > 0 && digits[last] == '0')
                last--;
            if (last > 0) {
                text[used++] = '.';
                for (i = 1; i <= last; i++)
                    text[used++] = digits[i];
            }
        }
        text[used] = 0;
        snprintf(out, (size_t)len, "%se%d", text, exponent);
        return;
    }

    if (exponent >= figures - 1) {
        /* A whole number, possibly with zeros put back on the end. */
        for (i = 0; i < figures; i++)
            text[used++] = digits[i];
        for (i = figures; i <= exponent; i++)
            text[used++] = '0';
        text[used] = 0;
    } else if (exponent >= 0) {
        int last = figures - 1;

        while (last > exponent && digits[last] == '0')
            last--;
        for (i = 0; i <= exponent; i++)
            text[used++] = digits[i];
        if (last > exponent) {
            text[used++] = '.';
            for (i = exponent + 1; i <= last; i++)
                text[used++] = digits[i];
        }
        text[used] = 0;
    } else {
        /* Smaller than one: "0.", then the leading zeros, then the digits. */
        int last = figures - 1;

        while (last > 0 && digits[last] == '0')
            last--;
        text[used++] = '0';
        text[used++] = '.';
        for (i = -1; i > exponent; i--)
            text[used++] = '0';
        for (i = 0; i <= last; i++)
            text[used++] = digits[i];
        text[used] = 0;
    }
    snprintf(out, (size_t)len, "%s", text);
}
