from flask import Blueprint, request, jsonify, send_file
from service.file_service import FileService
import io
from bson import ObjectId

files_bp = Blueprint('files', __name__)
file_service = FileService()

def init_mongo(app):
    file_service.init_mongo(app)

@files_bp.route('/share', methods=['POST'])
def share_file():
    try:
        data = request.get_json()
        sender_email = data.get('sender_email')
        receiver_email = data.get('receiver_email')
        file_data = data.get('file_data')
        file_name = data.get('file_name')

        if not all([sender_email, receiver_email, file_data, file_name]):
            return jsonify({"error": "Missing required fields"}), 400

        success = file_service.share_file(sender_email, receiver_email, file_data, file_name)
        if success:
            return jsonify({"message": "File shared successfully"}), 201
        return jsonify({"error": "Failed to share file"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@files_bp.route('/shared-files/<email>', methods=['GET'])
def get_shared_files(email):
    try:
        files = file_service.get_shared_files(email)
        # Convert ObjectId to string for JSON serialization
        for file in files:
            file['_id'] = str(file['_id'])
            file['shared_at'] = file['shared_at'].isoformat()
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@files_bp.route('/file/<file_id>', methods=['GET'])
def get_file(file_id):
    try:
        file_data = file_service.get_file(ObjectId(file_id))
        if file_data:
            return jsonify(file_data), 200
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500 