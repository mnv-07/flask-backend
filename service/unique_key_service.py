import random
import string
from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

key_blueprint = Blueprint('key', __name__)
mongo = None 

def init_mongo(app):
    global mongo
    mongo = PyMongo(app)

def generate_unique_key():
    return ''.join(random.choices(string.digits, k=10))

@key_blueprint.route('/generate_key', methods=['POST'])
def generate_key():
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
            {"$set": {"unique_key": hashed_key}, "$setOnInsert": {"connected_users": []}},
            upsert=True
        )
        return jsonify({"message": "Key generated successfully", "key": unique_key}), 200
    except Exception as e:
        return jsonify({"message": f"Database error: {e}"}), 500

@key_blueprint.route('/connect_users', methods=['POST'])
def connect_users():
    data = request.get_json()
    user1_email = data.get("user1_email")
    user2_key = data.get("user2_key")

    if not user1_email or not user2_key:
        return jsonify({"message": "Both user email and key are required"}), 400

    user1 = mongo.db.users.find_one({"email": user1_email})
    if not user1:
        return jsonify({"message": "User not found"}), 404

    user2 = mongo.db.users.find_one({"unique_key": user2_key})
    if not user2:
        return jsonify({"message": "Invalid unique key"}), 401

    user2_email = user2["email"]

    if user2_email in user1.get("connected_users", []):
        return jsonify({"message": "Users are already connected"}), 200

    mongo.db.users.update_one(
        {"email": user1_email},
        {"$push": {"connected_users": user2_email}}
    )

    mongo.db.users.update_one(
        {"email": user2_email},
        {"$push": {"connected_users": user1_email}}
    )

    return jsonify({"message": "Users successfully connected!"}), 200
