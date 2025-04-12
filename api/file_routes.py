from flask import Blueprint, request, jsonify
from service.file_service import FileService
from utils.auth_utils import token_required
from werkzeug.utils import secure_filename
import os

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        receiver_email = request.form.get('receiver_email')
        if not receiver_email:
            return jsonify({'error': 'Receiver email is required'}), 400

        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Initialize file service
        file_service = FileService(request.app.config['db'])
        
        # Upload file
        file_id = file_service.upload_file(
            file=file,
            sender_email=current_user['email'],
            receiver_email=receiver_email
        )

        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': file_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@file_bp.route('/shared-files', methods=['GET'])
@token_required
def get_shared_files(current_user):
    try:
        file_service = FileService(request.app.config['db'])
        files = file_service.get_shared_files(current_user['email'])
        
        # Convert ObjectId to string for JSON serialization
        for file in files:
            file['_id'] = str(file['_id'])
            file['upload_date'] = file['upload_date'].isoformat()

        return jsonify({'files': files}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@file_bp.route('/delete/<file_id>', methods=['DELETE'])
@token_required
def delete_file(current_user, file_id):
    try:
        file_service = FileService(request.app.config['db'])
        file_service.delete_file(file_id, current_user['email'])
        
        return jsonify({'message': 'File deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500 