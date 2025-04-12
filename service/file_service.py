import cloudinary
import cloudinary.uploader
from config.cloudinary_config import CLOUDINARY_CONFIG
from datetime import datetime
from bson import ObjectId

class FileService:
    def __init__(self, db):
        self.db = db
        cloudinary.config(**CLOUDINARY_CONFIG)

    def upload_file(self, file, sender_email, receiver_email):
        try:
            # Upload file to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder='file_sharing',
                resource_type='auto'
            )

            # Store file metadata in database
            file_metadata = {
                'file_url': upload_result['secure_url'],
                'file_name': file.filename,
                'file_size': upload_result['bytes'],
                'sender_email': sender_email,
                'receiver_email': receiver_email,
                'upload_date': datetime.utcnow(),
                'cloudinary_public_id': upload_result['public_id']
            }

            result = self.db.files.insert_one(file_metadata)
            return str(result.inserted_id)

        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")

    def get_shared_files(self, email):
        try:
            # Get files where user is either sender or receiver
            files = self.db.files.find({
                '$or': [
                    {'sender_email': email},
                    {'receiver_email': email}
                ]
            }).sort('upload_date', -1)

            return list(files)

        except Exception as e:
            raise Exception(f"Error fetching shared files: {str(e)}")

    def delete_file(self, file_id, email):
        try:
            # Get file metadata
            file_metadata = self.db.files.find_one({'_id': ObjectId(file_id)})
            
            if not file_metadata:
                raise Exception("File not found")

            # Check if user has permission to delete
            if file_metadata['sender_email'] != email and file_metadata['receiver_email'] != email:
                raise Exception("Unauthorized to delete this file")

            # Delete from Cloudinary
            cloudinary.uploader.destroy(file_metadata['cloudinary_public_id'])

            # Delete from database
            self.db.files.delete_one({'_id': ObjectId(file_id)})

            return True

        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}") 