from flask_pymongo import PyMongo
from model.user import User
from bson.objectid import ObjectId

class UserService:
    def __init__(self):
        self.mongo = PyMongo()

    def get_user_by_email(self, email):
        user_data = self.mongo.db.users.find_one({'email': email})
        if user_data:
            return User(
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                unique_key=user_data.get('unique_key'),
                connected_to=user_data.get('connected_to'),
                pending_requests=user_data.get('pending_requests', []),
                is_connected=user_data.get('is_connected', False)
            )
        return None

    def find_user_by_unique_key(self, unique_key):
        user_data = self.mongo.db.users.find_one({'unique_key': unique_key})
        if user_data:
            return User(
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                unique_key=user_data.get('unique_key'),
                connected_to=user_data.get('connected_to'),
                pending_requests=user_data.get('pending_requests', []),
                is_connected=user_data.get('is_connected', False)
            )
        return None

    def update_user(self, user):
        self.mongo.db.users.update_one(
            {'email': user.email},
            {
                '$set': {
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'unique_key': user.unique_key,
                    'connected_to': user.connected_to,
                    'pending_requests': user.pending_requests,
                    'is_connected': user.is_connected
                }
            },
            upsert=True
        )

    def add_user(self, user):
        if not self.get_user_by_email(user.email):
            self.mongo.db.users.insert_one({
                'email': user.email,
                'password_hash': user.password_hash,
                'unique_key': user.unique_key,
                'connected_to': None,
                'pending_requests': [],
                'is_connected': False
            })
            return True
        return False

    def validate_user(self, email, password_hash):
        user = self.get_user_by_email(email)
        if user and user.password_hash == password_hash:
            return user
        return None
