# Builds and runs the PC tests: no calculator toolchain needed.
#
#   make          both suites
#   make core     the chemistry only
#   make screens  the menus and screens, driven by scripted keypresses

# make's built-in default for CC is "cc", which is not always installed
ifeq ($(origin CC),default)
CC := gcc
endif
# -Wno-format-truncation: snprintf is used deliberately to cut text that will
# not fit the screen, and the compiler cannot tell that the element symbols
# inside a two-dimensional array are short.
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -Wno-format-truncation -O1 -g

CORE = ../src/core/chem.c ../src/core/elements.c ../src/core/stoich.c \
       ../src/core/solution.c ../src/core/balance.c ../src/core/energy.c

SCREENS = ../src/ui/ui.c ../src/screens/common.c ../src/screens/ptable.c \
          ../src/screens/stoich_screen.c ../src/screens/balance_screen.c \
          ../src/screens/gas_screen.c ../src/screens/aqua_screen.c \
          ../src/screens/energy_screen.c

all: core screens

test_core: test_core.c $(CORE) ../src/core/chem.h
	$(CC) $(CFLAGS) -o $@ test_core.c $(CORE) -lm

# The screens are built against the fake screen and keypad in test/stubs.
test_screens: test_screens.c fake_gint.c $(CORE) $(SCREENS)
	$(CC) $(CFLAGS) -I stubs -o $@ test_screens.c fake_gint.c $(CORE) $(SCREENS) -lm

core: test_core
	./test_core

screens: test_screens
	./test_screens

clean:
	rm -f test_core test_screens

.PHONY: all core screens clean
