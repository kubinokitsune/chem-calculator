"""
Browser click-through tests for the web UI (CHEMCALC FX-17).

Runs the real Flask app in a background thread and drives a real Chromium
browser: clicking module buttons, choosing options, pressing "Try example",
pressing Calculate (and Enter), and reading the output screen — the same
things a student does.

Needs Playwright:
    py -m pip install playwright
    py -m playwright install chromium

Run:  py test_files/test_ui.py
"""

import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ui_interface"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is not installed — skipping the browser tests.\n"
          "  py -m pip install playwright\n"
          "  py -m playwright install chromium")
    sys.exit(0)

import app as webapp
from werkzeug.serving import make_server

PASS = FAIL = 0
FAILURES = []


def record(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {label}" + (f"\n         {detail}" if detail else "")
        FAILURES.append(msg)
        print(msg)


def section(t):
    print(f"\n=== {t} ===")


class Server:
    """The real Flask app on a free port, in a background thread."""

    def __enter__(self):
        self.srv = make_server("127.0.0.1", 0, webapp.app, threaded=True)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()


class Page:
    """Small wrapper around the page: click a module, fill an example, calculate."""

    def __init__(self, page):
        self.page = page
        self.errors = []
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        # A rejected request (HTTP 400 from a deliberate bad input) is logged as a
        # console error by the browser — that is the API working, not a page bug.
        page.on("console", lambda m: self.errors.append(f"console {m.type}: {m.text}")
                if m.type == "error" and "Failed to load resource" not in m.text else None)

    def open_module(self, name):
        self.page.click(f".mod-btn:text-is('{name}')")
        self.page.wait_for_timeout(60)

    def choose(self, select_id, value):
        self.page.select_option(f"#{select_id}", value)
        self.page.wait_for_timeout(60)

    def example(self):
        self.page.click("#exampleBtn")
        self.page.wait_for_timeout(120)

    def calculate(self, with_enter=False):
        if with_enter:
            box = self.page.query_selector("#panelBody input:not([type=checkbox])")
            box.click()
            box.press("Enter")
        else:
            self.page.click(".calc-btn")
        self.page.wait_for_timeout(450)

    @property
    def out(self):
        return self.page.inner_text("#screenOut")

    @property
    def is_error(self):
        return "error" in (self.page.get_attribute("#screenOut", "class") or "")

    def set_sf(self, value):
        self.page.select_option("#sfSelect", value)
        self.page.wait_for_timeout(80)


MODULES = ["Mole Conv.", "Empirical Formula", "Lim. Reactant", "% Comp.", "Atom Economy", "% Yield",
           "Oxidation #", "Ionic Bond", "Periodic Table", "Thermodynamics", "Kinetics", "ICE Solver",
           "Acid-Base", "Electrochemistry", "Eqn Balancer", "Vol/Mass", "Gas Laws"]
TYPE_SELECTS = ["moleType", "volType", "yieldType", "gasType", "abType", "thermoType",
                "iceType", "ecType", "kinType"]


def main():
    with Server() as server, sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        raw = context.new_page()
        p = Page(raw)
        raw.goto(server.url)
        raw.wait_for_selector(".calc-btn")
        raw.evaluate("localStorage.clear()")
        raw.reload()
        raw.wait_for_selector(".calc-btn")

        section("Page loads")
        record("title is the calculator", raw.title() == "Chemistry Calculator")
        record("stylesheet and script are separate files",
               raw.eval_on_selector_all("link[rel=stylesheet], script[src]", "els => els.length") == 2)
        record("17 module buttons", raw.eval_on_selector_all(".mod-btn", "els => els.length") == 17)
        record("no JavaScript errors on load", not p.errors, "; ".join(p.errors))

        section("Every module and option: example → calculate")
        for name in MODULES:
            p.open_module(name)
            sel_id = next((s for s in TYPE_SELECTS if raw.query_selector(f"#{s}")), None)
            options = (raw.eval_on_selector(f"#{sel_id}", "el => [...el.options].map(o => o.value)")
                       if sel_id else [None])
            for value in options:
                if value is not None:
                    p.choose(sel_id, value)
                if name == "Ionic Bond":
                    pass
                p.example()
                ready = "ready" in (raw.get_attribute(".calc-btn", "class") or "")
                p.calculate()
                label = f"{name}" + (f" · {value}" if value else "")
                record(f"{label}: example calculates",
                       ready and not p.is_error and len(p.out) > 10,
                       f"ready={ready} out={p.out[:90]!r}")
            if name == "Ionic Bond":   # radio buttons, not a select
                for action in ("classify", "formula"):
                    raw.check(f"input[name=ionicAction][value={action}]")
                    raw.wait_for_timeout(60)
                    p.example()
                    p.calculate()
                    record(f"Ionic Bond · {action}: example calculates", not p.is_error, p.out[:90])

        section("Answers, rounding and copying")
        p.open_module("Gas Laws")
        p.choose("gasType", "ideal")
        p.example()
        p.calculate()
        record("gas law in kPa/cm³/°C", "99.15 kPa" in p.out, p.out[-60:])
        p.set_sf("3")
        record("3 s.f. line added in Detail mode", "Answer to 3 s.f.: P = 99.2 kPa" in p.out, p.out[-60:])
        raw.click("#outputModeBtn")
        raw.wait_for_timeout(100)
        record("Compact mode shows the rounded answer", p.out.strip() == "P = 99.2 kPa", p.out)
        p.set_sf("auto")
        record("Auto shows 4 s.f.", p.out.strip() == "P = 99.15 kPa", p.out)
        raw.click("#outputModeBtn")
        raw.wait_for_timeout(100)

        raw.click("#copyBtn")
        raw.wait_for_timeout(300)
        clip = raw.evaluate("navigator.clipboard.readText()")
        record("Copy puts the answer on the clipboard", "99.15" in clip, clip[:80])

        section("Enter calculates")
        p.open_module("% Comp.")
        p.example()
        p.calculate(with_enter=True)
        record("Enter runs the calculation", "249.7" in p.out or "CuSO4" in p.out, p.out[:90])

        section("Errors are shown, not crashes")
        p.open_module("% Comp.")
        raw.fill("#pctFormula", "Ca(OH")
        p.calculate()
        record("bad formula shows an error", p.is_error and "ERROR" in p.out, p.out[:90])
        record("still no JavaScript errors", not p.errors, "; ".join(p.errors))

        section("Limiting reactant → % Yield")
        p.open_module("Lim. Reactant")
        p.example()
        p.calculate()
        record("limiting reactant is O2", "O2" in p.out, p.out[:90])
        raw.click("#chainBar button")
        raw.wait_for_timeout(150)
        record("% Yield opened with the theoretical yield filled in",
               raw.input_value("#yB").startswith("18.0"), raw.input_value("#yB"))
        raw.fill("#yA", "15.3")
        p.calculate()
        record("% yield calculated from the chained value", "84.9" in p.out, p.out[-60:])

        section("Recent calculations")
        count = raw.inner_text("#historyBtn")
        record("history counts the calculations", "(" in count, count)
        raw.click("#historyBtn")
        raw.wait_for_timeout(120)
        record("history panel opens", raw.is_visible("#historyPanel"))
        raw.click(".history-item >> nth=1")
        raw.wait_for_timeout(150)
        record("clicking an entry shows that result again",
               "saved result" in raw.inner_text("#screenPrompt"), raw.inner_text("#screenPrompt"))
        raw.click("#historyPanel button.mini-btn")   # Clear
        raw.wait_for_timeout(120)
        record("history clears", "No calculations yet." in raw.inner_text("#historyList"))

        section("Theme and accent")
        raw.click("#themeBtn")
        raw.wait_for_timeout(120)
        record("theme switches to light", raw.get_attribute("html", "data-theme") == "light")
        raw.click(".accent-dot >> nth=2")
        raw.wait_for_timeout(120)
        record("accent colour applies",
               raw.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()") == "#10b981")
        raw.reload()
        raw.wait_for_selector(".calc-btn")
        record("preferences survive a reload", raw.get_attribute("html", "data-theme") == "light")

        record("no JavaScript errors in the whole run", not p.errors, "; ".join(p.errors))
        context.close()
        browser.close()

    print("\n" + "=" * 60)
    print(f"  UI tests  Total: {PASS + FAIL}   Passed: {PASS}   Failed: {FAIL}")
    if FAILURES:
        print("\nFailures:")
        print("\n".join(FAILURES))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
