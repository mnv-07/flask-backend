from flask import Flask
from flask_cors import CORS
from flask_backend.api.auth import auth_blueprint, init_mongo
from flask_backend.service.unique_key_service import key_blueprint, init_mongo as init_mongo_key
from flask_backend.api.connections import connections_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configure MongoDB URI
    app.config['MONGO_URI'] = os.getenv("MONGO_URI", "mongodb://mongo:NWLxNoJYJvLoYssKCKYUoXSazszGcPAM@caboose.proxy.rlwy.net:25575/UserAuth?authSource=admin")
    
    # Initialize MongoDB
    init_mongo(app)
    init_mongo_key(app)

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
