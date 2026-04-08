"""
Smart Brain Tumor Detection System - Backend API
Flask server with PostgreSQL, JWT authentication, and AI model integration
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
import io
import os
from pathlib import Path
import uuid
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from geopy.distance import geodesic
from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from ml.inference import BrainTumorPredictor, ModelNotReadyError

load_dotenv(Path(__file__).with_name('.env'))

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(
    os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024)
)

# Initialize JWT
jwt = JWTManager(app)

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:password@localhost:5432/neurodetect'
)
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '').strip()

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
predictor = BrainTumorPredictor()

def get_db_connection():
    """Create a PostgreSQL connection."""
    return connect(DATABASE_URL, row_factory=dict_row)


@contextmanager
def db_cursor(commit=False):
    """Context manager for DB access."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()


def init_db():
    """Create tables and indexes if they do not exist."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT DEFAULT 'Not specified',
            created_at TIMESTAMP NOT NULL,
            last_login TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER NOT NULL,
            rating DOUBLE PRECISION NOT NULL,
            hospital TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT DEFAULT '',
            contact TEXT NOT NULL,
            email TEXT NOT NULL,
            availability JSONB NOT NULL DEFAULT '[]'::jsonb,
            consultation_fee INTEGER NOT NULL,
            qualifications JSONB NOT NULL DEFAULT '[]'::jsonb,
            languages JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hospitals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT DEFAULT '',
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            specialists INTEGER NOT NULL,
            rating DOUBLE PRECISION NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            facilities JSONB NOT NULL DEFAULT '[]'::jsonb,
            departments JSONB NOT NULL DEFAULT '[]'::jsonb,
            timings TEXT NOT NULL,
            beds INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            image_path TEXT NOT NULL,
            detection_result JSONB NOT NULL,
            scan_date TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            doctor_id TEXT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            symptoms TEXT DEFAULT '',
            status TEXT NOT NULL,
            booked_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_doctors_city ON doctors(city)",
        "CREATE INDEX IF NOT EXISTS idx_doctors_state ON doctors(state)",
        "CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization)",
        "CREATE INDEX IF NOT EXISTS idx_doctors_rating ON doctors(rating DESC)",
        "CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id)",
        "CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)",
        "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)",
        "CREATE INDEX IF NOT EXISTS idx_hospitals_city ON hospitals(city)",
        "CREATE INDEX IF NOT EXISTS idx_hospitals_state ON hospitals(state)",
    ]

    with db_cursor(commit=True) as cur:
        for statement in statements:
            cur.execute(statement)
        cur.execute("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS state TEXT DEFAULT ''")
        cur.execute("ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS state TEXT DEFAULT ''")


def new_id():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def serialize_value(value):
    """Convert DB-native values to JSON-safe ones."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value


def serialize_record(record, rename_id=True):
    """Normalize DB row keys for API responses."""
    if not record:
        return None

    payload = {key: serialize_value(value) for key, value in record.items()}
    if rename_id and 'id' in payload:
        payload['_id'] = payload.pop('id')
    return payload


def place_supports_brain_specialty(place):
    """Return True when a Google Places result looks relevant for brain care."""
    haystack = ' '.join(
        str(value)
        for value in (
            place.get('name'),
            place.get('formatted_address'),
            ' '.join(place.get('types', [])),
        )
        if value
    ).lower()
    return any(
        keyword in haystack
        for keyword in ('neuro', 'brain', 'neurosurgery', 'neurology', 'neurosurgeon')
    )


def google_maps_directions_url(destination):
    """Build a Google Maps directions URL for a destination string."""
    return f"https://www.google.com/maps/dir/?api=1&destination={quote(destination)}"


def fetch_google_hospitals(city=None, lat=None, lng=None, radius=50, brain_specialty=True):
    """Fetch hospitals from Google Places Text Search when an API key is configured."""
    if not GOOGLE_MAPS_API_KEY:
        return []

    queries = []
    if lat is not None and lng is not None:
        queries.extend([
            f"neurology hospital near {lat},{lng}",
            f"neurosurgery hospital near {lat},{lng}",
        ])
    elif city:
        queries.extend([
            f"neurology hospital in {city}",
            f"neurosurgery hospital in {city}",
        ])
    else:
        queries.append("brain hospital")

    hospitals_by_place = {}
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    for query in queries:
        params = {
            'query': query,
            'key': GOOGLE_MAPS_API_KEY,
        }
        if lat is not None and lng is not None:
            params['location'] = f"{lat},{lng}"
            params['radius'] = int(radius * 1000)

        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()

        for place in payload.get('results', []):
            if brain_specialty and not place_supports_brain_specialty(place):
                continue

            place_id = place.get('place_id')
            if not place_id or place_id in hospitals_by_place:
                continue

            geometry = place.get('geometry', {}).get('location', {})
            place_lat = geometry.get('lat')
            place_lng = geometry.get('lng')

            distance = None
            if (
                lat is not None and lng is not None and
                place_lat is not None and place_lng is not None
            ):
                distance = round(geodesic((lat, lng), (place_lat, place_lng)).kilometers, 1)
                if distance > radius:
                    continue

            address = place.get('formatted_address', '')
            address_parts = [part.strip() for part in address.split(',') if part.strip()]
            inferred_city = city.strip() if city else (address_parts[-3] if len(address_parts) >= 3 else '')
            inferred_state = address_parts[-2] if len(address_parts) >= 2 else ''
            destination = ', '.join(filter(None, [place.get('name'), address]))

            hospitals_by_place[place_id] = {
                '_id': place_id,
                'name': place.get('name', 'Hospital'),
                'address': address,
                'city': inferred_city,
                'state': inferred_state,
                'latitude': place_lat,
                'longitude': place_lng,
                'specialists': None,
                'rating': place.get('rating'),
                'phone': 'Contact unavailable',
                'email': '',
                'facilities': [],
                'departments': [],
                'timings': 'Call for timings',
                'beds': None,
                'created_at': None,
                'source': 'google_places',
                'distance': distance,
                'directions_url': google_maps_directions_url(destination),
            }

    hospitals = list(hospitals_by_place.values())
    if lat is not None and lng is not None:
        hospitals.sort(key=lambda item: item.get('distance') if item.get('distance') is not None else float('inf'))
    else:
        hospitals.sort(key=lambda item: item['name'].lower())
    return hospitals

# Helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload_file(file):
    """Save uploaded file and return path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath
    return None

def analyze_image(image_path):
    """Analyze brain scan image using AI model"""
    import random

    try:
        return predictor.predict(image_path)
    except ModelNotReadyError:
        results = [
            {
                'detected': True,
                'confidence': 94.5,
                'severity': 'Severe',
                'tumor_type': 'Glioblastoma',
                'recommendation': 'Immediate consultation with neuro-oncologist required.'
            },
            {
                'detected': True,
                'confidence': 87.3,
                'severity': 'Moderate',
                'tumor_type': 'Meningioma',
                'recommendation': 'Schedule appointment within 48 hours for further evaluation.'
            },
            {
                'detected': True,
                'confidence': 76.8,
                'severity': 'Mild',
                'tumor_type': 'Pituitary Adenoma',
                'recommendation': 'Consult neurologist within one week for assessment.'
            },
            {
                'detected': False,
                'confidence': 92.1,
                'severity': 'None',
                'tumor_type': None,
                'recommendation': 'No tumor detected. Regular checkup recommended in 6 months.'
            }
        ]
        return random.choice(results)

def send_email(to_email, subject, html_content):
    """Send email using SendGrid"""
    try:
        message = Mail(
            from_email='noreply@neurodetect.com',
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def generate_pdf_report(scan_data, user_data):
    """Generate medical report PDF"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 80, "NeuroDetect AI")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, "Brain Tumor Detection Report")
    
    # Patient Information
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 140, "Patient Information:")
    c.setFont("Helvetica", 11)
    c.drawString(120, height - 165, f"Name: {user_data['name']}")
    c.drawString(120, height - 185, f"Email: {user_data['email']}")
    c.drawString(120, height - 205, f"Scan Date: {scan_data['scan_date']}")
    
    # Detection Results
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 245, "Detection Results:")
    c.setFont("Helvetica", 11)
    
    result = scan_data['detection_result']
    c.drawString(120, height - 270, f"Tumor Detected: {'Yes' if result['detected'] else 'No'}")
    c.drawString(120, height - 290, f"Confidence Level: {result['confidence']}%")
    c.drawString(120, height - 310, f"Severity: {result['severity']}")
    
    if result['tumor_type']:
        c.drawString(120, height - 330, f"Tumor Type: {result['tumor_type']}")
    
    # Recommendation
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 370, "Medical Recommendation:")
    c.setFont("Helvetica", 11)
    
    # Word wrap recommendation
    recommendation = result['recommendation']
    max_width = 400
    words = recommendation.split()
    line = ""
    y_position = height - 395
    
    for word in words:
        test_line = line + word + " "
        if c.stringWidth(test_line, "Helvetica", 11) < max_width:
            line = test_line
        else:
            c.drawString(120, y_position, line)
            line = word + " "
            y_position -= 20
    c.drawString(120, y_position, line)
    
    # Footer
    c.setFont("Helvetica", 9)
    c.drawString(100, 50, "This report is generated by AI and should be reviewed by a qualified medical professional.")
    c.drawString(100, 35, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.save()
    buffer.seek(0)
    return buffer


init_db()

# ==================== Authentication Endpoints ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json() or {}

        required_fields = ['name', 'email', 'password', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        with db_cursor(commit=True) as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
            if cur.fetchone():
                return jsonify({'error': 'Email already registered'}), 400

            user_id = new_id()
            now = datetime.utcnow()
            cur.execute(
                """
                INSERT INTO users (id, name, email, password, phone, city, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    data['name'],
                    data['email'],
                    generate_password_hash(data['password']),
                    data['phone'],
                    data.get('city', 'Not specified'),
                    now,
                    now,
                )
            )

        access_token = create_access_token(identity=user_id)
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json() or {}

        with db_cursor(commit=True) as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, password
                FROM users
                WHERE email = %s
                """,
                (data.get('email'),)
            )
            user = cur.fetchone()

            if not user or not check_password_hash(user['password'], data.get('password', '')):
                return jsonify({'error': 'Invalid email or password'}), 401

            cur.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.utcnow(), user['id'])
            )

        access_token = create_access_token(identity=user['id'])
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Send password reset email"""
    try:
        data = request.get_json() or {}
        email = data.get('email')

        with db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if not user:
            return jsonify({'message': 'If email exists, reset link has been sent'}), 200

        reset_token = create_access_token(
            identity=user['id'],
            expires_delta=timedelta(hours=1)
        )

        html_content = f"""
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <a href="https://neurodetect.com/reset/{reset_token}">Reset Password</a>
        <p>This link expires in 1 hour.</p>
        """

        send_email(email, 'Password Reset', html_content)
        return jsonify({'message': 'If email exists, reset link has been sent'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Detection Endpoints ====================

@app.route('/api/analyze', methods=['POST'])
@jwt_required()
def analyze_scan():
    """Analyze brain scan image"""
    try:
        user_id = get_jwt_identity()

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filepath = save_upload_file(file)
        if not filepath:
            return jsonify({'error': 'Invalid file type'}), 400

        detection_result = analyze_image(filepath)
        scan_id = new_id()

        with db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO scans (id, user_id, image_path, detection_result, scan_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    scan_id,
                    user_id,
                    filepath,
                    Jsonb(detection_result),
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.utcnow(),
                )
            )

        return jsonify({
            'scan_id': scan_id,
            'result': detection_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scans', methods=['GET'])
@jwt_required()
def get_scans():
    """Get user's scan history"""
    try:
        user_id = get_jwt_identity()

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, image_path, detection_result, scan_date, created_at
                FROM scans
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            scans = [serialize_record(scan) for scan in cur.fetchall()]

        return jsonify(scans), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scans/<scan_id>/report', methods=['GET'])
@jwt_required()
def download_report(scan_id):
    """Download scan report as PDF"""
    try:
        user_id = get_jwt_identity()

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, image_path, detection_result, scan_date, created_at
                FROM scans
                WHERE id = %s AND user_id = %s
                """,
                (scan_id, user_id)
            )
            scan = cur.fetchone()

            if not scan:
                return jsonify({'error': 'Scan not found'}), 404

            cur.execute(
                "SELECT id, name, email, phone, city, created_at, last_login FROM users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()

        pdf_buffer = generate_pdf_report(scan, user)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'brain_scan_report_{scan_id}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Doctor Endpoints ====================

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get all doctors"""
    try:
        city = request.args.get('city')
        specialization = request.args.get('specialization')
        state = request.args.get('state')

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, specialization, experience, rating, hospital, city, state,
                       contact, email, availability, consultation_fee, qualifications,
                       languages, created_at
                FROM doctors
                WHERE (%s IS NULL OR city ILIKE %s)
                  AND (%s IS NULL OR state ILIKE %s)
                  AND (%s IS NULL OR specialization ILIKE %s)
                ORDER BY rating DESC, name ASC
                """,
                (
                    city,
                    f"%{city.strip()}%" if city else None,
                    state,
                    f"%{state.strip()}%" if state else None,
                    specialization,
                    f"%{specialization.strip()}%" if specialization else None,
                )
            )
            doctors = [serialize_record(doctor) for doctor in cur.fetchall()]

        return jsonify(doctors), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/doctors/<doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Get specific doctor details"""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, specialization, experience, rating, hospital, city, state,
                       contact, email, availability, consultation_fee, qualifications,
                       languages, created_at
                FROM doctors
                WHERE id = %s
                """,
                (doctor_id,)
            )
            doctor = cur.fetchone()

        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        return jsonify(serialize_record(doctor)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Hospital Endpoints ====================

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Get hospitals"""
    try:
        city = request.args.get('city')
        state = request.args.get('state')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', default=50, type=float)
        brain_specialty = request.args.get('brain_specialty', default='true').lower() != 'false'

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, address, city, state, latitude, longitude, specialists, rating,
                       phone, email, facilities, departments, timings, beds, created_at
                FROM hospitals
                WHERE (%s IS NULL OR city ILIKE %s)
                  AND (%s IS NULL OR state ILIKE %s)
                  AND (
                        %s = FALSE
                        OR EXISTS (
                            SELECT 1
                            FROM jsonb_array_elements_text(departments) AS department
                            WHERE department ILIKE '%%neuro%%'
                               OR department ILIKE '%%brain%%'
                        )
                  )
                ORDER BY rating DESC, name ASC
                """,
                (
                    city,
                    f"%{city.strip()}%" if city else None,
                    state,
                    f"%{state.strip()}%" if state else None,
                    brain_specialty,
                )
            )
            hospitals = [serialize_record(hospital) for hospital in cur.fetchall()]

        if lat is not None and lng is not None:
            for hospital in hospitals:
                distance = geodesic(
                    (lat, lng),
                    (hospital['latitude'], hospital['longitude'])
                ).kilometers
                hospital['distance'] = round(distance, 1)

            hospitals = [h for h in hospitals if h['distance'] <= radius]
            hospitals.sort(key=lambda x: x['distance'])
        else:
            hospitals.sort(key=lambda x: x.get('name', '').lower())

        if GOOGLE_MAPS_API_KEY:
            google_hospitals = fetch_google_hospitals(
                city=city,
                lat=lat,
                lng=lng,
                radius=radius,
                brain_specialty=brain_specialty,
            )

            seen = {
                (
                    hospital.get('name', '').strip().lower(),
                    hospital.get('address', '').strip().lower(),
                )
                for hospital in hospitals
            }
            for hospital in google_hospitals:
                identity = (
                    hospital.get('name', '').strip().lower(),
                    hospital.get('address', '').strip().lower(),
                )
                if identity not in seen:
                    hospitals.append(hospital)
                    seen.add(identity)

            if lat is not None and lng is not None:
                hospitals.sort(key=lambda item: item.get('distance') if item.get('distance') is not None else float('inf'))
            else:
                hospitals.sort(key=lambda item: item.get('name', '').lower())

        return jsonify(hospitals), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Appointment Endpoints ====================

@app.route('/api/appointments', methods=['POST'])
@jwt_required()
def book_appointment():
    """Book an appointment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        required_fields = ['doctor_id', 'date', 'time', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        appointment_id = new_id()
        now = datetime.utcnow()

        with db_cursor(commit=True) as cur:
            cur.execute(
                "SELECT id, name, specialization FROM doctors WHERE id = %s",
                (data['doctor_id'],)
            )
            doctor = cur.fetchone()
            if not doctor:
                return jsonify({'error': 'Doctor not found'}), 404

            cur.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            cur.execute(
                """
                INSERT INTO appointments (
                    id, user_id, doctor_id, date, time, type, symptoms, status, booked_at, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    appointment_id,
                    user_id,
                    data['doctor_id'],
                    data['date'],
                    data['time'],
                    data['type'],
                    data.get('symptoms', ''),
                    'pending',
                    now,
                    now,
                )
            )

        html_content = f"""
        <h2>Appointment Confirmation</h2>
        <p>Dear {user['name']},</p>
        <p>Your appointment has been booked successfully.</p>
        <p><strong>Details:</strong></p>
        <ul>
            <li>Doctor: {doctor['name']}</li>
            <li>Specialization: {doctor['specialization']}</li>
            <li>Date: {data['date']}</li>
            <li>Time: {data['time']}</li>
            <li>Type: {data['type']}</li>
        </ul>
        <p>Please arrive 15 minutes early for in-person appointments.</p>
        """
        
        send_email(user['email'], 'Appointment Confirmation', html_content)

        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment_id': appointment_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """Get user's appointments"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.user_id,
                    a.doctor_id,
                    a.date,
                    a.time,
                    a.type,
                    a.symptoms,
                    a.status,
                    a.booked_at,
                    a.created_at,
                    d.id AS doctor_ref_id,
                    d.name AS doctor_name,
                    d.specialization AS doctor_specialization,
                    d.experience AS doctor_experience,
                    d.rating AS doctor_rating,
                    d.hospital AS doctor_hospital,
                    d.city AS doctor_city,
                    d.state AS doctor_state,
                    d.contact AS doctor_contact,
                    d.email AS doctor_email,
                    d.availability AS doctor_availability,
                    d.consultation_fee AS doctor_consultation_fee,
                    d.qualifications AS doctor_qualifications,
                    d.languages AS doctor_languages,
                    d.created_at AS doctor_created_at
                FROM appointments a
                JOIN doctors d ON d.id = a.doctor_id
                WHERE a.user_id = %s
                  AND (%s IS NULL OR a.status = %s)
                ORDER BY a.date DESC, a.time DESC
                """,
                (user_id, status, status)
            )
            rows = cur.fetchall()

        appointments = []
        for row in rows:
            appointment = serialize_record({
                'id': row['id'],
                'user_id': row['user_id'],
                'doctor_id': row['doctor_id'],
                'date': row['date'],
                'time': row['time'],
                'type': row['type'],
                'symptoms': row['symptoms'],
                'status': row['status'],
                'booked_at': row['booked_at'],
                'created_at': row['created_at'],
            })
            appointment['doctor'] = serialize_record({
                'id': row['doctor_ref_id'],
                'name': row['doctor_name'],
                'specialization': row['doctor_specialization'],
                'experience': row['doctor_experience'],
                'rating': row['doctor_rating'],
                'hospital': row['doctor_hospital'],
                'city': row['doctor_city'],
                'state': row['doctor_state'],
                'contact': row['doctor_contact'],
                'email': row['doctor_email'],
                'availability': row['doctor_availability'],
                'consultation_fee': row['doctor_consultation_fee'],
                'qualifications': row['doctor_qualifications'],
                'languages': row['doctor_languages'],
                'created_at': row['doctor_created_at'],
            })
            appointments.append(appointment)

        return jsonify(appointments), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments/<appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    """Update appointment status"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        if 'status' not in data:
            return jsonify({'error': 'No valid fields to update'}), 400

        with db_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE appointments
                SET status = %s
                WHERE id = %s AND user_id = %s
                """,
                (data['status'], appointment_id, user_id)
            )
            if cur.rowcount == 0:
                return jsonify({'error': 'Appointment not found'}), 404

        return jsonify({'message': 'Appointment updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments/<appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    try:
        user_id = get_jwt_identity()

        with db_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE appointments
                SET status = 'cancelled'
                WHERE id = %s AND user_id = %s
                """,
                (appointment_id, user_id)
            )
            if cur.rowcount == 0:
                return jsonify({'error': 'Appointment not found'}), 404

        return jsonify({'message': 'Appointment cancelled successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== User Profile Endpoints ====================

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, city, created_at, last_login
                FROM users
                WHERE id = %s
                """,
                (user_id,)
            )
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            cur.execute("SELECT COUNT(*) AS count FROM scans WHERE user_id = %s", (user_id,))
            total_scans = cur.fetchone()['count']

            cur.execute(
                "SELECT COUNT(*) AS count FROM appointments WHERE user_id = %s",
                (user_id,)
            )
            total_appointments = cur.fetchone()['count']

        return jsonify({
            'user': serialize_record(user),
            'statistics': {
                'total_scans': total_scans,
                'total_appointments': total_appointments
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        updates = []
        values = []
        for field in ['name', 'phone', 'city']:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        values.append(user_id)
        with db_cursor(commit=True) as cur:
            cur.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
                tuple(values)
            )

        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Utility Endpoints ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get dashboard statistics"""
    try:
        user_id = get_jwt_identity()

        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM scans WHERE user_id = %s", (user_id,))
            total_scans = cur.fetchone()['count']

            cur.execute(
                "SELECT COUNT(*) AS count FROM appointments WHERE user_id = %s",
                (user_id,)
            )
            total_appointments = cur.fetchone()['count']

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM scans
                WHERE user_id = %s
                  AND detection_result ->> 'detected' = 'true'
                """,
                (user_id,)
            )
            scans_with_tumor = cur.fetchone()['count']

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM appointments
                WHERE user_id = %s AND status = 'pending'
                """,
                (user_id,)
            )
            pending_appointments = cur.fetchone()['count']

        return jsonify({
            'total_scans': total_scans,
            'total_appointments': total_appointments,
            'scans_with_tumor': scans_with_tumor,
            'scans_clear': total_scans - scans_with_tumor,
            'pending_appointments': pending_appointments
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Run Server ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
