from flask import Flask
from flask_cors import CORS
from api.auth import auth_blueprint, init_mongo
from service.unique_key_service import key_blueprint, init_mongo as init_mongo_key
import os

def create_app():
    app = Flask(__name__)
    
    app.config['MONGO_URI'] = os.getenv("MONGO_URI", "mongodb://mongo:NWLxNoJYJvLoYssKCKYUoXSazszGcPAM@caboose.proxy.rlwy.net:25575/UserAuth?authSource=admin")

    init_mongo(app)
    init_mongo_key(app)

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(key_blueprint, url_prefix='/api')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
