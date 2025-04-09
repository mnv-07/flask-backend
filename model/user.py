# User model representation
class User:
    def __init__(self, email, password_hash):
        self.email = email
        self.password_hash = password_hash
