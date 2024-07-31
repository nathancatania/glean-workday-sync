# Cloud function to act as Workday report endpoint for testing
# Set entrypoint to 'workday_report_export' in main.py

import json
import base64
from flask import jsonify, make_response

USERNAME = "workdayuser"
SECRET_PATH = "/secrets/custom-connector-password"
SECRET_CACHE = None

def get_secret():
    global SECRET_CACHE
    if SECRET_CACHE is None:
        try:
            with open(SECRET_PATH, 'r') as secret_file:
                SECRET_CACHE = secret_file.read().strip()
        except IOError:
            print(f"Error reading secret from {SECRET_PATH}")
            return None
    return SECRET_CACHE

def authenticate_basic(request):
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return False
    
    auth_type, auth_string = auth_header.split(' ', 1)
    
    if auth_type.lower() not in ['basic', 'bearer']:
        return False
    
    stored_secret = get_secret()
    if stored_secret is None:
        return False

    if auth_type.lower() == 'basic':
        try:
            credentials = base64.b64decode(auth_string).decode('utf-8')
            username, password = credentials.split(':', 1)
            return username == USERNAME and password == stored_secret
        except:
            return False
    elif auth_type.lower() == 'bearer':
        return auth_string == stored_secret
    
    return False
    
def workday_report_export(request):

    if not authenticate_basic(request):
        return make_response(jsonify({'error': 'Unauthorized'}), 401)
    
    
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'format' in request_json:
        format = request_json['format']
    elif request_args and 'format' in request_args:
        format = request_args['format']
    else:
        return make_response(jsonify({'error': 'Missing format parameter. Add ?format=json to URL.'}), 400)
    
    report = request_json.get('report') if request_json else request_args.get('report')

    try:
        if report == 'teams':
            with open('sample_data_teams.json') as f:
                sample_data = json.load(f)
        elif report == 'additionalfields':
            with open('sample_data_additionalfields.json') as f:
                sample_data = json.load(f)
        else:
            with open('sample_data.json') as f:
                sample_data = json.load(f)
    except IOError:
        return make_response(jsonify({'error': 'Error loading sample data'}), 500)
    
    response = make_response(jsonify(sample_data))
    response.headers['Content-Type'] = 'application/json'
    return response