from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import json

app = Flask(__name__)
CORS(app)

DATABASE = 'database.db'
ALLOWED_USERTYPES = ['admin', 'alumni', 'external']

@app.route('/')
def hello():
    return jsonify({'message': 'Email already exists”'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data['username'], data['password']

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Retrieve the user from the database
    cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    try:
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if result is None or result[1] != hashed_password:
            raise Exception('Invalid username or password')
    except:
        return jsonify({'message': 'Invalid username or password'}), 401

    user_id = result[0]
    return jsonify({'message': f'User logged in successfully. User ID: {user_id}'}), 200

@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    username, password, user_type = data['username'], data['password'], data['user_type']

    if not username or not password or not user_type:
        return jsonify({'message': 'Missing username, password or user type'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    if result is not None:
        return jsonify({'message': 'Username already exists'}), 409
    
    if user_type not in ALLOWED_USERTYPES:
        return jsonify({'message': 'Invalid user type'}), 400
    
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Insert the new user into the database
    cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)", (username, hashed_password, user_type))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

''' 
Get user
This method can be used to let users download and acess their transcripts
'''

@app.route("/user", methods=['GET'])
def get_user():
    username = request.args.get('username')
    print(username)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return None

    user = {
        'id': result[0],
        'username': result[1],
        'user_type': result[3],
        'transcript_link': result[4],
        'graduate_certificate_link': result[5],
        'unique_certificate_number': result[6]
    }

    return user

# Update user
@app.route("/user", methods=['PUT'])
def update_user():
    data = request.get_json()
    try:

        username, transcript_link, graduate_certificate_link, unique_certificate_number = data['username'], data['transcript_link'], data['graduate_certificate_link'], data['unique_certificate_number']

        if not username or not transcript_link or not graduate_certificate_link or not unique_certificate_number:
            return jsonify({'message': 'Missing username, transcript link, graduate certificate link or unique certificate number'}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET transcript_link=?, graduate_certificate_link=?, unique_certificate_number=? WHERE username=?", (transcript_link, graduate_certificate_link, unique_certificate_number, username))
        conn.commit()
        conn.close()
    except:
        return jsonify({'message': 'Missing username, transcript link, graduate certificate link or unique certificate number'}), 400

    return jsonify({'message': 'User updated successfully'}), 200

''' 
Verify certificate
Method works by passing in a QP of ucn to the url
The method will then check if the ucn exists in the database
and return the user if it does
'''

@app.route("/verify", methods=['GET'])
def verify_certificate():
    unique_certificate_number = request.args.get('ucn')
    print(unique_certificate_number)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE unique_certificate_number=?", (unique_certificate_number,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return jsonify({'message': 'Certificate not found'}), 404

    user = {
        'username': result[1],
        'graduate_certificate_link': result[5],
        'unique_certificate_number': result[6]
    }

    return jsonify(user), 200

@app.route("/transcript", methods=['GET'])
def get_transcript():
    username = request.args.get('username')
    
    file_path = 'data/transcripts.json'
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for d in data['transcripts']:
        if d['username'] == username:
            transcript = jsonify(d)

    if transcript is None:
        return jsonify({'message': 'Transcript not found'}), 404

    return transcript, 200

@app.route("/certificate", methods=['GET'])
def get_certificate():
    username = request.args.get('username')
    
    file_path = 'data/certificates.json'
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for d in data['certificates']:
        if d['username'] == username:
            certificate = jsonify(d)

    if certificate is None:
        return jsonify({'message': 'Certificate not found'}), 404

    return certificate, 200


def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create User table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE NOT NULL,
                       password TEXT NOT NULL,
                       user_type TEXT NOT NULL,
                       transcript_link TEXT,
                       graduate_certificate_link TEXT,
                       unique_certificate_number TEXT
                       )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run()
    create_tables()



