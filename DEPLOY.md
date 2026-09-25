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

Verified: normal request 200, 600-char field 400, 100 KB body 413.

## Running it locally with a production server

```bash
cd modules/chemistry-calculator/ui_interface
waitress-serve --listen=127.0.0.1:5000 wsgi:application    # Windows
gunicorn --bind 127.0.0.1:5000 wsgi:application            # Linux/macOS
```

## Deploying

**PythonAnywhere** (simplest — persistent, no cold starts, no Docker):

1. Create a web app, choose **Flask** + Python 3.13.
2. Source directory: `modules/chemistry-calculator/ui_interface`
3. Point the WSGI config file at `wsgi.py`'s `application`.
4. `pip install -r modules/chemistry-calculator/requirements.txt`

**Render** (nicer git-push deploys; free tier sleeps when idle, so the first
request after a pause is slow):

1. New Web Service from the repo.
2. Build: `pip install -r modules/chemistry-calculator/requirements.txt`
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
