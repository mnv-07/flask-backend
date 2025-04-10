from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..service.user_service import UserService
from ..utils.security import verify_unique_key

connections_bp = Blueprint('connections', __name__)
user_service = UserService()

@connections_bp.route('/send-request', methods=['POST'])
@jwt_required()
def send_connection_request():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'unique_key' not in data:
        return jsonify({'error': 'Unique key is required'}), 400
    
    target_unique_key = data['unique_key']
    
    # Find user with matching unique key
    target_user = user_service.find_user_by_unique_key(target_unique_key)
    if not target_user:
        return jsonify({'error': 'No user found with this unique key'}), 404
    
    # Add connection request
    target_user.add_pending_request(current_user_email)
    user_service.update_user(target_user)
    
    return jsonify({'message': 'Connection request sent successfully'}), 200

@connections_bp.route('/accept-request', methods=['POST'])
@jwt_required()
def accept_connection_request():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'requester_email' not in data:
        return jsonify({'error': 'Requester email is required'}), 400
    
    requester_email = data['requester_email']
    current_user = user_service.get_user_by_email(current_user_email)
    
    if current_user.accept_connection(requester_email):
        # Update both users' connection status
        requester = user_service.get_user_by_email(requester_email)
        requester.connected_to = current_user_email
        requester.is_connected = True
        
        user_service.update_user(current_user)
        user_service.update_user(requester)
        
        return jsonify({'message': 'Connection established successfully'}), 200
    else:
        return jsonify({'error': 'No pending request from this user'}), 400

@connections_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect():
    current_user_email = get_jwt_identity()
    current_user = user_service.get_user_by_email(current_user_email)
    
    if not current_user.is_connected:
        return jsonify({'error': 'No active connection'}), 400
    
    connected_user_email = current_user.connected_to
    connected_user = user_service.get_user_by_email(connected_user_email)
    
    # Disconnect both users
    current_user.disconnect()
    connected_user.disconnect()
    
    user_service.update_user(current_user)
    user_service.update_user(connected_user)
    
    return jsonify({'message': 'Disconnected successfully'}), 200

@connections_bp.route('/status', methods=['GET'])
@jwt_required()
def get_connection_status():
    current_user_email = get_jwt_identity()
    current_user = user_service.get_user_by_email(current_user_email)
    
    return jsonify({
        'is_connected': current_user.is_connected,
        'connected_to': current_user.connected_to,
        'pending_requests': current_user.pending_requests
    }), 200 