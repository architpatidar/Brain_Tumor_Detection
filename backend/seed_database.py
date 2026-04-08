from datetime import datetime
import os
from pathlib import Path
import uuid

from dotenv import load_dotenv
from psycopg import connect
from psycopg.types.json import Jsonb

load_dotenv(Path(__file__).with_name('.env'))

DATABASE_URL = os.environ.get(
    'DATABASE_URL',''
)


def get_connection():
    return connect(DATABASE_URL)


def init_db(cur):
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
    ]

    for statement in statements:
        cur.execute(statement)
    cur.execute("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS state TEXT DEFAULT ''")
    cur.execute("ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS state TEXT DEFAULT ''")


def new_id():
    return str(uuid.uuid4())


def doctors_data():
    now = datetime.utcnow()
    return [
        {
            'id': new_id(), 'name': 'Dr. Amit Verma', 'specialization': 'Neurologist', 'experience': 18,
            'rating': 4.9, 'hospital': 'AIIMS Jaipur', 'city': 'Jaipur', 'state': 'Rajasthan',
            'contact': '+91-141-2652001', 'email': 'amit.verma@aiimsjaipur.example',
            'availability': ['Mon', 'Wed', 'Fri'], 'consultation_fee': 1200,
            'qualifications': ['MBBS', 'MD Neurology', 'DM Neurology'],
            'languages': ['Hindi', 'English'], 'created_at': now,
        },
        {
            'id': new_id(), 'name': 'Dr. Sneha Sharma', 'specialization': 'Neurosurgeon', 'experience': 14,
            'rating': 4.8, 'hospital': 'Fortis Hospital Jaipur', 'city': 'Jaipur', 'state': 'Rajasthan',
            'contact': '+91-141-2547001', 'email': 'sneha.sharma@fortisjaipur.example',
            'availability': ['Tue', 'Thu', 'Sat'], 'consultation_fee': 1500,
            'qualifications': ['MBBS', 'MS General Surgery', 'MCh Neurosurgery'],
            'languages': ['Hindi', 'English'], 'created_at': now,
        },
        {
            'id': new_id(), 'name': 'Dr. Rakesh Meena', 'specialization': 'Neurologist', 'experience': 11,
            'rating': 4.7, 'hospital': 'Apollo Hospital Jaipur', 'city': 'Jaipur', 'state': 'Rajasthan',
            'contact': '+91-141-2566667', 'email': 'rakesh.meena@apollojaipur.example',
            'availability': ['Mon', 'Tue', 'Thu', 'Fri'], 'consultation_fee': 1000,
            'qualifications': ['MBBS', 'MD Medicine', 'DM Neurology'],
            'languages': ['Hindi', 'English', 'Rajasthani'], 'created_at': now,
        },
    ]


def hospitals_data():
    now = datetime.utcnow()
    return [
        {
            'id': new_id(), 'name': 'AIIMS Jaipur', 'address': 'Basni Industrial Area, Jodhpur Road, Jaipur',
            'city': 'Jaipur', 'state': 'Rajasthan', 'latitude': 26.7829, 'longitude': 75.8637,
            'specialists': 12, 'rating': 4.9, 'phone': '+91-141-2652000',
            'email': 'info@aiimsjaipur.example',
            'facilities': ['MRI', 'CT Scan', 'ICU', 'Emergency', 'Neuro Rehab'],
            'departments': ['Neurology', 'Neurosurgery', 'Radiology', 'Oncology'],
            'timings': '24x7', 'beds': 800, 'created_at': now,
        },
        {
            'id': new_id(), 'name': 'Fortis Hospital Jaipur', 'address': 'Jawahar Lal Nehru Marg, Malviya Nagar, Jaipur',
            'city': 'Jaipur', 'state': 'Rajasthan', 'latitude': 26.8543, 'longitude': 75.8152,
            'specialists': 9, 'rating': 4.7, 'phone': '+91-141-2547000',
            'email': 'contact@fortisjaipur.example',
            'facilities': ['MRI', 'ICU', 'Emergency', 'Laboratory'],
            'departments': ['Neurology', 'Neurosurgery', 'Critical Care'],
            'timings': '24x7', 'beds': 300, 'created_at': now,
        },
        {
            'id': new_id(), 'name': 'Apollo Hospital Jaipur', 'address': 'Sector 26, Pratap Nagar, Jaipur',
            'city': 'Jaipur', 'state': 'Rajasthan', 'latitude': 26.8039, 'longitude': 75.8243,
            'specialists': 8, 'rating': 4.8, 'phone': '+91-141-2566666',
            'email': 'support@apollojaipur.example',
            'facilities': ['MRI', 'CT Scan', 'Emergency', 'Pharmacy'],
            'departments': ['Neurology', 'Neurosurgery', 'Oncology'],
            'timings': '24x7', 'beds': 250, 'created_at': now,
        },
    ]


def seed_doctors(cur):
    cur.execute('DELETE FROM appointments')
    cur.execute('DELETE FROM doctors')
    for doctor in doctors_data():
        cur.execute(
            """
            INSERT INTO doctors (
                id, name, specialization, experience, rating, hospital, city, state,
                contact, email, availability, consultation_fee, qualifications, languages, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                doctor['id'],
                doctor['name'],
                doctor['specialization'],
                doctor['experience'],
                doctor['rating'],
                doctor['hospital'],
                doctor['city'],
                doctor['state'],
                doctor['contact'],
                doctor['email'],
                Jsonb(doctor['availability']),
                doctor['consultation_fee'],
                Jsonb(doctor['qualifications']),
                Jsonb(doctor['languages']),
                doctor['created_at'],
            )
        )
    print(f"Inserted {len(doctors_data())} Jaipur doctors")


def seed_hospitals(cur):
    cur.execute('DELETE FROM hospitals')
    for hospital in hospitals_data():
        cur.execute(
            """
            INSERT INTO hospitals (
                id, name, address, city, state, latitude, longitude, specialists, rating,
                phone, email, facilities, departments, timings, beds, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                hospital['id'],
                hospital['name'],
                hospital['address'],
                hospital['city'],
                hospital['state'],
                hospital['latitude'],
                hospital['longitude'],
                hospital['specialists'],
                hospital['rating'],
                hospital['phone'],
                hospital['email'],
                Jsonb(hospital['facilities']),
                Jsonb(hospital['departments']),
                hospital['timings'],
                hospital['beds'],
                hospital['created_at'],
            )
        )
    print(f"Inserted {len(hospitals_data())} Jaipur hospitals")


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            init_db(cur)
            seed_doctors(cur)
            seed_hospitals(cur)
        conn.commit()
    print('PostgreSQL seeding completed successfully')


if __name__ == '__main__':
    main()
