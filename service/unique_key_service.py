import random
import string
from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import logging

key_blueprint = Blueprint('key', __name__)
logger = logging.getLogger(__name__)

mongo = None  # Global MongoDB connection

# Get encryption key and salt from environment variables
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-here').encode()
SALT = os.getenv('SALT', 'your-salt-here').encode()

def init_mongo(app):
    """Initialize MongoDB connection with Flask app."""
    global mongo
    try:
        mongo = PyMongo(app)
        logger.info("MongoDB initialized successfully for key service")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB for key service: {str(e)}")
        raise

def generate_unique_key():
    """Generate a random 10-digit unique key."""
    return ''.join(random.choices(string.digits, k=10))

def get_fernet():
    """Create a Fernet instance with the derived key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
    return Fernet(key)

def encrypt_key(key):
    """Encrypt the unique key before storing."""
    try:
        f = get_fernet()
        return f.encrypt(key.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise

def decrypt_key(encrypted_key):
    """Decrypt the unique key when retrieving."""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise

@key_blueprint.route('/generate_key', methods=['POST'])
def generate_key():
    """Generate and store a 10-digit key for a user upon login."""
    try:
        if mongo is None:
            logger.error("Database not initialized")
            return jsonify({"message": "Database not initialized"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get('email')
        name = data.get('name')

        if not email:
            return jsonify({"message": "Email is required"}), 400

        unique_key = generate_unique_key()
        encrypted_key = encrypt_key(unique_key)

        mongo.db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "unique_key": encrypted_key,
                    "name": name
                },
                "$setOnInsert": {
                    "connected_users": [],
                    "pending_requests": []
                }
            },
            upsert=True
        )
        return jsonify({
            "message": "Key generated successfully",
            "key": unique_key
        }), 200
    except Exception as e:
        logger.error(f"Key generation error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@key_blueprint.route('/connect_users', methods=['POST'])
def connect_users():
    """Send a connection request to another user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        user1_key = data.get("user1_key")
        user2_key = data.get("user2_key")

        if not user1_key or not user2_key:
            return jsonify({"message": "Both keys are required"}), 400

        # Find users by their keys
        user1 = mongo.db.users.find_one({"unique_key": encrypt_key(user1_key)})
        user2 = mongo.db.users.find_one({"unique_key": encrypt_key(user2_key)})

        if not user1 or not user2:
            return jsonify({"message": "Invalid key(s)"}), 401

        user1_email = user1["email"]
        user2_email = user2["email"]

        # Check if already connected
        if user2_email in user1.get("connected_users", []):
            return jsonify({"message": "Users are already connected"}), 200

        # Add to pending requests
        mongo.db.users.update_one(
            {"email": user2_email},
            {"$addToSet": {"pending_requests": user1_email}}
        )
        return jsonify({"message": "Connection request sent"}), 200
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@key_blueprint.route('/accept_request', methods=['POST'])
def accept_request():
    """Accept a connection request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        user_key = data.get("user_key")
        requester_email = data.get("requester_email")

        if not user_key or not requester_email:
            return jsonify({"message": "User key and requester email are required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"message": "Invalid user key"}), 401

        # Remove from pending and add to connected
        mongo.db.users.update_one(
            {"email": user["email"]},
            {
                "$pull": {"pending_requests": requester_email},
                "$addToSet": {"connected_users": requester_email}
            }
        )
        return jsonify({"message": "Request accepted"}), 200
    except Exception as e:
        logger.error(f"Accept request error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@key_blueprint.route('/reject_request', methods=['POST'])
def reject_request():
    """Reject a connection request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        user_key = data.get("user_key")
        requester_email = data.get("requester_email")

        if not user_key or not requester_email:
            return jsonify({"message": "User key and requester email are required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"message": "Invalid user key"}), 401

        mongo.db.users.update_one(
            {"email": user["email"]},
            {"$pull": {"pending_requests": requester_email}}
        )
        return jsonify({"message": "Request rejected"}), 200
    except Exception as e:
        logger.error(f"Reject request error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@key_blueprint.route('/get_connected_users', methods=['POST'])
def get_connected_users():
    """Get list of connected users."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        user_key = data.get("user_key")
        if not user_key:
            return jsonify({"message": "User key is required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"message": "Invalid user key"}), 401

        connected_users = user.get("connected_users", [])
        return jsonify({"connected_users": connected_users}), 200
    except Exception as e:
        logger.error(f"Get connected users error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@key_blueprint.route('/get_pending_requests', methods=['POST'])
def get_pending_requests():
    """Get list of pending connection requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        user_key = data.get("user_key")
        if not user_key:
            return jsonify({"message": "User key is required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"message": "Invalid user key"}), 401

        pending_requests = user.get("pending_requests", [])
        return jsonify({"pending_requests": pending_requests}), 200
    except Exception as e:
        logger.error(f"Get pending requests error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
