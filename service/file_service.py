from flask_pymongo import PyMongo
from cryptography.fernet import Fernet
import base64
import os
from datetime import datetime

class FileService:
    def __init__(self):
        self.mongo = None
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def init_mongo(self, app):
        """Initialize MongoDB connection for the service"""
        self.mongo = PyMongo(app)

    def encrypt_data(self, data):
        """Encrypt data using Fernet symmetric encryption"""
        if isinstance(data, str):
            data = data.encode()
        encrypted_data = self.cipher_suite.encrypt(data)
        return base64.b64encode(encrypted_data).decode()

    def decrypt_data(self, encrypted_data):
        """Decrypt data using Fernet symmetric encryption"""
        encrypted_data = base64.b64decode(encrypted_data.encode())
        return self.cipher_suite.decrypt(encrypted_data).decode()

    def share_file(self, sender_email, receiver_email, file_data, file_name):
        """Share an encrypted file between users"""
        if not self.mongo:
            raise Exception("MongoDB not initialized")

        # Encrypt the file data
        encrypted_data = self.encrypt_data(file_data)

        # Store the shared file in MongoDB
        shared_file = {
            'sender_email': sender_email,
            'receiver_email': receiver_email,
            'file_name': file_name,
            'encrypted_data': encrypted_data,
            'shared_at': datetime.utcnow(),
            'is_read': False
        }

        self.mongo.db.shared_files.insert_one(shared_file)
        return True

    def get_shared_files(self, email):
        """Get all files shared with a user"""
        if not self.mongo:
            raise Exception("MongoDB not initialized")

        files = list(self.mongo.db.shared_files.find({
            'receiver_email': email
        }).sort('shared_at', -1))

        return files

    def get_file(self, file_id):
        """Get and decrypt a specific shared file"""
        if not self.mongo:
            raise Exception("MongoDB not initialized")

        file_data = self.mongo.db.shared_files.find_one({'_id': file_id})
        if file_data:
            # Decrypt the file data
            decrypted_data = self.decrypt_data(file_data['encrypted_data'])
            return {
                'file_name': file_data['file_name'],
                'data': decrypted_data,
                'sender_email': file_data['sender_email'],
                'shared_at': file_data['shared_at']
            }
        return None 