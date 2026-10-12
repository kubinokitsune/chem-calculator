/* battery.h - the OS's own battery icon, borrowed for the status strip. */
#ifndef BATTERY_H
#define BATTERY_H

/* Draws the battery icon at the strip's left, exactly as the OS's status bar
 * shows it, and returns 1; returns 0, drawing nothing, if the OS drew none.
 * It asks the OS at most every 30 seconds and reuses the picture in between. */
int battery_draw(void);

#endif
