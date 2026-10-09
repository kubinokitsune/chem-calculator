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
#include "../src/core/energy.h"

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
    showed("with the products on their own lines", "->  3 CO2");
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
    showed("the 16 shows on the HCl line", "16 HCl");
    all_keys_used("permanganate");

    /* 47 characters: wider than the field, so it scrolls while typing. */
    fake_reset();
    equation("C6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("glucose + dichromate is 1, 4, 16, 6, 4, 4, 22",
           "Coefficients: 1, 4, 16, 6, 4, 4, 22");
    ok("the long equation was never drawn in one piece",
       !fake_screen_has("C6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O"), "no scrolling");
    showed("but its end was in view", "6H12O6+K2Cr2O7+H2SO4->CO2+K2SO4+Cr2(SO4)3+H2O");
    all_keys_used("long equation");

    /* Numbers in front are ignored, and the prompt says so. */
    fake_reset();
    equation("2C3H8+O2->CO2+H2O");
    fake_press(KEY_EXIT);
    screen_balance();
    showed("a typed coefficient is ignored by the balancer", "Coefficients: 1, 5, 3, 4");
    showed("and the prompt says so", "numbers in front are ignored");
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
           !fake_screen_has(text) && fake_screen_has(text + 2),
           "the whole text was drawn, or the end was not");

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
    fake_press_number("272");           /* its kJ/mol */
    fake_press_number("2");
    menu_pick(1);
    fake_press(KEY_EXE);
    bond_pick("C-H");        fake_press_number("1");
    menu_pick(1);
    bond_finish();
    showed("an unknown bond asks for its enthalpy", "Not in booklet. kJ/mol of c-s:");
    showed("and the typed value is used, in the spelling typed", "2 x c-s (272) = 544");
    showed("so dH is 544 - 414 = 130", "dH = 130 kJ/mol");
    showed("which is endothermic", "endothermic");

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

    /* Atom economy: one equation, then the product that is wanted. */
    fake_reset();
    menu_pick(5);                       /* Atom economy */
    equation("CH4+2O2->CO2+2H2O");
    menu_pick(2);                       /* Desired product: H2O */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("atom economy of 2 H2O from CH4 + 2O2 is 45.02 %", "atom economy = 45.02 %");
    showed("reactants M x coeff is 80.05", "reactants M x coeff = 80.05 g/mol");
    showed("wanted M x coeff is 36.04", "wanted M x coeff = 36.04 g/mol");
    showed("the product menu lists the right-hand side", "Desired product");
    showed("the equation is shown as used", "2 O2");
    ok("and it is not the old 71 %", !fake_screen_has("71"), NULL);
    all_keys_used("atom economy");

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
    showed("and the balanced H2O", "->  CO2");
    showed("and 2 H2O", "+   2 H2O");
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
    showed("its M x coeff is 44.01", "wanted M x coeff = 44.01 g/mol");
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

        /* UP from the top wraps to the last of 32 entries, far below the 9 rows
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

        /* A page of 14 lines shows its heading, scrolls with DOWN to reach the
         * last line, and has no BACK key either. */
        fake_reset();
        ui_result_begin("Long page");
        for (i = 0; i < 14; i++)
            ui_result_line(items[i]);
        for (i = 0; i < 4; i++)
            fake_press(KEY_DOWN);
        fake_press(KEY_EXE);
        ui_result_show();
        showed("a result page shows its heading", "Long page");
        showed("and DOWN scrolls to its last line", "Item 14");
        ok("the result page has no BACK key", !fake_screen_has("BACK"), NULL);
        all_keys_used("long page");

        fake_reset();
        fake_press(KEY_EXE);
        ui_message("Title", "A message");
        showed("a message is shown", "A message");
        ok("and has no BACK key", !fake_screen_has("BACK"), NULL);
        all_keys_used("message");
    }

    printf("\n============================================================\n");
    printf("  Screen tests  Total: %d   Passed: %d   Failed: %d\n",
           passed + failed, passed, failed);
    return failed ? 1 : 0;
}
