from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from utils.security import verify_unique_key
import random
import string

connections_bp = Blueprint('connections', __name__)

def generate_unique_key():
    """Generate a 10-digit unique key"""
    # Generate a random 10-digit number
    key = ''.join(random.choices(string.digits, k=10))
    return key

@connections_bp.route('/generate_key', methods=['POST'])
@jwt_required()
@cross_origin()
def generate_key():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        # Generate a new unique key
        new_key = generate_unique_key()
        
        # Update user's unique key
        user = current_app.user_service.get_user_by_email(current_user_email)
        if user:
            user.unique_key = new_key
            current_app.user_service.update_user(user)
            
            return jsonify({
                'message': 'Key generated successfully',
                'key': new_key
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@connections_bp.route('/send-request', methods=['POST'])
@jwt_required()
@cross_origin()
def send_connection_request():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'unique_key' not in data:
            return jsonify({'error': 'Unique key is required'}), 400
        
        target_unique_key = data['unique_key']
        
        # Find user with matching unique key
        target_user = current_app.user_service.find_user_by_unique_key(target_unique_key)
        if not target_user:
            return jsonify({'error': 'No user found with this unique key'}), 404
        
        # Check if already connected
        if target_user.is_connected:
            return jsonify({'error': 'User is already connected to someone else'}), 400
        
        # Check if already has a pending request from this user
        if current_user_email in target_user.pending_requests:
            return jsonify({'error': 'Connection request already sent'}), 400
        
        # Add connection request
        target_user.add_pending_request(current_user_email)
        current_app.user_service.update_user(target_user)
        
        return jsonify({
            'message': 'Connection request sent successfully',
            'target_email': target_user.email
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@connections_bp.route('/accept-request', methods=['POST'])
@jwt_required()
@cross_origin()
def accept_connection_request():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'requester_email' not in data:
            return jsonify({'error': 'Requester email is required'}), 400
        
        requester_email = data['requester_email']
        current_user = current_app.user_service.get_user_by_email(current_user_email)
        
        if current_user.is_connected:
            return jsonify({'error': 'You are already connected to someone else'}), 400
        
        if current_user.accept_connection(requester_email):
            # Update both users' connection status
            requester = current_app.user_service.get_user_by_email(requester_email)
            if requester.is_connected:
                return jsonify({'error': 'Requester is already connected to someone else'}), 400
                
            requester.connected_to = current_user_email
            requester.is_connected = True
            
            current_app.user_service.update_user(current_user)
            current_app.user_service.update_user(requester)
            
            return jsonify({
                'message': 'Connection established successfully',
                'connected_to': requester_email
            }), 200
        else:
            return jsonify({'error': 'No pending request from this user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@connections_bp.route('/disconnect', methods=['POST'])
@jwt_required()
@cross_origin()
def disconnect():
    try:
        current_user_email = get_jwt_identity()
        current_user = current_app.user_service.get_user_by_email(current_user_email)
        
        if not current_user.is_connected:
            return jsonify({'error': 'No active connection'}), 400
        
        connected_user_email = current_user.connected_to
        connected_user = current_app.user_service.get_user_by_email(connected_user_email)
        
        # Disconnect both users
        current_user.disconnect()
        connected_user.disconnect()
        
        current_app.user_service.update_user(current_user)
        current_app.user_service.update_user(connected_user)
        
        return jsonify({
            'message': 'Disconnected successfully',
            'disconnected_from': connected_user_email
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@connections_bp.route('/status', methods=['GET'])
@jwt_required()
@cross_origin()
def get_connection_status():
    try:
        current_user_email = get_jwt_identity()
        current_user = current_app.user_service.get_user_by_email(current_user_email)
        
        return jsonify({
            'is_connected': current_user.is_connected,
            'connected_to': current_user.connected_to,
            'pending_requests': current_user.pending_requests
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 