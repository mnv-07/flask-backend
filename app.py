from flask import Flask
from flask_cors import CORS
from api.auth import auth_blueprint, init_mongo
from service.unique_key_service import key_blueprint, init_mongo as init_mongo_key
from api.connections import connections_bp
from service.user_service import UserService
import os

def create_app():
    app = Flask(__name__)
    
    # Configure MongoDB URI
    app.config['MONGO_URI'] = os.getenv("MONGO_URI", "mongodb://mongo:NWLxNoJYJvLoYssKCKYUoXSazszGcPAM@caboose.proxy.rlwy.net:25575/UserAuth?authSource=admin")
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    
    # Initialize MongoDB
    init_mongo(app)
    init_mongo_key(app)
    
    # Initialize UserService
    user_service = UserService()
    user_service.init_mongo(app)
    app.user_service = user_service

    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(key_blueprint, url_prefix='/api')
    app.register_blueprint(connections_bp, url_prefix='/api')

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
