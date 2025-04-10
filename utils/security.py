from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def check_password(hash, password):
    return check_password_hash(hash, password)

def verify_unique_key(unique_key):
    """
    Verify if a unique key is valid.
    Args:
        unique_key (str): The unique key to verify
    Returns:
        bool: True if the key is valid, False otherwise
    """
    # Check if the key is not empty and has a reasonable length
    if not unique_key or len(unique_key) < 8:
        return False
    
    # Add any additional validation rules here
    # For example, check for specific format or characters
    
    return True
