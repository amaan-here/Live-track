# tracker_simulator.py

import requests
import json
import time
import random

# The URL of our Flask server's endpoint
URL = "http://127.0.0.1:5000/update_location"

# Starting coordinates (Udaipur, India)
lat1, lng1 = 24.5854, 73.7125
lat2, lng2 = 24.5750, 73.6900

print("Starting GPS tracker simulation...")
print(f"Data will be sent to {URL}")

try:
    while True:
        # Move the coordinates slightly to simulate movement
        lat1 += (random.random() - 0.5) * 0.001
        lng1 += (random.random() - 0.5) * 0.001
        
        lat2 += (random.random() - 0.5) * 0.001
        lng2 += (random.random() - 0.5) * 0.001
        
        # Data packet for the first tracker
        data1 = {
            "device_id": "tracker01",
            "lat": lat1,
            "lng": lng1
        }
        
        # Data packet for the second tracker
        data2 = {
            "device_id": "truck42",
            "lat": lat2,
            "lng": lng2
        }

        try:
            # Send data for tracker 1
            response1 = requests.post(URL, json=data1)
            print(f"Tracker01 Response: {response1.status_code}, {response1.json()}")
            
            # Send data for tracker 2
            response2 = requests.post(URL, json=data2)
            print(f"Truck42 Response: {response2.status_code}, {response2.json()}")

        except requests.exceptions.RequestException as e:
            print(f"Error sending request: {e}")

        # Wait for a few seconds before sending the next update
        time.sleep(5)

except KeyboardInterrupt:
    print("\nSimulation stopped by user.")