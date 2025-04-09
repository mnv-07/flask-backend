from flask import Flask
from flask_cors import CORS
from api.auth import auth_blueprint, init_mongo
from service.unique_key_service import key_blueprint, init_mongo as init_mongo_key
import os

def create_app():
    """Initialize Flask app and configure MongoDB."""
    app = Flask(__name__)

    # Use Railway MongoDB URI from Environment Variables (More Secure)
    app.config['MONGO_URI'] = os.getenv("MONGO_URI", "mongodb://mongo:yfUaIbyIuazrGmhbDHeSNfsekCNPrGkc@caboose.proxy.rlwy.net:29236/UserAuth?authSource=admin")

    # Initialize MongoDB connections
    init_mongo(app)
    init_mongo_key(app)

    # Enable CORS for API access from Flutter
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register API blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(key_blueprint, url_prefix='/api')

    return app

app = create_app()  # Ensure `app` is initialized here

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
