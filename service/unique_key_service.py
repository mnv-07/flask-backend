import random
import string
from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

key_blueprint = Blueprint('key', __name__)
mongo = None  # Global MongoDB connection

def init_mongo(app):
    """Initialize MongoDB connection with Flask app."""
    global mongo
    mongo = PyMongo(app)

def generate_unique_key():
    """Generate a random 10-digit unique key."""
    return ''.join(random.choices(string.digits, k=10))

@key_blueprint.route('/generate_key', methods=['POST'])
def generate_key():
    """Generate and store a 10-digit key for a user upon login."""
    global mongo
    if mongo is None:
        return jsonify({"message": "Database not initialized"}), 500

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    unique_key = generate_unique_key()
    hashed_key = generate_password_hash(unique_key)

    try:
        mongo.db.users.update_one(
            {"email": email},
            {"$set": {"unique_key": hashed_key}, "$setOnInsert": {"connected_users": [], "pending_requests": []}},
            upsert=True
        )
        return jsonify({"message": "Key generated successfully", "key": unique_key}), 200
    except Exception as e:
        return jsonify({"message": f"Database error: {e}"}), 500

@key_blueprint.route('/request_connection', methods=['POST'])
def request_connection():
    """Send a connection request to another user."""
    data = request.get_json()
    sender_email = data.get("sender_email")
    receiver_key = data.get("receiver_key")

    if not sender_email or not receiver_key:
        return jsonify({"message": "Both sender email and receiver key are required"}), 400

    receiver = mongo.db.users.find_one({"unique_key": receiver_key})
    if not receiver:
        return jsonify({"message": "Invalid unique key"}), 401

    receiver_email = receiver["email"]

    if sender_email in receiver.get("connected_users", []):
        return jsonify({"message": "Users are already connected"}), 200

    mongo.db.users.update_one(
        {"email": receiver_email},
        {"$addToSet": {"pending_requests": sender_email}}
    )

    return jsonify({"message": "Connection request sent!"}), 200

@key_blueprint.route('/get_pending_requests', methods=['POST'])
def get_pending_requests():
    """Fetch pending connection requests for a user."""
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"pending_requests": user.get("pending_requests", [])}), 200

@key_blueprint.route('/approve_connection', methods=['POST'])
def approve_connection():
    """Approve a connection request from another user."""
    data = request.get_json()
    receiver_email = data.get("receiver_email")
    sender_email = data.get("sender_email")

    if not receiver_email or not sender_email:
        return jsonify({"message": "Both sender and receiver email are required"}), 400

    receiver = mongo.db.users.find_one({"email": receiver_email})
    if not receiver:
        return jsonify({"message": "Receiver not found"}), 404

    if sender_email not in receiver.get("pending_requests", []):
        return jsonify({"message": "No pending request from this user"}), 400

    mongo.db.users.update_one(
        {"email": receiver_email},
        {"$pull": {"pending_requests": sender_email}, "$push": {"connected_users": sender_email}}
    )

    mongo.db.users.update_one(
        {"email": sender_email},
        {"$push": {"connected_users": receiver_email}}
    )

    return jsonify({"message": "Connection request approved!"}), 200
