from flask import Flask, send_from_directory, request, jsonify
import os, sys, subprocess

app = Flask(__name__, static_folder='.', static_url_path='')

# map keys shown in the menu to script filenames (in parent dir)
MODULE_MAP = {
    "mole_conversions": "mole_conversions.py",
    "empirical_formula": "Empirical_Formula_Calculator.py",
    "equation_balancer": "equation_balancer.py",
    "limiting_reactant": "limiting_reactant.py",
    # add others as needed
}

BASE_DIR = os.path.normpath(os.path.join(app.root_path, '..'))  # chemistry-calculator folder

@app.route('/')
def index():
    return send_from_directory('.', 'main_page.html')

@app.route('/api/open', methods=['POST'])
def api_open():
    data = request.json or {}
    module_key = data.get('module')
    if module_key not in MODULE_MAP:
        return jsonify(error="Unknown module"), 400
    script_rel = MODULE_MAP[module_key]
    script_path = os.path.join(BASE_DIR, script_rel)
    if not os.path.exists(script_path):
        return jsonify(error=f"Script not found: {script_path}"), 400

    try:
        # Launch a new console window running the module with the same Python interpreter
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_CONSOLE
        subprocess.Popen([sys.executable, script_path], cwd=BASE_DIR, creationflags=creationflags)
        return jsonify(status="launched", script=script_path)
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)