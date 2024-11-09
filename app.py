from flask import Flask, render_template, request, send_file, url_for
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime
import zipfile
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
print("admin password:", ADMIN_PASSWORD)

# Directory where QR codes are stored
QR_CODES_DIR = "qr_codes"  # Adjust the path as needed

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

@app.route("/admin", methods=["GET"])
def admin():
    return render_template("admin.html")

@app.route('/admin/download', methods=['POST'])
def download_qr_codes():
    # Check if the password provided in the form matches
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return "Unauthorized", 401

    base_url = "https://treasure-hunt-zairza.onrender.com/"

    # Create a BytesIO object to store the .zip file in memory
    zip_buffer = BytesIO()

    # Create a ZipFile object
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
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
            
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code to a temporary BytesIO object
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            # Add the image to the zip file
            zip_file.writestr(f"{location}.png", img_buffer.read())

    # Ensure the buffer's pointer is at the beginning
    zip_buffer.seek(0)

    # Send the zip file to the client for download
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='qr_codes.zip'
    )

def generate_qr_codes():
    """Generate all QR codes and save them to the system"""
    base_url = "https://treasure-hunt-zairza.onrender.com/"
    
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

def get_qr_code_data(location_id):
    """Get QR code as base64 string"""
    with open(f'static/qr_codes/location_{location_id}.png', 'rb') as f:
        return base64.b64encode(f.read()).decode()

@app.route('/')
def index():
    # Generate QR codes when the application starts
    generate_qr_codes()
    return render_template('index.html')

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)