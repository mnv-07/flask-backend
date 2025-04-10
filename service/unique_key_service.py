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

mongo = None
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-here').encode()
SALT = os.getenv('SALT', 'your-salt-here').encode()

def init_mongo(app):
    global mongo
    try:
        mongo = PyMongo(app)
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise

def generate_unique_key():
    return ''.join(random.choices(string.digits, k=10))

def get_fernet():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
    return Fernet(key)

def encrypt_key(key):
    try:
        f = get_fernet()
        return f.encrypt(key.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise

def decrypt_key(encrypted_key):
    try:
        f = get_fernet()
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise

@key_blueprint.route('/generate_key', methods=['POST'])
def generate_key():
    try:
        if mongo is None:
            return jsonify({"error": "Database not initialized"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get('email')
        name = data.get('name')

        if not email:
            return jsonify({"error": "Email is required"}), 400

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
        return jsonify({"error": "Internal server error"}), 500

@key_blueprint.route('/connect_users', methods=['POST'])
def connect_users():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user1_key = data.get("user1_key")
        user2_key = data.get("user2_key")

        if not user1_key or not user2_key:
            return jsonify({"error": "Both keys are required"}), 400

        user1 = mongo.db.users.find_one({"unique_key": encrypt_key(user1_key)})
        user2 = mongo.db.users.find_one({"unique_key": encrypt_key(user2_key)})

        if not user1 or not user2:
            return jsonify({"error": "Invalid key(s)"}), 401

        user1_email = user1["email"]
        user2_email = user2["email"]

        if user2_email in user1.get("connected_users", []):
            return jsonify({"message": "Users are already connected"}), 200

        mongo.db.users.update_one(
            {"email": user2_email},
            {"$addToSet": {"pending_requests": user1_email}}
        )
        return jsonify({"message": "Connection request sent"}), 200
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@key_blueprint.route('/accept_request', methods=['POST'])
def accept_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_key = data.get("user_key")
        requester_email = data.get("requester_email")

        if not user_key or not requester_email:
            return jsonify({"error": "User key and requester email are required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"error": "Invalid user key"}), 401

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
        return jsonify({"error": "Internal server error"}), 500

@key_blueprint.route('/reject_request', methods=['POST'])
def reject_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_key = data.get("user_key")
        requester_email = data.get("requester_email")

        if not user_key or not requester_email:
            return jsonify({"error": "User key and requester email are required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"error": "Invalid user key"}), 401

        mongo.db.users.update_one(
            {"email": user["email"]},
            {"$pull": {"pending_requests": requester_email}}
        )
        return jsonify({"message": "Request rejected"}), 200
    except Exception as e:
        logger.error(f"Reject request error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@key_blueprint.route('/get_connected_users', methods=['POST'])
def get_connected_users():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_key = data.get("user_key")
        if not user_key:
            return jsonify({"error": "User key is required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"error": "Invalid user key"}), 401

        connected_users = user.get("connected_users", [])
        return jsonify({"connected_users": connected_users}), 200
    except Exception as e:
        logger.error(f"Get connected users error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@key_blueprint.route('/get_pending_requests', methods=['POST'])
def get_pending_requests():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_key = data.get("user_key")
        if not user_key:
            return jsonify({"error": "User key is required"}), 400

        user = mongo.db.users.find_one({"unique_key": encrypt_key(user_key)})
        if not user:
            return jsonify({"error": "Invalid user key"}), 401

        pending_requests = user.get("pending_requests", [])
        return jsonify({"pending_requests": pending_requests}), 200
    except Exception as e:
        logger.error(f"Get pending requests error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
