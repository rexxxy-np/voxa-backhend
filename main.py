from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt, hashlib, os, json, datetime

app = Flask(__name__)
CORS(app)
SECRET = "voxa-secret-key-change-later"

# Simple file-based user storage (no database needed yet)
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return jsonify({"message": "Voxa Backend is live! 🎵"})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    username = data.get('username', '')
    if not email or not password or not username:
        return jsonify({"error": "All fields required"}), 400
    users = load_users()
    if email in users:
        return jsonify({"error": "Email already registered"}), 409
    users[email] = {"username": username, "password": hash_pw(password)}
    save_users(users)
    token = jwt.encode({"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)}, SECRET, algorithm="HS256")
    return jsonify({"token": token, "username": username})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    users = load_users()
    user = users.get(email)
    if not user or user['password'] != hash_pw(password):
        return jsonify({"error": "Invalid email or password"}), 401
    token = jwt.encode({"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)}, SECRET, algorithm="HS256")
    return jsonify({"token": token, "username": user['username']})

if __name__ == '__main__':
    app.run(debug=True)
