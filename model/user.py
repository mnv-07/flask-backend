class User:
    def __init__(self, email, password_hash, unique_key=None, connected_to=None, pending_requests=None, is_connected=False):
        self.email = email
        self.password_hash = password_hash
        self.unique_key = unique_key
        self.connected_to = connected_to
        self.pending_requests = pending_requests or []
        self.is_connected = is_connected

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
