/* ui.c - see ui.h. This is the only file that talks to the screen and keypad. */

#include "ui.h"
#include "../core/chem.h"

#include <gint/display.h>
#include <gint/keyboard.h>

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The fx-CG50's own applications are drawn on a 384 x 216 area that sits 6 px
 * in from the left of gint's 396 x 224 screen. gint's font is 8 x 9, so menu
 * rows are 18 px apart (the OS uses 24 with a bigger font). Result pages are
 * denser, 15 px, so a page of ten lines and its heading fit without scrolling. */
#define ROW_HEIGHT   18
#define PAGE_ROW     15
#define STRIP_HEIGHT 24          /* white status strip, 1 px rule on its last row */
#define SOFT_TOP     192         /* top of the softkey tabs */
#define BODY_TOP     (STRIP_HEIGHT + 2)
#define BODY_BOTTOM  (SOFT_TOP - 4)
#define BODY_ROWS    ((SOFT_TOP - BODY_TOP) / ROW_HEIGHT)
#define PAGE_ROWS    ((SOFT_TOP - BODY_TOP) / PAGE_ROW)
#define ROW_LEFT     6           /* the selected-row bar runs ROW_LEFT..ROW_RIGHT */
#define ROW_RIGHT    381
#define ARROW_X      381

/* Colours are 5-6-5: C_RGB takes 0-31 for each. */
#define COL_GREY      C_RGB(17, 17, 17)    /* the strip title and the hints */
#define COL_RED       C_RGB(31, 0, 0)      /* the ALPHA indicator */
#define COL_MAGENTA   C_RGB(31, 0, 31)     /* the scroll arrows */

/* ---- small drawing helpers ---------------------------------------------- */

/* Text drawn twice, a pixel apart, reads as bold with only one font. */
static void bold(int x, int y, int colour, const char *text)
{
    dtext(x, y, colour, text);
    dtext(x + 1, y, colour, text);
}

/* Row `i` of the body, counting from 0, for rows `pitch` px apart. */
static int row_y(int i, int pitch)
{
    return BODY_TOP + i * pitch;
}

/* Where text sits inside a row of `pitch` px. */
#define TEXT_DY(pitch) (((pitch) - 9) / 2)

/* A magenta arrow, 8 px wide and 7 high, pointing down (or up) at the right
 * edge of the row that starts at `y`. */
static void arrow(int y, int pitch, int up)
{
    int k, top = y + (pitch - 7) / 2;

    drect(ARROW_X, top + (up ? 3 : 0), ARROW_X + 1, top + (up ? 6 : 3), COL_MAGENTA);
    for (k = 0; k < 4; k++) {
        int line = up ? top + 3 - k : top + 3 + k;
        drect(ARROW_X - 3 + k, line, ARROW_X + 4 - k, line, COL_MAGENTA);
    }
}

/* Arrows for a list whose rows start at row `first_row` and show `shown` of
 * `total` items from item `first`: up on the first row if there are more above,
 * down on the last if there are more below. */
static void scroll_arrows(int first_row, int pitch, int first, int shown, int total)
{
    if (first > 0)
        arrow(row_y(first_row, pitch), pitch, 1);
    if (first + shown < total)
        arrow(row_y(first_row + shown - 1, pitch), pitch, 0);
}

/* The status strip: the screen's name, small and grey, in the middle, over a
 * black rule. */
void ui_frame(const char *title)
{
    dclear(C_WHITE);
    dtext_opt(DWIDTH / 2, STRIP_HEIGHT / 2 - 1, COL_GREY, C_NONE,
              DTEXT_CENTER, DTEXT_MIDDLE, title, -1);
    drect(ROW_LEFT + 2, STRIP_HEIGHT - 1, ROW_RIGHT + 6, STRIP_HEIGHT - 1, C_BLACK);
}

/* The input mode at the left of the strip, in a thin frame like the SHIFT and
 * ALPHA indicators: a red A or a for the letter modes, the digits otherwise. */
static void mode_box(const char *mode)
{
    char glyph[2] = {mode[0], 0};
    int digits = mode[0] == '1', width;

    if (mode[0] == 0)
        return;
    dsize(digits ? mode : glyph, NULL, &width, NULL);
    drect(ROW_LEFT + 2, 3, ROW_LEFT + width + 7, 19, C_BLACK);
    drect(ROW_LEFT + 3, 4, ROW_LEFT + width + 6, 18, C_WHITE);
    dtext(ROW_LEFT + 5, 7, digits ? C_BLACK : COL_RED, digits ? mode : glyph);
}

/* The six tabs. They are all commands, so each is white with a black border
 * (the OS draws keys that open another menu solid black). */
void ui_softkeys(const char *const *labels)
{
    int i;

    for (i = 0; i < 6; i++) {
        int x = 9 + 64 * i, y = SOFT_TOP, w = 61, h = 22;

        if (labels == NULL || labels[i] == NULL || labels[i][0] == 0)
            continue;
        drect(x + 1, y, x + w - 2, y, C_BLACK);
        drect(x + 1, y + h - 1, x + w - 2, y + h - 1, C_BLACK);
        drect(x, y + 1, x + 1, y + h - 2, C_BLACK);
        drect(x + w - 2, y + 1, x + w - 1, y + h - 2, C_BLACK);
        dtext_opt(x + w / 2, y + h / 2, C_BLACK, C_NONE,
                  DTEXT_CENTER, DTEXT_MIDDLE, labels[i], -1);
    }
}

/* ---- menus -------------------------------------------------------------- */

/* The example shown on entry screens, set by each procedure as it starts. */
static char current_example[UI_LINE_LEN + 20];

void ui_example(const char *text)
{
    if (text == NULL || text[0] == 0)
        current_example[0] = 0;
    else
        snprintf(current_example, sizeof current_example, "%s", text);
}

int ui_menu(const char *title, const char *const *items, int count, int *cursor)
{
    return ui_menu_hints(title, items, NULL, count, cursor);
}

int ui_menu_hints(const char *title, const char *const *items,
                  const char *const *hints, int count, int *cursor)
{
    int top = 0, here = (cursor != NULL) ? *cursor : 0;

    if (here >= count)
        here = 0;

    for (;;) {
        key_event_t event;
        int i;

        if (here < top)
            top = here;
        if (here >= top + BODY_ROWS)
            top = here - BODY_ROWS + 1;

        ui_frame(title);
        for (i = 0; i < BODY_ROWS && top + i < count; i++) {
            int y = row_y(i, ROW_HEIGHT);
            int picked = (top + i == here);
            char line[UI_LINE_LEN + 8];

            /* the chosen row is a black bar, like the OS's own menus */
            if (picked)
                drect(ROW_LEFT, y, ROW_RIGHT, y + ROW_HEIGHT - 1, C_BLACK);
            snprintf(line, sizeof line, "%d:%s", top + i + 1, items[top + i]);
            dtext(10, y + TEXT_DY(ROW_HEIGHT), picked ? C_WHITE : C_BLACK, line);
        }
        scroll_arrows(0, ROW_HEIGHT, top, BODY_ROWS, count);
        /* The example for whatever is highlighted, along the bottom: it says
         * what the option is for without having to open it. */
        if (hints != NULL && hints[here] != NULL && hints[here][0] != 0) {
            int y = BODY_BOTTOM - 14;
            dtext(10, y, COL_GREY, "e.g.");
            dtext(44, y, C_BLACK, hints[here]);
        }
        dupdate();

        event = getkey();
        switch (event.key) {
        case KEY_UP:
            here = (here > 0) ? here - 1 : count - 1;
            break;
        case KEY_DOWN:
            here = (here < count - 1) ? here + 1 : 0;
            break;
        case KEY_LEFT:
            here -= BODY_ROWS;
            if (here < 0)
                here = 0;
            break;
        case KEY_RIGHT:
            here += BODY_ROWS;
            if (here > count - 1)
                here = count - 1;
            break;
        case KEY_EXE:
            if (cursor != NULL)
                *cursor = here;
            return here;
        case KEY_EXIT:
        case KEY_F6:
            if (cursor != NULL)
                *cursor = here;
            return -1;
        default:
            /* the number keys jump straight to an entry */
            if (event.key >= KEY_1 && event.key <= KEY_3) {
                int n = event.key - KEY_1 + 1;
                if (n <= count)
                    here = n - 1;
            } else if (event.key >= KEY_4 && event.key <= KEY_6) {
                int n = event.key - KEY_4 + 4;
                if (n <= count)
                    here = n - 1;
            } else if (event.key >= KEY_7 && event.key <= KEY_9) {
                int n = event.key - KEY_7 + 7;
                if (n <= count)
                    here = n - 1;
            }
            break;
        }
    }
}

/* ---- the keypad's printed letters --------------------------------------- */

/* The red letters on the keys, in keyboard order: A on [X,0,T], B on [log],
 * and so on down to Z on [0]. */
static char letter_for_key(int key)
{
    switch (key) {
    case KEY_XOT:    return 'A';
    case KEY_LOG:    return 'B';
    case KEY_LN:     return 'C';
    case KEY_SIN:    return 'D';
    case KEY_COS:    return 'E';
    case KEY_TAN:    return 'F';
    case KEY_FRAC:   return 'G';
    case KEY_FD:     return 'H';
    case KEY_LEFTP:  return 'I';
    case KEY_RIGHTP: return 'J';
    case KEY_COMMA:  return 'K';
    case KEY_ARROW:  return 'L';
    case KEY_7:      return 'M';
    case KEY_8:      return 'N';
    case KEY_9:      return 'O';
    case KEY_4:      return 'P';
    case KEY_5:      return 'Q';
    case KEY_6:      return 'R';
    case KEY_MUL:    return 'S';
    case KEY_DIV:    return 'T';
    case KEY_1:      return 'U';
    case KEY_2:      return 'V';
    case KEY_3:      return 'W';
    case KEY_ADD:    return 'X';
    case KEY_SUB:    return 'Y';
    case KEY_0:      return 'Z';
    default:         return 0;
    }
}

static char digit_for_key(int key)
{
    switch (key) {
    case KEY_0: return '0';
    case KEY_1: return '1';
    case KEY_2: return '2';
    case KEY_3: return '3';
    case KEY_4: return '4';
    case KEY_5: return '5';
    case KEY_6: return '6';
    case KEY_7: return '7';
    case KEY_8: return '8';
    case KEY_9: return '9';
    default:    return 0;
    }
}

/* Room for typed text inside the field, leaving the cursor and a margin. */
#define FIELD_WIDTH (DWIDTH - 16 - 16 - 4)

/* Draw the shared parts of an entry screen. */
static void entry_screen(const char *title, const char *prompt,
                         const char *text, const char *mode,
                         const char *const *keys, const char *hint,
                         const char *hint2)
{
    int caret, y = row_y(1, ROW_HEIGHT) + TEXT_DY(ROW_HEIGHT);

    ui_frame(title);
    mode_box(mode);
    dtext(10, row_y(0, ROW_HEIGHT) + TEXT_DY(ROW_HEIGHT), C_BLACK, prompt);

    /* Text wider than the line scrolls: drop letters off the front until the
     * end, where the cursor is, fits. */
    for (dsize(text, NULL, &caret, NULL); caret > FIELD_WIDTH && text[0] != 0; text++)
        dsize(text + 1, NULL, &caret, NULL);
    dtext(10, y, C_BLACK, text);
    drect(11 + caret, y - 1, 12 + caret, y + 9, C_BLACK);

    if (current_example[0] != 0) {
        int ey = row_y(3, ROW_HEIGHT) + TEXT_DY(ROW_HEIGHT);

        dtext(10, ey, COL_GREY, "e.g.");
        dtext(44, ey, C_BLACK, current_example);
    }
    if (hint != NULL)
        dtext(10, BODY_BOTTOM - 12, COL_GREY, hint);
    if (hint2 != NULL)
        dtext(10, BODY_BOTTOM - 26, COL_GREY, hint2);
    ui_softkeys(keys);
}

/* The field behind ui_text_input, ui_bond_input and ui_equation_input. F1-F3
 * type the one-character labels in `extras`, which the softkey bar shows. It
 * is the bond field when they start with "-". With a fourth label it is the
 * equation field: F1-F4 type the labels (the last is "->", two characters), the
 * small-letters and digits toggles move to F5 and F6, and in digit mode the
 * keypad's own + ( ) . and -> keys type those too. */
static int text_field(const char *title, const char *prompt, char *buffer,
                      int length, const char *const *extras, int n_extras)
{
    const char *keys[6];
    int alpha = 1, small = 0, i;
    int used = (int)strlen(buffer);
    int bond = extras[0][0] == '-';
    int equation = n_extras == 4;

    for (;;) {
        key_event_t event;
        const char *typed = NULL;
        char letter[2] = {0, 0};

        /* The softkeys say what the keypad cannot: brackets, the hydrate dot,
         * and how to get small letters or digits into a field of letters. */
        for (i = 0; i < n_extras; i++)
            keys[i] = extras[i];
        keys[n_extras] = small ? "ABC" : "abc";
        keys[n_extras + 1] = alpha ? "123" : "ABC";
        if (!equation)
            keys[5] = "OK";

        entry_screen(title, prompt, buffer, alpha ? (small ? "abc" : "ABC") : "123",
                     keys, "[DEL] rub out   [EXE] accept   [EXIT] back",
                     equation ? "F1-F4: ( ) + ->    [SHIFT]: small letters" : NULL);
        dupdate();

        event = getkey();
        switch (event.key) {
        case KEY_EXE:
            return 1;
        case KEY_EXIT:
            return 0;
        case KEY_DEL:
            /* "->" goes as one, so no lone '-' is left behind */
            if (equation && used >= 2 && buffer[used - 2] == '-' && buffer[used - 1] == '>')
                used--;
            if (used > 0)
                buffer[--used] = 0;
            continue;
        case KEY_ALPHA:
            alpha = !alpha;
            continue;
        case KEY_SHIFT:
            small = !small;
            continue;
        case KEY_F1:
        case KEY_F2:
        case KEY_F3:
            typed = extras[event.key - KEY_F1];
            break;
        case KEY_F4:
            if (!equation) {
                small = !small;
                continue;
            }
            typed = extras[3];
            break;
        case KEY_F5:
            if (equation)
                small = !small;
            else
                alpha = !alpha;
            continue;
        case KEY_F6:
            if (!equation)
                return 1;
            alpha = !alpha;
            continue;
        default:
            if (alpha) {
                letter[0] = letter_for_key(event.key);
                if (letter[0] != 0 && small)
                    letter[0] = (char)(letter[0] - 'A' + 'a');
                if (letter[0] == 0)
                    letter[0] = digit_for_key(event.key);
            } else {
                letter[0] = digit_for_key(event.key);
                /* the keypad's own minus keys type a bond; in any other field
                 * [-] stays the letter on it and only (-) types a minus */
                if (letter[0] == 0 && (event.key == KEY_NEG || (bond && event.key == KEY_SUB)))
                    letter[0] = '-';
                /* the equation field's own symbols, in digit mode only */
                if (equation && letter[0] == 0) {
                    switch (event.key) {
                    case KEY_ADD:    letter[0] = '+'; break;
                    case KEY_LEFTP:  letter[0] = '('; break;
                    case KEY_RIGHTP: letter[0] = ')'; break;
                    case KEY_DOT:    letter[0] = '.'; break;
                    case KEY_ARROW:  typed = "->"; break;
                    default: break;
                    }
                }
                if (letter[0] == 0 && typed == NULL)
                    letter[0] = letter_for_key(event.key);
            }
            if (typed == NULL && letter[0] != 0)
                typed = letter;
            break;
        }
        /* a symbol goes in whole or not at all, never half an arrow */
        if (typed != NULL && used + (int)strlen(typed) < length) {
            strcpy(buffer + used, typed);
            used += (int)strlen(typed);
        }
    }
}

int ui_text_input(const char *title, const char *prompt, char *buffer, int length)
{
    static const char *const extras[3] = {"(", ")", "."};

    return text_field(title, prompt, buffer, length, extras, 3);
}

int ui_bond_input(const char *title, const char *prompt, char *buffer, int length)
{
    static const char *const extras[3] = {"-", "=", "#"};

    return text_field(title, prompt, buffer, length, extras, 3);
}

int ui_equation_input(const char *title, const char *prompt, char *buffer, int length)
{
    static const char *const extras[4] = {"(", ")", "+", "->"};

    return text_field(title, prompt, buffer, length, extras, 4);
}

/* "a", "0.5" or "a/b" as a count: a finite number above zero, with b above
 * zero too. */
static int parse_count(const char *text, double *value)
{
    char *end;
    double top = strtod(text, &end), bottom = 1.0;

    if (end == text)
        return 0;
    if (*end == '/') {
        const char *rest = end + 1;
        bottom = strtod(rest, &end);
        if (end == rest || bottom <= 0.0)
            return 0;
    }
    if (*end != 0 || !isfinite(top / bottom) || top / bottom <= 0.0)
        return 0;
    *value = top / bottom;
    return 1;
}

/* The field behind ui_number_input and ui_count_input. With `typed` given it
 * is a count: the keypad's fraction and divide keys (and F1) type "/", and the
 * entry must be a number above zero; a bad one is explained and the field
 * starts again. */
static int number_field(const char *title, const char *prompt, double *value,
                        int allow_blank, char *typed)
{
    static const char *const keys[6] = {"", "", "", "", "", "OK"};
    static const char *const count_keys[6] = {"/", "", "", "", "", "OK"};
    const char *hint = "[EXP] powers of ten   [(-)] minus";
    char text[UI_TEXT_LEN];
    int used = 0;

    text[0] = 0;
    if (typed != NULL)
        hint = "[a b/c] or [F1] types /   [(-)] minus";
    else if (allow_blank)
        hint = "[EXE] alone = solve for this one";

    for (;;) {
        key_event_t event;
        char letter = 0;

        entry_screen(title, prompt, text, "123", typed ? count_keys : keys, hint, NULL);
        dupdate();

        event = getkey();
        switch (event.key) {
        case KEY_EXE:
        case KEY_F6:
            if (used == 0) {
                if (allow_blank)
                    return 1;
                continue;           /* a number is needed here */
            }
            {
                double parsed = 0.0;
                if (typed != NULL) {
                    if (!parse_count(text, &parsed)) {
                        ui_message(title, "Use a number above 0, e.g. 1/2");
                        used = 0;
                        text[0] = 0;
                        continue;
                    }
                    snprintf(typed, UI_TEXT_LEN, "%s", text);
                } else if (sscanf(text, "%lf", &parsed) != 1)
                    continue;
                *value = parsed;
            }
            return 1;
        case KEY_EXIT:
            return 0;
        case KEY_DEL:
            if (used > 0)
                text[--used] = 0;
            continue;
        case KEY_DOT:
            letter = '.';
            break;
        case KEY_NEG:
            /* (-) at the start makes it negative, later it starts an exponent */
            letter = '-';
            break;
        case KEY_EXP:
            letter = 'e';
            break;
        case KEY_FRAC:
        case KEY_DIV:
        case KEY_F1:
            if (typed != NULL)
                letter = '/';
            break;
        default:
            letter = digit_for_key(event.key);
            break;
        }
        if (letter != 0 && used < (int)sizeof text - 1) {
            text[used++] = letter;
            text[used] = 0;
        }
    }
}

int ui_number_input(const char *title, const char *prompt, double *value,
                    int allow_blank)
{
    return number_field(title, prompt, value, allow_blank, NULL);
}

int ui_count_input(const char *title, const char *prompt, double *value,
                   char *typed)
{
    return number_field(title, prompt, value, 0, typed);
}

/* ---- result pages ------------------------------------------------------- */

static char page_title[UI_LINE_LEN];
static char page[UI_MAX_LINES][UI_LINE_LEN];
static int page_used;
static int page_last_rule;      /* lines after this one are the answers */

void ui_result_begin(const char *title)
{
    snprintf(page_title, sizeof page_title, "%s", title);
    page_used = 0;
    page_last_rule = -1;
}

void ui_result_line(const char *text)
{
    if (page_used >= UI_MAX_LINES)
        return;
    snprintf(page[page_used], UI_LINE_LEN, "%s", text);
    page_used++;
}

void ui_result_text(const char *label, const char *text)
{
    char line[UI_LINE_LEN];
    snprintf(line, sizeof line, "%s %s", label, text);
    ui_result_line(line);
}

void ui_result_value(const char *label, double value, const char *unit)
{
    char number[24], line[UI_LINE_LEN];

    chem_format(value, 4, number, sizeof number);
    if (unit != NULL && unit[0] != 0)
        snprintf(line, sizeof line, "%s = %s %s", label, number, unit);
    else
        snprintf(line, sizeof line, "%s = %s", label, number);
    ui_result_line(line);
}

void ui_result_rule(void)
{
    ui_result_line("\x01");        /* drawn as a horizontal line */
    page_last_rule = page_used - 1;
}

void ui_result_show(void)
{
    int top = 0, rows = PAGE_ROWS - 1;      /* row 0 holds the heading */

    for (;;) {
        key_event_t event;
        int i;

        ui_frame("ChemCalc");
        bold(10, row_y(0, PAGE_ROW) + TEXT_DY(PAGE_ROW), C_BLUE, page_title);

        /* Everything after the last rule is the answer, so it is drawn bold. */
        for (i = 0; i < rows && top + i < page_used; i++) {
            int y = row_y(i + 1, PAGE_ROW);
            int answer = (page_last_rule >= 0 && top + i > page_last_rule);

            if (page[top + i][0] == '\x01')
                drect(10, y + PAGE_ROW / 2, ROW_RIGHT - 6, y + PAGE_ROW / 2, C_BLACK);
            else if (answer)
                bold(12, y + TEXT_DY(PAGE_ROW), C_BLACK, page[top + i]);
            else
                dtext(12, y + TEXT_DY(PAGE_ROW), C_BLACK, page[top + i]);
        }
        scroll_arrows(1, PAGE_ROW, top, rows, page_used);
        dupdate();

        event = getkey();
        if (event.key == KEY_EXIT || event.key == KEY_EXE || event.key == KEY_F6)
            return;
        if (event.key == KEY_DOWN && top + rows < page_used)
            top++;
        if (event.key == KEY_UP && top > 0)
            top--;
    }
}

void ui_message(const char *title, const char *message)
{
    int width, middle = DHEIGHT / 2, x1, x2, y1 = middle - 24, y2 = middle + 24;

    ui_frame(title);
    dsize(message, NULL, &width, NULL);
    x1 = DWIDTH / 2 - width / 2 - 20;
    x2 = DWIDTH / 2 + width / 2 + 20;
    /* the OS's pop-up frame, outside in: 1 px black, 1 white, 4 blue, 2 black */
    drect(x1, y1, x2, y2, C_BLACK);
    drect(x1 + 1, y1 + 1, x2 - 1, y2 - 1, C_WHITE);
    drect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, C_BLUE);
    drect(x1 + 6, y1 + 6, x2 - 6, y2 - 6, C_BLACK);
    drect(x1 + 8, y1 + 8, x2 - 8, y2 - 8, C_WHITE);
    dtext_opt(DWIDTH / 2, middle, C_BLACK, C_NONE, DTEXT_CENTER, DTEXT_MIDDLE,
              message, -1);
    dupdate();
    getkey();
}
