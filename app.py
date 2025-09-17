import os
import json
import googlemaps
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv

# This finds and loads the variables from your .env file
load_dotenv()

# --- App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-random-secret-key-you-generate'
socketio = SocketIO(app)

# --- Initialize Google Maps Client ---
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise RuntimeError("GOOGLE_MAPS_API_KEY not found in .env file.")
gmaps = googlemaps.Client(key=API_KEY)

# --- In-Memory Data Storage ---
tracker_locations = {}

# --- API Endpoints using Google Maps ---

@app.route('/search_destination')
def search_destination():
    """Finds a destination and its nearby bus stops using Google Maps APIs."""
    query = request.args.get('query')
    user_lat = request.args.get('lat')
    user_lng = request.args.get('lng')

    if not query:
        return jsonify({"error": "Query is missing"}), 400

    try:
        # Step 1: Geocode the search query to get coordinates
        geocode_result = gmaps.geocode(query, region='in') # Bias search to India
        if not geocode_result:
            return jsonify({"error": "Location not found"}), 404
        dest_location = geocode_result[0]['geometry']['location']
        
        # Step 2: Find bus stops near the user's location
        nearby_stops = []
        if user_lat and user_lng:
            places_result = gmaps.places_nearby(
                location=(user_lat, user_lng),
                rank_by='distance',
                type='bus_station'
            )
            for place in places_result.get('results', [])[:4]: # Get top 4 nearby stops
                nearby_stops.append({
                    "name": place.get('name'),
                    "location": place['geometry']['location']
                })

        response_data = {
            "destination": {
                "name": geocode_result[0]['formatted_address'],
                "location": dest_location
            },
            "nearby_stops": nearby_stops
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Google Maps API Error: {e}")
        return jsonify({"error": "An error occurred with the mapping service"}), 500


@app.route('/get_route')
def get_route():
    """Calculates a route using the Google Maps Directions API."""
    start_coords = tuple(map(float, request.args.get('start').split(','))) # "lat,lng"
    end_coords = tuple(map(float, request.args.get('end').split(',')))     # "lat,lng"

    try:
        directions_result = gmaps.directions(start_coords, end_coords, mode="walking", departure_time=datetime.now())
        if not directions_result:
            return jsonify({"error": "Could not calculate a route"}), 404

        route = directions_result[0]
        overview_polyline = route['overview_polyline']['points'] # This is an encoded string
        duration_text = route['legs'][0]['duration']['text']
        
        return jsonify({ "polyline": overview_polyline, "duration": duration_text })

    except Exception as e:
        print(f"Google Directions API Error: {e}")
        return jsonify({"error": "An error occurred with the routing service"}), 500

# --- Live Tracker Endpoint ---
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    device_id = data['device_id']
    location = {'lat': data['lat'], 'lng': data['lng']}
    tracker_locations[device_id] = location
    socketio.emit('new_location', {'device_id': device_id, 'location': location})
    print(f"Received update from: {device_id} at {location}")
    return jsonify({"status": "success"})

# --- Page Serving Routes ---
@app.route('/')
def welcome(): return render_template('welcome.html')

@app.route('/tracker/<lang>')
def index(lang): return render_template('index.html')

@app.route('/mobile')
def mobile_tracker(): return render_template('mobile_tracker.html')

# --- Socket.IO Events ---
@socketio.on('connect')
def handle_connect():
    for device_id, location in tracker_locations.items():
        socketio.emit('new_location', {'device_id': device_id, 'location': location})

# --- Run the App ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)