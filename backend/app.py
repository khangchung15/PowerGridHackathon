from flask import Flask, render_template, jsonify, request
from scraper import scrape_ercot_data
from datetime import datetime
import os
import json

app = Flask(__name__, 
            template_folder=os.path.abspath('../frontend/templates'),
            static_folder=os.path.abspath('../frontend/static'))

# Default thresholds
DEFAULT_THRESHOLDS = {
    'COAST': 18646,
    'EAST': 2156,
    'FAR_WEST': 8752,
    'NORTH': 1900,
    'NORTH_C': 16584,
    'SOUTH_C': 5770,
    'SOUTHERN': 12374,
    'WEST': 1527
}

THRESHOLDS_FILE = 'thresholds.json'

def load_thresholds():
    """Load thresholds from JSON file or return defaults if file doesn't exist"""
    try:
        if os.path.exists(THRESHOLDS_FILE):
            with open(THRESHOLDS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading thresholds: {e}")
    return DEFAULT_THRESHOLDS

def save_thresholds(thresholds):
    """Save thresholds to JSON file"""
    with open(THRESHOLDS_FILE, 'w') as f:
        json.dump(thresholds, f, indent=4)

@app.route('/')
def serve_frontend():
    return render_template('hackathon.html')

@app.route('/api/grid-data')
def get_grid_data():
    current_thresholds = load_thresholds()
    scraped_data = scrape_ercot_data()
    
    if 'error' in scraped_data:
        return jsonify(scraped_data), scraped_data.get('status', 500)
    
    processed_data = process_grid_data(scraped_data, current_thresholds)
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'zones': processed_data,
        'current_thresholds': current_thresholds,
        'default_thresholds': DEFAULT_THRESHOLDS
    })

@app.route('/api/update-thresholds', methods=['POST'])
def update_thresholds():
    try:
        new_thresholds = request.json
        save_thresholds(new_thresholds)
        return jsonify({'status': 'success', 'thresholds': new_thresholds})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def military_to_standard_time(military_time):
    """Convert military time to standard format"""
    try:
        hour = int(military_time[:2])
        period = 'AM' if hour < 12 else 'PM'
        hour = hour if hour <= 12 else hour - 12
        return f"{hour} {period}"
    except:
        return military_time

def process_grid_data(raw_data, thresholds):
    zones = []
    REGION_ORDER = ['COAST', 'EAST', 'FAR_WEST', 'NORTH',
                   'NORTH_C', 'SOUTH_C', 'SOUTHERN', 'WEST']
    
    for row in raw_data.get('data', []):
        try:
            if len(row) >= 11:
                zone_data = {
                    'date': row[0],
                    'hour': row[1],
                    'hour_display': military_to_standard_time(row[1]),
                    'regions': {},
                    'total': float(row[10].replace(',', '')),
                    'warnings': []
                }
                
                for i, region in enumerate(REGION_ORDER):
                    load = float(row[2+i].replace(',', ''))
                    zone_data['regions'][region] = load
                    if load > thresholds.get(region, float('inf')):
                        zone_data['warnings'].append(region)
                
                zones.append(zone_data)
        except Exception as e:
            print(f"Skipping row: {e}")
            continue
    
    return zones

if __name__ == '__main__':
    # Ensure thresholds file exists on startup
    if not os.path.exists(THRESHOLDS_FILE):
        save_thresholds(DEFAULT_THRESHOLDS)
    app.run(debug=True, port=5000)