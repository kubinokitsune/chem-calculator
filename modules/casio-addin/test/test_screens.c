/* test_screens.c - drives the add-in's real screens with scripted keypresses.
 *
 *   make -C test screens
 *
 * The screens, the menus and the entry fields are the ones that will run on
 * the calculator; only the screen and keypad are faked. Each test types what
 * a student would type and then checks what came out.
 */

#include "fake_gint.h"
#include "../src/screens/screens.h"
#include "../src/ui/ui.h"
#include "../src/ui/battery.h"
#include "../src/core/energy.h"

#include <stdio.h>
#include <string.h>

static int passed, failed;

#define MAGENTA C_RGB(31, 0, 31)        /* the scroll arrows */

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

/* Check that the screen showed a piece of text. On failure, print the last
 * part of what was actually drawn, which is usually enough to see why. */
static void showed(const char *label, const char *wanted)
{
    const char *screen = fake_screen();
    int length = (int)strlen(screen);
    const char *tail = screen + (length > 300 ? length - 300 : 0);
    char detail[400];

    snprintf(detail, sizeof detail, "did not show \"%s\"; screen ended:\n%s",
             wanted, tail);
    ok(label, fake_screen_has(wanted), detail);
}

static void section(const char *title)
{
    printf("\n=== %s ===\n", title);
}

/* Choose an item from a menu by its number. The number keys move the cursor
 * straight to an entry, which is steady whatever the menu last remembered -
 * the menus keep their place between visits, as the calculator's own do. */
static void menu_pick(int item)
{
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    if (item >= 1 && item <= 9)
        fake_press(digits[item]);
    fake_press(KEY_EXE);
}

/* Choose a booklet bond in the bond list. Item 1 is Done, item 2 is Type a
 * bond and the table follows in order: the number key jumps to the top and the
 * arrows walk down from there. */
static void bond_pick(const char *bond)
{
    int i, item = 0;

    for (i = 0; i < energy_bond_count; i++)
        if (strcmp(energy_bonds[i].bond, bond) == 0)
            item = i + 3;
    if (item == 0)
        ok("the bond is in the booklet", 0, bond);
    fake_press(KEY_1);
    for (i = 1; i < item; i++)
        fake_press(KEY_DOWN);
    fake_press(KEY_EXE);
}

/* Choose a half-cell by name in the cell-potential lists, the same way. */
static void half_cell_pick(const char *half_cell)
{
    int i, item = 0;

    for (i = 0; i < energy_half_cell_count; i++)
        if (strcmp(energy_half_cells[i].half_cell, half_cell) == 0)
            item = i + 1;
    if (item == 0)
        ok("the half-cell is in the booklet", 0, half_cell);
    fake_press(KEY_1);
    for (i = 1; i < item; i++)
        fake_press(KEY_DOWN);
    fake_press(KEY_EXE);
}

/* The bond screen is open at Bond enthalpies: leave it, and check that the
 * script used exactly the keys the screens asked for. */
static void bond_finish(void)
{
    fake_press(KEY_EXE);                /* the bonds entered */
    fake_press(KEY_EXE);                /* the answer */
    fake_press(KEY_EXIT);               /* out of the energy menu */
    screen_energy();
    ok("the bond screens asked for every key and no more",
       fake_keys_left() == 0 && !fake_ran_out_of_keys(), "keys left over or missing");
}

/* Type an equation into its field and accept it. */
static void equation(const char *text)
{
    fake_press_text(text);
    fake_press(KEY_EXE);
}

/* The script used exactly the keys the screens asked for. */
static void all_keys_used(const char *what)
{
    char label[80];

    snprintf(label, sizeof label, "%s: every key used, none missing", what);
    ok(label, fake_keys_left() == 0 && !fake_ran_out_of_keys(), "keys left over or missing");
}

int main(void)
{
    section("1. The periodic table screens");

    /* Look up iron by symbol: menu item 1, type Fe, EXE, read, back out. */
    fake_reset();
    menu_pick(1);                       /* Element lookup */
    fake_press_text("Fe");
    fake_press(KEY_EXE);                /* accept the formula */
    fake_press(KEY_EXIT);               /* leave the result page */
    fake_press(KEY_EXIT);               /* leave the topic menu */
    screen_periodic_table();
    showed("looking up Fe names iron", "Iron");
    showed("and gives its mass", "55.85");
    showed("and its group", "Group 8");
    showed("and its category", "Transition metal");
    showed("group, period and block share a line", "Group 8   Period 4   d block");
    showed("and the last line, electronegativity, is in view", "Electronegativity = 1.83");
    ok("the screen did not run out of keys", fake_ran_out_of_keys() == 0, NULL);

    /* By atomic number this time. */
    fake_reset();
    menu_pick(1);
    fake_press(KEY_ALPHA);              /* text fields start on letters */
    fake_press_number("26");            /* digits, then EXE */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("looking up 26 also finds iron", "Iron");

    /* By name, in small letters. */
    fake_reset();
    menu_pick(1);
    fake_press_text("magnesium");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("looking up a name works", "Magnesium");
    showed("magnesium is in group 2", "Group 2");
    showed("and forms +2", "+2");

    /* A group listing. */
    fake_reset();
    menu_pick(2);                       /* List a group */
    fake_press_number("17");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("group 17 lists fluorine", "Fluorine");
    showed("group 17 lists astatine", "Astatine");

    /* Bond type. */
    fake_reset();
    menu_pick(4);                       /* Bond type */
    fake_press_text("Na");
    fake_press(KEY_EXE);
    fake_press_text("Cl");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("NaCl comes out ionic", "ionic");

    /* A made-up element must be reported, not accepted. */
    fake_reset();
    menu_pick(1);
    fake_press_text("Qz");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);               /* dismiss the message */
    fake_press(KEY_EXIT);               /* leave the field */
    fake_press(KEY_EXIT);               /* leave the menu */
    screen_periodic_table();
    showed("a made-up element is reported", "No such element");

    section("2. The stoichiometry screens");

    /* 10 g of CaCO3 is 0.0999 mol - the answer the other two versions give. */
    fake_reset();
    menu_pick(1);                       /* Moles */
    menu_pick(1);                       /* Mass to moles */
    fake_press_text("CaCO3");
    fake_press(KEY_EXE);
    fake_press_number("10");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("10 g of CaCO3 has the right molar mass", "100.1");
    showed("and is 0.0999 mol", "0.0999");

    /* Percentage composition of water. */
    fake_reset();
    menu_pick(2);                       /* Percent composition */
    fake_press_text("H2O");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("water is 11.2 % hydrogen", "11.2");
    showed("water is 88.8 % oxygen", "88.79");

    /* Empirical formula from percentages, then the molecular formula. */
    fake_reset();
    menu_pick(3);                       /* Empirical */
    fake_press_number("3");             /* three elements */
    fake_press_text("C");
    fake_press(KEY_EXE);
    fake_press_number("40");
    fake_press_text("H");
    fake_press(KEY_EXE);
    fake_press_number("6.7");
    fake_press_text("O");
    fake_press(KEY_EXE);
    fake_press_number("53.3");
    fake_press_number("180");           /* Mr, for the molecular formula */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("the empirical formula is CH2O", "CH2O");
    showed("and the molecular formula is C6H12O6", "C6H12O6");

    section("3. The balancer screen and the equation field");

    /* Type an equation (F-keys and mode switches come from fake_press_text),
     * accept it, look at the answer and leave. */
    fake_reset();
    equation("C3H8+O2->CO2+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("propane balances as 1, 5, 3, 4", "Coefficients: 1, 5, 3, 4");
    showed("and the equation is shown", "5 O2");
    showed("on one line, as it will be written", "C3H8 + 5 O2 -> 3 CO2 + 4 H2O");
    all_keys_used("propane");

    /* Brackets, typed with F1 and F2. */
    fake_reset();
    equation("Ca(OH)2+H3PO4->Ca3(PO4)2+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("calcium hydroxide + phosphoric acid is 3, 2, 1, 6",
           "Coefficients: 3, 2, 1, 6");
    all_keys_used("brackets");

    /* A long one: 28 characters, small letters, four products. */
    fake_reset();
    equation("KMnO4+HCl->KCl+MnCl2+H2O+Cl2");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("permanganate + HCl is 2, 16, 2, 2, 8, 5",
           "Coefficients: 2, 16, 2, 2, 8, 5");
    showed("the 16 shows on the HCl", "16 HCl");
    all_keys_used("permanganate");

    /* 46 characters: wider than the 34 the field shows, so it scrolls while typing. */
    fake_reset();
    equation("C6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    /* "Coefficients: " and these seven are 35 characters, one more than a line:
     * the list gets a line of its own rather than losing its last digit */
    showed("glucose + dichromate is 1, 4, 16, 6, 4, 4, 22",
           "Coefficients:\n1, 4, 16, 6, 4, 4, 22\n");
    ok("the long equation was never drawn in one piece",
       !fake_screen_has("C6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O"), "no scrolling");
    showed("but its end was in view", "2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O");
    all_keys_used("long equation");

    /* Numbers in front are ignored, and the prompt says so. */
    fake_reset();
    equation("2C3H8+O2->CO2+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("a typed coefficient is ignored by the balancer", "Coefficients: 1, 5, 3, 4");
    showed("and the prompt says so", "front numbers ignored");
    all_keys_used("ignored coefficient");

    /* Mistakes: the message is shown, the text stays, and it can be fixed. */
    fake_reset();
    equation("C3H8+O2");                /* no arrow */
    fake_press(KEY_EXE);                /* dismiss the message */
    fake_press_text("->CO2+H2O");       /* the field still holds C3H8+O2 */
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    screen_balance();
    showed("no arrow is explained", "Need -> or =");
    showed("and the text was kept: adding to it balances", "Coefficients: 1, 5, 3, 4");
    all_keys_used("no arrow");

    fake_reset();
    equation("C3H8+O2->CO2+H2Q");       /* Q is not an element */
    fake_press(KEY_EXE);
    fake_press(KEY_DEL);                /* rub out the Q ... */
    fake_press_text("O");               /* ... and the field still holds the rest */
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    screen_balance();
    showed("a bad formula is explained", "Unknown element");
    showed("and fixing it with DEL balances", "Coefficients: 1, 5, 3, 4");
    all_keys_used("bad formula");

    fake_reset();
    equation("H2->O2");
    fake_press(KEY_EXE);
    fake_press(KEY_DEL);  fake_press(KEY_DEL);
    fake_press(KEY_DEL);                            /* O2 and "->" are gone: back to H2 */
    equation("+O2->H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("an equation that cannot balance says so", "That will not balance");
    showed("and H2 + O2 -> H2O then balances", "Coefficients: 2, 1, 2");
    all_keys_used("will not balance");

    fake_reset();
    equation("->CO2");                  /* nothing on the left */
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);               /* give up from the field */
    screen_balance();
    showed("an empty side is explained", "Nothing typed");
    all_keys_used("empty side");

    /* The field itself: the keypad's own + ( ) . and arrow keys, in digit mode. */
    {
        char text[UI_EQUATION_LEN];

        fake_reset();
        text[0] = 0;
        fake_press_text("CH4");                                 /* ends in digit mode */
        fake_press(KEY_ADD);  fake_press(KEY_ALPHA);
        fake_press_text("O2");
        fake_press(KEY_ARROW);  fake_press(KEY_ALPHA);          /* the arrow key is ->  */
        fake_press_text("CO2");
        fake_press(KEY_ADD);  fake_press(KEY_ALPHA);
        fake_press_text("H2O");
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("the keypad's + and arrow keys type in digit mode",
           strcmp(text, "CH4+O2->CO2+H2O") == 0, text);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);
        fake_press(KEY_LEFTP);  fake_press(KEY_RIGHTP);  fake_press(KEY_DOT);
        fake_press(KEY_ALPHA);                                  /* back to letters */
        fake_press(KEY_ADD);  fake_press(KEY_ARROW);
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("( ) and . type in digit mode", strncmp(text, "().", 3) == 0, text);
        ok("in letters mode the same keys are still the letters on them",
           strcmp(text + 3, "XL") == 0, text);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);
        fake_press(KEY_ADD);  fake_press(KEY_LEFTP);  fake_press(KEY_ARROW);
        fake_press(KEY_EXE);
        ui_text_input("Formula", "Formula:", text, (int)sizeof text);
        ok("a formula field does not type + from KEY_ADD",
           strchr(text, '+') == NULL && strcmp(text, "XIL") == 0, text);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);
        fake_press(KEY_ARROW);  fake_press(KEY_EXE);
        ui_bond_input("Bond", "Bond:", text, (int)sizeof text);
        ok("nor does a bond field type an arrow", strchr(text, '>') == NULL, text);

        /* Past the width of the screen the field scrolls: the end is drawn, the
         * whole thing is not, and nothing is lost from the buffer. */
        fake_reset();
        text[0] = 0;
        fake_press_text("CH4+CH4+CH4+CH4+CH4+CH4+CH4+CH4+CH4+CH4+CH4+CH4");
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("a 47-character equation is all in the buffer",
           strlen(text) == 47 && strcmp(text + 40, "CH4+CH4") == 0, text);
        ok("the field scrolls rather than running off the screen",
           !fake_screen_has(text) && fake_screen_has(text + 13),
           "the whole text was drawn, or the end was not");

        /* The longest equation the field holds, UI_EQUATION_LEN - 1 characters, is
         * more than twice the screen's width: typing it must keep the end, and
         * the caret after it, inside the screen. A hundred are typed, so the
         * last few are refused. */
        {
            char many[101] = "";
            int before, i;

            for (i = 0; i < 25; i++)
                strcat(many, "CH4+");
            fake_reset();
            text[0] = 0;
            fake_press_text(many);
            fake_press(KEY_EXE);
            before = fake_overflows();
            ui_equation_input("Equation", "Equation:", text, UI_EQUATION_LEN);
            ok("a hundred typed characters fill the buffer to its limit",
               (int)strlen(text) == UI_EQUATION_LEN - 1, text);
            ok("its end is drawn", fake_screen_has(text + strlen(text) - 34), NULL);
            ok("and so is the caret, inside the screen: nothing ran past the edge",
               fake_overflows() == before, fake_first_overflow());
        }

        /* DEL takes "->" away in one go; any other character one at a time. */
        fake_reset();
        text[0] = 0;
        fake_press_text("CH4+O2->");
        fake_press(KEY_DEL);
        fake_press_text("C");
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("DEL after -> removes the whole arrow", strcmp(text, "CH4+O2C") == 0, text);
        fake_reset();
        text[0] = 0;
        fake_press_text("CH4+O2->");
        fake_press(KEY_DEL);
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("so no lone minus is left", strcmp(text, "CH4+O2") == 0, text);
        fake_reset();
        text[0] = 0;
        fake_press_text("CH4+O2->C");
        fake_press(KEY_DEL);
        fake_press(KEY_EXE);
        ui_equation_input("Equation", "Equation:", text, (int)sizeof text);
        ok("DEL after a letter only takes the letter", strcmp(text, "CH4+O2->") == 0, text);

        /* "->" goes in whole or not at all. */
        fake_reset();
        {
            char small[10] = "";
            fake_press_text("CH4+CH4+");      /* 8 of the 9 characters that fit */
            fake_press(KEY_F4);
            fake_press(KEY_EXE);
            ui_equation_input("Equation", "Equation:", small, (int)sizeof small);
            ok("an arrow that does not fit is not half typed",
               strcmp(small, "CH4+CH4+") == 0, small);
        }
        {
            char one[2] = "";               /* room for a single character */
            fake_reset();
            fake_press(KEY_F4);
            fake_press_text("C");
            fake_press(KEY_EXE);
            ui_equation_input("Equation", "Equation:", one, (int)sizeof one);
            ok("with one place left the arrow is not half typed", strcmp(one, "C") == 0, one);
        }
    }

    section("3b. The answer is in view the moment a result opens");

    /* No key is pressed on the result page except the one that leaves it, so
     * what shows is the first frame. A page that fits draws no scroll arrow. */
    fake_reset();
    menu_pick(5);                       /* Atom economy */
    equation("CH4+2O2->CO2+2H2O");
    menu_pick(2);                       /* H2O */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("atom economy: the equation takes one line", "CH4 + 2 O2 -> CO2 + 2 H2O");
    showed("atom economy: 45.02 % is on the first screen", "atom economy = 45.02 %");
    ok("atom economy: the page fits, so nothing is scrolled", fake_rects(MAGENTA) == 0, NULL);
    all_keys_used("atom economy first view");

    fake_reset();
    equation("C3H8+O2->CO2+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("balancer: propane's 1, 5, 3, 4 are on the first screen", "Coefficients: 1, 5, 3, 4");
    showed("balancer: with the equation above them", "C3H8 + 5 O2 -> 3 CO2 + 4 H2O");
    ok("balancer: the page fits, so nothing is scrolled", fake_rects(MAGENTA) == 0, NULL);
    all_keys_used("propane first view");

    fake_reset();
    equation("KMnO4+HCl->KCl+MnCl2+H2O+Cl2");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("balancer: permanganate's 2, 16, 2, 2, 8, 5 are on the first screen",
           "Coefficients: 2, 16, 2, 2, 8, 5");
    showed("balancer: the equation wraps at a + and shows its end", "5 Cl2");
    ok("balancer: and still nothing is scrolled", fake_rects(MAGENTA) == 0, NULL);
    all_keys_used("permanganate first view");

    /* A long equation still fits when it takes two lines... */
    fake_reset();
    menu_pick(5);
    equation("KMnO4+HCl->KCl+MnCl2+H2O+Cl2");
    menu_pick(4);                       /* Cl2 */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a two-line equation: the answer is on the first screen", "atom economy = 39.41 %");
    showed("and the equation's second line", "  + 2 MnCl2 + 8 H2O + 5 Cl2");
    /* heading, 2 + 1 + 2 + 1 + 1 lines: one more than the 6 a page holds, so it
     * opens scrolled to the answer, with the up arrow showing */
    ok("one line too many: the up arrow shows", fake_rects(MAGENTA) > 0, NULL);
    all_keys_used("two-line atom economy");

    /* ...but a three-line one makes the page too long: it opens scrolled so
     * that the last rule and the answer are in view, with the up arrow showing. */
    fake_reset();
    menu_pick(5);
    equation("C6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O");
    menu_pick(1);                       /* CO2 */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a three-line equation: the answer is still on the first screen", "atom economy = ");
    showed("and so is the last rule's wanted line", "CO2 M x coeff = ");
    ok("and the up arrow shows there is more above", fake_rects(MAGENTA) > 0, NULL);
    all_keys_used("three-line atom economy");

    section("4. The gas screens");

    /* 2.00 mol at 300 K in 5.00 dm3 gives 997 kPa. */
    fake_reset();
    menu_pick(1);                       /* pV = nRT */
    menu_pick(1);                       /* find pressure */
    fake_press_number("5");             /* V */
    fake_press_number("2");             /* n */
    fake_press_number("300");           /* T */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_gases();
    showed("pV = nRT gives 997 kPa", "997");

    section("5. The acid and base screens");

    /* 0.10 mol dm-3 hydrochloric acid has pH 1. */
    fake_reset();
    menu_pick(2);                       /* Strong acid or base */
    menu_pick(1);                       /* strong acid */
    fake_press_number("0.1");
    fake_press_number("1");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_acids();
    showed("0.10 mol dm-3 HCl has pH 1", "pH = 1");

    /* Ethanoic acid, Ka = 1.74e-5, 0.100 mol dm-3, pH 2.88. */
    fake_reset();
    menu_pick(3);                       /* Weak acid or base */
    menu_pick(1);                       /* weak acid */
    fake_press_number("1.74e-5");
    fake_press_number("0.1");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_acids();
    showed("ethanoic acid has pH 2.88", "2.88");
    showed("and its last answer, [OH-], is in view", "[OH-]");

    section("6. The energy screens");

    /* 100 g of water warmed 25 K takes 10450 J. */
    fake_reset();
    menu_pick(1);                       /* Calorimetry */
    fake_press_number("100");
    fake_press_number("4.18");
    fake_press_number("25");
    fake_press(KEY_EXE);                /* skip the moles */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("q = mcdT is 10450 J", "10450");

    /* dG from dH and dS. */
    fake_reset();
    menu_pick(3);                       /* Gibbs */
    menu_pick(1);                       /* dG from dH and dS */
    fake_press_number("-92.2");
    fake_press_number("-198.8");
    fake_press_number("298");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("dG comes out at -32.96 kJ/mol", "-32.96");
    showed("and it is called spontaneous", "spontaneous");

    /* Cu2+/Cu reduced and Zn2+/Zn oxidised: E(cell) 1.10 V, and every line of
     * the result, spontaneous last, is on the first screen. */
    fake_reset();
    menu_pick(4);                       /* Cell potential */
    half_cell_pick("Cu2+/Cu");
    half_cell_pick("Zn2+/Zn");
    fake_press_number("2");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("the cell names its reduced half-cell and E", "E(red) Cu2+/Cu = 0.34 V");
    showed("and its oxidised one", "E(ox) Zn2+/Zn = -0.76 V");
    showed("Cu2+/Cu against Zn2+/Zn is 1.1 V", "E(cell) = 1.1 V");
    showed("and spontaneous, in view without scrolling", "\nspontaneous\n");
    all_keys_used("cell potential");

    /* H2 + Cl2 -> 2HCl, picking every bond from the list. */
    fake_reset();
    menu_pick(2);                       /* Bond enthalpies */
    fake_press(KEY_EXE);                /* "First the bonds broken" */
    bond_pick("H-H");        fake_press_number("1");
    bond_pick("Cl-Cl");      fake_press_number("1");
    menu_pick(1);                       /* Done */
    fake_press(KEY_EXE);                /* "Now the bonds formed" */
    bond_pick("H-Cl");       fake_press_number("2");
    menu_pick(1);
    bond_finish();
    showed("the list shows what was broken", "1 x Cl-Cl (242) = 242");
    showed("and what was formed", "2 x H-Cl (431) = 862");
    showed("HCl comes out at -184", "dH = -184 kJ/mol");
    showed("and is exothermic", "exothermic");

    /* CH4 + 2O2 -> CO2 + 2H2O from the list: 2652 broken, 3460 formed. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("C-H");        fake_press_number("4");
    bond_pick("O=O");        fake_press_number("2");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("C=O");        fake_press_number("2");
    bond_pick("O-H");        fake_press_number("4");
    menu_pick(1);
    bond_finish();
    showed("methane burning breaks 2652", "broken = 2652 kJ/mol");
    showed("and forms 3460", "formed = 3460 kJ/mol");
    showed("so dH is -808", "dH = -808 kJ/mol");
    showed("which is exothermic", "exothermic");

    /* The same, typing every bond: "-" from the minus key, "=" from F2, and
     * small letters for the lower-case spelling. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(2);                       /* Type a bond */
    fake_press_text("C-H");  fake_press(KEY_EXE);  fake_press_number("4");
    menu_pick(2);
    fake_press_bond("O=O");  fake_press(KEY_EXE);  fake_press_number("2");
    menu_pick(1);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_bond("c=o");  fake_press(KEY_EXE);  fake_press_number("2");
    menu_pick(2);
    fake_press_text("O-H");  fake_press(KEY_EXE);  fake_press_number("4");
    menu_pick(1);
    bond_finish();
    showed("typed bonds are found, C-H x4", "4 x C-H (414) = 1656");
    showed("typed O=O reaches the table", "2 x O=O (498) = 996");
    showed("typed lower case c=o is shown as the booklet's C=O", "2 x C=O (804) = 1608");
    ok("and not as typed", !fake_screen_has("x c=o"), "showed the typed spelling");
    showed("typing gives the same -808", "dH = -808 kJ/mol");

    /* F1 types -, F3 types #, and (-) does the same as the minus key:
     * N2 + 3H2 -> 2NH3 is 945 + 3 x 436 broken, 6 N-H formed, -93. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_text("N");  fake_press(KEY_F3);  fake_press_text("N");
    fake_press(KEY_EXE);  fake_press_number("1");
    menu_pick(2);
    fake_press_text("H");  fake_press(KEY_F1);  fake_press_text("H");
    fake_press(KEY_EXE);  fake_press_number("3");
    menu_pick(1);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_text("N");  fake_press(KEY_ALPHA);  fake_press(KEY_NEG);
    fake_press(KEY_ALPHA);  fake_press_text("H");
    fake_press(KEY_EXE);  fake_press_number("6");
    menu_pick(1);
    bond_finish();
    showed("F3 typed the triple bond", "1 x N#N (945) = 945");
    showed("F1 typed a single bond", "3 x H-H (436) = 1308");
    showed("(-) typed a minus", "6 x N-H (391) = 2346");
    showed("ammonia comes out at -93", "dH = -93 kJ/mol");

    /* A bond the booklet lacks asks for its enthalpy and uses it:
     * 2 x C-S (272) = 544 broken, 1 x C-H formed, dH = +130. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_text("c-s");  fake_press(KEY_EXE);
    fake_press(KEY_EXE);                /* "not in the booklet" */
    fake_press_number("272");           /* its kJ/mol */
    fake_press_number("2");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("C-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("an unknown bond is said to be missing", "Bond not in the booklet");
    showed("and asks for its enthalpy", "kJ/mol of c-s:");
    showed("and the typed value is used, in the spelling typed", "2 x c-s (272) = 544");
    showed("so dH is 544 - 414 = 130", "dH = 130 kJ/mol");
    showed("which is endothermic", "endothermic");

    /* The longest bond name still shows the prompt to its colon. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_text("Cs-Cs-Cs-Cs-Cs");  fake_press(KEY_EXE);
    fake_press(KEY_EXE);
    fake_press_number("272");
    fake_press_number("2");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("C-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("a long bond name keeps the prompt's colon", "kJ/mol of Cs-Cs-Cs-Cs-Cs:");

    /* Equal bonds broken and formed: nothing changes, and it must not be
     * called endothermic. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("equal bonds give dH = 0", "dH = 0 kJ/mol");
    showed("and say no net change", "no net change");
    ok("and not endothermic", !fake_screen_has("endothermic"), "said endothermic");

    /* Fractional counts: H2 + 1/2 O2 -> H2O, the fraction typed on the real
     * fraction key. 436 + 249 = 685 broken, 2 x O-H = 926 formed, -241. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    bond_pick("O=O");        fake_press_number("1/2");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("O-H");        fake_press_number("2");
    menu_pick(1);
    bond_finish();
    showed("a half count is shown as typed", "1/2 x O=O (498) = 249");
    showed("a whole count still reads 1 x H-H", "1 x H-H (436) = 436");
    showed("water breaks 685", "broken = 685 kJ/mol");
    showed("and forms 926", "formed = 926 kJ/mol");
    showed("so water forms at -241", "dH = -241 kJ/mol");
    showed("which is exothermic", "exothermic");

    /* 3/2 through the divide key and 0.5 as a decimal: 3/2 x 498 = 747 and
     * 0.5 x 436 = 218 broken, 2 x 431 = 862 formed, dH = 103. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("O=O");
    fake_press(KEY_3);  fake_press(KEY_DIV);  fake_press(KEY_2);  fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("0.5");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("H-Cl");       fake_press_number("2");
    menu_pick(1);
    bond_finish();
    showed("3/2 typed with the divide key", "3/2 x O=O (498) = 747");
    showed("0.5 typed as a decimal", "0.5 x H-H (436) = 218");
    showed("they add up: 965 broken", "broken = 965 kJ/mol");

    /* F1 types the slash too, and 5/4 works: 5/4 x 436 = 545. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");
    fake_press(KEY_5);  fake_press(KEY_F1);  fake_press(KEY_4);  fake_press(KEY_EXE);
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("O-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("5/4 typed with F1", "5/4 x H-H (436) = 545");

    /* Every bad count is tried on its own: refused with the message, asked
     * again, and the good count after it is the only one that is used. A
     * count that slipped through would show as "0 x", "inf x" or its own
     * text on the result page, and would also upset the key script. */
    {
        static const char *const bad[] = {
            "1/0", "0", "-1/2", "1/-2", "-1/-2", "1/2/3", "1/", "1e999", "1/1e999"
        };
        unsigned b;

        for (b = 0; b < sizeof bad / sizeof bad[0]; b++) {
            char label[80], shown[40];

            fake_reset();
            menu_pick(2);
            fake_press(KEY_EXE);
            bond_pick("H-H");
            fake_press_number(bad[b]);  fake_press(KEY_EXE);    /* and the message */
            fake_press_number("2");
            menu_pick(1);
            fake_press(KEY_EXE);
            bond_pick("O-H");        fake_press_number("1");
            menu_pick(1);
            bond_finish();
            snprintf(label, sizeof label, "%s is refused with a message", bad[b]);
            showed(label, "Use a number above 0, e.g. 1/2");
            snprintf(label, sizeof label, "%s is not accepted as a count", bad[b]);
            snprintf(shown, sizeof shown, "%s x H-H", bad[b]);
            ok(label, !fake_screen_has(shown), shown);
            showed("the good count after it is used", "2 x H-H (436) = 872");
            ok("and nothing reads 0 x", !fake_screen_has("0 x"), "showed 0 x");
            ok("or inf", !fake_screen_has("inf"), "showed inf");
            ok("or nan", !fake_screen_has("nan"), "showed nan");
        }
    }

    /* Done with nothing on a side is refused and the list stays open. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(1);                       /* Done, with no bond yet */
    fake_press(KEY_EXE);                /* the message */
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    fake_press(KEY_EXE);
    menu_pick(1);                       /* the same on the formed side */
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("Done on an empty side is refused", "Add at least one bond");
    ok("and no bond is invented for it", !fake_screen_has("none"), "showed none");
    showed("the list stayed open for the real bond", "1 x H-H (436) = 436");

    /* Thirds add up with rounding dust, which is not a net change. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1/3");
    bond_pick("H-H");        fake_press_number("1/3");
    bond_pick("H-H");        fake_press_number("1/3");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("three thirds of H-H against one H-H is dH = 0", "dH = 0 kJ/mol");
    showed("which says no net change", "no net change");
    ok("and not exothermic or endothermic",
       !fake_screen_has("exothermic") && !fake_screen_has("endothermic"), NULL);

    /* The last bond in the booklet's table is in the list, however long it
     * grows. */
    {
        const char *last = energy_bonds[energy_bond_count - 1].bond;
        char want[40];

        fake_reset();
        menu_pick(2);
        fake_press(KEY_EXE);
        bond_pick(last);         fake_press_number("1");
        menu_pick(1);
        fake_press(KEY_EXE);
        bond_pick(last);         fake_press_number("1");
        menu_pick(1);
        bond_finish();
        snprintf(want, sizeof want, "1 x %s (%d)", last,
                 energy_bonds[energy_bond_count - 1].enthalpy);
        showed("the last bond in the table can be picked", want);
    }

    /* EXIT in a field drops that one bond and goes back to the list. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press_text("N-N");  fake_press(KEY_EXIT);     /* the bond field */
    bond_pick("C-H");        fake_press(KEY_EXIT);     /* the count field */
    menu_pick(2);
    fake_press_text("c-s");  fake_press(KEY_EXE);
    fake_press(KEY_EXE);                               /* "not in the booklet" */
    fake_press(KEY_EXIT);                              /* the kJ/mol field */
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("O-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("the bonds that were not abandoned are kept", "1 x H-H (436) = 436");
    ok("EXIT in the bond field drops the bond", !fake_screen_has("x N-N"), "kept N-N");
    ok("EXIT in the count field drops the bond", !fake_screen_has("x C-H"), "kept C-H");
    ok("EXIT in the kJ/mol field drops the bond", !fake_screen_has("x c-s"), "kept c-s");
    showed("and broken is only the one bond", "broken = 436 kJ/mol");

    /* EXIT in the list gives up the whole calculation, on either side. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    fake_press(KEY_EXIT);               /* the broken list */
    fake_press(KEY_EXIT);               /* the energy menu */
    screen_energy();
    ok("EXIT in the first list shows no result",
       !fake_screen_has("Bonds entered") && !fake_screen_has("dH ="), "showed a result");
    ok("and uses the keys exactly", fake_keys_left() == 0 && !fake_ran_out_of_keys(), NULL);

    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    bond_pick("H-H");        fake_press_number("1");
    menu_pick(1);
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);               /* the formed list */
    fake_press(KEY_EXIT);
    screen_energy();
    ok("EXIT in the second list shows no result too",
       !fake_screen_has("Bonds entered") && !fake_screen_has("dH ="), "showed a result");
    ok("and uses the keys exactly", fake_keys_left() == 0 && !fake_ran_out_of_keys(), NULL);

    /* Twelve bonds on a side is the most that fit; the list closes itself. */
    fake_reset();
    menu_pick(2);
    fake_press(KEY_EXE);
    {
        int i;

        for (i = 0; i < 12; i++) {
            bond_pick("H-H");    fake_press_number("1");
        }
    }
    fake_press(KEY_EXE);                /* "That is as many as fit" */
    fake_press(KEY_EXE);                /* "Now the bonds formed" */
    bond_pick("O-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("the twelfth bond says that is as many as fit", "That is as many as fit");
    showed("and all twelve count", "broken = 5232 kJ/mol");

    /* [-] types a minus in a bond field only; elsewhere it stays a letter. */
    {
        char text[UI_TEXT_LEN];

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_SUB);  fake_press(KEY_EXE);
        ui_text_input("Formula", "Formula:", text, (int)sizeof text);
        ok("[-] in a formula field is not a minus", strchr(text, '-') == NULL && text[0] != 0, text);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_NEG);  fake_press(KEY_EXE);
        ui_text_input("Formula", "Formula:", text, (int)sizeof text);
        ok("(-) in a formula field still types a minus", strcmp(text, "-") == 0, text);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_SUB);  fake_press(KEY_EXE);
        ui_bond_input("Bond", "Bond:", text, (int)sizeof text);
        ok("[-] in a bond field is a minus", strcmp(text, "-") == 0, text);
    }

    section("7. The structure and data screens");

    /* Electron configuration of iron, then of the Fe3+ ion. */
    fake_reset();
    menu_pick(1);                       /* Electron configuration */
    fake_press_text("Fe");
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);                /* charge left blank = the atom */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("iron fills 3d6 4s2", "3d6 4s2");
    showed("and the shorthand starts from argon", "[Ar]");

    fake_reset();
    menu_pick(1);
    fake_press_text("Fe");
    fake_press(KEY_EXE);
    fake_press_number("3");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("Fe3+ ends at 3d5", "3d5");

    /* Oganesson's configuration is over 80 characters, more than two lines of
     * 34: it is split at spaces over as many lines as it needs, and the last of
     * them is on a line of its own, not cut off. */
    fake_reset();
    menu_pick(1);
    fake_press_text("Og");
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("the heaviest configuration starts on its first line", "\n1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6\n");
    showed("and its last line is whole", "\n6p6 6d10 7s2 7p6\n");
    showed("its shorthand drops the whole [Rn] core", "\n[Rn] 5f14 6d10 7s2 7p6\n");
    all_keys_used("long configuration");

    fake_reset();
    menu_pick(1);
    fake_press_text("Pb");
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("lead's shorthand keeps 4f14 and drops 5s2 5p6", "\n[Xe] 4f14 5d10 6s2 6p2\n");

    /* Oxidation numbers of permanganate. */
    fake_reset();
    menu_pick(2);                       /* Oxidation numbers */
    fake_press_text("KMnO4");
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);                /* charge blank = a compound */
    fake_press(KEY_EXE);                /* not a peroxide */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("manganese comes out +7", "+7");

    /* Ionic formula: aluminium and oxygen. */
    fake_reset();
    menu_pick(3);                       /* Ionic formula */
    fake_press_text("Al");
    fake_press(KEY_EXE);
    fake_press_number("3");
    fake_press_text("O");
    fake_press(KEY_EXE);
    fake_press_number("2");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("aluminium oxide is Al2O3", "Al2O3");

    /* Ar of chlorine from its two isotopes. */
    fake_reset();
    menu_pick(4);                       /* Isotopes */
    menu_pick(1);                       /* Ar from the abundances */
    fake_press_number("2");             /* two isotopes */
    fake_press_number("34.969");
    fake_press_number("75.77");
    fake_press_number("36.966");
    fake_press_number("24.23");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("chlorine comes out at 35.45", "35.45");

    /* An uncertainty as a percentage. */
    fake_reset();
    menu_pick(5);                       /* Uncertainties */
    menu_pick(1);                       /* absolute to percentage */
    fake_press_number("25");
    fake_press_number("0.05");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("0.05 in 25.00 is 0.2 %", "0.2");

    /* IHD of benzene. */
    fake_reset();
    menu_pick(6);                       /* IHD */
    fake_press_text("C6H6");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("benzene has an IHD of 4", "IHD = 4");

    /* Atom economy: one equation, then the product that is wanted. The page
     * is a heading and 6 lines with no key pressed, answer included. */
    fake_reset();
    menu_pick(5);                       /* Atom economy */
    equation("CH4+2O2->CO2+2H2O");
    menu_pick(2);                       /* Desired product: H2O */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("atom economy of 2 H2O from CH4 + 2O2 is 45.02 %", "atom economy = 45.02 %");
    showed("reactants M x coeff is 80.05", "reactants M x coeff = 80.05 g/mol");
    showed("the wanted H2O has M x coeff 36.04", "H2O M x coeff = 36.04 g/mol");
    showed("the product menu lists the right-hand side", "Desired product");
    showed("the equation is shown as used", "2 O2");
    ok("and it is not the old 71 %", !fake_screen_has("71"), NULL);
    all_keys_used("atom economy");

    /* A long product formula must not push the value or its unit off the line. */
    fake_reset();
    menu_pick(5);                       /* Atom economy */
    equation("3CaCl2+2Na3PO4->Ca3(PO4)2+6NaCl");
    menu_pick(1);                       /* Desired product: Ca3(PO4)2 */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a long product is named on its own line", "wanted: Ca3(PO4)2");
    showed("and its value and unit are whole", "wanted M x coeff = 310.2 g/mol");
    showed("with the atom economy beneath", "atom economy = ");
    all_keys_used("atom economy, long product");

    /* No numbers typed: it balances the equation, and says what it used. */
    fake_reset();
    menu_pick(5);
    equation("CH4+O2->CO2+H2O");
    menu_pick(2);                       /* H2O */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("an unbalanced equation gives the same 45.02 %", "atom economy = 45.02 %");
    showed("the result shows the balanced O2", "2 O2");
    showed("and the whole balanced equation on one line", "CH4 + 2 O2 -> CO2 + 2 H2O");
    all_keys_used("unbalanced");

    /* The other product of the same reaction. */
    fake_reset();
    menu_pick(5);
    equation("CH4+2O2->CO2+2H2O");
    menu_pick(1);                       /* CO2 */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("CO2 is the wanted product: 54.98 %", "atom economy = 54.98 %");
    showed("and CO2 has M x coeff 44.01", "CO2 M x coeff = 44.01 g/mol");
    all_keys_used("CO2");

    fake_reset();
    menu_pick(5);
    equation("N2+3H2->2NH3");
    menu_pick(1);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a single product is 100 %", "atom economy = 100 %");
    all_keys_used("ammonia");

    /* Some numbers typed: they are used, and a missing one is 1. */
    fake_reset();
    menu_pick(5);
    equation("CH4+2O2->CO2+2H2O");
    menu_pick(2);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a missing coefficient counts as 1: CH4 + 2O2 -> CO2 + 2H2O", "atom economy = 45.02 %");
    all_keys_used("typed coefficients");

    /* Typed numbers that do not balance are refused, the text is kept, and
     * fixing the number gives the answer. */
    fake_reset();
    menu_pick(5);
    equation("CH4+2O2->CO2+H2O");
    menu_pick(2);
    fake_press(KEY_EXE);                /* "Numbers don't balance" */
    fake_press(KEY_DEL);  fake_press(KEY_DEL);
    fake_press(KEY_DEL);                /* rub out H2O ... */
    fake_press_text("2H2O");            /* ... and the field still holds the rest */
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("numbers that do not balance are refused", "Numbers don't balance");
    showed("the text was kept and fixing it gives 45.02 %", "atom economy = 45.02 %");
    all_keys_used("atom economy, unbalanced");

    /* Mistakes keep the text. */
    fake_reset();
    menu_pick(5);
    equation("CH4+2O2");                /* no arrow */
    fake_press(KEY_EXE);
    fake_press_text("->CO2+2H2O");
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("no arrow is explained", "Need -> or =");
    showed("and the text was kept", "atom economy = 45.02 %");
    all_keys_used("atom economy, no arrow");

    fake_reset();
    menu_pick(5);
    equation("CH4+2O2->CO2+2H2Q");      /* not an element */
    fake_press(KEY_EXE);
    fake_press(KEY_DEL);
    fake_press_text("O");
    fake_press(KEY_EXE);
    menu_pick(2);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("a bad formula is explained", "Unknown element");
    showed("and fixed in place", "atom economy = 45.02 %");
    all_keys_used("atom economy, bad formula");

    fake_reset();
    menu_pick(5);
    equation("H2->O2");
    menu_pick(1);
    fake_press(KEY_EXE);                /* "That will not balance" */
    fake_press(KEY_DEL);  fake_press(KEY_DEL);
    fake_press(KEY_DEL);                /* O2 and "->" are gone: back to H2 */
    equation("+O2->H2O");
    menu_pick(1);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("an equation that cannot balance says so", "That will not balance");
    showed("and fixing it gives 100 %", "atom economy = 100 %");
    all_keys_used("atom economy, will not balance");

    /* EXIT in the product menu goes back to the equation, text kept. */
    fake_reset();
    menu_pick(5);
    equation("CH4+2O2->CO2+2H2O");
    fake_press(KEY_EXIT);               /* leave Desired product */
    fake_press(KEY_EXE);                /* the equation is still there */
    menu_pick(2);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("backing out of the product menu keeps the equation", "atom economy = 45.02 %");
    all_keys_used("atom economy, back");


    section("8. Every procedure shows an example");

    /* A student who has never used the calculator should be able to tell what
     * a field wants from the screen itself. Each menu carries an example for
     * the highlighted entry, and each procedure puts one on its entry screens. */
    fake_reset();
    fake_press(KEY_1);                  /* highlight the first entry */
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("the stoichiometry menu shows an example", "e.g.");
    showed("and it is a worked one", "10 g of CaCO3 -> 0.0999 mol");

    fake_reset();
    fake_press(KEY_3);                  /* and the third one has its own */
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("each entry has its own example",
           "40 % C, 6.7 % H, 53.3 % O -> CH2O");

    fake_reset();
    menu_pick(1);                       /* Moles */
    fake_press(KEY_EXIT);               /* leave the sub-menu */
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("the moles menu explains each choice", "CaCO3, 10 g -> 0.0999 mol");

    fake_reset();
    menu_pick(2);                       /* Percent composition */
    fake_press(KEY_EXIT);               /* leave the formula field */
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("the formula field carries its example too",
           "H2O -> 11.2 % H and 88.8 % O");

    fake_reset();
    fake_press(KEY_2);
    fake_press(KEY_EXIT);
    screen_acids();
    showed("acids and bases have examples", "0.1 mol/dm3 HCl -> pH 1");

    fake_reset();
    fake_press(KEY_1);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("so does energy", "100 g of water, 25 K rise -> 10450 J");

    fake_reset();
    fake_press(KEY_2);
    fake_press(KEY_EXIT);
    screen_tools();
    showed("and structure and data", "KMnO4 -> manganese is +7");

    fake_reset();
    fake_press(KEY_EXIT);               /* the balancer asks straight away */
    screen_balance();
    showed("the balancer says what to type",
           "C3H8+O2->CO2+H2O gives 1, 5, 3, 4");

    section("9. The calculator's own look");

    /* Pixels cannot be read back, but the text and the scrolling can. */
    {
        static char names[32][16];
        static const char *items[32];
        int i, cursor = 0, choice;

        for (i = 0; i < 32; i++) {
            snprintf(names[i], sizeof names[i], "Item %d", i + 1);
            items[i] = names[i];
        }

        /* UP from the top wraps to the last of 32 entries, far below the 7 rows
         * that fit, and the list scrolls to show it. */
        fake_reset();
        fake_press(KEY_UP);
        fake_press(KEY_EXE);
        choice = ui_menu("Long menu", items, 32, &cursor);
        ok("a menu longer than the screen reaches its last entry", choice == 31, NULL);
        showed("and shows it, numbered like the OS menus", "32:Item 32");
        ok("the old 32/32 position badge is gone", !fake_screen_has("32/32"), NULL);
        ok("EXIT does the going back, so there is no BACK key", !fake_screen_has("BACK"), NULL);
        all_keys_used("long menu");

        /* A page of 14 lines shows its heading and 6 lines, scrolls with DOWN
         * one line at a time to reach the last line, and has no BACK key either. */
        fake_reset();
        ui_result_begin("Long page");
        for (i = 0; i < 14; i++)
            ui_result_line(items[i]);
        fake_press(KEY_EXE);
        ui_result_show();
        showed("a result page shows its heading", "Long page");
        showed("and its sixth line", "Item 6");
        ok("but not its seventh until it scrolls", !fake_screen_has("Item 7"), NULL);
        ok("the result page has no BACK key", !fake_screen_has("BACK"), NULL);
        all_keys_used("page top");

        fake_reset();
        ui_result_begin("Long page");
        for (i = 0; i < 14; i++)
            ui_result_line(items[i]);
        for (i = 0; i < 7; i++)
            fake_press(KEY_DOWN);
        fake_press(KEY_EXE);
        ui_result_show();
        ok("seven DOWNs are not enough to reach the 14th line", !fake_screen_has("Item 14"), NULL);
        all_keys_used("page almost at the end");

        fake_reset();
        ui_result_begin("Long page");
        for (i = 0; i < 14; i++)
            ui_result_line(items[i]);
        for (i = 0; i < 8; i++)
            fake_press(KEY_DOWN);
        fake_press(KEY_EXE);
        ui_result_show();
        showed("eight DOWNs scroll to its last line", "Item 14");
        all_keys_used("long page");

        /* a page that ends in a rule and an answer, as the procedures' do, but
         * is too long to fit: it opens scrolled down, so the answer is in view
         * and the up arrow (magenta) says there is more above */
        fake_reset();
        ui_result_begin("Answer page");
        for (i = 0; i < 9; i++)
            ui_result_line(items[i]);
        ui_result_rule();
        ui_result_line("the answer");
        fake_press(KEY_EXE);
        ui_result_show();
        showed("a long page opens with its answer in view", "the answer");
        ok("and the lines above scrolled out", !fake_screen_has("Item 4"), NULL);
        showed("down to the last rule's six lines", "Item 6");
        ok("an up arrow shows there is more above", fake_rects(MAGENTA) > 0, NULL);
        ok("and the heading is still there", fake_screen_has("Answer page"), NULL);
        all_keys_used("answer page");

        fake_reset();
        ui_result_begin("Answer page");
        for (i = 0; i < 9; i++)
            ui_result_line(items[i]);
        ui_result_rule();
        ui_result_line("the answer");
        for (i = 0; i < 5; i++)
            fake_press(KEY_UP);
        fake_press(KEY_EXE);
        ui_result_show();
        showed("UP scrolls back to the first line", "Item 1");
        all_keys_used("answer page, back up");

        /* every one of the 32 entries is drawn on the way down, in order, and
         * the sevens are paged by RIGHT */
        fake_reset();
        for (i = 0; i < 31; i++)
            fake_press(KEY_DOWN);
        fake_press(KEY_EXE);
        cursor = 0;
        choice = ui_menu("Long menu", items, 32, &cursor);
        for (i = 1; i <= 32; i++) {
            char line[16];

            snprintf(line, sizeof line, "%d:Item %d", i, i);
            if (!fake_screen_has(line))
                break;
        }
        ok("walking down a 32-item menu draws every item", i == 33 && choice == 31, NULL);
        all_keys_used("walk the long menu");

        fake_reset();
        fake_press(KEY_RIGHT);
        fake_press(KEY_EXE);
        cursor = 0;
        choice = ui_menu("Long menu", items, 32, &cursor);
        ok("RIGHT pages down by the seven rows shown", choice == 7, NULL);
        all_keys_used("page the long menu");

        /* a menu with examples keeps the seventh row for the example: six entries
         * are shown, the seventh is below the fold, and RIGHT pages by six */
        {
            static const char *const hints[32] = {"the example"};

            fake_reset();
            fake_press(KEY_EXE);
            cursor = 0;
            ui_menu_hints("Hints", items, hints, 32, &cursor);
            showed("a menu with examples shows its sixth entry", "6:Item 6");
            ok("but not its seventh, which would sit on the example",
               !fake_screen_has("7:Item 7"), NULL);
            showed("and the example", "the example");
            ok("and the arrow shows there is more", fake_rects(MAGENTA) > 0, NULL);

            fake_reset();
            fake_press(KEY_RIGHT);
            fake_press(KEY_EXE);
            cursor = 0;
            choice = ui_menu_hints("Hints", items, hints, 32, &cursor);
            ok("RIGHT pages by the six rows shown", choice == 6, NULL);
        }

        fake_reset();
        fake_press(KEY_EXE);
        ui_message("Title", "A message");
        showed("a message is shown", "A message");
        ok("and has no BACK key", !fake_screen_has("BACK"), NULL);
        all_keys_used("message");

        /* the longest message, 37 characters, is wider than the pop-up can be:
         * it wraps at a space, in two even lines rather than a word on its own */
        fake_reset();
        fake_press(KEY_EXE);
        ui_message("Rates", "Two different temperatures are needed");
        showed("a long message wraps: first line", "\nTwo different\n");
        showed("and second line", "\ntemperatures are needed\n");
        ok("and is not drawn in one piece", !fake_screen_has("different temperatures"), NULL);
        all_keys_used("long message");
    }

    section("10. Battery, mode indicators and the menus' background");

    {
        static const char *const items[] = {"Item 1", "Item 2", "Item 3"};
        static const char *const hints[] = {"hint one", "hint two", NULL};
        const int tint = C_RGB(31, UI_TINT_G, UI_TINT_B), red = C_RGB(31, 0, 0);
        const int yellow = C_RGB(31, 31, 0);
        int cursor = 0, v;
        char text[UI_EQUATION_LEN] = "";

        /* centivolts a reading must reach for 1, 2 and 3 bars: alkaline, Ni-MH */
        ok("alkaline: 4.49 V is empty, 4.50 V one bar",
           battery_bars(449, 1) == 0 && battery_bars(450, 1) == 1, NULL);
        ok("alkaline: 4.89 V is one bar, 4.90 V two",
           battery_bars(489, 1) == 1 && battery_bars(490, 1) == 2, NULL);
        ok("alkaline: 5.39 V is two bars, 5.40 V three, and fresh cells stay at three",
           battery_bars(539, 1) == 2 && battery_bars(540, 1) == 3 && battery_bars(640, 1) == 3, NULL);
        ok("Ni-MH: 4.39 V is empty, 4.40 V one bar",
           battery_bars(439, 2) == 0 && battery_bars(440, 2) == 1, NULL);
        ok("Ni-MH: 4.59 V is one bar, 4.60 V two",
           battery_bars(459, 2) == 1 && battery_bars(460, 2) == 2, NULL);
        ok("Ni-MH: 4.79 V is two bars, 4.80 V three",
           battery_bars(479, 2) == 2 && battery_bars(480, 2) == 3, NULL);
        ok("the battery type matters: 4.70 V is one bar of alkaline, two of Ni-MH",
           battery_bars(470, 1) == 1 && battery_bars(470, 2) == 2, NULL);
        ok("an unknown type (0, as on the emulator) is read as alkaline",
           battery_bars(470, 0) == battery_bars(470, 1), NULL);
        ok("nothing at all is no bars", battery_bars(0, 1) == 0, NULL);

        /* the strip: the OS's reading, as blue bars. Only a menu is drawn here,
         * and the one thing in a menu that is blue is the battery. */
        fake_reset();
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("6.00 V alkaline shows three blue bars", fake_rects(C_BLUE) == 3, NULL);
        ok("the OS was asked once", fake_os_reads() == 1, NULL);

        fake_reset();
        fake_battery(480, 1);
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("4.80 V alkaline shows one bar", fake_rects(C_BLUE) == 1, NULL);

        fake_reset();
        fake_battery(500, 2);
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("5.00 V Ni-MH shows three bars", fake_rects(C_BLUE) == 3, NULL);

        fake_reset();
        fake_battery(0, 1);
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("no reading from the OS draws no battery, not a made-up one",
           fake_rects(C_BLUE) == 0, NULL);
        ok("and the menu still works", fake_screen_has("1:Item 1"), NULL);

        /* only 2.00 V to 9.00 V is a battery: anything else is no reading */
        fake_battery(199, 1);
        ok("1.99 V is no reading", battery_level() == -1, NULL);
        fake_battery(200, 1);
        ok("2.00 V is a reading, empty", battery_level() == 0, NULL);
        fake_battery(900, 1);
        ok("9.00 V is a reading, full", battery_level() == 3, NULL);
        fake_battery(901, 1);
        ok("9.01 V is no reading", battery_level() == -1, NULL);
        fake_battery(-5, 1);
        ok("a negative reading is none", battery_level() == -1, NULL);
        fake_reset();
        fake_battery(901, 1);
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("and an implausible one draws no icon", fake_rects(C_BLUE) == 0, NULL);

        /* many redraws, few questions: it must not slow the keys down */
        fake_reset();
        for (v = 0; v < 5; v++)
            fake_press(KEY_DOWN);
        fake_press(KEY_EXE);
        ui_menu("Battery", items, 3, &cursor);
        ok("six redraws ask the OS once", fake_os_reads() == 1, NULL);
        fake_press(KEY_EXE);
        fake_advance(29);
        ui_menu("Battery", items, 3, &cursor);
        ok("and 29 seconds later still once", fake_os_reads() == 1, NULL);
        fake_press(KEY_EXE);
        fake_advance(2);
        ui_menu("Battery", items, 3, &cursor);
        ok("31 seconds later it asks again", fake_os_reads() == 2, NULL);

        /* The mode indicator, as the OS draws its ALPHA one (Software User's Guide,
         * "Status Bar"): white on a solid red box, A or a, with a yellow padlock
         * because ALPHA stays on until it is pressed again; nothing at all in
         * digit mode. A screen is a frame, so counting frames and red boxes says
         * which screens had the box. */

        /* the stand-in behaves like gint: getkey() swallows ALPHA and SHIFT as
         * modifiers and only getkey_opt() without them returns the keys */
        fake_reset();
        fake_press(KEY_ALPHA);  fake_press(KEY_1);
        fake_press(KEY_SHIFT);  fake_press(KEY_2);
        fake_press(KEY_ALPHA);  fake_press(KEY_ALPHA);
        {
            key_event_t a = getkey(), b = getkey();
            key_event_t c = getkey_opt(GETKEY_DEFAULT & ~(GETKEY_MOD_SHIFT | GETKEY_MOD_ALPHA), NULL);
            key_event_t d = getkey_opt(GETKEY_DEFAULT & ~(GETKEY_MOD_SHIFT | GETKEY_MOD_ALPHA), NULL);
            ok("getkey() swallows ALPHA: the next key comes back with alpha set",
               a.key == KEY_1 && a.alpha == 1 && a.shift == 0, NULL);
            ok("and SHIFT the same way", b.key == KEY_2 && b.shift == 1 && b.alpha == 0, NULL);
            ok("without the modifier options ALPHA is a key of its own",
               c.key == KEY_ALPHA && d.key == KEY_ALPHA, NULL);
        }

        fake_reset();
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("letters mode shows an A", fake_text_colour("A") != -2, NULL);
        ok("in white", fake_text_colour("A") == C_WHITE, NULL);
        ok("on a solid red box", fake_rects(red) == 1, NULL);
        ok("with the alpha-lock padlock, yellow", fake_rects(yellow) == 1, NULL);

        /* ALPHA off: the box goes (the second screen has none), digits type */
        fake_reset();
        fake_press(KEY_ALPHA);
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("ALPHA redraws the field", fake_frames() == 2, NULL);
        ok("and the red box is only on the screen before it", fake_rects(red) == 1, NULL);
        ok("and so is the padlock", fake_rects(yellow) == 1, NULL);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_1);  fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("after ALPHA a number key types its digit", strcmp(text, "1") == 0, text);

        /* ALPHA on again: the box comes back (first and third screens) */
        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_ALPHA);
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("ALPHA twice redraws twice", fake_frames() == 3, NULL);
        ok("the box is on the first and third screens", fake_rects(red) == 2, NULL);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_ALPHA);  fake_press(KEY_ALPHA);  fake_press(KEY_1);
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("after ALPHA twice a number key is the letter on it again", strcmp(text, "U") == 0, text);

        /* small letters: the same red box, with a white a, as the OS's A and a */
        fake_reset();
        fake_press(KEY_SHIFT);              /* SHIFT toggles small letters here */
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("after SHIFT it shows a small a, still white", fake_text_colour("a") == C_WHITE, NULL);
        ok("in a red box on both screens it was drawn", fake_rects(red) == 2, NULL);
        ok("SHIFT has no indicator of its own, since it is not a pending key",
           fake_text_colour("S") == -2, NULL);
        ok("the small a has the padlock too", fake_rects(yellow) == 2, NULL);

        fake_reset();
        text[0] = 0;
        fake_press(KEY_F5);                 /* the equation field's A <-> a key */
        fake_press(KEY_XOT);
        fake_press(KEY_F5);
        fake_press(KEY_XOT);
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("F5 and SHIFT agree: a then A", strcmp(text, "aA") == 0, text);

        /* digit mode has no indicator, even with small letters picked */
        fake_reset();
        fake_press(KEY_ALPHA);
        fake_press(KEY_SHIFT);
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("digits mode: SHIFT redraws, no box on the screens after ALPHA",
           fake_frames() == 3 && fake_rects(red) == 1, NULL);

        fake_reset();
        {
            double value = 0.0;
            fake_press(KEY_EXE);
            ui_number_input("Mode", "Number:", &value, 1);
        }
        ok("a number field has no box and no red", fake_rects(red) == 0
           && fake_text_colour("A") == -2 && !fake_screen_has("123"), NULL);

        /* the background: on the menus, not on the entry and result screens, as in
         * the OS; and the text on it is all still there, in its own colours */
        cursor = 0;
        fake_reset();
        fake_press(KEY_EXE);
        ui_menu_hints("Menu", items, hints, 3, &cursor);
        ok("a menu is drawn over the light orange gradient", fake_rects(tint) >= 1, NULL);
        ok("the menu text is all still captured",
           fake_screen_has("1:Item 1") && fake_screen_has("2:Item 2")
           && fake_screen_has("3:Item 3") && fake_screen_has("hint one"), NULL);
        ok("the chosen row is white on the black bar",
           fake_text_colour("1:Item 1") == C_WHITE && fake_text_colour("2:Item 2") == C_BLACK, NULL);
        ok("the hint stays black", fake_text_colour("hint one") == C_BLACK, NULL);

        fake_reset();
        fake_press(KEY_EXE);
        ui_equation_input("Mode", "Equation:", text, UI_EQUATION_LEN);
        ok("an entry screen stays white", fake_rects(tint) == 0, NULL);

        fake_reset();
        ui_result_begin("Result");
        ui_result_line("A line");
        fake_press(KEY_EXE);
        ui_result_show();
        ok("a result page stays white", fake_rects(tint) == 0, NULL);

        fake_reset();
        fake_press(KEY_EXE);
        ui_message("Title", "A message");
        ok("so does a message", fake_rects(tint) == 0, NULL);
    }

    /* every screen above has been drawn by now: none ran off the right edge */
    ok("nothing was drawn past the edge of the screen", fake_overflows() == 0,
       fake_first_overflow());

    printf("\n============================================================\n");
    printf("  Screen tests Total: %d   Passed: %d   Failed: %d\n",
           passed + failed, passed, failed);
    return failed ? 1 : 0;
}
