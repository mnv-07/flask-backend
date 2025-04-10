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
    name = data.get('name')  # Add name parameter

    if not email:
        return jsonify({"message": "Email is required"}), 400

    unique_key = generate_unique_key()

    try:
        mongo.db.users.update_one(
            {"email": email},
            {"$set": {"unique_key": unique_key, "name": name}, "$setOnInsert": {"connected_users": [], "pending_requests": []}},
            upsert=True
        )
        return jsonify({"message": "Key generated successfully", "key": unique_key}), 200
    except Exception as e:
        return jsonify({"message": f"Database error: {e}"}), 500

@key_blueprint.route('/connect_users', methods=['POST'])
def connect_users():
    """Send a connection request to another user."""
    data = request.get_json()
    user1_key = data.get("user1_key")
    user2_key = data.get("user2_key")

    if not user1_key or not user2_key:
        return jsonify({"message": "Both keys are required"}), 400

    # Find users by their keys
    user1 = mongo.db.users.find_one({"unique_key": user1_key})
    user2 = mongo.db.users.find_one({"unique_key": user2_key})

    if not user1 or not user2:
        return jsonify({"message": "Invalid key(s)"}), 401

    user1_email = user1["email"]
    user2_email = user2["email"]

    # Check if already connected
    if user2_email in user1.get("connected_users", []):
        return jsonify({"message": "Users are already connected"}), 200

    # Check if request already exists
    if user1_email in user2.get("pending_requests", []):
        return jsonify({"message": "Request already sent"}), 200

    # Add to pending requests
    mongo.db.users.update_one(
        {"email": user2_email},
        {"$addToSet": {"pending_requests": user1_email}}
    )

    return jsonify({"message": "Connection request sent!"}), 200

@key_blueprint.route('/pending_requests/<user_key>', methods=['GET'])
def get_pending_requests(user_key):
    """Fetch pending connection requests for a user."""
    user = mongo.db.users.find_one({"unique_key": user_key})
    if not user:
        return jsonify({"message": "User not found"}), 404

    pending_emails = user.get("pending_requests", [])
    requests = []
    
    for email in pending_emails:
        requester = mongo.db.users.find_one({"email": email})
        if requester:
            requests.append({
                "requester_email": email,
                "requester_key": requester.get("unique_key", ""),
                "requester_name": requester.get("name", "Unknown")
            })

    return jsonify({"requests": requests}), 200

@key_blueprint.route('/accept_request', methods=['POST'])
def accept_request():
    """Accept a connection request."""
    data = request.get_json()
    user_key = data.get("user_key")
    requester_key = data.get("requester_key")

    if not user_key or not requester_key:
        return jsonify({"message": "Both keys are required"}), 400

    user = mongo.db.users.find_one({"unique_key": user_key})
    requester = mongo.db.users.find_one({"unique_key": requester_key})

    if not user or not requester:
        return jsonify({"message": "Invalid key(s)"}), 401

    user_email = user["email"]
    requester_email = requester["email"]

    if requester_email not in user.get("pending_requests", []):
        return jsonify({"message": "No pending request from this user"}), 400

    # Update both users' connected lists
    mongo.db.users.update_one(
        {"email": user_email},
        {"$pull": {"pending_requests": requester_email}, "$push": {"connected_users": requester_email}}
    )

    mongo.db.users.update_one(
        {"email": requester_email},
        {"$push": {"connected_users": user_email}}
    )

    return jsonify({"message": "Connection request accepted!"}), 200

@key_blueprint.route('/reject_request', methods=['POST'])
def reject_request():
    """Reject a connection request."""
    data = request.get_json()
    user_key = data.get("user_key")
    requester_key = data.get("requester_key")

    if not user_key or not requester_key:
        return jsonify({"message": "Both keys are required"}), 400

    user = mongo.db.users.find_one({"unique_key": user_key})
    requester = mongo.db.users.find_one({"unique_key": requester_key})

    if not user or not requester:
        return jsonify({"message": "Invalid key(s)"}), 401

    user_email = user["email"]
    requester_email = requester["email"]

    # Remove from pending requests
    mongo.db.users.update_one(
        {"email": user_email},
        {"$pull": {"pending_requests": requester_email}}
    )

    return jsonify({"message": "Connection request rejected!"}), 200

@key_blueprint.route('/check_connection/<user1_key>/<user2_key>', methods=['GET'])
def check_connection(user1_key, user2_key):
    """Check if two users are connected."""
    user1 = mongo.db.users.find_one({"unique_key": user1_key})
    user2 = mongo.db.users.find_one({"unique_key": user2_key})

    if not user1 or not user2:
        return jsonify({"message": "Invalid key(s)", "connected": False}), 401

    user1_email = user1["email"]
    user2_email = user2["email"]

    connected = user2_email in user1.get("connected_users", [])
    return jsonify({"connected": connected}), 200

@key_blueprint.route('/get_connected_users/<user_key>', methods=['GET'])
def get_connected_users(user_key):
    """Get list of connected users with their details."""
    user = mongo.db.users.find_one({"unique_key": user_key})
    if not user:
        return jsonify({"message": "User not found"}), 404

    connected_emails = user.get("connected_users", [])
    connected_users = []
    
    for email in connected_emails:
        connected_user = mongo.db.users.find_one({"email": email})
        if connected_user:
            connected_users.append({
                "email": email,
                "name": connected_user.get("name", "Unknown"),
                "key": connected_user.get("unique_key", "")
            })

    return jsonify({"connected_users": connected_users}), 200
