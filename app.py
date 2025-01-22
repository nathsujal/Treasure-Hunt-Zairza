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
        'name': 'Starting Point - SAC',
        'riddle': '''
Where beats and rhythms fill the air,
Creativity flows and souls lay bare.
A hub for jamming, both day and night,
Your next clue hides where music feels right.
        ''',
        'password': 'start',
        'next_location': 'B'
    },
    'B': {
        'name': 'Stage Area',
        'riddle': '''
Once a spotlight for stars to shine,
Last year, it fell out of line.
But now it's ready, no longer away,
Find your next clue where performers sway.
        ''',
        'password': 'zairza',
        'next_location': 'C'
    },
    'C': {
        'name': 'OUTR FINE',
        'riddle': '''
Where ideas ignite and dreams take flight,
A hub of innovation, shining bright.
From spark to startup, it's the place to align,
Find your next clue where visions refine.
        ''',
        'password': 'stage area',
        'next_location': 'D'
    },
    'D': {
        'name': 'Bus Stand',
        'riddle': '''
Where wheels depart and friendships mend,
Hostel hearts bid goodbye to day scholar friends.
The journey begins, but bonds remain true,
Find your next clue where partings ensue.
        ''',
        'password': 'outr fine',
        'next_location': 'E'
    },
    'E': {
        'name': 'Zairza',
        'riddle': '''
Where hearts are healed over snacks and tea,
And corners buzz with carefree glee.
A break-time haven, both calm and loud,
Your next clue hides amidst the crowd.
-
Follow this link
https://pastebin.com/HAggA3Ry
        ''',
        'password': 'bus stand',
        'next_location': None
    },
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
    completion_time = None

    # Check if this is the final location
    is_final = location_id == 'F'

    # First location is always unlocked
    if location_id == 'A':
        unlocked = True

    # Handle POST requests
    if request.method == 'POST':
        if is_final and 'final_answer' in request.form:
            # Handle final answer submission
            final_answer = request.form.get('final_answer', '').strip()
            if final_answer == FINAL_ANSWER:
                completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return jsonify({
                    'status': 'success',
                    'message': 'Congratulations! You have completed the treasure hunt!',
                    'completion_time': completion_time
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Incorrect answer. Try again!'
                })
        else:
            # Handle regular password check
            password = request.form.get('password', '').lower()
            if password == location_data['password']:
                unlocked = True
            else:
                error = "Incorrect password! Try again."

    return render_template(
        'location.html',
        location_id=location_id,
        location=location_data,
        error=error,
        unlocked=unlocked,
        completion_time=completion_time,
        is_final=is_final  # Pass is_final to the template
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
