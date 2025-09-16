import os
import json
import requests # Make sure you have 'requests' installed (pip install requests)
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key!'
socketio = SocketIO(app)

# --- Load API Key ---
ORS_API_KEY = os.environ.get('ORS_API_KEY')

# --- (The rest of your setup remains the same) ---
bus_routes_data = []
try:
    with open('bus_data.json', 'r', encoding='utf-8') as f:
        bus_routes_data = json.load(f)
except FileNotFoundError:
    print("WARNING: bus_data.json not found.")
translations = {'en': {"header_title": "LiveTrack"}}
tracker_locations = {}

# --- NEW ROUTE to calculate a road path using OpenRouteService ---
@app.route('/get_route', methods=['GET'])
def get_route():
    if not ORS_API_KEY:
        return jsonify({"error": "ORS API key not configured on server"}), 500
        
    start_coords = request.args.get('start') # "lng,lat"
    end_coords = request.args.get('end')     # "lng,lat"

    if not start_coords or not end_coords:
        return jsonify({"error": "Start or end coordinates missing"}), 400
    
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    # Note: ORS expects coordinates in (longitude, latitude) format
    body = {
        "coordinates": [
            [float(coord) for coord in start_coords.split(',')],
            [float(coord) for coord in end_coords.split(',')]
        ]
    }
    
    # We'll use the foot-walking profile for the route
    response = requests.post(
        'https://api.openrouteservice.org/v2/directions/foot-walking/json', 
        json=body, 
        headers=headers
    )
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to get route from ORS", "details": response.text}), response.status_code

# --- (All other routes remain the same) ---
@app.route('/get_routes')
def get_routes(): return jsonify(bus_routes_data)
# ... (and so on for all your existing routes)
@app.route('/')
def welcome(): return render_template('welcome.html')
@app.route('/tracker/<lang>')
def index(lang):
    selected_translations = translations.get(lang, translations['en'])
    return render_template('index.html', translations=selected_translations)
@app.route('/mobile')
def mobile_tracker(): return render_template('mobile_tracker.html')
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json(); device_id = data['device_id']; location = {'lat': data['lat'], 'lng': data['lng']}
    tracker_locations[device_id] = location; socketio.emit('new_location', {'device_id': device_id, 'location': location})
    print(f"Received update from: {device_id} at {location}"); return jsonify({"status": "success"})
@socketio.on('connect')
def handle_connect():
    for device_id, location in tracker_locations.items():
        socketio.emit('new_location', {'device_id': device_id, 'location': location})
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)