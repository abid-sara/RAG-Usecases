from flask import Flask
from flask_cors import CORS
from flask_session import Session

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Configure server-side session storage
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    
    # Register blueprints
    from app.api.routes import api
    app.register_blueprint(api, url_prefix='/api')
    
    return app