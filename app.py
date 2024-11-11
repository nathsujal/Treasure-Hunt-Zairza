from flask import Flask, render_template, request, send_file, url_for, jsonify
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
FINAL_ANSWER = "69"

# Directory where QR codes are stored
QR_CODES_DIR = "qr_codes"  # Adjust the path as needed

# Location data
LOCATIONS = {
    'A': {
        'name': 'Starting Point - Zairza',
        'riddle': '''
A gate once grand, now forever closed tight,
Newcomers wonder if it ever saw light.
Promised repairs that seem to delay,
Find where the start is still locked away.''',
        'password': 'start',
        'next_location': 'B'
    },
    'B': {
        'name': 'Main Gate',
        'riddle': '''
Where melodies blend and secrets took flight,
Claps echoed loud through a skylight.
But true talent plays strings and keys,
Find where rhythm meets whispered tease.
        ''',
        'password': 'zairza',
        'next_location': 'C'
    },
    'C': {
        'name': 'Arpeggio',
        'riddle': '''
Where melodies blend and secrets took flight,
Claps echoed loud through a skylight.
But true talent plays strings and keys,
Find where rhythm meets whispered tease.
        ''',
        'password': 'main gate',
        'next_location': 'D'
    },
    'D': {
        'name': 'KHR',
        'riddle': '''
At 7 PM, outside I stand,
Not for food, but for something planned.
A crowd of boys, hearts in a whirl,
Waiting there for a glimpse of a twirl.
        ''',
        'password': 'arpeggio',
        'next_location': 'E'
    },
    'E': {
        'name': 'Zairza',
        'riddle': '''
Three minds, each from a different place,
One speaks Tamil, with speed and grace.
One from Marwari roots, sharp in trade,
The Brahmin’s wisdom, never to fade.
Together they lead, diverse yet strong,
Guess where they are, where they all belong?
        ''',
        'password': 'khr',
        'next_location': 'F'
    },
    'F': {
        'name': 'Zairza',
        'riddle': '''
A playful fee, a mischievous twist,
A number so cheeky, it can’t be missed.
Flip them around, the fun’s the same,
Zairzest owes this cheeky name.
What number pays for the fest’s delight,
Where tech and laughter unite?
        ''',
        'password': 'zairza',
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
            zip_file.writestr(f"{location_id}.png", img_buffer.read())

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

@app.route('/submit_final_answer', methods=['POST'])
def submit_final_answer():
    answer = request.form.get('answer', '').strip()
    if answer == FINAL_ANSWER:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({
            'status': 'success',
            'message': 'Correct answer!',
            'timestamp': timestamp
        })
    return jsonify({
        'status': 'error',
        'message': 'Incorrect answer. Try again!'
    })

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
        password = request.form.get('password', '').lower()
        if password == location_data['password']:
            unlocked = True
        else:
            error = "Incorrect password! Try again."

    # Check if this is the final location
    is_final = location_data.get('is_final', False)

    return render_template(
        'location.html',
        location_id=location_id,
        location=location_data,
        error=error,
        unlocked=unlocked,
        is_final=is_final
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)