from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DATABASE = 'database.db'

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

    if result is None or result[1] != password:
        return jsonify({'message': 'Invalid username or password'}), 401

    user_id = result[0]
    return jsonify({'message': f'User logged in successfully. User ID: {user_id}'}), 200

@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    username, password = data['username'], data['password']

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    if result is not None:
        return jsonify({'message': 'Username already exists'}), 409

    # Insert the new user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'}), 201


def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create User table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE NOT NULL,
                       password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run()
    create_tables()



