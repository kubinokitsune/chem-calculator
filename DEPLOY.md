# Deploying the web UI

The browser UI is a Flask app with a Python backend (`/api/*` routes do the
chemistry), so it needs a Python host — **GitHub Pages cannot run it.**

## Self-hosting at home, safely

A public web app on a home network means any bug in the app is a foothold on
the network everything else lives on. This project is self-hosted anyway, so
the setup below is built around containing that: the app runs alone in its own
unprivileged container as a non-root user, and it's published through
Tailscale Funnel, so no router port is ever opened. If the app were broken
into, there would be nothing next to it.

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

### Proxmox container + Tailscale Funnel (the one this project uses)

Always on, free, no domain, no port forward.

| Piece | Setup |
|---|---|
| Container | Proxmox LXC `chemcalc`: unprivileged, 1 core, 1 GB RAM, starts on boot, holds nothing else |
| Code | `/opt/chem-calculator` (a clone of this repo), venv at `/opt/venv` |
| App server | `chemcalc.service`: gunicorn, 2 workers × 4 threads, bound to `127.0.0.1:5000`, run as the non-root `chemcalc` user with `ProtectSystem=strict`, `NoNewPrivileges` and `MemoryMax=768M` |
| Public URL | `tailscale funnel --bg 5000` inside the container; Tailscale runs in userspace-networking mode because an unprivileged LXC has no `/dev/net/tun` |
| Logs | `/var/log/chemcalc/access.log` with the real client IP first (`X-Forwarded-For`), rotated daily and kept for 14 days |

**To deploy updates**, on the Proxmox host:

```bash
pct exec <ctid> -- sh -c 'cd /opt/chem-calculator && git pull && systemctl restart chemcalc'
```

Funnel's proxy sets `X-Forwarded-For`, so the per-IP rate limit keys on real
visitors. Funnel traffic never reaches the host's firewall, so abusive clients
are throttled by the app's limiter (429), not banned.

### PythonAnywhere (alternative)

No server of your own; the free tier gives `<username>.pythonanywhere.com`, but
free apps are disabled after a month without activity. Create a **Manual
configuration** web app (not the "Flask" option), point *Source code* and
*Working directory* at `modules/chemistry-calculator/ui_interface`, paste
[`deploy/pythonanywhere_wsgi.py`](deploy/pythonanywhere_wsgi.py) into the WSGI
file (set `USERNAME`), map `/static/` to that folder's `static/`, and Reload.

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
