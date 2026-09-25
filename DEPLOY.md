# Deploying the web UI

The browser UI is a Flask app with a Python backend (`/api/*` routes do the
chemistry), so it needs a Python host — **GitHub Pages cannot run it.**

## Why not self-host it at home

It's tempting to expose it from a home server through a tunnel. Don't: a public
web app on a home LAN means any bug in the app is a foothold on the network the
rest of your machines live on. A hosted platform isolates it — worst case you
redeploy, and nothing of yours was ever reachable.

## What's already set up

| File | Purpose |
|---|---|
| `modules/chemistry-calculator/ui_interface/wsgi.py` | WSGI entry point (`application`) |
| `Procfile` | Start command for Render / Railway / Heroku-style hosts |
| `modules/chemistry-calculator/requirements.txt` | Deps, incl. gunicorn (Linux) / waitress (Windows) |

`app.run()` in `app.py` stays for local development. It is Flask's development
server and must not face the internet.

## Hardening already applied

- `MAX_CONTENT_LENGTH = 64 KB` — oversized bodies get a 413 before parsing.
- `_MAX_FIELD_LEN = 512` — a `before_request` guard rejects absurdly long string
  fields with a 400. Every `/api/` route feeds strings to the chemistry parsers,
  whose cost grows with input length, so one guard covers all 22 of them.
- Debug mode is opt-in (`CHEMCALC_DEBUG=1`) and binding defaults to
  `127.0.0.1`. Neither should change for a local run.
- **Per-IP rate limiting** (Flask-Limiter): each visitor gets 90 requests/min
  and 1200/hour per route, keyed on the real client IP from `X-Forwarded-For`;
  over that returns `429`. Static assets are exempt. It is optional at runtime —
  if Flask-Limiter is not installed the app runs unthrottled rather than failing
  to boot.

Verified: normal request 200, 600-char field 400, 100 KB body 413, and the
limiter isolates per IP (one flooder is blocked while other visitors are not).

## Running it locally with a production server

```bash
cd modules/chemistry-calculator/ui_interface
gunicorn --bind 127.0.0.1:5000 wsgi:application            # Linux/macOS
waitress-serve --listen=127.0.0.1:5000 wsgi:application    # Windows
```

> **Testing rate limiting locally:** gunicorn passes `X-Forwarded-For` through,
> so the limiter keys on the real IP with no extra flags — this is how it runs
> in production. **waitress strips the header by default**, which collapses every
> visitor onto one shared counter; to test per-IP behaviour under waitress add
> `--trusted-proxy=127.0.0.1 --trusted-proxy-headers=x-forwarded-for`. This
> matters only for local testing on Windows, never in production.

## Deploying

### PythonAnywhere (the one this project uses)

Always-on, no cold starts, no Docker. Free tier gives
`<username>.pythonanywhere.com`.

**1. Get the code** — in a PythonAnywhere **Bash console**:

```bash
git clone https://github.com/kubinokitsune/chem-calculator.git
cd chem-calculator
pip3.13 install --user -r modules/chemistry-calculator/requirements.txt
```

**2. Create the web app** — *Web* tab → *Add a new web app* → **Manual
configuration** (**not** the "Flask" option, which scaffolds its own app) →
Python 3.13.

**3. Point it at the code** — still on the *Web* tab:

| Field | Value |
|---|---|
| Source code | `/home/<username>/chem-calculator/modules/chemistry-calculator/ui_interface` |
| Working directory | same as above |

**4. WSGI file** — click the *WSGI configuration file* link, delete everything,
and paste the contents of [`deploy/pythonanywhere_wsgi.py`](deploy/pythonanywhere_wsgi.py),
changing `USERNAME` to your username.

**5. Static files** (so CSS and fonts are served directly, not through Flask):

| URL | Directory |
|---|---|
| `/static/` | `/home/<username>/chem-calculator/modules/chemistry-calculator/ui_interface/static/` |

**6.** Hit **Reload**, then open the site.

**To deploy updates later:** in a Bash console, `cd chem-calculator && git pull`,
then press **Reload** on the Web tab.

### Render (alternative)

Nicer git-push deploys, but the free tier sleeps when idle, so the first request
after a pause takes ~50 s.

1. New Web Service from the repo.
2. Build: `pip install -r requirements.txt`
3. Start: leave blank — the `Procfile` is used.

`$PORT` is supplied by the host; the Procfile already reads it.

## Before going public

- [ ] Confirm `CHEMCALC_DEBUG` is **not** set in the host's environment.
- [ ] Check the host's logs after the first deploy for import errors.
- [ ] Re-read [NOTICE.md](NOTICE.md) — the exam-use disclaimer should stay
      visible on a public deployment.

## Note on the local `.venv`

`modules/chemistry-calculator/.venv` currently points at a Microsoft Store
Python that is no longer installed, so it can't run. Recreate it with a real
interpreter:

```bash
py -m venv modules/chemistry-calculator/.venv
modules/chemistry-calculator/.venv/Scripts/python -m pip install -r modules/chemistry-calculator/requirements.txt
```
