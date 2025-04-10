class User:
    def __init__(self, email, password_hash, unique_key=None):
        self.email = email
        self.password_hash = password_hash
        self.unique_key = unique_key
        self.connected_to = None  # Email of the user this user is connected to
        self.pending_requests = []  # List of emails who have sent connection requests
        self.is_connected = False

    def add_pending_request(self, requester_email):
        if requester_email not in self.pending_requests:
            self.pending_requests.append(requester_email)

    def accept_connection(self, requester_email):
        if requester_email in self.pending_requests:
            self.pending_requests.remove(requester_email)
            self.connected_to = requester_email
            self.is_connected = True
            return True
        return False

    def disconnect(self):
        self.connected_to = None
        self.is_connected = False
