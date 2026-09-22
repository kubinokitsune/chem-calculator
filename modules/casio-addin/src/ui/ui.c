/* ui.c - see ui.h. This is the only file that talks to the screen and keypad. */

#include "ui.h"
#include "../core/chem.h"

#include <gint/display.h>
#include <gint/keyboard.h>

#include <stdio.h>
#include <string.h>

/* The fx-CG50 screen is 396 x 224 and gint's font is 8 x 9, so a row of text
 * needs about 15 px to sit comfortably. */
#define ROW_HEIGHT   15
#define TITLE_HEIGHT 26
#define FOOT_HEIGHT  22
#define BODY_TOP     (TITLE_HEIGHT + 6)
#define BODY_BOTTOM  (DHEIGHT - FOOT_HEIGHT - 4)
#define BODY_ROWS    ((BODY_BOTTOM - BODY_TOP) / ROW_HEIGHT)
#define SCROLL_X     (DWIDTH - 8)

/* Colours are 5-6-5: C_RGB takes 0-31 for each. */
#define COL_BAR       C_RGB(3, 9, 18)      /* the deep blue title bar */
#define COL_BAR_EDGE  C_RGB(8, 20, 30)     /* the lighter line under it */
#define COL_ACCENT    C_RGB(0, 24, 20)     /* teal, for the accent line */
#define COL_TEXT      C_RGB(3, 3, 6)
#define COL_MUTED     C_RGB(14, 14, 17)
#define COL_STRIPE    C_RGB(30, 30, 31)    /* every other row */
#define COL_PICK      C_RGB(5, 16, 28)     /* the selected row */
#define COL_PANEL     C_RGB(26, 30, 31)    /* the answer panel */
#define COL_PANEL_EDGE C_RGB(16, 24, 29)
#define COL_FIELD     C_RGB(29, 29, 31)
#define COL_KEY       C_RGB(6, 6, 9)       /* the softkey tabs */
#define COL_RULE      C_RGB(20, 20, 23)

/* ---- small drawing helpers ---------------------------------------------- */

/* Text drawn twice, a pixel apart, reads as bold with only one font. */
static void bold(int x, int y, int colour, const char *text)
{
    dtext(x, y, colour, text);
    dtext(x + 1, y, colour, text);
}

/* A filled box with its corners knocked off, which reads as rounded. */
static void panel(int x1, int y1, int x2, int y2, int fill, int edge)
{
    drect(x1, y1, x2, y2, fill);
    if (edge >= 0) {
        drect(x1, y1, x2, y1, edge);
        drect(x1, y2, x2, y2, edge);
        drect(x1, y1, x1, y2, edge);
        drect(x2, y1, x2, y2, edge);
    }
}

static void scrollbar(int first, int shown, int total)
{
    int track_top = BODY_TOP, track_bottom = BODY_BOTTOM;
    int height = track_bottom - track_top;
    int bar_top, bar_height;

    if (total <= shown)
        return;
    bar_height = height * shown / total;
    if (bar_height < 12)
        bar_height = 12;
    bar_top = track_top + (height - bar_height) * first / (total - shown);

    drect(SCROLL_X, track_top, SCROLL_X + 3, track_bottom, C_RGB(28, 28, 30));
    panel(SCROLL_X, bar_top, SCROLL_X + 3, bar_top + bar_height, COL_BAR_EDGE, -1);
}

void ui_frame(const char *title)
{
    dclear(C_WHITE);
    drect(0, 0, DWIDTH - 1, TITLE_HEIGHT - 3, COL_BAR);
    drect(0, TITLE_HEIGHT - 2, DWIDTH - 1, TITLE_HEIGHT - 2, COL_BAR_EDGE);
    drect(0, TITLE_HEIGHT - 1, DWIDTH - 1, TITLE_HEIGHT - 1, COL_ACCENT);
    bold(8, TITLE_HEIGHT / 2 - 5, C_WHITE, title);
}

/* A short note on the right of the title bar: a position, a mode, an arrow. */
static void ui_badge(const char *text)
{
    int width;

    if (text == NULL || text[0] == 0)
        return;
    dsize(text, NULL, &width, NULL);
    panel(DWIDTH - width - 14, 4, DWIDTH - 6, TITLE_HEIGHT - 6, COL_BAR_EDGE, -1);
    dtext(DWIDTH - width - 10, TITLE_HEIGHT / 2 - 5, C_WHITE, text);
}

void ui_softkeys(const char *const *labels)
{
    int i, width = DWIDTH / 6;

    drect(0, DHEIGHT - FOOT_HEIGHT, DWIDTH - 1, DHEIGHT - 1, C_WHITE);
    for (i = 0; i < 6; i++) {
        int x = i * width + 2;
        int right = x + width - 5;

        if (labels == NULL || labels[i] == NULL || labels[i][0] == 0)
            continue;
        panel(x, DHEIGHT - FOOT_HEIGHT + 2, right, DHEIGHT - 3, COL_KEY, -1);
        dtext_opt((x + right) / 2, DHEIGHT - FOOT_HEIGHT / 2, C_WHITE, C_NONE,
                  DTEXT_CENTER, DTEXT_MIDDLE, labels[i], -1);
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
            char number[8];

            if (picked)
                panel(4, y - 2, SCROLL_X - 4, y + ROW_HEIGHT - 4, COL_PICK, -1);
            else if ((top + i) & 1)
                drect(4, y - 2, SCROLL_X - 4, y + ROW_HEIGHT - 4, COL_STRIPE);

            snprintf(number, sizeof number, "%d", top + i + 1);
            dtext(10, y, picked ? C_WHITE : COL_MUTED, number);
            if (picked) {
                bold(26, y, C_WHITE, items[top + i]);
                dtext(SCROLL_X - 16, y, C_WHITE, ">");
            } else {
                dtext(26, y, COL_TEXT, items[top + i]);
            }
        }
        if (count > BODY_ROWS) {
            char position[16];
            snprintf(position, sizeof position, "%d/%d", here + 1, count);
            ui_badge(position);
            scrollbar(top, BODY_ROWS, count);
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
                         const char *const *keys, const char *hint)
{
    int caret, box_top = BODY_TOP + ROW_HEIGHT + 2;

    ui_frame(title);
    ui_badge(mode);
    dtext(10, BODY_TOP, COL_MUTED, prompt);

    panel(8, box_top, DWIDTH - 9, box_top + 26, COL_FIELD, COL_PANEL_EDGE);
    bold(16, box_top + 9, COL_TEXT, text);

    dsize(text, NULL, &caret, NULL);
    drect(17 + caret, box_top + 7, 18 + caret, box_top + 19, COL_BAR_EDGE);

    if (hint != NULL)
        dtext(10, box_top + 36, COL_MUTED, hint);
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
                     keys, "[DEL] rub out   [EXE] accept   [EXIT] back");
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

        entry_screen(title, prompt, text, "123", keys,
                     allow_blank ? "[EXE] alone = solve for this one"
                                 : "[EXP] powers of ten   [(-)] minus");
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
    static const char *const keys[6] = {"", "", "", "", "", "BACK"};
    int top = 0;

    for (;;) {
        key_event_t event;
        int i;

        ui_frame(page_title);

        /* Everything after the last rule is the answer, so it gets a panel of
         * its own and heavier text: that is what the eye should land on. */
        if (page_last_rule >= 0 && page_last_rule >= top
            && page_last_rule < top + BODY_ROWS) {
            int first = page_last_rule + 1 - top;
            int last = page_used - 1 - top;

            if (last >= BODY_ROWS)
                last = BODY_ROWS - 1;
            if (last >= first)
                panel(6, BODY_TOP + first * ROW_HEIGHT - 3, SCROLL_X - 4,
                      BODY_TOP + (last + 1) * ROW_HEIGHT - 4,
                      COL_PANEL, COL_PANEL_EDGE);
        }

        for (i = 0; i < BODY_ROWS && top + i < page_used; i++) {
            int y = BODY_TOP + i * ROW_HEIGHT;
            int answer = (page_last_rule >= 0 && top + i > page_last_rule);

            if (page[top + i][0] == '\x01')
                drect(10, y + ROW_HEIGHT / 2 - 2, SCROLL_X - 8,
                      y + ROW_HEIGHT / 2 - 2, COL_RULE);
            else if (answer)
                bold(12, y, COL_TEXT, page[top + i]);
            else
                dtext(12, y, COL_TEXT, page[top + i]);
        }
        if (page_used > BODY_ROWS) {
            char position[16];
            snprintf(position, sizeof position, "%d/%d",
                     top + 1, page_used - BODY_ROWS + 1);
            ui_badge(position);
            scrollbar(top, BODY_ROWS, page_used);
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
    int width, middle = DHEIGHT / 2;

    ui_frame(title);
    dsize(message, NULL, &width, NULL);
    panel(DWIDTH / 2 - width / 2 - 14, middle - 18, DWIDTH / 2 + width / 2 + 14,
          middle + 18, COL_PANEL, COL_PANEL_EDGE);
    dtext_opt(DWIDTH / 2, middle, COL_TEXT, C_NONE, DTEXT_CENTER, DTEXT_MIDDLE,
              message, -1);
    ui_softkeys(keys);
    dupdate();
    getkey();
}
