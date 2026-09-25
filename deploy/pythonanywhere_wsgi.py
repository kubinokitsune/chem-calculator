"""PythonAnywhere WSGI configuration.

PythonAnywhere does not read the Procfile or wsgi.py from the repo. It runs one
file of its own, at:

    /var/www/<username>_pythonanywhere_com_wsgi.py

Open that file in the PythonAnywhere "Web" tab, delete what is there, and paste
this in. Replace USERNAME on the line below with your PythonAnywhere username.

The app imports the calculator modules from its parent directory, so the path
added here is the ui_interface folder -- app.py handles the rest itself.
"""

import sys

USERNAME = 'USERNAME'          # <- change this
REPO = f'/home/{USERNAME}/chem-calculator'

path = f'{REPO}/modules/chemistry-calculator/ui_interface'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application       # noqa: E402  (path must be set first)
