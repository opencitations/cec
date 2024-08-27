import sys
import os

# Determina il percorso della directory principale del progetto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
print("Project root:", project_root)

# Aggiunge la directory 'cic' al sys.path
cic_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.append(cic_path)

# Sopra aggiunte mie per trovare path, poi da server van tolte (suppongo...)
######################

from flask import Flask
from blueprints.web_interface import interface_bp
from blueprints.cic_api import api_bp

app = Flask(__name__)

# Registrazione blueprint
app.register_blueprint(interface_bp, url_prefix='/')
app.register_blueprint(api_bp, url_prefix='/api')

# Stampa per verificare che i blueprint siano registrati
#print("Blueprints registered:", app.blueprints)

if __name__ == '__main__':
    app.run(debug=True)
