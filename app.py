from flask import Flask, jsonify
from flask_cors import CORS
from api.auth import auth_blueprint, init_mongo
from service.unique_key_service import key_blueprint, init_mongo as init_mongo_key
import os
import logging
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Initialize Flask app and configure MongoDB."""
    app = Flask(__name__)

    # Use Railway MongoDB URI from Environment Variables (More Secure)
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:yfUaIbyIuazrGmhbDHeSNfsekCNPrGkc@caboose.proxy.rlwy.net:29236/UserAuth?authSource=admin")
    app.config['MONGO_URI'] = mongo_uri

    try:
        # Initialize MongoDB connections
        init_mongo(app)
        init_mongo_key(app)
        logger.info("MongoDB connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise

    # Enable CORS for API access from Flutter
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register API blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(key_blueprint, url_prefix='/api')

    # Error handlers
    @app.errorhandler(Exception)
    def handle_error(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        logger.error(f"Error occurred: {str(e)}")
        return jsonify(error=str(e)), code

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
