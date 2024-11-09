from flask import Flask, render_template, request, send_file, make_response
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Location data
LOCATIONS = {
    'A': {
        'name': 'Starting Point - Library',
        'riddle': 'Where numbers flow and waves grow, data streams in rows. Find the place where knowledge glows.',
        'password': 'start',
        'next_location': 'B'
    },
    'B': {
        'name': 'Computer Lab',
        'riddle': 'Leaves dance in circles, beneath ancient bark. Your next stop lies in nature\'s park.',
        'password': 'library',
        'next_location': 'C'
    },
    'C': {
        'name': 'Old Oak Tree',
        'riddle': 'Where athletes gather, victories soar. Find your next clue where players score.',
        'password': 'computerlab',
        'next_location': 'D'
    },
    'D': {
        'name': 'Sports Field',
        'riddle': 'Books and bytes in perfect peace, where silence helps the mind release.',
        'password': 'oaktree',
        'next_location': 'E'
    },
    'E': {
        'name': 'Study Room',
        'riddle': 'Final challenge in your quest: where morning greetings are expressed.',
        'password': 'sportsfield',
        'next_location': 'F'
    },
    'F': {
        'name': 'Main Entrance',
        'riddle': 'Congratulations! You\'ve completed the treasure hunt!',
        'password': 'studyroom',
        'next_location': None
    }
}

def generate_qr_code(data, location_id):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO object
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    # Save to file system
    if not os.path.exists('static/qr_codes'):
        os.makedirs('static/qr_codes')
    img.save(f'static/qr_codes/location_{location_id}.png')
    
    return base64.b64encode(buffered.getvalue()).decode()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr_codes')
def generate_qr_codes_page():
    base_url = request.url_root.rstrip('/')
    qr_codes = {}
    
    for location_id, location_data in LOCATIONS.items():
        url = f"{base_url}/location/{location_id}"
        qr_codes[location_id] = {
            'image': generate_qr_code(url, location_id),
            'name': location_data['name'],
            'url': url
        }
    
    return render_template('qr_codes.html', locations=LOCATIONS, qr_codes=qr_codes)

@app.route('/download_qr_codes')
def download_qr_codes():
    base_url = request.url_root.rstrip('/')
    
    # Generate all QR codes
    for location_id in LOCATIONS:
        url = f"{base_url}/location/{location_id}"
        generate_qr_code(url, location_id)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f'qr_codes_{timestamp}.zip'
    
    # Create zip file containing all QR codes
    import zipfile
    
    if not os.path.exists('static/downloads'):
        os.makedirs('static/downloads')
        
    zip_path = os.path.join('static/downloads', zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for location_id in LOCATIONS:
            qr_path = f'static/qr_codes/location_{location_id}.png'
            zipf.write(qr_path, f'location_{location_id}.png')
    
    return send_file(
        zip_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@app.route('/location/<location_id>', methods=['GET', 'POST'])
def location(location_id):
    if location_id not in LOCATIONS:
        return "Location not found", 404

    location_data = LOCATIONS[location_id]
    error = None
    unlocked = False

    if location_id == 'A':
        unlocked = True

    if request.method == 'POST':
        password = request.form.get('password', '').lower().replace(' ', '')
        if password == location_data['password']:
            unlocked = True
        else:
            error = "Incorrect password! Try again."

    return render_template(
        'location.html',
        location_id=location_id,
        location=location_data,
        error=error,
        unlocked=unlocked
    )

# Create templates directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

# Write the template files
with open('templates/qr_codes.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Treasure Hunt QR Codes</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen py-6">
    <div class="max-w-6xl mx-auto">
        <div class="bg-white rounded-xl shadow-md overflow-hidden m-4 p-6">
            <h1 class="text-2xl font-bold mb-4">Treasure Hunt QR Codes</h1>
            <div class="mb-4">
                <a href="{{ url_for('download_qr_codes') }}" 
                   class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Download All QR Codes (ZIP)
                </a>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {% for location_id, qr_data in qr_codes.items() %}
                <div class="border rounded-lg p-4">
                    <h2 class="text-xl font-semibold mb-2">Location {{ location_id }}: {{ qr_data.name }}</h2>
                    <img src="data:image/png;base64,{{ qr_data.image }}" 
                         alt="QR Code for Location {{ location_id }}"
                         class="mx-auto mb-2">
                    <div class="text-sm text-gray-600">
                        <p>URL: {{ qr_data.url }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
''')

# Update index.html to include link to QR codes page
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Treasure Hunt</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen py-6">
    <div class="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-2xl m-4 p-6">
        <h1 class="text-2xl font-bold mb-4">Welcome to the Treasure Hunt!</h1>
        <p class="mb-4">Start your journey by scanning the QR code at Location A.</p>
        <p class="text-sm text-gray-600 mb-4">Each location will provide you with a riddle leading to the next location.</p>
        <a href="{{ url_for('generate_qr_codes_page') }}" 
           class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Generate QR Codes
        </a>
    </div>
</body>
</html>
''')

# Update existing location.html template
with open('templates/location.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Location {{location_id}} - Treasure Hunt</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body class="bg-gray-100 min-h-screen py-6">
    <div class="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-2xl m-4 p-6">
        <h1 class="text-2xl font-bold mb-4">Location {{location_id}}</h1>
        
        {% if not unlocked %}
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">
                        Enter password from previous location:
                    </label>
                    <input type="text" name="password" 
                           class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                </div>
                {% if error %}
                    <p class="text-red-500 text-sm">{{error}}</p>
                {% endif %}
                <button type="submit" 
                        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Unlock
                </button>
            </form>
        {% else %}
            <div class="space-y-4">
                <div>
                    <h2 class="font-semibold">Current Location:</h2>
                    <p>{{location.name}}</p>
                </div>
                <div>
                    <h2 class="font-semibold">Your Riddle:</h2>
                    <p>{{location.riddle}}</p>
                </div>
                {% if location.next_location %}
                    <div>
                        <h2 class="font-semibold">Next Location:</h2>
                        <p>Find the QR code at the location described in the riddle!</p>
                    </div>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))