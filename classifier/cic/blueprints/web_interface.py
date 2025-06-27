from flask import Blueprint, render_template

interface_bp = Blueprint('interface', __name__)

@interface_bp.route('/')
def index():
    return render_template('index.html', prefix='/cic/')

@interface_bp.route('/classifier')
def classifier_page():
    return render_template('classifier.html', prefix='/cic')
