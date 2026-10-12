/* battery.h - the main battery's charge, read from the OS. */
#ifndef BATTERY_H
#define BATTERY_H

/* Bars (0 to 3) for a reading of `centivolts` from 4 AAA cells. `type` is the
 * OS's battery-type setting: 2 is Ni-MH, anything else alkaline. */
int battery_bars(int centivolts, int type);

/* The bars to show now, 0 to 3, or -1 when the OS gives no reading. It asks the
 * OS at most every 30 seconds and reuses the answer in between. */
int battery_level(void);

#endif
