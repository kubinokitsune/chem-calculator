"""WSGI entry point for production servers.

``app.run()`` in app.py is Flask's development server: single-threaded and
explicitly not meant to face the internet. Production hosts instead import a
WSGI callable, which is what this module exposes.

Run it with a real server:

    gunicorn --chdir modules/chemistry-calculator/ui_interface wsgi:application
    waitress-serve --listen=0.0.0.0:5000 wsgi:application      # Windows

Or, on a host that asks for an import path (PythonAnywhere and similar), point
it at this file's ``application``.
"""

from app import app as application

# Some hosts look for `app` instead of `application`; both names work.
app = application
