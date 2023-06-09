from flask import Flask, jsonify, request #, session
from flask_cors import CORS
import sqlite3
import hashlib
import json

app = Flask(__name__)
# app.secret_key = 'super-secret-key'
# app.config['SESSION_COOKIE_HTTPONLY'] = False
# app.config["SESSION_PERMANENT"] = True
CORS(app)

DATABASE = 'database.db'
ALLOWED_USERTYPES = ['admin', 'alumni', 'external']

@app.route('/')
def hello():
    file_path = 'data/api.json'
    with open(file_path, 'r') as file:
        data = json.load(file)

    return jsonify(data), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data['username'], data['password']

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Retrieve the user from the database
    cursor.execute("SELECT id, password, user_type FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    try:
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if result is None or result[1] != hashed_password:
            raise Exception('Invalid username or password')
    except:
        return jsonify({'message': 'Invalid username or password'}), 401

    user_id = result[0]
    user_type = result[2]
    # session['user_type'] = user_type
    # session['username'] = username
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
        'name': result[4],
        'email': result[5],
        'transcript_link': result[6],
        'graduate_certificate_link': result[7],
        'unique_certificate_number': result[8]
    }

    return user

# Update user
@app.route("/user", methods=['PUT'])
def update_user():
    data = request.get_json()

    # if 'user_type' in session:
    #     if session['user_type'] != 'admin':
    #         return jsonify({'message': 'Unauthorized. Not an admin.', 'session': session}), 401
    # else:
    #     return jsonify({'message': 'Unauthorized. Not logged in.', 'session': session}), 401

    try:

        username, email, name, transcript_link, graduate_certificate_link, unique_certificate_number = data['username'], data['email'], data['name'], data['transcript_link'], data['graduate_certificate_link'], data['unique_certificate_number']

        if not username or not transcript_link or not graduate_certificate_link or not unique_certificate_number or not email or not name:
            return jsonify({'message': 'Missing username, email, name, transcript link, graduate certificate link or unique certificate number'}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET email=?, name=?, transcript_link=?, graduate_certificate_link=?, unique_certificate_number=? WHERE username=?", (email, name, transcript_link, graduate_certificate_link, unique_certificate_number, username))
        conn.commit()
        conn.close()
    except:
        return jsonify({'message': 'Missing username, email, name, transcript link, graduate certificate link or unique certificate number'}), 400

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
    transcript = None
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
    certificate = None
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
                       name TEXT,
                       email TEXT,
                       transcript_link TEXT,
                       graduate_certificate_link TEXT,
                       unique_certificate_number TEXT
                       )''')
    conn.commit()
    conn.close()

    print("Table 'users' created")

if __name__ == '__main__':
    app.run()
    print('Server running on port 5000')
    create_tables()



