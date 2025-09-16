import os
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key!'
socketio = SocketIO(app)

bus_routes_data = []
try:
    with open('bus_data.json', 'r', encoding='utf-8') as f:
        bus_routes_data = json.load(f)
except FileNotFoundError:
    print("WARNING: bus_data.json not found.")

translations = {
    'en': {"header_title": "LiveTrack"}
}
tracker_locations = {}

@app.route('/get_routes')
def get_routes():
    return jsonify(bus_routes_data)

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    device_id = data['device_id']
    location = {'lat': data['lat'], 'lng': data['lng']}
    tracker_locations[device_id] = location
    socketio.emit('new_location', {'device_id': device_id, 'location': location})
    print(f"Received update from: {device_id} at {location}")
    return jsonify({"status": "success"})

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/tracker/<lang>')
def index(lang):
    selected_translations = translations.get(lang, translations['en'])
    return render_template('index.html', translations=selected_translations)

@app.route('/mobile')
def mobile_tracker():
    return render_template('mobile_tracker.html')

@socketio.on('connect')
def handle_connect():
    for device_id, location in tracker_locations.items():
        socketio.emit('new_location', {'device_id': device_id, 'location': location})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)