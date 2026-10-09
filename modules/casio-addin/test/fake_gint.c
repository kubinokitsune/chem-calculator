/* fake_gint.c - the calculator's screen and keypad, faked for the PC tests.
 *
 * Text that the add-in draws is collected into one buffer, and getkey()
 * hands out keypresses that the test queued up. Together they let the tests
 * drive the real screens exactly as a student would, and then read what came
 * out - no calculator needed.
 */

#include "fake_gint.h"
#include <gint/gint.h>
#include <gint/rtc.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char captured[FAKE_CAPTURE_LEN];
static int captured_used;

static int queue[FAKE_KEY_QUEUE];
static int queue_used, queue_next;
static int keys_exhausted;

/* every text drawn: where it starts in `captured` and its colour */
#define MAX_TEXTS 4096
static int text_at[MAX_TEXTS], text_fg[MAX_TEXTS], texts;

/* how many rectangles of each colour */
#define MAX_COLOURS 64
static int rect_colour[MAX_COLOURS], rect_count[MAX_COLOURS], colours;
static int rect_last[MAX_COLOURS][4];

/* The fonts. The add-in's own two are 10 px wide on every glyph; gint's
 * default is proportional, and its widths are those of font8x9.png as fxconv
 * trims them (95 glyphs from the space, each followed by 1 px of spacing). */
struct font { int width; };
font_t font_body = { 10 }, font_bold = { 10 };
static font_t font_small = { 0 };
static const font_t *current_font = &font_small;
static const unsigned char small_width[95] = {
    5, 2, 6, 7, 8, 6, 8, 3, 4, 4, 8, 8, 3, 7, 2, 5, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 7, 2, 3, 5, 7, 5, 6, 8, 7, 7, 7, 7, 7, 7, 7, 7, 6, 7, 7, 7, 8, 7, 8,
    7, 8, 7, 7, 8, 7, 8, 8, 8, 8, 6, 4, 5, 4, 7, 7, 4, 7, 7, 7, 8, 8, 7, 7,
    7, 4, 6, 7, 4, 8, 7, 8, 7, 7, 8, 7, 8, 7, 8, 8, 7, 7, 6, 4, 2, 4, 7
};

/* the last column of the OS's area, and drawing past it */
#define LAST_COLUMN 389
static int overflows;
static char first_overflow[80];

static int centivolts_now, battery_type_now, os_reads;
static uint32_t ticks;

void fake_reset(void)
{
    texts = 0;
    colours = 0;
    fake_battery(600, 1);
    os_reads = 0;
    captured[0] = 0;
    captured_used = 0;
    queue_used = 0;
    queue_next = 0;
    keys_exhausted = 0;
}

void fake_press(int key)
{
    if (queue_used >= FAKE_KEY_QUEUE) {
        fprintf(stderr, "fake_gint: more than %d keys queued\n", FAKE_KEY_QUEUE);
        exit(2);
    }
    queue[queue_used++] = key;
}

static void type(const char *text, int bond)
{
    /* Type a formula: letters come from the keypad's alpha letters, digits
     * from the number keys, with ALPHA switching between the two. F1-F3 are
     * ( ) . in a formula field and - = # in a bond field; in the equation
     * field they are ( ) + and ->. */
    static const int letters[26] = {
        KEY_XOT, KEY_LOG, KEY_LN, KEY_SIN, KEY_COS, KEY_TAN,
        KEY_FRAC, KEY_FD, KEY_LEFTP, KEY_RIGHTP, KEY_COMMA, KEY_ARROW,
        KEY_7, KEY_8, KEY_9,
        KEY_4, KEY_5, KEY_6, KEY_MUL, KEY_DIV,
        KEY_1, KEY_2, KEY_3, KEY_ADD, KEY_SUB,
        KEY_0
    };
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    int alpha = 1;      /* text fields start in letters mode */
    int small = 0;
    int i;

    for (i = 0; text[i]; i++) {
        char c = text[i];

        if (c >= 'A' && c <= 'Z') {
            if (!alpha) { fake_press(KEY_ALPHA); alpha = 1; }
            if (small) { fake_press(KEY_SHIFT); small = 0; }
            fake_press(letters[c - 'A']);
        } else if (c >= 'a' && c <= 'z') {
            if (!alpha) { fake_press(KEY_ALPHA); alpha = 1; }
            if (!small) { fake_press(KEY_SHIFT); small = 1; }
            fake_press(letters[c - 'a']);
        } else if (c >= '0' && c <= '9') {
            if (alpha) { fake_press(KEY_ALPHA); alpha = 0; }
            fake_press(digits[c - '0']);
        } else if (c == '+') {                  /* equation field */
            fake_press(KEY_F3);
        } else if (c == '>' || (c == '-' && text[i + 1] == '>')) {
            if (c == '-')
                i++;                            /* "->" is one key, F4 */
            fake_press(KEY_F4);
        } else if (c == '-') {
            /* the keypad's minus key; it only means minus in digit mode */
            if (alpha) { fake_press(KEY_ALPHA); alpha = 0; }
            fake_press(KEY_SUB);
        } else if (c == '(') {
            fake_press(KEY_F1);
        } else if (c == ')' || (bond && c == '=')) {
            fake_press(KEY_F2);
        } else if (c == '.' || (bond && c == '#')) {
            fake_press(KEY_F3);
        } else {
            fprintf(stderr, "fake_press_text: cannot type '%c'\n", c);
            exit(2);
        }
    }
}

void fake_press_text(const char *text)
{
    type(text, 0);
}

void fake_press_bond(const char *text)
{
    type(text, 1);
}

void fake_press_number(const char *text)
{
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    int i;

    for (i = 0; text[i]; i++) {
        char c = text[i];

        if (c >= '0' && c <= '9')
            fake_press(digits[c - '0']);
        else if (c == '.')
            fake_press(KEY_DOT);
        else if (c == '-')
            fake_press(KEY_NEG);
        else if (c == '/')
            fake_press(KEY_FRAC);       /* the [a b/c] key */
        else if (c == 'e' || c == 'E')
            fake_press(KEY_EXP);
    }
    fake_press(KEY_EXE);
}

const char *fake_screen(void)
{
    return captured;
}

int fake_keys_left(void)
{
    return queue_used - queue_next;
}

int fake_ran_out_of_keys(void)
{
    return keys_exhausted;
}

int fake_screen_has(const char *text)
{
    return strstr(captured, text) != NULL;
}

/* ---- the drawing calls the add-in makes --------------------------------- */

static int text_width(const char *text, const font_t *font)
{
    int width = 0;

    if (font == NULL)
        font = current_font;
    if (font->width != 0)
        return font->width * (int)strlen(text);
    for (; *text; text++)
        width += small_width[(*text >= 32 && *text < 127) ? *text - 32 : 0] + 1;
    return width > 0 ? width - 1 : 0;
}

static void overflow(const char *what)
{
    if (overflows++ == 0)
        snprintf(first_overflow, sizeof first_overflow, "%s", what);
}

/* `text` drawn with its left edge at x (halign 0), centred on it (1) or
 * ending at it (2) must stay inside the OS's area. */
static void check_text(int x, int halign, const char *text)
{
    int width = text_width(text, NULL);

    if (halign == 1)
        x -= width / 2;
    else if (halign == 2)
        x -= width;
    if (x < 0 || x + width - 1 > LAST_COLUMN)
        overflow(text);
}

int fake_overflows(void)
{
    return overflows;
}

const char *fake_first_overflow(void)
{
    return first_overflow;
}

const font_t *dfont(const font_t *font)
{
    const font_t *old = current_font;

    current_font = (font != NULL) ? font : &font_small;
    return old;
}

static void capture(const char *text, int fg)
{
    int length = (int)strlen(text);

    if (captured_used + length + 2 >= FAKE_CAPTURE_LEN) {
        /* dropping text would let a "did not show" check pass for nothing */
        fprintf(stderr, "fake_gint: more than %d characters drawn\n", FAKE_CAPTURE_LEN);
        exit(2);
    }
    if (texts >= MAX_TEXTS) {
        fprintf(stderr, "fake_gint: more than %d texts drawn\n", MAX_TEXTS);
        exit(2);
    }
    text_at[texts] = captured_used;
    text_fg[texts++] = fg;
    memcpy(captured + captured_used, text, (size_t)length);
    captured_used += length;
    captured[captured_used++] = '\n';
    captured[captured_used] = 0;
}

void dclear(int colour)
{
    (void)colour;
}

void drect(int x1, int y1, int x2, int y2, int colour)
{
    int i;

    if (x2 > LAST_COLUMN)
        overflow("a rectangle");
    for (i = 0; i < colours && rect_colour[i] != colour; i++)
        ;
    if (i == colours) {
        if (colours >= MAX_COLOURS) {
            fprintf(stderr, "fake_gint: more than %d colours drawn\n", MAX_COLOURS);
            exit(2);
        }
        rect_colour[colours++] = colour;
        rect_count[i] = 0;
    }
    rect_count[i]++;
    rect_last[i][0] = x1;
    rect_last[i][1] = y1;
    rect_last[i][2] = x2;
    rect_last[i][3] = y2;
}

int fake_last_rect(int colour, int *x1, int *y1, int *x2, int *y2)
{
    int i;

    for (i = 0; i < colours; i++)
        if (rect_colour[i] == colour) {
            *x1 = rect_last[i][0];
            *y1 = rect_last[i][1];
            *x2 = rect_last[i][2];
            *y2 = rect_last[i][3];
            return 1;
        }
    return 0;
}

int fake_rects(int colour)
{
    int i;

    for (i = 0; i < colours; i++)
        if (rect_colour[i] == colour)
            return rect_count[i];
    return 0;
}

int fake_text_colour(const char *text)
{
    int i, length = (int)strlen(text);

    for (i = texts - 1; i >= 0; i--)
        if (strncmp(captured + text_at[i], text, (size_t)length) == 0
            && captured[text_at[i] + length] == '\n')
            return text_fg[i];
    return -2;
}

void dtext(int x, int y, int fg, const char *text)
{
    (void)y;
    check_text(x, 0, text);
    capture(text, fg);
}

void dtext_opt(int x, int y, int fg, int bg, int halign, int valign,
               const char *text, int size)
{
    (void)y; (void)bg; (void)valign; (void)size;
    check_text(x, halign, text);
    capture(text, fg);
}

void dsize(const char *text, const font_t *font, int *width, int *height)
{
    if (font == NULL)
        font = current_font;
    if (width != NULL)
        *width = text_width(text, font);
    if (height != NULL)
        *height = (font == &font_small) ? 9 : 20;
}

void dupdate(void)
{
}

key_event_t getkey(void)
{
    key_event_t event;

    event.type = 1;
    event.shift = 0;
    event.alpha = 0;
    if (queue_next >= queue_used) {
        /* The screen asked for more input than the test provided. Rather than
         * spinning for ever, say EXIT and record that it happened. */
        keys_exhausted++;
        event.key = KEY_EXIT;
        if (keys_exhausted > 200) {
            fprintf(stderr, "fake_gint: a screen will not stop asking for keys\n");
            exit(2);
        }
        return event;
    }
    event.key = queue[queue_next++];
    return event;
}

/* ---- the OS: battery and clock ------------------------------------------ */

void fake_battery(int centivolts, int type)
{
    centivolts_now = centivolts;
    battery_type_now = type;
    fake_advance(60);
}

void fake_advance(int seconds)
{
    ticks += 128u * (uint32_t)seconds;
}

int fake_os_reads(void)
{
    return os_reads;
}

uint32_t rtc_ticks(void)
{
    return ticks;
}

int gint_world_switch(gint_call_t call)
{
    return call.function(call.arg);
}

/* The two syscalls battery.c uses, answering by their numbers on WikiPrizm. */
int fake_os_syscall(int number, int arg)
{
    switch (number) {
    case 0x1186:                        /* GetMainBatteryVoltage(1) */
        if (arg != 1) {
            fprintf(stderr, "fake_gint: GetMainBatteryVoltage wants 1, got %d\n", arg);
            exit(2);
        }
        os_reads++;
        return centivolts_now;
    case 0x12D5:                        /* GetBatteryType() */
        return battery_type_now;
    default:
        fprintf(stderr, "fake_gint: unexpected syscall 0x%x\n", number);
        exit(2);
    }
}
