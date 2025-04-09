from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

auth_blueprint = Blueprint('auth', __name__)

mongo = None  # Global variable for MongoDB

def init_mongo(app):
    """Initialize MongoDB with Flask app."""
    global mongo
    mongo = PyMongo(app)

@auth_blueprint.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    mongo.db.users.insert_one({"email": email, "password": hashed_password})

    return jsonify({"message": "User registered successfully"}), 201

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """Authenticate user login."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = mongo.db.users.find_one({"email": email})
    if user and check_password_hash(user['password'], password):
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid email or password"}), 401

@auth_blueprint.route('/verify_password', methods=['POST'])
def verify_password():
    """Verify old password before allowing password change."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if user and check_password_hash(user['password'], password):
        return jsonify({"message": "Password verified"}), 200
    return jsonify({"message": "Incorrect password"}), 401

@auth_blueprint.route('/change_password', methods=['POST'])
def change_password():
    """Update user password after verification."""
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        return jsonify({"error": "Missing email or new password"}), 400

    # **Find user in DB**
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # **Hash new password**
    hashed_password = generate_password_hash(new_password)

    # **Update the password**
    result = mongo.db.users.update_one(
        {"email": email}, 
        {"$set": {"password": hashed_password}}
    )

    if result.modified_count == 1:
        return jsonify({"message": "Password updated successfully"}), 200
    else:
        return jsonify({"error": "Failed to update password"}), 500

