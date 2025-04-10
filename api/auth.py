from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import logging

auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

mongo = None

def init_mongo(app):
    global mongo
    try:
        mongo = PyMongo(app)
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise

@auth_blueprint.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not all([email, password, name]):
            return jsonify({"error": "Email, password, and name are required"}), 400

        if mongo.db.users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 409

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            "email": email,
            "password": hashed_password,
            "name": name,
            "connected_users": [],
            "pending_requests": []
        })

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_blueprint.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({
            "message": "Login successful",
            "email": user['email'],
            "name": user.get('name', '')
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_blueprint.route('/verify_password', methods=['POST'])
def verify_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user['password'], password):
            return jsonify({"error": "Incorrect password"}), 401

        return jsonify({"message": "Password verified"}), 200
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_blueprint.route('/change_password', methods=['POST'])
def change_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get("email")
        new_password = data.get("new_password")

        if not email or not new_password:
            return jsonify({"error": "Email and new password required"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404

        hashed_password = generate_password_hash(new_password)
        result = mongo.db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Password updated successfully"}), 200
        return jsonify({"error": "Failed to update password"}), 500
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

