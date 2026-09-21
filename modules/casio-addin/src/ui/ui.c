/* ui.c - see ui.h. This is the only file that talks to the screen and keypad. */

#include "ui.h"
#include "../core/chem.h"

#include <gint/display.h>
#include <gint/keyboard.h>

#include <stdio.h>
#include <string.h>

/* The fx-CG50 screen is 396 x 224. gint's default font is 8 px wide and
 * 9 px tall, so a line is 11 px with a little air. */
#define ROW_HEIGHT   13
#define TITLE_HEIGHT 20
#define FOOT_HEIGHT  18
#define BODY_TOP     (TITLE_HEIGHT + 4)
#define BODY_BOTTOM  (DHEIGHT - FOOT_HEIGHT - 2)
#define BODY_ROWS    ((BODY_BOTTOM - BODY_TOP) / ROW_HEIGHT)

#define COLOUR_TITLE  C_RGB(4, 10, 20)
#define COLOUR_FOOT   C_RGB(24, 24, 26)
#define COLOUR_PICK   C_RGB(18, 26, 31)
#define COLOUR_RULE   C_RGB(20, 20, 22)

void ui_frame(const char *title)
{
    dclear(C_WHITE);
    drect(0, 0, DWIDTH - 1, TITLE_HEIGHT - 1, COLOUR_TITLE);
    dtext_opt(6, TITLE_HEIGHT / 2, C_WHITE, C_NONE, DTEXT_LEFT, DTEXT_MIDDLE,
              title, -1);
}

void ui_softkeys(const char *const *labels)
{
    int i, width = DWIDTH / 6;

    drect(0, DHEIGHT - FOOT_HEIGHT, DWIDTH - 1, DHEIGHT - 1, COLOUR_FOOT);
    for (i = 0; i < 6; i++) {
        int x = i * width;
        if (i > 0)
            drect(x, DHEIGHT - FOOT_HEIGHT, x, DHEIGHT - 1, C_WHITE);
        if (labels != NULL && labels[i] != NULL && labels[i][0] != 0) {
            dtext_opt(x + width / 2, DHEIGHT - FOOT_HEIGHT / 2, C_WHITE, C_NONE,
                      DTEXT_CENTER, DTEXT_MIDDLE, labels[i], -1);
        }
    }
}

/* ---- menus -------------------------------------------------------------- */

int ui_menu(const char *title, const char *const *items, int count, int *cursor)
{
    static const char *const keys[6] = {"", "", "", "", "", "BACK"};
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
            int y = BODY_TOP + i * ROW_HEIGHT;
            int picked = (top + i == here);
            char label[UI_LINE_LEN + 8];

            if (picked)
                drect(2, y - 1, DWIDTH - 3, y + ROW_HEIGHT - 2, COLOUR_PICK);
            snprintf(label, sizeof label, "%d %s", top + i + 1, items[top + i]);
            dtext(8, y, picked ? C_WHITE : C_BLACK, label);
        }
        if (count > BODY_ROWS) {
            char position[16];
            snprintf(position, sizeof position, "%d/%d", here + 1, count);
            dtext_opt(DWIDTH - 6, TITLE_HEIGHT / 2, C_WHITE, C_NONE,
                      DTEXT_RIGHT, DTEXT_MIDDLE, position, -1);
        }
        ui_softkeys(keys);
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

/* Draw the shared parts of an entry screen. */
static void entry_screen(const char *title, const char *prompt,
                         const char *text, const char *mode,
                         const char *const *keys)
{
    int caret;

    ui_frame(title);
    dtext(8, BODY_TOP, C_BLACK, prompt);

    drect(8, BODY_TOP + ROW_HEIGHT + 4, DWIDTH - 9, BODY_TOP + ROW_HEIGHT + 26,
          C_RGB(29, 29, 31));
    dtext(14, BODY_TOP + ROW_HEIGHT + 11, C_BLACK, text);

    dsize(text, NULL, &caret, NULL);
    drect(14 + caret, BODY_TOP + ROW_HEIGHT + 10, 15 + caret,
          BODY_TOP + ROW_HEIGHT + 20, C_BLACK);

    if (mode != NULL)
        dtext_opt(DWIDTH - 6, TITLE_HEIGHT / 2, C_WHITE, C_NONE,
                  DTEXT_RIGHT, DTEXT_MIDDLE, mode, -1);
    ui_softkeys(keys);
}

int ui_text_input(const char *title, const char *prompt, char *buffer, int length)
{
    const char *keys[6];
    int alpha = 1, small = 0;
    int used = (int)strlen(buffer);

    for (;;) {
        key_event_t event;
        char letter = 0;

        /* The softkeys say what the keypad cannot: brackets, the hydrate dot,
         * and how to get small letters or digits into a field of letters. */
        keys[0] = "(";
        keys[1] = ")";
        keys[2] = ".";
        keys[3] = small ? "ABC" : "abc";
        keys[4] = alpha ? "123" : "ABC";
        keys[5] = "OK";

        entry_screen(title, prompt, buffer, alpha ? (small ? "abc" : "ABC") : "123",
                     keys);
        dupdate();

        event = getkey();
        switch (event.key) {
        case KEY_EXE:
            return 1;
        case KEY_EXIT:
            return 0;
        case KEY_DEL:
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
            letter = '(';
            break;
        case KEY_F2:
            letter = ')';
            break;
        case KEY_F3:
            letter = '.';
            break;
        case KEY_F4:
            small = !small;
            continue;
        case KEY_F5:
            alpha = !alpha;
            continue;
        case KEY_F6:
            return 1;
        default:
            if (alpha) {
                letter = letter_for_key(event.key);
                if (letter != 0 && small)
                    letter = (char)(letter - 'A' + 'a');
                if (letter == 0)
                    letter = digit_for_key(event.key);
            } else {
                letter = digit_for_key(event.key);
                if (letter == 0)
                    letter = letter_for_key(event.key);
            }
            break;
        }
        if (letter != 0 && used < length - 1) {
            buffer[used++] = letter;
            buffer[used] = 0;
        }
    }
}

int ui_number_input(const char *title, const char *prompt, double *value,
                    int allow_blank)
{
    static const char *const keys[6] = {"", "", "", "", "", "OK"};
    char text[24];
    int used = 0;

    text[0] = 0;

    for (;;) {
        key_event_t event;
        char letter = 0;

        entry_screen(title, prompt, text, "123", keys);
        if (allow_blank)
            dtext(8, BODY_BOTTOM - ROW_HEIGHT, C_RGB(12, 12, 14),
                  "[EXE] alone = solve for this");
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
                if (sscanf(text, "%lf", &parsed) != 1)
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

/* ---- result pages ------------------------------------------------------- */

static char page_title[UI_LINE_LEN];
static char page[UI_MAX_LINES][UI_LINE_LEN];
static int page_used;

void ui_result_begin(const char *title)
{
    snprintf(page_title, sizeof page_title, "%s", title);
    page_used = 0;
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
}

void ui_result_show(void)
{
    static const char *const keys[6] = {"", "", "", "", "", "BACK"};
    int top = 0;

    for (;;) {
        key_event_t event;
        int i;

        ui_frame(page_title);
        for (i = 0; i < BODY_ROWS && top + i < page_used; i++) {
            int y = BODY_TOP + i * ROW_HEIGHT;
            if (page[top + i][0] == '\x01')
                drect(8, y + ROW_HEIGHT / 2, DWIDTH - 9, y + ROW_HEIGHT / 2,
                      COLOUR_RULE);
            else
                dtext(8, y, C_BLACK, page[top + i]);
        }
        if (page_used > BODY_ROWS) {
            dtext_opt(DWIDTH - 6, TITLE_HEIGHT / 2, C_WHITE, C_NONE,
                      DTEXT_RIGHT, DTEXT_MIDDLE, "v", -1);
        }
        ui_softkeys(keys);
        dupdate();

        event = getkey();
        if (event.key == KEY_EXIT || event.key == KEY_EXE || event.key == KEY_F6)
            return;
        if (event.key == KEY_DOWN && top + BODY_ROWS < page_used)
            top++;
        if (event.key == KEY_UP && top > 0)
            top--;
    }
}

void ui_message(const char *title, const char *message)
{
    static const char *const keys[6] = {"", "", "", "", "", "BACK"};

    ui_frame(title);
    dtext_opt(DWIDTH / 2, DHEIGHT / 2, C_BLACK, C_NONE, DTEXT_CENTER,
              DTEXT_MIDDLE, message, -1);
    ui_softkeys(keys);
    dupdate();
    getkey();
}
