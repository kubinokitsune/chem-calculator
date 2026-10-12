/* A stand-in for gint's gint.h, used only by the PC tests: the "OS world" is
 * the same world here, so a world switch just makes the call. */
#ifndef STUB_GINT_GINT_H
#define STUB_GINT_GINT_H

typedef struct {
    int (*function)(int);
    int arg;
} gint_call_t;

#define GINT_CALL(func, arg) ((gint_call_t){ (func), (arg) })

int gint_world_switch(gint_call_t call);

#endif
