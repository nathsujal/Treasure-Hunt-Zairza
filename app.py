from flask import Flask, render_template, request, send_file, url_for
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime
import zipfile

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Directory where QR codes are stored
QR_CODES_DIR = "qr_codes"  # Adjust the path as needed

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            # Create a zip file of all QR codes
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zipf:
                for root, dirs, files in os.walk(QR_CODES_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, QR_CODES_DIR))
            memory_file.seek(0)
            return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name="qr_codes.zip")
        else:
            return "Incorrect password", 403
    return render_template("admin.html")

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

def get_base_url():
    """Get the base URL for the application"""
    if os.environ.get('RENDER'):
        return os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
    return request.url_root.rstrip('/')

def generate_qr_codes():
    """Generate all QR codes and save them to the system"""
    base_url = get_base_url()
    
    if not os.path.exists('static/qr_codes'):
        os.makedirs('static/qr_codes')
    
    for location_id in LOCATIONS:
        url = f"{base_url}/location/{location_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f'static/qr_codes/location_{location_id}.png')

def get_qr_code_data(location_id):
    """Get QR code as base64 string"""
    with open(f'static/qr_codes/location_{location_id}.png', 'rb') as f:
        return base64.b64encode(f.read()).decode()

@app.route('/')
def index():
    # Generate QR codes when the application starts
    generate_qr_codes()
    return render_template('index.html')

@app.route('/download_qr_codes')
def download_qr_codes():
    # Create zip file containing all QR codes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f'qr_codes_{timestamp}.zip'
    
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

    # First location is always unlocked
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

# Ensure directories exist
for directory in ['static/qr_codes', 'static/downloads', 'templates']:
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)