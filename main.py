import os, hashlib, datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)
SECRET = "voxa-secret-key-change-later"
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return jsonify({"message": "Voxa Backend is live!"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    username = data.get('username', '')
    if not email or not password or not username:
        return jsonify({"error": "All fields required"}), 400
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
                    (email, username, hash_pw(password)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    token = jwt.encode({"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)}, SECRET, algorithm="HS256")
    return jsonify({"token": token, "username": username})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (email, hash_pw(password)))
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    token = jwt.encode({"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)}, SECRET, algorithm="HS256")
    return jsonify({"token": token, "username": user['username']})

init_db()
@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "No token"}), 401
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        email = payload['email']
    except:
        return jsonify({"error": "Invalid token"}), 401
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT email, username, created_at FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "email": user['email'],
        "username": user['username'],
        "created_at": str(user['created_at'])
    })
    import subprocess, tempfile, os

@app.route('/soundcloud/search', methods=['GET'])
def sc_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query required"}), 400
    try:
        result = subprocess.run([
            'yt-dlp',
            f'scsearch10:{query}',
            '--dump-json',
            '--flat-playlist',
            '--no-download'
        ], capture_output=True, text=True, timeout=30)
        tracks = []
        for line in result.stdout.strip().split('\n'):
            if line:
                import json
                try:
                    t = json.loads(line)
                    tracks.append({
                        'id': t.get('id',''),
                        'title': t.get('title',''),
                        'uploader': t.get('uploader',''),
                        'duration': t.get('duration',0),
                        'url': t.get('url',''),
                        'thumbnail': t.get('thumbnail','')
                    })
                except: pass
        return jsonify(tracks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/soundcloud/download', methods=['GET'])
def sc_download():
    url = request.args.get('url', '')
    if not url:
        return jsonify({"error": "URL required"}), 400
    try:
        result = subprocess.run([
            'yt-dlp',
            '-f', 'bestaudio',
            '--get-url',
            url
        ], capture_output=True, text=True, timeout=30)
        audio_url = result.stdout.strip()
        if not audio_url:
            return jsonify({"error": "Could not get audio URL"}), 500
        return jsonify({"url": audio_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
