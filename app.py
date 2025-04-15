from flask import Flask
from flask_cors import CORS
from api.auth import auth_blueprint, init_mongo
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
    
    # Initialize UserService
    user_service = UserService()
    user_service.init_mongo(app)
    app.user_service = user_service

    # Configure CORS with specific origins
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",  # Vite dev server
                "http://localhost:3000",  # Alternative dev port
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Register blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(connections_bp, url_prefix='/api')

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
