import os
import cloudinary
import cloudinary.uploader
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key    = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id                      SERIAL PRIMARY KEY,
            name                    TEXT NOT NULL,
            category                TEXT NOT NULL,
            location                TEXT NOT NULL,
            description             TEXT,
            whatsapp                TEXT,
            image_url               TEXT,
            public_id               TEXT,
            trial_started_at        TIMESTAMP DEFAULT NOW(),
            subscription_status     TEXT DEFAULT 'trial',
            subscription_expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days'),
            views                   INTEGER DEFAULT 0,
            whatsapp_taps           INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def home():
    return "Bantaba API is running"

@app.route("/businesses")
def get_businesses():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM businesses
        WHERE subscription_status IN ('trial', 'active')
        ORDER BY id DESC
    """)
    businesses = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(b) for b in businesses])

@app.route("/add-business", methods=["POST"])
def add_business():
    name        = request.form.get('name')
    category    = request.form.get('category')
    location    = request.form.get('location')
    description = request.form.get('description', '')
    whatsapp    = request.form.get('whatsapp', '')
    file        = request.files.get('file')

    if not name or not category or not location:
        return jsonify({"error": "Name, category and location required"}), 400

    image_url = None
    public_id = None

    if file:
        result = cloudinary.uploader.upload(
            file, folder="bantaba", resource_type="image"
        )
        image_url = result.get('secure_url')
        public_id = result.get('public_id')

    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO businesses
           (name, category, location, description, whatsapp, image_url, public_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (name, category, location, description, whatsapp, image_url, public_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Business added"}), 201

init_db()

if __name__ == "__main__":
    app.run(debug=True)
