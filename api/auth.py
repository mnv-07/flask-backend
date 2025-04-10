from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import logging

auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

mongo = None  # Global variable for MongoDB

def init_mongo(app):
    """Initialize MongoDB with Flask app."""
    global mongo
    try:
        mongo = PyMongo(app)
        logger.info("MongoDB initialized successfully for auth")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB for auth: {str(e)}")
        raise

@auth_blueprint.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        if mongo.db.users.find_one({"email": email}):
            return jsonify({"message": "User already exists"}), 409

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            "email": email,
            "password": hashed_password
        })

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """Authenticate user login."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"message": "Invalid email or password"}), 401

        if check_password_hash(user['password'], password):
            return jsonify({
                "message": "Login successful",
                "email": email
            }), 200
        return jsonify({"message": "Invalid email or password"}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@auth_blueprint.route('/verify_password', methods=['POST'])
def verify_password():
    """Verify old password before allowing password change."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"message": "User not found"}), 404

        if check_password_hash(user['password'], password):
            return jsonify({"message": "Password verified"}), 200
        return jsonify({"message": "Incorrect password"}), 401
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@auth_blueprint.route('/change_password', methods=['POST'])
def change_password():
    """Update user password after verification."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get("email")
        new_password = data.get("new_password")

        if not email or not new_password:
            return jsonify({"message": "Missing email or new password"}), 400

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"message": "User not found"}), 404

        hashed_password = generate_password_hash(new_password)
        result = mongo.db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Password updated successfully"}), 200
        else:
            return jsonify({"message": "Failed to update password"}), 500
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

